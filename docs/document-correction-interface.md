# Document Correction Interface - Implementation Plan

## Overview

Create an interface where users upload documents, the system validates them, and outputs a corrected version with fixes applied.

## Feasibility: ✅ **MEDIUM COMPLEXITY** - Definitely Possible

### What's Already Available
- ✅ Document extraction (PPTX, DOCX, PDF)
- ✅ Validation (Data Consistency, Disclaimers, Registration)
- ✅ Issue detection with precise locations (slide/page numbers)
- ✅ Libraries for document manipulation (`python-pptx`, `python-docx`)

### What Needs to Be Built
- 🔨 Document correction module
- 🔨 Fix application logic
- 🔨 Web interface (optional, can start with CLI/API)

---

## Architecture

```
User Uploads Document
    ↓
Extraction Pipeline (existing)
    ↓
Validation (existing)
    ↓
Document Corrector (NEW)
    ├─ Load original document
    ├─ Apply fixes based on validation results
    └─ Save corrected document
    ↓
Return Corrected Document + Report
```

---

## Implementation Approach

### Phase 1: Core Correction Module

Create `src/extractors/document_corrector.py`:

```python
class DocumentCorrector:
    """Apply validation fixes to documents"""
    
    def correct_document(
        self,
        original_path: str,
        validation_result: DataConsistencyResult,
        disclaimer_result: Optional[DisclaimerValidationResult] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply fixes to document and save corrected version
        
        Returns:
            {
                "corrected_path": str,
                "fixes_applied": List[Dict],
                "fixes_failed": List[Dict]
            }
        """
```

### Phase 2: Fix Types

#### 1. Source/Date Fixes (Easy)
- **Issue**: Missing source/date on tables/charts
- **Fix**: Add footnote or text box with "Source: X | Date: Y"
- **Location**: Slide/page number from validation result

#### 2. Disclaimer Fixes (Medium)
- **Issue**: Missing disclaimers
- **Fix**: Add disclaimer text to appropriate slide
- **Location**: Based on disclaimer rules

