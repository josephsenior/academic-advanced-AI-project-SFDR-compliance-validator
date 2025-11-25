"""
Test Chart Analyzer Structured Output

Tests the improved prompt and parsing to verify structured JSON output.
"""

import os
import sys
import base64
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PIL import Image, ImageDraw
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

from src.extractors.chart_analyzer import ChartAnalyzer


def create_realistic_chart_image() -> bytes:
    """Create a more realistic financial chart image"""
    if not HAS_DEPS:
        return None
    
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw title
    draw.text((200, 20), "Performance Comparison", fill='black')
    
    # Draw axes
    draw.line([(50, 300), (550, 300)], fill='black', width=2)  # X-axis
    draw.line([(50, 50), (50, 300)], fill='black', width=2)    # Y-axis
    
    # Draw Y-axis label
    draw.text((10, 150), "Return %", fill='black')
    
    # Draw bars (performance data)
    bars = [
        (80, 200, 150, 300, "Fund", "10.5%"),
        (180, 220, 250, 300, "Benchmark", "8.0%"),
        (280, 180, 350, 300, "Sector", "9.2%"),
    ]
    
    for x1, y1, x2, y2, label, value in bars:
        draw.rectangle([x1, y1, x2, y2], fill='blue', outline='black')
        draw.text((x1, y1 - 20), value, fill='black')
        draw.text((x1, 310), label, fill='black')
    
    # Draw X-axis label
    draw.text((250, 330), "1Y Performance", fill='black')
    
    # Draw source and date (CRITICAL for compliance)
    draw.text((50, 360), "Source: Bloomberg", fill='gray')
    draw.text((200, 360), "Date: 31/08/2025", fill='gray')
    
    # Convert to bytes
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()


def test_structured_output():
    """Test that chart analyzer produces well-structured output"""
    print("=" * 60)
    print("Chart Analyzer Structured Output Test")
    print("=" * 60)
    print()
    
    if not HAS_DEPS:
        print("[WARNING] Missing PIL, skipping test")
        return False
    
    # Check if environment variables are set
    api_key = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
    base_url = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
    
    if not api_key or not base_url:
        print("[ERROR] API credentials not found in environment variables.")
        print("   Please set TOKEN_FACTORY_API_KEY (or LLM_API_KEY) and")
        print("   TOKEN_FACTORY_BASE_URL (or LLM_BASE_URL) in your environment.")
        return False
    
    try:
        analyzer = ChartAnalyzer(use_llm=True)
        
        if not analyzer.use_llm:
            print("[ERROR] Chart analyzer LLM not initialized")
            return False
        
        print("Creating realistic chart image...")
        image_bytes = create_realistic_chart_image()
        
        print("Analyzing chart with improved prompt...")
        result = analyzer.analyze_chart_image(image_bytes)
        
        print()
        print("Analysis Results:")
        print(f"  Is Chart: {result.is_chart}")
        print(f"  Confidence: {result.confidence}")
        
        if result.metadata:
            print(f"  Chart Type: {result.metadata.chart_type}")
            print(f"  Title: {result.metadata.title}")
            print(f"  Has Source: {result.metadata.has_source}")
            print(f"  Has Date: {result.metadata.has_date}")
            if result.metadata.source_text:
                print(f"  Source Text: {result.metadata.source_text}")
            if result.metadata.date_text:
                print(f"  Date Text: {result.metadata.date_text}")
        
        print(f"  Data Points: {len(result.data_points)}")
        for i, point in enumerate(result.data_points[:3], 1):
            print(f"    {i}. {point.label}: {point.value}%")
        
        print(f"  Performance Values: {len(result.performance_values)}")
        for i, perf in enumerate(result.performance_values[:3], 1):
            print(f"    {i}. {perf.get('period', 'N/A')}: {perf.get('value', 'N/A')}%")
        
        if result.notes:
            print(f"  Notes: {result.notes[:100]}")
        
        print()
        
        # Validate structure
        checks = []
        
        # Check 1: Should detect as chart
        checks.append(("Detected as chart", result.is_chart == True))
        
        # Check 2: Should have metadata
        checks.append(("Has metadata", result.metadata is not None))
        
        # Check 3: Should extract source/date
        if result.metadata:
            checks.append(("Detected source", result.metadata.has_source == True))
            checks.append(("Detected date", result.metadata.has_date == True))
        
        # Check 4: Should extract data points
        checks.append(("Extracted data points", len(result.data_points) > 0))
        
        print("Validation Checks:")
        all_passed = True
        for check_name, passed in checks:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status}: {check_name}")
            if not passed:
                all_passed = False
        
        print()
        if all_passed:
            print("[SUCCESS] All validation checks passed!")
        else:
            print("[WARNING] Some checks failed - prompt may need further tuning")
        
        return all_passed
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_structured_output()
    sys.exit(0 if success else 1)

