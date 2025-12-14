"""
Document Family Detection
Groups related documents (versions, languages, presentation + prospectus)
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict

import uuid


class DocumentFamilyDetector:
    """Detect and manage document families"""
    
    def __init__(self):
        # Houni ninitializi DocumentFamilyDetector: n7ot rules li nest3mlhom fil detection
        self.family_rules = {
            'same_document_id': self._same_document_id,
            'same_fund_and_date': self._same_fund_and_date,
            'same_folder': self._same_folder,
            'related_by_name': self._related_by_name
        }
        self.families: Dict[str, Dict[str, Any]] = {}
    
    def detect_family(self, document_metadata: Dict[str, Any], existing_families: List[Dict] = None) -> Optional[str]:
        """
        Detect which family a document belongs to
        
        Args:
            document_metadata: Metadata dict with filename, fund_name, date, etc.
            existing_families: List of existing families from the in-memory cache
            
        Returns:
            Family ID (UUID string) if match found, None if new family
        """
        if existing_families is None:
            existing_families = list(self.families.values())
        
        # Try each detection rule
        for rule_name, rule_func in self.family_rules.items():
            family_id = rule_func(document_metadata, existing_families)
            if family_id:
                return family_id
        
        # No match found - will create new family
        return None
    
    def _same_document_id(self, metadata: Dict, families: List[Dict]) -> Optional[str]:
        # Nmatchi 3la document ID: ken fama doc_id fi metadata nsearchiw fi families
        """Match by document ID"""
        doc_id = metadata.get('document_id_extracted')
        if not doc_id:
            return None
        
        for family in families:
            # Check if any document in family has same ID
            if self._family_has_document_id(family, doc_id):
                return str(family['id'])
        
        return None
    
    def _same_fund_and_date(self, metadata: Dict, families: List[Dict]) -> Optional[str]:
        # Nmatchi 3la fund name w date (normalize names qbal comparison)
        """Match by fund name and date"""
        fund_name = metadata.get('fund_name')
        date = metadata.get('date_extracted')
        
        if not fund_name or not date:
            return None
        
        # Normalize fund name for comparison
        fund_normalized = self._normalize_fund_name(fund_name)
        date_str = str(date) if date else None
        
        for family in families:
            if family.get('fund_identifier'):
                family_fund_normalized = self._normalize_fund_name(family['fund_identifier'])
                if fund_normalized == family_fund_normalized:
                    # Check if date matches (or close)
                    if date_str and self._dates_match(date_str, family.get('date', '')):
                        return str(family['id'])
        
        return None
    
    def _same_folder(self, metadata: Dict, families: List[Dict]) -> Optional[str]:
        # Nchecki ken documents jaou men nafss folder
        """Match by same folder/directory"""
        file_directory = metadata.get('file_directory')
        if not file_directory:
            file_path = metadata.get('file_path')
            if file_path:
                file_directory = Path(file_path).parent
        if not file_directory:
            return None
        
        # Extract folder name (e.g., "example_1", "example_2")
        folder_name = file_directory.name if isinstance(file_directory, Path) else Path(file_directory).name
        
        # Check if any document in existing families is from same folder
        for family in families:
            if self._family_has_folder(family, folder_name):
                return str(family['id'])
        
        return None
    
    def _related_by_name(self, metadata: Dict, families: List[Dict]) -> Optional[str]:
        # Nmatchi fund names b logique simple (fuzzy) bach nal9aw relatives
        """Match by similar fund names (fuzzy matching)"""
        fund_name = metadata.get('fund_name')
        if not fund_name:
            return None
        
        fund_normalized = self._normalize_fund_name(fund_name)
        
        for family in families:
            if family.get('fund_identifier'):
                family_fund_normalized = self._normalize_fund_name(family['fund_identifier'])
                # Check if fund names are similar (same core fund name)
                if self._fund_names_similar(fund_normalized, family_fund_normalized):
                    return str(family['id'])
        
        return None
    
    def create_family(self, metadata: Dict) -> str:
        """
        Create a new document family
        
        Args:
            metadata: Document metadata
            
        Returns:
            Family ID (UUID string)
        """
        family_id = str(uuid.uuid4())

        family_entry = {
            'id': family_id,
            'family_name': self._generate_family_name(metadata),
            'fund_identifier': metadata.get('fund_name', 'Unknown Fund'),
            'documents': [metadata],
        }

        self.families[family_id] = family_entry
        return family_id
    
    def assign_to_family(self, metadata: Dict, family_id: str):
        # Nassigni document l family fil cache
        """Assign document metadata to an in-memory family"""
        family = self.families.setdefault(family_id, {
            'id': family_id,
            'family_name': self._generate_family_name(metadata),
            'fund_identifier': metadata.get('fund_name'),
            'documents': []
        })

        family.setdefault('documents', []).append(metadata)
    
    def detect_families_batch(self, documents_metadata: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Detect families for multiple documents
        
        Args:
            documents_metadata: List of metadata dicts
            
        Returns:
            Dict mapping document_id to family_id
        """
        document_to_family: Dict[str, str] = {}
        existing_families = list(self.families.values())

        for metadata in documents_metadata:
            doc_id = metadata.get('document_id') or metadata.get('document_id_extracted')
            if not doc_id:
                doc_id = metadata.get('filename') or str(uuid.uuid4())

            family_id = self.detect_family(metadata, existing_families)

            if family_id:
                document_to_family[doc_id] = family_id
                self.assign_to_family(metadata, family_id)
            else:
                family_id = self.create_family(metadata)
                document_to_family[doc_id] = family_id

            existing_families = list(self.families.values())

        return document_to_family
    
    # Helper methods
    
    def _get_existing_families(self) -> List[Dict]:
        # Nfetchi families men in-memory cache
        """Get existing families from in-memory cache"""
        return list(self.families.values())
    
    def _family_has_document_id(self, family: Dict, doc_id: str) -> bool:
        # Nchecki fi in-memory cache ken fama document b nafs id
        """Check if family has a document with given ID"""
        for doc in family.get('documents', []):
            existing_id = doc.get('document_id') or doc.get('document_id_extracted')
            if existing_id and existing_id == doc_id:
                return True
        return False
    
    def _family_has_folder(self, family: Dict, folder_name: str) -> bool:
        # Nchecki fi in-memory cache ken fama documents men nafs folder
        """Check if family has documents from given folder"""
        for doc in family.get('documents', []):
            directory = doc.get('file_directory')
            if not directory:
                file_path = doc.get('file_path')
                if file_path:
                    directory = Path(file_path).parent
            if not directory:
                continue
            folder = Path(directory).name if not isinstance(directory, Path) else directory.name
            if folder == folder_name:
                return True
        return False
    
    def _normalize_fund_name(self, fund_name: str) -> str:
        # Nnormalizi fund name (remove common words) qbal comparison
        """Normalize fund name for comparison"""
        if not fund_name:
            return ""
        
        # Remove common prefixes/suffixes
        normalized = fund_name.upper().strip()
        normalized = normalized.replace("ODDO BHF", "")
        normalized = normalized.replace("ODDO", "")
        normalized = normalized.replace("BHF", "")
        normalized = normalized.strip()
        
        return normalized
    
    def _dates_match(self, date1: str, date2: str) -> bool:
        # Ncompari dates (exact match) baadh ta3 manipulation simple
        """Check if dates match (exact or same day)"""
        if not date1 or not date2:
            return False
        
        # Extract date part (YYYY-MM-DD)
        date1_part = str(date1)[:10] if len(str(date1)) >= 10 else str(date1)
        date2_part = str(date2)[:10] if len(str(date2)) >= 10 else str(date2)
        
        return date1_part == date2_part
    
    def _fund_names_similar(self, name1: str, name2: str) -> bool:
        # Nchecki simple similarity based on core word overlap
        """Check if fund names are similar (fuzzy match)"""
        if not name1 or not name2:
            return False
        
        # Simple similarity check - same core words
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        # Remove common words
        common_words = {'US', 'EQUITY', 'ACTIVE', 'ETF', 'FUND', 'STRATEGY'}
        words1 = words1 - common_words
        words2 = words2 - common_words
        
        # Check overlap
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        overlap = len(words1.intersection(words2))
        min_length = min(len(words1), len(words2))
        
        # Similar if >50% overlap
        return overlap / min_length > 0.5
    
    def _generate_family_name(self, metadata: Dict) -> str:
        # Ncreatiw family name men fund name w date
        """Generate a family name from metadata"""
        fund_name = metadata.get('fund_name', 'Unknown Fund')
        date = metadata.get('date_extracted')
        
        if date:
            date_str = str(date)[:10]  # YYYY-MM-DD
            return f"{fund_name} - {date_str}"
        else:
            return fund_name
    
    def get_family_documents(self, family_id: str) -> List[Dict]:
        # Njib les documents lkol li 3andhom family_id specified
        """Get all documents in a family"""
        family = self.families.get(family_id)
        if not family:
            return []
        return family.get('documents', [])


