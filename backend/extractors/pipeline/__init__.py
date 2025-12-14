"""
Pipeline package

Contains the extraction pipeline orchestrator.
"""

from .orchestrator import ExtractionPipeline, process_document

__all__ = ['ExtractionPipeline', 'process_document']

