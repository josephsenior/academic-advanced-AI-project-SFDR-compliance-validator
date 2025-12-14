"""Simple endpoint tester for the Document Validation API.
Run after starting the API server (default http://127.0.0.1:5000).
"""

import requests
import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"

endpoints = [
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/list"),
]

print(f"Testing endpoints against {BASE}")
for method, path in endpoints:
    url = BASE + path
    try:
        if method == "GET":
            r = requests.get(url, timeout=10)
        else:
            r = requests.request(method, url, timeout=10)
        try:
            body = r.json()
        except Exception:
            body = r.text
        print(f"{method} {path} -> {r.status_code}\n{body}\n")
    except Exception as e:
        print(f"{method} {path} failed: {e}\n")

# Basic negative test: validate a non-existent document
fake_id = "00000000-0000-0000-0000-000000000000"
try:
    r = requests.post(f"{BASE}/api/v1/validate/{fake_id}", json={}, timeout=10)
    print(f"POST /api/v1/validate/{fake_id} -> {r.status_code} {r.text}\n")
except Exception as e:
    print(f"POST validate failed: {e}\n")

print("Done.")
