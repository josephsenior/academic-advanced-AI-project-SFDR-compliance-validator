"""
ESG Compliance Reporting

Functions for generating compliance reports.
"""

import logging
from pathlib import Path
from textwrap import wrap
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .models import ESGComplianceOutput

logger = logging.getLogger(__name__)


def generate_enhanced_compliance_report(result: ESGComplianceOutput, output_path: str):
    """
    RAPPORT AMÉLIORÉ avec keywords + slides où ils apparaissent
    """
    lines = []
    
    lines.append("=" * 80)
    lines.append("[CHART] RAPPORT COMPLET DE CONFORMITÉ ESG/SFDR".center(80))
    lines.append("=" * 80)
    lines.append("")
    
    lines.append(f"[PIN] FONDS : {result.fund_name}")
    lines.append(f"[LIST] ARTICLE SFDR : Article {result.esg_level.sfdr_article}")
    lines.append(f"[TARGET] NIVEAU ESG : {result.esg_level.level.upper()}")
    lines.append(f" TYPE CLIENT : {result.client_type.capitalize()}")
    lines.append(f"[DOC] TYPE DOCUMENT : {result.document_type.capitalize()}")
    lines.append(f" DATE : {result.processed_at.strftime('%d/%m/%Y à %H:%M:%S')}")
    lines.append(f"[FOLDER] FICHIER : {Path(result.file_name).name}")
    lines.append("")
    
    lines.append("-" * 80)
    status = "[OK] CONFORME" if result.is_compliant else "[RED] NON CONFORME"
    lines.append(f"STATUT GLOBAL : {status}".center(80))
    lines.append("-" * 80)
    lines.append("")
    
    lines.append("[UP] 1. ANALYSE DU TEXTE")
    lines.append("─" * 80)
    lines.append(f"  Ratio ESG total : {result.esg_mentions.esg_percentage}%")
    lines.append(f"  Mentions ESG (commerciales) : {result.esg_mentions.commercial_esg_mentions}")
    lines.append(f"  Mentions réglementaires : {result.esg_mentions.mandatory_regulatory_mentions}")
    lines.append(f"  Longueur totale : {result.esg_mentions.total_text_length:,} caractères")
    lines.append("")
    
    if result.esg_level.level == "engaging":
        lines.append("  [OK] Article 9 (Engaging) : ESG promotion ATTENDUE")
    elif result.esg_level.level == "reduced":
        lines.append(f"  [WARNING] Article 8 (Reduced) : ESG % doit être < 10% (actuel: {result.esg_mentions.esg_percentage}%)")
        if result.esg_mentions.esg_percentage > 10:
            lines.append("     [RED] DÉPASSE LE SEUIL!")
    elif result.esg_level.level in ["limited", "none"]:
        lines.append(f"  [NO] Article {result.esg_level.sfdr_article} (Non-ESG) : 0 mention ESG autorisée")
        if result.esg_mentions.commercial_esg_mentions > 0:
            lines.append(f"     [RED] {result.esg_mentions.commercial_esg_mentions} mention(s) détectée(s)!")
    
    lines.append("")
    
    if result.esg_mentions.esg_keywords_found:
        lines.append("[SEARCH] 2. MOTS-CLÉS ESG DÉTECTÉS (avec localisation slides)")
        lines.append("─" * 80)
        
        keywords_sorted = sorted(result.esg_mentions.esg_keywords_found)
        
        for keyword in keywords_sorted:
            slides = result.esg_mentions.esg_keywords_by_slide.get(keyword, [])
            if slides:
                slides_str = ", ".join([f"Slide {s}" for s in slides])
                lines.append(f"  • {keyword:20} → {slides_str}")
            else:
                lines.append(f"  • {keyword:20} → (Non localisé)")
        
        lines.append("")
    
    if result.image_analysis_results:
        lines.append("[IMAGE] 3. ANALYSE DES SLIDES/IMAGES")
        lines.append("─" * 80)
        
        total_images = len(result.image_analysis_results)
        perfect_slides = []
        good_slides = []
        missing_slides = []
        offTopic_slides = []
        
        for img in result.image_analysis_results:
            desc = img.llm_visual_description.lower()
            
            if "parfait" in desc:
                perfect_slides.append((img.slide_number, img.slide_title, img.esg_keywords_in_image))
            elif "bon" in desc:
                good_slides.append((img.slide_number, img.slide_title, img.esg_keywords_in_image))
            elif "manquant" in desc:
                missing_slides.append((img.slide_number, img.slide_title))
            else:
                offTopic_slides.append((img.slide_number, img.slide_title))
        
        lines.append(f"\n  [CHART] Résumé:")
        lines.append(f"     • Total slides : {total_images}")
        lines.append(f"     [GREEN] Slides PARFAITES (ESG complet) : {len(perfect_slides)}")
        lines.append(f"     [YELLOW] Slides BONNES (ESG basique) : {len(good_slides)}")
        lines.append(f"     [ORANGE] Slides MANQUANTES (sans ESG) : {len(missing_slides)}")
        lines.append(f"     [WHITE] Slides HORS-SUJET : {len(offTopic_slides)}")
        
        if perfect_slides:
            lines.append(f"\n  [OK] SLIDES PARFAITES ({len(perfect_slides)}):")
            for slide_num, title, keywords in perfect_slides:
                lines.append(f"     • Slide {slide_num}: {title}")
                if keywords:
                    kw = ", ".join(keywords[:4])
                    lines.append(f"       Keywords: {kw}")
        
        if good_slides:
            lines.append(f"\n  [YELLOW] SLIDES BONNES ({len(good_slides)}):")
            for slide_num, title, keywords in good_slides:
                lines.append(f"     • Slide {slide_num}: {title}")
                if keywords:
                    kw = ", ".join(keywords[:3])
                    lines.append(f"       Keywords: {kw}")
        
        if missing_slides:
            lines.append(f"\n  [ORANGE] SLIDES MANQUANTES - À AMÉLIORER ({len(missing_slides)}):")
            for slide_num, title in missing_slides:
                lines.append(f"     • Slide {slide_num}: {title} [WARNING] Ajouter contenu ESG")
        
        if offTopic_slides and result.esg_level.level != "none":
            lines.append(f"\n  [WHITE] SLIDES HORS-SUJET ({len(offTopic_slides)}):")
            for slide_num, title in offTopic_slides:
                lines.append(f"     • Slide {slide_num}: {title}")
        
        lines.append("")
    
    if result.violations:
        lines.append("[WARNING] 4. VIOLATIONS DÉTECTÉES")
        lines.append("─" * 80)
        for i, violation in enumerate(result.violations, 1):
            severity_map = {
                "critical": "[RED] CRITIQUE",
                "high": "[FAIL] HAUTE",
                "medium": "[WARNING] MOYENNE",
                "low": "ℹ️ BASSE"
            }
            severity_label = severity_map.get(violation.severity, "•")
            
            lines.append(f"\n  {i}. {severity_label} - {violation.description}")
            if violation.location:
                lines.append(f"     Localisation: {violation.location}")
            lines.append(f"     -> Recommandation: {violation.recommendation.split(chr(10))[0]}")
        lines.append("")
    else:
        lines.append("[OK] 4. VIOLATIONS")
        lines.append("─" * 80)
        lines.append("   Aucune violation détectée")
        lines.append("")
    
    lines.append("[NOTE] 5. ACTIONS REQUISES")
    lines.append("─" * 80)
    
    if not result.is_compliant:
        action_count = 1
        for violation in result.violations:
            rec = violation.recommendation.split('\n')[0].strip()
            lines.append(f"  {action_count}️⃣ {rec}")
            action_count += 1
        
        if result.image_analysis_results:
            missing_count = sum(1 for img in result.image_analysis_results 
                              if "manquant" in img.llm_visual_description.lower())
            if missing_count > 0:
                lines.append(f"  {action_count}️⃣ Compléter {missing_count} slide(s) avec contenu ESG approprié")
    else:
        lines.append("  [OK] Document CONFORME - Aucune action requise")
    
    lines.append("")
    
    lines.append("=" * 80)
    lines.append(f"Confiance: {result.overall_confidence * 100:.0f}% | Revue humaine: {'OUI' if result.requires_human_review else 'NON'}")
    lines.append("=" * 80)
    
    report_text = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    logger.info(f"\n[OK] Rapport amélioré sauvegardé: {output_path}")
    return report_text


def save_report_as_pdf(text: str, pdf_path: str):
    """Enregistre le rapport texte dans un PDF simple, multi-pages si besoin."""
    Path(pdf_path).parent.mkdir(parents=True, exist_ok=True)
    
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    margin = 50
    y = height - margin
    line_height = 14
    max_chars_per_line = 95
    
    for line in text.splitlines():
        for chunk in wrap(line, max_chars_per_line):
            if y <= margin:
                c.showPage()
                y = height - margin
            c.drawString(margin, y, chunk)
            y -= line_height
    
    c.save()
    logger.info(f"[DOC] Rapport PDF sauvegardé: {pdf_path}")

