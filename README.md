# Document Compliance Validation System

Advanced AI-powered document validation system for financial compliance checking with ESG validation, disclaimer verification, and regulatory requirement validation.

## Quick Start

### Backend API Server
```bash
# Start the API server (runs on port 5000)
start_web_interface.bat
```

### Frontend Dashboard
```bash
cd compliance-dashboard
pnpm install
pnpm dev
# Opens on http://localhost:3000
```

## System Architecture

### Backend (Python)
- **API Server**: Flask REST API (`api.py`) on port 5000
- **Extractors**: Document processing pipeline in `src/extractors/`
- **Utilities**: Helper functions in `src/utils/`
- **Tests**: Comprehensive test suite in `tests/`

### Frontend (Next.js)
- **Dashboard**: React/Next.js UI in `compliance-dashboard/`
- **Port**: 3000 (development)
- **Features**: Upload documents, view validation results, manage compliance

### Data
- **Dataset**: Reference data in `dataset/`
  - Registration abroad of Funds (82 funds, 21 countries)
  - Disclaimer Glossary (3 languages)
  - Compliance rules
- **Outputs**: Validation results in `outputs/`
- **Uploads**: User uploaded documents in `uploads/`

## Features

- Document Upload (3-file support)
  - Main document (required): .pptx, .pdf, .docx
  - Metadata (optional): metadata.json
  - Prospectus (optional): Reference document for performance validation

- Automated Validation
  - ESG compliance checking
  - Disclaimer verification (multilingual)
  - Performance data validation
  - Country-specific registration rules
  - Structure and formatting checks

- Interactive Dashboard
  - Real-time validation status
  - Detailed compliance reports
  - Issue categorization and severity
  - Document correction interface

## Documentation

All documentation is in the `docs/` folder:

- **System Overview**: `docs/system_overview.md`
- **API Documentation**: `docs/API_DOCUMENTATION.md`
- **Pipeline Usage**: `docs/pipeline_usage.md`
- **Environment Setup**: `docs/environment_setup.md`
- **Frontend Quick Start**: `docs/frontend_quick_start.md`

## Environment Variables

Required environment variables (set in `.env`):
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Tech Stack

### Backend
- Python 3.12
- Flask (REST API)
- Anthropic Claude (LLM processing)
- openpyxl, python-pptx (document processing)

### Frontend
- Next.js 16.0.7
- React 19
- TypeScript
- Tailwind CSS
- shadcn/ui components
- SWR for data fetching

## Project Structure

```
Advanced Ai Project/
├── api.py                    # Main API server
├── setup_env.py             # Environment setup script
├── start_web_interface.bat  # Start script (Windows)
├── start_web_interface.sh   # Start script (Unix)
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
├── compliance-dashboard/    # Frontend Next.js app
├── src/                     # Python source code
│   ├── extractors/          # Document processing
│   └── utils/               # Helper utilities
├── tests/                   # Test suite
├── dataset/                 # Reference data
├── docs/                    # Documentation
├── outputs/                 # Validation results
└── uploads/                 # Uploaded documents
```

## License

Proprietary - Internal use only
