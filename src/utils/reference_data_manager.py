"""
Reference Data Manager
Automates loading and versioning of reference documents (Prospectus, KID, SFDR)
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ReferenceDataManager:
    """Manages reference data loading, versioning, and updates"""
    
    def __init__(self, reference_dir: str = "reference_data"):
        self.reference_dir = Path(reference_dir)
        self.reference_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.reference_dir / "prospectus").mkdir(exist_ok=True)
        (self.reference_dir / "kid").mkdir(exist_ok=True)
        (self.reference_dir / "sfdr").mkdir(exist_ok=True)
        (self.reference_dir / "versions").mkdir(exist_ok=True)
        
        self.version_file = self.reference_dir / "versions" / "version_history.json"
        self._load_version_history()
    
    def _load_version_history(self) -> None:
        """Load version history from file"""
        if self.version_file.exists():
            with open(self.version_file, 'r', encoding='utf-8') as f:
                self.version_history = json.load(f)
        else:
            self.version_history = {
                "prospectus": [],
                "kid": [],
                "sfdr": []
            }
    
    def _save_version_history(self) -> None:
        """Save version history to file"""
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(self.version_history, f, indent=2, ensure_ascii=False)
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def add_reference_document(
        self,
        file_path: str,
        doc_type: str,  # 'prospectus', 'kid', 'sfdr'
        fund_name: str,
        effective_date: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add or update a reference document
        
        Args:
            file_path: Path to the reference document
            doc_type: Type of document ('prospectus', 'kid', 'sfdr')
            fund_name: Name of the fund
            effective_date: Effective date of the document (YYYY-MM-DD)
            metadata: Additional metadata
        
        Returns:
            Dictionary with version information
        """
        if doc_type not in ['prospectus', 'kid', 'sfdr']:
            raise ValueError(f"Invalid doc_type: {doc_type}")
        
        source_path = Path(file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Compute file hash
        file_hash = self._compute_file_hash(source_path)
        
        # Check if this version already exists
        for version in self.version_history[doc_type]:
            if version.get("fund_name") == fund_name and version.get("file_hash") == file_hash:
                logger.info(f"Document already exists: {fund_name} ({doc_type})")
                return version
        
        # Create version entry
        timestamp = datetime.utcnow().isoformat() + "Z"
        version_id = f"{fund_name.replace(' ', '_')}_{timestamp.replace(':', '-').split('.')[0]}"
        
        # Copy file to reference directory
        target_dir = self.reference_dir / doc_type / fund_name.replace(' ', '_')
        target_dir.mkdir(exist_ok=True)
        
        target_path = target_dir / f"{version_id}{source_path.suffix}"
        
        import shutil
        shutil.copy2(source_path, target_path)
        
        # Create version record
        version_record = {
            "version_id": version_id,
            "fund_name": fund_name,
            "doc_type": doc_type,
            "file_path": str(target_path),
            "file_hash": file_hash,
            "added_date": timestamp,
            "effective_date": effective_date or timestamp.split('T')[0],
            "metadata": metadata or {},
            "is_active": True
        }
        
        # Deactivate previous versions
        for version in self.version_history[doc_type]:
            if version.get("fund_name") == fund_name and version.get("is_active"):
                version["is_active"] = False
                version["superseded_by"] = version_id
                version["superseded_date"] = timestamp
        
        # Add new version
        self.version_history[doc_type].append(version_record)
        self._save_version_history()
        
        logger.info(f"Added reference document: {fund_name} ({doc_type}) - {version_id}")
        return version_record
    
    def get_active_document(
        self,
        fund_name: str,
        doc_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get the active version of a reference document"""
        for version in reversed(self.version_history[doc_type]):
            if version.get("fund_name") == fund_name and version.get("is_active"):
                return version
        return None
    
    def get_document_history(
        self,
        fund_name: str,
        doc_type: str
    ) -> List[Dict[str, Any]]:
        """Get version history for a specific fund and document type"""
        return [
            v for v in self.version_history[doc_type]
            if v.get("fund_name") == fund_name
        ]
    
    def check_for_updates(self) -> Dict[str, List[str]]:
        """
        Check which funds need reference data updates
        Returns funds that haven't been updated in 90+ days
        """
        from datetime import timedelta
        
        updates_needed = {
            "prospectus": [],
            "kid": [],
            "sfdr": []
        }
        
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        for doc_type in ["prospectus", "kid", "sfdr"]:
            fund_dates = {}
            
            # Find most recent date for each fund
            for version in self.version_history[doc_type]:
                if not version.get("is_active"):
                    continue
                
                fund_name = version.get("fund_name")
                added_date = datetime.fromisoformat(version.get("added_date").replace('Z', ''))
                
                if fund_name not in fund_dates or added_date > fund_dates[fund_name]:
                    fund_dates[fund_name] = added_date
            
            # Check which funds are outdated
            for fund_name, last_update in fund_dates.items():
                if last_update < cutoff_date:
                    updates_needed[doc_type].append(fund_name)
        
        return updates_needed
    
    def load_reference_data_for_fund(
        self,
        fund_name: str
    ) -> Dict[str, Any]:
        """
        Load all active reference data for a fund
        
        Returns:
            Dictionary with prospectus, kid, and sfdr data
        """
        reference_data = {
            "fund_name": fund_name,
            "prospectus": None,
            "kid": None,
            "sfdr": None,
            "loaded_at": datetime.utcnow().isoformat() + "Z"
        }
        
        for doc_type in ["prospectus", "kid", "sfdr"]:
            doc = self.get_active_document(fund_name, doc_type)
            if doc:
                reference_data[doc_type] = {
                    "file_path": doc["file_path"],
                    "effective_date": doc["effective_date"],
                    "version_id": doc["version_id"],
                    "metadata": doc.get("metadata", {})
                }
        
        return reference_data
    
    def get_all_funds(self) -> List[str]:
        """Get list of all funds in the reference data"""
        funds = set()
        for doc_type in ["prospectus", "kid", "sfdr"]:
            for version in self.version_history[doc_type]:
                funds.add(version.get("fund_name"))
        return sorted(list(funds))
    
    def export_version_report(self, output_path: str) -> None:
        """Export version report to JSON file"""
        report = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_funds": len(self.get_all_funds()),
            "documents_by_type": {
                "prospectus": len([v for v in self.version_history["prospectus"] if v.get("is_active")]),
                "kid": len([v for v in self.version_history["kid"] if v.get("is_active")]),
                "sfdr": len([v for v in self.version_history["sfdr"] if v.get("is_active")])
            },
            "updates_needed": self.check_for_updates(),
            "version_history": self.version_history
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Version report exported to: {output_path}")


def create_reference_manager(reference_dir: str = "reference_data") -> ReferenceDataManager:
    """Factory function to create reference data manager"""
    return ReferenceDataManager(reference_dir)


if __name__ == "__main__":
    # Example usage
    manager = ReferenceDataManager()
    
    # Add a prospectus
    # manager.add_reference_document(
    #     file_path="path/to/prospectus.pdf",
    #     doc_type="prospectus",
    #     fund_name="ODDO BHF Algo Trend US",
    #     effective_date="2025-01-01",
    #     metadata={"language": "EN", "pages": 50}
    # )
    
    # Check for updates
    updates = manager.check_for_updates()
    print("Updates needed:", updates)
    
    # Export report
    manager.export_version_report("reference_data_report.json")
