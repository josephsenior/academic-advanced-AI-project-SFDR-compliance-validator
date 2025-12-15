import sys

# --- MONKEYPATCH START ---
# Fix for Pydantic v1 on Python 3.12 (ForwardRef._evaluate signature change)
# This resolves the "TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'"
# error that occurs when using LangChain (which uses Pydantic v1) on Python 3.12+.
try:
    import pydantic.v1.typing
    
    # Save original to avoid infinite recursion if we patch multiple times
    if not hasattr(pydantic.v1.typing, "_original_evaluate_forwardref"):
        pydantic.v1.typing._original_evaluate_forwardref = pydantic.v1.typing.evaluate_forwardref

    def _patched_evaluate_forwardref(type_, globalns, localns):
        # Check if we are on Python 3.12+
        if sys.version_info >= (3, 12):
            # Check if the type is a ForwardRef and has _evaluate
            if hasattr(type_, "_evaluate"):
                # Python 3.12 requires recursive_guard
                # We pass a set() as the guard
                return type_._evaluate(globalns, localns, recursive_guard=set())
        
        # Fallback for older Python or other types
        return pydantic.v1.typing._original_evaluate_forwardref(type_, globalns, localns)

    pydantic.v1.typing.evaluate_forwardref = _patched_evaluate_forwardref
    # print("Applied Pydantic v1 ForwardRef monkeypatch for Python 3.12")
except (ImportError, AttributeError):
    # print(f"Could not apply monkeypatch: {e}")
    pass
# --- MONKEYPATCH END ---
