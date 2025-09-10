#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metrics Dashboard - G6.1 Platform
Real-time metrics visualization and monitoring dashboard

Features:
- Real-time metrics display with auto-refresh
- Customizable dashboard layout
- Interactive charts and graphs
- Performance monitoring
- Alert notifications
- Historical data visualization
"""

import os
import sys
import time
import json
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque, defaultdict

# Try to import Rich for enhanced terminal UI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
    from rich.align import Align
    from rich import box
    from rich.columns import Columns
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich not available, using basic terminal output")

@dataclass
class MetricPoint:
    """Individual metric data point."""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class MetricSeries:
    """Time series of metric points."""
    name: str
    description: str
    unit: str
    data_points: deque = field(default_factory=lambda: deque(maxlen=1000))
    alerts: List[Dict] = field(default_factory=list)

@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    refresh_interval: int = 5  # seconds
    max_data_points: int = 1000
    alert_thresholds: Dict[str, Dict] = field(default_factory=dict)
    display_mode: str = 'rich'  # 'rich', 'basic', 'web'
    auto_scroll: bool = True
    show_sparklines: bool = True

class MetricCollector:
    """Collects metrics from various sources."""
    
    def __init__(self):
        """Initialize metric collector."""
        self.metrics: Dict[str, MetricSeries] = {}
        self.collectors: List[Callable] = []
        self.running = False
        self.collection_thread = None
    
    def register_metric(self, name: str, description: str, unit: str = "") -> MetricSeries:
        """Register a new metric series.
        
        Args:
            name: Metric name
            description: Metric description
            unit: Unit of measurement
            
        Returns:
            MetricSeries object
        """
        metric = MetricSeries(name=name, description=description, unit=unit)
        self.metrics[name] = metric
        return metric
    
    def add_metric_point(self, name: str, value: float, tags: Dict[str, str] = None):
        """Add a data point to a metric series.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for the metric point
        """
        if name not in self.metrics:
            self.register_metric(name, name.title(), "")
        
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            tags=tags or {}
        )
        
        self.metrics[name].data_points.append(point)
    
    def register_collector(self, collector_func: Callable):
        """Register a metric collector function.
        
        Args:
            collector_func: Function that collects metrics
        """
        self.collectors.append(collector_func)
    
    def start_collection(self, interval: int = 5):
        """Start automatic metric collection.
        
        Args:
            interval: Collection interval in seconds
        """
        if self.running:
            return
        
        self.running = True
        
        def collection_loop():
            while self.running:
                try:
                    for collector in self.collectors:
                        collector()
                    time.sleep(interval)
                except Exception as e:
                    print(f"Error in metric collection: {e}")
                    time.sleep(interval)
        
        self.collection_thread = threading.Thread(target=collection_loop, daemon=True)
        self.collection_thread.start()
    
    def stop_collection(self):
        """Stop automatic metric collection."""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)

class MetricsDashboard:
    """Main metrics dashboard class."""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        """Initialize metrics dashboard.
        
        Args:
            config: Dashboard configuration
        """
        self.config = config or DashboardConfig()
        self.collector = MetricCollector()
        self.console = Console() if RICH_AVAILABLE else None
        self.running = False
        
        # Built-in metrics
        self._setup_builtin_metrics()
        
        # Register default collectors
        self._register_default_collectors()
    
    def _setup_builtin_metrics(self):
        """Setup built-in metrics."""
        # System metrics
        self.collector.register_metric("cpu_usage", "CPU Usage", "%")
        self.collector.register_metric("memory_usage", "Memory Usage", "%")
        self.collector.register_metric("disk_usage", "Disk Usage", "%")
        
        # Platform metrics
        self.collector.register_metric("options_processed", "Options Processed", "count")
        self.collector.register_metric("api_calls", "API Calls", "count/min")
        self.collector.register_metric("errors", "Errors", "count")
        self.collector.register_metric("collection_cycles", "Collection Cycles", "count")
        self.collector.register_metric("processing_rate", "Processing Rate", "opts/min")
        
        # Performance metrics
        self.collector.register_metric("response_time", "Response Time", "ms")
        self.collector.register_metric("throughput", "Throughput", "req/sec")
        self.collector.register_metric("error_rate", "Error Rate", "%")
    
    def _register_default_collectors(self):
        """Register default metric collectors."""
        self.collector.register_collector(self._collect_system_metrics)
        self.collector.register_collector(self._collect_platform_metrics)
    
    def _collect_system_metrics(self):
        """Collect system performance metrics."""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.collector.add_metric_point("cpu_usage", cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.collector.add_metric_point("memory_usage", memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.collector.add_metric_point("disk_usage", disk_percent)
            
        except ImportError:
            # Mock system metrics if psutil not available
            import random
            self.collector.add_metric_point("cpu_usage", random.uniform(10, 80))
            self.collector.add_metric_point("memory_usage", random.uniform(30, 70))
            self.collector.add_metric_point("disk_usage", random.uniform(20, 60))
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
    
    def _collect_platform_metrics(self):
        """Collect platform-specific metrics."""
        # Mock platform metrics for demonstration
        # In real implementation, these would come from the actual platform
        import random
        
        # Simulate increasing counters
        current_time = time.time()
        
        # Options processed (cumulative)
        base_options = int(current_time / 60) * random.randint(50, 100)
        self.collector.add_metric_point("options_processed", base_options)
        
        # API calls per minute
        api_calls = random.randint(80, 150)
        self.collector.add_metric_point("api_calls", api_calls)
        
        # Errors (occasional spikes)
        errors = random.choice([0, 0, 0, 0, 1, 2, 0])
        self.collector.add_metric_point("errors", errors)
        
        # Collection cycles
        cycles = int(current_time / 30)  # One cycle every 30 seconds
        self.collector.add_metric_point("collection_cycles", cycles)
        
        # Processing rate
        processing_rate = random.uniform(40, 90)
        self.collector.add_metric_point("processing_rate", processing_rate)
        
        # Response time
        response_time = random.uniform(50, 200)
        self.collector.add_metric_point("response_time", response_time)
    
    def start_dashboard(self):
        """Start the metrics dashboard."""
        if not RICH_AVAILABLE:
            return self._start_basic_dashboard()
        
        self.running = True
        self.collector.start_collection(self.config.refresh_interval)
        
        try:
            self._run_rich_dashboard()
        except KeyboardInterrupt:
            print("\nDashboard stopped by user")
        finally:
            self.running = False
            self.collector.stop_collection()
    
    def _run_rich_dashboard(self):
        """Run Rich-based dashboard."""
        with Live(self._create_dashboard_layout(), refresh_per_second=1/self.config.refresh_interval) as live:
            while self.running:
                try:
                    live.update(self._create_dashboard_layout())
                    time.sleep(self.config.refresh_interval)
                except KeyboardInterrupt:
                    break
    
    def _create_dashboard_layout(self) -> Layout:
        """Create dashboard layout with metrics."""
        layout = Layout()
        
        # Split into header, body, and footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Header
        header = Panel(
            Align.center(f"[bold blue]G6.1 Platform Metrics Dashboard[/bold blue]\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"),
            box=box.HEAVY
        )
        layout["header"].update(header)
        
        # Body - split into sections
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="system"),
            Layout(name="platform")
        )
        
        layout["right"].split_column(
            Layout(name="performance"),
            Layout(name="alerts")
        )
        
        # System metrics
        layout["system"].update(self._create_system_metrics_panel())
        
        # Platform metrics
        layout["platform"].update(self._create_platform_metrics_panel())
        
        # Performance metrics
        layout["performance"].update(self._create_performance_metrics_panel())
        
        # Alerts panel
        layout["alerts"].update(self._create_alerts_panel())
        
        # Footer
        footer_text = f"[dim]Refresh: {self.config.refresh_interval}s | Data Points: {sum(len(m.data_points) for m in self.collector.metrics.values())} | Press Ctrl+C to exit[/dim]"
        layout["footer"].update(Panel(footer_text, box=box.HEAVY))
        
        return layout
    
    def _create_system_metrics_panel(self) -> Panel:
        """Create system metrics panel."""
        table = Table(title="System Metrics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Current", style="green")
        table.add_column("Trend", style="yellow")
        
        system_metrics = ["cpu_usage", "memory_usage", "disk_usage"]
        
        for metric_name in system_metrics:
            if metric_name in self.collector.metrics:
                metric = self.collector.metrics[metric_name]
                
                if metric.data_points:
                    current_value = metric.data_points[-1].value
                    trend = self._calculate_trend(metric)
                    trend_symbol = "↗" if trend > 5 else "↘" if trend < -5 else "→"
                    
                    display_name = metric.description
                    current_display = f"{current_value:.1f}{metric.unit}"
                    
                    table.add_row(display_name, current_display, trend_symbol)
        
        return Panel(table, title="[bold]🖥️ System[/bold]")
    
    def _create_platform_metrics_panel(self) -> Panel:
        """Create platform metrics panel."""
        table = Table(title="Platform Metrics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Current", style="green")
        table.add_column("Rate", style="yellow")
        
        platform_metrics = ["options_processed", "api_calls", "collection_cycles", "errors"]
        
        for metric_name in platform_metrics:
            if metric_name in self.collector.metrics:
                metric = self.collector.metrics[metric_name]
                
                if metric.data_points:
                    current_value = metric.data_points[-1].value
                    rate = self._calculate_rate(metric)
                    
                    display_name = metric.description
                    current_display = f"{current_value:.0f}"
                    rate_display = f"{rate:.1f}/min" if rate > 0 else "0/min"
                    
                    table.add_row(display_name, current_display, rate_display)
        
        return Panel(table, title="[bold]📊 Platform[/bold]")
    
    def _create_performance_metrics_panel(self) -> Panel:
        """Create performance metrics panel."""
        table = Table(title="Performance Metrics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Current", style="green")
        table.add_column("Avg (5m)", style="yellow")
        
        performance_metrics = ["processing_rate", "response_time", "error_rate"]
        
        for metric_name in performance_metrics:
            if metric_name in self.collector.metrics:
                metric = self.collector.metrics[metric_name]
                
                if metric.data_points:
                    current_value = metric.data_points[-1].value
                    avg_5min = self._calculate_average(metric, minutes=5)
                    
                    display_name = metric.description
                    current_display = f"{current_value:.1f}{metric.unit}"
                    avg_display = f"{avg_5min:.1f}{metric.unit}"
                    
                    table.add_row(display_name, current_display, avg_display)
        
        return Panel(table, title="[bold]⚡ Performance[/bold]")
    
    def _create_alerts_panel(self) -> Panel:
        """Create alerts panel."""
        alerts = []
        
        # Check for alert conditions
        for metric_name, metric in self.collector.metrics.items():
            if not metric.data_points:
                continue
            
            current_value = metric.data_points[-1].value
            
            # Simple alert thresholds
            if metric_name == "cpu_usage" and current_value > 80:
                alerts.append("🔴 High CPU usage detected")
            elif metric_name == "memory_usage" and current_value > 85:
                alerts.append("🔴 High memory usage detected")
            elif metric_name == "errors" and current_value > 5:
                alerts.append("🔴 High error rate detected")
            elif metric_name == "response_time" and current_value > 150:
                alerts.append("🟡 Slow response time detected")
        
        if not alerts:
            alerts = ["✅ All systems operating normally"]
        
        alert_text = "\n".join(alerts[:5])  # Show max 5 alerts
        
        return Panel(alert_text, title="[bold]🚨 Alerts[/bold]", box=box.ROUNDED)
    
    def _calculate_trend(self, metric: MetricSeries, minutes: int = 5) -> float:
        """Calculate trend for a metric over specified time period.
        
        Args:
            metric: Metric series
            minutes: Time period in minutes
            
        Returns:
            Trend value (positive = increasing, negative = decreasing)
        """
        if len(metric.data_points) < 2:
            return 0
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_points = [
            point for point in metric.data_points
            if point.timestamp >= cutoff_time
        ]
        
        if len(recent_points) < 2:
            return 0
        
        # Simple linear trend calculation
        first_value = recent_points[0].value
        last_value = recent_points[-1].value
        
        return ((last_value - first_value) / first_value) * 100 if first_value != 0 else 0
    
    def _calculate_rate(self, metric: MetricSeries, minutes: int = 1) -> float:
        """Calculate rate of change for a metric.
        
        Args:
            metric: Metric series
            minutes: Time period in minutes
            
        Returns:
            Rate of change per minute
        """
        if len(metric.data_points) < 2:
            return 0
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_points = [
            point for point in metric.data_points
            if point.timestamp >= cutoff_time
        ]
        
        if len(recent_points) < 2:
            return 0
        
        first_value = recent_points[0].value
        last_value = recent_points[-1].value
        time_diff = (recent_points[-1].timestamp - recent_points[0].timestamp).total_seconds() / 60
        
        if time_diff == 0:
            return 0
        
        return (last_value - first_value) / time_diff
    
    def _calculate_average(self, metric: MetricSeries, minutes: int = 5) -> float:
        """Calculate average value for a metric over specified time period.
        
        Args:
            metric: Metric series
            minutes: Time period in minutes
            
        Returns:
            Average value
        """
        if not metric.data_points:
            return 0
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_points = [
            point for point in metric.data_points
            if point.timestamp >= cutoff_time
        ]
        
        if not recent_points:
            return 0
        
        return sum(point.value for point in recent_points) / len(recent_points)
    
    def _start_basic_dashboard(self):
        """Start basic text-based dashboard when Rich is not available."""
        self.running = True
        self.collector.start_collection(self.config.refresh_interval)
        
        try:
            while self.running:
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print("=" * 60)
                print("G6.1 PLATFORM METRICS DASHBOARD")
                print("=" * 60)
                print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print()
                
                # System metrics
                print("SYSTEM METRICS")
                print("-" * 20)
                for metric_name in ["cpu_usage", "memory_usage", "disk_usage"]:
                    if metric_name in self.collector.metrics:
                        metric = self.collector.metrics[metric_name]
                        if metric.data_points:
                            value = metric.data_points[-1].value
                            print(f"{metric.description}: {value:.1f}{metric.unit}")
                
                print()
                
                # Platform metrics
                print("PLATFORM METRICS")
                print("-" * 20)
                for metric_name in ["options_processed", "api_calls", "collection_cycles", "errors"]:
                    if metric_name in self.collector.metrics:
                        metric = self.collector.metrics[metric_name]
                        if metric.data_points:
                            value = metric.data_points[-1].value
                            print(f"{metric.description}: {value:.0f}")
                
                print()
                print("Press Ctrl+C to exit")
                
                time.sleep(self.config.refresh_interval)
                
        except KeyboardInterrupt:
            print("\nDashboard stopped by user")
        finally:
            self.running = False
            self.collector.stop_collection()
    
    def add_custom_metric(self, name: str, value: float, description: str = "", unit: str = ""):
        """Add custom metric from external source.
        
        Args:
            name: Metric name
            value: Metric value
            description: Metric description
            unit: Unit of measurement
        """
        if name not in self.collector.metrics:
            self.collector.register_metric(name, description or name.title(), unit)
        
        self.collector.add_metric_point(name, value)
    
    def export_metrics(self, format_type: str = 'json') -> str:
        """Export current metrics data.
        
        Args:
            format_type: Export format ('json', 'csv')
            
        Returns:
            Formatted metrics data
        """
        if format_type == 'json':
            metrics_data = {}
            
            for name, metric in self.collector.metrics.items():
                metrics_data[name] = {
                    'description': metric.description,
                    'unit': metric.unit,
                    'current_value': metric.data_points[-1].value if metric.data_points else None,
                    'data_points': [
                        {
                            'timestamp': point.timestamp.isoformat(),
                            'value': point.value,
                            'tags': point.tags
                        }
                        for point in list(metric.data_points)[-100:]  # Last 100 points
                    ]
                }
            
            return json.dumps(metrics_data, indent=2)
        
        elif format_type == 'csv':
            lines = ['timestamp,metric,value,unit,description']
            
            for name, metric in self.collector.metrics.items():
                for point in metric.data_points:
                    lines.append(
                        f"{point.timestamp.isoformat()},{name},{point.value},{metric.unit},{metric.description}"
                    )
            
            return '\n'.join(lines)
        
        return ""

# Example usage and integration functions
def integrate_with_platform(dashboard: MetricsDashboard, platform_metrics: Dict[str, Any]):
    """Integrate dashboard with platform metrics.
    
    Args:
        dashboard: MetricsDashboard instance
        platform_metrics: Dictionary of platform metrics
    """
    # Map platform metrics to dashboard
    metric_mapping = {
        'options_processed': 'options_processed',
        'collection_cycles': 'collection_cycles',
        'errors': 'errors',
        'api_calls': 'api_calls',
        'processing_rate': 'processing_rate'
    }
    
    for platform_key, dashboard_key in metric_mapping.items():
        if platform_key in platform_metrics:
            dashboard.add_custom_metric(
                dashboard_key,
                platform_metrics[platform_key],
                platform_key.replace('_', ' ').title()
            )

# Main execution
if __name__ == "__main__":
    # Example usage
    config = DashboardConfig(
        refresh_interval=3,
        display_mode='rich' if RICH_AVAILABLE else 'basic'
    )
    
    dashboard = MetricsDashboard(config)
    
    print("Starting G6.1 Platform Metrics Dashboard...")
    print("Press Ctrl+C to stop")
    
    try:
        dashboard.start_dashboard()
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
    except Exception as e:
        print(f"Dashboard error: {e}")
    
    print("Dashboard stopped.")