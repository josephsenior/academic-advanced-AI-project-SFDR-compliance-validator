# Data Consistency Agent - Company Usage Guide

## Overview

This guide explains how your company can integrate and use the Data Consistency Agent in your document review workflow to ensure compliance and data accuracy.

---

## When to Use the Agent

### 1. **Pre-Publication Review** (Primary Use Case)
- **When**: Before finalizing any marketing document (presentations, fact sheets, brochures)
- **Purpose**: Catch errors before documents go to clients
- **Frequency**: Every document revision

### 2. **Automated Quality Checks**
- **When**: As part of automated document processing pipeline
- **Purpose**: Continuous validation during document creation
- **Frequency**: On every save/update (optional)

### 3. **Batch Validation**
- **When**: Validating multiple documents at once (e.g., quarterly review)
- **Purpose**: Ensure consistency across all published materials
- **Frequency**: Monthly/quarterly audits

### 4. **CI/CD Integration** (Advanced)
- **When**: In automated testing pipelines
- **Purpose**: Prevent non-compliant documents from being published
- **Frequency**: On every commit/merge

---

## Where to Use the Agent

### Recommended Integration Points

```
Document Creation Workflow:
┌─────────────────┐
│  Create/Edit    │
│  Document       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Extract Data   │  ← Extraction Pipeline
│  (Pipeline)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validate Data  │  ← Data Consistency Agent (HERE)
│  Consistency    │
└────────┬────────┘
         │
         ▼
    ┌────┴────┐
    │  PASS   │  →  Continue to Review
    │  FAIL   │  →  Fix Issues
    └─────────┘
```

### Integration Options

1. **Standalone Script** (Current)
   - Run manually or via scheduled tasks
   - Good for: Initial adoption, testing

2. **API Endpoint** (Recommended)
   - REST API that accepts document paths
   - Returns validation results
   - Good for: Integration with existing systems

3. **Pipeline Integration** (Best)
   - Built into ExtractionPipeline
   - Automatic validation after extraction
   - Good for: Seamless workflow

4. **Web Interface** (Future)
   - Upload document → Get validation report
   - Good for: Non-technical users

---

## Output Format Recommendations

### Format 1: JSON (For Programmatic Access)

**Use Case**: API responses, automated processing, integration with other systems

**Structure**:
```json
{
  "document_id": "doc-123",
  "validation_timestamp": "2025-11-18T10:30:00Z",
  "overall_status": "error",
  "has_errors": true,
  "has_warnings": false,
  "summary": [
    "2/4 tables have complete source and date",
    "1 numerical inconsistency found"
  ],
  "source_date_validation": {
    "total_checked": 4,
    "passed": 2,
    "failed": 2,
    "issues": [
      {
        "type": "missing_date",
        "location": "slide 5, table 3",
        "severity": "error",
        "message": "Table has source but missing date"
      }
    ]
  },
  "numerical_validation": {
    "total_checked": 10,
    "passed": 9,
    "failed": 1,
    "inconsistencies": [
      {
        "type": "performance",
        "location": "slide 3",
        "document_value": 10.5,
        "reference_value": 10.0,
        "period": "1Y",
        "severity": "error",
        "message": "Mismatch: 10.5% vs 10.0%"
      }
    ]
  },
  "cross_reference_validation": {
    "issues": []
  }
}
```

**File Location**: `outputs/{document_id}/data_consistency_result.json`

---

### Format 2: Human-Readable Report (HTML/PDF)

**Use Case**: Reviewers, compliance officers, management

**Structure**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Data Consistency Report - Document XYZ</title>
    <style>
        .error { color: red; }
        .warning { color: orange; }
        .pass { color: green; }
    </style>
</head>
<body>
    <h1>Data Consistency Validation Report</h1>
    <p><strong>Document:</strong> XYZ Presentation.pptx</p>
    <p><strong>Date:</strong> 2025-11-18</p>
    <p><strong>Status:</strong> <span class="error">ERROR</span></p>
    
    <h2>Summary</h2>
    <ul>
        <li>2/4 tables have complete source and date</li>
        <li>1 numerical inconsistency found</li>
    </ul>
    
    <h2>Source/Date Validation</h2>
    <table>
        <tr>
            <th>Location</th>
            <th>Issue</th>
            <th>Severity</th>
        </tr>
        <tr>
            <td>Slide 5, Table 3</td>
            <td>Missing date</td>
            <td class="error">ERROR</td>
        </tr>
    </table>
    
    <h2>Numerical Validation</h2>
    <!-- Similar table for numerical issues -->
