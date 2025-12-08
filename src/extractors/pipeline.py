"""
Main Extraction Pipeline Orchestrator
Coordinates all extraction modules without relying on database storage
"""

import os
import uuid
import json
import re
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import sys
from functools import lru_cache

from src.extractors.metadata_extractor import MetadataExtractor
from src.extractors.document_extractor import DocumentExtractor
from src.extractors.feature_extractor import ContentFeatureExtractor
from src.extractors.llm_config import create_feature_extractor
from src.extractors.models import ContentFeatures

# Import performance and monitoring utilities
try:
    from src.utils.llm_cache import get_llm_cache
    from src.utils.metrics import get_metrics_collector
    from src.utils.parallel_processor import ChartBatchProcessor
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    print("Warning: Performance utilities not available")


PIPELINE_VERSION = "0.3.0"

# Local copy of the PII regexes so the pipeline can warn without importing the
# entire extractor module (avoids circular imports when running tests).
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{6,}")


class ExtractionPipeline:
    """Main pipeline orchestrator for document extraction"""
    
    def __init__(self, use_llm: bool = True, output_dir: Optional[str] = None, enable_metrics: bool = True):
        """
        Initialize pipeline
        
        Args:
            use_llm: Whether to use LLM for feature extraction (default: True)
            output_dir: Directory where JSON outputs will be stored (default: ./outputs)
            enable_metrics: Whether to enable metrics tracking (default: True)
        """
        # Houni ninitializiw l pipeline: metadata extractor, document extractor, optional LLM feature extractor
        # Enable LLM for metadata extraction if use_llm is True
        self.metadata_extractor = MetadataExtractor(use_llm=use_llm)
        # Initialize document extractor with chart analysis enabled by default
        self.document_extractor = DocumentExtractor(enable_chart_analysis=True)
        self.use_llm = use_llm
        self.output_dir = Path(output_dir or os.getenv("PIPELINE_OUTPUT_DIR", "outputs"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metrics tracking
        self.enable_metrics = enable_metrics and UTILS_AVAILABLE
        self.metrics = get_metrics_collector() if self.enable_metrics else None
        
        if use_llm:
            try:
                self.feature_extractor = create_feature_extractor()
            except Exception as e:
                print(f"Warning: Could not initialize LLM feature extractor: {e}")
                print("Continuing without LLM feature extraction...")
                self.use_llm = False
                self.feature_extractor = None
        else:
            self.feature_extractor = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert date objects to ISO format strings
        def convert_dates(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_dates(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_dates(item) for item in obj]
            return obj
        
        data = convert_dates(data)
        
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _compute_file_hash(self, path: Path) -> str:
        # SHA-256 gives us a deterministic fingerprint so we can guarantee the
        # same document revisions produce identical outputs.  This guards against
        # accidental reprocessing and allows quick integrity checks.
        sha256 = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _normalize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {}
        for key, value in metadata.items():
            if isinstance(value, str):
                normalized[key] = value.strip()
            else:
                normalized[key] = value
        normalized.setdefault("pipeline_version", PIPELINE_VERSION)
        return normalized

    def _validate_extraction(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        warnings = []
        text_content = extraction_result.get('text', '') or ''
        if not text_content.strip():
            warnings.append("No text extracted from document")
        elif len(text_content.strip()) < 200:
            warnings.append("Extracted text is very short (<200 chars); verify OCR output")

        tables = extraction_result.get('tables', [])
        if isinstance(tables, list) and len(tables) == 0 and extraction_result.get('total_tables', 0) > 0:
            warnings.append("Table count mismatch between metadata and table data")

        # Simple PII detection: marketing decks should not contain emails or
        # phone numbers unless explicitly approved.  We warn so reviewers can
        # double-check the offending sections.
        emails = EMAIL_PATTERN.findall(text_content)
        phones = PHONE_PATTERN.findall(text_content)
        if emails:
            warnings.append(f"Potential email addresses detected: {', '.join(set(emails))[:120]}...")
        if phones:
            warnings.append("Potential phone numbers detected in extracted text")

        return {"warnings": warnings}

    def _validate_features(self, features: ContentFeatures) -> Dict[str, Any]:
        warnings = []

        for perf in features.performance_data:
            has_percent = perf.percentage is not None or ('%' in perf.text)
            has_date = bool(perf.date_range)
            if not has_percent:
                warnings.append(
                    f"Performance mention without percentage: '{perf.text[:80]}'"
                )
            if not has_date:
                warnings.append(
                    f"Performance mention missing date range: '{perf.text[:80]}'"
                )

        esg_keywords = {"esg", "sustainable", "article", "sfdr", "responsible"}
        for esg in features.esg_mentions:
            if not any(keyword.lower() in esg.text.lower() for keyword in esg_keywords):
                warnings.append(
                    f"ESG mention lacks expected keywords: '{esg.text[:80]}'"
                )

        for country in features.country_mentions:
            if not country.country_name or len(country.country_name) < 3:
                warnings.append(
                    f"Country mention with suspicious name: '{country.country_name}'"
                )

        return {"warnings": warnings}

    def _build_summary(
        self,
        metadata: Dict[str, Any],
        extraction_result: Dict[str, Any],
        features_summary: Optional[Dict[str, int]],
        warnings: Optional[list]
    ) -> Dict[str, Any]:
        document_name = metadata.get('filename') or metadata.get('file_path')
        text_length = len((extraction_result.get('text') or ""))
        total_tables = extraction_result.get('total_tables', 0)
        structure = extraction_result.get('structure') or {}
        identifier_count = len(extraction_result.get('identifiers') or [])
        issuer_count = len(extraction_result.get('issuer_mentions') or [])
        country_count = len(extraction_result.get('country_entries') or [])

        summary = {
            "document": document_name,
            "text_characters": text_length,
            "total_tables": total_tables,
            "identifier_count": identifier_count,
            "issuer_count": issuer_count,
            "country_mentions_count": country_count,
            "has_glossary": structure.get('has_glossary'),
            "has_management_notice": structure.get('has_management_notice'),
            "warnings": warnings or [],
        }

        if features_summary:
            summary["feature_counts"] = features_summary

        return summary

    def _persist_outputs(
        self,
        document_id: str,
        original_filename: str,
        metadata: Dict[str, Any],
        extraction_result: Dict[str, Any],
        features_dump: Optional[Dict[str, Any]],
        summary: Dict[str, Any]
    ) -> Dict[str, str]:
        document_dir = self.output_dir / document_id
        document_dir.mkdir(parents=True, exist_ok=True)

        metadata_path = document_dir / "metadata.json"
        extraction_path = document_dir / "extraction.json"
        manifest_path = document_dir / "manifest.json"

        self._write_json(metadata_path, metadata)
        self._write_json(extraction_path, extraction_result)

        features_path = None
        if features_dump is not None:
            features_path = document_dir / "features.json"
            self._write_json(features_path, features_dump)

        manifest_payload = {
            "document_id": document_id,
            "original_filename": original_filename,
            "processed_at": datetime.utcnow().isoformat() + "Z",
            "paths": {
                "metadata": str(metadata_path.relative_to(self.output_dir)),
                "extraction": str(extraction_path.relative_to(self.output_dir)),
                "features": str(features_path.relative_to(self.output_dir)) if features_path else None,
            },
            "summary": summary,
        }
        self._write_json(manifest_path, manifest_payload)

        return {
            "document_dir": str(document_dir),
            "metadata": str(metadata_path),
            "extraction": str(extraction_path),
            "features": str(features_path) if features_path else None,
            "manifest": str(manifest_path),
        }

    def _read_index_entries(self, index_path: Path) -> Dict[str, Any]:
        entries = {}
        if not index_path.exists():
            return entries

        with index_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    doc_id = payload.get("document_id")
                    if doc_id:
                        entries[doc_id] = payload
                except json.JSONDecodeError:
                    continue
        return entries

    def _append_index_entry(self, manifest_payload: Dict[str, Any]) -> None:
        index_path = self.output_dir / "index.jsonl"
        entries = self._read_index_entries(index_path)
        entries[manifest_payload["document_id"]] = manifest_payload

        with index_path.open("w", encoding="utf-8") as f:
            for entry in entries.values():
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _find_existing_by_checksum(self, checksum: str) -> Optional[Dict[str, Any]]:
        index_path = self.output_dir / "index.jsonl"
        entries = self._read_index_entries(index_path)
        for entry in entries.values():
            if entry.get('file_checksum') == checksum:
                return entry
        return None

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_disclaimer_glossary() -> Dict[str, Dict[str, Dict[str, str]]]:
        data_path = Path(__file__).resolve().parent / 'data' / 'disclaimer_glossary.json'
        if not data_path.exists():
            return {}
        with data_path.open('r', encoding='utf-8') as f:
            return json.load(f)

    def _doc_types_from_categories(self, categories: Any, metadata: Dict[str, Any]) -> set:
        categories = categories or []
        doc_types = set()
        if 'performance' in categories:
            doc_types.add('Performance')
        if 'esg_risk' in categories:
            doc_types.add('ESG Risk')
        if 'issuers' in categories:
            doc_types.add('Issuers mentioned ')
        if 'simulation' in categories:
            doc_types.add('Simulations  of  future performance')
        if 'backtest' in categories:
            doc_types.add('Back-tested performance')
        if 'ytm' in categories:
            doc_types.add('YtM/YtW usage')
        if 'opinion' in categories:
            doc_types.add('Opinion')
        if 'new_offer' in categories:
            if metadata.get('is_new_product'):
                doc_types.add('New offer products (strategy mentioning funds track record)')
            else:
                doc_types.add('New offer products (strategy only)')
        return doc_types

    def _base_disclaimer_doc_types(self, metadata: Dict[str, Any]) -> set:
        doc_types = {'OBAM Presentation'}
        mgmt = metadata.get('management_company') or metadata.get('management_company_full')
        if mgmt:
            mgmt_upper = mgmt.upper()
            if 'SAS' in mgmt_upper:
                doc_types.add('Commercial documentation : management company = OBAM SAS')
            elif 'GMBH' in mgmt_upper:
                doc_types.add('Commercial documentation : management company = OBAM GmbH')
            elif 'LUX' in mgmt_upper:
                doc_types.add('Commercial documentation : management company = OBAM Lux')
        return doc_types

    def _map_disclaimers_to_glossary(
        self,
        extraction_result: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        glossary = self._load_disclaimer_glossary()
        if not glossary:
            return []

        language = (metadata.get('language_code') or 'ENGLISH').upper()
        if language not in glossary:
            language = 'ENGLISH'

        client_type = 'professional' if metadata.get('is_professional_client') else 'non_professional'
        lang_map = glossary.get(language, {})
        client_map = lang_map.get(client_type, {})
        if not client_map:
            return []

        matches = []
        seen = set()

        def add_doc_type(doc_type: str, location: Dict[str, Any]):
            text = client_map.get(doc_type)
            if not text:
                return
            key = (doc_type, tuple(sorted(location.items())))
            if key in seen:
                return
            seen.add(key)
            matches.append({
                'doc_type': doc_type,
                'language': language,
                'client_type': client_type,
                'text': text,
                **location
            })

        for doc_type in self._base_disclaimer_doc_types(metadata):
            add_doc_type(doc_type, {'source': 'document'})

        # Slides
        for slide in extraction_result.get('slide_summaries', []):
            if not slide.get('contains_disclaimer'):
                continue
            doc_types = self._doc_types_from_categories(slide.get('disclaimer_categories'), metadata)
            if not doc_types:
                doc_types = {'OBAM Presentation'}
            for doc_type in doc_types:
                add_doc_type(doc_type, {'slide_number': slide['slide_number']})

        # Paragraphs (DOCX)
        for para in extraction_result.get('paragraph_summaries', []):
            if not para.get('contains_disclaimer'):
                continue
            doc_types = self._doc_types_from_categories(para.get('disclaimer_categories'), metadata)
            for doc_type in doc_types:
                add_doc_type(doc_type, {'paragraph_number': para['paragraph_number']})

        # PDF pages
        for page in extraction_result.get('page_summaries', []):
            if not page.get('contains_disclaimer'):
                continue
            doc_types = self._doc_types_from_categories(page.get('disclaimer_categories'), metadata)
            for doc_type in doc_types:
                add_doc_type(doc_type, {'page_number': page['page_number']})

        return matches
    
    def process_document(
        self, 
        file_path: str,
        metadata_json_path: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        chunk_size: int = 10000
    ) -> Dict[str, Any]:
        """
        Process a document through the entire extraction pipeline
        
        Args:
            file_path: Path to document file (PPTX, DOCX, PDF)
            metadata_json_path: Optional path to metadata JSON file
            uploaded_by: Optional user identifier
            chunk_size: Text chunk size for LLM processing (if needed)
            
        Returns:
            Dict with processing results and document_id
        """
        # Main pipeline flow: extract metadata, detect family, create record,
        # extract content, optionally extract features with LLM, finalize
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        file_checksum = self._compute_file_hash(file_path)

        existing_entry = self._find_existing_by_checksum(file_checksum)
        if existing_entry:
            manifest_rel = existing_entry.get('paths', {}).get('manifest')
            manifest_path = self.output_dir / manifest_rel if manifest_rel else None
            reuse_result = {
                'document_id': existing_entry['document_id'],
                'status': 'skipped',
                'warnings': ["Reused existing extraction for identical file checksum"],
                'steps_completed': ['cache_hit'],
                'file_checksum': file_checksum,
                'output_paths': existing_entry.get('paths')
            }
            if manifest_path and manifest_path.exists():
                try:
                    reuse_result['manifest'] = json.loads(manifest_path.read_text(encoding='utf-8'))
                except Exception:
                    reuse_result['warnings'].append('Failed to load existing manifest; consider reprocessing')
            return reuse_result

        result = {
            'document_id': None,
            'status': 'started',
            'errors': [],
            'warnings': [],
            'steps_completed': [],
            'file_checksum': file_checksum
        }
        
        try:
            # Step 1: Extract basic metadata (filename + JSON)
            print(f"[Step 1/6] Extracting metadata from: {file_path.name}")
            try:
                metadata = self.metadata_extractor.extract(
                    file_path=str(file_path),
                    metadata_json_path=metadata_json_path
                    # Note: extraction_result will be added in Step 4 after document extraction
                )
                normalized_metadata = self._normalize_metadata(metadata)
                result['metadata'] = normalized_metadata
                result['steps_completed'].append('metadata_extraction')
            except Exception as e:
                error_msg = f"Metadata extraction failed: {str(e)}"
                result['errors'].append(error_msg)
                print(f"  WARNING: {error_msg}")
                # Continue with basic metadata
                normalized_metadata = {
                    'filename': file_path.name,
                    'file_type': file_path.suffix.upper().lstrip('.'),
                    'file_path': str(file_path),
                    'pipeline_version': PIPELINE_VERSION
                }
                result['metadata'] = normalized_metadata

            result['metadata']['file_checksum'] = file_checksum
            
            # Step 2: Skip family detection now that database is removed
            print(f"[Step 2/6] Skipping document family detection (database removed)")
            family_id = None
            result['family_id'] = family_id
            result['steps_completed'].append('family_detection_skipped')
            
            # Step 3: Create an in-memory document identifier
            print(f"[Step 3/6] Creating in-memory document record...")
            document_id = str(uuid.uuid4())
            result['document_id'] = document_id
            result['steps_completed'].append('document_record_created')
            
            # Step 4: Extract document content (text and tables)
            print(f"[Step 4/6] Extracting document content...")
            features_dump = None
            try:
                extraction_result = self.document_extractor.extract(str(file_path))
                
                if 'error' in extraction_result:
                    raise Exception(extraction_result['error'])
                
                extraction_id = str(uuid.uuid4())
                result['extraction_id'] = extraction_id
                result['extraction_result'] = extraction_result
                result['steps_completed'].append('content_extraction')

                if extraction_result.get('title_information'):
                    result['metadata']['title_information'] = extraction_result['title_information']

                if extraction_result.get('identifiers'):
                    result['metadata']['identifiers'] = extraction_result['identifiers']

                if extraction_result.get('issuer_mentions'):
                    result['metadata']['issuer_mentions'] = extraction_result['issuer_mentions']

                if extraction_result.get('country_entries'):
                    result['metadata']['country_entries'] = extraction_result['country_entries']

                if extraction_result.get('performance_table_entries'):
                    result['metadata']['performance_table_entries'] = extraction_result['performance_table_entries']

                glossary_matches = self._map_disclaimers_to_glossary(extraction_result, result['metadata'])
                if glossary_matches:
                    result['metadata']['disclaimer_glossary_matches'] = glossary_matches

                extraction_validation = self._validate_extraction(extraction_result)
                if extraction_validation['warnings']:
                    result['warnings'].extend(extraction_validation['warnings'])

                print(f"  [OK] Extracted {len(extraction_result.get('text', ''))} characters")
                print(f"  [OK] Found {extraction_result.get('total_tables', 0)} tables")
                if extraction_result.get('total_charts', 0) > 0:
                    print(f"  [OK] Found {extraction_result.get('total_charts', 0)} charts")
                
                # Enhance metadata with content-based detection
                try:
                    enhanced_metadata = self.metadata_extractor.extract(
                        file_path=str(file_path),
                        metadata_json_path=metadata_json_path,
                        extraction_result=extraction_result
                    )
                    # Merge enhanced metadata (content detection adds new fields)
                    for key, value in enhanced_metadata.items():
                        if key not in result['metadata'] or not result['metadata'].get(key):
                            result['metadata'][key] = value
                        elif key in ['client_type', 'management_company', 'is_sicav_product', 
                                    'is_professional_client', 'is_new_strategy', 'is_new_product']:
                            # Content detection can override if JSON didn't provide it
                            if result['metadata'].get(key) == 'Unknown' or result['metadata'].get(key) is False:
                                result['metadata'][key] = value
                    result['metadata']['has_content_metadata'] = enhanced_metadata.get('has_content_metadata', False)
                except Exception as e:
                    # Non-critical: content-based metadata detection failed, continue with existing metadata
                    print(f"  [WARNING] Content-based metadata detection failed: {str(e)}")
                
            except Exception as e:
                error_msg = f"Content extraction failed: {str(e)}"
                result['errors'].append(error_msg)
                print(f"  [ERROR] {error_msg}")
                raise
            
            # Step 5: Extract features using LLM (if enabled)
            if self.use_llm and self.feature_extractor and extraction_result.get('text'):
                print(f"[Step 5/6] Extracting content features using LLM...")
                try:
                    text_content = extraction_result.get('text', '')
                    
                    # Use chunking for large documents
                    if len(text_content) > chunk_size:
                        print(f"  [INFO] Document is large ({len(text_content)} chars), using chunking...")
                        features = self.feature_extractor.extract_features_chunked(
                            text_content, 
                            chunk_size=chunk_size
                        )
                    else:
                        features = self.feature_extractor.extract_features(text_content)
 
                    features_dump = features.model_dump()
                    result['features'] = {
                        'esg_mentions': len(features.esg_mentions),
                        'performance_data': len(features.performance_data),
                        'country_mentions': len(features.country_mentions),
                        'company_mentions': len(features.company_mentions),
                        'financial_terms': len(features.financial_terms)
                    }
                    result['feature_details'] = features_dump
                    result['steps_completed'].append('feature_extraction')

                    feature_validation = self._validate_features(features)
                    if feature_validation['warnings']:
                        result['warnings'].extend(feature_validation['warnings'])
                    
                    print(f"  [OK] Extracted {len(features.esg_mentions)} ESG mentions")
                    print(f"  [OK] Extracted {len(features.performance_data)} performance data points")
                    print(f"  [OK] Extracted {len(features.country_mentions)} country mentions")
                    
                except Exception as e:
                    error_msg = f"Feature extraction failed: {str(e)}"
                    result['warnings'].append(error_msg)
                    print(f"  WARNING: {error_msg}")
                    # Continue without features
            else:
                print(f"[Step 5/6] Skipping feature extraction (LLM disabled or no text)")
                result['steps_completed'].append('feature_extraction_skipped')
            
            # Step 6: Finalize
            print(f"[Step 6/6] Finalizing...")
            result['status'] = 'success'
            result['steps_completed'].append('finalization')
            print(f"  [OK] Document processing completed successfully!")
            
            # Log performance metrics
            if self.enable_metrics and self.metrics:
                document_type = result['metadata'].get('document_type', 'unknown')
                self.metrics.log_performance(
                    operation_type="document_extraction",
                    document_type=document_type,
                    success=True,
                    details={
                        'steps_completed': len(result.get('steps_completed', [])),
                        'text_length': len(extraction_result.get('text', '')),
                        'total_tables': extraction_result.get('total_tables', 0),
                        'total_charts': extraction_result.get('total_charts', 0),
                        'has_features': 'features' in result
                    }
                )

            summary = {
                'steps_completed': result.get('steps_completed', []),
                'warnings': result.get('warnings', []),
                'errors': result.get('errors', []),
                'extraction_id': result.get('extraction_id'),
                'feature_counts': result.get('features'),
                'structure': extraction_result.get('structure'),
                'countries': extraction_result.get('structure', {}).get('countries_detected'),
                'title_information': extraction_result.get('title_information'),
                'identifiers_count': len(extraction_result.get('identifiers') or []),
                'issuer_mentions_count': len(extraction_result.get('issuer_mentions') or []),
                'country_entries_count': len(extraction_result.get('country_entries') or []),
                'performance_table_entries_count': len(extraction_result.get('performance_table_entries') or []),
                'disclaimer_matches_count': len(result['metadata'].get('disclaimer_glossary_matches', [])),
                'metadata_flags': {
                    'is_new_product': result['metadata'].get('is_new_product'),
                    'is_new_strategy': result['metadata'].get('is_new_strategy'),
                    'is_professional_client': result['metadata'].get('is_professional_client'),
                    'is_sicav_product': result['metadata'].get('is_sicav_product'),
                }
            }

            executive_summary = self._build_summary(
                metadata=result['metadata'],
                extraction_result=extraction_result,
                features_summary=result.get('features'),
                warnings=result.get('warnings')
            )
            result['executive_summary'] = executive_summary

            output_paths = self._persist_outputs(
                document_id=document_id,
                original_filename=file_path.name,
                metadata=result['metadata'],
                extraction_result=extraction_result,
                features_dump=features_dump,
                summary=summary
            )
            result['output_paths'] = output_paths

            manifest_payload = {
                "document_id": document_id,
                "original_filename": file_path.name,
                "processed_at": datetime.utcnow().isoformat() + "Z",
                "file_checksum": file_checksum,
                "paths": {
                    "manifest": str(Path(output_paths['manifest']).relative_to(self.output_dir)),
                    "metadata": str(Path(output_paths['metadata']).relative_to(self.output_dir)),
                    "extraction": str(Path(output_paths['extraction']).relative_to(self.output_dir)),
                    "features": str(Path(output_paths['features']).relative_to(self.output_dir)) if output_paths.get('features') else None,
                },
                "summary": summary,
                "executive_summary": executive_summary,
                "pipeline_version": PIPELINE_VERSION,
            }
            self._append_index_entry(manifest_payload)

            return result
            
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(str(e))
            print(f"\n[ERROR] Pipeline failed: {str(e)}")
            
            # Log error metrics
            if self.enable_metrics and self.metrics:
                document_type = result.get('metadata', {}).get('document_type', 'unknown')
                self.metrics.log_performance(
                    operation_type="document_extraction",
                    document_type=document_type,
                    success=False,
                    details={
                        'error': str(e),
                        'steps_completed': len(result.get('steps_completed', []))
                    }
                )
            
            return result
    

def process_document(
    file_path: str,
    metadata_json_path: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    use_llm: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to process a document
    
    Args:
        file_path: Path to document file
        metadata_json_path: Optional path to metadata JSON
        uploaded_by: Optional user identifier
        use_llm: Whether to use LLM for feature extraction
        
    Returns:
        Processing results dict
    """
    # Convenience wrapper: yaayet l ExtractionPipeline w yruni process_document
    pipeline = ExtractionPipeline(use_llm=use_llm)
    return pipeline.process_document(
        file_path=file_path,
        metadata_json_path=metadata_json_path,
        uploaded_by=uploaded_by
    )


if __name__ == "__main__":
    # Test with example document
    import sys
    
    test_file = "dataset/example_1/47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx"
    metadata_file = "dataset/example_1/metadata.json"
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    if len(sys.argv) > 2:
        metadata_file = sys.argv[2]
    
    if os.path.exists(test_file):
        print("="*60)
        print("Document Extraction Pipeline Test")
        print("="*60)
        
        pipeline = ExtractionPipeline(use_llm=True)
        result = pipeline.process_document(
            file_path=test_file,
            metadata_json_path=metadata_file if os.path.exists(metadata_file) else None
        )
        
        print("\n" + "="*60)
        print("Pipeline Results:")
        print("="*60)
        print(f"Status: {result['status']}")
        print(f"Document ID: {result.get('document_id')}")
        print(f"Steps Completed: {', '.join(result.get('steps_completed', []))}")
        
        if result.get('errors'):
            print(f"\nErrors: {len(result['errors'])}")
            for error in result['errors']:
                print(f"  - {error}")
        
        if result.get('warnings'):
            print(f"\nWarnings: {len(result['warnings'])}")
            for warning in result['warnings']:
                print(f"  - {warning}")
        
        if result.get('features'):
            print(f"\nFeatures Extracted:")
            for key, value in result['features'].items():
                print(f"  - {key}: {value}")
    else:
        print(f"Test file not found: {test_file}")
        print("\nUsage: python -m src.extractors.pipeline <file_path> [metadata_json_path]")

