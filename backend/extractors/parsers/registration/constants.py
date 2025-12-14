"""
Registration Parser Constants

Country patterns and keyword definitions for registration validation.
"""

# Enhanced country patterns with word boundaries to avoid false positives
COUNTRY_PATTERNS = {
    # Europe
    "germany": r'\b(?:germany|german|deutschland)\b',
    "austria": r'\b(?:austria|austrian|österreich)\b',
    "belgium": r'\b(?:belgium|belgian|belgique|belgië)\b',
    "spain": r'\b(?:spain|spanish|españa|espagne)\b',
    "france": r'\b(?:france|french|français|française)\b',
    "italy": r'\b(?:italy|italian|italia|italien)\b',
    "luxembourg": r'\b(?:luxembourg|luxembourgish)\b',
    "netherlands": r'\b(?:netherlands|dutch|holland|pays-bas)\b',
    "portugal": r'\b(?:portugal|portuguese)\b',
    "united kingdom": r'\b(?:united kingdom|uk|u\.k\.|britain|british|grande-bretagne)\b',
    "switzerland": r'\b(?:switzerland|swiss|suisse|schweiz)\b',
    "sweden": r'\b(?:sweden|swedish|sverige)\b',
    "finland": r'\b(?:finland|finnish|suomi)\b',
    "denmark": r'\b(?:denmark|danish|danmark)\b',
    "norway": r'\b(?:norway|norwegian|norge)\b',
    "ireland": r'\b(?:ireland|irish|irlande)\b',
    "iceland": r'\b(?:iceland|icelandic|ísland)\b',
    "greece": r'\b(?:greece|greek|grèce)\b',
    "poland": r'\b(?:poland|polish|polska|pologne)\b',
    "czech republic": r'\b(?:czech republic|czech|czechia)\b',
    "hungary": r'\b(?:hungary|hungarian|hongrie)\b',
    "romania": r'\b(?:romania|romanian|roumanie)\b',
    "bulgaria": r'\b(?:bulgaria|bulgarian)\b',
    "croatia": r'\b(?:croatia|croatian)\b',
    "slovakia": r'\b(?:slovakia|slovak|slovaquie)\b',
    "slovenia": r'\b(?:slovenia|slovenian|slovénie)\b',
    "estonia": r'\b(?:estonia|estonian)\b',
    "latvia": r'\b(?:latvia|latvian)\b',
    "lithuania": r'\b(?:lithuania|lithuanian)\b',
    "malta": r'\b(?:malta|maltese|malte)\b',
    "cyprus": r'\b(?:cyprus|cypriot|chypre)\b',
    
    # Americas
    "chile": r'\b(?:chile|chilean|chili)\b',
    "peru": r'\b(?:peru|peruvian|pérou)\b',
    "united states": r'\b(?:united states|usa|u\.s\.a\.|us|u\.s\.|america|american|états-unis)\b',
    "canada": r'\b(?:canada|canadian)\b',
    "mexico": r'\b(?:mexico|mexican|mexique)\b',
    "brazil": r'\b(?:brazil|brazilian|brésil)\b',
    "argentina": r'\b(?:argentina|argentinian|argentine)\b',
    "colombia": r'\b(?:colombia|colombian|colombie)\b',
    
    # Asia-Pacific
    "singapore": r'\b(?:singapore|singaporean|singapour)\b',
    "japan": r'\b(?:japan|japanese|japon)\b',
    "china": r'\b(?:china|chinese|chine)\b',
    "hong kong": r'\b(?:hong kong|hongkong)\b',
    "south korea": r'\b(?:south korea|korea|korean|corée)\b',
    "taiwan": r'\b(?:taiwan|taiwanese)\b',
    "australia": r'\b(?:australia|australian|australie)\b',
    "new zealand": r'\b(?:new zealand|nz)\b',
    "india": r'\b(?:india|indian|inde)\b',
    "thailand": r'\b(?:thailand|thai|thaïlande)\b',
    "malaysia": r'\b(?:malaysia|malaysian|malaisie)\b',
    "indonesia": r'\b(?:indonesia|indonesian|indonésie)\b',
    "philippines": r'\b(?:philippines|philippine|filipino)\b',
    "vietnam": r'\b(?:vietnam|vietnamese)\b',
    
    # Middle East
    "united arab emirates": r'\b(?:united arab emirates|uae|u\.a\.e\.|emirates|émirats)\b',
    "saudi arabia": r'\b(?:saudi arabia|saudi|arabie saoudite)\b',
    "qatar": r'\b(?:qatar|qatari)\b',
    "bahrain": r'\b(?:bahrain|bahraini|bahreïn)\b',
    "kuwait": r'\b(?:kuwait|kuwaiti|koweït)\b',
    "israel": r'\b(?:israel|israeli|israël)\b',
    
    # Africa
    "south africa": r'\b(?:south africa|south african|afrique du sud)\b',
    "egypt": r'\b(?:egypt|egyptian|égypte)\b',
    "morocco": r'\b(?:morocco|moroccan|maroc)\b',
    "nigeria": r'\b(?:nigeria|nigerian|nigéria)\b',
}

# Keywords indicating distribution/availability context (should trigger validation)
DISTRIBUTION_KEYWORDS = {
    'available', 'distributed', 'marketed', 'sold', 'commercialized',
    'registered', 'authorized', 'approved', 'permitted', 'offered',
    'disponible', 'distribué', 'commercialisé', 'vendu', 'enregistré',
    'autorisé', 'approuvé', 'distribution', 'commercialisation',
    'verkauft', 'verfügbar', 'zugelassen', 'genehmigt', 'marketing',
    'for sale', 'for distribution', 'can be purchased'
}

# Keywords indicating general reference (should NOT trigger validation)
GENERAL_REFERENCE_KEYWORDS = {
    'investor', 'market', 'economy', 'regulation', 'law', 'based in',
    'domiciled', 'headquartered', 'located', 'resident', 'citizenship',
    'investisseur', 'marché', 'économie', 'réglementation', 'loi',
    'basé', 'domicilié', 'situé', 'résident'
}

