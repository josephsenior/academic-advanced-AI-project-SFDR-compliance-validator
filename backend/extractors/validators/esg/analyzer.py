"""
ESG Analyzer

Analyzes ESG content in documents using LLM and pattern matching.
"""

import logging
import os
import re
import json
import base64
import hashlib
import time
from typing import List, Dict, Optional, cast, Literal
import openai

from .models import ESGLevel, ESGMentions, ImageAnalysisResult
from .config import LLM_MODEL, LLM_MODEL_IMAGE
from .utils import normalize_esg_level

logger = logging.getLogger(__name__)


class ESGAnalyzer:
    """Analyzes ESG content in documents."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "")
        
        self.esg_keywords = {
            "ESG": ["ESG", "environnement", "social", "governance", "environmental", "sustainable", "durabilité"],
            "Durabilité": ["durable", "durabilité", "sustainability", "sustainable"],
            "Impact": ["impact", "impact investing", "investissement d'impact"],
            "Carbone": ["carbone", "carbon", "CO2", "émission"],
            "Climat": ["climat", "climate", "transition"],
            "Responsable": ["responsable", "responsible", "éthique", "ethics"],
            "Vert": ["vert", "green", "écologique"],
            "ISR": ["ISR", "SRI", "investissement socialement responsable"]
        }

        self.regulatory_patterns = [
            r"Article\s+[689]\s+",
            r"SFDR",
            r"durabilité\s+dans\s+le\s+secteur",
            r"règlement\s+européen",
            r"publication\s+d.informations",
            r"facteurs\s+de\s+durabilité",
            r"risques?\s+de\s+durabilité"
        ]
        self.compiled_patterns = [re.compile(p) for p in self.regulatory_patterns]
        
        # Pre-compile ESG keyword pattern for performance
        all_keywords = [kw.lower() for keywords in self.esg_keywords.values() for kw in keywords]
        self.esg_keyword_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(kw) for kw in all_keywords) + r')\b',
            re.IGNORECASE
        )
        
        # LLM result cache
        self._esg_level_cache = {}
        self._esg_mentions_cache = {}

    def analyze_image_with_advanced_vision(self, image_path: str, slide_title: str, slide_number: int) -> ImageAnalysisResult:
        """Analyse image avec vision LLM AVANCÉE (sans OCR Tesseract)."""
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            
            prompt = f"""Analyse cette image du slide "{slide_title}" (Slide {slide_number}).

[LIST] INSTRUCTIONS DÉTAILLÉES:

1. CONTENU VISUEL : Décris graphiques, logos, couleurs, mise en page
2. TEXTE VISIBLE : Extrait TOUS les textes (titres, légendes, données)
3. COHÉRENCE TITRE-IMAGE : L'image correspond-elle au titre ? (OUI/NON + explication)
4. ANALYSE ESG :
   - Identifie mentions ESG (environnement, social, gouvernance, durable, vert, responsable, impact)
   - Détecte symboles ESG (labels, certifications, graphiques de durabilité)
   - Évalue l'importance de l'ESG dans l'image (faible/moyen/élevé)
5. DISCLAIMERS : Signale tout avertissement, restriction légale ou condition
6. QUALITÉ COMMUNICATION : Greenwashing détecté ? (OUI/NON + explications)

CLASSIFICATION ESG DE L'IMAGE:
- "PARFAIT": Slide avec contenu ESG cohérent et complet
- "BON": Slide avec ESG présent mais basique
- "MANQUANT": Slide sans contenu ESG (pour fonds Article 8/9)
- "HORS SUJET": Slide non-ESG (acceptable pour Article 6)

