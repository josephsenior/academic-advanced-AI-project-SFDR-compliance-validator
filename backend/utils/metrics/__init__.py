"""
Metrics module
"""

from .core import (
    MetricsCollector,
    ValidationMetric,
    APIUsageMetric,
    PerformanceMetric
)

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Global metrics collector
_global_metrics = None


def get_metrics_collector(metrics_dir: str = "metrics") -> MetricsCollector:
    """Get or create global metrics collector"""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector(metrics_dir)
    return _global_metrics


class AlertSystem:
    """Alert system for critical events"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        """
        Initialize alert system
        
        Args:
            metrics_collector: MetricsCollector instance to monitor
        """
        self.metrics = metrics_collector
        self.alerts: List[Dict[str, Any]] = []
        
        # Thresholds
        self.thresholds = {
            "validation_failure_rate": 0.2,  # 20% failure rate
            "api_cost_per_hour": 10.0,  # $10/hour
            "critical_validation_failures": 3  # 3 critical failures
        }
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        new_alerts = []
        summary = self.metrics.get_summary(hours=1)
        
        # Check validation failure rate
        total_validations = summary["validation"]["total"]
        if total_validations > 10:  # Need minimum sample
            failure_rate = summary["validation"]["failed"] / total_validations
            if failure_rate > self.thresholds["validation_failure_rate"]:
                new_alerts.append({
                    "type": "high_validation_failure_rate",
                    "severity": "warning",
                    "message": f"Validation failure rate: {failure_rate:.1%}",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check API costs
        hourly_cost = summary["api_usage"]["total_cost"]
        if hourly_cost > self.thresholds["api_cost_per_hour"]:
            new_alerts.append({
                "type": "high_api_cost",
                "severity": "warning",
                "message": f"API cost: ${hourly_cost:.2f}/hour",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check critical validation failures
        critical_failures = summary["validation"]["by_severity"].get("critical", 0)
        if critical_failures >= self.thresholds["critical_validation_failures"]:
            new_alerts.append({
                "type": "critical_validation_failures",
                "severity": "critical",
                "message": f"{critical_failures} critical validation failures in last hour",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        self.alerts.extend(new_alerts)
        
        for alert in new_alerts:
            logger.warning(f"ALERT: {alert['message']}")
        
        return new_alerts
    
    def get_active_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alerts from specified time period"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        
        return [
            alert for alert in self.alerts
            if alert["timestamp"] >= cutoff_str
        ]


__all__ = [
    'MetricsCollector',
    'ValidationMetric',
    'APIUsageMetric',
    'PerformanceMetric',
    'get_metrics_collector',
    'AlertSystem',
]
