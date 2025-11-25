# Data Consistency Agent

## Overview

The Data Consistency Agent verifies that numerical data, sources, and charts in marketing documents match official reference documents (Prospectus, KID, SFDR). It ensures compliance with the rule: **"All data, charts, and figures must include source and date."**

## Role

Verify that numerical data, sources, and charts match the official documents (Prospectus, KID, SFDR).

## Based On

- Word rules: "All data, charts, and figures must include source and date"
- General compliance requirements for financial marketing materials

## Tasks

1. **Check that each chart includes source + date**
   - Validates all tables and charts have proper source attribution
   - Ensures dates are present for all data visualizations
   - Flags missing or incomplete source/date information

2. **Validate numbers against the prospectus or SFDR annex**
   - Compares performance figures with reference documents
   - Validates table entries against official data
   - Uses configurable tolerance for numerical comparisons

3. **Flag inconsistencies**
   - Reports errors for missing source/date information
   - Reports errors for numerical mismatches beyond tolerance
   - Reports warnings for unvalidatable data (no reference available)

## Usage

### Basic Usage

```python
from src.extractors.data_consistency_agent import DataConsistencyAgent, ReferenceData

# Create reference data from official documents
reference_data = ReferenceData(
    fund_name="ODDO BHF Algo Trend US",
    isin="FR0012345678",
    performance_data={
        "1Y": {"net": 10.5, "gross": 12.0},
        "3Y": {"net": 8.2}
    },
    table_data={
        "fund": 10.5,
        "benchmark": 8.0
    },
    reference_date="2025-08-31",
    source_document="Prospectus"
)

# Initialize agent
agent = DataConsistencyAgent(reference_data=reference_data)

# Validate extraction results
result = agent.validate(
    extraction_result=extraction_result,
    metadata=metadata,
    document_id="doc-123"
)

# Check results
print(f"Status: {result.overall_status}")
print(f"Errors: {len([i for i in result.source_date_issues if i.severity == 'error'])}")
print(f"Inconsistencies: {len(result.numerical_inconsistencies)}")
```

### Integration with Extraction Pipeline

```python
from src.extractors.pipeline import ExtractionPipeline
from src.extractors.data_consistency_agent import DataConsistencyAgent, ReferenceData

# Process document
pipeline = ExtractionPipeline(use_llm=True)
pipeline_result = pipeline.process_document("path/to/document.pptx")

# Prepare reference data (load from your reference data source)
reference_data = ReferenceData(
    performance_data={
        "1Y": {"net": 10.5},
        "ytd": {"net": 8.3}
    },
    source_document="Prospectus"
)

# Validate
agent = DataConsistencyAgent(reference_data=reference_data)
validation_result = agent.validate(
    extraction_result=pipeline_result['extraction_result'],
    metadata=pipeline_result['metadata'],
    document_id=pipeline_result['document_id']
)

# Access results
for issue in validation_result.source_date_issues:
    print(f"❌ {issue.message}")

for inconsistency in validation_result.numerical_inconsistencies:
    print(f"⚠️  {inconsistency.message}")
```

### Without Reference Data

If reference data is not available, the agent will still validate source/date requirements:

```python
# Initialize without reference data
agent = DataConsistencyAgent(reference_data=None)

# Only source/date validation will run
result = agent.validate(extraction_result=extraction_result)
```

## Validation Results

### DataConsistencyResult

The validation result contains:

- **Source/Date Validation:**
  - `source_date_issues`: List of issues found
  - `total_tables_checked`: Total number of tables/charts checked
  - `tables_with_source_date`: Number of tables with complete source+date
  - `tables_missing_source_date`: Number of tables missing source/date

- **Numerical Validation:**
  - `numerical_inconsistencies`: List of inconsistencies found
  - `total_numerical_values_checked`: Total values compared
  - `values_matching_reference`: Number of matching values
  - `values_with_inconsistencies`: Number of inconsistent values

- **Overall Status:**
  - `overall_status`: "pass", "warning", or "error"
  - `has_errors`: Boolean flag for errors
  - `has_warnings`: Boolean flag for warnings
  - `summary`: Human-readable summary messages

### Issue Types

#### SourceDateIssue

Issues with source/date information:
- `issue_type`: "missing_source", "missing_date", or "both_missing"
- `location`: Document location (slide/page/table)
- `severity`: "error" or "warning"
- `message`: Human-readable description

#### NumericalInconsistency

Numerical data inconsistencies:
- `data_type`: "performance", "table_entry", or "other"
- `document_value`: Value found in document
- `reference_value`: Value from reference document
- `period`: Time period (e.g., "1Y", "YTD")
- `basis`: "net", "gross", "backtest", "simulation"
- `severity`: "error" or "warning"
- `tolerance`: Allowed tolerance for differences

## Reference Data Structure

### ReferenceData Model

```python
ReferenceData(
    fund_name: Optional[str] = None,
    isin: Optional[str] = None,
    performance_data: Dict[str, Dict[str, float]] = {},
    table_data: Dict[str, float] = {},
    reference_date: Optional[str] = None,
    source_document: Optional[str] = None
)
```

### Performance Data Format

Performance data is structured as:
```python
{
    "1Y": {"net": 10.5, "gross": 12.0},
    "3Y": {"net": 8.2},
    "ytd": {"net": 8.3}
}
```

Where:
- First key: Period ("1Y", "3Y", "YTD", etc.)
- Second key: Basis ("net", "gross", "backtest", "simulation")
- Value: Numerical performance percentage

### Table Data Format

Table data is keyed by label/description:
```python
{
    "fund": 10.5,
    "benchmark": 8.0,
    "sector average": 7.5
}
```

## Configuration

### Tolerance

Default tolerance for numerical comparisons is 1% (0.01). Values within this tolerance are considered matching.

To customize:
```python
agent = DataConsistencyAgent(reference_data=reference_data)
agent.default_tolerance = 0.02  # 2% tolerance
```

## Input Data Requirements

The agent expects extraction results from `DocumentExtractor.extract()` containing:

- `tables`: List of table objects with `slide_number`, `page_number`, `table_index`
- `table_sources`: List of source information with `slide_number`, `source_name`, `source_date`
- `performance_sections`: List of performance sections with `entries` containing:
  - `value`: Numerical value
  - `period`: Time period
  - `basis`: "net", "gross", etc.
- `performance_table_entries`: List of normalized table entries with:
  - `value`: Numerical value
  - `label`: Row label
  - `column`: Column header

## Output Integration

The validation results can be:
- Saved to JSON for reporting
- Integrated into compliance workflows
- Used to generate validation reports
- Stored alongside extraction results

Example:
```python
# Save results
import json
result_dict = validation_result.model_dump()
with open("validation_results.json", "w") as f:
    json.dump(result_dict, f, indent=2)
```

## Examples

See `tests/test_data_consistency_agent.py` for comprehensive examples.

## Related Modules

- **DocumentExtractor**: Provides extraction results for validation
- **ExtractionPipeline**: Orchestrates document processing
- **Data Validation & Compliance Agent**: May merge with this agent for unified compliance checking

