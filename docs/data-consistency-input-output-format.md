# Data Consistency Agent - Production Input/Output Format

## Overview

This document defines the exact input and output data formats for the Data Consistency Agent in production use.

---

## INPUT FORMAT

### Function Signature

```python
def validate(
    self,
    extraction_result: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    document_id: Optional[str] = None
) -> DataConsistencyResult:
```

### 1. `extraction_result` (Required)

**Type**: `Dict[str, Any]`

**Required Fields**:

```python
{
    # Tables (required, can be empty list)
    "tables": [
        {
            "slide_number": int | None,      # Slide number (1-indexed)
            "page_number": int | None,        # Page number (1-indexed)
            "table_index": int,               # Table index on slide/page (0-indexed)
            "data": List[List[str]]           # Table data as 2D array
        }
    ],
    
    # Table sources (required, can be empty list)
    "table_sources": [
        {
            "slide_number": int | None,       # Must match table's slide_number
            "page_number": int | None,        # Must match table's page_number
            "source_name": str | None,        # Source name (e.g., "Bloomberg")
            "source_date": str | None,        # Date string (e.g., "2025-08-31")
            "raw_note": str | None            # Original source note text
        }
    ],
    
    # Performance sections (optional, can be empty list)
    "performance_sections": [
        {
            "slide_number": int | None,
            "page_number": int | None,
            "sentences": List[str],           # Original sentences containing performance data
            "entries": [
                {
                    "sentence": str,          # Full sentence text
                    "value": float,           # Numerical value (percentage)
                    "period": str,            # Time period (e.g., "1y", "3y", "ytd")
                    "basis": str | None,      # "net", "gross", "backtest", "simulation"
                    "benchmark": float | None # Benchmark value if mentioned
                }
            ]
        }
    ],
    
    # Performance table entries (optional, can be empty list)
    "performance_table_entries": [
        {
            "label": str,                     # Row label (e.g., "Fund", "Benchmark")
            "column": str,                    # Column header (e.g., "1Y", "3Y", "YTD")
            "value": float,                   # Numerical value (percentage)
            "raw": str,                       # Original cell text (e.g., "10.5%")
            "slide_number": int | None,
            "table_index": int
        }
    ],
    
    # Charts (optional, can be empty list)
    "charts": [
        {
            "slide_number": int | None,
            "chart_title": str | None,
            "source_date_info": {
                "has_source": bool,
                "has_date": bool,
                "source_text": str | None,
                "date_text": str | None
            }
        }
    ]
}
```

**Field Requirements**:

- `tables`: List of table objects. Each table must have `slide_number`, `table_index`, and `data`.
- `table_sources`: List of source information. Must match tables by `(slide_number, page_number)` tuple.
- `performance_sections`: Optional. Contains performance data extracted from text.
- `performance_table_entries`: Optional. Contains performance data extracted from tables.
- `charts`: Optional. Contains chart information with source/date validation.

**Example**:

```python
extraction_result = {
    "tables": [
        {
            "slide_number": 2,
            "table_index": 1,
            "data": [["Fund", "10%"], ["Benchmark", "8%"]]
        }
    ],
    "table_sources": [
        {
            "slide_number": 2,
            "source_name": "Bloomberg",
            "source_date": "2025-08-31",
            "raw_note": "Source: Bloomberg | Data as of 31/08/2025"
        }
    ],
    "performance_sections": [
        {
            "slide_number": 3,
            "entries": [
                {
                    "sentence": "Net performance 1Y: 10.5%",
                    "value": 10.5,
                    "period": "1y",
                    "basis": "net",
                    "benchmark": None
                }
            ]
        }
    ],
    "performance_table_entries": [],
    "charts": []
}
```

### 2. `metadata` (Optional)

**Type**: `Dict[str, Any] | None`

**Used Fields**:

```python
{
    # Document date for date validation
    "document_date": str | None,              # ISO format: "2025-08-31"
    "date": str | None,                       # Alternative field name
    
    # Title information (nested)
    "title_information": {
        "document_date": str | None,
        "date": str | None
    },
    
    # Other metadata (not used by agent but may be passed through)
    # ... any other fields ...
}
```

**Purpose**: Used for date consistency validation (checking if source dates are after document date).

**Example**:

```python
metadata = {
    "document_date": "2025-08-31",
    "title_information": {
        "document_date": "2025-08-31"
    }
}
```

### 3. `document_id` (Optional)

