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
from typing import Dict, Optional

from backend.extractors.agents.data_consistency_agent import DataConsistencyResult  # type: ignore


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
        
        def get_val(obj, key, default=None):
            if hasattr(obj, key):
                return getattr(obj, key)
            if isinstance(obj, dict):
                val = obj.get(key)
                if val is not None:
                    return val
                # Check inside nested 'statistics' if present
                stats = obj.get('statistics', {})
                return stats.get(key, default)
            return default

        status_color = {
            "pass": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
            "compliant": "#28a745",
            "non_compliant": "#dc3545"
        }.get(get_val(validation_result, 'overall_status'), "#6c757d")
        
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
        <p><strong>Document:</strong> {document_name or get_val(validation_result, 'filename') or get_val(validation_result, 'document_id') or 'N/A'}</p>
        <p><strong>Document ID:</strong> {get_val(validation_result, 'document_id') or 'N/A'}</p>
        <p><strong>Validation Date:</strong> {get_val(validation_result, 'validation_timestamp')}</p>
        <p><strong>Compliance Status:</strong> <strong>{get_val(validation_result, 'compliance_status_label', 'N/A')}</strong></p>
        <p><strong>Validation Status:</strong> <span class="status-badge">{str(get_val(validation_result, 'overall_status', 'N/A')).upper()}</span></p>
    </div>
    
    <div class="section">
        <h2>Summary</h2>
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-value">{get_val(validation_result, 'total_tables_checked', 0)}</div>
                <div class="stat-label">Tables/Charts Checked</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{get_val(validation_result, 'tables_with_source_date', 0)}</div>
                <div class="stat-label">With Source & Date</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([i for i in get_val(validation_result, 'compliance_issues', []) if get_val(i, 'severity', '') in ['error', 'critical']])}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([i for i in get_val(validation_result, 'compliance_issues', []) if get_val(i, 'severity', '') in ['warning', 'high']])}</div>
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
                html += """                <tr>
                    <td>""" + str(issue.location) + """</td>
                    <td>""" + str(issue.issue_type.replace('_', ' ').title()) + """</td>
                    <td class=""" + str(severity_class) + """>""" + str(issue.severity.upper()) + """</td>
                    <td>""" + str(issue.message) + """</td>
                </tr>
"""
            html += """            </tbody>
        </table>
"""
        else:
            html += """        <p class="pass">[PASS] No source/date issues found</p>
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
                    html += """                <tr>
                    <td>""" + str(inc.location) + """</td>
                    <td>""" + str(inc.document_value) + "%" + """</td>
                    <td>""" + str(inc.reference_value or 'N/A') + "%" + """</td>
                    <td>""" + str(inc.period or 'N/A') + """</td>
                    <td class=\""" + str(severity_class) + ""\">""" + str(inc.severity.upper()) + """</td>
                    <td>""" + str(inc.message) + """</td>
                </tr>
"""
                html += """            </tbody>
        </table>
"""
            else:
                html += """        <p class="pass">[PASS] No numerical inconsistencies found</p>
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
                html += (
                    "                <tr>\n"
                    f"                    <td>{issue.location}</td>\n"
                    f"                    <td>{issue.issue_type.replace('_', ' ').title()}</td>\n"
                    f"                    <td>{issue.value1 or 'N/A'}</td>\n"
                    f"                    <td>{issue.value2 or 'N/A'}</td>\n"
                    f"                    <td class=\"{severity_class}\">{issue.severity.upper()}</td>\n"
                    f"                    <td>{issue.message}</td>\n"
                    "                </tr>\n"
                )
            html += """            </tbody>
        </table>
    </div>
