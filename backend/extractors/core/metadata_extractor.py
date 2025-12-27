"""
Metadata Extraction Module
Extracts metadata from JSON files, filename parsing, and document content
Uses LLM for intelligent content-based detection when available
Combines all sources for complete metadata
"""

import json
import os
import sys
# Note: pydantic v1 compatibility handled centrally when needed
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


def _import_pydantic_output_parser():
    """Import PydanticOutputParser from whichever langchain package is available.

    This centralises the import to avoid defining the same name multiple times
    in different function scopes which can trigger mypy `no-redef` errors.
    """
    import importlib
    try:
        mod = importlib.import_module("langchain_core.output_parsers")
    except Exception:
        mod = importlib.import_module("langchain.output_parsers")
    return getattr(mod, "PydanticOutputParser")

from ..parsers.filename_parser import FilenameParser  # noqa: E402


class MetadataDetectionResult(BaseModel):
    """Structured result from LLM-based metadata detection"""
    client_type: Optional[str] = Field(None, description="'Professional' or 'Non-professional' or None")
    is_professional_client: Optional[bool] = Field(None, description="True if professional, False if non-professional, None if unknown")
    management_company: Optional[str] = Field(None, description="'SAS', 'GmbH', 'Lux', or None")
    management_company_full: Optional[str] = Field(None, description="Full management company name")
    is_sicav_product: Optional[bool] = Field(None, description="True if product is part of SICAV Oddo, False if not, None if unknown")
    is_new_strategy: Optional[bool] = Field(None, description="True if document references new strategy, False otherwise, None if unknown")
    is_new_product: Optional[bool] = Field(None, description="True if document references new product, False otherwise, None if unknown")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence in detection (0-1)")


