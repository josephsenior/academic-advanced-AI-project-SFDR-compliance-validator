Usage

1. Ensure Python venv is activated (if using the repository venv).
2. Install requirements: `pip install -r requirements.txt` (run from repo root).
3. Start the API server: `python api.py` (defaults to http://127.0.0.1:5000).
4. Run the tester: `python scripts/test_endpoints.py` or pass a base URL: `python scripts/test_endpoints.py http://localhost:5000`

The script performs simple health and list checks and attempts a negative validation request to confirm proper 404 handling.