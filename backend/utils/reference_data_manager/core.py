"""
Reference Data Manager (modularized)
Contains ReferenceDataManager split from monolithic reference_data_manager.py
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
		(self.reference_dir / "prospectus").mkdir(exist_ok=True)
		(self.reference_dir / "kid").mkdir(exist_ok=True)
		(self.reference_dir / "sfdr").mkdir(exist_ok=True)
		(self.reference_dir / "versions").mkdir(exist_ok=True)
		self.version_file = self.reference_dir / "versions" / "version_history.json"
		self._load_version_history()

	def _load_version_history(self) -> None:
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
		with open(self.version_file, 'w', encoding='utf-8') as f:
			json.dump(self.version_history, f, indent=2, ensure_ascii=False)

	def _compute_file_hash(self, file_path: Path) -> str:
		sha256 = hashlib.sha256()
		with open(file_path, 'rb') as f:
			for chunk in iter(lambda: f.read(4096), b''):
				sha256.update(chunk)
		return sha256.hexdigest()

	def add_reference_document(
		self,
		file_path_str: str,
		doc_type: str,  # 'prospectus', 'kid', 'sfdr'
		fund_name: str,
		version: Optional[str] = None,
		metadata: Optional[Dict[str, Any]] = None
	) -> Dict[str, Any]:
		file_path = Path(file_path_str)
		if not file_path.exists():
			raise FileNotFoundError(f"Reference document not found: {file_path}")
		file_hash = self._compute_file_hash(file_path)
		version = version or datetime.now().strftime("%Y%m%d")
		dest_dir = self.reference_dir / doc_type.lower()
		dest_file = dest_dir / f"{fund_name}_{version}{file_path.suffix}"
		dest_file.write_bytes(file_path.read_bytes())
		entry = {
			"fund_name": fund_name,
			"version": version,
			"file": str(dest_file),
			"hash": file_hash,
			"metadata": metadata or {},
			"added_at": datetime.now().isoformat()
		}
		self.version_history.setdefault(doc_type, []).append(entry)
		self._save_version_history()
		return entry

	def get_latest_reference(self, fund_name: str, doc_type: str) -> Optional[Dict[str, Any]]:
		entries = self.version_history.get(doc_type, [])
		candidates = [e for e in entries if e["fund_name"] == fund_name]
		if not candidates:
			return None
		return max(candidates, key=lambda e: e["version"])

	def list_versions(self, fund_name: str, doc_type: str) -> List[Dict[str, Any]]:
		entries = self.version_history.get(doc_type, [])
		return [e for e in entries if e["fund_name"] == fund_name]

	def load_reference_data_for_fund(self, fund_name: str) -> Optional[Dict[str, Any]]:
		# This is a stub for loading parsed reference data for a fund
		# In a real system, this would load from a database or pre-parsed JSON
		# For now, just return the latest reference document metadata
		for doc_type in ["prospectus", "kid", "sfdr"]:
			latest = self.get_latest_reference(fund_name, doc_type)
			if latest:
				return latest
		return None
