# Validation Results Fixes [OK]

## Issues Identified and Fixed

### 1. Double Counting in `issues_by_severity` [OK] FIXED
**Problem**: 
- Errors were counted in both `error` and `high` (line 34: `high_count = sum(1 for i in result.compliance_issues if i.severity in ["high", "error"])`)
- Warnings were counted in both `warning` and `medium` (line 35: `medium_count = sum(1 for i in result.compliance_issues if i.severity in ["medium", "warning"])`)

**Fix**: 
- Changed to count only exact matches:
  - `high_count = sum(1 for i in result.compliance_issues if i.severity == "high")`
  - `medium_count = sum(1 for i in result.compliance_issues if i.severity == "medium")`

**Result**: 
- `error: 6` [OK] (only errors)
- `warning: 5` [OK] (only warnings)
- `high: 0` [OK] (no high severity issues)
- `medium: 0` [OK] (no medium severity issues)

### 2. Missing Category Assignment [OK] FIXED
**Problem**: 
- All issues were categorized as "compliance" (default value)
- Issues should be categorized as: performance, structure, disclaimer, esg, etc.

**Fix**: 
- Added `_get_issue_category()` function to map issue types to categories
- Updated serialization to infer category from `issue_type` when `issue_category` is default "compliance"
- Categories are now correctly assigned:
  - `performance_starts_document` → "performance"
  - `insufficient_performance_history` → "performance"
  - `missing_benchmark_comparison` → "performance"
  - `missing_fund_name` → "structure"
  - `missing_date` → "structure"
  - `missing_risk_profile` → "structure"
  - `missing_glossary` → "structure"
  - `missing_standard_disclaimer` → "disclaimer"
  - `missing_performance_disclaimer` → "disclaimer"

**Result**: 
- Issues are now properly categorized in `issues_by_category` and `category_counts`

### 3. Missing `filename` Field [OK] FIXED
**Problem**: 
- Frontend expects `filename` field in validation results
- Results were missing this field

**Fix**: 
- Added `filename` parameter to `format_validation_result()`
- Extract filename from job record in `validation_service.py`
- Include filename in formatted result

**Result**: 
- `filename` field now included in validation results

### 4. Category Counts Logic [OK] FIXED
**Problem**: 
- Category counts were using same double-counting logic
- Warnings counted as "high" in category_counts

**Fix**: 
- Updated category_counts logic to properly map severities:
  - `critical` → critical
  - `error` → critical (errors are critical severity)
  - `high` → high
  - `warning` → high (warnings count as high severity)
  - `medium` → medium
  - `low` → low

## Expected Results After Fix

```json
{
  "issues_by_severity": {
    "error": 6,      // Only errors
    "warning": 5,    // Only warnings
    "critical": 0,   // No critical
    "high": 0,       // No high (fixed!)
    "medium": 0,     // No medium (fixed!)
    "low": 0         // No low
  },
  "category_counts": {
    "performance": { "total": 4, "critical": 1, "high": 3, ... },
    "structure": { "total": 5, "critical": 4, "high": 1, ... },
    "disclaimer": { "total": 2, "critical": 2, ... }
  },
  "filename": "document.pptx"  // Added!
}
```

## Files Modified

1. **`server/serialization.py`**:
   - Added `_get_issue_category()` function
   - Fixed double counting in `issues_by_severity`
   - Fixed category assignment in `issues_by_category`
   - Added `filename` parameter and field

2. **`server/services/validation_service.py`**:
   - Extract filename from job record
   - Pass filename to `format_validation_result()`

## Testing

Run validation endpoint again to verify:
- No double counting in severity counts
- Proper category assignment
- Filename included in results

