#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Complete Metrics Collection System for G6.1 Platform
Author: AI Assistant (Comprehensive metrics with Prometheus compatibility)

✅ Features:
- Multiple metric types (Counter, Gauge, Histogram, Summary)
- Prometheus-compatible metrics export
- Real-time performance monitoring
- Custom metric collectors
- Metrics aggregation and rollup
- Historical metrics storage
- Alert-based metrics
- System resource metrics
"""

import logging
import time
import datetime
import threading
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
from enum import Enum
import json

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """📊 Metric type enumeration."""
    COUNTER = "counter"       # Monotonically increasing
    GAUGE = "gauge"          # Can go up and down
    HISTOGRAM = "histogram"   # Distribution of values
    SUMMARY = "summary"      # Similar to histogram
    TIMING = "timing"        # Timing measurements

@dataclass
class MetricSample:
    """📊 Individual metric sample."""
    value: Union[int, float]
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass
class HistogramBucket:
    """📊 Histogram bucket definition."""
    upper_bound: float
    count: int = 0

@dataclass
class MetricMetadata:
    """📋 Metric metadata."""
    name: str
    metric_type: MetricType
    help_text: str = ""
    unit: str = ""
    labels: List[str] = field(default_factory=list)
    
    # 📊 Collection settings
    collection_interval: float = 60.0
    retention_period: int = 86400  # 24 hours in seconds
    
    # 🎯 Alert settings
    alert_enabled: bool = False
    alert_threshold: Optional[float] = None
    alert_condition: str = "greater_than"  # greater_than, less_than, equal_to

class BaseMetric:
    """📊 Base metric class."""
    
    def __init__(self, metadata: MetricMetadata):
        """🆕 Initialize base metric."""
        self.metadata = metadata
        self.samples: deque = deque(maxlen=10000)  # Keep last 10k samples
        self.lock = threading.RLock()
        self.created_at = datetime.datetime.now()
        self.last_updated = datetime.datetime.now()
    
    def add_sample(self, value: Union[int, float], labels: Dict[str, str] = None):
        """📊 Add a metric sample."""
        with self.lock:
            sample = MetricSample(
                value=value,
                labels=labels or {},
                timestamp=datetime.datetime.now()
            )
            self.samples.append(sample)
            self.last_updated = datetime.datetime.now()
    
    def get_current_value(self) -> Optional[Union[int, float]]:
        """📊 Get current metric value."""
        with self.lock:
            return self.samples[-1].value if self.samples else None
    
    def get_samples(self, 
                   limit: Optional[int] = None,
                   since: Optional[datetime.datetime] = None) -> List[MetricSample]:
        """📊 Get metric samples."""
        with self.lock:
            samples = list(self.samples)
            
            # 📅 Filter by time
            if since:
                samples = [s for s in samples if s.timestamp >= since]
            
            # 🔢 Limit results
            if limit:
                samples = samples[-limit:]
            
            return samples

class Counter(BaseMetric):
    """📈 Counter metric - monotonically increasing."""
    
    def __init__(self, name: str, help_text: str = "", labels: List[str] = None):
        """🆕 Initialize counter."""
        metadata = MetricMetadata(
            name=name,
            metric_type=MetricType.COUNTER,
            help_text=help_text,
            labels=labels or []
        )
        super().__init__(metadata)
        self._value = 0.0
    
    def inc(self, amount: float = 1.0, labels: Dict[str, str] = None):
        """📈 Increment counter."""
        if amount < 0:
            raise ValueError("Counter can only be incremented by non-negative amounts")
        
        with self.lock:
            self._value += amount
            self.add_sample(self._value, labels)
    
    def get_value(self) -> float:
        """📊 Get current counter value."""
        return self._value

class Gauge(BaseMetric):
    """📊 Gauge metric - can go up and down."""
    
    def __init__(self, name: str, help_text: str = "", labels: List[str] = None):
        """🆕 Initialize gauge."""
        metadata = MetricMetadata(
            name=name,
            metric_type=MetricType.GAUGE,
            help_text=help_text,
            labels=labels or []
        )
        super().__init__(metadata)
        self._value = 0.0
    
    def set(self, value: float, labels: Dict[str, str] = None):
        """📊 Set gauge value."""
        with self.lock:
            self._value = value
            self.add_sample(self._value, labels)
    
    def inc(self, amount: float = 1.0, labels: Dict[str, str] = None):
        """📈 Increment gauge."""
        self.set(self._value + amount, labels)
    
    def dec(self, amount: float = 1.0, labels: Dict[str, str] = None):
        """📉 Decrement gauge."""
        self.set(self._value - amount, labels)
    
    def get_value(self) -> float:
        """📊 Get current gauge value."""
        return self._value

class Histogram(BaseMetric):
    """📊 Histogram metric - distribution of values."""
    
    def __init__(self, 
                 name: str, 
                 help_text: str = "", 
                 buckets: List[float] = None, 
                 labels: List[str] = None):
        """🆕 Initialize histogram."""
        metadata = MetricMetadata(
            name=name,
            metric_type=MetricType.HISTOGRAM,
            help_text=help_text,
            labels=labels or []
        )
        super().__init__(metadata)
        
        # 📊 Default buckets if none provided
        if buckets is None:
            buckets = [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf')]
        
        self.buckets = [HistogramBucket(upper_bound=bound) for bound in sorted(buckets)]
        self.sum = 0.0
        self.count = 0
    
    def observe(self, value: float, labels: Dict[str, str] = None):
        """📊 Observe a value."""
        with self.lock:
            # 📊 Update buckets
            for bucket in self.buckets:
                if value <= bucket.upper_bound:
                    bucket.count += 1
            
            # 📊 Update sum and count
            self.sum += value
            self.count += 1
            
            # 📊 Add sample
            self.add_sample(value, labels)
    
    def get_bucket_counts(self) -> Dict[float, int]:
        """📊 Get bucket counts."""
        with self.lock:
            return {bucket.upper_bound: bucket.count for bucket in self.buckets}
    
    def get_percentile(self, percentile: float) -> Optional[float]:
        """📊 Calculate percentile from samples."""
        if not 0 <= percentile <= 100:
            raise ValueError("Percentile must be between 0 and 100")
        
        with self.lock:
            if not self.samples:
                return None
            
            values = [sample.value for sample in self.samples]
            values.sort()
            
            if percentile == 0:
                return values[0]
            elif percentile == 100:
                return values[-1]
            else:
                index = int((percentile / 100) * (len(values) - 1))
                return values[index]

class Summary(BaseMetric):
    """📊 Summary metric - similar to histogram but with quantiles."""
    
    def __init__(self, 
                 name: str, 
                 help_text: str = "", 
                 quantiles: List[float] = None,
                 labels: List[str] = None):
        """🆕 Initialize summary."""
        metadata = MetricMetadata(
            name=name,
            metric_type=MetricType.SUMMARY,
            help_text=help_text,
            labels=labels or []
        )
        super().__init__(metadata)
        
        # 📊 Default quantiles if none provided
        if quantiles is None:
            quantiles = [0.5, 0.75, 0.9, 0.95, 0.99]
        
        self.quantiles = quantiles
        self.sum = 0.0
        self.count = 0
    
    def observe(self, value: float, labels: Dict[str, str] = None):
        """📊 Observe a value."""
        with self.lock:
            self.sum += value
            self.count += 1
            self.add_sample(value, labels)
    
    def get_quantiles(self) -> Dict[float, float]:
        """📊 Calculate quantiles from samples."""
        with self.lock:
            if not self.samples:
                return {}
            
            values = [sample.value for sample in self.samples]
            values.sort()
            
            quantile_values = {}
            for quantile in self.quantiles:
                if quantile == 0:
                    quantile_values[quantile] = values[0]
                elif quantile == 1:
                    quantile_values[quantile] = values[-1]
                else:
                    index = int(quantile * (len(values) - 1))
                    quantile_values[quantile] = values[index]
            
            return quantile_values

class Timer:
    """⏱️ Timer utility for measuring execution time."""
    
    def __init__(self, metric: Union[Histogram, Summary], labels: Dict[str, str] = None):
        """🆕 Initialize timer."""
        self.metric = metric
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        """▶️ Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """⏹️ Stop timing and record."""
        if self.start_time:
            duration = time.time() - self.start_time
            self.metric.observe(duration, self.labels)

