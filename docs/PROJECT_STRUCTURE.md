# Project Structure

Clean, organized structure with no duplicate or obsolete files.

## Root Directory Files

### Main Applications
- `app.py` - Web interface for document extraction and validation
- `app_visual.py` - Visual correction interface for document review
- `check_env_vars.py` - Environment variable validation utility
- `setup_env.py` - Environment setup script

### Configuration
- `.env` - Environment variables (API keys, configuration)
- `.gitignore` - Git ignore rules
- `requirements.txt` - Python dependencies

### Launch Scripts
- `start_web_interface.bat` - Windows launcher for web interface
- `start_web_interface.sh` - Unix/Linux launcher for web interface

## Folder Organization

### `src/` - Source Code
Main application source code with all extraction and validation modules.

**Structure:**
- `src/extractors/` - All extraction agents and processors
  - `pipeline.py` - Main extraction pipeline orchestrator
  - `document_extractor.py` - Document content extraction
  - `metadata_extractor.py` - Metadata extraction
  - `chart_analyzer.py` - Chart analysis and validation
  - `data_consistency_agent.py` - **Main validation orchestrator** (2337 lines, unified)
  - `esg_compliance_agent.py` - ESG/SFDR compliance validation
  - `disclaimer_validator.py` - Disclaimer validation
  - `registration_parser.py` - Country registration validation
  - `compliance_rules.py` - Compliance rule definitions and models
  
- `src/utils/` - Utility modules
  - `reference_data_manager.py` - Reference data loading/management
  - `metrics.py` - Metrics collection and monitoring
  - `pydantic_v1_patch.py` - Python 3.12 compatibility patch

### `tests/` - Test Suite
Complete test coverage for all modules.

**Test Files:**
- `run_all_tests.py` - Main test runner
- `test_api_connection.py` - API connectivity tests
- `test_chart_analyzer_*.py` - Chart analyzer tests
- `test_data_consistency_agent.py` - Data consistency validation tests
- `test_document_extractor_helpers.py` - Document extraction tests
- `test_integration_end_to_end.py` - End-to-end integration tests
- `test_metadata_extractor_comprehensive.py` - Metadata extraction tests
- `test_pipeline_golden.py` - Pipeline golden tests
- `test_compliance_rules.py` - Compliance rules tests
- `test_edge_cases.py` - Edge case tests
- `test_real_world_example.py` - Real-world document tests
- `test_comprehensive_esg.py` - Comprehensive ESG tests
- `test_esg_all_examples.py` - ESG example tests
- `test_esg_integration.py` - ESG integration tests
- `test_data_consistency_output.py` - Data consistency output tests

**Golden Test Data:**
- `tests/golden/` - Golden test outputs for validation

### `examples/` - Example Scripts
Working examples demonstrating system usage.

**Example Files:**
- `data_consistency_example.py` - Data consistency validation example
- `disclaimer_validation_example.py` - Disclaimer validation example
- `validation_report_example.py` - Validation report generation example
- `run_demo_pipeline.py` - Demo pipeline runner
- `run_full_pipeline_with_consistency.py` - Full pipeline with consistency checks
- `run_extraction_to_test_output.py` - Extraction with test output generation

### `scripts/` - Utility Scripts
Production utility scripts for document processing.

**Script Files:**
- `correct_document.py` - Document correction workflow
- `generate_consistency_report.py` - Consistency report generator
- `run_extraction_to_test_output.py` - Simple extraction runner

### `docs/` - Documentation
Comprehensive system documentation.

**Documentation Files:**
- `README.md` - Main documentation index
- `system_overview.md` - System architecture overview
- `system_status.md` - Current system status
- `pipeline_usage.md` - Pipeline usage guide
- `data-consistency-agent.md` - Data consistency agent documentation
- `data-consistency-usage-guide.md` - Data consistency usage guide
- `disclaimer-validation.md` - Disclaimer validation documentation
- `disclaimers_glossary_overview.md` - Disclaimers and glossary overview
- `document-correction-interface.md` - Document correction interface guide
- `document-correction-usage.md` - Document correction usage guide
- `environment_setup.md` - Environment setup instructions
- `extraction-output-cheatsheet.md` - Extraction output format reference
- `registration_abroad_of_funds_overview.md` - Registration abroad documentation
- `visual-correction-ux-design.md` - Visual correction UX design
- `chart-analyzer-improvements.md` - Chart analyzer improvements
- `data-consistency-technical-improvements.md` - Technical improvements
- `final_system_assessment.md` - Final system assessment
- `requirements_compliance_analysis.md` - Requirements compliance analysis
- `real_world_test_results.md` - Real-world test results
- `test_suite_results.md` - Test suite results
- `api_test_results.md` - API test results

### `dataset/` - Test Dataset
Test documents and reference data for validation.