**Type**: `str | None`

**Purpose**: Identifier for the document being validated. Stored in result for traceability.

**Example**: `"doc-abc123"` or `"47861-6PG-FR-ODDO-BHF-Algo-Trend-US"`

---

## OUTPUT FORMAT

### Return Type

**Type**: `DataConsistencyResult` (Pydantic model)

### Structure

```python
{
    # Document identification
    "document_id": str | None,
    "validation_timestamp": str,              # ISO format with Z: "2025-01-15T14:30:00.123Z"
    
    # Source/Date validation results
    "source_date_issues": [
        {
            "issue_type": str,                # "missing_source", "missing_date", "both_missing",
                                              # "invalid_date_format", "date_too_old", "date_inconsistent"
            "location": str,                  # Human-readable: "slide 5, table 3"
            "table_index": int | None,
            "slide_number": int | None,
            "page_number": int | None,
            "severity": str,                  # "error" or "warning"
            "message": str                    # Human-readable description
        }
    ],
    "total_tables_checked": int,              # Total tables + charts checked
    "tables_with_source_date": int,           # Count of compliant tables/charts
    "tables_missing_source_date": int,        # Count of non-compliant tables/charts
    
    # Numerical validation results
    "numerical_inconsistencies": [
        {
            "data_type": str,                 # "performance", "table_entry", "other"
            "location": str,                  # Human-readable: "slide 3"
            "document_value": float,          # Value found in document
            "reference_value": float | None,  # Value from reference document
            "reference_source": str | None,   # "Prospectus", "KID", "SFDR Annex"
            "period": str | None,             # "1Y", "3Y", "ytd"
            "basis": str | None,              # "net", "gross"
            "label": str | None,              # Table entry label
            "severity": str,                  # "error" or "warning"
            "message": str,                   # Human-readable description
            "tolerance": float | None         # Allowed tolerance (percentage)
        }
    ],
    "total_numerical_values_checked": int,    # Total values compared
    "values_matching_reference": int,         # Count of matching values
    "values_with_inconsistencies": int,       # Count of inconsistent values
    
    # Cross-reference validation results
    "cross_reference_issues": [
        {
            "issue_type": str,                # "performance_mismatch", "duplicate_inconsistency"
            "location": str,                  # Human-readable location
            "value1": float | None,           # First value
            "value2": float | None,           # Second value
            "location1": str | None,          # Location of first value
            "location2": str | None,          # Location of second value
            "period": str | None,             # Time period
            "severity": str,                  # "error" or "warning"
            "message": str                    # Human-readable description
        }
    ],
    
    # Disclaimer validation (optional, only if enabled)
    "disclaimer_validation": {
        # Structure depends on DisclaimerValidator output
        # Typically includes: has_errors, has_warnings, total_missing, etc.
    } | None,
    
    # Overall status
    "has_errors": bool,                       # True if any error-level issues found
    "has_warnings": bool,                     # True if any warning-level issues found
    "overall_status": str,                    # "pass", "warning", "error", "unknown"
    
    # Summary messages
    "summary": [                              # List of human-readable summary messages
        "Source/Date Validation: 2/4 tables have complete source and date information",
        "[WARNING]  2 table(s) missing source/date information",
        "Numerical Validation: 9/10 values match reference documents",
        "[WARNING]  1 value(s) have inconsistencies",
        "[OK] All validations passed"  # or "[FAIL] Validation found errors that require attention"
    ]
}
```

### Field Guarantees

**Always Present**:
- `validation_timestamp`: Always set (ISO format with Z)
- `source_date_issues`: Always a list (may be empty)
- `total_tables_checked`: Always an integer (≥ 0)
- `tables_with_source_date`: Always an integer (≥ 0)
- `tables_missing_source_date`: Always an integer (≥ 0)
- `numerical_inconsistencies`: Always a list (may be empty)
- `total_numerical_values_checked`: Always an integer (≥ 0)
- `values_matching_reference`: Always an integer (≥ 0)
- `values_with_inconsistencies`: Always an integer (≥ 0)
- `cross_reference_issues`: Always a list (may be empty)
- `has_errors`: Always a boolean (never None)
- `has_warnings`: Always a boolean (never None)
- `overall_status`: Always one of: "pass", "warning", "error", "unknown"
- `summary`: Always a list (may be empty)

**Conditionally Present**:
- `document_id`: Only if provided in input
- `disclaimer_validation`: Only if `enable_disclaimer_validation=True` and validator provided

