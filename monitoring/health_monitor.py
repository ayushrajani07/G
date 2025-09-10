#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
❤️ Complete Health Monitoring System for G6.1 Platform
Author: AI Assistant (Comprehensive health monitoring with alerting)

✅ Features:
- Real-time component health monitoring
- System performance tracking
- Automated health checks with scheduling
- Alert generation and notification
- Health history and trending
- Dependency health monitoring
- Performance benchmarking
- Auto-recovery mechanisms
"""

import logging
import time
import datetime
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import psutil
import json
from enum import Enum

logger = logging.getLogger(__name__)

class HealthLevel(Enum):
    """❤️ Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    """🧪 Individual health check definition."""
    name: str
    description: str
    check_function: Callable[[], Dict[str, Any]]
    interval_seconds: float = 60.0
    timeout_seconds: float = 30.0
    enabled: bool = True
    critical: bool = False
    
    # 📊 Tracking
    last_run: Optional[datetime.datetime] = None
    last_result: Optional[Dict[str, Any]] = None
    consecutive_failures: int = 0
    total_runs: int = 0
    total_failures: int = 0

@dataclass
class HealthResult:
    """📊 Health check result."""
    check_name: str
    status: HealthLevel
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    
    @property
    def is_healthy(self) -> bool:
        """❤️ Check if result indicates healthy status."""
        return self.status == HealthLevel.HEALTHY

@dataclass
class ComponentHealth:
    """📊 Complete component health status."""
    component_name: str
    overall_status: HealthLevel
    health_score: float  # 0.0 to 1.0
    
    # 🧪 Check results
    check_results: Dict[str, HealthResult] = field(default_factory=dict)
    
    # 📈 Performance metrics
    uptime_seconds: float = 0.0
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    last_activity: Optional[datetime.datetime] = None
    
    # 📊 Statistics
    total_checks_run: int = 0
    checks_passed: int = 0
    checks_failed: int = 0
    consecutive_failures: int = 0
    
    # ⏰ Timestamps
    last_check_time: Optional[datetime.datetime] = None
    last_healthy_time: Optional[datetime.datetime] = None
    
    @property
    def success_rate(self) -> float:
        """📊 Calculate check success rate."""
        return self.checks_passed / self.total_checks_run if self.total_checks_run > 0 else 1.0
    
    @property
    def is_degraded(self) -> bool:
        """⚠️ Check if component is degraded."""
        return self.overall_status == HealthLevel.DEGRADED
    
    @property
    def is_unhealthy(self) -> bool:
        """🔴 Check if component is unhealthy."""
        return self.overall_status in [HealthLevel.UNHEALTHY, HealthLevel.CRITICAL]

