#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Performance Monitor - G6 Platform v3.0
Advanced performance monitoring with metrics collection and analysis.

Restructured from: performance_monitor.py, metrics_system.py
Features:
- Real-time performance metrics collection
- Resource usage monitoring and trending
- Latency and throughput analysis
- Performance benchmarking and SLA tracking
- Alert generation for performance degradation
- Historical performance analysis
"""

import time
import logging
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    value: Union[float, int]
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'metadata': self.metadata
        }

@dataclass
class PerformanceSnapshot:
    """Performance snapshot at a point in time."""
    timestamp: datetime
    
    # System metrics
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_bytes_sent: int
    network_bytes_recv: int
    
    # Application metrics
    active_threads: int
    open_connections: int
    cache_hit_rate: float
    request_rate: float
    error_rate: float
    average_response_time: float
    
    # Custom metrics
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'system': {
                'cpu_percent': self.cpu_percent,
                'memory_percent': self.memory_percent,
                'memory_used_mb': self.memory_used_mb,
                'disk_io_read_mb': self.disk_io_read_mb,
                'disk_io_write_mb': self.disk_io_write_mb,
                'network_bytes_sent': self.network_bytes_sent,
                'network_bytes_recv': self.network_bytes_recv
            },
            'application': {
                'active_threads': self.active_threads,
                'open_connections': self.open_connections,
                'cache_hit_rate': self.cache_hit_rate,
                'request_rate': self.request_rate,
                'error_rate': self.error_rate,
                'average_response_time': self.average_response_time
            },
            'custom': self.custom_metrics
        }

@dataclass
class PerformanceAlert:
    """Performance alert information."""
    id: str
    timestamp: datetime
    metric_name: str
    threshold_type: str  # above, below, change
    threshold_value: float
    current_value: float
    severity: str  # info, warning, error, critical
    message: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class PerformanceThreshold:
    """Performance threshold configuration."""
    
    def __init__(self,
                 metric_name: str,
                 warning_above: Optional[float] = None,
                 critical_above: Optional[float] = None,
                 warning_below: Optional[float] = None,
                 critical_below: Optional[float] = None,
                 change_warning_percent: Optional[float] = None,
                 change_critical_percent: Optional[float] = None):
        """
        Initialize performance threshold.
        
        Args:
            metric_name: Name of the metric to monitor
            warning_above: Warning threshold for values above
            critical_above: Critical threshold for values above
            warning_below: Warning threshold for values below
            critical_below: Critical threshold for values below
            change_warning_percent: Warning threshold for percentage change
            change_critical_percent: Critical threshold for percentage change
        """
        self.metric_name = metric_name
        self.warning_above = warning_above
        self.critical_above = critical_above
        self.warning_below = warning_below
        self.critical_below = critical_below
        self.change_warning_percent = change_warning_percent
        self.change_critical_percent = change_critical_percent
        
        self.last_value: Optional[float] = None
        self.last_check: Optional[datetime] = None

class PerformanceMonitor:
    """
    📊 Advanced performance monitoring system.
    
    Provides comprehensive performance monitoring with real-time metrics
    collection, threshold monitoring, and performance analysis.
    """
    
    def __init__(self,
                 collection_interval: float = 30.0,
                 retention_period: int = 86400,  # 24 hours in seconds
                 enable_system_monitoring: bool = True,
                 enable_threshold_monitoring: bool = True):
        """
        Initialize performance monitor.
        
        Args:
            collection_interval: Metrics collection interval in seconds
            retention_period: Data retention period in seconds
            enable_system_monitoring: Enable system resource monitoring
            enable_threshold_monitoring: Enable threshold-based alerting
        """
        self.collection_interval = collection_interval
        self.retention_period = retention_period
        self.enable_system_monitoring = enable_system_monitoring
        self.enable_threshold_monitoring = enable_threshold_monitoring
        
        # Metrics storage
        self._metrics: deque = deque(maxlen=10000)
        self._snapshots: deque = deque(maxlen=2880)  # 24h at 30s intervals
        self._custom_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Thresholds and alerts
        self._thresholds: Dict[str, PerformanceThreshold] = {}
        self._alerts: Dict[str, PerformanceAlert] = {}
        self._alert_handlers: List[Callable[[PerformanceAlert], None]] = []
        
        # Monitoring state
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self._lock = threading.RLock()
        
        # Performance counters
        self._request_counter = 0
        self._error_counter = 0
        self._response_times: deque = deque(maxlen=1000)
        self._last_network_stats = None
        self._last_disk_stats = None
        
        # Initialize default thresholds
        self._setup_default_thresholds()
        
        logger.info("📊 Performance monitor initialized")
        logger.info(f"⚙️ Collection interval: {collection_interval}s, Retention: {retention_period}s")
    
    def _setup_default_thresholds(self):
        """Setup default performance thresholds."""
        # CPU thresholds
        self.add_threshold(
            metric_name="cpu_percent",
            warning_above=70.0,
            critical_above=90.0
        )
        
        # Memory thresholds
        self.add_threshold(
            metric_name="memory_percent",
            warning_above=80.0,
            critical_above=95.0
        )
        
        # Response time thresholds
        self.add_threshold(
            metric_name="average_response_time",
            warning_above=1000.0,  # 1 second
            critical_above=3000.0  # 3 seconds
        )
        
        # Error rate thresholds
        self.add_threshold(
            metric_name="error_rate",
            warning_above=5.0,   # 5%
            critical_above=10.0  # 10%
        )
    
    def start(self):
        """Start performance monitoring."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("⚠️ Performance monitor already running")
            return
        
        self._stop_monitoring.clear()
        
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="PerformanceMonitor"
        )
        self._monitor_thread.start()
        
        logger.info("🚀 Performance monitoring started")
    
    def stop(self, timeout: float = 10.0):
        """Stop performance monitoring."""
        logger.info("🛑 Stopping performance monitoring...")
        
        self._stop_monitoring.set()
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=timeout)
        
        logger.info("✅ Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        logger.info("🔄 Performance monitoring loop started")
        
        while not self._stop_monitoring.is_set():
            try:
                # Collect performance snapshot
                snapshot = self._collect_performance_snapshot()
                
                # Store snapshot
                with self._lock:
                    self._snapshots.append(snapshot)
                
                # Check thresholds
                if self.enable_threshold_monitoring:
                    self._check_thresholds(snapshot)
                
                # Cleanup old data
                self._cleanup_old_data()
                
                # Wait for next collection
                self._stop_monitoring.wait(self.collection_interval)
                
            except Exception as e:
                logger.error(f"🔴 Performance monitoring error: {e}")
                self._stop_monitoring.wait(60)  # Wait longer on error
        
        logger.info("🔄 Performance monitoring loop stopped")
    
    def _collect_performance_snapshot(self) -> PerformanceSnapshot:
        """Collect current performance snapshot."""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Disk I/O
        disk_stats = psutil.disk_io_counters()
        disk_read_mb = 0.0
        disk_write_mb = 0.0
        
        if self._last_disk_stats and disk_stats:
            read_bytes = disk_stats.read_bytes - self._last_disk_stats.read_bytes
            write_bytes = disk_stats.write_bytes - self._last_disk_stats.write_bytes
            disk_read_mb = read_bytes / (1024 * 1024)
            disk_write_mb = write_bytes / (1024 * 1024)
        
        self._last_disk_stats = disk_stats
        
        # Network I/O
        network_stats = psutil.net_io_counters()
        network_sent = network_stats.bytes_sent if network_stats else 0
        network_recv = network_stats.bytes_recv if network_stats else 0
        
        # Application metrics
        active_threads = threading.active_count()
        
        # Calculate rates
        with self._lock:
            request_rate = self._calculate_request_rate()
            error_rate = self._calculate_error_rate()
            avg_response_time = self._calculate_average_response_time()
        
        return PerformanceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_bytes_sent=network_sent,
            network_bytes_recv=network_recv,
            active_threads=active_threads,
            open_connections=0,  # Would need specific implementation
            cache_hit_rate=0.0,  # Would need specific implementation
            request_rate=request_rate,
            error_rate=error_rate,
            average_response_time=avg_response_time
        )
    
    def _calculate_request_rate(self) -> float:
        """Calculate request rate per second."""
        # This would need integration with request tracking
        return 0.0
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate percentage."""
        if self._request_counter == 0:
            return 0.0
        return (self._error_counter / self._request_counter) * 100
    
    def _calculate_average_response_time(self) -> float:
        """Calculate average response time in milliseconds."""
        if not self._response_times:
            return 0.0
        return statistics.mean(self._response_times)
    
    def _check_thresholds(self, snapshot: PerformanceSnapshot):
        """Check performance thresholds and generate alerts."""
        snapshot_dict = snapshot.to_dict()
        
        # Flatten the snapshot for threshold checking
        flat_metrics = {}
        flat_metrics.update(snapshot_dict['system'])
        flat_metrics.update(snapshot_dict['application'])
        flat_metrics.update(snapshot_dict['custom'])
        
        for metric_name, value in flat_metrics.items():
            if metric_name in self._thresholds:
                threshold = self._thresholds[metric_name]
                alerts = self._evaluate_threshold(threshold, value, snapshot.timestamp)
                
                for alert in alerts:
                    self._handle_alert(alert)
    
    def _evaluate_threshold(self,
                          threshold: PerformanceThreshold,
                          current_value: float,
                          timestamp: datetime) -> List[PerformanceAlert]:
        """Evaluate threshold against current value."""
        alerts = []
        
        # Check absolute thresholds
        if threshold.critical_above and current_value > threshold.critical_above:
            alert = PerformanceAlert(
                id=f"{threshold.metric_name}_critical_{int(time.time())}",
                timestamp=timestamp,
                metric_name=threshold.metric_name,
                threshold_type="above",
                threshold_value=threshold.critical_above,
                current_value=current_value,
                severity="critical",
                message=f"{threshold.metric_name} is critically high: {current_value:.2f} > {threshold.critical_above:.2f}"
            )
            alerts.append(alert)
            
        elif threshold.warning_above and current_value > threshold.warning_above:
            alert = PerformanceAlert(
                id=f"{threshold.metric_name}_warning_{int(time.time())}",
                timestamp=timestamp,
                metric_name=threshold.metric_name,
                threshold_type="above",
                threshold_value=threshold.warning_above,
                current_value=current_value,
                severity="warning",
                message=f"{threshold.metric_name} is high: {current_value:.2f} > {threshold.warning_above:.2f}"
            )
            alerts.append(alert)
        
        if threshold.critical_below and current_value < threshold.critical_below:
            alert = PerformanceAlert(
                id=f"{threshold.metric_name}_critical_{int(time.time())}",
                timestamp=timestamp,
                metric_name=threshold.metric_name,
                threshold_type="below",
                threshold_value=threshold.critical_below,
                current_value=current_value,
                severity="critical",
                message=f"{threshold.metric_name} is critically low: {current_value:.2f} < {threshold.critical_below:.2f}"
            )
            alerts.append(alert)
            
        elif threshold.warning_below and current_value < threshold.warning_below:
            alert = PerformanceAlert(
                id=f"{threshold.metric_name}_warning_{int(time.time())}",
                timestamp=timestamp,
                metric_name=threshold.metric_name,
                threshold_type="below",
                threshold_value=threshold.warning_below,
                current_value=current_value,
                severity="warning",
                message=f"{threshold.metric_name} is low: {current_value:.2f} < {threshold.warning_below:.2f}"
            )
            alerts.append(alert)
        
        # Check change thresholds
        if threshold.last_value is not None:
            change_percent = abs((current_value - threshold.last_value) / threshold.last_value) * 100
            
            if threshold.change_critical_percent and change_percent > threshold.change_critical_percent:
                alert = PerformanceAlert(
                    id=f"{threshold.metric_name}_change_critical_{int(time.time())}",
                    timestamp=timestamp,
                    metric_name=threshold.metric_name,
                    threshold_type="change",
                    threshold_value=threshold.change_critical_percent,
                    current_value=change_percent,
                    severity="critical",
                    message=f"{threshold.metric_name} changed critically: {change_percent:.1f}% > {threshold.change_critical_percent:.1f}%"
                )
                alerts.append(alert)
                
            elif threshold.change_warning_percent and change_percent > threshold.change_warning_percent:
                alert = PerformanceAlert(
                    id=f"{threshold.metric_name}_change_warning_{int(time.time())}",
                    timestamp=timestamp,
                    metric_name=threshold.metric_name,
                    threshold_type="change",
                    threshold_value=threshold.change_warning_percent,
                    current_value=change_percent,
                    severity="warning",
                    message=f"{threshold.metric_name} changed significantly: {change_percent:.1f}% > {threshold.change_warning_percent:.1f}%"
                )
                alerts.append(alert)
        
        # Update threshold state
        threshold.last_value = current_value
        threshold.last_check = timestamp
        
        return alerts
    
    def _handle_alert(self, alert: PerformanceAlert):
        """Handle performance alert."""
        # Store alert
        with self._lock:
            self._alerts[alert.id] = alert
        
        # Notify handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"🔴 Alert handler error: {e}")
        
        logger.warning(f"🚨 Performance alert: {alert.message}")
    
    def _cleanup_old_data(self):
        """Clean up old performance data."""
        cutoff_time = datetime.now() - timedelta(seconds=self.retention_period)
        
        with self._lock:
            # Clean snapshots
            while (self._snapshots and 
                   self._snapshots[0].timestamp < cutoff_time):
                self._snapshots.popleft()
            
            # Clean custom metrics
            for metric_name, values in self._custom_metrics.items():
                while values and values[0].timestamp < cutoff_time:
                    values.popleft()
    
    # Public API methods
    
    def add_threshold(self,
                     metric_name: str,
                     warning_above: Optional[float] = None,
                     critical_above: Optional[float] = None,
                     warning_below: Optional[float] = None,
                     critical_below: Optional[float] = None,
                     change_warning_percent: Optional[float] = None,
                     change_critical_percent: Optional[float] = None) -> bool:
        """Add performance threshold."""
        try:
            threshold = PerformanceThreshold(
                metric_name=metric_name,
                warning_above=warning_above,
                critical_above=critical_above,
                warning_below=warning_below,
                critical_below=critical_below,
                change_warning_percent=change_warning_percent,
                change_critical_percent=change_critical_percent
            )
            
            with self._lock:
                self._thresholds[metric_name] = threshold
            
            logger.info(f"✅ Performance threshold added for {metric_name}")
            return True
            
        except Exception as e:
            logger.error(f"🔴 Failed to add threshold for {metric_name}: {e}")
            return False
    
    def remove_threshold(self, metric_name: str) -> bool:
        """Remove performance threshold."""
        with self._lock:
            if metric_name in self._thresholds:
                del self._thresholds[metric_name]
                logger.info(f"🗑️ Performance threshold removed for {metric_name}")
                return True
            return False
    
    def record_metric(self,
                     name: str,
                     value: Union[float, int],
                     unit: str = "",
                     tags: Dict[str, str] = None,
                     metadata: Dict[str, Any] = None):
        """Record custom performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=float(value),
            unit=unit,
            timestamp=datetime.now(),
            tags=tags or {},
            metadata=metadata or {}
        )
        
        with self._lock:
            self._metrics.append(metric)
            self._custom_metrics[name].append(metric)
    
    def record_request(self, response_time_ms: float, success: bool = True):
        """Record request performance."""
        with self._lock:
            self._request_counter += 1
            if not success:
                self._error_counter += 1
            
            self._response_times.append(response_time_ms)
    
    def get_current_performance(self) -> Dict[str, Any]:
        """Get current performance snapshot."""
        with self._lock:
            if self._snapshots:
                latest_snapshot = self._snapshots[-1]
                return latest_snapshot.to_dict()
            return {}
    
    def get_performance_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get performance history."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            history = []
            for snapshot in self._snapshots:
                if snapshot.timestamp >= cutoff_time:
                    history.append(snapshot.to_dict())
            
            return sorted(history, key=lambda x: x['timestamp'])
    
    def get_metric_statistics(self, metric_name: str, hours: int = 1) -> Dict[str, Any]:
        """Get statistics for a specific metric."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            values = []
            
            # Check custom metrics
            if metric_name in self._custom_metrics:
                for metric in self._custom_metrics[metric_name]:
                    if metric.timestamp >= cutoff_time:
                        values.append(metric.value)
            
            # Check snapshot metrics
            for snapshot in self._snapshots:
                if snapshot.timestamp >= cutoff_time:
                    snapshot_dict = snapshot.to_dict()
                    if metric_name in snapshot_dict.get('system', {}):
                        values.append(snapshot_dict['system'][metric_name])
                    elif metric_name in snapshot_dict.get('application', {}):
                        values.append(snapshot_dict['application'][metric_name])
                    elif metric_name in snapshot_dict.get('custom', {}):
                        values.append(snapshot_dict['custom'][metric_name])
            
            if not values:
                return {'error': f'No data found for metric {metric_name}'}
            
            return {
                'metric_name': metric_name,
                'period_hours': hours,
                'sample_count': len(values),
                'min_value': min(values),
                'max_value': max(values),
                'average_value': statistics.mean(values),
                'median_value': statistics.median(values),
                'std_deviation': statistics.stdev(values) if len(values) > 1 else 0.0
            }
    
    def get_alerts(self, unresolved_only: bool = True) -> List[Dict[str, Any]]:
        """Get performance alerts."""
        with self._lock:
            alerts = []
            for alert in self._alerts.values():
                if unresolved_only and alert.resolved:
                    continue
                
                alert_dict = {
                    'id': alert.id,
                    'timestamp': alert.timestamp.isoformat(),
                    'metric_name': alert.metric_name,
                    'threshold_type': alert.threshold_type,
                    'threshold_value': alert.threshold_value,
                    'current_value': alert.current_value,
                    'severity': alert.severity,
                    'message': alert.message,
                    'resolved': alert.resolved
                }
                
                if alert.resolved_at:
                    alert_dict['resolved_at'] = alert.resolved_at.isoformat()
                
                alerts.append(alert_dict)
            
            return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve performance alert."""
        with self._lock:
            if alert_id in self._alerts:
                alert = self._alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"✅ Performance alert resolved: {alert_id}")
                return True
            return False
    
    def add_alert_handler(self, handler: Callable[[PerformanceAlert], None]):
        """Add alert notification handler."""
        self._alert_handlers.append(handler)
        logger.info("✅ Performance alert handler added")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        # CPU information
        cpu_info = {
            'logical_cores': psutil.cpu_count(logical=True),
            'physical_cores': psutil.cpu_count(logical=False),
            'current_freq': psutil.cpu_freq().current if psutil.cpu_freq() else None,
            'max_freq': psutil.cpu_freq().max if psutil.cpu_freq() else None
        }
        
        # Memory information
        memory = psutil.virtual_memory()
        memory_info = {
            'total_gb': memory.total / (1024 ** 3),
            'available_gb': memory.available / (1024 ** 3),
            'used_gb': memory.used / (1024 ** 3),
            'percent_used': memory.percent
        }
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_info = {
            'total_gb': disk.total / (1024 ** 3),
            'used_gb': disk.used / (1024 ** 3),
            'free_gb': disk.free / (1024 ** 3),
            'percent_used': (disk.used / disk.total) * 100
        }
        
        return {
            'cpu': cpu_info,
            'memory': memory_info,
            'disk': disk_info,
            'monitoring_active': not self._stop_monitoring.is_set(),
            'retention_hours': self.retention_period / 3600,
            'collection_interval': self.collection_interval
        }