Retourne JSON STRUCTURÉ:
{{
  "visual_description": "description détaillée du contenu visuel",
  "extracted_text": "texte exact extrait de l'image",
  "title_coherence": "OUI/NON - explication brève",
  "esg_elements": ["élément1", "élément2", ...],
  "esg_intensity": "faible/moyen/élevé",
  "esg_quality_rating": "PARFAIT/BON/MANQUANT/HORS_SUJET",
  "sustainability_indicators": ["indicator1", "indicator2"],
  "greenwashing_risk": "AUCUN/BAS/MOYEN/ÉLEVÉ",
  "disclaimers_detected": ["disclaimer1", "disclaimer2"],
  "recommendations": "recommandations d'amélioration"
}}"""
            
            response = client.chat.completions.create(
                model=LLM_MODEL_IMAGE,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0,
                max_tokens=1200,
                response_format={"type": "json_object"}
            )
            
            llm_result = json.loads(response.choices[0].message.content)
            
            visual_desc = llm_result.get("visual_description", "")
            extracted_text = llm_result.get("extracted_text", "")
            title_coherence = llm_result.get("title_coherence", "NON")
            esg_elements = llm_result.get("esg_elements", [])
            esg_intensity = llm_result.get("esg_intensity", "faible")
            esg_quality = llm_result.get("esg_quality_rating", "HORS_SUJET")
            sustainability = llm_result.get("sustainability_indicators", [])
            greenwashing = llm_result.get("greenwashing_risk", "AUCUN")
            disclaimers = llm_result.get("disclaimers_detected", [])
            
            combined_keywords = list(set(esg_elements + sustainability))
            
            compliance_issues = disclaimers.copy()
            if greenwashing in ["MOYEN", "ÉLEVÉ"]:
                compliance_issues.append(f"[WARNING] Risque de greenwashing: {greenwashing}")
            
            return ImageAnalysisResult(
                image_path=image_path,
                slide_number=slide_number,
                slide_title=slide_title,
                extracted_text_ocr=extracted_text,
                llm_visual_description=f"{visual_desc}\n\n[CHART] QUALITÉ ESG: {esg_quality}\n[STRONG] INTENSITÉ: {esg_intensity}",
                title_image_coherence=title_coherence,
                esg_keywords_in_image=combined_keywords,
                compliance_issues=compliance_issues
            )
            
        except Exception as e:
            logger.error(f"Erreur analyse vision: {e}")
            return ImageAnalysisResult(
                image_path=image_path,
                slide_number=slide_number,
                slide_title=slide_title,
                extracted_text_ocr=f"Erreur: {str(e)}",
                llm_visual_description=f"Erreur analyse: {str(e)}",
                title_image_coherence="ERREUR",
                esg_keywords_in_image=[],
                compliance_issues=[f"Erreur technique: {str(e)}"]
            )

    def detect_esg_level_v2(self, fund_name: str, text: str, sfdr_article: Optional[int] = None) -> ESGLevel:
        """Détermine le niveau ESG via LLM avec PROMPTS STRICTS."""
        # Check cache first
        cache_key = hashlib.md5(f"{fund_name}:{text[:1000]}:{sfdr_article}".encode()).hexdigest()
        if cache_key in self._esg_level_cache:
            logger.info("[LIST] Using cached ESG level detection")
            return self._esg_level_cache[cache_key]
        
        logger.info("[AI] Détection ESG level via LLM...")
        client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

        article_match = re.search(r"Article\s+([689])\s", text)
        detected_article = int(article_match.group(1)) if article_match else sfdr_article

        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[{
                        "role": "system",
                        "content": """You are an ESG/SFDR compliance expert.

CRITICAL: You MUST return a strict JSON with these exact fields:
- level: MUST be one of ["engaging", "reduced", "limited", "none"] (lowercase, nothing else)
- sfdr_article: integer 6, 8, or 9 (or null)
- exclusion_percentage: number or null
- portfolio_coverage: number or null
- description: brief string

