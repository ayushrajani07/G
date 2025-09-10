#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 G6 Platform Core - Main Business Logic and Orchestration
Restructured from multiple scattered files into clean, maintainable architecture.

This module contains the core platform logic extracted and consolidated from:
- main_application_complete.py
- g6_platform_main_FINAL_WORKING.py
- Various other platform files

Features:
- Clean separation of concerns
- Comprehensive error handling and resilience
- Thread-safe operations with proper synchronization
- Memory management and resource cleanup
- Structured logging throughout
- Signal handling for graceful shutdown
"""

import os
import sys
import time
import logging
import signal
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from pathlib import Path
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Platform imports
from ..config.manager import get_config_manager, ConfigurationManager
from ..monitoring.health import HealthMonitor
from ..monitoring.performance import PerformanceMonitor
from ..monitoring.metrics import MetricsSystem

logger = logging.getLogger(__name__)

@dataclass
class PlatformState:
    """Platform state tracking."""
    status: str = "initializing"  # initializing, running, stopping, stopped, error
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    cycles_completed: int = 0
    last_cycle_at: Optional[datetime] = None
    errors_count: int = 0
    uptime_seconds: float = 0.0
    
    def update_uptime(self):
        """Update uptime calculation."""
        if self.started_at:
            self.uptime_seconds = (datetime.now() - self.started_at).total_seconds()

@dataclass
class CollectionStats:
    """Data collection statistics."""
    total_options_processed: int = 0
    successful_collections: int = 0
    failed_collections: int = 0
    total_processing_time: float = 0.0
    average_cycle_time: float = 0.0
    last_cycle_stats: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate collection success rate."""
        total = self.successful_collections + self.failed_collections
        return (self.successful_collections / max(1, total)) * 100