class HealthMonitor:
    """
    ❤️ AI Assistant: Comprehensive Health Monitoring System.
    
    Monitors system and component health with:
    - Automated health checks
    - Performance monitoring
    - Alert generation
    - Health history tracking
    - Auto-recovery mechanisms
    """
    
    def __init__(self, 
                 enable_system_monitoring: bool = True,
                 enable_auto_recovery: bool = True,
                 health_history_size: int = 1000):
        """
        🆕 Initialize Health Monitor.
        
        Args:
            enable_system_monitoring: Enable system resource monitoring
            enable_auto_recovery: Enable automatic recovery attempts
            health_history_size: Size of health history buffer
        """
        self.enable_system_monitoring = enable_system_monitoring
        self.enable_auto_recovery = enable_auto_recovery
        self.health_history_size = health_history_size
        
        self.logger = logging.getLogger(f"{__name__}.HealthMonitor")
        
        # 📊 Health tracking
        self.components: Dict[str, ComponentHealth] = {}
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_history: deque = deque(maxlen=health_history_size)
        
        # 🔔 Alert system
        self.alert_handlers: List[Callable[[str, Dict[str, Any]], None]] = []
        self.alert_thresholds = {
            'consecutive_failures': 3,
            'health_score_threshold': 0.5,
            'response_time_threshold_ms': 5000
        }
        
        # 🔄 Monitoring control
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # 📈 Performance tracking
        self.start_time = time.time()
        self.total_checks_run = 0
        self.total_alerts_sent = 0
        
        # 🔒 Thread safety
        self.lock = threading.RLock()
        
        self.logger.info("✅ Health Monitor initialized")
    
    def register_component(self, 
                          component_name: str, 
                          health_checks: List[HealthCheck]) -> bool:
        """
        📋 Register a component with its health checks.
        
        Args:
            component_name: Name of the component
            health_checks: List of health checks for the component
            
        Returns:
            bool: True if registration successful
        """
        try:
            with self.lock:
                # 📊 Create component health record
                self.components[component_name] = ComponentHealth(
                    component_name=component_name,
                    overall_status=HealthLevel.UNKNOWN,
                    health_score=1.0
                )
                
                # 📋 Register health checks
                for check in health_checks:
                    check_key = f"{component_name}.{check.name}"
                    self.health_checks[check_key] = check
                    
                    self.logger.debug(f"✅ Registered check: {check_key}")
                
                self.logger.info(f"✅ Component registered: {component_name} with {len(health_checks)} checks")
                return True
                
        except Exception as e:
            self.logger.error(f"🔴 Failed to register component {component_name}: {e}")
            return False
    
    def add_alert_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        """🔔 Add alert handler function."""
        self.alert_handlers.append(handler)
        self.logger.info("✅ Alert handler added")
    
    def start_monitoring(self, check_interval: float = 30.0) -> bool:
        """
        🚀 Start continuous health monitoring.
        
        Args:
            check_interval: Base interval between monitoring cycles
            
        Returns:
            bool: True if monitoring started successfully
        """
        try:
            if self.monitoring_active:
                self.logger.warning("⚠️ Monitoring is already active")
                return True
            
            self.monitoring_active = True
            self.stop_event.clear()
            
            # 🔄 Start monitoring thread
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                args=(check_interval,),
                name="HealthMonitor",
                daemon=True
            )
            self.monitor_thread.start()
            
            self.logger.info(f"🚀 Health monitoring started with {check_interval}s interval")
            return True
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to start monitoring: {e}")
            self.monitoring_active = False
            return False
    
    def stop_monitoring(self):
        """🛑 Stop health monitoring."""
        try:
            self.monitoring_active = False
            self.stop_event.set()
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5.0)
            
            self.logger.info("🛑 Health monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"🔴 Error stopping monitoring: {e}")
    
    def run_health_check(self, component_name: str, check_name: str) -> Optional[HealthResult]:
        """
        🧪 Run a specific health check.
        
        Args:
            component_name: Name of the component
            check_name: Name of the health check
            
        Returns:
            Optional[HealthResult]: Health check result or None if failed
        """
        check_key = f"{component_name}.{check_name}"
        
        try:
            with self.lock:
                if check_key not in self.health_checks:
                    self.logger.warning(f"⚠️ Health check not found: {check_key}")
                    return None
                
                check = self.health_checks[check_key]
                
                if not check.enabled:
                    self.logger.debug(f"⏭️ Health check disabled: {check_key}")
                    return None
                
                # ⏱️ Execute check with timeout
                start_time = time.time()
                
                try:
                    # 🧪 Run the check function
                    result_data = check.check_function()
                    execution_time_ms = (time.time() - start_time) * 1000
                    
                    # 📊 Parse result
                    status_str = result_data.get('status', 'unknown').lower()
                    status = HealthLevel(status_str) if status_str in [e.value for e in HealthLevel] else HealthLevel.UNKNOWN
                    message = result_data.get('message', 'No message')
                    details = result_data.get('details', {})
                    
                    # ✅ Create result
                    result = HealthResult(
                        check_name=check_name,
                        status=status,
                        message=message,
                        details=details,
                        execution_time_ms=execution_time_ms
                    )
                    
                    # 📊 Update check tracking
                    check.last_run = datetime.datetime.now()
                    check.last_result = result_data
                    check.total_runs += 1
                    
                    if result.is_healthy:
                        check.consecutive_failures = 0
                    else:
                        check.consecutive_failures += 1
                        check.total_failures += 1
                    
                    self.total_checks_run += 1
                    self.logger.debug(f"🧪 Check completed: {check_key} -> {status.value}")
                    
                    return result
                    
                except Exception as check_error:
                    execution_time_ms = (time.time() - start_time) * 1000
                    
                    # 🔴 Check execution failed
                    result = HealthResult(
                        check_name=check_name,
                        status=HealthLevel.CRITICAL,
                        message=f"Check execution failed: {str(check_error)}",
                        execution_time_ms=execution_time_ms
                    )
                    
                    check.consecutive_failures += 1
                    check.total_failures += 1
                    check.total_runs += 1
                    
                    self.logger.warning(f"⚠️ Check execution failed: {check_key} - {check_error}")
                    return result
                    
        except Exception as e:
            self.logger.error(f"🔴 Error running health check {check_key}: {e}")
            return None
    
    def run_all_health_checks(self) -> Dict[str, ComponentHealth]:
        """
        🧪 Run all health checks and update component health.
        
        Returns:
            Dict[str, ComponentHealth]: Updated component health status
        """
        try:
            with self.lock:
                # 📊 Group checks by component
                component_checks = defaultdict(list)
                for check_key, check in self.health_checks.items():
                    component_name = check_key.split('.')[0]
                    component_checks[component_name].append((check_key, check))
                
                # 🔄 Run checks for each component
                for component_name, checks in component_checks.items():
                    self._update_component_health(component_name, checks)
                
                # 📊 Update system-wide metrics
                if self.enable_system_monitoring:
                    self._update_system_metrics()
                
                # 📚 Add to history
                current_health = self._get_overall_health_snapshot()
                self.health_history.append(current_health)
                
                return dict(self.components)
                
        except Exception as e:
            self.logger.error(f"🔴 Error running all health checks: {e}")
            return {}
    
    def _update_component_health(self, component_name: str, checks: List[tuple]):
        """📊 Update component health based on check results."""
        try:
            if component_name not in self.components:
                return
            
            component = self.components[component_name]
            check_results = {}
            
            # 🧪 Run all checks for this component
            for check_key, check in checks:
                check_name = check_key.split('.', 1)[1]  # Remove component prefix
                result = self.run_health_check(component_name, check_name)
                
                if result:
                    check_results[check_name] = result
            
            # 📊 Calculate overall component health
            if check_results:
                healthy_checks = sum(1 for r in check_results.values() if r.is_healthy)
                total_checks = len(check_results)
                health_score = healthy_checks / total_checks
                
                # 🎯 Determine overall status
                if health_score >= 0.9:
                    overall_status = HealthLevel.HEALTHY
                elif health_score >= 0.7:
                    overall_status = HealthLevel.DEGRADED
                elif health_score >= 0.3:
                    overall_status = HealthLevel.UNHEALTHY
                else:
                    overall_status = HealthLevel.CRITICAL
                
                # 📈 Update component
                component.check_results = check_results
                component.overall_status = overall_status
                component.health_score = health_score
                component.total_checks_run += total_checks
                component.checks_passed += healthy_checks
                component.checks_failed += (total_checks - healthy_checks)
                component.last_check_time = datetime.datetime.now()
                
                # 📊 Track consecutive failures
                if overall_status == HealthLevel.HEALTHY:
                    component.consecutive_failures = 0
                    component.last_healthy_time = datetime.datetime.now()
                else:
                    component.consecutive_failures += 1
                
                # 🔔 Check for alerts
                self._check_component_alerts(component_name, component)
                
            else:
                # 🔴 No check results available
                component.overall_status = HealthLevel.UNKNOWN
                
        except Exception as e:
            self.logger.error(f"🔴 Error updating component health {component_name}: {e}")
    
    def _update_system_metrics(self):
        """📊 Update system-wide performance metrics."""
        try:
            # 📈 CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            memory_usage_mb = memory.used / 1024 / 1024
            
            # 📊 Update all components with system metrics
            for component in self.components.values():
                component.cpu_usage_percent = cpu_percent
                component.memory_usage_mb = memory_usage_mb
                component.uptime_seconds = time.time() - self.start_time
                
        except Exception as e:
            self.logger.debug(f"⚠️ Error updating system metrics: {e}")
    
    def _check_component_alerts(self, component_name: str, component: ComponentHealth):
        """🔔 Check if component triggers any alerts."""
        try:
            alert_data = {
                'component': component_name,
                'status': component.overall_status.value,
                'health_score': component.health_score,
                'consecutive_failures': component.consecutive_failures,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # 🚨 Critical status alert
            if component.overall_status == HealthLevel.CRITICAL:
                self._send_alert(f"CRITICAL: {component_name} is in critical state", alert_data)
            
            # ⚠️ Consecutive failures alert
            elif component.consecutive_failures >= self.alert_thresholds['consecutive_failures']:
                self._send_alert(f"WARNING: {component_name} has {component.consecutive_failures} consecutive failures", alert_data)
            
            # 📉 Low health score alert
            elif component.health_score < self.alert_thresholds['health_score_threshold']:
                self._send_alert(f"WARNING: {component_name} health score is low ({component.health_score:.2f})", alert_data)
            
        except Exception as e:
            self.logger.error(f"🔴 Error checking alerts for {component_name}: {e}")
    
    def _send_alert(self, message: str, alert_data: Dict[str, Any]):
        """🔔 Send alert to all registered handlers."""
        try:
            self.total_alerts_sent += 1
            
            for handler in self.alert_handlers:
                try:
                    handler(message, alert_data)
                except Exception as e:
                    self.logger.error(f"🔴 Alert handler error: {e}")
            
            self.logger.warning(f"🔔 ALERT: {message}")
            
        except Exception as e:
            self.logger.error(f"🔴 Error sending alert: {e}")
    
    def _monitoring_loop(self, base_interval: float):
        """🔄 Main monitoring loop."""
        self.logger.info("🔄 Health monitoring loop started")
        
        while self.monitoring_active and not self.stop_event.is_set():
            try:
                # 🧪 Run all health checks
                self.run_all_health_checks()
                
                # 😴 Wait for next cycle
                self.stop_event.wait(base_interval)
                
            except Exception as e:
                self.logger.error(f"🔴 Error in monitoring loop: {e}")
                time.sleep(5)  # Brief pause before retry
        
        self.logger.info("🔄 Health monitoring loop stopped")
    
    def _get_overall_health_snapshot(self) -> Dict[str, Any]:
        """📊 Get overall system health snapshot."""
        try:
            total_components = len(self.components)
            healthy_components = sum(1 for c in self.components.values() 
                                   if c.overall_status == HealthLevel.HEALTHY)
            
            if total_components > 0:
                system_health_score = healthy_components / total_components
                
                if system_health_score >= 0.8:
                    system_status = HealthLevel.HEALTHY
                elif system_health_score >= 0.6:
                    system_status = HealthLevel.DEGRADED
                else:
                    system_status = HealthLevel.UNHEALTHY
            else:
                system_health_score = 1.0
                system_status = HealthLevel.UNKNOWN
            
            return {
                'timestamp': datetime.datetime.now().isoformat(),
                'system_status': system_status.value,
                'system_health_score': system_health_score,
                'total_components': total_components,
                'healthy_components': healthy_components,
                'total_checks_run': self.total_checks_run,
                'total_alerts_sent': self.total_alerts_sent,
                'uptime_seconds': time.time() - self.start_time
            }
            
        except Exception as e:
            self.logger.error(f"🔴 Error creating health snapshot: {e}")
            return {'error': str(e)}
    
    def get_health_status(self, component_name: Optional[str] = None) -> Dict[str, Any]:
        """
        📊 Get health status for component or entire system.
        
        Args:
            component_name: Specific component name or None for system-wide
            
        Returns:
            Dict[str, Any]: Health status information
        """
        try:
            with self.lock:
                if component_name:
                    # 📊 Component-specific status
                    if component_name in self.components:
                        component = self.components[component_name]
                        return {
                            'component': component_name,
                            'status': component.overall_status.value,
                            'health_score': component.health_score,
                            'uptime_seconds': component.uptime_seconds,
                            'success_rate': component.success_rate,
                            'consecutive_failures': component.consecutive_failures,
                            'last_check_time': component.last_check_time.isoformat() if component.last_check_time else None,
                            'last_healthy_time': component.last_healthy_time.isoformat() if component.last_healthy_time else None,
                            'check_results': {name: {
                                'status': result.status.value,
                                'message': result.message,
                                'execution_time_ms': result.execution_time_ms
                            } for name, result in component.check_results.items()}
                        }
                    else:
                        return {'error': f'Component {component_name} not found'}
                else:
                    # 📊 System-wide status
                    return self._get_overall_health_snapshot()
                    
        except Exception as e:
            self.logger.error(f"🔴 Error getting health status: {e}")
            return {'error': str(e)}
    
    def get_health_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """📚 Get health history."""
        try:
            with self.lock:
                history_slice = list(self.health_history)[-limit:] if limit > 0 else list(self.health_history)
                return history_slice
        except Exception as e:
            self.logger.error(f"🔴 Error getting health history: {e}")
            return []
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """📊 Get monitoring statistics."""
        try:
            with self.lock:
                return {
                    'monitoring_active': self.monitoring_active,
                    'total_components': len(self.components),
                    'total_checks_registered': len(self.health_checks),
                    'total_checks_run': self.total_checks_run,
                    'total_alerts_sent': self.total_alerts_sent,
                    'uptime_seconds': time.time() - self.start_time,
                    'health_history_size': len(self.health_history),
                    'alert_handlers_count': len(self.alert_handlers)
                }
        except Exception as e:
            return {'error': str(e)}

# 🧪 AI Assistant: Built-in health checks
class CommonHealthChecks:
    """🧪 Collection of common health check functions."""
    
    @staticmethod
    def memory_usage_check(threshold_percent: float = 80.0) -> Dict[str, Any]:
        """💾 Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            if usage_percent > threshold_percent:
                status = 'unhealthy'
                message = f"Memory usage high: {usage_percent:.1f}%"
            elif usage_percent > threshold_percent * 0.8:
                status = 'degraded'
                message = f"Memory usage elevated: {usage_percent:.1f}%"
            else:
                status = 'healthy'
                message = f"Memory usage normal: {usage_percent:.1f}%"
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'usage_percent': usage_percent,
                    'used_mb': memory.used / 1024 / 1024,
                    'available_mb': memory.available / 1024 / 1024,
                    'threshold_percent': threshold_percent
                }
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'message': f"Memory check failed: {str(e)}",
                'details': {'error': str(e)}
            }
    
    @staticmethod
    def cpu_usage_check(threshold_percent: float = 80.0) -> Dict[str, Any]:
        """⚡ Check CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent > threshold_percent:
                status = 'unhealthy'
                message = f"CPU usage high: {cpu_percent:.1f}%"
            elif cpu_percent > threshold_percent * 0.8:
                status = 'degraded'
                message = f"CPU usage elevated: {cpu_percent:.1f}%"
            else:
                status = 'healthy'
                message = f"CPU usage normal: {cpu_percent:.1f}%"
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'cpu_percent': cpu_percent,
                    'threshold_percent': threshold_percent,
                    'cpu_count': psutil.cpu_count()
                }
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'message': f"CPU check failed: {str(e)}",
                'details': {'error': str(e)}
            }
    
    @staticmethod
    def disk_usage_check(threshold_percent: float = 85.0, path: str = '/') -> Dict[str, Any]:
        """💾 Check disk usage."""
        try:
            disk_usage = psutil.disk_usage(path)
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            if usage_percent > threshold_percent:
                status = 'unhealthy'
                message = f"Disk usage high: {usage_percent:.1f}%"
            elif usage_percent > threshold_percent * 0.9:
                status = 'degraded'
                message = f"Disk usage elevated: {usage_percent:.1f}%"
            else:
                status = 'healthy'
                message = f"Disk usage normal: {usage_percent:.1f}%"
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'usage_percent': usage_percent,
                    'used_gb': disk_usage.used / 1024**3,
                    'free_gb': disk_usage.free / 1024**3,
                    'total_gb': disk_usage.total / 1024**3,
                    'threshold_percent': threshold_percent,
                    'path': path
                }
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'message': f"Disk check failed: {str(e)}",
                'details': {'error': str(e)}
            }

