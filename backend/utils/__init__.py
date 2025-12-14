"""
Utility modules for the extraction pipeline
"""

# Re-export from new modular structure for backward compatibility

# Serialization
from .serialization import dump_toon, load_toon

# Reporting
from .reporting import ValidationReportGenerator

# Cache
try:
    from .cache import get_llm_cache, LLMCache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    get_llm_cache = None
    LLMCache = None

# Processing
try:
    from .processing import ChartBatchProcessor
    PROCESSING_AVAILABLE = True
except ImportError:
    PROCESSING_AVAILABLE = False
    ChartBatchProcessor = None

# Rendering
try:
    from .rendering import render_slides_to_images
    RENDERING_AVAILABLE = True
except ImportError:
    RENDERING_AVAILABLE = False
    render_slides_to_images = None

# Matching
try:
    from .matching import TextMatcher
    MATCHING_AVAILABLE = True
except ImportError:
    MATCHING_AVAILABLE = False
    TextMatcher = None

# Metrics
try:
    from .metrics.core import MetricsCollector, ValidationMetric, APIUsageMetric, PerformanceMetric
    from .metrics import get_metrics_collector
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    MetricsCollector = None
    ValidationMetric = None
    APIUsageMetric = None
    PerformanceMetric = None
    get_metrics_collector = None

# Reference data manager
try:
    from .reference_data_manager.core import ReferenceDataManager
    REFERENCE_DATA_AVAILABLE = True
except ImportError:
    REFERENCE_DATA_AVAILABLE = False
    ReferenceDataManager = None

__all__ = [
    'dump_toon',
    'load_toon',
    'ValidationReportGenerator',
]

if CACHE_AVAILABLE:
    __all__.extend(['get_llm_cache', 'LLMCache'])

if PROCESSING_AVAILABLE:
    __all__.append('ChartBatchProcessor')

if RENDERING_AVAILABLE:
    __all__.append('render_slides_to_images')

if MATCHING_AVAILABLE:
    __all__.append('TextMatcher')

if METRICS_AVAILABLE:
    __all__.extend([
        'MetricsCollector',
        'ValidationMetric',
        'APIUsageMetric',
        'PerformanceMetric',
        'get_metrics_collector',
    ])

if REFERENCE_DATA_AVAILABLE:
    __all__.append('ReferenceDataManager')