**Contents:**
- `example_1/`, `example_2/`, `example_3/` - Example document directories with metadata
- `excel_analysis_summary.md` - Excel analysis summary
- `glossary_disclaimers.json` - Glossary and disclaimer reference data

### `outputs/` - Extraction Outputs
Pipeline output directory for extracted documents.

**Structure:**
- `index.jsonl` - Output index file
- `{document_id}/` - Individual document output folders

### `debug_scripts/` - Debug Utilities
Development and debugging scripts (not for production use).

**Debug Files:**
- `check_chatopenai.py` - ChatOpenAI compatibility check
- `check_types.py` - Type checking utility
- `check_unified_output.py` - Output format verification
- `debug_llm_fix.py` - LLM initialization debugging
- `debug_llm_fix_v2.py` - LLM initialization debugging (v2)
- `debug_llm_init.py` - LLM initialization testing
- `inspect_langchain.py` - LangChain inspection utility

### `test_outputs/` - Test Outputs
Test output files and artifacts.

**Contents:**
- `test_esg_output.json` - ESG test output
- `test_comprehensive_esg_output.json` - Comprehensive ESG test output
- `test_corrected.pptx` - Corrected test document

### `corrected_documents/` - Corrected Documents
Output directory for corrected documents from the visual correction interface.

### `uploads/` - Upload Directory
Temporary upload directory for web interface.

### `static/` - Static Web Assets
CSS, JavaScript, and other static web assets.

### `templates/` - Web Templates
HTML templates for web interfaces.

**Templates:**
- `index.html` - Main web interface template
- `visual_index.html` - Visual correction interface template

## Key Modules

### Data Consistency Agent
**File:** `src/extractors/data_consistency_agent.py` (2337 lines)

**Main orchestrator for all validation tasks:**
1. ✅ Source/Date validation - All tables/charts have proper attribution
2. ✅ Numerical validation - Compare against reference documents
3. ✅ Cross-reference validation - Performance text vs tables consistency
4. ✅ Compliance rules validation - All regulatory requirements
5. ✅ ESG/SFDR compliance - ESG claims validation
6. ✅ Disclaimer validation - Required disclaimer presence
7. ✅ Performance rules - 10Y/5Y history, benchmarks
8. ✅ Structure rules - Cover page, slide 2 requirements
9. ✅ Content rules - Morningstar ratings, team changes
10. ✅ Registration rules - Country authorization validation
11. ✅ Fund type rules - Dated fund, PE, ETF specific rules
12. ✅ Date recency validation - Date format and age checks

**Output:** Unified `ComplianceIssue` array with all validation results

### Pipeline Architecture
**File:** `src/extractors/pipeline.py`

**Complete extraction and validation flow:**
1. Document extraction (metadata, content, tables, charts)
2. Chart analysis (if enabled)
3. Data consistency validation
4. Disclaimer validation (if enabled)
5. ESG compliance validation (if enabled)
6. Output generation with complete results

## Recent Cleanup (December 7, 2025)

### Removed Files
- ❌ `data_consistency_agent_v2.py` - Incomplete modular version (5% complete)
- ❌ `validators/` folder - Incomplete validator modules
- ❌ `scripts/convert_issues_to_compliance.py` - Obsolete conversion script
- ❌ `docs/modular_validation_architecture.md` - Obsolete documentation

### Organized Files
- ✅ Moved all debug scripts to `debug_scripts/`
- ✅ Moved all test files to `tests/`
- ✅ Moved example scripts to `examples/`
- ✅ Moved test outputs to `test_outputs/`
- ✅ Clean root directory with only essential files

## Current Status

✅ **All 6 modules fully implemented and integrated**
1. Document Extraction
2. Disclaimer Validation
3. ESG Compliance
4. Data Consistency
5. Structure Validation
6. Registration Validation

✅ **Unified output format** - Single `ComplianceIssue` array
✅ **Complete functionality** - All 16 validation methods working
✅ **Clean codebase** - No duplicate or obsolete files
✅ **Well-organized** - Clear folder structure
✅ **Production-ready** - Tested and validated

## Development Workflow

1. **Add new features** → `src/extractors/`
2. **Write tests** → `tests/`
3. **Create examples** → `examples/`
4. **Update documentation** → `docs/`
5. **Debug issues** → `debug_scripts/` (temporary)

## Testing

Run all tests:
```bash
python tests/run_all_tests.py
```

Run specific test:
```bash
python tests/test_data_consistency_agent.py
```

## Running the Application

### Web Interface
```bash
python app.py
```
or
```bash
start_web_interface.bat  # Windows
./start_web_interface.sh  # Unix/Linux
```

### Visual Correction Interface
```bash
python app_visual.py
```

### Command-Line Pipeline
```python
from src.extractors.pipeline import ExtractionPipeline

pipeline = ExtractionPipeline(use_llm=True)
result = pipeline.process_document("path/to/document.pptx")
```

See `examples/` folder for more usage examples.
