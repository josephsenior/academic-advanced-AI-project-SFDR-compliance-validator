#!/usr/bin/env python3
"""Test what the validator returns"""

from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent
import json

agent = DataConsistencyAgent()

with open('outputs/full_pipeline_test/extraction.json', encoding='utf-8') as f:
    extraction = json.load(f)

with open('dataset/example_3/metadata.json', encoding='utf-8') as f:
    metadata = json.load(f)

result = agent.validate(extraction, metadata)

print(f"Validation result type: {type(result)}")
print(f"Has compliance_issues: {hasattr(result, 'compliance_issues')}")
print(f"compliance_issues count: {len(result.compliance_issues)}")
print(f"\nFirst 3 issues:")
for i, issue in enumerate(result.compliance_issues[:3], 1):
    print(f"{i}. [{issue.severity}] {issue.issue_type}: {issue.message}")