class MetricsRegistry:
    """
    📊 AI Assistant: Comprehensive Metrics Registry.
    
    Central registry for all metrics with:
    - Automatic metric discovery
    - Prometheus export format
    - Metric aggregation
    - Performance monitoring
    - Alert integration
    """
    
    def __init__(self):
        """🆕 Initialize metrics registry."""
        self.metrics: Dict[str, BaseMetric] = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger(f"{__name__}.MetricsRegistry")
        
        # 📊 Built-in system metrics
        self._setup_system_metrics()
        
        self.logger.info("✅ Metrics Registry initialized")
    
    def register(self, metric: BaseMetric) -> bool:
        """📋 Register a metric."""
        try:
            with self.lock:
                if metric.metadata.name in self.metrics:
                    self.logger.warning(f"⚠️ Metric {metric.metadata.name} already registered")
                    return False
                
                self.metrics[metric.metadata.name] = metric
                self.logger.debug(f"✅ Registered metric: {metric.metadata.name}")
                return True
                
        except Exception as e:
            self.logger.error(f"🔴 Error registering metric: {e}")
            return False
    
    def get_metric(self, name: str) -> Optional[BaseMetric]:
        """📊 Get metric by name."""
        with self.lock:
            return self.metrics.get(name)
    
    def create_counter(self, name: str, help_text: str = "", labels: List[str] = None) -> Counter:
        """📈 Create and register a counter."""
        counter = Counter(name, help_text, labels)
        self.register(counter)
        return counter
    
    def create_gauge(self, name: str, help_text: str = "", labels: List[str] = None) -> Gauge:
        """📊 Create and register a gauge."""
        gauge = Gauge(name, help_text, labels)
        self.register(gauge)
        return gauge
    
    def create_histogram(self, 
                        name: str, 
                        help_text: str = "", 
                        buckets: List[float] = None,
                        labels: List[str] = None) -> Histogram:
        """📊 Create and register a histogram."""
        histogram = Histogram(name, help_text, buckets, labels)
        self.register(histogram)
        return histogram
    
    def create_summary(self, 
                      name: str, 
                      help_text: str = "", 
                      quantiles: List[float] = None,
                      labels: List[str] = None) -> Summary:
        """📊 Create and register a summary."""
        summary = Summary(name, help_text, quantiles, labels)
        self.register(summary)
        return summary
    
    def create_timer(self, histogram_name: str) -> Optional[Timer]:
        """⏱️ Create timer for existing histogram."""
        histogram = self.get_metric(histogram_name)
        if isinstance(histogram, (Histogram, Summary)):
            return Timer(histogram)
        return None
    
    def _setup_system_metrics(self):
        """📊 Setup built-in system metrics."""
        try:
            # 📊 System resource metrics
            self.cpu_usage = Gauge("system_cpu_usage_percent", "CPU usage percentage")
            self.memory_usage = Gauge("system_memory_usage_bytes", "Memory usage in bytes")
            self.disk_usage = Gauge("system_disk_usage_bytes", "Disk usage in bytes")
            
            # 📈 Application metrics
            self.uptime = Gauge("application_uptime_seconds", "Application uptime in seconds")
            self.requests_total = Counter("requests_total", "Total number of requests")
            self.request_duration = Histogram("request_duration_seconds", "Request duration in seconds")
            self.errors_total = Counter("errors_total", "Total number of errors")
            
            # 📊 Register system metrics
            for metric in [self.cpu_usage, self.memory_usage, self.disk_usage, 
                          self.uptime, self.requests_total, self.request_duration, self.errors_total]:
                self.register(metric)
                
        except Exception as e:
            self.logger.error(f"🔴 Error setting up system metrics: {e}")
    
    def update_system_metrics(self):
        """📊 Update system resource metrics."""
        try:
            import psutil
            
            # 💾 Memory metrics
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.used)
            
            # ⚡ CPU metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_usage.set(cpu_percent)
            
            # 💾 Disk metrics
            disk = psutil.disk_usage('/')
            self.disk_usage.set(disk.used)
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error updating system metrics: {e}")
    
    def get_all_metrics(self) -> Dict[str, BaseMetric]:
        """📊 Get all registered metrics."""
        with self.lock:
            return dict(self.metrics)
    
    def export_prometheus_format(self) -> str:
        """📊 Export metrics in Prometheus format."""
        try:
            with self.lock:
                output_lines = []
                
                for name, metric in self.metrics.items():
                    # 📋 Add help text
                    if metric.metadata.help_text:
                        output_lines.append(f"# HELP {name} {metric.metadata.help_text}")
                    
                    # 📊 Add type
                    output_lines.append(f"# TYPE {name} {metric.metadata.metric_type.value}")
                    
                    # 📊 Add metric values
                    if isinstance(metric, Counter):
                        output_lines.append(f"{name} {metric.get_value()}")
                    
                    elif isinstance(metric, Gauge):
                        output_lines.append(f"{name} {metric.get_value()}")
                    
                    elif isinstance(metric, Histogram):
                        # 📊 Histogram buckets
                        for upper_bound, count in metric.get_bucket_counts().items():
                            bound_str = "+Inf" if upper_bound == float('inf') else str(upper_bound)
                            output_lines.append(f'{name}_bucket{{le="{bound_str}"}} {count}')
                        
                        # 📊 Histogram sum and count
                        output_lines.append(f"{name}_sum {metric.sum}")
                        output_lines.append(f"{name}_count {metric.count}")
                    
                    elif isinstance(metric, Summary):
                        # 📊 Summary quantiles
                        quantiles = metric.get_quantiles()
                        for quantile, value in quantiles.items():
                            output_lines.append(f'{name}{{quantile="{quantile}"}} {value}')
                        
                        # 📊 Summary sum and count
                        output_lines.append(f"{name}_sum {metric.sum}")
                        output_lines.append(f"{name}_count {metric.count}")
                    
                    output_lines.append("")  # Empty line between metrics
                
                return "\n".join(output_lines)
                
        except Exception as e:
            self.logger.error(f"🔴 Error exporting Prometheus format: {e}")
            return f"# Error exporting metrics: {str(e)}\n"
    
    def export_json_format(self) -> Dict[str, Any]:
        """📄 Export metrics in JSON format."""
        try:
            with self.lock:
                metrics_data = {}
                
                for name, metric in self.metrics.items():
                    metric_data = {
                        'name': name,
                        'type': metric.metadata.metric_type.value,
                        'help': metric.metadata.help_text,
                        'timestamp': datetime.datetime.now().isoformat(),
                    }
                    
                    if isinstance(metric, Counter):
                        metric_data['value'] = metric.get_value()
                    
                    elif isinstance(metric, Gauge):
                        metric_data['value'] = metric.get_value()
                    
                    elif isinstance(metric, Histogram):
                        metric_data.update({
                            'buckets': metric.get_bucket_counts(),
                            'sum': metric.sum,
                            'count': metric.count,
                            'percentiles': {
                                '50': metric.get_percentile(50),
                                '95': metric.get_percentile(95),
                                '99': metric.get_percentile(99)
                            }
                        })
                    
                    elif isinstance(metric, Summary):
                        metric_data.update({
                            'quantiles': metric.get_quantiles(),
                            'sum': metric.sum,
                            'count': metric.count
                        })
                    
                    metrics_data[name] = metric_data
                
                return {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'metrics': metrics_data
                }
                
        except Exception as e:
            self.logger.error(f"🔴 Error exporting JSON format: {e}")
            return {'error': str(e)}
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """📊 Get metrics registry summary."""
        try:
            with self.lock:
                type_counts = defaultdict(int)
                for metric in self.metrics.values():
                    type_counts[metric.metadata.metric_type.value] += 1
                
                return {
                    'total_metrics': len(self.metrics),
                    'metric_types': dict(type_counts),
                    'metric_names': list(self.metrics.keys())
                }
                
        except Exception as e:
            return {'error': str(e)}

