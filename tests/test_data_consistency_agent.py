"""
Tests for Data Consistency Agent
"""

import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.data_consistency_agent import (
    DataConsistencyAgent,
    ReferenceData,
    SourceDateIssue,
    NumericalInconsistency,
    DataConsistencyResult
)


def test_source_date_validation():
    """Test source and date validation"""
    print("=" * 60)
    print("Test 1: Source and Date Validation")
    print("=" * 60)
    
    # Mock extraction result with tables
    extraction_result = {
        'tables': [
            {
                'slide_number': 2,
                'table_index': 1,
                'data': [['Fund', '10%'], ['Benchmark', '8%']]
            },
            {
                'slide_number': 3,
                'table_index': 1,
                'data': [['Performance', '15%']]
            },
            {
                'slide_number': 4,
                'table_index': 1,
                'data': [['Data', '20%']]
            }
        ],
        'table_sources': [
            {
                'slide_number': 2,
                'source_name': 'Bloomberg',
                'source_date': '2025-08-31',
                'raw_note': 'Source: Bloomberg 2025-08-31'
            },
            {
                'slide_number': 3,
                'source_name': 'Bloomberg',
                'source_date': None,  # Missing date
                'raw_note': 'Source: Bloomberg'
            }
            # Slide 4 has no source entry - will be flagged
        ],
        'performance_sections': [],
        'performance_table_entries': []
    }
    
    agent = DataConsistencyAgent(reference_data=None)
    result = agent.validate(extraction_result)
    
    print(f"\nOverall Status: {result.overall_status}")
    print(f"Total Tables Checked: {result.total_tables_checked}")
    print(f"Tables with Source+Date: {result.tables_with_source_date}")
    print(f"Tables Missing Source/Date: {result.tables_missing_source_date}")
    print(f"\nIssues Found: {len(result.source_date_issues)}")
    
    for issue in result.source_date_issues:
        print(f"  - [{issue.severity.upper()}] {issue.message}")
    
    print("\nSummary:")
    for msg in result.summary:
        print(f"  {msg}")
    
    assert result.total_tables_checked == 3
    assert result.tables_with_source_date == 1
    assert result.tables_missing_source_date == 2
    assert len(result.source_date_issues) >= 2
    print("\nSUCCESS: Test 1 passed!\n")


def test_numerical_validation():
    """Test numerical data validation"""
    print("=" * 60)
    print("Test 2: Numerical Data Validation")
    print("=" * 60)
    
    # Create reference data
    reference_data = ReferenceData(
        fund_name="Test Fund",
        performance_data={
            "1y": {"net": 10.5, "gross": 12.0},
            "3y": {"net": 8.2},
            "ytd": {"net": 8.3}
        },
        table_data={
            "fund": 10.5,
            "benchmark": 8.0
        },
        source_document="Prospectus"
    )
    
    # Mock extraction result with performance data
    extraction_result = {
        'tables': [],
        'table_sources': [],
        'performance_sections': [
            {
                'slide_number': 2,
                'entries': [
                    {
                        'sentence': 'Net performance 1Y: 10.5%',
                        'value': 10.5,
                        'period': '1y',
                        'basis': 'net',
                        'benchmark': None
                    },
                    {
                        'sentence': 'Net performance 3Y: 8.5%',  # Mismatch: should be 8.2%
                        'value': 8.5,
                        'period': '3y',
                        'basis': 'net',
                        'benchmark': None
                    },
                    {
                        'sentence': 'YTD performance: 8.3%',
                        'value': 8.3,
                        'period': 'ytd',
                        'basis': 'net',
                        'benchmark': None
                    }
                ]
            }
        ],
        'performance_table_entries': [
            {
                'label': 'Fund',
                'column': '1Y',
                'value': 10.5,
                'raw': '10.5%',
                'slide_number': 3,
                'table_index': 1
            },
            {
                'label': 'Benchmark',
                'column': '1Y',
                'value': 8.0,
                'raw': '8.0%',
                'slide_number': 3,
                'table_index': 1
            }
        ]
    }
    
    agent = DataConsistencyAgent(reference_data=reference_data)
    result = agent.validate(extraction_result)
    
    print(f"\nOverall Status: {result.overall_status}")
    print(f"Total Values Checked: {result.total_numerical_values_checked}")
    print(f"Values Matching: {result.values_matching_reference}")
    print(f"Values with Inconsistencies: {result.values_with_inconsistencies}")
    print(f"\nInconsistencies Found: {len(result.numerical_inconsistencies)}")
    
    for inc in result.numerical_inconsistencies:
        print(f"  - [{inc.severity.upper()}] {inc.message}")
    
    print("\nSummary:")
    for msg in result.summary:
        print(f"  {msg}")
    
    assert result.total_numerical_values_checked > 0
    assert result.values_matching_reference >= 3  # 10.5%, 8.3%, 10.5%, 8.0% should match
    assert result.values_with_inconsistencies >= 1  # 8.5% vs 8.2% should be flagged
    print("\nSUCCESS: Test 2 passed!\n")


