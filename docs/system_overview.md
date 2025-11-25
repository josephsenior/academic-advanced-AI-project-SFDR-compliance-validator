# System Overview

**Status**: ✅ **PRODUCTION-READY**  
**Last Updated**: Current

## Quick Summary

This system automates compliance validation for financial marketing documents using AI/LLM technology. It extracts data from documents (PPTX, DOCX, PDF), validates compliance rules, and checks for required disclaimers and registrations.

## Core Capabilities

### Document Processing
- ✅ Multi-format support (PPTX, DOCX, PDF)
- ✅ Text, table, and chart extraction
- ✅ Metadata extraction (from filename + JSON)
- ✅ Performance data extraction
- ✅ Source/date detection
- ✅ Country and issuer detection

### Chart Analysis
- ✅ LLM-based chart/graph analysis (LLaVA)
- ✅ Data point extraction from visualizations
- ✅ Performance value extraction from charts
- ✅ Source/date extraction from charts

### Compliance Validation
- ✅ **Data Consistency**: Source/date validation, numerical validation, cross-reference checks
- ✅ **Disclaimer Validation**: 15+ disclaimer types, Excel glossary integration, multi-language support
- ✅ **Registration Validation**: Country registration checks via Excel parser

## System Architecture

```
Document → ExtractionPipeline → DataConsistencyAgent → Validation Results
                ↓
         DocumentExtractor
         ├─ Text/Table Extraction
         ├─ Chart Analyzer (LLM)
         └─ Feature Extraction (optional LLM)
                ↓
         DisclaimerValidator
         RegistrationParser
```

## Key Modules

- **ExtractionPipeline** (`src/extractors/pipeline.py`) - Main orchestrator
- **DocumentExtractor** (`src/extractors/document_extractor.py`) - Content extraction
- **ChartAnalyzer** (`src/extractors/chart_analyzer.py`) - Chart/graph analysis
- **DataConsistencyAgent** (`src/extractors/data_consistency_agent.py`) - Data validation
- **DisclaimerValidator** (`src/extractors/disclaimer_validator.py`) - Disclaimer validation
- **RegistrationParser** (`src/extractors/registration_parser.py`) - Country registration validation

## Usage

See [pipeline_usage.md](pipeline_usage.md) for detailed usage instructions.

## Documentation

- **[system_status.md](system_status.md)** - Current system status and integration details
- **[final_system_assessment.md](final_system_assessment.md)** - Comprehensive assessment
- **[requirements_compliance_analysis.md](requirements_compliance_analysis.md)** - Requirements compliance