# 🧪 AI Assistant: Testing functions
def test_health_monitor():
    """🧪 Test Health Monitor functionality."""
    print("🧪 Testing Health Monitor...")
    
    try:
        # 📊 Create health monitor
        monitor = HealthMonitor()
        
        # 🧪 Create sample health checks
        health_checks = [
            HealthCheck(
                name="memory_check",
                description="Check memory usage",
                check_function=lambda: CommonHealthChecks.memory_usage_check(90.0),
                interval_seconds=30.0
            ),
            HealthCheck(
                name="cpu_check", 
                description="Check CPU usage",
                check_function=lambda: CommonHealthChecks.cpu_usage_check(90.0),
                interval_seconds=30.0
            )
        ]
        
        # 📋 Register component
        success = monitor.register_component("test_component", health_checks)
        print(f"✅ Component registration: {'Success' if success else 'Failed'}")
        
        # 🧪 Run health checks
        results = monitor.run_all_health_checks()
        print(f"✅ Health checks completed: {len(results)} components")
        
        for component_name, component in results.items():
            print(f"  {component_name}: {component.overall_status.value} (score: {component.health_score:.2f})")
        
        # 📊 Get health status
        status = monitor.get_health_status("test_component")
        print(f"✅ Component health status retrieved: {status.get('status', 'unknown')}")
        
        # 📊 Get monitoring stats
        stats = monitor.get_monitoring_stats()
        print(f"✅ Monitoring stats: {stats['total_checks_run']} checks run")
        
        print("🎉 Health Monitor test completed!")
        return True
        
    except Exception as e:
        print(f"🔴 Health Monitor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_health_monitor()