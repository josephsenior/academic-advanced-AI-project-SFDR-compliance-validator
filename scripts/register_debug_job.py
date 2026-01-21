
import json
import os
from datetime import datetime, timezone

def register_job():
    persistence_file = "jobs_persistence.json"
    doc_id = "5432ef2e-c9e1-4569-b42a-9153c2692419"
    
    if os.path.exists(persistence_file):
        with open(persistence_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)
    else:
        jobs = {}

    if doc_id not in jobs:
        print(f"Registering job {doc_id}")
        jobs[doc_id] = {
            "document_id": doc_id,
            "filename": "FINAL 47861-6PG-FR-ODDO BHF Algo Trend US-20250831.pptx",
            "file_path": r"C:\Users\GIGABYTE\Desktop\Portfolio\Advanced Ai Project\dataset\example_1\FINAL 47861-6PG-FR-ODDO BHF Algo Trend US-20250831.pptx",
            "status": "completed",
            "progress": 100,
            "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "updated_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "extraction_result": {},
            "validation_result": {
                "compliance_issues": [] # Will be filled by fix endpoint if needed, or we can load it
            },
            "metadata": {"test": True},
            "error": None
        }
        
        # Try to load real validation result from desktop
        report_path = r"C:\Users\GIGABYTE\Desktop\validation_report_5432ef2e-c9e1-4569-b42a-9153c2692419.json"
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                jobs[doc_id]["validation_result"] = json.load(f)
        
        with open(persistence_file, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2)
        print("Persistence updated.")
    else:
        print(f"Job {doc_id} already exists.")

if __name__ == "__main__":
    register_job()
