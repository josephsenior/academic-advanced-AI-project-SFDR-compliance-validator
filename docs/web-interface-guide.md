# Web Interface - Quick Start Guide

## Installation

First, install Flask (if not already installed):

```bash
pip install flask werkzeug
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Running the Web Interface

### Option 1: Direct Python

```bash
python app.py
```

### Option 2: Flask Command

```bash
flask --app app run
```

The server will start on `http://localhost:5000`

## Usage

1. **Open your browser** and navigate to `http://localhost:5000`
2. **Upload a PowerPoint file** (.pptx format)
3. **Select options**:
   - Auto-fix missing disclaimers (optional)
   - Use LLM for enhanced extraction (optional, slower)
4. **Click "Process Document"**
5. **Wait for processing** (you'll see progress steps)
6. **Review results** (validation stats and fixes applied)
7. **Download corrected document**

## Features

- [OK] Beautiful, minimalist interface
- [OK] Drag & drop file upload
- [OK] Real-time progress tracking
- [OK] Detailed validation results
- [OK] Download corrected document
- [OK] Shows fixes applied and manual review items

## Troubleshooting

### Port Already in Use

If port 5000 is busy, change it in `app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port number
```

### File Upload Issues

- Maximum file size: 50MB
- Only .pptx files are supported
- Make sure the file is not corrupted

### Processing Errors

- Check console output for detailed error messages
- Ensure all dependencies are installed
- Verify the document is a valid PowerPoint file