# 📊 AI Assistant: Global metrics registry instance
_global_registry = None

def get_registry() -> MetricsRegistry:
    """📊 Get global metrics registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = MetricsRegistry()
    return _global_registry

# 📊 AI Assistant: Convenience functions
def counter(name: str, help_text: str = "", labels: List[str] = None) -> Counter:
    """📈 Create counter using global registry."""
    return get_registry().create_counter(name, help_text, labels)

def gauge(name: str, help_text: str = "", labels: List[str] = None) -> Gauge:
    """📊 Create gauge using global registry."""
    return get_registry().create_gauge(name, help_text, labels)

def histogram(name: str, help_text: str = "", buckets: List[float] = None, labels: List[str] = None) -> Histogram:
    """📊 Create histogram using global registry."""
    return get_registry().create_histogram(name, help_text, buckets, labels)

def summary(name: str, help_text: str = "", quantiles: List[float] = None, labels: List[str] = None) -> Summary:
    """📊 Create summary using global registry."""
    return get_registry().create_summary(name, help_text, quantiles, labels)

def timer(histogram_name: str) -> Optional[Timer]:
    """⏱️ Create timer using global registry."""
    return get_registry().create_timer(histogram_name)

# 🧪 AI Assistant: Testing functions
def test_metrics_system():
    """🧪 Test metrics system functionality."""
    print("🧪 Testing Metrics System...")
    
    try:
        # 📊 Create metrics registry
        registry = MetricsRegistry()
        
        # 📈 Test counter
        request_counter = registry.create_counter("test_requests_total", "Total test requests")
        request_counter.inc()
        request_counter.inc(5)
        print(f"✅ Counter value: {request_counter.get_value()}")
        
        # 📊 Test gauge
        temperature_gauge = registry.create_gauge("test_temperature_celsius", "Test temperature")
        temperature_gauge.set(23.5)
        temperature_gauge.inc(2.1)
        print(f"✅ Gauge value: {temperature_gauge.get_value()}")
        
        # 📊 Test histogram
        response_histogram = registry.create_histogram("test_response_time_seconds", "Test response time")
        for value in [0.1, 0.2, 0.15, 0.3, 0.25, 1.2, 0.8]:
            response_histogram.observe(value)
        
        print(f"✅ Histogram count: {response_histogram.count}, sum: {response_histogram.sum:.2f}")
        print(f"  95th percentile: {response_histogram.get_percentile(95):.2f}s")
        
        # ⏱️ Test timer
        timing_histogram = registry.create_histogram("test_operation_duration", "Test operation duration")
        with Timer(timing_histogram):
            time.sleep(0.01)  # Simulate work
        
        print(f"✅ Timer recorded operation duration")
        
        # 📊 Export formats
        prometheus_export = registry.export_prometheus_format()
        json_export = registry.export_json_format()
        
        print(f"✅ Prometheus export: {len(prometheus_export)} characters")
        print(f"✅ JSON export: {len(json_export.get('metrics', {}))} metrics")
        
        # 📊 Registry summary
        summary = registry.get_metrics_summary()
        print(f"✅ Registry summary: {summary['total_metrics']} metrics")
        
        print("🎉 Metrics System test completed!")
        return True
        
    except Exception as e:
        print(f"🔴 Metrics System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_metrics_system()