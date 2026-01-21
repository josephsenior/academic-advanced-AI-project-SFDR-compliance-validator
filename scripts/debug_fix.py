
import requests
import json

BASE_URL = "http://localhost:5000/api/v1"
DOC_ID = "05617c9a-9801-438a-9731-7f4f0cc83180" # Existing ID from logs

print(f"Calling /fix/{DOC_ID}...")
r = requests.post(f"{BASE_URL}/fix/{DOC_ID}?force=true")

print(f"Status: {r.status_code}")
if r.status_code == 200:
    res = r.json()
    print(f"Success! {res.get('fixes_applied')} fixes applied.")
    with open("debug_fix_latest.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print("Saved to debug_fix_latest.json")
else:
    print(f"Error: {r.text}")
