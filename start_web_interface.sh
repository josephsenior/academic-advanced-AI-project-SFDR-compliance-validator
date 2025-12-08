#!/bin/bash

echo "========================================"
echo "Document Correction Web Interface"
echo "========================================"
echo ""

# Check if Flask is installed
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Flask not found. Installing..."
    pip install flask werkzeug
    echo ""
fi

echo "Starting web server..."
echo ""
echo "Open your browser and navigate to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

python3 app.py

