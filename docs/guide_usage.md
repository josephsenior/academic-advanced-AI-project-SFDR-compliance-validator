# User Guide

## 🚀 Quick Start

### 1. Start the System
The easiest way to run the full system (Backend + Frontend) is using the launch script:

```bash
# Windows
start_web_interface.bat

# Linux/Mac
./start_web_interface.sh
```

- **Backend API**: Runs on `http://localhost:5000`
- **Frontend UI**: Runs on `http://localhost:3000`

### 2. Using the Web Dashboard
1.  Navigate to `http://localhost:3000`.
2.  **Upload**: Drag and drop your PPTX, PDF, or DOCX file.
3.  **Wait**: The pipeline will show "Extracting" -> "Validating".
4.  **Review**: Click on the completed document to see the **Validation Report**.
5.  **Correct**: Use the "Correct" tab to apply auto-fixes to validatable issues.

---

## 💻 Command Line Interface (CLI)

You can run the extraction pipeline directly from the terminal for batch processing or debugging.

### Basic Usage

```python
from backend.extractors.pipeline import ExtractionPipeline

# Initialize pipeline
pipeline = ExtractionPipeline()

# Process a document
result = pipeline.process_document("dataset/example_1/my_presentation.pptx")

if result.get('status') == 'success' or 'extraction_result' in result:
    print(f"Document processed successfully")
    print(f"Extraction result: {result.get('extraction_result', {})}")
else:
    print("Processing failed.")
```

### Using the API Programmatically

```python
import requests

# Upload document
with open("document.pptx", "rb") as f:
    response = requests.post(
        "http://localhost:5000/api/v1/upload",
        files={"document": f}
    )
    data = response.json()
    document_id = data["document_id"]

# Start validation
response = requests.post(
    f"http://localhost:5000/api/v1/validate/{document_id}",
    json={"options": {"use_llm": True, "enable_disclaimers": True}}
)

# Check status
response = requests.get(f"http://localhost:5000/api/v1/status/{document_id}")
status = response.json()
print(f"Status: {status['status']}, Progress: {status['progress']}%")

# Get results
response = requests.get(f"http://localhost:5000/api/v1/results/{document_id}")
results = response.json()
print(f"Compliance Score: {results['compliance_score']}")
print(f"Total Issues: {results['total_issues']}")
```

---

## 📊 Understanding Results

Outputs are stored in `outputs/<document_id>/`.

### Key Output Files

Outputs are stored in `outputs/<document_id>/`:

- **`extraction.json`**: Raw extracted content including:
  - Text from all slides/pages
  - Tables with structured data
  - Chart data points (from vision analysis)
  - Slide/page metadata
  - Document structure

- **`validation_result.json`**: The core compliance report containing:
  - `compliance_score`: Overall compliance score (0-100)
  - `total_issues`: Total number of issues found
  - `issues_by_category`: Issues grouped by category:
    - `disclaimer`: Missing or incorrect disclaimers
    - `consistency`: Data inconsistencies (text vs. tables vs. charts)
    - `registration`: Country registration violations
    - `esg`: ESG/SFDR compliance issues
    - `formatting`: Visual formatting issues
    - `content`: Content validation issues
  - `metadata`: Detected document metadata
  - `extraction_summary`: Summary of extracted content

- **`report.html`** / **`report.pdf`**: Human-readable validation reports (generated via API)

### Issue Severity Levels
- **CRITICAL**: Blocking compliance violation (e.g., Unregistered country, Missing Article 8 statements).
- **HIGH**: Major data inconsistency (text says +5%, table says +3%).
- **MEDIUM**: Formatting or non-critical styling issues.
- **LOW**: Suggestions or minor warnings.

---

## 🔧 Configuration

### Configuration

**Environment Variables** (configure in `.env` file):
- `TOKEN_FACTORY_API_KEY`: Required - API key for LLM services
- `TOKEN_FACTORY_BASE_URL`: Required - Base URL for Token Factory API
- `LLM_MODEL_NAME`: Optional - Text model (default: `hosted_vllm/Llama-3.1-70B-Instruct`)
- `LLM_VISION_MODEL`: Optional - Vision model (default: `hosted_vllm/llava-1.5-7b-hf`)
- `FLASK_ENV`: Optional - Flask environment (default: `development`)
- `DEBUG`: Optional - Enable debug mode (default: `True`)

**API Configuration** (via `server/config.py`):
- `max_content_length_bytes`: Maximum upload size (default: 100MB)
- `upload_folder`: Upload directory (default: `uploads/`)
- `output_folder`: Output directory (default: `outputs/`)
- `corrected_folder`: Corrected documents directory (default: `corrected_documents/`)

### Large Documents

The pipeline automatically handles large documents:
- Text is chunked for LLM processing
- Charts are processed in batches
- Memory-efficient file streaming

If you encounter memory issues:
1. Reduce document size or split into smaller files
2. Disable LLM features (`use_llm=False` in validation options)
3. Increase system memory allocation
4. Process documents sequentially rather than in parallel
