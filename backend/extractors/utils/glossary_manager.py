"""
Glossary Manager - Load and manage disclaimers from glossary_disclaimers.json

This is the SINGLE SOURCE OF TRUTH for all disclaimer text and requirements.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class GlossaryManager:
    """Manages disclaimer glossary from glossary_disclaimers.json."""
    
    def __init__(self, glossary_path: str = "dataset/glossary_disclaimers.json"):
        """Initialize glossary manager.
        
        Args:
            glossary_path: Path to glossary JSON file (relative or absolute)
        """
        self.glossary_path = Path(glossary_path)
        self.glossary: Dict[str, Any] = {}
        self._load_glossary()
    
    def _load_glossary(self) -> None:
        """Load disclaimer glossary from JSON file."""
        if not self.glossary_path.exists():
            # Try relative to project root
            alt_path = Path("dataset") / "glossary_disclaimers.json"
            if alt_path.exists():
                self.glossary_path = alt_path
            else:
                print(f"Warning: Glossary file not found at {self.glossary_path} or {alt_path}")
                return
        
        try:
            with open(self.glossary_path, 'r', encoding='utf-8') as f:
                self.glossary = json.load(f)
            print(f"✅ Loaded glossary with {len(self.glossary)} language sections")
        except Exception as e:
            print(f"❌ Error loading glossary: {e}")
    
    def get_required_disclaimers(
        self,
        language: str = "ENGLISH",
        client_type: str = "non_professional",
        management_company: Optional[str] = None
    ) -> Dict[str, str]:
        """Get all required disclaimers for a document type and client.
        
        Args:
            language: Language code (ENGLISH, FRENCH, GERMAN)
            client_type: 'professional' or 'non_professional'
            management_company: Management company (SAS, GmbH, Lux) for variant selection
        
        Returns:
            Dictionary of {disclaimer_type: disclaimer_text}
        """
        disclaimers = {}
        
        if not self.glossary:
            return disclaimers
        
        # Normalize inputs
        lang = language.upper()
        client = "professional" if "professional" in client_type.lower() else "non_professional"
        
        # Get language section
        lang_section = self.glossary.get(lang, {})
        
        # Handle list structure (from Excel/JSON export)
        if isinstance(lang_section, list):
            # Map column names based on language
            content_col = f"{lang} LANGUAGE"
            prof_col = "Unnamed: 2" # Based on the JSON snippet provided
            
            for item in lang_section:
                if not isinstance(item, dict):
                    continue
                
                doc_type = item.get("Document type ", "").strip()
                if not doc_type:
                    continue
                
                # Professional text
                text = ""
                if client == "professional":
                    # Try Unnamed: 2 first, then language column
                    text = item.get(prof_col, "") or item.get(content_col, "")
                else:
                    # Non-professional: only language column
                    text = item.get(content_col, "")
                
                # Clean up "Not allowed" or empty
                if text and isinstance(text, str) and text.strip().lower() != "not allowed":
                    disclaimers[doc_type] = text.strip()
            
            return disclaimers

        # Handle dictionary structure (original/legacy)
        if isinstance(lang_section, dict):
            for doc_type, text_or_variants in lang_section.items():
                # Handle different glossary structures
                if isinstance(text_or_variants, str):
                    # Simple text
                    disclaimers[doc_type] = text_or_variants
                elif isinstance(text_or_variants, dict):
                    # May have professional/non_professional variants
                    if client in text_or_variants:
                        disclaimers[doc_type] = text_or_variants[client]
                    elif 'text' in text_or_variants:
                        disclaimers[doc_type] = text_or_variants['text']
                elif isinstance(text_or_variants, list) and len(text_or_variants) > 0:
                    # Sometimes stored as list
                    if isinstance(text_or_variants[0], str):
                        disclaimers[doc_type] = text_or_variants[0]
                    elif isinstance(text_or_variants[0], dict):
                        # First item might be professional, second non_professional
                        idx = 0 if client == "professional" else (1 if len(text_or_variants) > 1 else 0)
                        disclaimers[doc_type] = text_or_variants[idx].get('text', '')
        
        return disclaimers

    def get_disclaimer_text(
        self,
        disclaimer_type: str,
        language: str = "ENGLISH",
        client_type: str = "non_professional"
    ) -> Optional[str]:
        """Get specific disclaimer text."""
        disclaimers = self.get_required_disclaimers(language, client_type)
        return disclaimers.get(disclaimer_type)
    
    def get_all_disclaimer_types(self, language: str = "ENGLISH") -> List[str]:
        """Get all available disclaimer types for a language.
        
        Args:
            language: Language code
        
        Returns:
            List of disclaimer type names
        """
        lang = language.upper()
        lang_section = self.glossary.get(lang, {})
        
        if isinstance(lang_section, list):
            types = []
            for item in lang_section:
                if isinstance(item, dict):
                    doc_type = item.get("Document type ", "").strip()
                    if doc_type:
                        types.append(doc_type)
            return types
        elif isinstance(lang_section, dict):
            return list(lang_section.keys())
        
        return []
    
    def verify_disclaimer_presence(
        self,
        document_text: str,
        disclaimer_type: str,
        language: str = "ENGLISH",
        client_type: str = "non_professional",
        min_similarity: float = 0.8
    ) -> tuple[bool, float]:
        """Verify if a disclaimer exists in document text.
        
        Args:
            document_text: Full document text to search
            disclaimer_type: Type of disclaimer to find
            language: Language code
            client_type: Client type
            min_similarity: Minimum similarity threshold (0-1)
        
        Returns:
            Tuple of (found: bool, similarity_score: float)
        """
        disclaimer_text = self.get_disclaimer_text(disclaimer_type, language, client_type)
        if not disclaimer_text:
            return False, 0.0
        
        # Simple substring matching (can be enhanced with fuzzy matching)
        doc_lower = document_text.lower()
        disc_lower = disclaimer_text.lower()
        
        # Check for exact match
        if disc_lower in doc_lower:
            return True, 1.0
        
        # Check for partial matches (first 50 chars)
        if len(disc_lower) > 50:
            partial = disc_lower[:50]
            if partial in doc_lower:
                return True, 0.9
        
        # Check for key phrases
        key_phrases = disc_lower.split('.')[:2]  # First 1-2 sentences
        found_phrases = 0
        for phrase in key_phrases:
            if phrase.strip() and phrase.strip() in doc_lower:
                found_phrases += 1
        
        similarity = found_phrases / len(key_phrases) if key_phrases else 0
        return similarity >= min_similarity, similarity
    
    def get_glossary_structure(self) -> Dict[str, List[str]]:
        """Get structure of glossary (languages and types).
        
        Returns:
            Dictionary of {language: [disclaimer_types]}
        """
        structure = {}
        for lang, section in self.glossary.items():
            if isinstance(section, dict):
                structure[lang] = list(section.keys())
            elif isinstance(section, list):
                types = []
                for item in section:
                    if isinstance(item, dict):
                        doc_type = item.get("Document type ", "").strip()
                        if doc_type:
                            types.append(doc_type)
                structure[lang] = types
            else:
                structure[lang] = []
        return structure
