"""
TOON serializer removed.

This module previously implemented a custom TOON (Text Object Oriented Notation)
serializer. The implementation has been removed. Importing this module will
raise ImportError to surface any remaining callers so they can be migrated to
JSON-based serialization.
"""

raise ImportError("TOON serializer has been removed; use JSON serialization instead")