</body>
</html>
```

**File Location**: `outputs/{document_id}/data_consistency_report.html`

---

### Format 3: Dashboard-Friendly (Simplified JSON)

**Use Case**: Real-time dashboards, monitoring systems

**Structure**:
```json
{
  "document_id": "doc-123",
  "status": "error",
  "score": 75,
  "issues_count": {
    "errors": 2,
    "warnings": 0
  },
  "quick_summary": {
    "source_date": "2/4 tables compliant",
    "numerical": "1 mismatch found",
    "cross_reference": "No issues"
  },
  "action_required": true
}
```

---

### Format 4: Excel/CSV (For Spreadsheet Analysis)

**Use Case**: Compliance teams, batch analysis

**Structure** (CSV):
```csv
Issue Type,Location,Severity,Message,Document ID
missing_date,slide 5 table 3,error,Table has source but missing date,doc-123
numerical_mismatch,slide 3,error,Performance mismatch: 10.5% vs 10.0%,doc-123
```

**File Location**: `outputs/{document_id}/data_consistency_issues.csv`

---

## Recommended Workflow

### Step 1: Prepare Reference Data

Before validation, you need reference data from official documents:

```python
from src.extractors.data_consistency_agent import ReferenceData

# Option A: Manual creation
reference_data = ReferenceData(
    fund_name="ODDO BHF Algo Trend US",
    isin="FR0012345678",
    performance_data={
        "1Y": {"net": 10.0, "gross": 12.0},
        "3Y": {"net": 8.5},
        "YTD": {"net": 7.2}
    },
    table_data={
        "fund": 10.0,
        "benchmark": 8.0
    },
    reference_date="2025-08-31",
    source_document="Prospectus"
)

# Option B: Load from database/API
# (You would implement this based on your data source)
```

**Best Practice**: Store reference data in a database and load it automatically based on fund name/ISIN.

---

### Step 2: Run Validation

```python
from src.extractors.pipeline import ExtractionPipeline
from src.extractors.data_consistency_agent import DataConsistencyAgent

# Extract document
pipeline = ExtractionPipeline(use_llm=True)
result = pipeline.process_document("path/to/document.pptx")

# Validate
agent = DataConsistencyAgent(
    reference_data=reference_data,
    max_date_age_days=365,
    enable_cross_reference=True,
    enable_date_validation=True
)

validation_result = agent.validate(
    extraction_result=result['extraction_result'],
    metadata=result['metadata'],
    document_id=result['document_id']
)
```

---

### Step 3: Handle Results

```python
# Check status
if validation_result.overall_status == "error":
    print("[FAIL] Document has errors - DO NOT PUBLISH")
    # Send notification, block publication, etc.
elif validation_result.overall_status == "warning":
    print("[WARNING] Document has warnings - Review required")
else:
    print("[OK] Document passed validation")

# Get actionable issues
errors = [
    issue for issue in validation_result.source_date_issues 
    if issue.severity == "error"
]

for error in errors:
    print(f"Fix: {error.message} at {error.location}")
```

---

## Integration Examples

### Example 1: Standalone Validation Script

```python
#!/usr/bin/env python3
"""
validate_document.py - Validate a single document
Usage: python validate_document.py path/to/document.pptx
"""

import sys
from pathlib import Path
from src.extractors.pipeline import ExtractionPipeline
from src.extractors.data_consistency_agent import DataConsistencyAgent, ReferenceData

def main():
    doc_path = sys.argv[1]
    
    # Load reference data (from your database/config)
    reference_data = load_reference_data(doc_path)
    
    # Extract and validate
    pipeline = ExtractionPipeline()
    result = pipeline.process_document(doc_path)
    
    agent = DataConsistencyAgent(reference_data=reference_data)
    validation = agent.validate(
        extraction_result=result['extraction_result'],
        metadata=result['metadata'],
        document_id=result['document_id']
    )
    
    # Save results
    save_results(validation, result['document_id'])
    
    # Exit with error code if validation failed
    if validation.overall_status == "error":
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

### Example 2: Batch Validation

