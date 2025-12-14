# Modularization Plan for Large Files

## Overview
This document outlines the modularization strategy for breaking down large files into smaller, more maintainable modules.

## Files to Modularize

### 1. `data_consistency_agent.py` (2361 lines) [OK] IN PROGRESS
**Status**: Partially modularized

**Structure**:
- [OK] `models.py` - Data models (DataConsistencyResult)
- [OK] `validators/utils.py` - Utility functions
- [OK] `validators/issue_factory.py` - Issue creation helpers
- [OK] `validators/reference_data_utils.py` - Reference data utilities
- ⏳ `validators/source_date_validator.py` - Source/date validation
- ⏳ `validators/numerical_validator.py` - Numerical validation
- ⏳ `validators/cross_reference_validator.py` - Cross-reference validation
- ⏳ `validators/chart_validator.py` - Chart validation
- ⏳ `validators/compliance_validator.py` - Compliance rules validation
- ⏳ `data_consistency_agent.py` - Main orchestrator (refactored to use modules)

### 2. `document_extractor.py` (1134 lines) [OK] COMPLETED
**Status**: Fully modularized

**Structure**:
- [OK] `extractors/utils/text_utils.py` - Text processing utilities
- [OK] `extractors/utils/keywords.py` - Keyword definitions
- [OK] `extractors/utils/field_extractors.py` - Field extraction (title, identifiers, performance, etc.)
- [OK] `extractors/utils/ocr_utils.py` - OCR utilities
- [OK] `extractors/utils/table_extractor.py` - Table extraction logic
- [OK] `extractors/formats/pptx_extractor.py` - PowerPoint extraction
- [OK] `extractors/formats/docx_extractor.py` - Word document extraction
- [OK] `extractors/formats/pdf_extractor.py` - PDF extraction
- [OK] `document_extractor.py` - Main orchestrator (refactored to use modules, ~150 lines)

### 3. `compliance_rules.py` (1032 lines) [OK] COMPLETED
**Status**: Fully modularized

**Structure**:
- [OK] `rules/enums.py` - All enums (ClientType, DocumentType, FundType, ComplianceIssueType, etc.)
- [OK] `rules/constants.py` - Constants (RETAIL_SHARE_CLASSES, PERFORMANCE_PERIODS, etc.)
- [OK] `rules/models.py` - ComplianceIssue model
- [OK] `rules/general.py` - GeneralRules
- [OK] `rules/cover_page.py` - CoverPageRules
- [OK] `rules/slide2.py` - Slide2Rules
- [OK] `rules/content.py` - ContentRules
- [OK] `rules/esg.py` - ESGRules
- [OK] `rules/securities.py` - SecuritiesMentionRules
- [OK] `rules/performance.py` - PerformanceRules, GermanyPerformanceRules
- [OK] `rules/fund_types.py` - StrategyRules, DatedFundRules, PrivateEquityRules
- [OK] `rules/disclaimer.py` - DisclaimerRules, SimulationRules
- [OK] `rules/fund_changes.py` - FundChangesRules
- [OK] `rules/helpers.py` - Helper functions
- [OK] `rules/slide_validation.py` - SlideValidationRules
- [OK] `compliance_rules.py` - Main re-export file (~10 lines)

### 4. `esg_compliance_agent.py` (985 lines) [OK] COMPLETED
**Status**: Fully modularized

**Structure**:
- [OK] `validators/esg/models.py` - All Pydantic models (ESGLevel, ESGMentions, ImageAnalysisResult, ESGViolation, ESGComplianceOutput)
- [OK] `validators/esg/config.py` - Configuration constants and environment variables
- [OK] `validators/esg/utils.py` - Utility functions (normalize_esg_level, extract_fund_metadata_from_prospectus)
- [OK] `validators/esg/loaders.py` - DocumentLoader and MetadataLoader classes
- [OK] `validators/esg/analyzer.py` - ESGAnalyzer class (ESG level detection, mentions analysis, image analysis)
- [OK] `validators/esg/validator.py` - ESGComplianceAgent class (compliance validation logic)
- [OK] `validators/esg/reporting.py` - Report generation functions (generate_enhanced_compliance_report, save_report_as_pdf)
- [OK] `esg_compliance_agent.py` - Main re-export file (~60 lines)

### 5. `registration_parser.py` (755 lines) [OK] COMPLETED
**Status**: Fully modularized

**Structure**:
- [OK] `parsers/registration/models.py` - Pydantic models (CountryMention, FundRegistration)
- [OK] `parsers/registration/constants.py` - Country patterns and keyword definitions
- [OK] `parsers/registration/file_utils.py` - File discovery and version extraction utilities
- [OK] `parsers/registration/parser.py` - Excel parsing logic
- [OK] `parsers/registration/detector.py` - Country mention detection with context awareness
- [OK] `parsers/registration/validator.py` - Validation logic (temporal, registration status, document validation)
- [OK] `parsers/registration/registration_parser.py` - Main RegistrationParser class (~200 lines)
- [OK] `registration_parser.py` - Main re-export file (~20 lines)

## Benefits

1. **Maintainability**: Smaller files are easier to understand and modify
2. **Testability**: Individual modules can be tested in isolation
3. **Reusability**: Utility functions can be reused across modules
4. **Collaboration**: Multiple developers can work on different modules
5. **Performance**: Easier to optimize specific modules

## Migration Strategy

1. Create new modular structure
2. Extract code into new modules
3. Update imports in main file
4. Test to ensure functionality is preserved
5. Update all dependent files
6. Remove old code

## Next Steps

1. Complete modularization of `data_consistency_agent.py`
2. Modularize `document_extractor.py`
3. Modularize `compliance_rules.py`
4. Modularize remaining large files