class MetadataExtractor:
    """Extract and combine metadata from JSON files and filename"""
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize metadata extractor
        
        Args:
            use_llm: Whether to use LLM for content-based metadata detection (default: True)
        """
        # Houni ninitializiw FilenameParser bach nparsi filenames
        self.filename_parser = FilenameParser()
        self.use_llm = use_llm
        self.llm_metadata_extractor = None
        
        if use_llm:
            try:
                from ..config.llm_config import get_token_factory_config
                config = get_token_factory_config()
                self.llm_metadata_extractor = self._create_llm_extractor(config)
            except Exception as e:
                print(f"Warning: LLM metadata extraction not available: {e}")
                print("Falling back to keyword-based detection...")
                self.use_llm = False
    
    def extract(
        self, 
        file_path: str, 
        metadata_json_path: Optional[str] = None,
        extraction_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract metadata from filename, JSON file, and document content
        
        Args:
            file_path: Path to the document file
            metadata_json_path: Optional path to metadata.json file (if None, searches in same directory)
            extraction_result: Optional extraction result from DocumentExtractor (for content-based detection)
            
        Returns:
            Combined metadata dictionary
        """
        # Ynajjem yakhedh file_path, yparsi filename w yakhedh metadata men JSON
        file_path = Path(file_path)
        filename = file_path.name
        
        # Extract from filename
        filename_metadata = self.filename_parser.parse(filename)
        
        # Extract from JSON file
        json_metadata = {}
        if metadata_json_path:
            json_metadata = self._load_json_metadata(metadata_json_path)
        else:
            # Try to find metadata.json in same directory
            json_path = file_path.parent / "metadata.json"
            if json_path.exists():
                json_metadata = self._load_json_metadata(str(json_path))
        
        # Extract from document content (if extraction result provided)
        content_metadata = {}
        if extraction_result:
            # Try LLM-based detection first (more accurate)
            if self.use_llm and self.llm_metadata_extractor:
                try:
                    content_metadata = self._extract_from_content_llm(extraction_result)
                    content_metadata['detection_method'] = 'llm'
                except Exception as e:
                    print(f"Warning: LLM metadata detection failed: {e}")
                    print("Falling back to keyword-based detection...")
                    # Fall back to keyword-based detection
                    content_metadata = self._extract_from_content(extraction_result)
                    content_metadata['detection_method'] = 'keyword'
            else:
                # Use keyword-based detection
                content_metadata = self._extract_from_content(extraction_result)
                content_metadata['detection_method'] = 'keyword'
        
        # ycombini metadata (JSON takes precedence, then content, then filename fills gaps)
        combined_metadata = self._combine_metadata(filename_metadata, json_metadata, content_metadata)
        
        # Add file information
        combined_metadata['file_path'] = str(file_path)
        combined_metadata['filename'] = filename
        combined_metadata['file_directory'] = str(file_path.parent)
        combined_metadata['extracted_at'] = datetime.now().isoformat()
        
        return combined_metadata
    
    def _load_json_metadata(self, json_path: str) -> Dict[str, Any]:
        # Y7el metadata.json w ynormalizi w yrajja3 {} ken fama error
        """Load metadata from JSON file"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return self._normalize_json_metadata(data)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON metadata file {json_path}: {e}")
            return {}
    
    def _normalize_json_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize JSON metadata to standard format
        
        Expected JSON structure:
        {
            "Société de Gestion": "ODDO BHF ASSET MANAGEMENT SAS",
            "Est ce que le produit fait partie de la Sicav d'Oddo": true/false,
            "Le client est-il un professionnel": true/false,
            "Le document fait-il référence à une nouvelle Stratégie": true/false,
            "Le document fait-il référence à un nouveau Produit": true/false
        }
        """
        # Ynormalizi structure ta3 JSON bach tmatchi schema mta3na
        normalized = {}
        
        # Management company
        management_company = data.get("Société de Gestion", "")
        if management_company:
            # Extract company type (SAS, GmbH, Lux)
            if "SAS" in management_company:
                normalized['management_company'] = "SAS"
                normalized['management_company_full'] = management_company
            elif "GmbH" in management_company:
                normalized['management_company'] = "GmbH"
                normalized['management_company_full'] = management_company
            elif "Lux" in management_company or "Luxembourg" in management_company:
                normalized['management_company'] = "Lux"
                normalized['management_company_full'] = management_company
            else:
                normalized['management_company'] = "Unknown"
                normalized['management_company_full'] = management_company
        
        # Sicav product flag
        sicav_keys = [
            "Est ce que le produit fait partie de la Sicav d'Oddo",
            "Est ce que le produit fait partie de la Sicav luxembourgeoise ",
            "is_sicav"
        ]
        for key in sicav_keys:
            if key in data:
                normalized['is_sicav_product'] = bool(data[key])
                break
        
        # Client type (professional vs non-professional)
        client_type_key = "Le client est-il un professionnel"
        if client_type_key in data:
            is_professional = bool(data[client_type_key])
            normalized['is_professional_client'] = is_professional
            normalized['client_type'] = 'Professional' if is_professional else 'Non-professional'
        
        # New strategy flag
        new_strategy_keys = ["Le document fait-il référence à une nouvelle Stratégie", "is_new_strategy"]
        for key in new_strategy_keys:
            if key in data:
                normalized['is_new_strategy'] = bool(data[key])
                break
        
        # New product flag
        new_product_keys = ["Le document fait-il référence à un nouveau Produit", "is_new_product"]
        for key in new_product_keys:
            if key in data:
                normalized['is_new_product'] = bool(data[key])
                break
        
        # Store raw JSON for reference
        normalized['raw_json_metadata'] = data
        
        return normalized
    
    def _create_llm_extractor(self, config: Dict[str, Any]):
        """Create LLM-based metadata extractor using LangChain"""
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            import httpx

            # Disable SSL verification for self-signed certificates
            _http_client = httpx.Client(verify=False)
            _http_async_client = httpx.AsyncClient(verify=False)

            llm = ChatOpenAI(
                model=config['model_name'],
                api_key=(lambda: config['api_key']),
                base_url=config['base_url'],
                temperature=0.0
            )
            # Manually set clients to bypass validation issues in langchain-openai 0.0.2
            # llm.http_client = http_client
            # llm.http_async_client = http_async_client

            parser = _import_pydantic_output_parser()(pydantic_object=MetadataDetectionResult)
            
            template = """You are an expert in analyzing financial marketing documents for compliance purposes.

Your task is to extract specific metadata from the document text that is required for compliance validation.

**Extract the following metadata:**

1. **Client Type**:
   - Determine if the document targets "Professional" clients or "Non-professional" (retail) clients
   - Look for explicit mentions like "professional clients", "retail clients", "investisseurs professionnels", "grand public"
   - Consider the document type and language used
   - Return: "Professional", "Non-professional", or None if unclear

2. **Management Company Entity Type**:
   - Find mentions of "ODDO BHF Asset Management" or "ODDO BHF AM"
   - Determine the entity type: "SAS" (French), "GmbH" (German), or "Lux" (Luxembourg)
   - Extract the full company name if available
   - Return: "SAS", "GmbH", "Lux", or None if not found

3. **SICAV Involvement**:
   - Determine if the product/fund is part of the SICAV Oddo
   - Look for phrases like "part of the SICAV", "fait partie de la SICAV", "SICAV product"
   - Consider context: positive mentions (is part of) vs negative (not part of)
   - Return: True if part of SICAV, False if explicitly not, None if unclear

4. **New Strategy**:
   - Check if document references a new investment strategy
   - Look for phrases like "new strategy", "nouvelle stratégie", "new approach"
   - Return: True if new strategy mentioned, False otherwise, None if unclear

5. **New Product**:
   - Check if document references a new product/fund
   - Look for phrases like "new product", "nouveau produit", "new fund", "new offering"
   - Return: True if new product mentioned, False otherwise, None if unclear

**Important:**
- Be accurate and conservative - only return True/False if you're confident
- Return None if the information is not clearly stated in the document
- Consider the document language (English, French, German)
- Provide confidence score based on how clear the information is

**Document Text:**
{document_text}

**Format Instructions:**
{format_instructions}
"""
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | llm | parser
            
            return chain
            
        except Exception as e:
            raise Exception(f"Failed to create LLM extractor: {e}")
    
    def _extract_from_content_llm(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from document content using LLM (more accurate)
        
        Args:
            extraction_result: Result from DocumentExtractor.extract()
            
        Returns:
            Dictionary with detected metadata from content
        """
        if not self.llm_metadata_extractor:
            return {}
        
        # Get full text for analysis (limit to first 8000 chars for efficiency)
        full_text = extraction_result.get('full_text', '') or extraction_result.get('text', '')
        if not full_text:
            return {}
        
        # Use first part of document (usually contains metadata in title/header)
        # Also include title_info if available
        text_to_analyze = full_text[:8000]
        title_info = extraction_result.get('title_information', {})
        if isinstance(title_info, dict) and title_info:
            title_text = " ".join([f"{k}: {v}" for k, v in title_info.items() if v])
            text_to_analyze = title_text + "\n\n" + text_to_analyze
        
        try:
            # Get format instructions from parser (needed for prompt template)
            # The parser is already created in _create_llm_extractor, but we need format_instructions here
            parser = _import_pydantic_output_parser()(pydantic_object=MetadataDetectionResult)
            format_instructions = parser.get_format_instructions()
            
            # Call LLM with both required variables
            result = self.llm_metadata_extractor.invoke({
                "document_text": text_to_analyze,
                "format_instructions": format_instructions
            })
            
            # Convert to dict
            content_meta = {}
            if result.client_type:
                content_meta['client_type'] = result.client_type
                content_meta['is_professional_client'] = result.is_professional_client
            
            if result.management_company:
                content_meta['management_company'] = result.management_company
                if result.management_company_full:
                    content_meta['management_company_full'] = result.management_company_full
            
            if result.is_sicav_product is not None:
                content_meta['is_sicav_product'] = result.is_sicav_product
            
            if result.is_new_strategy is not None:
                content_meta['is_new_strategy'] = result.is_new_strategy
            
            if result.is_new_product is not None:
                content_meta['is_new_product'] = result.is_new_product
            
            content_meta['llm_confidence'] = result.confidence
            content_meta['content_detection_attempted'] = True
            
            return content_meta
            
        except Exception as e:
            # If LLM fails, fall back to keyword-based detection and return that result.
            print(f"LLM metadata extraction error: {e}")
            try:
                # Ensure we prefer the `text` field for keyword fallback when full_text is a placeholder
                fallback_input = dict(extraction_result)
                txt = extraction_result.get('text') or ''
                # If full_text is missing or obviously placeholder like '...', prefer 'text'
                if not fallback_input.get('full_text') or fallback_input.get('full_text') == '...':
                    fallback_input['full_text'] = txt
                fallback = self._extract_from_content(fallback_input)
            except Exception:
                fallback = {}
            # Mark confidence low and that detection was attempted
            fallback['llm_confidence'] = 0.0
            fallback['content_detection_attempted'] = True
            return fallback
    
    def _extract_from_content(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from document content (text, title fields, etc.)
        
        Args:
            extraction_result: Result from DocumentExtractor.extract()
            
        Returns:
            Dictionary with detected metadata from content
        """
        content_meta = {}
        
        # Get full text for analysis
        full_text = extraction_result.get('full_text', '') or extraction_result.get('text', '')
        if not full_text:
            return content_meta
        
        text_lower = full_text.lower()
        
        # 1. Client Type Detection
        # Check for explicit mentions of professional/retail clients
        if not content_meta.get('client_type'):
            if any(keyword in text_lower for keyword in [
                'professional client', 'clients professionnels', 'professionnel',
                'professional investors', 'investisseurs professionnels'
            ]):
                content_meta['client_type'] = 'Professional'
                content_meta['is_professional_client'] = True
            elif any(keyword in text_lower for keyword in [
                'retail client', 'clients de détail', 'grand public',
                'non-professional', 'non professional', 'non-professionnel',
                'retail investors', 'investisseurs particuliers'
            ]):
                content_meta['client_type'] = 'Non-professional'
                content_meta['is_professional_client'] = False
        
        # Also check title_info if available (from DocumentExtractor)
        title_info = extraction_result.get('title_information', {})
        if isinstance(title_info, dict):
            title_client_type = title_info.get('client_type')
            if title_client_type and not content_meta.get('client_type'):
                if title_client_type == 'professional':
                    content_meta['client_type'] = 'Professional'
                    content_meta['is_professional_client'] = True
                elif title_client_type == 'retail':
                    content_meta['client_type'] = 'Non-professional'
                    content_meta['is_professional_client'] = False
        
        # 2. Entity Type Detection (SAS/GmbH/Lux)
        # Check for management company mentions
        management_company_text = None
        
        # First check title_info
        if isinstance(title_info, dict):
            management_company_text = title_info.get('management_company')
        
        # If not found, search in full text
        if not management_company_text:
            import re
            mgmt_patterns = [
                r'ODDO\s+BHF\s+ASSET\s+MANAGEMENT\s+(SAS|GmbH|Lux)',
                r'ODDO\s+BHF\s+AM\s+(SAS|GmbH|Lux)',
                r'ODDO\s+BHF\s+ASSET\s+MANAGEMENT\s+(S\.A\.S\.|GmbH|Luxembourg)',
            ]
            for pattern in mgmt_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    management_company_text = match.group(0)
                    break
        
        if management_company_text:
            mgmt_upper = management_company_text.upper()
            if 'SAS' in mgmt_upper or 'S.A.S.' in mgmt_upper:
                content_meta['management_company'] = 'SAS'
                content_meta['management_company_full'] = management_company_text
            elif 'GMBH' in mgmt_upper:
                content_meta['management_company'] = 'GmbH'
                content_meta['management_company_full'] = management_company_text
            elif 'LUX' in mgmt_upper or 'LUXEMBOURG' in mgmt_upper:
                content_meta['management_company'] = 'Lux'
                content_meta['management_company_full'] = management_company_text
        
        # 3. SICAV Involvement Detection
        # Check for mentions of SICAV Oddo
        sicav_keywords = [
            'sicav oddo', 'sicav d\'oddo', 'oddo sicav',
            'part of the sicav', 'fait partie de la sicav',
            'sicav product', 'produit sicav'
        ]
        if any(keyword in text_lower for keyword in sicav_keywords):
            # Try to determine if it's positive or negative
            # Look for context around SICAV mentions
            import re
            sicav_context_pattern = r'.{0,100}(?:sicav|SICAV).{0,100}'
            sicav_matches = re.findall(sicav_context_pattern, text_lower, re.IGNORECASE)
            
            is_sicav = False
            for match in sicav_matches:
                # Positive indicators
                if any(pos in match for pos in [
                    'part of', 'fait partie', 'included', 'inclus',
                    'belongs to', 'appartient', 'yes', 'oui'
                ]):
                    is_sicav = True
                    break
                # Negative indicators
                elif any(neg in match for neg in [
                    'not part', 'ne fait pas partie', 'not included',
                    'not a', 'n\'est pas', 'no', 'non'
                ]):
                    is_sicav = False
                    break
                # Default: if mentioned, assume yes (conservative)
                else:
                    is_sicav = True
            
            content_meta['is_sicav_product'] = is_sicav
        
        # 4. New Strategy/Product Detection (already done in disclaimer detection, but add here too)
        # Check for new strategy/product mentions
        new_strategy_keywords = [
            'new strategy', 'nouvelle stratégie', 'new approach',
            'new investment strategy', 'nouvelle approche'
        ]
        if any(keyword in text_lower for keyword in new_strategy_keywords):
            content_meta['is_new_strategy'] = True
        
        new_product_keywords = [
            'new product', 'nouveau produit', 'new fund',
            'new offering', 'nouvelle offre'
        ]
        if any(keyword in text_lower for keyword in new_product_keywords):
            content_meta['is_new_product'] = True
        
        # Mark that content-based detection was attempted
        content_meta['content_detection_attempted'] = True
        
        return content_meta
    
    def _combine_metadata(
        self, 
        filename_meta: Dict[str, Any], 
        json_meta: Dict[str, Any],
        content_meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Combine metadata from filename and JSON
        JSON takes precedence, filename fills gaps
        """
        # Ycombine metadata: JSON toma precedence, filename yemla li majhouz
        combined = {}
        
        # Document ID - prefer filename, fallback to JSON if available
        combined['document_id_extracted'] = filename_meta.get('document_id_extracted')
        
        # Document type - prefer filename
        combined['document_type'] = filename_meta.get('document_type')
        
        # Language - prefer filename (more accurate for filenames), but JSON can override
        combined['language_code'] = filename_meta.get('language_code') or json_meta.get('language_code')
        
        # Fund name - prefer filename, but JSON might have it
        combined['fund_name'] = filename_meta.get('fund_name') or json_meta.get('fund_name')
        
        # Date - prefer filename
        combined['date_extracted'] = filename_meta.get('date_extracted')
        if combined['date_extracted']:
            combined['date_extracted'] = str(combined['date_extracted'])  # Convert to string for JSON
        
        # Version - from filename only
        combined['version_number'] = filename_meta.get('version_number')
        combined['version_type'] = filename_meta.get('version_type')
        combined['status_extracted'] = filename_meta.get('status_extracted')
        
        # Parsing confidence - from filename
        combined['filename_parsing_confidence'] = filename_meta.get('parsing_confidence', 0.0)
        
        # Management company - JSON takes precedence, then content, then Unknown
        combined['management_company'] = (
            json_meta.get('management_company') or 
            (content_meta or {}).get('management_company') or 
            'Unknown'
        )
        combined['management_company_full'] = (
            json_meta.get('management_company_full') or 
            (content_meta or {}).get('management_company_full')
        )
        
        # Flags - JSON takes precedence, then content detection, then defaults
        combined['is_sicav_product'] = (
            json_meta.get('is_sicav_product') 
            if 'is_sicav_product' in json_meta 
            else (content_meta or {}).get('is_sicav_product', False)
        )
        combined['is_professional_client'] = (
            json_meta.get('is_professional_client')
            if 'is_professional_client' in json_meta
            else (content_meta or {}).get('is_professional_client', False)
        )
        combined['client_type'] = (
            json_meta.get('client_type') or 
            (content_meta or {}).get('client_type') or 
            'Unknown'
        )
        combined['is_new_strategy'] = (
            json_meta.get('is_new_strategy')
            if 'is_new_strategy' in json_meta
            else (content_meta or {}).get('is_new_strategy', False)
        )
        combined['is_new_product'] = (
            json_meta.get('is_new_product')
            if 'is_new_product' in json_meta
            else (content_meta or {}).get('is_new_product', False)
        )
        
        # Track metadata sources
        combined['has_content_metadata'] = bool(content_meta and content_meta.get('content_detection_attempted'))
        
        # Raw metadata for reference
        combined['raw_json_metadata'] = json_meta.get('raw_json_metadata', {})
        combined['raw_filename_metadata'] = filename_meta
        
        # Metadata source flags
        combined['has_json_metadata'] = bool(json_meta.get('raw_json_metadata'))
        combined['has_filename_metadata'] = bool(filename_meta.get('parsing_confidence', 0) > 0)
        
        return combined
    
    def extract_from_directory(self, directory_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract metadata for all documents in a directory
        
        Args:
            directory_path: Path to directory containing documents and metadata.json
            
        Returns:
            Dict mapping filename to metadata
        """
        # Yruni extract 3la documents lkol fi directory (ysearchi metadata.json)
        directory = Path(directory_path)
        results = {}
        
        # Find metadata.json
        metadata_json_path = directory / "metadata.json"
        json_metadata_path = str(metadata_json_path) if metadata_json_path.exists() else None
        
        # Find all document files
        document_extensions = ['.pptx', '.docx', '.pdf']
        for ext in document_extensions:
            for doc_file in directory.glob(f'*{ext}'):
                metadata = self.extract(str(doc_file), json_metadata_path)
                results[doc_file.name] = metadata
        
        return results


def extract_metadata(
    file_path: str, 
    metadata_json_path: Optional[str] = None,
    extraction_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    # Convenience function: yaayet l MetadataExtractor w yreturni extract result
    """Convenience function to extract metadata"""
    extractor = MetadataExtractor()
    return extractor.extract(file_path, metadata_json_path, extraction_result)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # Test with example files
    test_files = [
        "dataset/example_1/47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx",
        "dataset/example_2/FINAL-PRS-GB-ODDO BHF US Equity Active ETF-20250630_8PN_clean.pptx",
        "dataset/example_3/1 - V1-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx"
    ]
    
    extractor = MetadataExtractor()
    
    print("="*80)
    print("Metadata Extraction Test")
    print("="*80)
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\nFile: {os.path.basename(test_file)}")
            print("-"*80)
            
            metadata = extractor.extract(test_file)
            
            print(f"Document ID: {metadata.get('document_id_extracted')}")
            print(f"Document Type: {metadata.get('document_type')}")
            print(f"Language: {metadata.get('language_code')}")
            print(f"Fund Name: {metadata.get('fund_name')}")
            print(f"Date: {metadata.get('date_extracted')}")
            print(f"Version: {metadata.get('version_number')} ({metadata.get('version_type')})")
            print(f"\nManagement Company: {metadata.get('management_company')} ({metadata.get('management_company_full')})")
            print(f"Client Type: {metadata.get('client_type')}")
            print(f"Is Professional: {metadata.get('is_professional_client')}")
            print(f"Is Sicav Product: {metadata.get('is_sicav_product')}")
            print(f"Is New Strategy: {metadata.get('is_new_strategy')}")
            print(f"Is New Product: {metadata.get('is_new_product')}")
            print(f"\nHas JSON Metadata: {metadata.get('has_json_metadata')}")
            print(f"Has Filename Metadata: {metadata.get('has_filename_metadata')}")
            print(f"Filename Parsing Confidence: {metadata.get('filename_parsing_confidence', 0):.2f}")
        else:
            print(f"\nERROR: File not found: {test_file}")

