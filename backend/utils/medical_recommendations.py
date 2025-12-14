"""
Medical-Style Recommendation Engine

Generates actionable compliance recommendations with medical-style reporting:
- Severity classification
- Health assessment
- Detailed prescriptions with priority levels
- Treatment plans with time estimates
- Prognosis and follow-up recommendations
"""

from typing import List, Dict, Any, Tuple


class ComplianceSeverity:
    """Severity levels for compliance issues"""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class MedicalRecommendationEngine:
    """
    Generates medical-style compliance recommendations.
    
    Treats compliance issues like medical conditions:
    - Diagnosis (what's wrong)
    - Prescription (how to fix)
    - Prognosis (expected outcome)
    - Follow-up (monitoring plan)
    """
    
    @staticmethod
    def classify_severity(
        score: int,
        missing_count: int,
        incorrect_count: int,
        structural_errors: int
    ) -> str:
        """
        Classify overall document severity.
        
        Args:
            score: Compliance score (0-100)
            missing_count: Number of missing required items
            incorrect_count: Number of incorrect items present
            structural_errors: Number of structural violations
            
        Returns:
            Severity level string
        """
        if incorrect_count > 0 or score < 50:
            return ComplianceSeverity.CRITICAL
        elif score < 70 or missing_count > 3 or structural_errors > 5:
            return ComplianceSeverity.HIGH
        elif score < 90 or missing_count > 0:
            return ComplianceSeverity.MEDIUM
        else:
            return ComplianceSeverity.LOW
    
    @staticmethod
    def get_overall_health(score: int) -> str:
        """
        Determine overall document health status.
        
        Args:
            score: Compliance score (0-100)
            
        Returns:
            Health status string
        """
        if score >= 95:
            return "Excellent"
        elif score >= 85:
            return "Good"
        elif score >= 70:
            return "Moderate"
        elif score >= 50:
            return "Poor"
        else:
            return "Critical"
    
    @staticmethod
    def generate_primary_diagnosis(
        score: int,
        status: str,
        total_missing: int,
        total_incorrect: int,
        doc_type: str = "document"
    ) -> str:
        """
        Generate primary diagnosis statement.
        
        Args:
            score: Compliance score
            status: Compliance status
            total_missing: Total missing items
            total_incorrect: Total incorrect items
            doc_type: Document type
            
        Returns:
            Primary diagnosis string
        """
        if total_incorrect > 0:
            return (
                f"Contamination by inappropriate disclaimers detected ({total_incorrect} cases). "
                f"High regulatory risk requiring immediate intervention."
            )
        elif score < 50:
            return (
                f"Severe compliance deficiency (score: {score}/100). "
                f"Document does not meet regulatory standards."
            )
        elif score < 70:
            return (
                f"Moderate insufficiency in required disclaimers ({total_missing} missing). "
                f"Partial compliance requiring corrections."
            )
        elif score < 90:
            return (
                f"Acceptable compliance with minor gaps. "
                f"{total_missing} disclaimer(s) to be added."
            )
        else:
            return (
                f"Document in good regulatory health (score: {score}/100). "
                f"Satisfactory compliance."
            )
    
    @staticmethod
    def generate_secondary_diagnoses(
        structural_errors: List[str],
        inconsistent_items: List[Dict],
        non_compliant_sections: int,
        total_sections: int,
        low_quality_matches: List[Dict]
    ) -> List[str]:
        """
        Generate secondary diagnosis statements.
        
        Args:
            structural_errors: List of structural error descriptions
            inconsistent_items: List of inconsistent items detected
            non_compliant_sections: Number of non-compliant sections
            total_sections: Total number of sections
            low_quality_matches: List of low-quality matches
            
        Returns:
            List of secondary diagnosis strings
        """
        diagnoses = []
        
        # Structural errors
        if structural_errors:
            count = len(structural_errors)
            diagnoses.append(
                f"Structural anomalies detected ({count} cases): "
                f"document architecture non-compliant"
            )
        
        # Inconsistencies
        if inconsistent_items:
            count = len(inconsistent_items)
            diagnoses.append(
                f"Inter-section inconsistencies ({count} items): "
                f"non-uniform distribution of required elements"
            )
        
        # Non-compliant sections
        if non_compliant_sections > 0:
            pct = round((non_compliant_sections / total_sections) * 100)
            diagnoses.append(
                f"Critical sections detected: {non_compliant_sections}/{total_sections} "
                f"({pct}%) in non-compliant state"
            )
        
        # Low quality matches
        if low_quality_matches:
            diagnoses.append(
                f"Sub-optimal match quality: {len(low_quality_matches)} "
                f"item(s) with score < 70%"
            )
        
        return diagnoses
    
    @staticmethod
    def generate_prescriptions(
        incorrect_items: List[Dict],
        critical_missing: List[Dict],
        non_critical_missing: List[Dict],
        structural_errors: List[str],
        doc_type: str = "document"
    ) -> List[Dict]:
        """
        Generate detailed prescriptions for each issue.
        
        Args:
            incorrect_items: List of incorrect items by section
            critical_missing: List of critical missing items
            non_critical_missing: List of non-critical missing items
            structural_errors: List of structural error descriptions
            doc_type: Document type
            
        Returns:
            List of prescription dictionaries
        """
        prescriptions = []
        
        # Process incorrect items (CRITICAL PRIORITY)
        for item in incorrect_items:
            section_id = item.get('section_id', 'unknown')
            prescriptions.append({
                "issue": f"Inappropriate content detected (Section {section_id})",
                "diagnosis": item.get('reason', 'Content mismatch detected'),
                "prescription": (
                    f"REMOVE IMMEDIATELY the item '{item.get('id', 'unknown')[:60]}...' "
                    f"from section {section_id}. This content is intended for "
                    f"'{item.get('intended_type', 'other')}' documents, not '{doc_type}'."
                ),
                "priority": ComplianceSeverity.CRITICAL,
                "estimated_time": "15 minutes",
                "risk_if_ignored": "Major regulatory non-compliance, risk of sanctions"
            })
        
        # Process critical missing items
        for item in critical_missing:
            sections = item.get('sections', [])
            sections_str = ", ".join(map(str, sections))
            prescriptions.append({
                "issue": "Critical required content missing",
                "diagnosis": (
                    f"Mandatory regulatory content absent from {len(sections)} section(s)"
                ),
                "prescription": (
                    f"ADD IMMEDIATELY the required content '{item.get('id', 'unknown')[:60]}...' "
                    f"to sections: {sections_str}. This is a regulatory requirement."
                ),
                "priority": ComplianceSeverity.CRITICAL,
                "estimated_time": f"{len(sections) * 10} minutes",
                "risk_if_ignored": "Regulatory violation, potential legal consequences"
            })
        
        # Process non-critical missing items
        for item in non_critical_missing:
            sections = item.get('sections', [])
            sections_str = ", ".join(map(str, sections))
            prescriptions.append({
                "issue": "Standard content missing",
                "diagnosis": (
                    f"Recommended content absent from {len(sections)} section(s)"
                ),
                "prescription": (
                    f"Add the content '{item.get('id', 'unknown')[:60]}...' "
                    f"to sections: {sections_str}"
                ),
                "priority": ComplianceSeverity.MEDIUM,
                "estimated_time": f"{len(sections) * 5} minutes",
                "risk_if_ignored": "Incomplete compliance, moderate risk"
            })
        
        # Process structural errors
        for error in structural_errors:
            priority = ComplianceSeverity.HIGH if any(
                word in error.lower() 
                for word in ['missing', 'absent', 'required', 'mandatory']
            ) else ComplianceSeverity.MEDIUM
            
            prescriptions.append({
                "issue": "Structural error",
                "diagnosis": error,
                "prescription": f"Correct the structure: {error}",
                "priority": priority,
                "estimated_time": "20-30 minutes",
                "risk_if_ignored": "Non-compliance with document standards"
            })
        
        # Sort by priority
        priority_order = {
            ComplianceSeverity.CRITICAL: 0,
            ComplianceSeverity.HIGH: 1,
            ComplianceSeverity.MEDIUM: 2,
            ComplianceSeverity.LOW: 3
        }
        prescriptions.sort(key=lambda x: priority_order.get(x['priority'], 999))
        
        return prescriptions
    
    @staticmethod
    def generate_treatment_plan(prescriptions: List[Dict], score: int) -> Dict:
        """
        Generate structured treatment plan.
        
        Args:
            prescriptions: List of prescription dictionaries
            score: Current compliance score
            
        Returns:
            Treatment plan dictionary
        """
        immediate = [p for p in prescriptions if p['priority'] == ComplianceSeverity.CRITICAL]
        short_term = [p for p in prescriptions if p['priority'] == ComplianceSeverity.HIGH]
        long_term = [p for p in prescriptions if p['priority'] in [ComplianceSeverity.MEDIUM, ComplianceSeverity.LOW]]
        
        # Calculate estimated recovery time
        total_time = 0
        for p in prescriptions:
            time_str = p['estimated_time'].split()[0].split('-')[0]
            if time_str.isdigit():
                total_time += int(time_str)
        
        if total_time < 60:
            recovery_time = f"{total_time} minutes"
        else:
            hours = total_time // 60
            minutes = total_time % 60
            recovery_time = f"{hours}h{minutes:02d}"
        
        return {
            "immediate_actions": [
                p['prescription'] for p in immediate
            ] or ["No critical immediate action required"],
            "short_term_actions": [
                p['prescription'] for p in short_term
            ] or ["No short-term action required"],
            "long_term_actions": [
                p['prescription'] for p in long_term
            ] or ["Maintain current compliance level"],
            "estimated_recovery_time": recovery_time,
            "total_prescriptions": len(prescriptions)
        }
    
    @staticmethod
    def generate_prognosis(score: int, prescriptions: List[Dict]) -> Dict:
        """
        Generate recovery prognosis.
        
        Args:
            score: Current compliance score
            prescriptions: List of prescriptions
            
        Returns:
            Prognosis dictionary
        """
        critical_count = sum(1 for p in prescriptions if p['priority'] == ComplianceSeverity.CRITICAL)
        high_count = sum(1 for p in prescriptions if p['priority'] == ComplianceSeverity.HIGH)
        
        # Determine recovery likelihood
        if critical_count == 0 and high_count == 0:
            recovery_likelihood = "Excellent"
            recovery_desc = "Full recovery expected with minor corrections"
        elif critical_count == 0 and high_count <= 2:
            recovery_likelihood = "Good"
            recovery_desc = "Recovery likely with targeted corrections"
        elif critical_count <= 2:
            recovery_likelihood = "Fair"
            recovery_desc = "Recovery possible but requires significant intervention"
        else:
            recovery_likelihood = "Poor"
            recovery_desc = "Recovery difficult, major revision required"
        
        # Risk factors
        risk_factors = []
        if critical_count > 0:
            risk_factors.append(
                f"{critical_count} critical issue(s) requiring immediate attention"
            )
        if high_count > 3:
            risk_factors.append(
                f"High volume of corrections ({high_count} high priority)"
            )
        if score < 50:
            risk_factors.append(
                "Very low compliance score, complete revision recommended"
            )
        
        # Success indicators
        success_indicators = [
            "Compliance score ≥ 90/100",
            "No incorrect content present",
            "All critical required content added",
            "Structural validation without errors",
            "Inter-section consistency verified"
        ]
        
        return {
            "recovery_likelihood": recovery_likelihood,
            "recovery_description": recovery_desc,
            "risk_factors": risk_factors or ["No major risk factors identified"],
            "success_indicators": success_indicators,
            "expected_final_score": min(100, score + (len(prescriptions) * 5))
        }
    
    @staticmethod
    def generate_follow_up(severity: str) -> Dict:
        """
        Generate follow-up recommendations.
        
        Args:
            severity: Severity level string
            
        Returns:
            Follow-up plan dictionary
        """
        if severity == ComplianceSeverity.CRITICAL:
            monitoring = "Daily"
            next_review = "Within 24 hours after corrections"
            checks = [
                "Verify all incorrect content has been removed",
                "Confirm all critical required content has been added",
                "Re-run complete compliance analysis",
                "Validation by compliance officer before distribution"
            ]
        elif severity == ComplianceSeverity.HIGH:
            monitoring = "Every 2-3 days"
            next_review = "Within 48-72 hours after corrections"
            checks = [
                "Verify addition of missing priority content",
                "Check correction of structural errors",
                "Re-analyze modified sections",
                "Internal validation before distribution"
            ]
        elif severity == ComplianceSeverity.MEDIUM:
            monitoring = "Weekly"
            next_review = "Within 1 week"
            checks = [
                "Verify minor corrections",
                "Standard quality control",
                "Routine compliance analysis"
            ]
        else:
            monitoring = "Monthly"
            next_review = "At next document update"
            checks = [
                "Maintain current compliance level",
                "Periodic compliance review"
            ]
        
        return {
            "monitoring_frequency": monitoring,
            "next_review": next_review,
            "recommended_checks": checks,
            "escalation_criteria": [
                "New critical issues discovered",
                "Compliance score drops below 70",
                "Regulatory requirements change"
            ]
        }
    
    @staticmethod
    def generate_medical_report(
        score: int,
        status: str,
        total_missing: int,
        total_incorrect: int,
        structural_errors: List[str],
        inconsistent_items: List[Dict],
        non_compliant_sections: int,
        total_sections: int,
        incorrect_items: List[Dict],
        critical_missing: List[Dict],
        non_critical_missing: List[Dict],
        doc_type: str = "document"
    ) -> Dict:
        """
        Generate complete medical-style report.
        
        Args:
            score: Compliance score
            status: Compliance status
            total_missing: Total missing items
            total_incorrect: Total incorrect items
            structural_errors: List of structural errors
            inconsistent_items: List of inconsistencies
            non_compliant_sections: Number of non-compliant sections
            total_sections: Total sections
            incorrect_items: Detailed incorrect items
            critical_missing: Detailed critical missing items
            non_critical_missing: Detailed non-critical missing items
            doc_type: Document type
            
        Returns:
            Complete medical report dictionary
        """
        severity = MedicalRecommendationEngine.classify_severity(
            score, total_missing, total_incorrect, len(structural_errors)
        )
        
        health = MedicalRecommendationEngine.get_overall_health(score)
        
        primary_diagnosis = MedicalRecommendationEngine.generate_primary_diagnosis(
            score, status, total_missing, total_incorrect, doc_type
        )
        
        secondary_diagnoses = MedicalRecommendationEngine.generate_secondary_diagnoses(
            structural_errors, inconsistent_items,
            non_compliant_sections, total_sections, []
        )
        
        prescriptions = MedicalRecommendationEngine.generate_prescriptions(
            incorrect_items, critical_missing, non_critical_missing,
            structural_errors, doc_type
        )
        
        treatment_plan = MedicalRecommendationEngine.generate_treatment_plan(
            prescriptions, score
        )
        
        prognosis = MedicalRecommendationEngine.generate_prognosis(score, prescriptions)
        
        follow_up = MedicalRecommendationEngine.generate_follow_up(severity)
        
        return {
            "medical_diagnosis": {
                "overall_health": health,
                "severity_level": severity,
                "primary_diagnosis": primary_diagnosis,
                "secondary_diagnoses": secondary_diagnoses
            },
            "prescriptions": prescriptions,
            "treatment_plan": treatment_plan,
            "prognosis": prognosis,
            "follow_up": follow_up,
            "summary": {
                "total_issues": len(prescriptions),
                "critical_issues": sum(1 for p in prescriptions if p['priority'] == ComplianceSeverity.CRITICAL),
                "high_priority_issues": sum(1 for p in prescriptions if p['priority'] == ComplianceSeverity.HIGH),
                "estimated_time": treatment_plan["estimated_recovery_time"],
                "expected_outcome": prognosis["recovery_likelihood"]
            }
        }
