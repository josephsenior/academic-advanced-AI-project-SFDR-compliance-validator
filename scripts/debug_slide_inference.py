
import sys
import os
import logging

# Add backend to path
sys.path.append(os.getcwd())

from backend.extractors.core.document_extractor import DocumentExtractor
from backend.extractors.validators.utils import infer_performance_slide, infer_slide_containing_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_slide_inference(file_path):
    print(f"Analyzing file: {file_path}")
    
    # 1. Extract
    extractor = DocumentExtractor()
    extraction_result = extractor.extract(file_path)
    
    # 2. Inspect Performance Sections
    perf_sections = extraction_result.get('performance_sections', [])
    print(f"\n[Performance Sections]: {len(perf_sections)} found")
    for idx, section in enumerate(perf_sections):
        print(f"  Section {idx+1}: Slide {section.get('slide_number')} - Content snippet: {str(section)[:100]}...")
        
    # 3. Inspect Slides
    print("\n[Slide Analysis]")
    slides = extraction_result.get('slides', [])
    for i, slide in enumerate(slides, 1):
        content = (slide.get('content', '') or slide.get('text', ''))[:100].replace('\n', ' ')
        print(f"  Slide {i}: {content}...")
        
        # Check for performance keywords
        perf_keywords = ['performance', 'rendement', 'ytd', '1y', '3y', '5y', '10y', 'benchmark', 'indice']
        found_keywords = [k for k in perf_keywords if k in content.lower()]
        if found_keywords:
            print(f"    -> Contains performance keywords: {found_keywords}")
            
    # 4. Test Infer Performance Slide
    inferred_slide = infer_performance_slide(extraction_result, perf_sections)
    print(f"\n[Inferred Performance Slide]: {inferred_slide}")
    
    # 5. Test Generic Inference
    morningstar_slide = infer_slide_containing_text(extraction_result, ['morningstar'])
    print(f"[Inferred Morningstar Slide]: {morningstar_slide}")
    
    portfolio_slide = infer_slide_containing_text(extraction_result, ['portfolio', 'holdings', 'top 10'])
    print(f"[Inferred Portfolio Slide]: {portfolio_slide}")

if __name__ == "__main__":
    file_path = "dataset/example_3/3 - FINAL CLEAN-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx"
    analyze_slide_inference(file_path)
