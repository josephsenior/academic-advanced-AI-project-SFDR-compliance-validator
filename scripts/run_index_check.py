from backend.extractors.document_corrector import DocumentCorrector
from pptx import Presentation

def main():
    sample = "dataset/example_1/FINAL 47861-6PG-FR-ODDO BHF Algo Trend US-20250831.pptx"
    prs = Presentation(sample)
    c = DocumentCorrector()
    c._build_shape_indices(prs)
    print("OK: built indices for sample")

if __name__ == "__main__":
    main()

