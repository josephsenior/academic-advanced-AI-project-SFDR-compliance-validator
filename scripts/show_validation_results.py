#!/usr/bin/env python3
"""Display validation endpoint results"""

import json
from pathlib import Path

results_file = Path("test_output/validation_endpoint_results.json")

if not results_file.exists():
    print("Results file not found!")
    exit(1)

with open(results_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 70)
print("VALIDATION ENDPOINT RESULTS")
print("=" * 70)
print()
print(f"Document ID: {data.get('document_id')}")
print(f"Overall Status: {data.get('overall_status')}")
print(f"Compliance Score: {data.get('compliance_score')}/100")
print(f"Total Issues: {data.get('total_issues')}")
print()

print("Issues by Severity:")
for k, v in data.get('issues_by_severity', {}).items():
    if v > 0:
        print(f"  {k.capitalize()}: {v}")

print()
print("Statistics:")
stats = data.get('statistics', {})
print(f"  Tables checked: {stats.get('total_tables_checked', 0)}")
print(f"  Tables with source/date: {stats.get('tables_with_source_date', 0)}")
print(f"  Tables missing source/date: {stats.get('tables_missing_source_date', 0)}")
print(f"  Charts analyzed: {stats.get('total_charts_analyzed', 0)}")
print(f"  Charts with source/date: {stats.get('charts_with_source_date', 0)}")
print(f"  Charts missing source/date: {stats.get('charts_missing_source_date', 0)}")

print()
print("Top 10 Issues:")
for i, issue in enumerate(data.get('compliance_issues', [])[:10], 1):
    severity = issue.get('severity', 'unknown').upper()
    issue_type = issue.get('issue_type', 'unknown')
    message = issue.get('message', 'No message')
    location = issue.get('location', 'Unknown')
    print(f"  {i}. [{severity}] {issue_type}")
    print(f"     Location: {location}")
    print(f"     Message: {message[:100]}")
    if issue.get('suggestion'):
        print(f"     Suggestion: {issue.get('suggestion')[:100]}")
    print()

print("=" * 70)
print("Summary:")
for summary_line in data.get('summary', [])[:5]:
    print(f"  - {summary_line}")
print("=" * 70)

