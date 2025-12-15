"""
Pipeline package

Contains the extraction pipeline orchestrator.
"""

from .orchestrator import ExtractionPipeline, process_document, PIPELINE_VERSION

__all__ = ['ExtractionPipeline', 'process_document', 'PIPELINE_VERSION']

