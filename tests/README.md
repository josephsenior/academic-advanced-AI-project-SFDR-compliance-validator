# Test Suite Documentation

This directory contains the comprehensive test suite for the Document Compliance Validation System.

## Test Organization

Tests are organized by functionality and component:

### Core Pipeline Tests
- **`test_pipeline_golden.py`**: Golden document tests - ensures no regression in extraction quality against known-good documents
- **`test_pipeline_charts.py`**: Chart extraction and analysis tests using vision models
- **`test_pipeline_utils.py`**: Pipeline utility function tests

### Validation Tests
- **`test_data_consistency_agent.py`**: Data consistency agent logic and rule validation tests
- **`test_data_consistency_output.py`**: Output format and structure validation tests
- **`test_compliance_rules.py`**: Compliance rule implementation tests
- **`test_validator_output.py`**: Validator output format and structure tests

### ESG Tests
- **`test_comprehensive_esg.py`**: Comprehensive ESG validation tests covering Article 8/9 scenarios
- **`test_esg_all_examples.py`**: ESG tests across all example documents in dataset
- **`test_esg_integration.py`**: ESG integration tests with full pipeline

### API Tests
- **`test_api.py`**: Core API endpoint tests (upload, validate, status, results)
- **`test_api_smoke_test_client.py`**: Smoke tests for API client integration
- **`test_fix_endpoint_ci.py`**: Document correction endpoint tests

### Extraction Tests
- **`test_metadata_extractor_comprehensive.py`**: Comprehensive metadata extraction tests
- **`test_document_extractor_helpers.py`**: Document extraction helper function tests
- **`test_enhanced_registration.py`**: Registration parser and country validation tests

### Edge Cases & Quality
- **`test_edge_cases.py`**: Edge case handling tests (empty documents, malformed files, etc.)
- **`test_refactor.py`**: Refactoring validation tests to ensure behavior preservation
- **`test_coverage_additions.py`**: Additional coverage tests for less-tested code paths

## Running Tests

### Run All Tests
```bash
# Using the test runner script
python tests/run_all_tests.py

# Using pytest directly
pytest tests/ -v

# With coverage report
pytest tests/ --cov=backend --cov-report=html
```

### Run Specific Test Categories
```bash
# Run only pipeline tests
pytest tests/test_pipeline*.py -v

# Run only validation tests
pytest tests/test_data_consistency*.py tests/test_compliance_rules.py -v

# Run only ESG tests
pytest tests/test_*esg*.py -v

# Run only API tests
pytest tests/test_api*.py -v
```

### Run Individual Test Files
```bash
# Run specific test file
pytest tests/test_pipeline_golden.py -v

# Run specific test function
pytest tests/test_pipeline_golden.py::test_example_1 -v

# Run with detailed output
pytest tests/test_pipeline_golden.py -v -s
```

## Test Requirements

### Environment Setup
Tests require:
- Python 3.12+
- All dependencies from `requirements.txt`
- Environment variables configured (see `.env.example`)
- Test dataset files in `dataset/` directory

### Test Data
Tests use sample documents from the `dataset/` directory:
- `example_1/`: Sample presentation with known-good extraction results
- `example_2/`: Additional test cases
- `example_3/`: Complex scenarios with multiple validation checks

### API Tests
API tests require the Flask server to be running:
```bash
# In one terminal, start the server
python api.py

# In another terminal, run API tests
pytest tests/test_api.py -v
```

## Test Coverage Goals

- **Core Pipeline**: >90% coverage
- **Validators**: >85% coverage
- **API Endpoints**: >80% coverage
- **Edge Cases**: Comprehensive coverage of error paths

## Writing New Tests

### Test Structure
```python
import pytest
from backend.extractors.pipeline import ExtractionPipeline

def test_feature_name():
    """Test description explaining what is being tested."""
    # Arrange
    pipeline = ExtractionPipeline()
    test_file = "path/to/test/document.pptx"
    
    # Act
    result = pipeline.process_document(test_file)
    
    # Assert
    assert result['status'] == 'success'
    assert 'extraction_result' in result
```

### Best Practices
1. **Descriptive Names**: Use clear, descriptive test function names
2. **Arrange-Act-Assert**: Follow AAA pattern for test structure
3. **Isolation**: Each test should be independent and not rely on others
4. **Fixtures**: Use pytest fixtures for common setup/teardown
5. **Assertions**: Use specific assertions with helpful error messages
6. **Documentation**: Add docstrings explaining test purpose

### Example Test
```python
def test_disclaimer_validation_for_article_8_fund():
    """Test that Article 8 funds require ESG risk disclaimer."""
    # Arrange
    validator = DisclaimerValidator()
    extraction = {
        'metadata': {'fund_type': 'Article 8'},
        'content': {'text': 'ESG-focused investment strategy'}
    }
    
    # Act
    issues = validator.validate(extraction)
    
    # Assert
    esg_issues = [i for i in issues if 'ESG' in i.category]
    assert len(esg_issues) > 0, "Article 8 funds must have ESG disclaimer"
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- All tests should pass without manual intervention
- No external dependencies beyond what's in requirements.txt
- Tests clean up after themselves (no persistent side effects)
- API tests can run against mock server if needed

## Troubleshooting

### Common Issues

**Import Errors:**
- Ensure you're running tests from project root
- Check that `backend/` is in Python path
- Verify virtual environment is activated

**API Test Failures:**
- Ensure Flask server is running on port 5000
- Check that no other process is using the port
- Verify environment variables are set

**Golden Test Failures:**
- May indicate legitimate changes in extraction logic
- Review changes carefully before updating golden files
- Ensure test data files exist in `dataset/` directory

**LLM API Errors:**
- Check `TOKEN_FACTORY_API_KEY` is set
- Verify API endpoint is accessible
- Some tests may require valid API credentials

## Test Maintenance

- **Update Golden Tests**: When extraction logic changes, update golden test expectations
- **Add New Tests**: Add tests for new features or bug fixes
- **Review Coverage**: Regularly check test coverage and add tests for uncovered areas
- **Refactor Tests**: Keep tests maintainable and remove duplication