class G6Platform:
    """
    🚀 Core G6 Platform - Main orchestrator for options data collection and analysis.
    
    This class consolidates the main application logic from multiple scattered files
    into a clean, maintainable architecture with proper separation of concerns.
    """
    
    def __init__(self, 
                 config_manager: Optional[ConfigurationManager] = None,
                 auto_start_monitoring: bool = True):
        """
        Initialize the G6 Platform.
        
        Args:
            config_manager: Configuration manager instance (creates new if None)
            auto_start_monitoring: Whether to automatically start monitoring systems
        """
        # Core components
        self.config_manager = config_manager or get_config_manager()
        self.config = self.config_manager.get_all()
        
        # State management
        self.state = PlatformState()
        self.stats = CollectionStats()
        self._shutdown_event = threading.Event()
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        
        # Monitoring systems
        self.health_monitor: Optional[HealthMonitor] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        self.metrics_system: Optional[MetricsSystem] = None
        
        # Core subsystems (will be initialized in start())
        self._api_provider = None
        self._collectors = {}
        self._storage_backends = {}
        self._analytics_engine = None
        
        # Threading and synchronization
        self._main_thread: Optional[threading.Thread] = None
        self._collection_lock = threading.RLock()
        
        # Signal handling
        self._setup_signal_handlers()
        
        # Initialize monitoring if requested
        if auto_start_monitoring:
            self._initialize_monitoring()
        
        logger.info("🚀 G6 Platform initialized successfully")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            logger.info(f"📶 Received signal {signal_name}, initiating graceful shutdown...")
            self.stop()
        
        # Register handlers for common termination signals
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination
        
        # Windows doesn't have SIGHUP
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)  # Reload config
    
    def _initialize_monitoring(self):
        """Initialize monitoring systems."""
        try:
            # Health monitoring
            self.health_monitor = HealthMonitor(
                check_interval=self.config.get('monitoring.health.check_interval', 60),
                alert_threshold=self.config.get('monitoring.health.alert_threshold', 3)
            )
            
            # Performance monitoring  
            self.performance_monitor = PerformanceMonitor(
                collection_interval=self.config.get('monitoring.performance.collection_interval', 30),
                retention_period=self.config.get('monitoring.performance.retention_hours', 24) * 3600
            )
            
            # Metrics system
            self.metrics_system = MetricsSystem(
                export_interval=self.config.get('monitoring.metrics.export_interval', 60),
                enabled_exporters=self.config.get('monitoring.metrics.exporters', ['console'])
            )
            
            # Add platform health checks
            self._register_health_checks()
            
            logger.info("📊 Monitoring systems initialized")
            
        except Exception as e:
            logger.error(f"🔴 Failed to initialize monitoring: {e}")
            # Continue without monitoring rather than fail
    
    def _register_health_checks(self):
        """Register platform-specific health checks."""
        if not self.health_monitor:
            return
        
        def check_api_connectivity():
            """Check if API provider is connected and responding."""
            if not self._api_provider:
                return {"status": "unhealthy", "message": "API provider not initialized"}
            
            try:
                # Perform a lightweight API check
                health = getattr(self._api_provider, 'health_check', lambda: True)()
                return {"status": "healthy" if health else "unhealthy"}
            except Exception as e:
                return {"status": "unhealthy", "error": str(e)}
        
        def check_storage_backends():
            """Check storage backend health."""
            if not self._storage_backends:
                return {"status": "unhealthy", "message": "No storage backends initialized"}
            
            healthy_backends = 0
            for name, backend in self._storage_backends.items():
                try:
                    if hasattr(backend, 'health_check') and backend.health_check():
                        healthy_backends += 1
                except Exception:
                    pass
            
            total_backends = len(self._storage_backends)
            if healthy_backends == total_backends:
                return {"status": "healthy", "backends": f"{healthy_backends}/{total_backends}"}
            elif healthy_backends > 0:
                return {"status": "degraded", "backends": f"{healthy_backends}/{total_backends}"}
            else:
                return {"status": "unhealthy", "backends": f"{healthy_backends}/{total_backends}"}
        
        def check_thread_pool():
            """Check thread pool health."""
            if not self._thread_pool:
                return {"status": "unhealthy", "message": "Thread pool not initialized"}
            
            if self._thread_pool._shutdown:
                return {"status": "unhealthy", "message": "Thread pool is shutdown"}
            
            # Check for thread starvation
            active_threads = getattr(self._thread_pool, '_threads', set())
            max_workers = getattr(self._thread_pool, '_max_workers', 0)
            
            return {
                "status": "healthy",
                "active_threads": len(active_threads),
                "max_workers": max_workers
            }
        
        # Register health checks
        self.health_monitor.add_check("api_connectivity", check_api_connectivity, interval=30)
        self.health_monitor.add_check("storage_backends", check_storage_backends, interval=60)
        self.health_monitor.add_check("thread_pool", check_thread_pool, interval=120)
    
    def start(self) -> bool:
        """
        Start the G6 Platform.
        
        Returns:
            True if startup was successful, False otherwise
        """
        try:
            logger.info("🚀 Starting G6 Platform...")
            self.state.status = "initializing"
            self.state.started_at = datetime.now()
            
            # Initialize core components
            if not self._initialize_core_components():
                return False
            
            # Start monitoring systems
            if not self._start_monitoring_systems():
                logger.warning("⚠️ Some monitoring systems failed to start")
            
            # Start main collection thread
            self._main_thread = threading.Thread(
                target=self._main_collection_loop,
                name="G6-MainCollection",
                daemon=False
            )
            self._main_thread.start()
            
            self.state.status = "running"
            logger.info("✅ G6 Platform started successfully")
            return True
            
        except Exception as e:
            logger.error(f"🔴 Failed to start G6 Platform: {e}")
            self.state.status = "error"
            return False
    
    def _initialize_core_components(self) -> bool:
        """Initialize core platform components."""
        try:
            # Initialize thread pool
            max_workers = self.config.get('data_collection.performance.max_workers', 4)
            self._thread_pool = ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix="G6-Worker"
            )
            
            # Initialize API provider
            if not self._initialize_api_provider():
                return False
            
            # Initialize collectors
            if not self._initialize_collectors():
                return False
            
            # Initialize storage backends
            if not self._initialize_storage():
                return False
            
            # Initialize analytics engine
            if not self._initialize_analytics():
                logger.warning("⚠️ Analytics engine initialization failed")
            
            logger.info("✅ Core components initialized")
            return True
            
        except Exception as e:
            logger.error(f"🔴 Core component initialization failed: {e}")
            return False
    
    def _initialize_api_provider(self) -> bool:
        """Initialize API data provider."""
        try:
            from ..api.kite_provider import KiteDataProvider
            
            # Get API credentials from config
            api_config = self.config.get('api.kite', {})
            api_key = self.config_manager.get('api.kite.api_key') or os.getenv('KITE_API_KEY')
            access_token = self.config_manager.get('api.kite.access_token') or os.getenv('KITE_ACCESS_TOKEN')
            
            if not api_key or not access_token:
                logger.error("🔴 Kite API credentials not found in config or environment")
                return False
            
            self._api_provider = KiteDataProvider(
                api_key=api_key,
                access_token=access_token,
                **api_config
            )
            
            logger.info("✅ API provider initialized")
            return True
            
        except ImportError as e:
            logger.error(f"🔴 Failed to import API provider: {e}")
            return False
        except Exception as e:
            logger.error(f"🔴 API provider initialization failed: {e}")
            return False
    
    def _initialize_collectors(self) -> bool:
        """Initialize data collectors."""
        try:
            from ..collectors.atm_collector import ATMOptionsCollector
            from ..collectors.overview_collector import OverviewCollector
            
            # ATM Options Collector
            atm_config = self.config.get('data_collection.atm_options', {})
            self._collectors['atm_options'] = ATMOptionsCollector(
                api_provider=self._api_provider,
                **atm_config
            )
            
            # Overview Collector (if enabled)
            if self.config.get('data_collection.overview.enabled', True):
                overview_config = self.config.get('data_collection.overview', {})
                self._collectors['overview'] = OverviewCollector(
                    api_provider=self._api_provider,
                    **overview_config
                )
            
            logger.info(f"✅ Initialized {len(self._collectors)} collectors")
            return True
            
        except ImportError as e:
            logger.error(f"🔴 Failed to import collectors: {e}")
            return False
        except Exception as e:
            logger.error(f"🔴 Collectors initialization failed: {e}")
            return False
    
    def _initialize_storage(self) -> bool:
        """Initialize storage backends."""
        try:
            storage_config = self.config.get('storage', {})
            
            # CSV Storage
            if storage_config.get('csv', {}).get('enabled', True):
                from ..storage.csv_sink import CSVSink
                csv_config = storage_config.get('csv', {})
                self._storage_backends['csv'] = CSVSink(**csv_config)
            
            # InfluxDB Storage
            if storage_config.get('influxdb', {}).get('enabled', False):
                from ..storage.influxdb_sink import InfluxDBSink
                influx_config = storage_config.get('influxdb', {})
                self._storage_backends['influxdb'] = InfluxDBSink(**influx_config)
            
            if not self._storage_backends:
                logger.error("🔴 No storage backends initialized")
                return False
            
            logger.info(f"✅ Initialized {len(self._storage_backends)} storage backends")
            return True
            
        except ImportError as e:
            logger.error(f"🔴 Failed to import storage backends: {e}")
            return False
        except Exception as e:
            logger.error(f"🔴 Storage initialization failed: {e}")
            return False
    
    def _initialize_analytics(self) -> bool:
        """Initialize analytics engine."""
        try:
            from ..analytics.engine import AnalyticsEngine
            
            analytics_config = self.config.get('analytics', {})
            self._analytics_engine = AnalyticsEngine(**analytics_config)
            
            logger.info("✅ Analytics engine initialized")
            return True
            
        except ImportError as e:
            logger.warning(f"⚠️ Analytics engine not available: {e}")
            return False
        except Exception as e:
            logger.error(f"🔴 Analytics engine initialization failed: {e}")
            return False
    
    def _start_monitoring_systems(self) -> bool:
        """Start monitoring systems."""
        success = True
        
        try:
            if self.health_monitor:
                self.health_monitor.start()
                logger.info("✅ Health monitor started")
        except Exception as e:
            logger.error(f"🔴 Failed to start health monitor: {e}")
            success = False
        
        try:
            if self.performance_monitor:
                self.performance_monitor.start()
                logger.info("✅ Performance monitor started")
        except Exception as e:
            logger.error(f"🔴 Failed to start performance monitor: {e}")
            success = False
        
        try:
            if self.metrics_system:
                self.metrics_system.start()
                logger.info("✅ Metrics system started")
        except Exception as e:
            logger.error(f"🔴 Failed to start metrics system: {e}")
            success = False
        
        return success
    
    def _main_collection_loop(self):
        """Main data collection loop."""
        logger.info("🔄 Starting main collection loop")
        
        while not self._shutdown_event.is_set():
            try:
                cycle_start = time.time()
                
                # Run collection cycle
                cycle_result = self._run_collection_cycle()
                
                # Update statistics
                cycle_time = time.time() - cycle_start
                self._update_cycle_stats(cycle_result, cycle_time)
                
                # Wait for next cycle
                collection_interval = self.config.get('market.collection_interval', 30)
                if not self._shutdown_event.wait(collection_interval):
                    continue  # Normal timeout, continue with next cycle
                else:
                    break  # Shutdown requested
                
            except Exception as e:
                logger.error(f"🔴 Collection cycle error: {e}")
                self.state.errors_count += 1
                
                # Exponential backoff on errors
                error_backoff = min(300, 5 * (2 ** min(5, self.state.errors_count)))
                logger.info(f"⏱️ Backing off for {error_backoff} seconds after error")
                
                if self._shutdown_event.wait(error_backoff):
                    break  # Shutdown requested during backoff
        
        logger.info("🔄 Main collection loop stopped")
    
    def _run_collection_cycle(self) -> Dict[str, Any]:
        """Run a single collection cycle."""
        cycle_result = {
            'success': True,
            'indices_processed': 0,
            'total_options': 0,
            'errors': [],
            'processing_times': {}
        }
        
        try:
            with self._collection_lock:
                # Get market indices to process
                indices = self.config.get('market.indices', ['NIFTY', 'BANKNIFTY'])
                
                logger.info(f"🔄 Starting cycle {self.state.cycles_completed + 1} for {len(indices)} indices")
                
                # Process each index
                for index in indices:
                    try:
                        index_start = time.time()
                        
                        # Collect options data for this index
                        index_result = self._process_index(index)
                        
                        # Update cycle result
                        if index_result['success']:
                            cycle_result['indices_processed'] += 1
                            cycle_result['total_options'] += index_result.get('options_count', 0)
                        else:
                            cycle_result['errors'].append({
                                'index': index,
                                'error': index_result.get('error', 'Unknown error')
                            })
                        
                        # Track processing time
                        processing_time = time.time() - index_start
                        cycle_result['processing_times'][index] = processing_time
                        
                        logger.info(f"✅ {index} processed in {processing_time:.2f}s")
                        
                    except Exception as e:
                        logger.error(f"🔴 Error processing {index}: {e}")
                        cycle_result['errors'].append({
                            'index': index,
                            'error': str(e)
                        })
                        cycle_result['success'] = False
                
                # Check if cycle was successful
                if cycle_result['errors']:
                    cycle_result['success'] = len(cycle_result['errors']) < len(indices)
                
                return cycle_result
                
        except Exception as e:
            logger.error(f"🔴 Collection cycle failed: {e}")
            cycle_result['success'] = False
            cycle_result['errors'].append({'cycle': str(e)})
            return cycle_result
    
    def _process_index(self, index: str) -> Dict[str, Any]:
        """Process options data for a single index."""
        result = {'success': False, 'options_count': 0, 'error': None}
        
        try:
            # Get ATM options collector
            atm_collector = self._collectors.get('atm_options')
            if not atm_collector:
                raise ValueError("ATM options collector not available")
            
            # Collect options data
            options_data = atm_collector.collect_atm_options(
                index_name=index,
                include_greeks=self.config.get('data_collection.options.include_greeks', True),
                include_market_depth=self.config.get('data_collection.options.include_market_depth', False)
            )
            
            if not options_data:
                raise ValueError(f"No options data received for {index}")
            
            # Store the data
            self._store_options_data(index, options_data)
            
            # Update analytics if available
            if self._analytics_engine:
                try:
                    self._analytics_engine.process_options_data(index, options_data)
                except Exception as e:
                    logger.warning(f"⚠️ Analytics processing failed for {index}: {e}")
            
            result['success'] = True
            result['options_count'] = len(options_data) if isinstance(options_data, list) else 1
            
        except Exception as e:
            logger.error(f"🔴 Failed to process {index}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _store_options_data(self, index: str, options_data: Any):
        """Store options data using configured storage backends."""
        for backend_name, backend in self._storage_backends.items():
            try:
                if hasattr(backend, 'store_options_data'):
                    backend.store_options_data(index, options_data)
                elif hasattr(backend, 'write'):
                    backend.write(index, options_data)
                else:
                    logger.warning(f"⚠️ Storage backend {backend_name} has no store method")
            except Exception as e:
                logger.error(f"🔴 Failed to store data in {backend_name}: {e}")
    
    def _update_cycle_stats(self, cycle_result: Dict[str, Any], cycle_time: float):
        """Update collection statistics."""
        self.state.cycles_completed += 1
        self.state.last_cycle_at = datetime.now()
        self.state.update_uptime()
        
        if cycle_result['success']:
            self.stats.successful_collections += 1
        else:
            self.stats.failed_collections += 1
            self.state.errors_count += len(cycle_result.get('errors', []))
        
        self.stats.total_options_processed += cycle_result.get('total_options', 0)
        self.stats.total_processing_time += cycle_time
        
        # Calculate average cycle time
        total_collections = self.stats.successful_collections + self.stats.failed_collections
        if total_collections > 0:
            self.stats.average_cycle_time = self.stats.total_processing_time / total_collections
        
        self.stats.last_cycle_stats = cycle_result.copy()
        
        logger.info(f"📊 Cycle {self.state.cycles_completed} completed in {cycle_time:.2f}s "
                   f"({cycle_result['indices_processed']}/{len(cycle_result.get('processing_times', {}))} indices)")
    
    def stop(self, timeout: float = 30.0) -> bool:
        """
        Stop the G6 Platform gracefully.
        
        Args:
            timeout: Maximum time to wait for graceful shutdown
            
        Returns:
            True if stopped gracefully, False if forced
        """
        logger.info("🛑 Stopping G6 Platform...")
        self.state.status = "stopping"
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for main thread to complete
        if self._main_thread and self._main_thread.is_alive():
            logger.info("⏱️ Waiting for main collection loop to stop...")
            self._main_thread.join(timeout=timeout)
            
            if self._main_thread.is_alive():
                logger.warning("⚠️ Main collection loop did not stop gracefully")
        
        # Stop monitoring systems
        self._stop_monitoring_systems()
        
        # Shutdown thread pool
        if self._thread_pool:
            logger.info("⏱️ Shutting down thread pool...")
            self._thread_pool.shutdown(wait=True, timeout=timeout/2)
        
        # Close storage backends
        self._close_storage_backends()
        
        self.state.status = "stopped"
        self.state.stopped_at = datetime.now()
        
        logger.info("✅ G6 Platform stopped successfully")
        return True
    
    def _stop_monitoring_systems(self):
        """Stop monitoring systems."""
        for monitor, name in [(self.health_monitor, "health"), 
                             (self.performance_monitor, "performance"),
                             (self.metrics_system, "metrics")]:
            if monitor:
                try:
                    monitor.stop()
                    logger.info(f"✅ {name.title()} monitor stopped")
                except Exception as e:
                    logger.error(f"🔴 Failed to stop {name} monitor: {e}")
    
    def _close_storage_backends(self):
        """Close storage backends."""
        for name, backend in self._storage_backends.items():
            try:
                if hasattr(backend, 'close'):
                    backend.close()
                elif hasattr(backend, 'shutdown'):
                    backend.shutdown()
                logger.info(f"✅ {name} storage backend closed")
            except Exception as e:
                logger.error(f"🔴 Failed to close {name} storage: {e}")
    
    # Public API methods
    
    def get_status(self) -> Dict[str, Any]:
        """Get current platform status."""
        self.state.update_uptime()
        
        return {
            'status': self.state.status,
            'uptime_seconds': self.state.uptime_seconds,
            'cycles_completed': self.state.cycles_completed,
            'success_rate': self.stats.success_rate,
            'total_options_processed': self.stats.total_options_processed,
            'average_cycle_time': self.stats.average_cycle_time,
            'errors_count': self.state.errors_count,
            'last_cycle_at': self.state.last_cycle_at.isoformat() if self.state.last_cycle_at else None,
            'components': {
                'api_provider': bool(self._api_provider),
                'collectors': len(self._collectors),
                'storage_backends': len(self._storage_backends),
                'analytics_engine': bool(self._analytics_engine),
                'monitoring': {
                    'health': bool(self.health_monitor),
                    'performance': bool(self.performance_monitor),
                    'metrics': bool(self.metrics_system)
                }
            }
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get platform health information."""
        if self.health_monitor:
            return self.health_monitor.get_health_summary()
        else:
            return {'status': 'unknown', 'message': 'Health monitoring not available'}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get platform metrics."""
        if self.metrics_system:
            return self.metrics_system.get_all_metrics()
        else:
            return {'error': 'Metrics system not available'}
    
    def reload_config(self) -> bool:
        """Reload configuration."""
        try:
            if self.config_manager.reload():
                self.config = self.config_manager.get_all()
                logger.info("✅ Configuration reloaded successfully")
                return True
            else:
                logger.error("🔴 Configuration reload failed")
                return False
        except Exception as e:
            logger.error(f"🔴 Configuration reload error: {e}")
            return False