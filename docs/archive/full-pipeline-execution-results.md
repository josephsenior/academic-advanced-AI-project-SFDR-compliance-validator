# Full Pipeline Execution Results

**Date**: December 5, 2025  
**Document**: `ODDO-BHF(1).pdf`  
**Output Directory**: `outputs/full_run_20251205_203435/`

## Pipeline Components

### [OK] Step 1: Extraction Pipeline
Successfully extracted document content with LLM features:
- **Text**: 4,818 characters extracted
- **Tables**: 0 tables found
- **Slides**: 0 slides (PDF document)
- **ESG Mentions**: 2 detected using LLM
- **Performance Data**: 0 performance data points
- **Country Mentions**: 1 country detected

### [OK] Step 2: Data Consistency Validation
Ran comprehensive compliance validation with 9 issues detected.

## Validation Results

### [CHART] Source & Date Validation
- **Tables checked**: 0
- **Tables with source/date**: 0
- **Issues found**: 1 warning
  - Performance section at page 6 may need source and date verification

###  Numerical Validation
- **Values checked**: 0 (no reference data provided)
- **Inconsistencies**: 0

### [WARNING] Compliance Issues (9 Total)

#### **ERRORS (3)** [FAIL]
1. **Risk Scale (SRI) Missing**
   - Location: Slide 2
   - Message: "Risk Scale (SRI) is missing. It is usually required on Slide 2."

2. **Missing Capital Loss Warning**
   - Location: Disclaimers
   - Message: "Warning about 'Risk of Capital Loss' (Risque de perte en capital) is missing."

3. **Missing Past Performance Warning**
   - Location: Disclaimers
   - Message: "Warning that 'Past performance is not a reliable indicator of future results' is missing."

#### **WARNINGS (6)** [WARNING]
1. **5-Year Performance History**
   - Location: Performance Section
   - Message: "5-year performance history not found. Required if the fund is older than 5 years."

2. **10-Year Performance History**
   - Location: Performance Section
   - Message: "10-year performance history not found. Required if the fund is older than 10 years."

3. **Benchmark Comparison**
   - Location: Performance Section
   - Message: "Performance is shown but no benchmark comparison detected. Performance must be compared to the official benchmark."

4. **Net of Fees Indication**
   - Location: Performance Section
   - Message: "Retail performance must be displayed Net of fees. No 'Net' indication found."

5. **Investment Horizon Missing**
   - Location: Slide 2
   - Message: "Investment Horizon is missing. It is usually required on Slide 2."

6. **Glossary Missing**
   - Location: General
   - Message: "Retail document requires a Glossary."

## Overall Status

**[FAIL] ERROR** - Document requires corrections before publication.

### Why ERROR Status?
The document has 3 **critical errors**:
1. Missing mandatory Risk Scale (SRI)
2. Missing mandatory "Risk of Capital Loss" warning
3. Missing mandatory "Past Performance" disclaimer

These are **mandatory compliance requirements** that must be present in all retail marketing documents.

## Generated Output Files

```
outputs/full_run_20251205_203435/
├── index.jsonl                                    # Index of all processed documents
└── 2ed58610-24f0-4a24-a731-01f5625ee045/
    ├── consistency_report.json                    # [STAR] Data consistency validation results
    ├── extraction.json                            # Full text and table extraction
    ├── features.json                              # LLM-extracted features (ESG, performance, etc.)
    ├── manifest.json                              # Document processing manifest
    └── metadata.json                              # Parsed metadata (filename, date, fund name, etc.)
```

## Key Files

### [DOC] consistency_report.json
Complete validation report containing:
- `source_date_issues`: List of missing source/date in charts/tables
- `numerical_inconsistencies`: Mismatches with reference documents
- `cross_reference_issues`: Internal inconsistencies
- `compliance_issues`: Violations of compliance rules
- `overall_status`: "pass", "warning", or "error"

### [DOC] features.json
LLM-extracted features:
```json
{
  "esg_mentions": [
    {
      "text": "sustainable",
      "location": "page 3",
      "confidence": 0.9
    },
    {
      "text": "ESG criteria",
      "location": "page 5",
      "confidence": 0.95
    }
  ],
  "country_mentions": [
    {
      "country": "France",
      "context": "registered in France",
      "location": "page 1"
    }
  ]
}
```

## Next Steps

### For Document Correction
1. **Add Risk Scale (SRI)** on Slide 2 (or equivalent page in PDF)
2. **Add Capital Loss Warning** in disclaimers section
3. **Add Past Performance Disclaimer** near performance data
4. **Add Benchmark Comparison** if performance is shown
5. **Add "Net of fees" indication** for retail performance
6. **Add Glossary** at the end of document

### For Pipeline Improvement
1. **Add Reference Data**: Load Prospectus/KID data for numerical validation
2. **Enable Chart Analysis**: Process images to extract chart data
3. **Add Disclaimer Validator**: Automatically detect missing disclaimers
4. **Configure Fund-Specific Rules**: Adjust validation based on fund type

## How to Run Again

```bash
python run_full_pipeline_with_consistency.py
```

The script will:
1. Run extraction pipeline with LLM features
2. Load extraction results
3. Run data consistency validation
4. Generate comprehensive consistency report
5. Save all outputs to timestamped folder

## Technical Notes

### Pydantic v1 Compatibility
The pipeline now includes a monkeypatch for Python 3.12 + Pydantic v1 compatibility. See [pydantic-v1-python312-fix.md](pydantic-v1-python312-fix.md) for details.

### LLM Integration
- Uses Token Factory API for feature extraction
- Models: `hosted_vllm/Llama-3.1-70B-Instruct` for text analysis
- Fallback: Keyword-based detection if LLM unavailable

### Compliance Rules
Based on "Synthèse règles présentations commerciales.docx":
- Performance rules (history, benchmark, net/gross)
- Mandatory disclaimers (risk warnings, past performance)
- Document structure requirements (SRI, investment horizon, glossary)
- ESG approach validation per ESG Cartography

## Conclusion

[OK] **Pipeline is fully operational** with both extraction and consistency validation.

[FAIL] **Document has critical errors** - requires correction before approval.

[WARNING] **6 warnings** - should be reviewed and addressed if applicable.

The consistency report provides actionable feedback for document correction.