def test_integration_with_golden_fixture():
    """Test with golden fixture data"""
    print("=" * 60)
    print("Test 3: Integration with Golden Fixture")
    print("=" * 60)
    
    # Load golden fixture
    fixture_path = Path(__file__).parent / "golden" / "extraction_fixture.json"
    if not fixture_path.exists():
        print(f"WARNING: Golden fixture not found at {fixture_path}")
        print("   Skipping integration test")
        return
    
    with open(fixture_path, 'r', encoding='utf-8') as f:
        extraction_result = json.load(f)
    
    # Create reference data based on fixture
    reference_data = ReferenceData(
        fund_name="ODDO Algo",
        performance_data={
            "1y": {"net": 10.0}  # Matches fixture value
        },
        table_data={
            "fund": 10.0,
            "benchmark": 8.0
        },
        source_document="Prospectus"
    )
    
    agent = DataConsistencyAgent(reference_data=reference_data)
    result = agent.validate(extraction_result)
    
    print(f"\nOverall Status: {result.overall_status}")
    print(f"Source/Date Issues: {len(result.source_date_issues)}")
    print(f"Numerical Inconsistencies: {len(result.numerical_inconsistencies)}")
    
    print("\nIssues:")
    for issue in result.source_date_issues:
        print(f"  - {issue.message}")
    
    print("\nInconsistencies:")
    for inc in result.numerical_inconsistencies:
        print(f"  - {inc.message}")
    
    print("\nSummary:")
    for msg in result.summary:
        print(f"  {msg}")
    
    print("\nSUCCESS: Test 3 passed!\n")


def test_reference_data_creation():
    """Test creating reference data from dictionary"""
    print("=" * 60)
    print("Test 4: Reference Data Creation")
    print("=" * 60)
    
    from src.extractors.data_consistency_agent import create_reference_data_from_dict
    
    data = {
        'fund_name': 'Test Fund',
        'isin': 'FR0012345678',
        'performance_data': {
            '1Y': {'net': 10.5, 'gross': 12.0},
            '3Y': {'net': 8.2}
        },
        'table_data': {
            'fund': 10.5,
            'benchmark': 8.0
        },
        'reference_date': '2025-08-31',
        'source_document': 'Prospectus'
    }
    
    ref_data = create_reference_data_from_dict(data)
    
    print(f"Fund Name: {ref_data.fund_name}")
    print(f"ISIN: {ref_data.isin}")
    print(f"Performance Data: {ref_data.performance_data}")
    print(f"Table Data: {ref_data.table_data}")
    print(f"Source Document: {ref_data.source_document}")
    
    assert ref_data.fund_name == 'Test Fund'
    assert ref_data.isin == 'FR0012345678'
    assert '1Y' in ref_data.performance_data
    assert ref_data.performance_data['1Y']['net'] == 10.5
    
    print("\nSUCCESS: Test 4 passed!\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Data Consistency Agent Tests")
    print("=" * 60 + "\n")
    
    try:
        test_source_date_validation()
        test_numerical_validation()
        test_integration_with_golden_fixture()
        test_reference_data_creation()
        
        print("=" * 60)
        print("SUCCESS: All tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\nERROR: Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

