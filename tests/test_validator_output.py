#!/usr/bin/env python3
"""Test what the validator returns"""

import pytest
from pathlib import Path
from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent
import json

def test_validator_output():
    """Test validator output format and structure"""
    agent = DataConsistencyAgent()
    
    # Check if test data exists, skip if not
    extraction_path = Path('outputs/full_pipeline_test/extraction.json')
    metadata_path = Path('dataset/example_3/metadata.json')
    
    if not extraction_path.exists():
        pytest.skip(f"Test data not found: {extraction_path}. Run run_full_pipeline.py first to generate test data.")
    
    if not metadata_path.exists():
        pytest.skip(f"Metadata file not found: {metadata_path}")
    
    with open(extraction_path, encoding='utf-8') as f:
        extraction = json.load(f)

    with open(metadata_path, encoding='utf-8') as f:
        metadata = json.load(f)

    result = agent.validate(extraction, metadata)

    # Assertions
    assert hasattr(result, 'compliance_issues'), "Result should have compliance_issues attribute"
    assert isinstance(result.compliance_issues, list), "compliance_issues should be a list"
    
    print(f"Validation result type: {type(result)}")
    print(f"Has compliance_issues: {hasattr(result, 'compliance_issues')}")
    print(f"compliance_issues count: {len(result.compliance_issues)}")
    
    if result.compliance_issues:
        print("\nFirst 3 issues:")
        for i, issue in enumerate(result.compliance_issues[:3], 1):
            print(f"{i}. [{issue.severity}] {issue.issue_type}: {issue.message}")
