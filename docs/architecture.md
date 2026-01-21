# System Architecture

**Status**: [OK] **PRODUCTION-READY**

## System Overview

The **Document Compliance Validation System** is an AI-powered pipeline designed to automate compliance reviews for financial marketing documents. It validates documents against complex regulatory rules (SFDR, ESG, Cross-border registration) using a hybrid approach of heuristic algorithms and Generative AI.

### Core Architecture

```mermaid
graph TD
    User[User / Client] -->|Upload PPTX/PDF| API[REST API (Flask)]
    API -->|Queue| Pipeline[Extraction Pipeline]
    
    subgraph "Backend (Python)"
        Pipeline -->|1. Extract| DocExt[Document Extractor]
        Pipeline -->|2. Analyze| Chart[Chart Analyzer (LLaVA)]
        Pipeline -->|3. Feature| LLM[LLM Feature Extractor (Llama)]
        Pipeline -->|4. Validate| DC[Data Consistency Agent]
        
        DocExt -->|Text/Tables| Parsing
        Chart -->|Data Points| parsing
        LLM -->|Metadata/Claims| Validation
        
        DC -->|Validate| Compliance[Compliance Rules]
        DC -->|Verify| Disclaimer[Disclaimer Validator]
        DC -->|Check| Reg[Registration Parser]
    end
    
    Pipeline -->|JSON Result| Output[Output Artifacts]
    Output -->|Read| Dashboard[Next.js Dashboard]
```

## Project Structure

The codebase is organized into a clear separation between Backend (Python/Flask) and Frontend (Next.js).

### Root Directory
- **`api.py`**: Main entry point for the Backend REST API.
- **`setup_env.py`**: Scripts to initialize the development environment.
- **`start_web_interface.bat/.sh`**: Helper scripts to launch the full stack.

### Backend (`backend/`)

The backend is organized into three main modules: `extractors/`, `server/`, and `utils/`.

#### `extractors/` - Core Extraction & Validation Logic

**Core Extractors** (`core/`):
- **`document_extractor.py`**: Handles parsing of PPTX, PDF, and DOCX files. Extracts text, tables, and slide metadata.
- **`chart_analyzer.py`**: Uses Vision LLMs (LLaVA) to interpret charts and graphs, extracting data points and labels.
- **`feature_extractor.py`**: Uses LLM (Llama 3.1) to extract high-level features like ESG claims, fund codes, and performance metrics.
- **`metadata_extractor.py`**: Infers metadata from file content, naming conventions, and document structure.

**Pipeline** (`pipeline/`):
- **`orchestrator.py`**: The central orchestrator (`ExtractionPipeline`). Manages the complete lifecycle from document upload to validation results.

**Validators** (`validators/`):
- **`disclaimer.py`**: Checks for presence and correctness of legal disclaimers (15+ types).
- **`esg_compliance.py`**: Validates ESG/SFDR compliance (Article 8/9 classification).
- **`performance.py`**: Validates performance claims and data consistency.
- **`country.py`**: Validates country-specific requirements.
- **`content.py`**: Content validation and formatting checks.
- **`fund_type.py`**: Validates fund type classifications.
- **`visual_formatting.py`**: Checks visual formatting requirements.
- **`visual_prominence.py`**: Validates visual prominence of disclaimers.
- **`translation_consistency.py`**: Ensures consistency across translations.
- **`dynamic_prospectus.py`**: Validates against prospectus documents.

**Agents** (`agents/`):
- **`data_consistency_agent.py`**: The primary validation agent. Runs 16+ validation checks including:
  - Numerical accuracy (text vs. tables vs. charts)
  - Date recency checks
  - Source attribution
  - Cross-reference validation
  - Prospectus comparison
- **`validators/`**: Specialized validators for charts, cross-references, numerical data, and source dates.

**Parsers** (`parsers/`):
- **`filename_parser.py`**: Extracts metadata from filenames.
- **`registration/`**: Validates fund distribution rights against country databases.

**Document Processing**:
- **`document_corrector.py`**: Applies automatic corrections to documents based on validation results.
- **`document_family.py`**: Detects document family types (presentation, prospectus, etc.).

#### `server/` - Flask API Server

- **`app.py`**: Flask application factory and initialization.
- **`config.py`**: API configuration (upload limits, folder paths, etc.).
- **`constants.py`**: API constants (allowed file types, validation statuses).
- **`store.py`**: In-memory job store for tracking document processing.
- **`serialization.py`**: JSON serialization helpers for datetime and complex types.
- **`services/validation_service.py`**: Service layer for running validation pipeline.
- **`routes/v1/`**: REST API endpoints:
  - `upload.py`: Document upload
  - `validate.py`: Start validation
  - `status.py`: Get processing status
  - `results.py`: Get validation results
  - `fix.py`: Apply document corrections
  - `download.py`: Download original/corrected documents
  - `report.py`: Generate reports (JSON/HTML/PDF)
  - `list_delete.py`: List and delete documents
  - `health.py`: Health check endpoint

#### `utils/` - Utilities

- **`metrics/`**: System telemetry and performance tracking.
- **`cache/llm_cache.py`**: LLM response caching to reduce costs.
- **`matching/text_matcher.py`**: Text matching utilities for validation.
- **`reference_data_manager/`**: Loads external truth sources (Excel glossaries, registration databases).
- **`reporting/validation_report_generator.py`**: Generates HTML/PDF reports.
- **`rendering/slide_renderer.py`**: Slide rendering utilities.
- **`processing/parallel_processor.py`**: Parallel processing utilities.

### Frontend (`frontend/`)
A generic modern web dashboard built with **Next.js 16**, **React 19**, and **Tailwind CSS**.
- **Features**: Document upload, real-time status tracking, interactive correction interface, and report viewing.

### Data & Resources
- **`dataset/`**: Reference datasets (e.g., `GLOSSAIRE DISCLAIMERS.xlsx`, `Registration abroad.xlsx`) and golden test samples.
- **`outputs/`**: Generated artifacts for processed documents (JSON, corrected files).
- **`uploads/`**: Temporary storage for incoming files.

## Data Flow

1.  **Ingestion**: File is uploaded via API. SHA-256 checksum is generated to prevent duplicate processing.
2.  **Extraction**:
    - Text and tables are parsed using standard libraries (python-pptx, pdf2image).
    - Charts are converted to images and their data points extracted via Vision LLM.
3.  **Analysis**:
    - LLM (Llama 3.1) extracts high-level features (ESG claims, Fund codes).
    - Metadata is inferred (Client type, Strategy).
4.  **Validation**:
    - **Consistency**: "Does the chart data match the text?"
    - **Compliance**: "Is this Article 8 fund making unsupported quantitative claims?"
    - **Regulatory**: "Is this fund registered for sale in Italy?"
5.  **Output**: A structured JSON report including a unified `ComplianceIssue` list.

## Technology Stack

- **Language**: Python 3.12 (Backend), TypeScript (Frontend)
- **Frameworks**: Flask (API), Next.js (UI)
- **AI Models**:
    - **Text**: Llama-3.1-70B-Instruct (via Token Factory API)
    - **Vision**: LLaVA-1.5-7B-HF
- **Data Integration**: Excel parsing (openpyxl) for regulatory datasets.
