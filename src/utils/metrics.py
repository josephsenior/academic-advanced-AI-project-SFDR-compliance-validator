"""
Monitoring and Metrics System
Tracks validation metrics, API usage, and system performance
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ValidationMetric:
    """Single validation metric"""
    timestamp: str
    validation_type: str  # disclaimer, numerical, esg, etc.
    status: str  # passed, failed, warning
    document_type: str  # prospectus, kid, etc.
    fund_name: Optional[str] = None
    error_message: Optional[str] = None
    severity: str = "info"  # info, warning, error, critical


@dataclass
class APIUsageMetric:
    """API usage tracking"""
    timestamp: str
    api_name: str  # openai, anthropic, etc.
    model: str
    operation: str  # chart_analysis, esg_validation, etc.
    tokens_used: int
    duration_seconds: float
    cost_estimate: float
    cached: bool = False


@dataclass
class PerformanceMetric:
    """Performance tracking"""
    timestamp: str
    operation: str
    duration_seconds: float
    items_processed: int
    memory_mb: Optional[float] = None


class MetricsCollector:
    """Collects and stores metrics"""
    
    def __init__(self, metrics_dir: str = "metrics"):
        """
        Initialize metrics collector
        
        Args:
            metrics_dir: Directory to store metrics
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory buffers
        self.validation_metrics: List[ValidationMetric] = []
        self.api_metrics: List[APIUsageMetric] = []
        self.performance_metrics: List[PerformanceMetric] = []
        
        # Counters
        self.counters = defaultdict(int)
    
    def log_validation(
        self,
        validation_type: str,
        status: str,
        document_type: str,
        fund_name: Optional[str] = None,
        error_message: Optional[str] = None,
        severity: str = "info"
    ) -> None:
        """Log a validation event"""
        metric = ValidationMetric(
            timestamp=datetime.utcnow().isoformat(),
            validation_type=validation_type,
            status=status,
            document_type=document_type,
            fund_name=fund_name,
            error_message=error_message,
            severity=severity
        )
        
        self.validation_metrics.append(metric)
        self.counters[f"validation_{status}"] += 1
        
        if status == "failed" and severity in ["error", "critical"]:
            logger.warning(
                f"Validation failed: {validation_type} for {document_type} - {error_message}"
            )
    
    def log_api_usage(
        self,
        api_name: str,
        model: str,
        operation: str,
        tokens_used: int,
        duration_seconds: float,
        cost_estimate: float,
        cached: bool = False
    ) -> None:
        """Log API usage"""
        metric = APIUsageMetric(
            timestamp=datetime.utcnow().isoformat(),
            api_name=api_name,
            model=model,
            operation=operation,
            tokens_used=tokens_used,
            duration_seconds=duration_seconds,
            cost_estimate=cost_estimate,
            cached=cached
        )
        
        self.api_metrics.append(metric)
        self.counters["api_calls"] += 1
        self.counters["total_tokens"] += tokens_used
    
    def log_performance(
        self,
        operation: str,
        duration_seconds: float,
        items_processed: int,
        memory_mb: Optional[float] = None
    ) -> None:
        """Log performance metric"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow().isoformat(),
            operation=operation,
            duration_seconds=duration_seconds,
            items_processed=items_processed,
            memory_mb=memory_mb
        )
        
        self.performance_metrics.append(metric)
        self.counters[f"perf_{operation}"] += 1
    
    def get_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get summary of metrics for specified time period
        
        Args:
            hours: Number of hours to summarize
        
        Returns:
            Dictionary with summary statistics
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        
        # Filter metrics by time
        recent_validations = [
            m for m in self.validation_metrics
            if m.timestamp >= cutoff_str
        ]
        recent_api = [
            m for m in self.api_metrics
            if m.timestamp >= cutoff_str
        ]
        recent_perf = [
            m for m in self.performance_metrics
            if m.timestamp >= cutoff_str
        ]
        
        # Validation summary
        validation_summary = {
            "total": len(recent_validations),
            "passed": sum(1 for m in recent_validations if m.status == "passed"),
            "failed": sum(1 for m in recent_validations if m.status == "failed"),
            "warnings": sum(1 for m in recent_validations if m.status == "warning"),
            "by_type": defaultdict(int),
            "by_severity": defaultdict(int)
        }
        
        for m in recent_validations:
            validation_summary["by_type"][m.validation_type] += 1
            validation_summary["by_severity"][m.severity] += 1
        
        # API usage summary
        api_summary = {
            "total_calls": len(recent_api),
            "cached_calls": sum(1 for m in recent_api if m.cached),
            "total_tokens": sum(m.tokens_used for m in recent_api),
            "total_cost": sum(m.cost_estimate for m in recent_api),
            "by_operation": defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0}),
            "avg_duration": (
                sum(m.duration_seconds for m in recent_api) / len(recent_api)
                if recent_api else 0
            )
        }
        
        for m in recent_api:
            api_summary["by_operation"][m.operation]["calls"] += 1
            api_summary["by_operation"][m.operation]["tokens"] += m.tokens_used
            api_summary["by_operation"][m.operation]["cost"] += m.cost_estimate
        
        # Performance summary
        perf_summary = {
            "total_operations": len(recent_perf),
            "by_operation": defaultdict(lambda: {
                "count": 0,
                "total_duration": 0,
                "total_items": 0
            })
        }
        
        for m in recent_perf:
            perf_summary["by_operation"][m.operation]["count"] += 1
            perf_summary["by_operation"][m.operation]["total_duration"] += m.duration_seconds
            perf_summary["by_operation"][m.operation]["total_items"] += m.items_processed
        
        return {
            "period_hours": hours,
            "generated_at": datetime.utcnow().isoformat(),
            "validation": dict(validation_summary),
            "api_usage": dict(api_summary),
            "performance": dict(perf_summary)
        }
    
    def export_metrics(self, output_path: Optional[str] = None) -> str:
        """
        Export all metrics to JSON file
        
        Args:
            output_path: Optional custom output path
        
        Returns:
            Path to exported file
        """
        if output_path is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = self.metrics_dir / f"metrics_{timestamp}.json"
        
        metrics_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "validation_metrics": [asdict(m) for m in self.validation_metrics],
            "api_metrics": [asdict(m) for m in self.api_metrics],
            "performance_metrics": [asdict(m) for m in self.performance_metrics],
            "counters": dict(self.counters),
            "summary": self.get_summary(hours=24)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported metrics to {output_path}")
        return str(output_path)
    
    def flush(self) -> None:
        """Clear all in-memory metrics"""
        self.validation_metrics.clear()
        self.api_metrics.clear()
        self.performance_metrics.clear()
        logger.info("Metrics flushed")


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


# Global metrics collector
_global_metrics = None


def get_metrics_collector(metrics_dir: str = "metrics") -> MetricsCollector:
    """Get or create global metrics collector"""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector(metrics_dir)
    return _global_metrics


if __name__ == "__main__":
    # Test metrics system
    collector = MetricsCollector()
    
    # Log some test metrics
    collector.log_validation("disclaimer", "passed", "prospectus", "Test Fund")
    collector.log_validation("numerical", "failed", "kid", "Test Fund", "Value mismatch", "error")
    collector.log_api_usage("openai", "gpt-4", "chart_analysis", 1500, 2.5, 0.045)
    collector.log_performance("document_extraction", 45.3, 1)
    
    # Get summary
    summary = collector.get_summary(hours=24)
    print("Summary:")
    print(json.dumps(summary, indent=2))
    
    # Export metrics
    output = collector.export_metrics()
    print(f"\nExported to: {output}")
    
    # Test alerts
    alert_system = AlertSystem(collector)
    alerts = alert_system.check_alerts()
    print(f"\nAlerts: {len(alerts)}")
