"""
ESG Compliance Validator

Validates ESG compliance based on analysis results.
"""

import logging
from pathlib import Path
from typing import Optional, Literal
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import ESGComplianceOutput, ESGViolation
from .analyzer import ESGAnalyzer
from .loaders import DocumentLoader
from .utils import extract_fund_metadata_from_prospectus

logger = logging.getLogger(__name__)


class ESGComplianceAgent:
    """Main ESG compliance validation agent."""
    
    def __init__(self, api_key: str, base_url: str, enable_rag: bool = False, max_workers: int = 3):
        self.analyzer = ESGAnalyzer(api_key, base_url)
        self.rag_enabled = False
        self.rag = None
        self.max_workers = max_workers

    def check_compliance(self,
                        file_path: str,
                        metadata_file: Optional[str] = None,
                        prospectus_path: Optional[str] = None,
                        document_type: str = "marketing",
                        document_id: str = "ESG-001",
                        analyze_images: bool = False) -> ESGComplianceOutput:

        logger.info("\n" + "="*70)
        logger.info(f"[SEARCH] ANALYSE: {Path(file_path).name}")
        logger.info("="*70)

        loader = DocumentLoader(file_path)
        raw_doc = loader.load()
        full_text = raw_doc.get("full_text", "")
        slides_data = raw_doc.get("slides_data", [])

        fund_name = "Unknown Fund"
        sfdr_article_from_prospectus = None

        if prospectus_path and Path(prospectus_path).exists():
            fund_meta = extract_fund_metadata_from_prospectus(prospectus_path)
            fund_name = fund_meta.get("fund_name", "Unknown Fund")
            sfdr_article_from_prospectus = fund_meta.get("sfdr_article")

        client_type: Literal["retail", "professional"] = "retail"
        image_results = []

        # Fix vision analysis + smart sampling
        if analyze_images and "images" in raw_doc and raw_doc["images"]:
            logger.info(f"[IMAGE] Analyzing {len(raw_doc['images'])} image(s) with vision LLM...")
            
            # Smart sampling: Only analyze slides with ESG keywords
            slides_dict = {slide['slide_number']: slide['text'].lower() for slide in slides_data}
            slides_to_analyze = []
            
            for img_info in raw_doc["images"]:
                slide_num = img_info.get("slide_number", 0)
                slide_text = slides_dict.get(slide_num, "")
                
                # Only analyze if slide contains ESG keywords
                if any(keyword.lower() in slide_text for category in self.analyzer.esg_keywords.values() for keyword in category):
                    slides_to_analyze.append(img_info)
            
            # Cap at 5 slides to control costs
            slides_to_analyze = slides_to_analyze[:5]
            
            if slides_to_analyze:
                logger.info(f"[TARGET] Smart sampling: {len(slides_to_analyze)}/{len(raw_doc['images'])} slides selected for vision analysis")
                
                # Parallel vision analysis
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {}
                    for img_info in slides_to_analyze:
                        # Note: Vision requires actual image files, skip if path not available
                        if img_info.get("path"):
                            future = executor.submit(
                                self.analyzer.analyze_image_with_advanced_vision,
                                img_info["path"],
                                img_info.get("slide_title", f"Slide {img_info.get('slide_number')}"),
                                img_info.get("slide_number", 0)
                            )
                            futures[future] = img_info
                    
                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            image_results.append(result)
                        except Exception as e:
                            img_info = futures[future]
                            logger.error(f"[FAIL] Vision analysis failed for slide {img_info.get('slide_number')}: {e}")
            else:
                logger.info("[LIST] No slides with ESG keywords found, skipping vision analysis")

        # Parallel LLM calls for 2x speedup
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_level = executor.submit(
                self.analyzer.detect_esg_level_v2,
                fund_name, full_text, sfdr_article_from_prospectus
            )
            future_mentions = executor.submit(
                self.analyzer.analyze_esg_mentions_v2,
                full_text, document_type, slides_data
            )
            
            esg_level = future_level.result()
            esg_mentions = future_mentions.result()

        violations = []
        is_compliant = True

        logger.info("\n[WARNING] DÉTECTION VIOLATIONS...")

        if esg_level.level == "engaging":
            if (esg_level.exclusion_percentage or 0) < 20 or (esg_level.portfolio_coverage or 0) < 90:
                violations.append(ESGViolation(
                    violation_type="engaging_criteria_not_met",
                    severity="high",
                    description="Fonds 'engaging' mais critères non respectés.",
                    recommendation="Vérifier la classification du fonds et les critères ESG."
                ))
                is_compliant = False
                logger.warning(" [RED] HAUTE: Critères Article 9 non respectés")

        elif esg_level.level == "reduced":
            if esg_mentions.esg_percentage > 10:
                violations.append(ESGViolation(
                    violation_type="esg_overmentioned_article8",
                    severity="critical",
                    description=f"Article 8: {esg_mentions.esg_percentage}% mentions ESG (max 10%)",
                    recommendation="Réduire mentions ESG à < 10%"
                ))
                is_compliant = False
                logger.warning(f" [RED] CRITIQUE: Ratio ESG trop élevé ({esg_mentions.esg_percentage}%)")

        elif esg_level.level in ["limited", "none"]:
            if esg_mentions.commercial_esg_mentions > 2:
                violations.append(ESGViolation(
                    violation_type="esg_forbidden_article6",
                    severity="critical",
                    description=f"Article 6 (non-ESG): {esg_mentions.commercial_esg_mentions} mentions ESG détectées",
                    recommendation="Supprimer toutes mentions ESG commerciales"
                ))
                is_compliant = False
                logger.warning(" [RED] CRITIQUE: Mentions ESG dans Article 6")

        for img_result in image_results:
            if img_result.esg_keywords_in_image and esg_level.level == "none":
                violations.append(ESGViolation(
                    violation_type="esg_in_image_article6",
                    severity="high",
                    description=f"Slide {img_result.slide_number}: contient ESG {img_result.esg_keywords_in_image}",
                    location=f"Slide {img_result.slide_number}: {img_result.slide_title}",
                    recommendation="Retirer éléments ESG visuels"
                ))
                is_compliant = False
                logger.warning(f" [FAIL] HAUTE: Image Slide {img_result.slide_number}")

        if is_compliant:
            logger.info(" [OK] Aucune violation")

        output = ESGComplianceOutput(
            document_id=document_id,
            file_name=str(file_path),
            fund_name=fund_name,
            client_type=client_type,
            document_type=document_type,
            esg_level=esg_level,
            esg_mentions=esg_mentions,
            is_compliant=is_compliant,
            violations=violations,
            overall_confidence=0.95,
            requires_human_review=len(violations) > 0,
            image_analysis_results=image_results
        )

        return output

