"""
Test Chart Analyzer API Compatibility

Tests the Token Factory API with the provided credentials to verify:
1. API connection works
2. Vision model (LLaVA) is accessible
3. Image format is compatible
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

# Note: Functions prefixed with _ are not pytest tests - they're called from main()

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    from PIL import Image
    HAS_DEPS = True
except ImportError as e:
    print(f"Missing dependencies: {e}")
    HAS_DEPS = False


def create_test_image() -> bytes:
    """Create a simple test image (a basic chart-like image)"""
    if not HAS_DEPS or Image is None:
        return None
    
    # Create a simple test image - a basic bar chart representation
    img = Image.new('RGB', (400, 300), color='white')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Draw a simple bar chart
    bars = [(50, 200, 100, 250), (150, 150, 200, 250), (250, 100, 300, 250)]
    for bar in bars:
        draw.rectangle(bar, fill='blue')
    
    # Add some text
    draw.text((50, 50), "Test Chart", fill='black')
    draw.text((50, 260), "Source: Test", fill='gray')
    
    # Convert to bytes
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()


def _test_api_connection():
    """Test basic API connection"""
    print("=" * 60)
    print("Test 1: API Connection Test")
    print("=" * 60)
    
    # Load from environment variables
    api_key = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
    base_url = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
    model_name = os.getenv("LLM_VISION_MODEL", "hosted_vllm/llava-1.5-7b-hf")
    
    if not api_key or not base_url:
        print("[ERROR] API credentials not found in environment variables.")
        print("   Please set TOKEN_FACTORY_API_KEY (or LLM_API_KEY) and")
        print("   TOKEN_FACTORY_BASE_URL (or LLM_BASE_URL) in your environment.")
        return False, None
    
    try:
        llm = ChatOpenAI(
            model=model_name,
            temperature=0.0,
            api_key=api_key,
            base_url=base_url
        )
        
        # Test with simple text first
        print(f"Testing connection to: {base_url}")
        print(f"Using model: {model_name}")
        print(f"API Key: {api_key[:10]}...")
        print()
        
        response = llm.invoke("Say 'API connection successful' if you can read this.")
        print(f"[SUCCESS] Text API Response: {response.content[:100]}")
        return True, llm
        
    except Exception as e:
        print(f"[ERROR] API Connection Failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def _test_vision_api(llm):
    """Test vision API with an image"""
    print()
    print("=" * 60)
    print("Test 2: Vision API Test (Image Analysis)")
    print("=" * 60)
    
    if llm is None:
        print("[WARNING] LLM not available, skipping vision test")
        return False
    
    if not HAS_DEPS:
        print("[WARNING] Missing dependencies (PIL), skipping vision test")
        return False
    
    try:
        # Create test image
        print("Creating test image...")
        image_bytes = create_test_image()
        if not image_bytes:
            print("[ERROR] Could not create test image")
            return False
        
        # Convert to base64
        img_base64 = base64.b64encode(image_bytes).decode()
        print(f"[SUCCESS] Test image created ({len(image_bytes)} bytes)")
        print()
        
        # Prepare message with image
        print("Sending image to vision model...")
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Describe what you see in this image. Is it a chart, graph, or other visualization? If it's a chart, what type is it?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_base64}"
                    }
                }
            ]
        )
        
        # Call API
        response = llm.invoke([message])
        print(f"[SUCCESS] Vision API Response: {response.content[:200]}")
        print()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Vision API Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def _test_chart_analyzer_integration():
    """Test the actual ChartAnalyzer class"""
    print()
    print("=" * 60)
    print("Test 3: Chart Analyzer Integration Test")
    print("=" * 60)
    
    try:
        from src.extractors.chart_analyzer import ChartAnalyzer
        
        # Check if environment variables are set
        api_key = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
        base_url = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
        
        if not api_key or not base_url:
            print("[ERROR] API credentials not found in environment variables.")
            print("   Please set TOKEN_FACTORY_API_KEY (or LLM_API_KEY) and")
            print("   TOKEN_FACTORY_BASE_URL (or LLM_BASE_URL) in your environment.")
            return False
        
        print("Initializing ChartAnalyzer...")
        analyzer = ChartAnalyzer(use_llm=True)
        
        if not analyzer.use_llm or not analyzer.llm:
            print("[ERROR] ChartAnalyzer failed to initialize LLM")
            return False
        
        print(f"[SUCCESS] ChartAnalyzer initialized")
        model_name = getattr(analyzer.llm, 'model_name', None) or getattr(analyzer.llm, '_model_name', None) or 'N/A'
        print(f"   Model: {model_name}")
        print()
        
        # Test with actual image
        if HAS_DEPS:
            image_bytes = create_test_image()
            if image_bytes:
                print("Testing chart analysis...")
                result = analyzer.analyze_chart_image(image_bytes)
                print(f"[SUCCESS] Chart analysis completed")
                print(f"   Is Chart: {result.is_chart}")
                print(f"   Confidence: {result.confidence}")
                if result.metadata:
                    print(f"   Chart Type: {result.metadata.chart_type}")
                if result.notes:
                    print(f"   Notes: {result.notes[:100]}")
                return True
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Chart Analyzer Integration Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Chart Analyzer API Compatibility Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: API Connection
    success, llm = _test_api_connection()
    results.append(("API Connection", success))
    
    if success and llm:
        # Test 2: Vision API
        vision_success = _test_vision_api(llm)
        results.append(("Vision API", vision_success))
    
    # Test 3: Chart Analyzer Integration
    integration_success = _test_chart_analyzer_integration()
    results.append(("Chart Analyzer Integration", integration_success))
    
    # Summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status}: {test_name}")
    
    all_passed = all(success for _, success in results)
    print()
    if all_passed:
        print("[SUCCESS] All tests passed! API format is compatible.")
    else:
        print("[WARNING] Some tests failed. Check errors above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

