# Documentation Hub

Welcome to the **Document Compliance Validation System** documentation. This AI-powered system automates compliance validation for financial marketing documents using advanced LLM technology (Llama 3.1 & LLaVA).

## 🚀 Quick Start

New to the system? Start here:

1. **[User Guide](guide_usage.md)** - Learn how to use the system
2. **[Development Guide](guide_development.md)** - Set up your development environment
3. **[API Reference](api_reference.md)** - Integrate via REST API

## 📚 Complete Documentation

### 🏗️ Architecture & Design
- **[System Architecture](architecture.md)**
  - High-level system design and data flow
  - Complete project structure (`backend/`, `server/`, `frontend/`)
  - Technology stack and AI models
  - Module organization and responsibilities

### 🚀 Usage Guides
- **[User Guide](guide_usage.md)**
  - Web dashboard usage
  - Command-line interface
  - API integration examples
  - Understanding validation results
  - Document correction workflow
  - Configuration options

### 🛠️ Development & Deployment
- **[Development Guide](guide_development.md)**
  - Environment setup (Python, Node.js, dependencies)
  - Testing strategies and test organization
  - Performance tuning and optimization
  - Production deployment (Docker, Gunicorn)
  - Monitoring and debugging

### ⚡ Features & Validation Rules
- **[Features & Validation Rules](features.md)**
  - **Disclaimer Validation**: 15+ disclaimer types with multi-language support
  - **Data Consistency**: Cross-reference validation (text, tables, charts)
  - **Registration Validation**: Country distribution authorization
  - **ESG/SFDR Compliance**: Article 8/9 validation and greenwashing detection
  - **Content & Formatting**: Visual formatting and content quality checks
  - **Metadata Inference**: Automatic document characterization
  - Issue severity levels and compliance scoring

### 🔌 API Reference
- **[API Reference](api_reference.md)**
  - Complete REST API documentation
  - All endpoints with request/response examples
  - Document management (upload, validate, status, results)
  - Document correction and download
  - Report generation (JSON/HTML/PDF)
  - Error handling and status codes

## 📖 Documentation Structure

```
docs/
├── index.md              # This file - Documentation hub
├── architecture.md       # System design and structure
├── guide_usage.md        # User guide and usage examples
├── guide_development.md  # Development setup and testing
├── features.md           # Validation rules and features
└── api_reference.md     # Complete API documentation
```

## 🎯 Common Tasks

**For End Users:**
- [Upload and validate a document](guide_usage.md#using-the-web-dashboard)
- [Understand validation results](guide_usage.md#understanding-results)
- [Apply document corrections](guide_usage.md#document-correction)

**For Developers:**
- [Set up development environment](guide_development.md#environment-setup)
- [Run tests](guide_development.md#testing)
- [Deploy to production](guide_development.md#production-deployment)

**For API Integrators:**
- [Upload documents via API](api_reference.md#upload-document)
- [Get validation results](api_reference.md#get-results)
- [Apply fixes programmatically](api_reference.md#apply-fixes)

## 🔗 Quick Links

- **Main Repository**: `Advanced Ai Project/`
- **Dashboard**: http://localhost:3000 (when running)
- **API Server**: http://localhost:5000 (when running)
- **Health Check**: http://localhost:5000/api/v1/health

## 📝 Key Concepts

- **Document Processing**: Upload → Extract → Validate → Report
- **Compliance Score**: 0-100 score based on issue severity
- **Issue Categories**: Disclaimer, Consistency, Registration, ESG, Formatting, Content
- **Severity Levels**: Critical, High, Medium, Low
- **Validation Agents**: Data Consistency Agent, ESG Analyzer, various validators
