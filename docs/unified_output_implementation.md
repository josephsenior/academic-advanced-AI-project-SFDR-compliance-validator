# Unified Output Implementation

## Overview

The system now produces a **single unified output** containing all validation results (data consistency, ESG compliance, disclaimers, etc.) in one consolidated structure.

## Output Structure

### DataConsistencyResult

```python
{
  "document_id": "test-esg-001",
  "overall_status": "error",
  
  # All compliance issues in one unified array
  "compliance_issues": [
    {
      "issue_type": "missing_fund_name",
      "severity": "error",
      "location": "Slide 1",
      "message": "Fund Name is missing on the cover page.",
      "client_type": "retail",
      "fund_type": "etf",
      ...
    },
    {
      "issue_type": "esg_overmentioned_article8",
      "severity": "high",
      "location": "Document-wide",
      "message": "Article 8 fund: ESG content exceeds 10% limit (48.73%)",
      "client_type": "retail",
      "fund_type": "etf",
      ...
    }
  ],
  
  # ESG enrichment metadata (optional field)
  "esg_analysis": {
    "esg_level": {
      "level": "engaging",
      "sfdr_article": 8,
      "exclusion_percentage": null,
      "portfolio_coverage": null,
      "description": "Fund integrates ESG factors..."
    },
    "esg_mentions": {
      "esg_percentage": 48.73,
      "total_text_length": 314,
      "esg_text_length": 153,
      "commercial_esg_mentions": 1,
      "mandatory_regulatory_mentions": 0,
      "keywords_found": ["esg"],
      "keywords_by_slide": {"esg": [2]}
    },
    "analysis_timestamp": "2025-12-07T15:48:51.302747Z"
  }
}
```

## Key Features

### 1. Unified Compliance Issues Array

All validation issues (ESG, disclaimers, performance, data consistency) are stored in a single `compliance_issues` array. Each issue includes:

- `issue_type`: Type of compliance issue
- `severity`: "critical", "error", "high", "warning", "info"
- `location`: Where the issue was found
- `message`: Description of the issue
- `context`: Surrounding context (optional)
- `suggestion`: How to fix it (optional)
- `client_type`: "retail" or "professional"
- `fund_type`: "standard", "etf", "private_equity", "dated"
- `slide_number`: Specific slide (optional)
- `country`: Country-specific rules (optional)

### 2. ESG Enrichment Data

When ESG validation is enabled, the output includes an `esg_analysis` field with detailed metadata:

**ESG Level Information:**
- Detected ESG level (none/reduced/engaging)
- SFDR Article classification (6/8/9)
- Exclusion percentage (for Article 9 funds)
- Portfolio coverage percentage
- Description of ESG approach

**ESG Mentions Analysis:**
- Overall ESG percentage in document
- Total text length analyzed
- ESG-specific text length
- Commercial vs regulatory mentions
- Keywords found
- Keyword locations by slide

**Timestamp:**
- Analysis timestamp (ISO 8601 format)

### 3. Client and Fund Type Detection

Each compliance issue is enriched with context:

**Client Type Detection:**
- Determined from `metadata['is_professional_client']`
- `False` → `ClientType.RETAIL`
- `True` → `ClientType.PROFESSIONAL`

**Fund Type Detection:**
- ETF: Keywords "etf", "exchange traded" in fund name
- Private Equity: Keywords "fcpr", "fpci", "private equity"
- Dated: Keywords "daté", "dated", "échéance"
- Standard: Default for all other funds

## Implementation

### Data Consistency Agent

The `DataConsistencyAgent` now:

1. **Initializes with ESG support** (optional):
```python
agent = DataConsistencyAgent(
    enable_esg_validation=True,
    esg_api_key="your-api-key",
    esg_base_url="https://api.example.com"
)
```

2. **Validates document** and produces unified output:
```python
result = agent.validate(
    extraction_result=extraction_result,
    metadata=metadata,
    document_id="doc-123"
)
```

3. **Caches ESG metadata** during validation:
   - Stores ESG level and mentions in `_esg_analysis_cache`
   - Converts ESG violations to `ComplianceIssue` objects
   - Injects cache into `result.esg_analysis` field

4. **Returns consolidated result**:
   - All issues in `compliance_issues` array
   - ESG metadata in `esg_analysis` field (if enabled)
   - Single overall status

### Application Pipeline

The main application ([app.py](../app.py)) now:

1. **Checks for ESG credentials**:
```python
esg_api_key = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
esg_base_url = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
```