"""
        
        html += """</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

    def generate_pdf_report(
        self,
        validation_result: DataConsistencyResult,
        output_path: Path,
        document_name: Optional[str] = None
    ) -> None:
        """Generate a clean, minimalist PDF report using ReportLab."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        except Exception as e:
            raise RuntimeError("ReportLab is required for PDF generation") from e

        # Ensure validation_result is a Pydantic model, not a dict
        if isinstance(validation_result, dict):
            try:
                validation_result = DataConsistencyResult(**validation_result)
            except Exception as e:
                print(f"Warning: Failed to convert dict to DataConsistencyResult: {e}")
                # Fallback: wrap in a simple object to allow attribute access?
                # Or just let it fail, but the conversion is the right fix.


        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        normal = styles['Normal']
        h1 = ParagraphStyle('Heading1', parent=styles['Heading1'], alignment=0, spaceAfter=12)
        h2 = ParagraphStyle('Heading2', parent=styles['Heading2'], spaceAfter=8)

        story = []

        def get_val(obj, key, default=None):
            if hasattr(obj, key):
                return getattr(obj, key)
            if isinstance(obj, dict):
                val = obj.get(key)
                if val is not None:
                    return val
                # Check inside nested 'statistics' if present
                stats = obj.get('statistics', {})
                return stats.get(key, default)
            return default

        # === HEADER SECTION ===
        doc_id = get_val(validation_result, 'document_id', 'N/A')
        val_time = get_val(validation_result, 'validation_timestamp', 'N/A')
        overall_status = str(get_val(validation_result, 'overall_status', 'UNKNOWN')).upper()
        compliance_score = get_val(validation_result, 'compliance_score', 0)

        title_text = f"SFDR Compliance Validation Report"
        story.append(Paragraph(title_text, h1))
        story.append(Paragraph(f"<b>Document:</b> {document_name or 'N/A'}", normal))
        story.append(Spacer(1, 8))

        # === EXECUTIVE SUMMARY ===
        story.append(Paragraph("Executive Summary", h2))
        
        # Status badge color
        status_color = "#dc2626" if overall_status == "NON_COMPLIANT" else "#16a34a" if overall_status == "COMPLIANT" else "#f59e0b"
        
        summary_info = [
            ["Document ID", str(doc_id) if doc_id else "N/A"],
            ["Validation Date", str(val_time)],
            ["Compliance Status", get_val(validation_result, 'compliance_status_label', 'N/A')],
            ["Overall Status", overall_status],
            ["Compliance Score", f"{compliance_score}/100"],
        ]
        
        # Get issue counts
        compliance_issues = get_val(validation_result, 'compliance_issues', [])
        total_issues = len(compliance_issues)
        
        critical_count = sum(1 for i in compliance_issues if get_val(i, 'severity', '') in ['critical', 'error'])
        high_count = sum(1 for i in compliance_issues if get_val(i, 'severity', '') in ['high', 'warning'])
        medium_count = sum(1 for i in compliance_issues if get_val(i, 'severity', '') == 'medium')
        low_count = sum(1 for i in compliance_issues if get_val(i, 'severity', '') == 'low')
        
        summary_info.extend([
            ["Total Issues Found", str(total_issues)],
            ["Critical Issues", str(critical_count)],
            ["High Priority Issues", str(high_count)],
            ["Medium Priority Issues", str(medium_count)],
            ["Low Priority Issues", str(low_count)],
        ])
        
        summary_table = Table(summary_info, colWidths=[150, 350])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 16))

        # === DOCUMENT METADATA ===
        metadata = get_val(validation_result, 'metadata', {})
        if metadata:
            story.append(Paragraph("Document Metadata", h2))
            meta_items = []
            meta_fields = [
                ('fund_name', 'Fund Name'),
                ('societe_de_gestion', 'Management Company'),
                ('is_professional_client', 'Professional Client'),
                ('is_new_product', 'New Product'),
                ('is_new_strategy', 'New Strategy'),
                ('is_sicav', 'SICAV'),
                ('sfdr_article', 'SFDR Article'),
            ]
            for key, label in meta_fields:
                val = metadata.get(key) if isinstance(metadata, dict) else getattr(metadata, key, None)
                if val is not None:
                    display_val = "Yes" if val is True else "No" if val is False else str(val)
                    meta_items.append([label, display_val])
            
            if meta_items:
                meta_table = Table(meta_items, colWidths=[150, 350])
                meta_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fafafa')),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e8e8e8')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(meta_table)
            story.append(Spacer(1, 16))

        # === VALIDATION STATISTICS ===
        story.append(Paragraph("Validation Statistics", h2))
        
        total_tables = get_val(validation_result, 'total_tables_checked', 0)
        tables_with_source = get_val(validation_result, 'tables_with_source_date', 0)
        total_charts = get_val(validation_result, 'total_charts_analyzed', 0)
        charts_with_source = get_val(validation_result, 'charts_with_source_date', 0)
        numerical_checked = get_val(validation_result, 'total_numerical_values_checked', 0)
        numerical_matching = get_val(validation_result, 'values_matching_reference', 0)
        
        stats_data = [
            ["Metric", "Value", "Status"],
            ["Tables Checked", str(total_tables), "✓" if total_tables > 0 else "-"],
            ["Tables with Source/Date", str(tables_with_source), "✓" if tables_with_source == total_tables else "!"],
            ["Charts Analyzed", str(total_charts), "✓" if total_charts > 0 else "-"],
            ["Charts with Source/Date", str(charts_with_source), "✓" if charts_with_source == total_charts else "!"],
            ["Numerical Values Checked", str(numerical_checked), "✓" if numerical_checked > 0 else "-"],
            ["Values Matching Reference", str(numerical_matching), "✓" if numerical_matching == numerical_checked else "!"],
        ]
        
        stats_table = Table(stats_data, colWidths=[200, 150, 50])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 20))

        # === DETAILED COMPLIANCE ISSUES ===
        if compliance_issues:
            story.append(Paragraph("Detailed Compliance Issues", h1))
            story.append(Spacer(1, 8))
            
            # Group issues by category
            issues_by_category = {}
            for issue in compliance_issues:
                cat = get_val(issue, 'issue_category', None) or get_val(issue, 'category', 'compliance') or 'compliance'
                if cat not in issues_by_category:
                    issues_by_category[cat] = []
                issues_by_category[cat].append(issue)
            
            issue_number = 0
            for category, cat_issues in sorted(issues_by_category.items()):
                # Category header
                cat_title = category.replace('_', ' ').upper()
                story.append(Paragraph(f"<b>{cat_title}</b> ({len(cat_issues)} issue{'s' if len(cat_issues) != 1 else ''})", h2))
                story.append(Spacer(1, 6))
                
                for issue in cat_issues:
                    issue_number += 1
                    
                    issue_type = get_val(issue, 'issue_type', 'Unknown')
                    severity = str(get_val(issue, 'severity', 'medium')).upper()
                    location = get_val(issue, 'location', 'N/A')
                    slide_num = get_val(issue, 'slide_number', None)
                    message = get_val(issue, 'message', 'No description')
                    context = get_val(issue, 'context', None)
                    suggestion = get_val(issue, 'suggestion', None)
                    rule_ref = get_val(issue, 'rule_reference', None)
                    auto_fixable = get_val(issue, 'auto_fixable', False)
                    
                    # Severity color
                    sev_color = "#dc2626" if severity in ['CRITICAL', 'ERROR'] else "#f97316" if severity in ['HIGH', 'WARNING'] else "#eab308" if severity == 'MEDIUM' else "#6b7280"
                    
                    # Issue header
                    issue_header = f"<b>Issue #{issue_number}:</b> {issue_type.replace('_', ' ').title()}"
                    story.append(Paragraph(issue_header, normal))
                    
                    # Issue details table
                    issue_details = [
                        ["Severity", severity],
                        ["Location", f"{location}" + (f" (Slide {slide_num})" if slide_num else "")],
                    ]
                    
                    # Add full message
                    issue_details.append(["Description", message])
                    
                    # Add context if available
                    if context:
                        issue_details.append(["Context", str(context)])
                    
                    # Add suggestion if available
                    if suggestion:
                        issue_details.append(["Suggested Fix", suggestion])
                    
                    # Add rule reference if available
                    if rule_ref:
                        issue_details.append(["Rule Reference", rule_ref])
                    
                    # Add auto-fixable status
                    issue_details.append(["Auto-Fixable", "Yes ✓" if auto_fixable else "No - Manual Review Required"])
                    
                    issue_table = Table(issue_details, colWidths=[100, 400])
                    issue_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f9fafb')),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    story.append(issue_table)
                    story.append(Spacer(1, 10))
                
                story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("Compliance Issues", h2))
            story.append(Paragraph("<b>✓ PASS</b> - No compliance issues found. Document is compliant.", normal))

        # === SUMMARY SECTION ===
        story.append(Spacer(1, 20))
        story.append(Paragraph("Summary", h2))
        
        summary_text = get_val(validation_result, 'summary', [])
        if summary_text:
            if isinstance(summary_text, list):
                for line in summary_text:
                    story.append(Paragraph(f"• {line}", normal))
            else:
                story.append(Paragraph(str(summary_text), normal))
        else:
            story.append(Paragraph(f"Validation completed with {total_issues} issue(s) found.", normal))
        
        story.append(Spacer(1, 16))
        story.append(Paragraph(f"<i>Report generated on {val_time}</i>", normal))

        # Finalize
        doc.build(story)

    
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

