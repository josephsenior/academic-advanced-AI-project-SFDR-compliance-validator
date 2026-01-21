import json
from pathlib import Path

from backend.extractors.document_corrector import DocumentCorrector

REPORT = Path("C:/Users/GIGABYTE/Desktop/validation_report_5432ef2e-c9e1-4569-b42a-9153c2692419.json")
SOURCE = Path("dataset/example_1/FINAL 47861-6PG-FR-ODDO BHF Algo Trend US-20250831.pptx")
OUT = Path("corrected_documents/5432ef2e-c9e1-4569-b42a-9153c2692419_corrected_v2.pptx")

def load_validation_report(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def build_disclaimer_result(validation_result):
    missing = validation_result.get("issues_by_category", {}).get("disclaimer", [])
    # Simple namespace object with attribute missing_disclaimers
    class R:
        pass
    r = R()
    r.missing_disclaimers = missing
    return r

def main():
    vr = load_validation_report(REPORT)
    corrector = DocumentCorrector()
    disclaimer_result = build_disclaimer_result(vr)
    result = corrector.correct(str(SOURCE), vr, disclaimer_result=disclaimer_result, output_path=str(OUT), auto_fix_disclaimers=True)
    print("Success:", result.success, "Applied:", len(result.fixes_applied))
    if result.fixes_applied:
        for f in result.fixes_applied:
            print(f)

if __name__ == "__main__":
    main()