def detect_document_family(metadata: Dict[str, Any]) -> Optional[str]:
    # Convenience wrapper: yaayet l DocumentFamilyDetector w y detecti
    """Convenience function to detect document family"""
    detector = DocumentFamilyDetector()
    return detector.detect_family(metadata)


if __name__ == "__main__":
    # Test with example metadata
    from .core.metadata_extractor import MetadataExtractor
    
    test_files = [
        "dataset/example_1/47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx",
        "dataset/example_1/47861-6PG-GB-ODDO BHF Algo Trend US-20250831 v3 pn.pptx",
        "dataset/example_1/FINAL 47861-6PG-FR-ODDO BHF Algo Trend US-20250831.pptx",
        "dataset/example_1/FINAL 47861-6PG-GB-ODDO BHF Algo Trend US-20250831vdef.pptx",
    ]
    
    extractor = MetadataExtractor()
    detector = DocumentFamilyDetector()
    
    print("="*80)
    print("Document Family Detection Test")
    print("="*80)
    
    metadata_list = []
    for test_file in test_files:
        if os.path.exists(test_file):
            metadata = extractor.extract(test_file)
            metadata_list.append(metadata)
            print(f"\nFile: {os.path.basename(test_file)}")
            print(f"   Fund: {metadata.get('fund_name')}")
            print(f"   Date: {metadata.get('date_extracted')}")
            print(f"   Language: {metadata.get('language_code')}")
            print(f"   Version: {metadata.get('version_number')}")
    
    print("\n" + "="*80)
    print("Family Detection Results")
    print("="*80)
    
    # Detect families
    families = {}
    for metadata in metadata_list:
        family_id = detector.detect_family(metadata)
        
        if not family_id:
            # Create new family
            family_id = detector.create_family(metadata)
            print(f"\nSUCCESS: Created new family: {family_id}")
            print(f"   Family name: {detector._generate_family_name(metadata)}")
        else:
            print(f"\nSUCCESS: Matched existing family: {family_id}")
        
        families[metadata.get('filename')] = family_id
    
    # Show grouping
    print("\n" + "="*80)
    print("Document Grouping")
    print("="*80)
    
    family_groups = defaultdict(list)
    for filename, family_id in families.items():
        family_groups[family_id].append(filename)
    
    for family_id, files in family_groups.items():
        print(f"\nFamily {family_id}:")
        for file in files:
            print(f"  - {file}")

