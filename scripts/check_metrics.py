
import sys
import os
sys.path.append(os.getcwd())

try:
    print("Attempting to import backend.utils.metrics...")
    import backend.utils.metrics  # noqa: F401
    print("Import successful.")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