### Status Values

**`overall_status`**:
- `"pass"`: No errors, no warnings
- `"warning"`: Has warnings but no errors
- `"error"`: Has at least one error
- `"unknown"`: Should not occur in production (indicates validation didn't complete)

**`severity`** (in issues):
- `"error"`: Critical issue that must be fixed
- `"warning"`: Non-critical issue that should be reviewed

### Count Consistency

The following relationships are guaranteed:

```python
# Source/Date counts
total_tables_checked == tables_with_source_date + tables_missing_source_date

# Numerical counts (may not be equal if some values can't be validated)
total_numerical_values_checked >= values_matching_reference + values_with_inconsistencies
```

---

## Example Usage

### Minimal Input

```python
from src.extractors.data_consistency_agent import DataConsistencyAgent

agent = DataConsistencyAgent(reference_data=None)

extraction_result = {
    "tables": [
        {
            "slide_number": 2,
            "table_index": 1,
            "data": [["Fund", "10%"]]
        }
    ],
    "table_sources": [],
    "performance_sections": [],
    "performance_table_entries": [],
    "charts": []
}

result = agent.validate(extraction_result)

# Access output
print(result.overall_status)  # "error" (table missing source/date)
print(result.has_errors)      # True
print(len(result.source_date_issues))  # 1
```

### Full Input with Reference Data

```python
from src.extractors.data_consistency_agent import (
    DataConsistencyAgent,
    ReferenceData
)

# Prepare reference data
reference_data = ReferenceData(
    fund_name="ODDO BHF Algo Trend US",
    performance_data={
        "1y": {"net": 10.5},
        "3y": {"net": 8.2}
    },
    table_data={
        "fund": 10.5,
        "benchmark": 8.0
    },
    source_document="Prospectus"
)

# Initialize agent
agent = DataConsistencyAgent(reference_data=reference_data)

# Prepare extraction result
extraction_result = {
    "tables": [
        {
            "slide_number": 2,
            "table_index": 1,
            "data": [["Fund", "10%"], ["Benchmark", "8%"]]
        }
    ],
    "table_sources": [
        {
            "slide_number": 2,
            "source_name": "Bloomberg",
            "source_date": "2025-08-31"
        }
    ],
    "performance_sections": [
        {
            "slide_number": 3,
            "entries": [
                {
                    "sentence": "Net performance 1Y: 10.5%",
                    "value": 10.5,
                    "period": "1y",
                    "basis": "net"
                }
            ]
        }
    ],
    "performance_table_entries": [],
    "charts": []
}

# Prepare metadata
metadata = {
    "document_date": "2025-08-31"
}

# Validate
result = agent.validate(
    extraction_result=extraction_result,
    metadata=metadata,
    document_id="doc-123"
)

# Access output
print(result.overall_status)                    # "pass" or "error" or "warning"
print(result.has_errors)                        # bool
print(result.has_warnings)                      # bool
print(result.total_tables_checked)              # int
print(len(result.source_date_issues))           # int
print(len(result.numerical_inconsistencies))    # int
print(result.summary)                           # List[str]
```

---

## Validation Rules

### Input Validation

The agent expects:
1. `extraction_result` must be a dict
2. `tables` must be a list (can be empty)
3. `table_sources` must be a list (can be empty)
4. All table objects must have `slide_number`, `table_index`, and `data`
5. All source objects must have `slide_number`

**Note**: The agent is lenient and will handle missing optional fields gracefully (returns empty lists/zeros).

### Output Guarantees

1. All numeric fields are integers (never floats)
2. All boolean fields are booleans (never None)
3. All list fields are lists (never None)
4. `overall_status` is always one of the valid values
5. Timestamp is always valid ISO format with Z suffix

---

## Type Hints (For Reference)

```python
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

# Input
extraction_result: Dict[str, Any]
metadata: Optional[Dict[str, Any]] = None
document_id: Optional[str] = None

# Output
result: DataConsistencyResult  # Pydantic BaseModel
```

---

## JSON Serialization

The output can be serialized to JSON:

```python
import json

result = agent.validate(extraction_result, metadata, document_id)

# Serialize to JSON
json_str = json.dumps(result.model_dump(), indent=2, default=str)

# Or save to file
with open("validation_result.json", "w") as f:
    json.dump(result.model_dump(), f, indent=2, default=str)
```

**Note**: Use `default=str` to handle any date/datetime objects that might be present.

