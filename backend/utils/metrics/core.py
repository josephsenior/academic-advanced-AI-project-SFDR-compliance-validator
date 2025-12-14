"""
Metrics System (modularized)
Contains MetricsCollector and metric dataclasses split from monolithic metrics.py
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
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
		self.metrics_dir = Path(metrics_dir)
		self.metrics_dir.mkdir(parents=True, exist_ok=True)
		self.validation_metrics: List[ValidationMetric] = []
		self.api_metrics: List[APIUsageMetric] = []
		self.performance_metrics: List[PerformanceMetric] = []
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
		self.counters[f"api_{api_name}"] += 1

	def log_performance(
		self,
		operation: str,
		duration_seconds: float,
		items_processed: int,
		memory_mb: Optional[float] = None
	) -> None:
		metric = PerformanceMetric(
			timestamp=datetime.utcnow().isoformat(),
			operation=operation,
			duration_seconds=duration_seconds,
			items_processed=items_processed,
			memory_mb=memory_mb
		)
		self.performance_metrics.append(metric)
		self.counters[f"perf_{operation}"] += 1

	def save_metrics(self) -> None:
		self._save_metrics("validation", self.validation_metrics)
		self._save_metrics("api", self.api_metrics)
		self._save_metrics("performance", self.performance_metrics)

	def _save_metrics(self, metric_type: str, metrics: List[Any]) -> None:
		if not metrics:
			return
		path = self.metrics_dir / f"{metric_type}_metrics.jsonl"
		with path.open("a", encoding="utf-8") as f:
			for metric in metrics:
				f.write(json.dumps(asdict(metric), ensure_ascii=False) + "\n")
		metrics.clear()

	def get_counters(self) -> Dict[str, int]:
		return dict(self.counters)
	
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
		val_by_type: Dict[str, int] = defaultdict(int)
		val_by_severity: Dict[str, int] = defaultdict(int)
		validation_summary = {
			"total": len(recent_validations),
			"passed": sum(1 for m in recent_validations if m.status == "passed"),
			"failed": sum(1 for m in recent_validations if m.status == "failed"),
			"warnings": sum(1 for m in recent_validations if m.status == "warning"),
			"by_type": val_by_type,
			"by_severity": val_by_severity
		}
		
		for m in recent_validations:
			val_by_type[m.validation_type] += 1
			val_by_severity[m.severity] += 1
		
		# API usage summary
		api_by_operation: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0})
		api_summary = {
			"total_calls": len(recent_api),
			"cached_calls": sum(1 for m in recent_api if m.cached),
			"total_tokens": sum(m.tokens_used for m in recent_api),
			"total_cost": sum(m.cost_estimate for m in recent_api),
			"by_operation": api_by_operation,
			"avg_duration": (
				sum(m.duration_seconds for m in recent_api) / len(recent_api)
				if recent_api else 0
			)
		}
		
		for m in recent_api:
			api_by_operation[m.operation]["calls"] += 1
			api_by_operation[m.operation]["tokens"] += m.tokens_used
			api_by_operation[m.operation]["cost"] += m.cost_estimate
		
		# Performance summary
		perf_by_operation: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
			"count": 0,
			"total_duration": 0,
			"total_items": 0
		})
		perf_summary = {
			"total_operations": len(recent_perf),
			"by_operation": perf_by_operation
		}
		
		for m in recent_perf:
			perf_by_operation[m.operation]["count"] += 1
			perf_by_operation[m.operation]["total_duration"] += m.duration_seconds
			perf_by_operation[m.operation]["total_items"] += m.items_processed
		
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