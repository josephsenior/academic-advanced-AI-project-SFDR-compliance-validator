# Pydantic v1 + Python 3.12 Compatibility Fix

## Root Cause Analysis

### The Problem
The extraction pipeline was failing with:
```
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
```

This error occurred because:
1. **Python 3.12 Breaking Change**: Python 3.12 changed the signature of `typing.ForwardRef._evaluate()` to require `recursive_guard` as a **keyword-only argument**
2. **Pydantic v1 Incompatibility**: LangChain uses Pydantic v1 internally (via `pydantic.v1` namespace in Pydantic v2), which calls `ForwardRef._evaluate()` with positional arguments
3. **Initialization Cascade**: The error propagated during LangChain initialization, preventing any LLM features from loading

### Why It Wasn't Robust
Previous attempts to fix this using `try/except ImportError` blocks didn't address the root cause - the error occurred **during import**, not during usage. The imports failed before any code could execute, causing the pipeline to silently fall back to keyword-based detection.

## The Solution

### 1. Monkeypatch Pydantic v1's ForwardRef Handling
Created a centralized patch module at [src/utils/pydantic_v1_patch.py](../src/utils/pydantic_v1_patch.py):

```python
import sys

try:
    import pydantic.v1.typing
    
    if not hasattr(pydantic.v1.typing, "_original_evaluate_forwardref"):
        pydantic.v1.typing._original_evaluate_forwardref = pydantic.v1.typing.evaluate_forwardref

    def _patched_evaluate_forwardref(type_, globalns, localns):
        if sys.version_info >= (3, 12):
            if hasattr(type_, "_evaluate"):
                # Python 3.12+ requires recursive_guard as keyword argument
                return type_._evaluate(globalns, localns, recursive_guard=set())
        
        # Fallback for older Python
        return pydantic.v1.typing._original_evaluate_forwardref(type_, globalns, localns)

    pydantic.v1.typing.evaluate_forwardref = _patched_evaluate_forwardref
except (ImportError, AttributeError):
    pass
```

### 2. Apply Patch Before Any LangChain Imports
Modified all files that import LangChain to apply the patch first:
- [src/extractors/feature_extractor.py](../src/extractors/feature_extractor.py)
- [src/extractors/metadata_extractor.py](../src/extractors/metadata_extractor.py)
- [src/extractors/chart_analyzer.py](../src/extractors/chart_analyzer.py)
- [run_demo_pipeline.py](../run_demo_pipeline.py)

Pattern used:
```python
import sys
# Apply Pydantic v1 patch for Python 3.12 compatibility
try:
    from src.utils import pydantic_v1_patch
except ImportError:
    pass

# Now LangChain imports work
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
```

### 3. Fix Import Order for PydanticOutputParser
Changed from:
```python
from langchain_core.output_parsers import PydanticOutputParser  # Doesn't exist in langchain-core 0.3+
```

To:
```python
from langchain.output_parsers import PydanticOutputParser  # Correct location
```

### 4. Remove Invalid http_client Assignments
Removed problematic code that tried to set `http_client` attributes:
```python
# REMOVED - causes validation errors
# self.llm.http_client = sync_client
# self.llm.http_async_client = async_client
```

The `langchain-openai` library only accepts `httpx.AsyncClient` in the constructor's `http_client` parameter, not sync clients, and doesn't allow direct attribute assignment after initialization.

## Verification

After applying these fixes, the pipeline runs successfully with LLM features enabled:

```
[Step 5/6] Extracting content features using LLM...
  [OK] Extracted 2 ESG mentions
  [OK] Extracted 0 performance data points
  [OK] Extracted 1 country mentions
```

## Long-Term Solutions

### Option 1: Pin Dependencies (Recommended)
Create `requirements-pinned.txt`:
```
# Tested and working configuration
pydantic==2.9.1
langchain==0.3.0
langchain-core==0.3.0
langchain-openai==0.2.0
langsmith==0.1.134
```

### Option 2: Downgrade Python (If Possible)
If Python 3.11 is acceptable:
```bash
pyenv install 3.11.9
pyenv local 3.11.9
```

### Option 3: Wait for Upstream Fixes
Monitor these issues:
- [pydantic/pydantic#8764](https://github.com/pydantic/pydantic/issues/8764) - Pydantic v1 Python 3.12 compatibility
- [langchain-ai/langchain#14500](https://github.com/langchain-ai/langchain/issues/14500) - LangChain Python 3.12 support

## Files Modified

1. **New file**: [src/utils/pydantic_v1_patch.py](../src/utils/pydantic_v1_patch.py) - Centralized monkeypatch
2. **Modified**: [src/extractors/feature_extractor.py](../src/extractors/feature_extractor.py) - Apply patch before imports
3. **Modified**: [src/extractors/metadata_extractor.py](../src/extractors/metadata_extractor.py) - Apply patch before imports
4. **Modified**: [src/extractors/chart_analyzer.py](../src/extractors/chart_analyzer.py) - Apply patch before imports
5. **Modified**: [run_demo_pipeline.py](../run_demo_pipeline.py) - Apply patch before imports

## Testing
```bash
python run_demo_pipeline.py
```

Expected output:
- No import errors
- LLM features enabled
- Feature extraction successful
- Output files generated with features.json

## Conclusion

**Root Cause**: Python 3.12's breaking change to `typing.ForwardRef._evaluate()` signature incompatible with Pydantic v1's usage.

**Solution**: Monkeypatch `pydantic.v1.typing.evaluate_forwardref` to call `_evaluate()` with `recursive_guard` as keyword argument on Python 3.12+.

**Result**: Robust pipeline execution with full LLM functionality restored.
