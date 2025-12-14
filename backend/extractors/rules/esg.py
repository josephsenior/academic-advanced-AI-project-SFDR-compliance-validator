"""
ESG Compliance Rules

Section 4.1 - ESG Communication Rules (excluding professional funds).
"""

from dataclasses import dataclass


@dataclass
class ESGRules:
    """Section 4.1 - ESG Communication Rules (excluding professional funds)"""
    
    # ESG approach thresholds
    ENGAGEANTE_MIN_EXCLUSION_PCT: float = 20.0
    ENGAGEANTE_MIN_COVERAGE_PCT: float = 90.0
    
    # Communication limits
    ENGAGEANTE_NO_LIMIT: bool = True
    REDUITE_MAX_VOLUME_PCT: float = 10.0  # Max 10% of presentation volume
    LIMITEE_ONLY_FOR_INSTITUTIONAL_PRO: bool = True
    OTHER_FUNDS_ONLY_OBAM_EXCLUSIONS: bool = True
    
    # ESG keywords to detect
    ESG_KEYWORDS = [
        "ESG", "environnement", "environment", "Umwelt",
        "social", "sozial", "governance", "gouvernance",
        "durable", "sustainable", "nachhaltig",
        "responsable", "responsible", "verantwortlich",
        "ISR", "SRI", "carbon", "carbone", "Kohlenstoff",
        "climat", "climate", "Klima", "green", "vert", "grün",
        "impact", "éthique", "ethical", "ethisch"
    ]

