"""Full endpoint tester for the Document Validation API.

This script will:
 - Check /api/v1/health and /api/v1/list
 - Upload a sample document + metadata
 - Start validation
 - Poll status until completed (or timeout)
 - Fetch results
 - Request fixes
 - Attempt to download corrected document and JSON report

Usage: python scripts/full_endpoint_test.py [BASE_URL]
"""

import requests
import sys
import time
import os
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
SAMPLE_DOC = Path("dataset/example_1/FINAL 47861-6PG-GB-ODDO BHF Algo Trend US-20250831vdef.pptx")
SAMPLE_METADATA = Path("dataset/example_1/metadata.json")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"Running full endpoint test against {BASE}")

def expect_ok(r):
    print(f"{r.request.method} {r.request.path_url} -> {r.status_code}")
    try:
        print(r.json())
    except Exception:
        print(r.text[:1000])

# Health
try:
    r = requests.get(BASE + "/api/v1/health", timeout=10)
    expect_ok(r)
except Exception as e:
    print("Health check failed:", e)
    sys.exit(1)

# List
try:
    r = requests.get(BASE + "/api/v1/list", timeout=10)
    expect_ok(r)
except Exception as e:
    print("List failed:", e)

# Upload
if not SAMPLE_DOC.exists():
    print("Sample document not found:", SAMPLE_DOC)
    sys.exit(1)

files = {"document": (SAMPLE_DOC.name, open(SAMPLE_DOC, "rb"), "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
if SAMPLE_METADATA.exists():
    files["metadata"] = (SAMPLE_METADATA.name, open(SAMPLE_METADATA, "rb"), "application/json")

print("Uploading document...")
try:
    r = requests.post(BASE + "/api/v1/upload", files=files, timeout=60)
    expect_ok(r)
    if r.status_code not in (200,201):
        print("Upload failed")
        sys.exit(1)
    data = r.json()
    doc_id = data.get("document_id")
    if not doc_id:
        print("Upload response missing document_id")
        sys.exit(1)
    print("Uploaded document_id:", doc_id)
except Exception as e:
    print("Upload exception:", e)
    sys.exit(1)

# Start validation
print("Starting validation...")
try:
    r = requests.post(f"{BASE}/api/v1/validate/{doc_id}", json={"options": {}}, timeout=10)
    expect_ok(r)
except Exception as e:
    print("Validate start failed:", e)

# Poll status
print("Polling status (timeout 180s)...")
start = time.time()
status = None
while time.time() - start < 180:
    try:
        r = requests.get(f"{BASE}/api/v1/status/{doc_id}", timeout=10)
        if r.status_code == 200:
            s = r.json()
            status = s.get("status")
            progress = s.get("progress")
            print(f"Status: {status} progress={progress}")
            if status in ("completed", "COMPLETED", "failed", "FAILED"):
                break
        else:
            print("Status fetch returned", r.status_code)
    except Exception as e:
        print("Status poll error:", e)
    time.sleep(3)

# Get results
print("Fetching results...")
try:
    r = requests.get(f"{BASE}/api/v1/results/{doc_id}", timeout=10)
    expect_ok(r)
    results = r.json() if r.status_code == 200 else None
except Exception as e:
    print("Get results failed:", e)
    results = None

# Apply fixes
print("Requesting automatic fixes...")
try:
    r = requests.post(f"{BASE}/api/v1/fix/{doc_id}", json={"fix_types": ["all"]}, timeout=60)
    expect_ok(r)
    fixes = r.json() if r.status_code == 200 else None
except Exception as e:
    print("Fix request failed:", e)
    fixes = None

# Download corrected
print("Attempting to download corrected document...")
try:
    r = requests.get(f"{BASE}/api/v1/download/{doc_id}?type=corrected", timeout=60)
    if r.status_code == 200:
        out_path = OUTPUT_DIR / f"corrected_{doc_id}.pptx"
        with open(out_path, "wb") as f:
            f.write(r.content)
        print("Saved corrected to", out_path)
    else:
        print("Download returned", r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)
except Exception as e:
    print("Download failed:", e)

# Download JSON report
print("Attempting to download JSON report...")
try:
    r = requests.get(f"{BASE}/api/v1/report/{doc_id}?format=json", timeout=30)
    if r.status_code == 200:
        out_path = OUTPUT_DIR / f"report_{doc_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(r.text)
        print("Saved report to", out_path)
    else:
        print("Report returned", r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)
except Exception as e:
    print("Report download failed:", e)

print("Full endpoint test complete.")
