"""
Keyword Definitions

Centralized keyword lists for document analysis.
"""

# Legal disclaimers often include these anchors
DISCLAIMER_KEYWORDS = {
    "disclaimer",
    "legal notice",
    "risk warning",
    "important information",
    "performance disclaimer",
    "back-tested performance",
    "simulation of future performance",
}

# Glossary sections have a distinctive label in the template
GLOSSARY_KEYWORDS = {"glossary", "definitions"}

COUNTRY_SECTION_KEYWORDS = {
    "distribution": "distribution",
    "available": "available",
    "enregistr": "enregistr",  # captures enregistré/enregistrée
    "registr": "registr",
    "marketing": "commercialisation",
}

ISSUER_SECTION_KEYWORDS = {
    "top holdings",
    "principales positions",
    "top 10",
    "top issuers",
    "main holdings",
    "largest positions",
    "top positions",
}

LEGAL_NOTICE_KEYWORDS = [
    "oddo bhf asset management",
    "société de gestion",
    "management company",
    "regulated by",
    "autorité des marchés financiers",
]

DISCLAIMER_CATEGORIES = {
    # Mandatory disclaimers
    'obam_presentation': ["oddo bhf asset management", "obam", "oddo bhf am", "oddo bhf asset management sas", "oddo bhf am gmbh", "oddo bhf am lux"],
    'commercial_documentation': ["commercial documentation", "documentation commerciale", "commerciale dokumentation"],
    'commercial_documentation_raif': ["raif", "luxembourg funds-raif", "luxembourg funds raif", "fonds luxembourg-raif"],
    
    # Content-specific disclaimers
    'performance': ["past performance", "performances passées", "performance disclaimer", "past performance is not", "performances passées ne préjugent pas"],
    'esg_risk': ["esg", "sustainable", "article 8", "article 9", "article 6", "sustainability", "durabilité"],
    'issuers': ["issuer", "issuers", "emetteur", "émetteurs", "company logo", "logo", "entreprise mentionnée"],
    'simulation': ["simulation", "simulé", "forward-looking", "future performance", "projection", "prévision"],
    'backtest': ["back-tested", "backtested", "données arrière", "historique reconstruit", "back test", "back-test"],
    'new_offer': ["new product", "nouvelle offre", "nouvelle stratégie", "new strategy", "nouveau produit", "new offer"],
    'ytm': ["ytm", "ytw", "yield to maturity", "yield to worst", "yield-to-maturity", "yield-to-worst"],
    'opinion': ["opinion", "avis", "view", "vue", "forecast", "prévision"],
    'additional_information': ["additional information", "informations complémentaires", "zusätzliche informationen"],
    
    # Regulatory disclaimers
    'sfdr_article_6': ["article 6", "sfdr article 6", "article 6 sfdr"],
    'sfdr_article_8': ["article 8", "sfdr article 8", "article 8 sfdr"],
    'sfdr_article_9': ["article 9", "sfdr article 9", "article 9 sfdr"],
    'sfdr': ["sfdr", "sustainable finance disclosure regulation"],
    'money_market_fund': ["money market fund", "fonds monétaire", "geldmarktfonds", "mmf"],
    'sri': ["sri", "summary risk indicator", "indicateur de risque synthétique", "risikoindikator", "risk indicator"],
}


def detect_disclaimer_flags(text: str) -> bool:
    """Check if text contains disclaimer keywords."""
    lowered = text.lower()
    return any(keyword in lowered for keyword in DISCLAIMER_KEYWORDS)


def detect_glossary(text: str) -> bool:
    """Check if text contains glossary keywords."""
    lowered = text.lower()
    return any(keyword in lowered for keyword in GLOSSARY_KEYWORDS)


def detect_legal_notice(text: str) -> bool:
    """Check if text contains legal notice keywords."""
    lowered = text.lower()
    return any(keyword in lowered for keyword in LEGAL_NOTICE_KEYWORDS)


def categorize_disclaimer(text: str) -> list[str]:
    """Categorize disclaimer based on keywords."""
    categories = []
    lowered = text.lower()
    for category, keywords in DISCLAIMER_CATEGORIES.items():
        if any(keyword in lowered for keyword in keywords):
            categories.append(category)
    return categories

