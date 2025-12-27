"""
Comprehensive ESG Integration Test
Tests the integrated ESG analyzer with real document extraction
"""

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.extractors.core.document_extractor import DocumentExtractor  # noqa: E402
from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent  # noqa: E402
import json  # noqa: E402

# Real document extraction
doc_path = 'dataset/example_2/XXX-PRS-GB-ODDO BHF US Equity Active ETF-20250630_6PN.pptx'

def test_comprehensive_esg_integration():
    print('='*80)
    print('[TEST] COMPREHENSIVE ESG INTEGRATION TEST')
    print('='*80)
    print(f'\n[DOC] Document: {doc_path}')

    # Step 1: Extract document
    print('\n️  Step 1: Extracting document...')
    extractor = DocumentExtractor()
    extraction_result = extractor.extract(doc_path)

    # Debug: Check what's in extraction_result
    print(f'[LIST] Extraction result keys: {list(extraction_result.keys())}')

    # Get slides from correct location
    if 'slides' in extraction_result:
        slides = extraction_result['slides']
    elif 'structure' in extraction_result and 'slides' in extraction_result['structure']:
        slides = extraction_result['structure']['slides']
    else:
        slides = []

    print(f'[OK] Extracted: {len(slides)} slides')

    # Step 2: Prepare metadata
    metadata = {
        'title_information': {
            'fund_name': 'ODDO BHF US Equity Active ETF'
        },
        'fund_name': 'ODDO BHF US Equity Active ETF',
        'sfdr_article': 8,
        'esg_approach': 'Article 8 - Promotes environmental/social characteristics',
        'document_type': 'marketing',
        'client_type': 'retail',
        'fund_type': 'standard'
    }

    # Step 3: Run integrated ESG validation
    print('\n️  Step 2: Running integrated ESG validation...')
    agent = DataConsistencyAgent(
        enable_esg_validation=True,
        esg_api_key='dummy',
        esg_base_url='http://localhost:8080/v1'
    )

    result = agent.validate(extraction_result, metadata)

    # Step 4: Analyze ESG-specific issues
    esg_issues = [
        issue for issue in result.compliance_issues 
        if 'esg' in issue.issue_type.lower() or 
        'sfdr' in issue.issue_type.lower() or 
        'engaging' in issue.issue_type.lower()
    ]

    print('\n[CHART] RESULTS:')
    print(f'   Total Issues: {len(result.compliance_issues)}')
    print(f'   ESG-Specific Issues: {len(esg_issues)}')

    # Categorize by severity
    critical = [i for i in result.compliance_issues if i.severity == 'critical']
    errors = [i for i in result.compliance_issues if i.severity == 'error' or i.severity == 'high']
    warnings = [i for i in result.compliance_issues if i.severity == 'warning' or i.severity == 'low' or i.severity == 'medium']

    print(f'\n   [RED] Critical: {len(critical)}')
    print(f'   [FAIL] Errors/High: {len(errors)}')
    print(f'   [WARNING]  Warnings: {len(warnings)}')

    print('\n[SEARCH] ESG ISSUES DETAIL:')
    print('='*80)

    for i, issue in enumerate(esg_issues, 1):
        severity_emoji = {
            'critical': '[RED]',
            'high': '[FAIL]',
            'error': '[FAIL]',
            'medium': '[WARNING]',
            'warning': '[WARNING]',
            'low': 'ℹ️'
        }.get(issue.severity.lower(), '•')
        
        print(f'{severity_emoji} {i}. {issue.issue_type} ({issue.severity})')
        print(f'   {issue.message}')
        
        print(f'\n{severity_emoji} Issue #{i}: {issue.issue_type}')
        print(f'   Severity: {issue.severity.upper()}')
        print(f'   Location: {issue.location}')
        print(f'   Message: {issue.message}')
        if issue.context:
            print(f'   Context: {issue.context}')
        if issue.suggestion:
            print(f'   [IDEA] Suggestion: {issue.suggestion}')
        
        # Show details if available
        if hasattr(issue, 'details') and issue.details:
            print('   [LIST] Details:')
            for key, value in issue.details.items():
                if isinstance(value, list) and len(value) > 3:
                    print(f'      {key}: {value[:3]} ... ({len(value)} total)')
                else:
                    print(f'      {key}: {value}')

    print('\n' + '='*80)

    # Show document statistics
    print('\n[UP] DOCUMENT STATISTICS:')
    print('='*80)

    # Count text content - check structure first
    if 'structure' in extraction_result and 'slides' in extraction_result['structure']:
        structure_slides = extraction_result['structure']['slides']
        print(f'   Structure slides: {len(structure_slides)}')
    else:
        structure_slides = []
        print('   No structure.slides found')

    total_text = ""
    for slide in slides:
        if isinstance(slide, dict):
            title = slide.get('title', '')
            content_items = slide.get('content', [])
            total_text += title + " "
            for item in content_items:
                if isinstance(item, dict):
                    total_text += item.get('text', '') + " "
                else:
                    total_text += str(item) + " "
        else:
            # Slide might be a string or other format
            total_text += str(slide) + " "

    print(f'   Total Characters: {len(total_text)}')
    print(f'   Total Words: {len(total_text.split())}')
    print(f'   Total Slides: {len(slides)}')

    # ESG keyword analysis
    esg_keywords = ['ESG', 'sustainable', 'environmental', 'social', 'governance', 'durabilité']
    found_keywords = []
    for keyword in esg_keywords:
        if keyword.lower() in total_text.lower():
            count = total_text.lower().count(keyword.lower())
            found_keywords.append(f'{keyword}({count})')

    if found_keywords:
        print(f'   ESG Keywords Found: {", ".join(found_keywords)}')

    print('\n' + '='*80)
    print('[OK] COMPREHENSIVE TEST COMPLETE')
    print('='*80)

    # Save detailed output
    output_file = 'test_comprehensive_esg_output.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'document_path': doc_path,
            'total_issues': len(result.compliance_issues),
            'esg_issues': len(esg_issues),
            'severity_breakdown': {
                'critical': len(critical),
                'errors_high': len(errors),
                'warnings': len(warnings)
            },
            'all_issues': [
                {
                    'issue_type': issue.issue_type,
                    'severity': issue.severity,
                    'location': issue.location,
                    'message': issue.message,
                    'context': issue.context,
                    'suggestion': issue.suggestion,
                    'details': issue.details if hasattr(issue, 'details') else None
                }
                for issue in result.compliance_issues
            ]
        }, f, indent=2, ensure_ascii=False)

    # Assertions
    assert len(slides) > 0, "No slides extracted"
    # We expect some issues or at least a result
    assert result is not None


    print(f'\n[SAVE] Detailed results saved to: {output_file}')

