from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

def standardize_results(results: dict) -> dict:
    """Standardize severities and structure for frontend and backend consumers."""
    if not results:
        return results

    # Map for severity standardization
    severity_map = {
        "error": "critical",
        "warning": "high",
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "low"
    }

    # Fix compliance_issues list
    if "compliance_issues" in results:
        for issue in results["compliance_issues"]:
            # Robust get severity
            sev = issue.get("severity") if isinstance(issue, dict) else getattr(issue, "severity", None)
            if sev in severity_map:
                new_sev = severity_map[sev]
                if isinstance(issue, dict):
                    issue["severity"] = new_sev
                else:
                    try:
                        setattr(issue, "severity", new_sev)
                    except (AttributeError, TypeError):
                        pass

    # Build issues_by_category if missing (crucial for frontend and fixers)
    if "compliance_issues" in results and "issues_by_category" not in results:
        issues_by_cat = {}
        for issue in results["compliance_issues"]:
            cat = None
            if isinstance(issue, dict):
                 cat = issue.get("category") or issue.get("issue_category")
            else:
                 cat = getattr(issue, "category", None) or getattr(issue, "issue_category", None)
            
            cat = cat or "compliance"
            if cat not in issues_by_cat:
                issues_by_cat[cat] = []
            issues_by_cat[cat].append(issue)
        results["issues_by_category"] = issues_by_cat

    # Fix issues_by_category list
    if "issues_by_category" in results:
        for category, issues in results["issues_by_category"].items():
            for issue in issues:
                sev = issue.get("severity") if isinstance(issue, dict) else getattr(issue, "severity", None)
                if sev in severity_map:
                    new_sev = severity_map[sev]
                    if isinstance(issue, dict):
                        issue["severity"] = new_sev
                    else:
                        try:
                            setattr(issue, "severity", new_sev)
                        except (AttributeError, TypeError):
                            pass

    # Rebuild issues_by_severity counts
    if "compliance_issues" in results:
        issues = results["compliance_issues"]
        def get_sev(i):
             return i.get("severity") if isinstance(i, dict) else getattr(i, "severity", None)
             
        results["issues_by_severity"] = {
            "critical": sum(1 for i in issues if get_sev(i) == "critical"),
            "high": sum(1 for i in issues if get_sev(i) == "high"),
            "medium": sum(1 for i in issues if get_sev(i) == "medium"),
            "low": sum(1 for i in issues if get_sev(i) == "low"),
        }

    # Add descriptive label if missing (legacy results)
    if "compliance_status_label" not in results:
        score = results.get("compliance_score", 100)
        if score == 100:
            results["compliance_status_label"] = "Totally compliant"
        elif score > 0:
            results["compliance_status_label"] = "Partially compliant"
        else:
            results["compliance_status_label"] = "Non-compliant"

    return results
