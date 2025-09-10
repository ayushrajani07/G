#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 Metrics System - G6 Platform v3.0
Comprehensive metrics collection, aggregation, and export system.

Features:
- Multi-dimensional metrics with tags and metadata
- Aggregation and statistical analysis
- Multiple export formats (JSON, Prometheus, CSV)
- Real-time metrics streaming
- Historical metrics storage and querying
- Custom metric types and calculations
"""

import time
import logging
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import statistics

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"

class AggregationType(Enum):
    """Aggregation type enumeration."""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    RATE = "rate"
    PERCENTILE = "percentile"

@dataclass
class MetricValue:
    """Individual metric value with metadata."""
    value: Union[float, int]
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'metadata': self.metadata
        }

@dataclass
class Metric:
    """Metric definition with historical values."""
    name: str
    type: MetricType
    description: str
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    values: deque = field(default_factory=lambda: deque(maxlen=10000))
    
    def add_value(self, value: Union[float, int], tags: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """Add a value to the metric."""
        metric_value = MetricValue(
            value=value,
            timestamp=datetime.now(),
            tags={**self.tags, **(tags or {})},
            metadata=metadata or {}
        )
        self.values.append(metric_value)
    
    def get_latest_value(self) -> Optional[MetricValue]:
        """Get the latest metric value."""
        return self.values[-1] if self.values else None
    
    def get_values_since(self, since: datetime) -> List[MetricValue]:
        """Get values since a specific timestamp."""
        return [v for v in self.values if v.timestamp >= since]
    
    def calculate_aggregation(self, 
                            aggregation: AggregationType,
                            since: Optional[datetime] = None,
                            percentile: float = 95.0) -> Optional[float]:
        """Calculate aggregated value."""
        values_to_aggregate = self.get_values_since(since) if since else list(self.values)
        
        if not values_to_aggregate:
            return None
        
        numeric_values = [v.value for v in values_to_aggregate]
        
        if aggregation == AggregationType.SUM:
            return sum(numeric_values)
        elif aggregation == AggregationType.AVERAGE:
            return statistics.mean(numeric_values)
        elif aggregation == AggregationType.MIN:
            return min(numeric_values)
        elif aggregation == AggregationType.MAX:
            return max(numeric_values)
        elif aggregation == AggregationType.COUNT:
            return len(numeric_values)
        elif aggregation == AggregationType.RATE:
            # Calculate rate per second
            if len(values_to_aggregate) < 2:
                return 0.0
            
            first_value = values_to_aggregate[0]
            last_value = values_to_aggregate[-1]
            time_diff = (last_value.timestamp - first_value.timestamp).total_seconds()
            
            if time_diff <= 0:
                return 0.0
            
            value_diff = last_value.value - first_value.value
            return value_diff / time_diff
        elif aggregation == AggregationType.PERCENTILE:
            if len(numeric_values) == 1:
                return numeric_values[0]
            return statistics.quantiles(numeric_values, n=100)[int(percentile) - 1]
        
        return None

class MetricsExporter:
    """Base class for metrics exporters."""
    
    def export(self, metrics: Dict[str, Metric]) -> str:
        """Export metrics to string format."""
        raise NotImplementedError

class JSONExporter(MetricsExporter):
    """JSON format exporter."""
    
    def export(self, metrics: Dict[str, Metric]) -> str:
        """Export metrics to JSON format."""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {}
        }
        
        for name, metric in metrics.items():
            latest_value = metric.get_latest_value()
            
            export_data['metrics'][name] = {
                'type': metric.type.value,
                'description': metric.description,
                'unit': metric.unit,
                'tags': metric.tags,
                'current_value': latest_value.value if latest_value else None,
                'last_updated': latest_value.timestamp.isoformat() if latest_value else None,
                'total_samples': len(metric.values)
            }
        
        return json.dumps(export_data, indent=2)

class PrometheusExporter(MetricsExporter):
    """Prometheus format exporter."""
    
    def export(self, metrics: Dict[str, Metric]) -> str:
        """Export metrics to Prometheus format."""
        lines = []
        
        for name, metric in metrics.items():
            # Add help text
            lines.append(f"# HELP {name} {metric.description}")
            lines.append(f"# TYPE {name} {self._get_prometheus_type(metric.type)}")
            
            # Add metric values
            latest_value = metric.get_latest_value()
            if latest_value:
                tags_str = self._format_prometheus_tags(latest_value.tags)
                lines.append(f"{name}{tags_str} {latest_value.value}")
        
        return '\n'.join(lines)
    
    def _get_prometheus_type(self, metric_type: MetricType) -> str:
        """Convert metric type to Prometheus type."""
        mapping = {
            MetricType.COUNTER: "counter",
            MetricType.GAUGE: "gauge",
            MetricType.HISTOGRAM: "histogram",
            MetricType.SUMMARY: "summary",
            MetricType.TIMER: "histogram"
        }
        return mapping.get(metric_type, "gauge")
    
    def _format_prometheus_tags(self, tags: Dict[str, str]) -> str:
        """Format tags for Prometheus."""
        if not tags:
            return ""
        
        tag_pairs = [f'{key}="{value}"' for key, value in tags.items()]
        return "{" + ",".join(tag_pairs) + "}"

class MetricsSystem:
    """
    📈 Comprehensive metrics collection and export system.
    
    Provides enterprise-grade metrics collection with multiple export formats,
    aggregation capabilities, and real-time monitoring.
    """
    
    def __init__(self,
                 export_interval: int = 60,
                 retention_hours: int = 24,
                 max_metrics: int = 1000,
                 enabled_exporters: List[str] = None):
        """
        Initialize metrics system.
        
        Args:
            export_interval: Export interval in seconds
            retention_hours: Data retention period in hours
            max_metrics: Maximum number of metrics to track
            enabled_exporters: List of enabled exporters
        """
        self.export_interval = export_interval
        self.retention_period = timedelta(hours=retention_hours)
        self.max_metrics = max_metrics
        self.enabled_exporters = enabled_exporters or ['json']
        
        # Metrics storage
        self._metrics: Dict[str, Metric] = {}
        self._lock = threading.RLock()
        
        # Exporters
        self._exporters = {
            'json': JSONExporter(),
            'prometheus': PrometheusExporter()
        }
        
        # Export handlers
        self._export_handlers: List[Callable[[str, str], None]] = []
        
        # Background tasks
        self._export_thread: Optional[threading.Thread] = None
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_background_tasks = threading.Event()
        
        # Aggregated metrics cache
        self._aggregated_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.Lock()
        
        logger.info("📈 Metrics system initialized")
        logger.info(f"⚙️ Export interval: {export_interval}s, Retention: {retention_hours}h")
    
    def start(self):
        """Start metrics system background tasks."""
        if self._export_thread and self._export_thread.is_alive():
            logger.warning("⚠️ Metrics system already running")
            return
        
        self._stop_background_tasks.clear()
        
        # Start export thread
        self._export_thread = threading.Thread(
            target=self._export_loop,
            daemon=True,
            name="MetricsExport"
        )
        self._export_thread.start()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="MetricsCleanup"
        )
        self._cleanup_thread.start()
        
        logger.info("🚀 Metrics system started")
    
    def stop(self, timeout: float = 10.0):
        """Stop metrics system."""
        logger.info("🛑 Stopping metrics system...")
        
        self._stop_background_tasks.set()
        
        # Wait for threads to stop
        for thread in [self._export_thread, self._cleanup_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=timeout/2)
        
        logger.info("✅ Metrics system stopped")
    
    def _export_loop(self):
        """Background export loop."""
        logger.info("📤 Metrics export loop started")
        
        while not self._stop_background_tasks.is_set():
            try:
                # Export metrics for each enabled exporter
                for exporter_name in self.enabled_exporters:
                    if exporter_name in self._exporters:
                        exporter = self._exporters[exporter_name]
                        
                        with self._lock:
                            exported_data = exporter.export(self._metrics)
                        
                        # Notify export handlers
                        for handler in self._export_handlers:
                            try:
                                handler(exporter_name, exported_data)
                            except Exception as e:
                                logger.error(f"🔴 Export handler error: {e}")
                
                # Update aggregated cache
                self._update_aggregated_cache()
                
                # Wait for next export
                self._stop_background_tasks.wait(self.export_interval)
                
            except Exception as e:
                logger.error(f"🔴 Metrics export error: {e}")
                self._stop_background_tasks.wait(60)  # Wait longer on error
        
        logger.info("📤 Metrics export loop stopped")
    
    def _cleanup_loop(self):
        """Background cleanup loop."""
        logger.info("🧹 Metrics cleanup loop started")
        
        while not self._stop_background_tasks.is_set():
            try:
                self._cleanup_old_data()
                
                # Run cleanup every hour
                self._stop_background_tasks.wait(3600)
                
            except Exception as e:
                logger.error(f"🔴 Metrics cleanup error: {e}")
                self._stop_background_tasks.wait(3600)
        
        logger.info("🧹 Metrics cleanup loop stopped")
    
    def _cleanup_old_data(self):
        """Clean up old metric data."""
        cutoff_time = datetime.now() - self.retention_period
        
        with self._lock:
            for metric in self._metrics.values():
                # Remove old values
                while metric.values and metric.values[0].timestamp < cutoff_time:
                    metric.values.popleft()
        
        logger.debug("🧹 Old metrics data cleaned up")
    
    def _update_aggregated_cache(self):
        """Update aggregated metrics cache."""
        try:
            with self._cache_lock:
                self._aggregated_cache = {}
                
                with self._lock:
                    for name, metric in self._metrics.items():
                        # Calculate common aggregations
                        self._aggregated_cache[name] = {
                            'current': metric.get_latest_value().value if metric.get_latest_value() else None,
                            'avg_1h': metric.calculate_aggregation(
                                AggregationType.AVERAGE,
                                since=datetime.now() - timedelta(hours=1)
                            ),
                            'max_1h': metric.calculate_aggregation(
                                AggregationType.MAX,
                                since=datetime.now() - timedelta(hours=1)
                            ),
                            'min_1h': metric.calculate_aggregation(
                                AggregationType.MIN,
                                since=datetime.now() - timedelta(hours=1)
                            ),
                            'count_1h': metric.calculate_aggregation(
                                AggregationType.COUNT,
                                since=datetime.now() - timedelta(hours=1)
                            )
                        }
        
        except Exception as e:
            logger.error(f"🔴 Failed to update aggregated cache: {e}")
    
    # Public API methods
    
    def register_metric(self,
                       name: str,
                       metric_type: MetricType,
                       description: str,
                       unit: str = "",
                       tags: Dict[str, str] = None) -> bool:
        """
        Register a new metric.
        
        Args:
            name: Metric name
            metric_type: Type of metric
            description: Metric description
            unit: Unit of measurement
            tags: Default tags for the metric
            
        Returns:
            True if registered successfully
        """
        try:
            if len(self._metrics) >= self.max_metrics:
                logger.warning(f"⚠️ Maximum metrics limit reached ({self.max_metrics})")
                return False
            
            with self._lock:
                if name in self._metrics:
                    logger.warning(f"⚠️ Metric {name} already registered")
                    return False
                
                metric = Metric(
                    name=name,
                    type=metric_type,
                    description=description,
                    unit=unit,
                    tags=tags or {}
                )
                
                self._metrics[name] = metric
            
            logger.info(f"📊 Metric registered: {name} ({metric_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"🔴 Failed to register metric {name}: {e}")
            return False
    
    def record_value(self,
                    name: str,
                    value: Union[float, int],
                    tags: Dict[str, str] = None,
                    metadata: Dict[str, Any] = None) -> bool:
        """
        Record a value for a metric.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Additional tags
            metadata: Additional metadata
            
        Returns:
            True if recorded successfully
        """
        try:
            with self._lock:
                if name not in self._metrics:
                    # Auto-register as gauge if not exists
                    self.register_metric(name, MetricType.GAUGE, f"Auto-registered metric: {name}")
                
                metric = self._metrics[name]
                metric.add_value(value, tags, metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"🔴 Failed to record value for {name}: {e}")
            return False
    
    def increment_counter(self,
                         name: str,
                         amount: Union[float, int] = 1,
                         tags: Dict[str, str] = None) -> bool:
        """
        Increment a counter metric.
        
        Args:
            name: Counter name
            amount: Amount to increment
            tags: Additional tags
            
        Returns:
            True if incremented successfully
        """
        try:
            with self._lock:
                if name not in self._metrics:
                    self.register_metric(name, MetricType.COUNTER, f"Counter: {name}")
                
                metric = self._metrics[name]
                current_value = metric.get_latest_value()
                new_value = (current_value.value if current_value else 0) + amount
                
                metric.add_value(new_value, tags)
            
            return True
            
        except Exception as e:
            logger.error(f"🔴 Failed to increment counter {name}: {e}")
            return False
    
    def set_gauge(self,
                 name: str,
                 value: Union[float, int],
                 tags: Dict[str, str] = None) -> bool:
        """
        Set a gauge metric value.
        
        Args:
            name: Gauge name
            value: Gauge value
            tags: Additional tags
            
        Returns:
            True if set successfully
        """
        try:
            with self._lock:
                if name not in self._metrics:
                    self.register_metric(name, MetricType.GAUGE, f"Gauge: {name}")
                
                metric = self._metrics[name]
                metric.add_value(value, tags)
            
            return True
            
        except Exception as e:
            logger.error(f"🔴 Failed to set gauge {name}: {e}")
            return False
    
    def time_function(self, name: str, tags: Dict[str, str] = None):
        """
        Decorator to time function execution.
        
        Args:
            name: Timer metric name
            tags: Additional tags
            
        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    execution_time = (time.time() - start_time) * 1000  # Convert to ms
                    self.record_value(name, execution_time, tags)
            return wrapper
        return decorator
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get metric by name."""
        with self._lock:
            return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics with current values."""
        with self._lock:
            result = {}
            for name, metric in self._metrics.items():
                latest_value = metric.get_latest_value()
                result[name] = {
                    'type': metric.type.value,
                    'description': metric.description,
                    'unit': metric.unit,
                    'tags': metric.tags,
                    'current_value': latest_value.value if latest_value else None,
                    'last_updated': latest_value.timestamp.isoformat() if latest_value else None,
                    'total_samples': len(metric.values)
                }
            
            return result
    
    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get cached aggregated metrics."""
        with self._cache_lock:
            return self._aggregated_cache.copy()
    
    def query_metric_history(self,
                            name: str,
                            since: Optional[datetime] = None,
                            aggregation: Optional[AggregationType] = None,
                            window_minutes: int = 5) -> Dict[str, Any]:
        """
        Query metric history with optional aggregation.
        
        Args:
            name: Metric name
            since: Start time for query
            aggregation: Aggregation type
            window_minutes: Window size for time-based aggregation
            
        Returns:
            Query results
        """
        try:
            with self._lock:
                if name not in self._metrics:
                    return {'error': f'Metric {name} not found'}
                
                metric = self._metrics[name]
                since = since or (datetime.now() - timedelta(hours=1))
                
                values = metric.get_values_since(since)
                
                if not values:
                    return {'error': f'No data found for {name} since {since}'}
                
                result = {
                    'metric_name': name,
                    'query_start': since.isoformat(),
                    'query_end': datetime.now().isoformat(),
                    'sample_count': len(values),
                    'values': [v.to_dict() for v in values]
                }
                
                # Add aggregation if requested
                if aggregation:
                    agg_value = metric.calculate_aggregation(aggregation, since)
                    result['aggregation'] = {
                        'type': aggregation.value,
                        'value': agg_value
                    }
                
                return result
                
        except Exception as e:
            logger.error(f"🔴 Failed to query metric history for {name}: {e}")
            return {'error': str(e)}
    
    def export_metrics(self, format_type: str = 'json') -> Optional[str]:
        """
        Export metrics in specified format.
        
        Args:
            format_type: Export format (json, prometheus)
            
        Returns:
            Exported metrics string or None if error
        """
        try:
            if format_type not in self._exporters:
                logger.error(f"🔴 Unknown export format: {format_type}")
                return None
            
            exporter = self._exporters[format_type]
            
            with self._lock:
                return exporter.export(self._metrics)
                
        except Exception as e:
            logger.error(f"🔴 Failed to export metrics: {e}")
            return None
    
    def add_export_handler(self, handler: Callable[[str, str], None]):
        """
        Add export handler.
        
        Args:
            handler: Function to handle exported metrics (format, data)
        """
        self._export_handlers.append(handler)
        logger.info("✅ Metrics export handler added")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get metrics system statistics."""
        with self._lock:
            total_values = sum(len(metric.values) for metric in self._metrics.values())
            
            return {
                'total_metrics': len(self._metrics),
                'total_values': total_values,
                'max_metrics': self.max_metrics,
                'retention_hours': self.retention_period.total_seconds() / 3600,
                'export_interval': self.export_interval,
                'enabled_exporters': self.enabled_exporters,
                'background_tasks_running': not self._stop_background_tasks.is_set()
            }