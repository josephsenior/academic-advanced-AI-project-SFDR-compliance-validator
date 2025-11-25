"""
Validation Report Generator

Generates multiple output formats from DataConsistencyResult:
- JSON (full result)
- HTML (human-readable report)
- CSV (issues list)
- Summary JSON (dashboard-friendly)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from src.extractors.data_consistency_agent import DataConsistencyResult


class ValidationReportGenerator:
    """Generate multiple report formats from validation results"""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_all_reports(
        self,
        validation_result: DataConsistencyResult,
        document_id: str,
        document_name: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Generate all report formats and return paths to generated files.
        
        Args:
            validation_result: DataConsistencyResult from agent.validate()
            document_id: Document identifier
            document_name: Optional document name for display
            
        Returns:
            Dict mapping report type to file path
        """
        doc_output_dir = self.output_dir / document_id
        doc_output_dir.mkdir(parents=True, exist_ok=True)
        
        reports = {}
        
        # Generate JSON report
        json_path = doc_output_dir / "data_consistency_result.json"
        self.generate_json_report(validation_result, json_path)
        reports['json'] = json_path
        
        # Generate HTML report
        html_path = doc_output_dir / "data_consistency_report.html"
        self.generate_html_report(validation_result, html_path, document_name)
        reports['html'] = html_path
        
        # Generate CSV report
        csv_path = doc_output_dir / "data_consistency_issues.csv"
        self.generate_csv_report(validation_result, csv_path)
        reports['csv'] = csv_path
        
        # Generate summary JSON
        summary_path = doc_output_dir / "data_consistency_summary.json"
        self.generate_summary_json(validation_result, summary_path)
        reports['summary'] = summary_path
        
        return reports
    
    def generate_json_report(
        self,
        validation_result: DataConsistencyResult,
        output_path: Path
    ) -> None:
        """Generate full JSON report"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(validation_result.model_dump(), f, indent=2, ensure_ascii=False)
    
    def generate_html_report(
        self,
        validation_result: DataConsistencyResult,
        output_path: Path,
        document_name: Optional[str] = None
    ) -> None:
        """Generate human-readable HTML report"""
        
        status_color = {
            "pass": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545"
        }.get(validation_result.overall_status, "#6c757d")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Consistency Report - {document_name or validation_result.document_id or 'Document'}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
            background-color: {status_color};
        }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .section h2 {{
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }}
        .error {{
            color: #dc3545;
            font-weight: 600;
        }}
        .warning {{
            color: #ffc107;
            font-weight: 600;
        }}
        .pass {{
            color: #28a745;
            font-weight: 600;
        }}
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .stat-label {{
            color: #6c757d;
            font-size: 14px;
            margin-top: 5px;
        }}
        .summary-list {{
            list-style: none;
            padding: 0;
        }}
        .summary-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        .summary-list li:last-child {{
            border-bottom: none;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Data Consistency Validation Report</h1>
        <p><strong>Document:</strong> {document_name or validation_result.document_id or 'N/A'}</p>
        <p><strong>Document ID:</strong> {validation_result.document_id or 'N/A'}</p>
        <p><strong>Validation Date:</strong> {validation_result.validation_timestamp}</p>
        <p><strong>Status:</strong> <span class="status-badge">{validation_result.overall_status.upper()}</span></p>
    </div>
    
    <div class="section">
        <h2>Summary</h2>
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-value">{validation_result.total_tables_checked}</div>
                <div class="stat-label">Tables/Charts Checked</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{validation_result.tables_with_source_date}</div>
                <div class="stat-label">With Source & Date</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([i for i in validation_result.source_date_issues if i.severity == 'error'])}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([i for i in validation_result.source_date_issues if i.severity == 'warning'])}</div>
                <div class="stat-label">Warnings</div>
            </div>
        </div>
        <ul class="summary-list">
"""
        
        for msg in validation_result.summary:
            html += f"            <li>{msg}</li>\n"
        
        html += """        </ul>
    </div>
    
    <div class="section">
        <h2>Source/Date Validation</h2>
        <p><strong>Tables Checked:</strong> {total_checked} | 
           <strong>Compliant:</strong> {compliant} | 
           <strong>Issues:</strong> {issues}</p>
""".format(
            total_checked=validation_result.total_tables_checked,
            compliant=validation_result.tables_with_source_date,
            issues=validation_result.tables_missing_source_date
        )
        
        if validation_result.source_date_issues:
            html += """        <table>
            <thead>
                <tr>
                    <th>Location</th>
                    <th>Issue Type</th>
                    <th>Severity</th>
                    <th>Message</th>
                </tr>
            </thead>
            <tbody>
"""
            for issue in validation_result.source_date_issues:
                severity_class = issue.severity
                html += f"""                <tr>
                    <td>{issue.location}</td>
                    <td>{issue.issue_type.replace('_', ' ').title()}</td>
                    <td class="{severity_class}">{issue.severity.upper()}</td>
                    <td>{issue.message}</td>
                </tr>
"""
            html += """            </tbody>
        </table>
"""
        else:
            html += """        <p class="pass">✅ No source/date issues found</p>
"""
        
        html += """    </div>
"""
        
        # Numerical validation section
        if validation_result.total_numerical_values_checked > 0:
            html += f"""    <div class="section">
        <h2>Numerical Validation</h2>
        <p><strong>Values Checked:</strong> {validation_result.total_numerical_values_checked} | 
           <strong>Matching:</strong> {validation_result.values_matching_reference} | 
           <strong>Inconsistencies:</strong> {validation_result.values_with_inconsistencies}</p>
"""
            
            if validation_result.numerical_inconsistencies:
                html += """        <table>
            <thead>
                <tr>
                    <th>Location</th>
                    <th>Document Value</th>
                    <th>Reference Value</th>
                    <th>Period</th>
                    <th>Severity</th>
                    <th>Message</th>
                </tr>
            </thead>
            <tbody>
"""
                for inc in validation_result.numerical_inconsistencies:
                    severity_class = inc.severity
                    html += f"""                <tr>
                    <td>{inc.location}</td>
                    <td>{inc.document_value}%</td>
                    <td>{inc.reference_value or 'N/A'}%</td>
                    <td>{inc.period or 'N/A'}</td>
                    <td class="{severity_class}">{inc.severity.upper()}</td>
                    <td>{inc.message}</td>
                </tr>
"""
                html += """            </tbody>
        </table>
"""
            else:
                html += """        <p class="pass">✅ No numerical inconsistencies found</p>
"""
            
            html += """    </div>
"""
        
        # Cross-reference validation section
        if validation_result.cross_reference_issues:
            html += """    <div class="section">
        <h2>Cross-Reference Validation</h2>
        <table>
            <thead>
                <tr>
                    <th>Location</th>
                    <th>Issue Type</th>
                    <th>Value 1</th>
                    <th>Value 2</th>
                    <th>Severity</th>
                    <th>Message</th>
                </tr>
            </thead>
            <tbody>
"""
            for issue in validation_result.cross_reference_issues:
                severity_class = issue.severity
                html += f"""                <tr>
                    <td>{issue.location}</td>
                    <td>{issue.issue_type.replace('_', ' ').title()}</td>
                    <td>{issue.value1 or 'N/A'}</td>
                    <td>{issue.value2 or 'N/A'}</td>
                    <td class="{severity_class}">{issue.severity.upper()}</td>
                    <td>{issue.message}</td>
                </tr>
"""
            html += """            </tbody>
        </table>
    </div>
"""
        
        html += """</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def generate_csv_report(
        self,
        validation_result: DataConsistencyResult,
        output_path: Path
    ) -> None:
        """Generate CSV report with all issues"""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Issue Type',
                'Category',
                'Location',
                'Severity',
                'Message',
                'Document Value',
                'Reference Value',
                'Period',
                'Document ID'
            ])
            
            # Source/Date issues
            for issue in validation_result.source_date_issues:
                writer.writerow([
                    issue.issue_type,
                    'source_date',
                    issue.location,
                    issue.severity,
                    issue.message,
                    '',
                    '',
                    '',
                    validation_result.document_id or ''
                ])
            
            # Numerical inconsistencies
            for inc in validation_result.numerical_inconsistencies:
                writer.writerow([
                    'numerical_inconsistency',
                    'numerical',
                    inc.location,
                    inc.severity,
                    inc.message,
                    inc.document_value,
                    inc.reference_value or '',
                    inc.period or '',
                    validation_result.document_id or ''
                ])
            
            # Cross-reference issues
            for issue in validation_result.cross_reference_issues:
                writer.writerow([
                    issue.issue_type,
                    'cross_reference',
                    issue.location,
                    issue.severity,
                    issue.message,
                    issue.value1 or '',
                    issue.value2 or '',
                    issue.period or '',
                    validation_result.document_id or ''
                ])
    
    def generate_summary_json(
        self,
        validation_result: DataConsistencyResult,
        output_path: Path
    ) -> None:
        """Generate dashboard-friendly summary JSON"""
        
        error_count = len([i for i in validation_result.source_date_issues if i.severity == 'error'])
        warning_count = len([i for i in validation_result.source_date_issues if i.severity == 'warning'])
        
        # Calculate score (0-100)
        total_checks = (
            validation_result.total_tables_checked +
            validation_result.total_numerical_values_checked
        )
        passed_checks = (
            validation_result.tables_with_source_date +
            validation_result.values_matching_reference
        )
        score = int((passed_checks / total_checks * 100)) if total_checks > 0 else 100
        
        summary = {
            'document_id': validation_result.document_id,
            'validation_timestamp': validation_result.validation_timestamp,
            'status': validation_result.overall_status,
            'score': score,
            'has_errors': validation_result.has_errors,
            'has_warnings': validation_result.has_warnings,
            'issues_count': {
                'errors': error_count + len([i for i in validation_result.numerical_inconsistencies if i.severity == 'error']),
                'warnings': warning_count + len([i for i in validation_result.numerical_inconsistencies if i.severity == 'warning'])
            },
            'quick_summary': {
                'source_date': f"{validation_result.tables_with_source_date}/{validation_result.total_tables_checked} tables compliant",
                'numerical': f"{validation_result.values_matching_reference}/{validation_result.total_numerical_values_checked} values match" if validation_result.total_numerical_values_checked > 0 else "No numerical validation",
                'cross_reference': f"{len(validation_result.cross_reference_issues)} issues found" if validation_result.cross_reference_issues else "No cross-reference issues"
            },
            'action_required': validation_result.has_errors
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

