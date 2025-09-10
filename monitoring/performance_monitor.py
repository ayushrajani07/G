#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Monitor - G6.1 Platform
Comprehensive performance monitoring and profiling

Features:
- Real-time performance monitoring
- Memory usage tracking
- CPU profiling and analysis
- I/O performance monitoring
- Database query performance
- Network latency tracking
- Bottleneck identification
"""

import os
import sys
import time
import psutil
import threading
import traceback
import functools
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import json

@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class ProfileResult:
    """Function profiling result."""
    function_name: str
    execution_time: float
    call_count: int
    avg_time: float
    max_time: float
    min_time: float
    total_time: float
    memory_delta: int
    cpu_usage: float

@dataclass
class SystemSnapshot:
    """System performance snapshot."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    open_files: int
    threads_count: int
    load_average: List[float] = field(default_factory=list)

class FunctionProfiler:
    """Decorator and context manager for function profiling."""
    
    def __init__(self, monitor: 'PerformanceMonitor'):
        """Initialize profiler.
        
        Args:
            monitor: PerformanceMonitor instance
        """
        self.monitor = monitor
        self.results: Dict[str, ProfileResult] = {}
        
    def profile(self, func_name: str = None):
        """Decorator for profiling functions.
        
        Args:
            func_name: Optional custom function name
            
        Returns:
            Decorated function
        """
        def decorator(func):
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self._profile_execution(name, func, *args, **kwargs)
            
            return wrapper
        return decorator
    
    def _profile_execution(self, name: str, func: Callable, *args, **kwargs):
        """Profile function execution.
        
        Args:
            name: Function name
            func: Function to profile
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        # Get initial state
        start_time = time.perf_counter()
        process = psutil.Process()
        start_memory = process.memory_info().rss
        start_cpu = process.cpu_percent()
        
        try:
            # Execute function
            result = func(*args, **kwargs)
            
            # Calculate metrics
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            end_memory = process.memory_info().rss
            memory_delta = end_memory - start_memory
            
            # Update profiling results
            self._update_profile_result(name, execution_time, memory_delta, start_cpu)
            
            # Send metrics to monitor
            self.monitor.add_metric(
                f"function_execution_time.{name}",
                execution_time * 1000,  # Convert to milliseconds
                "ms",
                "performance",
                {"function": name}
            )
            
            return result
            
        except Exception as e:
            # Record error metrics
            self.monitor.add_metric(
                f"function_errors.{name}",
                1,
                "count",
                "errors",
                {"function": name, "error": str(e)}
            )
            raise
    
    def _update_profile_result(self, name: str, execution_time: float, memory_delta: int, cpu_usage: float):
        """Update profiling results for a function.
        
        Args:
            name: Function name
            execution_time: Execution time in seconds
            memory_delta: Memory usage delta in bytes
            cpu_usage: CPU usage percentage
        """
        if name not in self.results:
            self.results[name] = ProfileResult(
                function_name=name,
                execution_time=execution_time,
                call_count=1,
                avg_time=execution_time,
                max_time=execution_time,
                min_time=execution_time,
                total_time=execution_time,
                memory_delta=memory_delta,
                cpu_usage=cpu_usage
            )
        else:
            result = self.results[name]
            result.call_count += 1
            result.total_time += execution_time
            result.avg_time = result.total_time / result.call_count
            result.max_time = max(result.max_time, execution_time)
            result.min_time = min(result.min_time, execution_time)
            result.execution_time = execution_time  # Most recent
            result.memory_delta = memory_delta  # Most recent
            result.cpu_usage = cpu_usage  # Most recent

class MemoryTracker:
    """Memory usage tracking and analysis."""
    
    def __init__(self):
        """Initialize memory tracker."""
        self.snapshots: List[Dict] = []
        self.threshold_mb = 100  # Memory threshold for alerts
        
    def take_snapshot(self) -> Dict[str, Any]:
        """Take memory usage snapshot.
        
        Returns:
            Dictionary with memory metrics
        """
        process = psutil.Process()
        memory_info = process.memory_info()
        
        snapshot = {
            'timestamp': datetime.now(),
            'rss': memory_info.rss,  # Resident Set Size
            'vms': memory_info.vms,  # Virtual Memory Size
            'percent': process.memory_percent(),
            'available': psutil.virtual_memory().available,
            'used': psutil.virtual_memory().used,
            'total': psutil.virtual_memory().total
        }
        
        self.snapshots.append(snapshot)
        
        # Keep only recent snapshots
        if len(self.snapshots) > 1000:
            self.snapshots = self.snapshots[-500:]
        
        return snapshot
    
    def detect_memory_leaks(self, window_minutes: int = 30) -> Dict[str, Any]:
        """Detect potential memory leaks.
        
        Args:
            window_minutes: Time window for analysis
            
        Returns:
            Dictionary with leak analysis results
        """
        if len(self.snapshots) < 10:
            return {'status': 'insufficient_data'}
        
        # Filter snapshots to time window
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_snapshots = [
            s for s in self.snapshots
            if s['timestamp'] >= cutoff_time
        ]
        
        if len(recent_snapshots) < 5:
            return {'status': 'insufficient_data'}
        
        # Analyze memory trend
        memory_values = [s['rss'] / 1024 / 1024 for s in recent_snapshots]  # MB
        
        # Linear regression to detect trend
        n = len(memory_values)
        x_values = list(range(n))
        
        # Calculate slope (trend)
        slope = (n * sum(x * y for x, y in zip(x_values, memory_values)) - 
                sum(x_values) * sum(memory_values)) / (n * sum(x * x for x in x_values) - sum(x_values) ** 2)
        
        # Calculate correlation coefficient
        mean_x = statistics.mean(x_values)
        mean_y = statistics.mean(memory_values)
        
        correlation = (sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, memory_values)) / 
                      (sum((x - mean_x) ** 2 for x in x_values) * sum((y - mean_y) ** 2 for y in memory_values)) ** 0.5)
        
        # Determine leak status
        leak_detected = slope > 1.0 and correlation > 0.7  # 1MB/measurement increase with strong correlation
        
        return {
            'status': 'leak_detected' if leak_detected else 'normal',
            'slope_mb_per_measurement': slope,
            'correlation': correlation,
            'current_memory_mb': memory_values[-1],
            'memory_increase_mb': memory_values[-1] - memory_values[0],
            'window_minutes': window_minutes
        }

class PerformanceMonitor:
    """Main performance monitoring class."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize performance monitor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.alerts: List[Dict] = []
        
        # Components
        self.profiler = FunctionProfiler(self)
        self.memory_tracker = MemoryTracker()
        
        # Monitoring state
        self.monitoring = False
        self.monitor_thread = None
        
        # System monitoring
        self.system_snapshots: deque = deque(maxlen=1000)
        
        # Performance thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'response_time_ms': 1000.0,
            'error_rate_percent': 5.0
        }
        
        # Update with config thresholds
        self.thresholds.update(config.get('thresholds', {}))
    
    def start_monitoring(self, interval: int = 5):
        """Start continuous performance monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.monitoring:
            return
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    # Take system snapshot
                    snapshot = self._take_system_snapshot()
                    self.system_snapshots.append(snapshot)
                    
                    # Take memory snapshot
                    memory_snapshot = self.memory_tracker.take_snapshot()
                    
                    # Add metrics
                    self.add_metric("cpu_percent", snapshot.cpu_percent, "%", "system")
                    self.add_metric("memory_percent", snapshot.memory_percent, "%", "system")
                    self.add_metric("disk_usage_percent", snapshot.disk_usage_percent, "%", "system")
                    
                    # Check for alerts
                    self._check_performance_alerts(snapshot)
                    
                    # Check for memory leaks
                    if len(self.memory_tracker.snapshots) % 12 == 0:  # Every 12 measurements
                        leak_analysis = self.memory_tracker.detect_memory_leaks()
                        if leak_analysis.get('status') == 'leak_detected':
                            self._add_alert("memory_leak", "Potential memory leak detected", leak_analysis)
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    print(f"Error in performance monitoring: {e}")
                    time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _take_system_snapshot(self) -> SystemSnapshot:
        """Take system performance snapshot.
        
        Returns:
            SystemSnapshot object
        """
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        
        # Network I/O
        network = psutil.net_io_counters()
        
        # Process info
        process = psutil.Process()
        
        # Load average (Unix only)
        load_avg = []
        if hasattr(os, 'getloadavg'):
            try:
                load_avg = list(os.getloadavg())
            except:
                pass
        
        return SystemSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=disk_usage_percent,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            open_files=len(process.open_files()),
            threads_count=process.num_threads(),
            load_average=load_avg
        )
    
    def add_metric(self, name: str, value: float, unit: str, category: str, tags: Dict[str, str] = None):
        """Add performance metric.
        
        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement
            category: Metric category
            tags: Optional tags
        """
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            category=category,
            tags=tags or {}
        )
        
        self.metrics[name].append(metric)
    
    def _check_performance_alerts(self, snapshot: SystemSnapshot):
        """Check for performance alerts.
        
        Args:
            snapshot: System snapshot to check
        """
        # CPU alert
        if snapshot.cpu_percent > self.thresholds['cpu_percent']:
            self._add_alert(
                "high_cpu",
                f"High CPU usage: {snapshot.cpu_percent:.1f}%",
                {"cpu_percent": snapshot.cpu_percent}
            )
        
        # Memory alert
        if snapshot.memory_percent > self.thresholds['memory_percent']:
            self._add_alert(
                "high_memory",
                f"High memory usage: {snapshot.memory_percent:.1f}%",
                {"memory_percent": snapshot.memory_percent}
            )
        
        # Disk alert
        if snapshot.disk_usage_percent > self.thresholds['disk_usage_percent']:
            self._add_alert(
                "high_disk",
                f"High disk usage: {snapshot.disk_usage_percent:.1f}%",
                {"disk_usage_percent": snapshot.disk_usage_percent}
            )
    
    def _add_alert(self, alert_type: str, message: str, data: Dict[str, Any]):
        """Add performance alert.
        
        Args:
            alert_type: Type of alert
            message: Alert message
            data: Additional alert data
        """
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now(),
            'data': data
        }
        
        self.alerts.append(alert)
        
        # Keep only recent alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-50:]
    
    def profile_function(self, func_name: str = None):
        """Decorator for profiling functions.
        
        Args:
            func_name: Optional custom function name
            
        Returns:
            Profiling decorator
        """
        return self.profiler.profile(func_name)
    
    def get_performance_summary(self, minutes: int = 30) -> Dict[str, Any]:
        """Get performance summary for specified time period.
        
        Args:
            minutes: Time period in minutes
            
        Returns:
            Dictionary with performance summary
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        summary = {
            'time_period_minutes': minutes,
            'system_metrics': {},
            'function_profiles': {},
            'alerts': [],
            'memory_analysis': {}
        }
        
        # System metrics summary
        recent_snapshots = [
            s for s in self.system_snapshots
            if s.timestamp >= cutoff_time
        ]
        
        if recent_snapshots:
            cpu_values = [s.cpu_percent for s in recent_snapshots]
            memory_values = [s.memory_percent for s in recent_snapshots]
            disk_values = [s.disk_usage_percent for s in recent_snapshots]
            
            summary['system_metrics'] = {
                'cpu': {
                    'avg': statistics.mean(cpu_values),
                    'max': max(cpu_values),
                    'min': min(cpu_values),
                    'current': cpu_values[-1] if cpu_values else 0
                },
                'memory': {
                    'avg': statistics.mean(memory_values),
                    'max': max(memory_values),
                    'min': min(memory_values),
                    'current': memory_values[-1] if memory_values else 0
                },
                'disk': {
                    'avg': statistics.mean(disk_values),
                    'max': max(disk_values),
                    'min': min(disk_values),
                    'current': disk_values[-1] if disk_values else 0
                }
            }
        
        # Function profiles
        summary['function_profiles'] = {
            name: {
                'call_count': result.call_count,
                'avg_time_ms': result.avg_time * 1000,
                'max_time_ms': result.max_time * 1000,
                'total_time_ms': result.total_time * 1000
            }
            for name, result in self.profiler.results.items()
        }
        
        # Recent alerts
        recent_alerts = [
            alert for alert in self.alerts
            if alert['timestamp'] >= cutoff_time
        ]
        summary['alerts'] = recent_alerts
        
        # Memory analysis
        summary['memory_analysis'] = self.memory_tracker.detect_memory_leaks(minutes)
        
        return summary
    
    def get_bottlenecks(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks.
        
        Args:
            top_n: Number of top bottlenecks to return
            
        Returns:
            List of bottleneck analyses
        """
        bottlenecks = []
        
        # Function execution time bottlenecks
        for name, result in self.profiler.results.items():
            if result.call_count > 0:
                bottlenecks.append({
                    'type': 'function_execution',
                    'name': name,
                    'severity': result.avg_time * result.call_count,  # Total impact
                    'avg_time_ms': result.avg_time * 1000,
                    'call_count': result.call_count,
                    'total_time_ms': result.total_time * 1000
                })
        
        # System resource bottlenecks
        if self.system_snapshots:
            latest = self.system_snapshots[-1]
            
            if latest.cpu_percent > 70:
                bottlenecks.append({
                    'type': 'system_cpu',
                    'name': 'CPU Usage',
                    'severity': latest.cpu_percent,
                    'current_value': latest.cpu_percent,
                    'threshold': self.thresholds['cpu_percent']
                })
            
            if latest.memory_percent > 70:
                bottlenecks.append({
                    'type': 'system_memory',
                    'name': 'Memory Usage',
                    'severity': latest.memory_percent,
                    'current_value': latest.memory_percent,
                    'threshold': self.thresholds['memory_percent']
                })
        
        # Sort by severity and return top N
        bottlenecks.sort(key=lambda x: x['severity'], reverse=True)
        return bottlenecks[:top_n]
    
    def export_performance_data(self, format_type: str = 'json') -> str:
        """Export performance data.
        
        Args:
            format_type: Export format ('json', 'csv')
            
        Returns:
            Formatted performance data
        """
        if format_type == 'json':
            data = {
                'summary': self.get_performance_summary(),
                'bottlenecks': self.get_bottlenecks(),
                'alerts': self.alerts[-50:],  # Recent alerts
                'system_snapshots': [
                    {
                        'timestamp': s.timestamp.isoformat(),
                        'cpu_percent': s.cpu_percent,
                        'memory_percent': s.memory_percent,
                        'disk_usage_percent': s.disk_usage_percent
                    }
                    for s in list(self.system_snapshots)[-100:]  # Recent snapshots
                ]
            }
            return json.dumps(data, indent=2)
        
        elif format_type == 'csv':
            lines = ['timestamp,metric_name,value,unit,category']
            
            for metric_name, metric_list in self.metrics.items():
                for metric in metric_list:
                    lines.append(
                        f"{metric.timestamp.isoformat()},{metric_name},{metric.value},{metric.unit},{metric.category}"
                    )
            
            return '\n'.join(lines)
        
        return ""

# Context manager for performance monitoring
class PerformanceContext:
    """Context manager for monitoring code blocks."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        """Initialize performance context.
        
        Args:
            monitor: PerformanceMonitor instance
            operation_name: Name of the operation to monitor
        """
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
        self.start_memory = None
    
    def __enter__(self):
        """Enter performance monitoring context."""
        self.start_time = time.perf_counter()
        process = psutil.Process()
        self.start_memory = process.memory_info().rss
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit performance monitoring context."""
        end_time = time.perf_counter()
        execution_time = end_time - self.start_time
        
        process = psutil.Process()
        end_memory = process.memory_info().rss
        memory_delta = end_memory - self.start_memory
        
        # Add metrics
        self.monitor.add_metric(
            f"operation_time.{self.operation_name}",
            execution_time * 1000,  # milliseconds
            "ms",
            "operations"
        )
        
        self.monitor.add_metric(
            f"operation_memory.{self.operation_name}",
            memory_delta / 1024 / 1024,  # MB
            "MB",
            "operations"
        )

# Example usage
if __name__ == "__main__":
    # Initialize monitor
    monitor = PerformanceMonitor()
    
    # Start monitoring
    monitor.start_monitoring(interval=2)
    
    # Example profiled function
    @monitor.profile_function("example_calculation")
    def example_function():
        time.sleep(0.1)  # Simulate work
        return sum(range(10000))
    
    # Example usage with context manager
    def example_operations():
        with PerformanceContext(monitor, "data_processing"):
            time.sleep(0.05)  # Simulate processing
            
        # Call profiled function
        result = example_function()
        return result
    
    try:
        print("Performance Monitor Started...")
        print("Running example operations...")
        
        # Run some operations
        for i in range(10):
            example_operations()
            time.sleep(1)
        
        # Get performance summary
        summary = monitor.get_performance_summary(minutes=5)
        print("\nPerformance Summary:")
        print(json.dumps(summary, indent=2, default=str))
        
        # Get bottlenecks
        bottlenecks = monitor.get_bottlenecks()
        print("\nTop Bottlenecks:")
        for bottleneck in bottlenecks:
            print(f"- {bottleneck['name']}: {bottleneck['severity']:.2f}")
        
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        monitor.stop_monitoring()
        print("Monitor stopped.")