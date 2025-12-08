@echo off
echo ========================================
echo Document Correction Web Interface
echo ========================================
echo.

REM Check if Flask is installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Flask not found. Installing...
    pip install flask werkzeug
    echo.
)

echo Starting web server...
echo.
echo Open your browser and navigate to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python app.py

pause

