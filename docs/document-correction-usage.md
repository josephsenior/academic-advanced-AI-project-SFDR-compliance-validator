# Document Correction Tool - Usage Guide

## Overview

The Document Correction Tool automatically fixes validation issues in PowerPoint documents and flags items that require manual review.

## Features

### Auto-Fixes (Applied Automatically)
- [OK] **Missing Source/Date**: Adds source and date notes to slides with missing information
- [OK] **Missing Disclaimers**: Adds required disclaimers (when `--fix-disclaimers` is used)

### Manual Review Required (Flagged, Not Auto-Fixed)
- [WARNING] **Numerical Inconsistencies**: Values that don't match reference documents
- [WARNING] **Cross-Reference Issues**: Performance data mismatches between text and tables

## Installation

No additional installation required. Uses existing dependencies:
- `python-pptx` (already in requirements.txt)

## Usage

### Basic Usage

```bash
python scripts/correct_document.py input.pptx
```

This will:
1. Process the document
2. Validate it
3. Apply source/date fixes
4. Save corrected version as `input_corrected.pptx`

### Specify Output File

```bash
python scripts/correct_document.py input.pptx --output corrected.pptx
```

### Fix Disclaimers Too

```bash
python scripts/correct_document.py input.pptx --fix-disclaimers
```

### With Metadata File

```bash
python scripts/correct_document.py input.pptx --metadata metadata.json
```

### With Reference Data (for numerical validation)

```bash
python scripts/correct_document.py input.pptx --reference-data reference.json
```

### Full Example

```bash
python scripts/correct_document.py \
    "dataset/example_1/document.pptx" \
    --metadata "dataset/example_1/metadata.json" \
    --output "corrected_document.pptx" \
    --fix-disclaimers
```

## Output

### Corrected Document

The tool creates a new PowerPoint file with fixes applied:
- Source/date notes added to slides with missing information
- Disclaimers added (if `--fix-disclaimers` is used)
- Original document is not modified

### Console Output

The tool provides detailed output:

```
[OK] Document processed: <document_id>
[OK] Validation completed
   Status: ERROR
   Source/Date issues: 4
   Numerical inconsistencies: 0
   Cross-reference issues: 1

[OK] Correction completed!
   Corrected file: corrected.pptx
   Fixes applied: 1
   Fixes failed: 0
   Manual review required: 1
```

## What Gets Fixed

### Source/Date Fixes

**Issue**: Table or chart missing source and/or date information

**Fix Applied**: Adds a text box at the bottom of the slide with:
```
Source: [To be specified] | Data as of 2025-11-26
```

**Note**: The source name is set to "[To be specified]" as a placeholder. You should manually update this with the actual source name.

### Disclaimer Fixes

**Issue**: Missing required disclaimers

**Fix Applied**: Adds disclaimer text to the last slide of the presentation

**Note**: Only applied when `--fix-disclaimers` flag is used

## What Requires Manual Review

### Numerical Inconsistencies

These are **not** auto-corrected because:
- Numbers need human verification
- May be intentional differences
- Could indicate data errors that need investigation

**Example**:
```
Manual Review Required:
  • numerical_inconsistency: Performance mismatch at slide 3: 
    document shows 10.5% but reference shows 10.0%
```

### Cross-Reference Issues

These are **not** auto-corrected because:
- May indicate copy-paste errors
- Need context to determine correct value
- Could be legitimate differences

**Example**:
```
Manual Review Required:
  • cross_reference: Performance mismatch: text shows 10.5% 
    but table shows 10.0% at slide 3
```

## Reference Data Format

If using `--reference-data`, provide a JSON file with this structure:

```json
{
  "fund_name": "ODDO BHF Algo Trend US",
  "performance_data": {
    "1y": {"net": 10.5},
    "3y": {"net": 8.2}
  },
  "table_data": {
    "fund": 10.5,
    "benchmark": 8.0
  },
  "source_document": "Prospectus"
}
```

## Limitations

### Current Limitations

1. **PowerPoint Only**: Currently only supports `.pptx` format
2. **Source Placeholder**: Source names are set to "[To be specified]" - manual update required
3. **No Number Correction**: Numerical issues are flagged but not auto-corrected
4. **Basic Disclaimer Placement**: Disclaimers are added to last slide (may need repositioning)

### Future Enhancements

- [ ] Word document (.docx) support
- [ ] PDF annotation support
- [ ] Smart source name detection
- [ ] Better disclaimer placement logic
- [ ] Web interface

## Troubleshooting

### "Unsupported format" Error

Only `.pptx` files are currently supported. Convert other formats first.

### "Pipeline failed" Warning

If you see this warning but extraction succeeded, the tool will continue. This is usually a JSON serialization issue that doesn't affect correction.

### No Fixes Applied

If no fixes are applied, check:
1. Are there any source/date issues? (Check validation output)
2. Are issues severity "error" or "warning"? (Only errors are auto-fixed)
3. Are slide numbers valid? (Check if slides exist in presentation)

## Examples

### Example 1: Basic Correction

```bash
python scripts/correct_document.py presentation.pptx
```

**Result**: `presentation_corrected.pptx` with source/date fixes applied

### Example 2: Full Correction with Disclaimers

```bash
python scripts/correct_document.py \
    presentation.pptx \
    --output final_version.pptx \
    --fix-disclaimers \
    --metadata metadata.json
```

**Result**: `final_version.pptx` with source/date and disclaimer fixes applied

## Integration

### Python API

You can also use the corrector programmatically:

```python
from src.extractors.pipeline import ExtractionPipeline
from src.extractors.data_consistency_agent import DataConsistencyAgent
from src.extractors.document_corrector import DocumentCorrector

# Process and validate
pipeline = ExtractionPipeline()
result = pipeline.process_document("input.pptx")

agent = DataConsistencyAgent()
validation = agent.validate(result['extraction_result'])

# Correct
corrector = DocumentCorrector()
correction = corrector.correct(
    "input.pptx",
    validation,
    output_path="corrected.pptx"
)

print(f"Fixes applied: {len(correction.fixes_applied)}")
print(f"Manual review: {len(correction.manual_review_required)}")
```

## Best Practices

1. **Always Review**: Even auto-fixed items should be reviewed
2. **Update Source Names**: Replace "[To be specified]" with actual source names
3. **Check Manual Review Items**: Address flagged numerical and cross-reference issues
4. **Keep Originals**: The original document is never modified
5. **Test First**: Test with a copy before processing important documents

