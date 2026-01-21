
import sys
import os

import logging

# Add project root to path
sys.path.append(os.getcwd())

from backend.extractors.core.document_extractor import DocumentExtractor
from backend.extractors.validators.content import ContentValidator
from backend.extractors.validators.performance import PerformanceValidator
from backend.extractors.validators.disclaimer import DisclaimerValidator
from backend.extractors.validators.fund_type import FundTypeValidator
from backend.extractors.validators.country import CountryValidator
from backend.extractors.validators.esg_compliance import EsgValidator
from backend.extractors.rules.enums import ClientType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_file(file_path):
    print(f"Validating file: {file_path}")
    
    # 1. Extract
    extractor = DocumentExtractor()
    extraction_result = extractor.extract(file_path)
    
    # 2. Validate
    validators = [
        ContentValidator(),
        PerformanceValidator(),
        DisclaimerValidator(),
        FundTypeValidator(),
        CountryValidator(),
        EsgValidator()
    ]
    
    all_issues = []
    for validator in validators:
        issues = validator.validate(
            extraction_result, 
            client_type=ClientType.RETAIL
        )
        all_issues.extend(issues)
        
    print(f"\nTotal Issues Found: {len(all_issues)}")
    print("-" * 50)
    
    issue_types = [issue.issue_type for issue in all_issues]
    for i, issue in enumerate(all_issues, 1):
        print(f"{i}. [{issue.issue_type}] - Slide {issue.slide_number} - {issue.location}")
        
    return issue_types

if __name__ == "__main__":
    file_path = "dataset/example_3/3 - FINAL CLEAN-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx"
    validate_file(file_path)