2. **Initializes agent with ESG** if available:
```python
if esg_api_key and esg_base_url:
    agent = DataConsistencyAgent(
        reference_data=None,
        enable_esg_validation=True,
        esg_api_key=esg_api_key,
        esg_base_url=esg_base_url
    )
else:
    agent = DataConsistencyAgent(reference_data=None)
```

3. **Produces unified output** for entire pipeline:
   - Document extraction
   - Data consistency validation
   - ESG compliance (if enabled)
   - Disclaimer validation
   - **All in one output file**

## Benefits

### For Users

- **Single source of truth**: All validation results in one place
- **Consistent format**: All issues follow same structure
- **Rich context**: Each issue includes client/fund type, location, suggestions
- **Enrichment data**: ESG metadata provides deeper insights

### For Developers

- **Backwards compatible**: `esg_analysis` field is optional
- **Easy integration**: Single `validate()` call for all validations
- **Flexible**: ESG validation can be enabled/disabled
- **Extensible**: Easy to add more enrichment fields

### For Compliance Teams

- **Complete picture**: All compliance issues visible at once
- **Prioritized**: Issues sorted by severity
- **Actionable**: Each issue includes fix suggestions
- **Auditable**: Timestamps and full context preserved

## Testing

### Test Script

Run the integration test:

```bash
python test_esg_integration.py
```

### Verify Output

Check the unified output structure:

```bash
python check_unified_output.py
```

### Expected Results

```
UNIFIED OUTPUT STRUCTURE
========================
Top-level keys: ['document_id', 'overall_status', 'compliance_issues', 'esg_analysis']

ESG ANALYSIS ENRICHMENT DATA
============================
✅ ESG enrichment data found!

ESG ISSUES IN compliance_issues ARRAY
=====================================
Found 2 ESG-related issues:
1. esg_overmentioned_article8 (high)
2. engaging_criteria_not_met (high)

SUMMARY
=======
Total compliance issues: 10
ESG-specific issues: 2
ESG enrichment data: ✅ Present
Overall status: error
```

## Next Steps

### 1. Report Generation

Update `ValidationReportGenerator` to include ESG enrichment data in PDF/JSON reports:

```python
# In generate_json_report():
if validation_result.esg_analysis:
    report_data['esg_analysis'] = validation_result.esg_analysis
```

### 2. Frontend Display

Update web interface to display:
- ESG enrichment metadata (level, percentages, keywords)
- Separate ESG issues section with visual indicators
- ESG compliance status badge

### 3. Documentation

- API documentation for unified output structure
- User guide for interpreting ESG enrichment data
- Developer guide for adding new enrichment fields

## Architecture

```
Document Upload
       ↓
Document Extraction (metadata, text, structure)
       ↓
Data Consistency Agent.validate()
       ├─→ Performance Validation → ComplianceIssue[]
       ├─→ Structure Validation → ComplianceIssue[]
       ├─→ ESG Validation (if enabled)
       │   ├─→ ESG Level Detection → ESGLevel
       │   ├─→ ESG Mentions Analysis → ESGMentions
       │   ├─→ Cache enrichment → _esg_analysis_cache
       │   └─→ Generate issues → ComplianceIssue[]
       └─→ Disclaimer Validation → ComplianceIssue[]
       ↓
Unified DataConsistencyResult
       ├─→ compliance_issues: ComplianceIssue[]
       └─→ esg_analysis: Dict (enrichment)
       ↓
Single Output File (JSON)
```

## Configuration

### Environment Variables

```env
# Required for ESG validation
TOKEN_FACTORY_API_KEY=your-api-key
TOKEN_FACTORY_BASE_URL=https://api.example.com

# Or alternative names
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.example.com
```

### Agent Configuration

```python
# With ESG validation
agent = DataConsistencyAgent(
    enable_esg_validation=True,
    esg_api_key=api_key,
    esg_base_url=base_url,
    reference_data=None  # Optional reference data
)

# Without ESG validation
agent = DataConsistencyAgent(
    enable_esg_validation=False,  # or omit parameter
    reference_data=None
)
```

## Backwards Compatibility

The unified output is fully backwards compatible:

- **Existing code**: Still works with `compliance_issues` array
- **ESG field**: Optional, only present if ESG validation enabled
- **Legacy fields**: `source_date_issues`, `numerical_inconsistencies` still available
- **API unchanged**: Same `validate()` method signature

## Conclusion

The unified output implementation provides:

✅ **Single consolidated output** for entire pipeline  
✅ **ESG compliance integrated** with data consistency  
✅ **Rich enrichment data** for deeper analysis  
✅ **Backwards compatible** with existing code  
✅ **Production ready** in main application  

All validation results are now in one place, making it easier to understand document compliance status at a glance.