#### 3. Numerical Corrections (Hard - Manual Review)
- **Issue**: Numerical inconsistencies
- **Fix**: **Flag for manual review** (don't auto-correct numbers)
- **Reason**: Numbers need human verification

#### 4. Cross-Reference Fixes (Hard - Manual Review)
- **Issue**: Performance mismatches
- **Fix**: **Flag for manual review**

### Phase 3: Supported Formats

#### PowerPoint (.pptx) - **EASIEST**
- ✅ Can add text boxes for sources/dates
- ✅ Can add footnotes
- ✅ Can modify table notes
- ✅ Can add disclaimer slides

#### Word (.docx) - **MEDIUM**
- ✅ Can add footnotes
- ✅ Can modify text
- ✅ Can add disclaimer sections

#### PDF - **HARDEST**
- ❌ Cannot easily modify PDFs
- ⚠️ Would need to convert to editable format first
- 💡 Alternative: Generate annotated PDF with comments

---

## Example Implementation

### PowerPoint Correction

```python
from pptx import Presentation
from pptx.util import Inches, Pt

class PowerPointCorrector:
    def add_source_date_note(
        self,
        slide: Slide,
        source_name: str,
        date: str,
        location: str = "bottom"
    ):
        """Add source/date note to slide"""
        # Add text box at bottom of slide
        left = Inches(0.5)
        top = Inches(6.5)  # Near bottom
        width = Inches(9)
        height = Inches(0.5)
        
        textbox = slide.shapes.add_textbox(left, top, width, height)
        text_frame = textbox.text_frame
        text_frame.text = f"Source: {source_name} | Data as of {date}"
        
        # Format text
        paragraph = text_frame.paragraphs[0]
        paragraph.font.size = Pt(9)
        paragraph.font.color.rgb = RGBColor(128, 128, 128)
```

### Word Correction

```python
from docx import Document
from docx.shared import Pt, RGBColor

class WordCorrector:
    def add_footer_note(
        self,
        paragraph,
        source_name: str,
        date: str
    ):
        """Add source/date as footnote"""
        footnote = paragraph.add_footnote(
            f"Source: {source_name} | Data as of {date}"
        )
```

---

## Interface Options

### Option 1: Web Interface (Recommended)

**Tech Stack**:
- **Backend**: Flask/FastAPI
- **Frontend**: React/Vue or simple HTML
- **File Upload**: Standard file upload
- **Download**: Return corrected file

**Flow**:
```
1. User uploads document
2. Show progress: "Processing..."
3. Show validation results
4. Show "Apply Fixes" button
5. Generate corrected document
6. Download corrected file
```

### Option 2: CLI Tool

```bash
python correct_document.py input.pptx --output corrected.pptx
```

### Option 3: API Endpoint

```python
POST /api/correct-document
{
    "file": <uploaded_file>,
    "apply_fixes": ["source_date", "disclaimers"],
    "auto_correct_numbers": false
}

Response:
{
    "corrected_file_url": "/downloads/corrected_abc123.pptx",
    "report": {...}
}
```

---

## Fix Application Strategy

### Automatic Fixes (Safe to Apply)

1. **Add Missing Source/Date**
   - ✅ Low risk
   - ✅ Clear validation rules
   - ✅ Easy to verify

2. **Add Missing Disclaimers**
   - ✅ Based on glossary rules
   - ✅ Standardized text
   - ⚠️ Need to verify placement

### Manual Review Required

1. **Numerical Corrections**
   - ❌ Don't auto-correct
   - ✅ Flag in report
   - ✅ Highlight in document (comments/annotations)

2. **Cross-Reference Issues**
   - ❌ Don't auto-correct
   - ✅ Flag in report

---

## Implementation Steps

### Step 1: Create Document Corrector Module

```python
# src/extractors/document_corrector.py

class DocumentCorrector:
    def __init__(self):
        self.supported_formats = {
            '.pptx': self._correct_pptx,
            '.docx': self._correct_docx,
            '.pdf': self._annotate_pdf  # Add comments instead
        }
    
    def correct(
        self,
        original_path: str,
        validation_result: DataConsistencyResult,
        output_path: Optional[str] = None
    ) -> CorrectionResult:
        """Main correction entry point"""
```

### Step 2: Implement PowerPoint Corrector

```python
def _correct_pptx(
    self,
    file_path: str,
    validation_result: DataConsistencyResult,
    output_path: str
):
    prs = Presentation(file_path)
    
    # Apply source/date fixes
    for issue in validation_result.source_date_issues:
        if issue.issue_type in ["missing_source", "missing_date", "both_missing"]:
            slide = prs.slides[issue.slide_number - 1]  # 0-indexed
            self._add_source_date_to_slide(slide, issue)
    
    # Save corrected presentation
    prs.save(output_path)
```

### Step 3: Create Web Interface

```python
# app.py (Flask example)

@app.route('/upload', methods=['POST'])
def upload_and_correct():
    file = request.files['document']
    
    # Save uploaded file
    upload_path = save_upload(file)
    
    # Run pipeline
    pipeline = ExtractionPipeline()
    result = pipeline.process_document(upload_path)
    
    # Validate
    agent = DataConsistencyAgent()
    validation = agent.validate(
        result['extraction_result'],
        result['metadata']
    )
    
    # Correct document
    corrector = DocumentCorrector()
    correction = corrector.correct(
        upload_path,
        validation
    )
    
    return jsonify({
        "corrected_file": correction['corrected_path'],
        "validation_report": validation.model_dump()
    })
```

---

## Complexity Assessment

### Easy (1-2 days)
- ✅ Add source/date notes to PowerPoint slides
- ✅ Add source/date footnotes to Word documents
- ✅ Basic CLI tool

### Medium (3-5 days)
- ⚠️ Add disclaimers to documents
- ⚠️ Web interface with file upload/download
- ⚠️ Fix placement logic (where to add notes)

### Hard (1-2 weeks)
- ❌ PDF modification (would need conversion)
- ❌ Complex layout preservation
- ❌ Multi-language disclaimer placement

---

## Recommended Approach

### MVP (Minimum Viable Product)

1. **Start with PowerPoint only** (easiest format)
2. **Fix only source/date issues** (safest fixes)
3. **CLI tool first** (faster to build)
4. **Add web interface later**

### Example MVP Usage

```python
from src.extractors.pipeline import ExtractionPipeline
from src.extractors.data_consistency_agent import DataConsistencyAgent
from src.extractors.document_corrector import DocumentCorrector

# Process document
pipeline = ExtractionPipeline()
result = pipeline.process_document("input.pptx")

# Validate
agent = DataConsistencyAgent()
validation = agent.validate(result['extraction_result'])

# Correct
corrector = DocumentCorrector()
correction = corrector.correct(
    "input.pptx",
    validation,
    output_path="corrected.pptx"
)

print(f"✅ Corrected document saved: {correction['corrected_path']}")
print(f"   Fixes applied: {len(correction['fixes_applied'])}")
```

---

## Next Steps

1. ✅ Create `DocumentCorrector` class
2. ✅ Implement PowerPoint source/date fixes
3. ✅ Test with sample documents
4. ✅ Add disclaimer fixes
5. ✅ Create web interface
6. ✅ Add Word document support

---

## Questions to Consider

1. **Should we auto-correct numbers?**
   - Recommendation: **No** - flag for manual review

2. **What about formatting?**
   - Preserve original formatting as much as possible
   - Use standard styles for added content

3. **How to handle conflicts?**
   - If source exists but date is wrong, replace or add?
   - Recommendation: Add new note, don't modify existing

4. **Version control?**
   - Keep original file
   - Save corrected version with suffix: `_corrected.pptx`

