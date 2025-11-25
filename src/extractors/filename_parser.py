"""
Filename Parser
Extracts metadata from ODDO BHF document filenames

Example filenames:
- 47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx
- FINAL 47861-6PG-GB-ODDO BHF Algo Trend US-20250831.pptx
- XXX-PRS-GB-ODDO BHF US Equity Active ETF-20250630_6PN.pptx
"""

import re
from datetime import datetime
from typing import Dict, Optional, Tuple
from pathlib import Path


class FilenameParser:
    """Parse ODDO BHF document filenames to extract metadata"""
    
    # Language codes
    LANGUAGE_CODES = {
        'FR': 'FR',
        'GB': 'EN',
        'DE': 'DE',
        'EN': 'EN'
    }
    
    # Version patterns
    VERSION_PATTERNS = [
        r'v\d+',           # v3, v1, v10
        r'V\d+',           # V3, V1
        r'FINAL',          # FINAL
        r'final',          # final
        r'CLEAN',          # CLEAN
        r'clean',          # clean
        r'pn',             # pn (pre-notice)
        r'def',            # def (definitive)
    ]
    
    # Document type patterns
    DOC_TYPE_PATTERNS = {
        '6PG': '6-page',
        'PRS': 'presentation',
        'XXX': 'draft'
    }
    
    def __init__(self):
        # Houni n'compilei regex patterns li n'est3mlo fil parsing
        self.date_pattern = re.compile(r'(\d{8})')  # YYYYMMDD
        self.version_pattern = re.compile(r'\b(' + '|'.join(self.VERSION_PATTERNS) + r')\b', re.IGNORECASE)
        self.id_pattern = re.compile(r'^(\d{5})')  # 5-digit ID at start
        self.language_pattern = re.compile(r'\b(FR|GB|DE|EN)\b')
    
    def parse(self, filename: str) -> Dict:
        """
        Parse filename and extract metadata
        
        Returns:
            Dict with extracted information:
            - document_id: str
            - document_type: str
            - language_code: str
            - fund_name: str
            - date_extracted: date
            - version_number: str
            - version_type: str
            - status_extracted: str
            - parsing_confidence: float
        """
        # Houni nparsi filename: nensa extension, nforce patterns, n7awel n'extracti fields
        # Remove file extension
        base_name = Path(filename).stem
        
        result = {
            'document_id_extracted': None,
            'document_type': None,
            'language_code': None,
            'fund_name': None,
            'date_extracted': None,
            'version_number': None,
            'version_type': None,
            'status_extracted': None,
            'parsing_confidence': 0.0
        }
        
        # Confidence score incremental based on matches
        confidence_score = 0.0
        
        # Nextracti document ID (5 digits fl iwal) w nzid score
        id_match = self.id_pattern.match(base_name)
        if id_match:
            result['document_id_extracted'] = id_match.group(1)
            confidence_score += 0.2
        
        # Nextracti date (YYYYMMDD) w nconverti l date object
        date_match = self.date_pattern.search(base_name)
        if date_match:
            date_str = date_match.group(1)
            try:
                result['date_extracted'] = datetime.strptime(date_str, '%Y%m%d').date()
                confidence_score += 0.2
            except ValueError:
                pass
        
        # Nextracti language code (FR/GB/DE/EN) w nmapih lil codes internationaux
        lang_match = self.language_pattern.search(base_name)
        if lang_match:
            lang_code = lang_match.group(1)
            result['language_code'] = self.LANGUAGE_CODES.get(lang_code, lang_code)
            confidence_score += 0.2
        
        # Ndetecti document type (6PG, PRS, XXX) 3la asas patterns
        for pattern, doc_type in self.DOC_TYPE_PATTERNS.items():
            if pattern in base_name:
                result['document_type'] = doc_type
                confidence_score += 0.15
                break
        
        # Nextracti version info (v1, FINAL, CLEAN, pn, def)
        version_match = self.version_pattern.search(base_name)
        if version_match:
            version_str = version_match.group(1).upper()
            result['version_number'] = version_str
            
            # Determine version type
            if version_str in ['FINAL', 'final']:
                result['version_type'] = 'final'
            elif version_str in ['CLEAN', 'clean']:
                result['version_type'] = 'clean'
            elif version_str in ['pn']:
                result['version_type'] = 'draft'
                result['status_extracted'] = 'pre-notice'
            elif version_str.startswith('V') or version_str.startswith('v'):
                result['version_type'] = 'draft'
                result['version_number'] = version_str
            else:
                result['version_type'] = 'draft'
            
            confidence_score += 0.15
        
        # nextracti fund name 7asb language w date (pattern based)
        # Pattern: ...-LANG-FUND NAME-DATE...
        parts = base_name.split('-')
        if len(parts) >= 4:
            # Look for language code position
            lang_pos = None
            for i, part in enumerate(parts):
                if part in ['FR', 'GB', 'DE', 'EN']:
                    lang_pos = i
                    break
            
            if lang_pos and lang_pos + 1 < len(parts):
                # Fund name is between language and date
                fund_parts = []
                for i in range(lang_pos + 1, len(parts)):
                    part = parts[i]
                    # Stop if we hit a date
                    if self.date_pattern.match(part):
                        break
                    fund_parts.append(part)
                
                if fund_parts:
                    result['fund_name'] = ' '.join(fund_parts).strip()
                    confidence_score += 0.1

        # Ken ma tlawech fund name, nhebb nsearchi pattern "ODDO BHF..."
        if not result['fund_name']:
            # Look for "ODDO BHF" pattern
            oddo_match = re.search(r'ODDO\s+BHF[^-]+', base_name)
            if oddo_match:
                result['fund_name'] = oddo_match.group(0).strip()
                confidence_score += 0.05
        
        # Na3tiw final parsing confidence (cap 1.0)
        result['parsing_confidence'] = min(confidence_score, 1.0)
        
        return result
    
    def extract_fund_identifier(self, filename: str) -> Optional[str]:
        # Yraja3 fund name sinon None
        """Extract fund identifier (ISIN or fund name) from filename"""
        parsed = self.parse(filename)
        return parsed.get('fund_name')


def parse_filename(filename: str) -> Dict:
    # Convenience function: ycreati FilenameParser w yparsi filename
    """Convenience function to parse a filename"""
    parser = FilenameParser()
    return parser.parse(filename)


if __name__ == "__main__":
    # Test with example filenames
    test_files = [
        "47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx",
        "FINAL 47861-6PG-GB-ODDO BHF Algo Trend US-20250831.pptx",
        "XXX-PRS-GB-ODDO BHF US Equity Active ETF-20250630_6PN.pptx",
        "FINAL-PRS-GB-ODDO BHF US Equity Active ETF-20250630_8PN_clean.pptx",
        "1 - V1-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx",
        "3 - FINAL CLEAN-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx"
    ]
    
    parser = FilenameParser()
    
    print("="*80)
    print("Filename Parser Test")
    print("="*80)
    
    for filename in test_files:
        print(f"\n📄 Filename: {filename}")
        result = parser.parse(filename)
        print(f"   ID: {result['document_id_extracted']}")
        print(f"   Type: {result['document_type']}")
        print(f"   Language: {result['language_code']}")
        print(f"   Fund: {result['fund_name']}")
        print(f"   Date: {result['date_extracted']}")
        print(f"   Version: {result['version_number']} ({result['version_type']})")
        print(f"   Status: {result['status_extracted']}")
        print(f"   Confidence: {result['parsing_confidence']:.2f}")

