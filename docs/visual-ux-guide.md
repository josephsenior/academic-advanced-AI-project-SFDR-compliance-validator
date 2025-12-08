# Visual Document Correction UX

## Overview

Simplified user experience for document correction:

1. **Upload** - User uploads a PowerPoint file
2. **Preview** - Original slides are displayed in the UI
3. **Process** - Agent processes and corrects the document
4. **Review** - Corrected slides shown with visual indicators
5. **Accept/Reject** - User reviews and accepts/denies each change
6. **Download** - Final document with accepted changes

## Features

- ✅ Visual slide preview
- ✅ Side-by-side comparison
- ✅ Change annotations on slides
- ✅ Accept/reject per change
- ✅ Clean, simple interface

## Running

```bash
python app_visual.py
```

Then open: http://localhost:5000

## Technical Details

### Slide Rendering
- Uses `python-pptx` to extract slide content
- Creates placeholder images (can be enhanced with actual rendering)
- Annotates slides with change markers

### Change Tracking
- Tracks all changes by slide number
- Records change type, position, and description
- Enables visual annotation

### Future Enhancements
- Actual slide rendering (comtypes on Windows, libreoffice on Linux)
- Side-by-side before/after view
- More detailed change annotations
- Selective change application

