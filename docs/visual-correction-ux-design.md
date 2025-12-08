# Visual Correction UX Design

## User Flow

```
1. User uploads PPTX
   ↓
2. Display slide previews in UI
   ↓
3. Agent processes and corrects
   ↓
4. Show corrected slides with visual indicators
   - Highlighted changes
   - Added elements marked
   - Issues flagged
   ↓
5. User reviews each change
   - Accept/Reject per change
   - See before/after
   ↓
6. Generate final document with accepted changes
```

## Technical Approach

### 1. Slide Preview Generation
- Convert PPTX slides to images (PNG/JPEG)
- Use `python-pptx` + `Pillow` or `pdf2image` approach
- Display thumbnails in UI

### 2. Visual Change Indicators
- Overlay markers on corrected slides
- Color-coded annotations:
  - Green: Added content
  - Yellow: Modified content
  - Red: Issues flagged
- Tooltips with change details

### 3. Accept/Reject Interface
- Side-by-side comparison
- Per-change accept/reject buttons
- Summary of all changes
- Final document generation

