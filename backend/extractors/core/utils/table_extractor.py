"""
Table Extraction Utilities

Utilities for extracting and normalizing table data.
"""

from typing import List, Dict, Any
from .text_utils import parse_numeric_value


def normalize_table_rows(rows: List[List[str]]) -> List[Dict[str, Any]]:
    """Normalize table rows into structured entries."""
    if not rows or len(rows) < 2:
        return []
    headers = [str(h).strip() for h in rows[0]]
    entries = []
    for row in rows[1:]:
        if not row:
            continue
        label = str(row[0]).strip()
        if not label:
            continue
        for idx, cell in enumerate(row[1:], start=1):
            cell_text = str(cell).strip()
            if not cell_text:
                continue
            value = parse_numeric_value(cell_text)
            if value is None:
                continue
            column = headers[idx] if idx < len(headers) else f'column_{idx}'
            entries.append({
                'label': label,
                'column': column,
                'value': value,
                'raw': cell_text,
            })
    return entries


def extract_pptx_table(table) -> List[List[str]]:
    """Extract data from PowerPoint table."""
    rows = []
    for row in table.rows:
        cells = [cell.text.strip() if cell.text else "" for cell in row.cells]
        rows.append(cells)
    return rows


def extract_docx_table(table) -> List[List[str]]:
    """Extract data from Word document table."""
    rows = []
    for row in table.rows:
        cells = [cell.text.strip() if cell.text else "" for cell in row.cells]
        rows.append(cells)
    return rows