NEVER put "Article 8" or "Article 9" inside the "level" field.
"level" is independent from sfdr_article.
Example:
{
  "level": "reduced",
  "sfdr_article": 8,
  "exclusion_percentage": null,
  "portfolio_coverage": null,
  "description": "Fund applies ESG factors in a limited way"
}"""
                    }, {
                        "role": "user",
                        "content": f"Fund: {fund_name}\nDetected Article SFDR: {detected_article or 'Unknown'}\n\nText excerpt:\n{text[:2000]}"
                    }],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                break
            except openai.RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"[WARNING] Rate limit hit, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            except openai.APIError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"[WARNING] API error, retrying... ({e})")
                    time.sleep(1)
                else:
                    raise

        # Structured output validation with fallback
        try:
            data = json.loads(response.choices[0].message.content)
            logger.info(f"Raw LLM response: {data}")
            
            data = normalize_esg_level(data)
            logger.info(f"Normalized data: {data}")
            
            esg_level = ESGLevel(**data)
            logger.info(f"[OK] ESG Level: {esg_level.level.upper()} (Article {esg_level.sfdr_article})")
            
            # Cache successful result
            self._esg_level_cache[cache_key] = esg_level
            return esg_level
        except Exception as e:
            logger.error(f"[FAIL] Erreur parsing ESG Level: {e}")
            logger.error(f"Data reçu: {data if 'data' in locals() else 'N/A'}")
            
            # Fallback: Try to fix JSON with LLM
            try:
                logger.info("[FIX] Attempting to fix invalid JSON...")
                fix_response = client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[{
                        "role": "system",
                        "content": f"Fix this invalid JSON to match ESGLevel schema: {ESGLevel.schema_json()}"
                    }, {
                        "role": "user",
                        "content": f"Invalid JSON: {data if 'data' in locals() else response.choices[0].message.content}"
                    }],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                fixed_data = json.loads(fix_response.choices[0].message.content)
                fixed_data = normalize_esg_level(fixed_data)
                esg_level = ESGLevel(**fixed_data)
                logger.info(f"[OK] Fixed ESG Level: {esg_level.level.upper()}")
                self._esg_level_cache[cache_key] = esg_level
                return esg_level
            except:
                # Ultimate fallback
                logger.error("[FAIL] Could not fix JSON, using safe default")
                default_sfdr = cast(Literal[6,8,9], sfdr_article if sfdr_article in [6, 8, 9] else 6)
                default_level = ESGLevel(
                    level="none",
                    sfdr_article=default_sfdr,
                    exclusion_percentage=None,
                    portfolio_coverage=None,
                    description="ESG level could not be determined - defaulting to Article 6"
                )
                self._esg_level_cache[cache_key] = default_level
                return default_level

    def analyze_esg_mentions_v2(self, text: str, document_type: str = "marketing", slides_data: List[dict] = None) -> ESGMentions:
        """Analyse ESG mentions + track chaque keyword par slide."""
        # Check cache first
        cache_key = hashlib.md5(f"{text[:1000]}:{document_type}".encode()).hexdigest()
        if cache_key in self._esg_mentions_cache:
            logger.info("[LIST] Using cached ESG mentions analysis")
            return self._esg_mentions_cache[cache_key]
        
        logger.info("[CHART] Analyse ESG mentions avec localisation par slide...")
        
        total_length = len(text)
        sentences = re.split(r'[.!?]', text)

        esg_keywords_found = set()
        esg_keywords_by_slide: Dict[str, List[int]] = {}
        esg_sentences = []
        esg_text_length = 0
        mandatory_regulatory = 0
        commercial_esg = 0

        slides_dict = {}
        if slides_data:
            for slide in slides_data:
                slides_dict[slide["slide_number"]] = slide["text"].lower()

        # Use pre-compiled regex for faster matching
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Fast keyword detection with pre-compiled pattern
            found_keywords = self.esg_keyword_pattern.findall(sentence_lower)
            
            if found_keywords:
                esg_keywords_found.update(found_keywords)
                
                is_regulatory = any(pattern.search(sentence_lower) for pattern in self.compiled_patterns)
                if is_regulatory:
                    mandatory_regulatory += 1
                else:
                    commercial_esg += 1
                    esg_sentences.append(sentence.strip())
                esg_text_length += len(sentence)

        # Optimize slide mapping
        for keyword in esg_keywords_found:
            slide_numbers = []
            if slides_dict:
                keyword_lower = keyword.lower()
                slide_numbers = [num for num, text in slides_dict.items() if keyword_lower in text]
            esg_keywords_by_slide[keyword] = sorted(slide_numbers) if slide_numbers else []

        esg_percentage = (esg_text_length / total_length * 100) if total_length > 0 else 0

        mentions = ESGMentions(
            total_text_length=total_length,
            esg_text_length=esg_text_length,
            esg_percentage=round(esg_percentage, 2),
            esg_keywords_found=list(esg_keywords_found),
            esg_keywords_by_slide=esg_keywords_by_slide,
            esg_sentences=esg_sentences[:10],
            mandatory_regulatory_mentions=mandatory_regulatory,
            commercial_esg_mentions=commercial_esg
        )
        
        # Cache result
        self._esg_mentions_cache[cache_key] = mentions
        
        logger.info(f"[OK] Mentions: {mentions.esg_percentage}% ({commercial_esg} commerciales)")
        return mentions

