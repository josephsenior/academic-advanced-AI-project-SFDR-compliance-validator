"""
API Documentation and Testing Guide
Document Validation REST API
"""

# ==================== API ENDPOINTS ====================

## 1. Health Check
GET /api/v1/health

Response:
{
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2025-12-07T22:35:00.000000"
}

## 2. Upload Document
POST /api/v1/upload

Form Data:
- file: Document file (pptx/pdf/docx)
- metadata: (Optional) JSON string with document metadata

Example metadata:
{
    "Société de Gestion": "ODDO BHF ASSET MANAGEMENT SAS",
    "Le client est-il un professionnel": false,
    "Le document fait-il référence à une nouvelle Stratégie": false,
    "Le document fait-il référence à un nouveau Produit": false
}

Response (201):
{
    "document_id": "abc-123-def-456",
    "filename": "presentation.pptx",
    "status": "pending",
    "message": "Upload successful. Use /api/v1/validate/{document_id} to start validation."
}

## 3. Start Validation
POST /api/v1/validate/<document_id>

JSON Body (optional):
{
    "options": {
        "enable_llm": false,
        "enable_esg": false,
        "enable_disclaimers": true
    },
    "metadata": {
        // Additional metadata
    }
}

Response:
{
    "document_id": "abc-123-def-456",
    "status": "completed",
    "progress": 100,
    "message": "Validation completed",
    "results": {
        "document_id": "abc-123-def-456",
        "overall_status": "error",
        "compliance_score": 67,
        "total_issues": 14,
        "issues_by_severity": {
            "critical": 2,
            "high": 5,
            "medium": 4,
            "low": 3
        },
        "issues_by_category": {
            "esg": [...],
            "performance": [...],
            "structure": [...],
            "disclaimers": [...]
        },
        "category_counts": {
            "esg": {
                "total": 5,
                "critical": 1,
                "high": 2,
                "medium": 1,
                "low": 1
            }
        },
        "statistics": {
            "total_tables_checked": 59,
            "tables_with_source_date": 45,
            "tables_missing_source_date": 14,
            "total_charts_analyzed": 52
        }
    }
}

## 4. Get Status
GET /api/v1/status/<document_id>

Response:
{
    "document_id": "abc-123-def-456",
    "filename": "presentation.pptx",
    "status": "completed",  // pending, uploading, extracting, validating, completed, failed
    "progress": 100,  // 0-100
    "created_at": "2025-12-07T22:00:00.000000",
    "updated_at": "2025-12-07T22:05:00.000000",
    "error": null
}

## 5. Get Results
GET /api/v1/results/<document_id>?category=esg&severity=critical&slide=3

Query Parameters:
- category: Filter by category (esg, performance, structure, etc.)
- severity: Filter by severity (critical, high, medium, low)
- slide: Filter by slide number

Response: Same as validation results

## 6. Apply Fixes
POST /api/v1/fix/<document_id>

JSON Body:
{
    "fix_types": ["disclaimers", "formatting", "all"],
    "options": {}
}

Response:
{
    "document_id": "abc-123-def-456",
    "corrected_file_path": "corrected_documents/abc-123-def-456_corrected.pptx",
    "fixes_applied": 5,
    "message": "Document corrected successfully. 5 fixes applied."
}

## 7. Download Document
GET /api/v1/download/<document_id>?type=corrected

Query Parameters:
- type: 'original' or 'corrected' (default: corrected)

Response: File download

## 8. Generate Report
GET /api/v1/report/<document_id>?format=json

Query Parameters:
- format: 'json', 'html', 'pdf' (default: json)

Response: Report in requested format

## 9. List Documents
GET /api/v1/list?status=completed&limit=50&offset=0

Query Parameters:
- status: Filter by status
- limit: Max results (default: 50)
- offset: Pagination offset (default: 0)

Response:
{
    "total": 100,
    "limit": 50,
    "offset": 0,
    "documents": [
        {
            "document_id": "abc-123",
            "filename": "presentation.pptx",
            "status": "completed",
            "progress": 100,
            "created_at": "2025-12-07T...",
            "updated_at": "2025-12-07T...",
            "compliance_score": 67,
            "total_issues": 14
        }
    ]
}

## 10. Delete Document
DELETE /api/v1/delete/<document_id>

Response:
{
    "message": "Document deleted successfully",
    "document_id": "abc-123-def-456"
}

# ==================== WORKFLOW ====================

1. Upload document → Get document_id
2. Start validation → Get validation results
3. (Optional) Apply fixes
4. Download corrected document
5. Generate report

# ==================== ISSUE STRUCTURE ====================

Each issue in the results contains:
{
    "issue_type": "esg_overmentioned_article8",
    "severity": "critical",  // critical, high, medium, low
    "category": "esg",
    "location": "Slide 3, 5, 7",
    "slide_number": 3,
    "message": "Article 8 fund exceeds 10% ESG limit (15.3% found)",
    "context": "Full context text...",
    "suggestion": "Reduce ESG content to below 10%",
    "auto_fixable": false,
    "rule_reference": "Section 4.1 - ESG Compliance",
    "details": {}
}

# ==================== CATEGORIES ====================

- esg: ESG/SFDR compliance issues
- performance: Performance data validation
- structure: Document structure issues (cover page, slide 2, etc.)
- disclaimers: Missing or incorrect disclaimers
- cross_reference: Cross-reference consistency
- date_validation: Date format and recency
- source_attribution: Missing source or date
- registration: Country registration validation
- general: Other issues
