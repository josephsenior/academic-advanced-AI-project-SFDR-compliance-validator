
import sys
import os
sys.path.append(os.getcwd())

try:
    print("Attempting to import ChartAnalyzer...")
    from backend.extractors.core.chart_analyzer import ChartAnalyzer
    print("Import successful.")
    
    print("Attempting to initialize ChartAnalyzer...")
    analyzer = ChartAnalyzer(use_llm=False) # Test without LLM first
    print("Initialization successful (no LLM).")
    
    try:
        analyzer_llm = ChartAnalyzer(use_llm=True)
        print("Initialization successful (with LLM).")
    except Exception as e:
        print(f"Initialization with LLM failed: {e}")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
