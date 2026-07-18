# Document Compliance Validation System

**AI-powered autonomous compliance reviews for proper financial documentation.**

This system uses Generative AI (Llama 3.1 & LLaVA) to automatically validate marketing documents against complex regulatory rules (SFDR, ESG, Cross-border registration).

## Demo

<video src="https://github.com/josephsenior/academic-advanced-AI-project-SFDR-compliance-validator/raw/refs/heads/main/assets/demo.mp4" controls width="100%">
  Your browser does not support embedded video. [Download the demo](assets/demo.mp4).
</video>

> Product walkthrough of the Document Compliance Validation System.

## 📚 Documentation

**[Enter the Documentation Hub](docs/index.md)**

- **[Architecture](docs/architecture.md)**: How the backend/frontend and AI agents work together.
- **[User Guide](docs/guide_usage.md)**: How to run the pipeline and use the dashboard.
- **[Development](docs/guide_development.md)**: Setup, testing, and deployment.
- **[API Reference](docs/api_reference.md)**: Endpoints for the REST API.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- Node.js 18+ (for UI)
- Tesseract OCR (for image extraction)

### 2. Setup
```bash
# Clone and Install
git clone <repo>
cd "Advanced Ai Project"
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\Activate on Windows
pip install -r requirements.txt

# Configure Env
cp .env.example .env
# Edit .env with your API Keys
```

### 3. Run
**Windows**:
```batch
start_web_interface.bat
```

**Linux/Mac**:
```bash
./start_web_interface.sh
```

- **Dashboard**: http://localhost:3000
- **API**: http://localhost:5000

## 📁 Project Structure

```
Advanced Ai Project/
├── api.py                    # Flask API entry point
├── backend/                  # Core Python Application
│   ├── extractors/           # Extraction & Validation Logic
│   │   ├── core/            # Document, chart, feature extractors
│   │   ├── pipeline/        # Pipeline orchestrator
│   │   ├── validators/      # Compliance validators (15+ validators)
│   │   ├── agents/          # Data consistency agent
│   │   ├── parsers/         # Filename & registration parsers
│   │   └── rules/           # Compliance rules engine
│   ├── server/               # Flask API Server
│   │   ├── routes/v1/       # REST API endpoints
│   │   ├── services/        # Business logic services
│   │   └── config.py        # API configuration
│   ├── utils/                # Utilities (metrics, caching, reporting)
│   └── evaluation/          # Evaluation metrics
├── frontend/                 # Next.js Dashboard (React 19, Tailwind CSS)
├── server/                   # Flask application (legacy, use api.py)
├── docs/                     # Complete Documentation
│   ├── index.md             # Documentation hub
│   ├── architecture.md     # System architecture
│   ├── guide_usage.md       # User guide
│   ├── guide_development.md # Development guide
│   ├── features.md           # Validation rules & features
│   └── api_reference.md     # Complete API documentation
├── tests/                    # Comprehensive Test Suite
│   ├── README.md            # Test documentation
│   ├── test_pipeline_*.py    # Pipeline tests
│   ├── test_data_consistency*.py  # Validation tests
│   ├── test_esg_*.py        # ESG compliance tests
│   ├── test_api*.py         # API endpoint tests
│   └── run_all_tests.py     # Test runner
├── examples/                 # Example scripts
├── scripts/                  # Utility scripts
├── dataset/                  # Test datasets & reference data
└── outputs/                  # Generated outputs (gitignored)
```

## License
Proprietary - Internal use only.
