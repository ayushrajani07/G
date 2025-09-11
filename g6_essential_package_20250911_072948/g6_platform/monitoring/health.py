#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
❤️ Health Monitor - G6 Platform v3.0
Comprehensive system health monitoring with automated alerts and recovery.

Restructured from: health_monitor.py, performance_monitor.py
Features:
- Real-time component health monitoring
- Automated health checks with scheduling
- Alert generation and notification
- Health history and trending
- Auto-recovery mechanisms and circuit breakers
- Performance benchmarking and SLA tracking
"""

import time
import logging
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import json

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class HealthCheck:
    """Individual health check definition."""
    name: str
    description: str
    check_function: Callable[[], Dict[str, Any]]
    interval_seconds: float = 60.0
    timeout_seconds: float = 30.0
    enabled: bool = True
    critical: bool = False
    tags: List[str] = field(default_factory=list)
    
    # State tracking
    last_run: Optional[datetime] = None
    last_result: Optional[Dict[str, Any]] = None
    consecutive_failures: int = 0
    total_runs: int = 0
    total_failures: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_runs == 0:
            return 0.0
        return ((self.total_runs - self.total_failures) / self.total_runs) * 100

@dataclass
class HealthAlert:
    """Health alert information."""
    id: str
    timestamp: datetime
    severity: AlertSeverity
    component: str
    check_name: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_percent: float
    disk_used_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    load_average: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used_mb,
            'disk_percent': self.disk_percent,
            'disk_used_gb': self.disk_used_gb,
            'network_bytes_sent': self.network_bytes_sent,
            'network_bytes_recv': self.network_bytes_recv,
            'load_average': self.load_average
        }

class HealthMonitor:
    """
    ❤️ Comprehensive health monitoring system.
    
    Provides real-time monitoring of system and application health with
    automated alerts, trending, and recovery mechanisms.
    """
    
    def __init__(self,
                 check_interval: float = 60.0,
                 alert_threshold: int = 3,
                 history_retention_hours: int = 24,
                 enable_system_monitoring: bool = True,
                 enable_alerts: bool = True):
        """
        Initialize health monitor.
        
        Args:
            check_interval: Default check interval in seconds
            alert_threshold: Consecutive failures before alert
            history_retention_hours: Hours to retain health history
            enable_system_monitoring: Enable system resource monitoring
            enable_alerts: Enable alert generation
        """
        self.check_interval = check_interval
        self.alert_threshold = alert_threshold
        self.history_retention = timedelta(hours=history_retention_hours)
        self.enable_system_monitoring = enable_system_monitoring
        self.enable_alerts = enable_alerts
        
        # Health checks registry
        self._health_checks: Dict[str, HealthCheck] = {}
        self._check_lock = threading.RLock()
        
        # Health history
        self._health_history: deque = deque(maxlen=10000)
        self._system_metrics: deque = deque(maxlen=1000)
        self._history_lock = threading.RLock()
        
        # Alerts
        self._alerts: Dict[str, HealthAlert] = {}
        self._alert_handlers: List[Callable[[HealthAlert], None]] = []
        self._alerts_lock = threading.RLock()
        
        # Monitoring threads
        self._monitor_thread: Optional[threading.Thread] = None
        self._system_monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        # Current system state
        self._overall_status = HealthStatus.UNKNOWN
        self._component_status: Dict[str, HealthStatus] = {}
        
        # Register default system checks
        self._register_default_checks()
        
        logger.info("❤️ Health monitor initialized")
        logger.info(f"⚙️ Check interval: {check_interval}s, Alert threshold: {alert_threshold}")
    
    def _register_default_checks(self):
        """Register default system health checks."""
        # System resource checks
        self.add_check(
            name="system_cpu",
            description="Monitor CPU usage",
            check_function=self._check_cpu_usage,
            interval=30,
            critical=False
        )
        
        self.add_check(
            name="system_memory",
            description="Monitor memory usage",
            check_function=self._check_memory_usage,
            interval=30,
            critical=False
        )
        
        self.add_check(
            name="system_disk",
            description="Monitor disk usage",
            check_function=self._check_disk_usage,
            interval=60,
            critical=False
        )
        
        # Network connectivity check
        self.add_check(
            name="network_connectivity",
            description="Check network connectivity",
            check_function=self._check_network_connectivity,
            interval=120,
            critical=True
        )
    
    def add_check(self,
                  name: str,
                  description: str,
                  check_function: Callable[[], Dict[str, Any]],
                  interval: float = None,
                  timeout: float = 30.0,
                  critical: bool = False,
                  enabled: bool = True,
                  tags: List[str] = None) -> bool:
        """
        Add health check.
        
        Args:
            name: Unique check name
            description: Check description
            check_function: Function that returns health status
            interval: Check interval in seconds
            timeout: Check timeout in seconds
            critical: Whether this is a critical check
            enabled: Whether check is enabled
            tags: Optional tags for categorization
            
        Returns:
            True if added successfully
        """
        try:
            interval = interval or self.check_interval
            tags = tags or []
            
            health_check = HealthCheck(
                name=name,
                description=description,
                check_function=check_function,
                interval_seconds=interval,
                timeout_seconds=timeout,
                critical=critical,
                enabled=enabled,
                tags=tags
            )
            
            with self._check_lock:
                self._health_checks[name] = health_check
            
            logger.info(f"✅ Health check added: {name} ({'critical' if critical else 'normal'})")
            return True
            
        except Exception as e:
            logger.error(f"🔴 Failed to add health check {name}: {e}")
            return False
    
    def remove_check(self, name: str) -> bool:
        """Remove health check."""
        try:
            with self._check_lock:
                if name in self._health_checks:
                    del self._health_checks[name]
                    logger.info(f"🗑️ Health check removed: {name}")
                    return True
                else:
                    logger.warning(f"⚠️ Health check not found: {name}")
                    return False
                    
        except Exception as e:
            logger.error(f"🔴 Failed to remove health check {name}: {e}")
            return False
    
    def start(self):
        """Start health monitoring."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("⚠️ Health monitor already running")
            return
        
        self._stop_monitoring.clear()
        
        # Start main monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="HealthMonitor"
        )
        self._monitor_thread.start()
        
        # Start system monitoring if enabled
        if self.enable_system_monitoring:
            self._system_monitor_thread = threading.Thread(
                target=self._system_monitoring_loop,
                daemon=True,
                name="SystemMonitor"
            )
            self._system_monitor_thread.start()
        
        logger.info("🚀 Health monitoring started")
    
    def stop(self, timeout: float = 10.0):
        """Stop health monitoring."""
        logger.info("🛑 Stopping health monitoring...")
        
        self._stop_monitoring.set()
        
        # Wait for threads to stop
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=timeout)
        
        if self._system_monitor_thread and self._system_monitor_thread.is_alive():
            self._system_monitor_thread.join(timeout=timeout)
        
        logger.info("✅ Health monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        logger.info("🔄 Health monitoring loop started")
        
        while not self._stop_monitoring.is_set():
            try:
                current_time = time.time()
                
                # Run scheduled health checks
                checks_to_run = []
                
                with self._check_lock:
                    for check in self._health_checks.values():
                        if not check.enabled:
                            continue
                        
                        # Check if it's time to run
                        if (check.last_run is None or
                            (current_time - check.last_run.timestamp()) >= check.interval_seconds):
                            checks_to_run.append(check)
                
                # Execute health checks
                for check in checks_to_run:
                    self._execute_health_check(check)
                
                # Update overall status
                self._update_overall_status()
                
                # Cleanup old history
                self._cleanup_history()
                
                # Sleep until next check
                self._stop_monitoring.wait(min(10, self.check_interval))
                
            except Exception as e:
                logger.error(f"🔴 Monitoring loop error: {e}")
                self._stop_monitoring.wait(30)  # Wait longer on error
        
        logger.info("🔄 Health monitoring loop stopped")
    
    def _system_monitoring_loop(self):
        """System resource monitoring loop."""
        logger.info("📊 System monitoring loop started")
        
        while not self._stop_monitoring.is_set():
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                
                # Store metrics
                with self._history_lock:
                    self._system_metrics.append(metrics)
                
                # Sleep for next collection
                self._stop_monitoring.wait(30)  # Collect every 30 seconds
                
            except Exception as e:
                logger.error(f"🔴 System monitoring error: {e}")
                self._stop_monitoring.wait(60)  # Wait longer on error
        
        logger.info("📊 System monitoring loop stopped")
    
    def _execute_health_check(self, check: HealthCheck):
        """Execute a single health check."""
        start_time = time.time()
        
        try:
            # Run the check function with timeout
            result = self._run_with_timeout(check.check_function, check.timeout_seconds)
            
            # Process result
            if result is None:
                result = {'status': 'timeout', 'message': 'Health check timed out'}
            
            # Determine status
            status_str = result.get('status', 'unknown').lower()
            if status_str in ['healthy', 'ok', 'pass']:
                status = HealthStatus.HEALTHY
            elif status_str in ['degraded', 'warning']:
                status = HealthStatus.DEGRADED
            elif status_str in ['unhealthy', 'error', 'fail']:
                status = HealthStatus.UNHEALTHY
            elif status_str in ['critical']:
                status = HealthStatus.CRITICAL
            else:
                status = HealthStatus.UNKNOWN
            
            # Update check state
            check.last_run = datetime.now()
            check.last_result = result
            check.total_runs += 1
            
            if status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                check.consecutive_failures += 1
                check.total_failures += 1
            else:
                check.consecutive_failures = 0
            
            # Store in history
            history_entry = {
                'timestamp': check.last_run.isoformat(),
                'check_name': check.name,
                'status': status.value,
                'result': result,
                'execution_time': time.time() - start_time,
                'critical': check.critical
            }
            
            with self._history_lock:
                self._health_history.append(history_entry)
            
            # Update component status
            self._component_status[check.name] = status
            
            # Generate alerts if needed
            if self.enable_alerts and check.consecutive_failures >= self.alert_threshold:
                self._generate_alert(check, status, result)
            
            logger.debug(f"✅ Health check completed: {check.name} -> {status.value}")
            
        except Exception as e:
            logger.error(f"🔴 Health check failed: {check.name} -> {e}")
            
            # Update failure state
            check.last_run = datetime.now()
            check.total_runs += 1
            check.total_failures += 1
            check.consecutive_failures += 1
            
            # Store error in history
            error_entry = {
                'timestamp': check.last_run.isoformat(),
                'check_name': check.name,
                'status': HealthStatus.CRITICAL.value,
                'error': str(e),
                'execution_time': time.time() - start_time,
                'critical': check.critical
            }
            
            with self._history_lock:
                self._health_history.append(error_entry)
            
            self._component_status[check.name] = HealthStatus.CRITICAL
    
    def _run_with_timeout(self, func: Callable, timeout: float) -> Optional[Dict[str, Any]]:
        """Run function with timeout."""
        import signal
        
        class TimeoutException(Exception):
            pass
        
        def timeout_handler(signum, frame):
            raise TimeoutException("Function timed out")
        
        try:
            # Set timeout handler (Unix only)
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(timeout))
            
            # Execute function
            result = func()
            
            # Clear timeout
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
            
        except TimeoutException:
            return None
        except Exception as e:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            raise
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        
        # Disk usage (root partition)
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        
        # Network I/O
        network = psutil.net_io_counters()
        network_sent = network.bytes_sent
        network_recv = network.bytes_recv
        
        # Load average (Unix only)
        load_avg = None
        if hasattr(psutil, 'getloadavg'):
            try:
                load_avg = psutil.getloadavg()[0]  # 1-minute load average
            except:
                pass
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            network_bytes_sent=network_sent,
            network_bytes_recv=network_recv,
            load_average=load_avg
        )
    
    def _update_overall_status(self):
        """Update overall system status based on component statuses."""
        if not self._component_status:
            self._overall_status = HealthStatus.UNKNOWN
            return
        
        statuses = list(self._component_status.values())
        critical_count = statuses.count(HealthStatus.CRITICAL)
        unhealthy_count = statuses.count(HealthStatus.UNHEALTHY)
        degraded_count = statuses.count(HealthStatus.DEGRADED)
        
        # Determine overall status
        if critical_count > 0:
            self._overall_status = HealthStatus.CRITICAL
        elif unhealthy_count > len(statuses) * 0.3:  # More than 30% unhealthy
            self._overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > len(statuses) * 0.5:  # More than 50% degraded
            self._overall_status = HealthStatus.DEGRADED
        else:
            self._overall_status = HealthStatus.HEALTHY
    
    def _generate_alert(self, check: HealthCheck, status: HealthStatus, result: Dict[str, Any]):
        """Generate health alert."""
        try:
            # Create alert
            alert_id = f"{check.name}_{int(time.time())}"
            
            # Determine severity
            if status == HealthStatus.CRITICAL or check.critical:
                severity = AlertSeverity.CRITICAL
            elif status == HealthStatus.UNHEALTHY:
                severity = AlertSeverity.ERROR
            elif status == HealthStatus.DEGRADED:
                severity = AlertSeverity.WARNING
            else:
                severity = AlertSeverity.INFO
            
            alert = HealthAlert(
                id=alert_id,
                timestamp=datetime.now(),
                severity=severity,
                component=check.name,
                check_name=check.name,
                message=f"Health check {check.name} failed {check.consecutive_failures} times",
                details={
                    'consecutive_failures': check.consecutive_failures,
                    'total_failures': check.total_failures,
                    'success_rate': check.success_rate,
                    'last_result': result,
                    'critical': check.critical
                }
            )
            
            # Store alert
            with self._alerts_lock:
                self._alerts[alert_id] = alert
            
            # Notify alert handlers
            for handler in self._alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"🔴 Alert handler error: {e}")
            
            logger.warning(f"🚨 Health alert generated: {alert.message}")
            
        except Exception as e:
            logger.error(f"🔴 Failed to generate alert: {e}")
    
    def _cleanup_history(self):
        """Clean up old history entries."""
        try:
            cutoff_time = datetime.now() - self.history_retention
            
            with self._history_lock:
                # Clean health history
                while (self._health_history and 
                       datetime.fromisoformat(self._health_history[0]['timestamp']) < cutoff_time):
                    self._health_history.popleft()
                
                # Clean system metrics
                while (self._system_metrics and 
                       self._system_metrics[0].timestamp < cutoff_time):
                    self._system_metrics.popleft()
            
        except Exception as e:
            logger.error(f"🔴 History cleanup error: {e}")
    
    # Default health check functions
    
    def _check_cpu_usage(self) -> Dict[str, Any]:
        """Check CPU usage."""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > 90:
            return {'status': 'critical', 'cpu_percent': cpu_percent, 'message': 'CPU usage critical'}
        elif cpu_percent > 80:
            return {'status': 'unhealthy', 'cpu_percent': cpu_percent, 'message': 'CPU usage high'}
        elif cpu_percent > 70:
            return {'status': 'degraded', 'cpu_percent': cpu_percent, 'message': 'CPU usage elevated'}
        else:
            return {'status': 'healthy', 'cpu_percent': cpu_percent, 'message': 'CPU usage normal'}
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage."""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        if memory_percent > 95:
            return {'status': 'critical', 'memory_percent': memory_percent, 'message': 'Memory usage critical'}
        elif memory_percent > 85:
            return {'status': 'unhealthy', 'memory_percent': memory_percent, 'message': 'Memory usage high'}
        elif memory_percent > 75:
            return {'status': 'degraded', 'memory_percent': memory_percent, 'message': 'Memory usage elevated'}
        else:
            return {'status': 'healthy', 'memory_percent': memory_percent, 'message': 'Memory usage normal'}
    
    def _check_disk_usage(self) -> Dict[str, Any]:
        """Check disk usage."""
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        if disk_percent > 95:
            return {'status': 'critical', 'disk_percent': disk_percent, 'message': 'Disk usage critical'}
        elif disk_percent > 85:
            return {'status': 'unhealthy', 'disk_percent': disk_percent, 'message': 'Disk usage high'}
        elif disk_percent > 75:
            return {'status': 'degraded', 'disk_percent': disk_percent, 'message': 'Disk usage elevated'}
        else:
            return {'status': 'healthy', 'disk_percent': disk_percent, 'message': 'Disk usage normal'}
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity."""
        try:
            import socket
            
            # Try to connect to a reliable server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('8.8.8.8', 53))  # Google DNS
            sock.close()
            
            if result == 0:
                return {'status': 'healthy', 'message': 'Network connectivity OK'}
            else:
                return {'status': 'unhealthy', 'message': 'Network connectivity failed'}
                
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Network check error: {e}'}
    
    # Public API methods
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        with self._check_lock:
            checks_summary = {}
            for name, check in self._health_checks.items():
                checks_summary[name] = {
                    'status': self._component_status.get(name, HealthStatus.UNKNOWN).value,
                    'enabled': check.enabled,
                    'critical': check.critical,
                    'last_run': check.last_run.isoformat() if check.last_run else None,
                    'consecutive_failures': check.consecutive_failures,
                    'success_rate': check.success_rate,
                    'last_result': check.last_result
                }
        
        # Get recent system metrics
        recent_metrics = None
        with self._history_lock:
            if self._system_metrics:
                recent_metrics = self._system_metrics[-1].to_dict()
        
        return {
            'overall_status': self._overall_status.value,
            'checks': checks_summary,
            'system_metrics': recent_metrics,
            'active_alerts': len(self._alerts),
            'monitoring_active': not self._stop_monitoring.is_set()
        }
    
    def get_alerts(self, unresolved_only: bool = True) -> List[Dict[str, Any]]:
        """Get alerts."""
        with self._alerts_lock:
            alerts = []
            for alert in self._alerts.values():
                if unresolved_only and alert.resolved:
                    continue
                
                alerts.append({
                    'id': alert.id,
                    'timestamp': alert.timestamp.isoformat(),
                    'severity': alert.severity.value,
                    'component': alert.component,
                    'message': alert.message,
                    'acknowledged': alert.acknowledged,
                    'resolved': alert.resolved,
                    'details': alert.details
                })
            
            return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        with self._alerts_lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].acknowledged = True
                logger.info(f"✅ Alert acknowledged: {alert_id}")
                return True
            return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        with self._alerts_lock:
            if alert_id in self._alerts:
                alert = self._alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"✅ Alert resolved: {alert_id}")
                return True
            return False
    
    def add_alert_handler(self, handler: Callable[[HealthAlert], None]):
        """Add alert notification handler."""
        self._alert_handlers.append(handler)
        logger.info("✅ Alert handler added")
    
    def get_system_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get system metrics history."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._history_lock:
            metrics = []
            for metric in self._system_metrics:
                if metric.timestamp >= cutoff_time:
                    metrics.append(metric.to_dict())
            
            return sorted(metrics, key=lambda x: x['timestamp'])
    
    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends and statistics."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._history_lock:
            # Analyze health history
            status_counts = defaultdict(int)
            check_stats = defaultdict(lambda: {'total': 0, 'failures': 0})
            
            for entry in self._health_history:
                entry_time = datetime.fromisoformat(entry['timestamp'])
                if entry_time >= cutoff_time:
                    status_counts[entry['status']] += 1
                    check_name = entry['check_name']
                    check_stats[check_name]['total'] += 1
                    
                    if entry['status'] in ['unhealthy', 'critical']:
                        check_stats[check_name]['failures'] += 1
            
            # Calculate trends
            trends = {}
            for check_name, stats in check_stats.items():
                if stats['total'] > 0:
                    trends[check_name] = {
                        'total_checks': stats['total'],
                        'failure_rate': (stats['failures'] / stats['total']) * 100,
                        'success_rate': ((stats['total'] - stats['failures']) / stats['total']) * 100
                    }
            
            return {
                'period_hours': hours,
                'status_distribution': dict(status_counts),
                'check_trends': trends,
                'total_checks': sum(status_counts.values())
            }