"""
Document extraction modules
"""

# Re-export from new modular structure for backward compatibility

# Parsers
from .parsers import (
    FilenameParser,
    parse_filename,
    RegistrationParser,
    FundRegistration
)

# Extractors
from .core.document_extractor import (
    DocumentExtractor,
    extract_document
)
from .core.metadata_extractor import (
    MetadataExtractor,
    extract_metadata
)
from .core.feature_extractor import (
    ContentFeatureExtractor,
    extract_content_features
)
from .core.chart_analyzer import (
    ChartAnalyzer,
    ChartAnalysis,
    ChartMetadata,
    ChartDataPoint,
    analyze_chart
)

# Validators
from .validators import (
    DisclaimerValidator,
    FundTypeValidator,
    PerformanceValidator,
    CountryValidator,
    ContentValidator,
    EsgValidator
)

# Try to import ESG validators (optional)
try:
    from .validators import (
        ESGAnalyzer,
        ESGLevel,
        ESGMentions,
        ESGViolation
    )
    ESG_AVAILABLE = True
except ImportError:
    ESG_AVAILABLE = False
    ESGAnalyzer = None
    ESGLevel = None
    ESGMentions = None
    ESGViolation = None

# Config
from .config import (
    get_token_factory_config,
    get_vision_model_config,
    create_feature_extractor
)

# Pipeline
from .pipeline import ExtractionPipeline, process_document

# Agents
from .agents.data_consistency_agent import DataConsistencyAgent
from .agents.models import DataConsistencyResult
from .agents.reference_data import ReferenceData

# Try to import create_reference_data_from_dict if available
try:
    from .agents.data_consistency_agent import create_reference_data_from_dict
except ImportError:
    create_reference_data_from_dict = None

# Document family
from .document_family import DocumentFamilyDetector, detect_document_family

# Models
from .models import (
    ContentFeatures,
    ESGFeature,
    PerformanceFeature,
    CountryFeature,
    CompanyFeature,
    FinancialTermFeature
)

# Document corrector
from .document_corrector import DocumentCorrector

# Compliance rules
from .rules import (
    ComplianceIssue,
    ComplianceIssueType,
    PerformanceRules,
    ClientType,
    FundType,
    GeneralRules
)

__all__ = [
    # Parsers
    'FilenameParser',
    'parse_filename',
    'RegistrationParser',
    'FundRegistration',
    # Extractors
    'DocumentExtractor',
    'extract_document',
    'MetadataExtractor',
    'extract_metadata',
    'ContentFeatureExtractor',
    'extract_content_features',
    'ChartAnalyzer',
    'ChartAnalysis',
    'ChartMetadata',
    'ChartDataPoint',
    'analyze_chart',
    # Validators
    'DisclaimerValidator',
    'FundTypeValidator',
    'PerformanceValidator',
    'CountryValidator',
    'ContentValidator',
    'EsgValidator',
    # Config
    'get_token_factory_config',
    'get_vision_model_config',
    'create_feature_extractor',
    # Pipeline
    'ExtractionPipeline',
    'process_document',
    # Agents
    'DataConsistencyAgent',
    'DataConsistencyResult',
    'ReferenceData',
    # Document family
    'DocumentFamilyDetector',
    'detect_document_family',
    # Models
    'ContentFeatures',
    'ESGFeature',
    'PerformanceFeature',
    'CountryFeature',
    'CompanyFeature',
    'FinancialTermFeature',
    # Document corrector
    'DocumentCorrector',
    # Compliance rules
    'ComplianceIssue',
    'ComplianceIssueType',
    'PerformanceRules',
    'ClientType',
    'FundType',
    'GeneralRules',
]

# Add ESG exports if available
if ESG_AVAILABLE:
    __all__.extend([
        'ESGAnalyzer',
        'ESGLevel',
        'ESGMentions',
        'ESGViolation',
    ])

if create_reference_data_from_dict:
    __all__.append('create_reference_data_from_dict')
