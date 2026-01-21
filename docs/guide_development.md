# Development & Development Guide

## 🛠️ Environment Setup

### Prerequisites
- **Python**: 3.12+
- **Node.js**: 18+ (for Frontend)
- **Tesseract OCR**: Required for image-based PDFs/PPTX.
- **Poppler**: Required for PDF processing.

### Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd "Advanced Ai Project"
    ```

2.  **Set up Python Environment**:
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\Activate
    # Linux/Mac
    source .venv/bin/activate
    
    pip install -r requirements.txt
    ```

3.  **Set up Frontend**:
    ```bash
    cd frontend
    npm install
    ```

### Configuration (.env)

Create a `.env` file in the root directory. **Do not commit this file.**

```env
# API Keys
TOKEN_FACTORY_API_KEY=your_key_here
TOKEN_FACTORY_BASE_URL=https://tokenfactory.esprit.tn/api
ANTHROPIC_API_KEY=your_anthropic_key  # Optional if using Claude

# System Settings
FLASK_ENV=development
DEBUG=True
PIPELINE_OUTPUT_DIR=outputs/
```

---

## 🧪 Testing

We use `pytest` for the backend.

### Running Tests
```bash
# Run all tests
python tests/run_all_tests.py

# Run specific test category
pytest tests/test_data_consistency_agent.py
```

### Test Organization

Tests are organized by functionality:

**Core Pipeline Tests:**
- **`test_pipeline_golden.py`**: Golden document tests - ensures no regression in extraction quality
- **`test_pipeline_charts.py`**: Chart extraction and analysis tests
- **`test_pipeline_utils.py`**: Pipeline utility function tests

**Validation Tests:**
- **`test_data_consistency_agent.py`**: Data consistency agent logic tests
- **`test_data_consistency_output.py`**: Output format validation tests
- **`test_compliance_rules.py`**: Compliance rule validation tests
- **`test_validator_output.py`**: Validator output format tests

**ESG Tests:**
- **`test_comprehensive_esg.py`**: Comprehensive ESG validation tests
- **`test_esg_all_examples.py`**: ESG tests across all example documents
- **`test_esg_integration.py`**: ESG integration tests

**API Tests:**
- **`test_api.py`**: Core API endpoint tests
- **`test_api_smoke_test_client.py`**: Smoke tests for API client
- **`test_fix_endpoint_ci.py`**: Document correction endpoint tests

**Extraction Tests:**
- **`test_metadata_extractor_comprehensive.py`**: Comprehensive metadata extraction tests
- **`test_document_extractor_helpers.py`**: Document extraction helper tests
- **`test_enhanced_registration.py`**: Registration parser tests

**Edge Cases:**
- **`test_edge_cases.py`**: Edge case handling tests
- **`test_refactor.py`**: Refactoring validation tests
- **`test_coverage_additions.py`**: Additional coverage tests

### Running Tests

```bash
# Run all tests
python tests/run_all_tests.py

# Run specific test file
pytest tests/test_pipeline_golden.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run specific test category
pytest tests/test_*esg*.py -v
```

---

## 🚀 Production Deployment

### Deployment Strategy
The system is designed to be deployed as two separate services:
1.  **Backend (Flask)**: Dockerized Python application.
2.  **Frontend (Next.js)**: Static export or Node.js server.

### Docker Deployment

**Dockerfile (Backend Equivalent)**
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y tesseract-ocr poppler-utils
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "api:app"]
```

### Performance Tuning

**LLM Caching:**
- Enabled by default via `backend/utils/cache/llm_cache.py`
- Responses cached in `.cache/llm/` directory
- Reduces API costs and speeds up reprocessing
- Cache key based on prompt + model parameters

**Concurrency:**
- **Workers**: Adjust Gunicorn workers based on CPU cores (`2 * Cores + 1`)
- **Threading**: API endpoints are thread-safe
- **Processing**: Documents processed sequentially to avoid memory issues

**Memory Management:**
- Minimum 4GB RAM recommended
- Large PDFs with charts may require 8GB+
- File streaming for large uploads
- Automatic cleanup of temporary files

**Optimization Tips:**
- Use `use_llm=False` for faster processing (no semantic analysis)
- Process documents in batches during off-peak hours
- Monitor `.cache/` directory size and clean periodically
- Use `enable_esg=False` if ESG validation not needed

### Monitoring

**Logging:**
- Application logs written to stdout/stderr
- Log level configurable via `FLASK_ENV` and `DEBUG` env vars
- Structured logging for production (JSON format recommended)

**Health Checks:**
- `GET /api/v1/health`: Returns system status and version
- Monitor response time and error rates
- Check disk space for upload/output folders

**Metrics:**
- `backend/utils/metrics/core.py`: Tracks API usage and validation metrics
- Metrics include:
  - API call counts
  - Token usage and costs
  - Validation success rates
  - Processing times
  - Error rates

**Debugging:**
- Enable `DEBUG=True` for detailed error messages
- Check `outputs/<document_id>/` for intermediate results
- Use `/api/v1/debug/jobs` endpoint to inspect job state
- Review logs for LLM API errors or timeouts
