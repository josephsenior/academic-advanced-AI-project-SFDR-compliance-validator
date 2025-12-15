"""
Registration Parser File Utilities

Utilities for finding and managing registration files.
"""

import re
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime


def find_latest_registration_file(dataset_dir: Path) -> Path:
    """
    Auto-discover the most recent registration file in dataset directory.
    
    Args:
        dataset_dir: Directory to search for registration files
        
    Returns:
        Path to the latest registration file
    """
    if not dataset_dir.exists():
        # Fallback to default
        return Path("dataset/Registration abroad of Funds_20251008.xlsx")
    
    # Search for registration files with various patterns
    patterns = [
        "Registration*Funds*.xlsx",
        "Registration*abroad*.xlsx",
        "registration*.xlsx"
    ]
    
    all_files = []
    for pattern in patterns:
        all_files.extend(dataset_dir.glob(pattern))
    
    if not all_files:
        # Fallback to default
        return Path("dataset/Registration abroad of Funds_20251008.xlsx")
    
    # Sort by modification time, return most recent
    latest_file = max(all_files, key=lambda p: p.stat().st_mtime)
    print(f"[INFO] Auto-discovered registration file: {latest_file.name}")
    
    return latest_file


def extract_file_version(registration_path: Path) -> Tuple[Optional[str], Optional[datetime]]:
    """
    Extract version/date information from filename.
    
    Args:
        registration_path: Path to registration file
        
    Returns:
        Tuple of (version_string, date_object)
    """
    filename = registration_path.stem
    
    # Try to extract date from filename (format: YYYYMMDD or YYYY-MM-DD)
    date_match = re.search(r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})', filename)
    if date_match:
        year, month, day = date_match.groups()
        try:
            file_date = datetime(int(year), int(month), int(day))
            version = f"{year}-{month}-{day}"
            return version, file_date
        except ValueError:
            pass
    
    # Fallback: use file modification time
    try:
        mod_time = datetime.fromtimestamp(registration_path.stat().st_mtime)
        version = mod_time.strftime("%Y-%m-%d")
        return version, mod_time
    except Exception:
        return None, None