```python
"""
validate_batch.py - Validate multiple documents
Usage: python validate_batch.py folder/with/documents/
"""

import sys
from pathlib import Path
from src.extractors.pipeline import ExtractionPipeline
from src.extractors.data_consistency_agent import DataConsistencyAgent

def validate_folder(folder_path):
    folder = Path(folder_path)
    results = []
    
    pipeline = ExtractionPipeline()
    
    for doc_file in folder.glob("*.pptx"):
        print(f"Processing: {doc_file.name}")
        
        result = pipeline.process_document(str(doc_file))
        reference_data = load_reference_data(str(doc_file))
        
        agent = DataConsistencyAgent(reference_data=reference_data)
        validation = agent.validate(
            extraction_result=result['extraction_result'],
            metadata=result['metadata'],
            document_id=result['document_id']
        )
        
        results.append({
            'document': doc_file.name,
            'status': validation.overall_status,
            'errors': len([i for i in validation.source_date_issues if i.severity == "error"]),
            'warnings': len([i for i in validation.source_date_issues if i.severity == "warning"])
        })
    
    # Generate summary report
    generate_summary_report(results)

if __name__ == "__main__":
    validate_folder(sys.argv[1])
```

---

### Example 3: API Endpoint (Flask)

```python
"""
api.py - REST API for document validation
"""

from flask import Flask, request, jsonify
from src.extractors.pipeline import ExtractionPipeline
from src.extractors.data_consistency_agent import DataConsistencyAgent, ReferenceData

app = Flask(__name__)
pipeline = ExtractionPipeline()

@app.route('/api/validate', methods=['POST'])
def validate_document():
    data = request.json
    doc_path = data['document_path']
    reference_data_dict = data.get('reference_data')
    
    # Extract
    result = pipeline.process_document(doc_path)
    
    # Prepare reference data
    reference_data = ReferenceData(**reference_data_dict) if reference_data_dict else None
    
    # Validate
    agent = DataConsistencyAgent(reference_data=reference_data)
    validation = agent.validate(
        extraction_result=result['extraction_result'],
        metadata=result['metadata'],
        document_id=result['document_id']
    )
    
    # Return JSON response
    return jsonify({
        'status': validation.overall_status,
        'has_errors': validation.has_errors,
        'has_warnings': validation.has_warnings,
        'summary': validation.summary,
        'issues': [
            {
                'type': 'source_date',
                'location': issue.location,
                'severity': issue.severity,
                'message': issue.message
            }
            for issue in validation.source_date_issues
        ],
        'numerical_inconsistencies': [
            {
                'location': inc.location,
                'document_value': inc.document_value,
                'reference_value': inc.reference_value,
                'severity': inc.severity,
                'message': inc.message
            }
            for inc in validation.numerical_inconsistencies
        ]
    })

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Output File Structure

Recommended output directory structure:

```
outputs/
└── {document_id}/
    ├── metadata.json
    ├── extraction.json
    ├── features.json
    ├── data_consistency_result.json          # Full JSON result
    ├── data_consistency_report.html          # Human-readable report
    ├── data_consistency_issues.csv           # Issues in CSV format
    └── data_consistency_summary.json         # Dashboard-friendly summary
```

---

## Best Practices

### 1. **Reference Data Management**
- Store reference data in a centralized database
- Update reference data when official documents are updated
- Version control reference data (track changes over time)

### 2. **Error Handling**
- Always check `validation_result.overall_status` before proceeding
- Log all validation results for audit purposes
- Set up alerts for critical errors

### 3. **Performance**
- Cache reference data (don't reload for every validation)
- Run validations in parallel for batch processing
- Use `use_llm=False` for faster extraction if LLM features aren't needed

### 4. **Configuration**
- Adjust `max_date_age_days` based on your requirements
- Set appropriate `tolerance` for numerical comparisons
- Enable/disable validations based on document type

### 5. **Reporting**
- Generate reports in multiple formats (JSON, HTML, CSV)
- Include document metadata in reports
- Add timestamps and user information for audit trails

---

## Next Steps

1. **Set up reference data source**: Create a system to load reference data from your Prospectus/KID/SFDR documents
2. **Choose integration method**: Decide between standalone script, API, or pipeline integration
3. **Define output format**: Choose formats based on your stakeholders' needs
4. **Test with sample documents**: Validate a few documents to ensure everything works
5. **Integrate into workflow**: Add validation step to your document review process
6. **Train users**: Ensure reviewers understand how to interpret validation results

---

## Support

For questions or issues, refer to:
- `docs/data-consistency-agent.md` - Technical documentation
- `examples/data_consistency_example.py` - Code examples
- `tests/test_data_consistency_agent.py` - Test cases

