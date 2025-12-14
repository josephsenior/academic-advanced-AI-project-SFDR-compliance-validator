# System Overview

**Status**: [OK] **PRODUCTION-READY**  
**Last Updated**: Current

## Quick Summary

This system automates compliance validation for financial marketing documents using AI/LLM technology. It extracts data from documents (PPTX, DOCX, PDF), validates compliance rules, and checks for required disclaimers and registrations.

## Core Capabilities

### Document Processing
- [OK] Multi-format support (PPTX, DOCX, PDF)
- [OK] Text, table, and chart extraction
- [OK] Metadata extraction (from filename + JSON)
- [OK] Performance data extraction
- [OK] Source/date detection
- [OK] Country and issuer detection

### Chart Analysis
- [OK] LLM-based chart/graph analysis (LLaVA)
- [OK] Data point extraction from visualizations
- [OK] Performance value extraction from charts
- [OK] Source/date extraction from charts

### Compliance Validation
- [OK] **Data Consistency**: Source/date validation, numerical validation, cross-reference checks
- [OK] **Disclaimer Validation**: 15+ disclaimer types, Excel glossary integration, multi-language support
- [OK] **Registration Validation**: Country registration checks via Excel parser

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

- **ExtractionPipeline** (`backend/extractors/pipeline.py`) - Main orchestrator
- **DocumentExtractor** (`backend/extractors/document_extractor.py`) - Content extraction
- **ChartAnalyzer** (`backend/extractors/chart_analyzer.py`) - Chart/graph analysis
- **DataConsistencyAgent** (`backend/extractors/data_consistency_agent.py`) - Data validation
- **DisclaimerValidator** (`backend/extractors/disclaimer_validator.py`) - Disclaimer validation
- **RegistrationParser** (`backend/extractors/registration_parser.py`) - Country registration validation

## Usage

See [pipeline_usage.md](pipeline_usage.md) for detailed usage instructions.

## Documentation

- **[system_status.md](system_status.md)** - Current system status and integration details
- **[final_system_assessment.md](final_system_assessment.md)** - Comprehensive assessment
- **[requirements_compliance_analysis.md](requirements_compliance_analysis.md)** - Requirements compliance

