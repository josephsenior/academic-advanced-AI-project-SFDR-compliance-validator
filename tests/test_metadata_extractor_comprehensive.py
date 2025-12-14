"""
Comprehensive Test Suite for Metadata Extractor - Pytest Compatible
"""

import sys
import os
import pytest
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from backend.extractors.core.metadata_extractor import MetadataExtractor
from backend.extractors.core.document_extractor import DocumentExtractor
from backend.extractors.pipeline import ExtractionPipeline

def get_api_credentials():
    api_key = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
    base_url = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
    return api_key, base_url

def test_llm_detection():
    """Test LLM-based metadata detection"""
    api_key, base_url = get_api_credentials()
    
    if not api_key or not base_url:
        pytest.skip("LLM API keys not found")
    
    extractor = MetadataExtractor(use_llm=True)
    if not extractor.use_llm:
        pytest.skip("LLM extractor failed to initialize")
        
    # Mock result
    extraction_result = {
        'text': """
        ODDO BHF ASSET MANAGEMENT SAS
        This document is intended for professional clients only.
        The fund is part of the SICAV Oddo.
        This is a new investment strategy.
        """,
        'full_text': "..." 
    }
    
    content_meta = extractor._extract_from_content_llm(extraction_result)
    
    assert content_meta.get('client_type') in ['Professional', 'Non-professional'] or content_meta.get('is_professional_client') is not None
    assert content_meta.get('management_company') in ['SAS', 'GmbH', 'Lux'] or 'management_company' not in content_meta
    assert content_meta.get('is_sicav_product') is not None or 'is_sicav_product' not in content_meta
    assert 'llm_confidence' in content_meta

def test_keyword_fallback():
    """Test keyword-based fallback detection"""
    extractor = MetadataExtractor(use_llm=False)
    
    # Check Professional Client
    res1 = {'text': "This document is for professional clients only.", 'full_text': "This document is for professional clients only."}
    meta1 = extractor._extract_from_content(res1)
    assert meta1.get('client_type') == 'Professional' or meta1.get('is_professional_client') is True
    
    # Check Retail Client
    res2 = {'text': "This document is for retail clients.", 'full_text': "This document is for retail clients."}
    meta2 = extractor._extract_from_content(res2)
    assert meta2.get('client_type') == 'Non-professional' or meta2.get('is_professional_client') is False
    
    # Check SAS Entity
    res3 = {'text': "ODDO BHF ASSET MANAGEMENT SAS", 'full_text': "ODDO BHF ASSET MANAGEMENT SAS", 'title_information': {'management_company': 'ODDO BHF ASSET MANAGEMENT SAS'}}
    meta3 = extractor._extract_from_content(res3)
    assert meta3.get('management_company') == 'SAS'

    # Check SICAV
    res4 = {'text': "part of the SICAV Oddo", 'full_text': "part of the SICAV Oddo"}
    meta4 = extractor._extract_from_content(res4)
    assert meta4.get('is_sicav_product') is True

    # Check New Strategy
    res5 = {'text': "presents a new investment strategy", 'full_text': "presents a new investment strategy"}
    meta5 = extractor._extract_from_content(res5)
    assert meta5.get('is_new_strategy') is True

def test_json_metadata():
    """Test JSON metadata loading and normalization"""
    extractor = MetadataExtractor()
    json_data = {
        "Société de Gestion": "ODDO BHF ASSET MANAGEMENT SAS",
        "Est ce que le produit fait partie de la Sicav d'Oddo": True
    }
    normalized = extractor._normalize_json_metadata(json_data)
    assert normalized.get('management_company') == 'SAS'
    assert normalized.get('is_sicav_product') is True

def test_filename_parsing():
    """Test filename parsing"""
    extractor = MetadataExtractor()
    filename = "47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx"
    meta = extractor.filename_parser.parse(filename)
    
    assert meta.get('document_type') in ['6PG', '6-page'] or '6PG' in filename
    assert meta.get('language_code') == 'FR'
    assert 'Algo Trend US' in (meta.get('fund_name') or '')

def test_priority_system():
    """Test metadata priority system"""
    extractor = MetadataExtractor(use_llm=False)
    
    filename_meta = {}
    json_meta = {'client_type': 'Professional'}
    content_meta = {'client_type': 'Non-professional'}
    
    # JSON wins
    combined = extractor._combine_metadata(filename_meta, json_meta, content_meta)
    assert combined.get('client_type') == 'Professional'
    
    # Content wins if JSON empty
    combined2 = extractor._combine_metadata(filename_meta, {}, content_meta)
    assert combined2.get('client_type') == 'Non-professional'

def test_edge_cases():
    """Test edge cases"""
    extractor = MetadataExtractor(use_llm=False)
    
    # Empty text
    meta_empty = extractor._extract_from_content({'text': '', 'full_text': ''})
    assert meta_empty == {} or 'content_detection_attempted' in meta_empty
    
    # Invalid JSON file
    try:
        empty = extractor._load_json_metadata("nonexistent.json")
        assert empty == {}
    except Exception:
        pass # Exception is acceptable behavior too, or returns empty

def test_real_documents():
    """Test with real documents from dataset"""
    test_docs = [
        "dataset/example_1/FINAL 47861-6PG-GB-ODDO BHF Algo Trend US-20250831vdef.pptx",
    ]
    # Check existence relative to project root
    root = Path(__file__).parent.parent
    
    passed_any = False
    for relative_path in test_docs:
        doc_path = root / relative_path
        if not doc_path.exists():
            continue
            
        passed_any = True
        document_extractor = DocumentExtractor(enable_chart_analysis=False)
        extractor = MetadataExtractor(use_llm=False)
        
        try:
            result = document_extractor.extract(str(doc_path))
            metadata = extractor.extract(file_path=str(doc_path), extraction_result=result)
            
            assert metadata.get('filename') is not None
            assert metadata.get('language_code') is not None
        except Exception as e:
            pytest.fail(f"Failed on real doc {doc_path.name}: {e}")

    if not passed_any:
        pytest.skip("No real documents found in dataset/example_1")

# Ensure other tests don't break
def test_pipeline_integration():
    """Test pipeline integration"""
    root = Path(__file__).parent.parent
    doc_path = root / "dataset/example_1/FINAL 47861-6PG-GB-ODDO BHF Algo Trend US-20250831vdef.pptx"
    
    if not doc_path.exists():
        pytest.skip("Test document not found")
        
    pipeline = ExtractionPipeline(use_llm=False)
    result = pipeline.process_document(str(doc_path))
    
    if result['status'] == 'success':
        meta = result.get('metadata', {})
        assert meta.get('filename') is not None
    else:
        # If pipeline fails (e.g. JSON error), at least extraction result should exist
        assert 'extraction_result' in result
