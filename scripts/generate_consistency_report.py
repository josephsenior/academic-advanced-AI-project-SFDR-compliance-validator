import json
import re
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
TEST_OUTPUT = WORKSPACE / 'test_output'
REPORT_PATH = TEST_OUTPUT / 'consistency_report.json'

DATE_PATTERNS = [
    r"(\d{4}-\d{2}-\d{2})",
    r"(\d{2}/\d{2}/\d{4})",
    r"(\d{8})"
]


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def normalize(text: str):
    return (text or '').lower()


def find_date_variants(date_str: str):
    # date_str expected like YYYY-MM-DD
    if not date_str:
        return []
    variants = set()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if m:
        y, mo, d = m.groups()
        variants.add(f"{y}-{mo}-{d}")
        variants.add(f"{d}/{mo}/{y}")
        variants.add(f"{y}{mo}{d}")
        variants.add(f"{d} {mo} {y}")
    else:
        variants.add(date_str)
    return list(variants)


def main():
    TEST_OUTPUT.mkdir(parents=True, exist_ok=True)

    # Load all metadata.json files and index by document_id_extracted
    metadata_index = {}
    for md in TEST_OUTPUT.rglob('metadata.json'):
        data = load_json(md)
        if not data:
            continue
        doc_id = str(data.get('document_id_extracted'))
        if doc_id:
            metadata_index[doc_id] = {
                'path': str(md),
                'data': data
            }

    report = []

    # Process content JSON files (those that contain 'text' or 'slides')
    for jf in TEST_OUTPUT.rglob('*.json'):
        # skip metadata files
        if jf.name == 'metadata.json' or jf.name == 'consistency_report.json':
            continue

        data = load_json(jf)
        if not data:
            continue

        is_content = 'text' in data or 'slides' in data
        if not is_content:
            continue

        filename = jf.name
        # Try extract 5-digit doc id from filename
        doc_id_match = re.search(r"(\d{5})", filename)
        doc_id = doc_id_match.group(1) if doc_id_match else None

        matched_md = metadata_index.get(doc_id)
        metadata_present = matched_md is not None
        metadata = matched_md['data'] if matched_md else None

        text = data.get('text', '')
        text_norm = normalize(text)

        fund_name = metadata.get('fund_name') if metadata else None
        fund_in_text = False
        if fund_name:
            fund_in_text = normalize(fund_name) in text_norm

        # Date check
        metadata_date = metadata.get('date_extracted') if metadata else None
        date_in_text = False
        if metadata_date:
            for variant in find_date_variants(str(metadata_date)):
                if variant in text or variant in text_norm:
                    date_in_text = True
                    break

        slides = data.get('total_slides') or len(data.get('slides', []))
        tables = data.get('total_tables') or len(data.get('tables', []))

        # Countries detected (from slide_summaries or table entries)
        countries = set()
        for s in data.get('slide_summaries', []):
            for c in s.get('countries', []):
                countries.add(c)

        # Basic flags
        flags = []
        if not metadata_present:
            flags.append('missing_metadata')
        if fund_name and not fund_in_text:
            flags.append('fund_not_in_text')
        if metadata_date and not date_in_text:
            flags.append('date_not_in_text')

        report.append({
            'file': str(jf.relative_to(TEST_OUTPUT)),
            'document_id': doc_id,
            'metadata_present': metadata_present,
            'metadata_path': matched_md['path'] if matched_md else None,
            'fund_name': fund_name,
            'fund_in_text': fund_in_text,
            'metadata_date': metadata_date,
            'date_in_text': date_in_text,
            'slides': slides,
            'tables': tables,
            'countries_detected': sorted(list(countries)),
            'flags': flags
        })

    # Write report
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    # Print brief summary
    total = len(report)
    issues = sum(1 for r in report if r['flags'])
    print(f"Consistency report written to: {REPORT_PATH}")
    print(f"Files checked: {total}, with issues: {issues}")


if __name__ == '__main__':
    main()
