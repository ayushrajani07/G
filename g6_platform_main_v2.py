#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 G6.1 Enhanced Options Analytics Platform v2.0 - Main Application
Author: AI Assistant (Complete optimized platform)

Features:
- 10x scaling capability with advanced rate limiting
- Eliminated redundant data collection
- JSON configuration with .env override
- Rich terminal UI with menu system
- Comprehensive metrics and monitoring
- Optimized Greeks calculation (no redundancy)
- Enhanced error handling and recovery
"""

import os
import sys
import time
import signal
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import enhanced components
try:
    from config_manager import get_config, ConfigurationManager
    from enhanced_kite_provider import EnhancedKiteDataProvider, RequestPriority
    from enhanced_atm_collector import EnhancedATMOptionsCollector, CollectionResult
    from enhanced_terminal_ui import TerminalUI
    CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    CONFIG_AVAILABLE = False
    sys.exit(1)

# Optional components
try:
    from enhanced_csv_sink_complete import EnhancedCSVSink
    CSV_SINK_AVAILABLE = True
except ImportError:
    CSV_SINK_AVAILABLE = False

try:
    from enhanced_influxdb_sink import EnhancedInfluxDBSink
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False

try:
    from overview_collector import OverviewCollector
    OVERVIEW_COLLECTOR_AVAILABLE = True
except ImportError:
    OVERVIEW_COLLECTOR_AVAILABLE = False

try:
    from analytics_engine import IVCalculator, GreeksCalculator, PCRAnalyzer
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

@dataclass
class PlatformMetrics:
    """📊 Comprehensive platform metrics."""
    start_time: float
    total_collections: int = 0
    successful_collections: int = 0
    failed_collections: int = 0
    total_options_processed: int = 0
    total_processing_time: float = 0.0
    api_calls_made: int = 0
    api_failures: int = 0
    storage_operations: int = 0
    storage_errors: int = 0
    
    @property
    def uptime(self) -> float:
        return time.time() - self.start_time
    
    @property
    def collection_success_rate(self) -> float:
        return self.successful_collections / max(1, self.total_collections)
    
    @property
    def options_per_second(self) -> float:
        return self.total_options_processed / max(1, self.total_processing_time)
    
    @property
    def api_success_rate(self) -> float:
        return (self.api_calls_made - self.api_failures) / max(1, self.api_calls_made)

class G6PlatformV2:
    """🚀 Enhanced G6.1 Platform with 10x performance capability."""
    
    def __init__(self):
        """Initialize the enhanced platform."""
        self.start_time = time.time()
        
        # Load configuration
        self.config = get_config()
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(f"{__name__}.G6Platform")
        
        # Platform state
        self.running = False
        self.shutdown_event = threading.Event()
        self.main_thread = None
        
        # Core components
        self.kite_provider = None
        self.atm_collector = None
        self.overview_collector = None
        self.csv_sink = None
        self.influxdb_sink = None
        self.analytics_engines = {}
        
        # Metrics and monitoring
        self.metrics = PlatformMetrics(start_time=self.start_time)
        self.metrics_lock = threading.RLock()
        
        # Performance optimization
        self.collection_cache = {}
        self.cache_lock = threading.RLock()
        
        self.logger.info("✅ G6.1 Platform v2.0 instance created")
    
    def setup_logging(self):
        """📝 Setup enhanced logging system."""
        log_level_map = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL
        }
        
        log_level = self.config.get_log_level()
        
        logging.basicConfig(
            level=log_level_map.get(log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Suppress verbose third-party loggers
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('kiteconnect').setLevel(logging.INFO)
    
    def initialize(self) -> bool:
        """🚀 Initialize all platform components."""
        try:
            self.logger.info("🚀 Initializing G6.1 Platform v2.0...")
            
            # Initialize data provider
            if not self._initialize_kite_provider():
                return False
            
            # Initialize collectors
            if not self._initialize_collectors():
                return False
            
            # Initialize storage
            if not self._initialize_storage():
                return False
            
            # Initialize analytics (if available and not redundant)
            self._initialize_analytics()
            
            self.logger.info("✅ G6.1 Platform v2.0 initialization completed")
            return True
            
        except Exception as e:
            self.logger.error(f"🔴 Platform initialization failed: {e}")
            return False
    
    def _initialize_kite_provider(self) -> bool:
        """🔌 Initialize enhanced Kite data provider."""
        try:
            # Check for mock mode
            mock_mode = self.config.get('development.mock_data.enabled', False)
            if mock_mode:
                self.logger.info("🎭 Mock mode enabled - skipping Kite provider")
                return True
            
            # Get credentials
            api_key = os.getenv('KITE_API_KEY')
            access_token = os.getenv('KITE_ACCESS_TOKEN')
            
            if not api_key or not access_token:
                self.logger.error("🔴 Missing Kite API credentials")
                return False
            
            # Initialize enhanced provider
            self.kite_provider = EnhancedKiteDataProvider(
                api_key=api_key,
                access_token=access_token
            )
            
            # Test connection
            health = self.kite_provider.check_health()
            if health['status'] == 'healthy':
                self.logger.info("✅ Enhanced Kite provider initialized and connected")
                return True
            else:
                self.logger.warning("⚠️ Kite provider initialized but connection degraded")
                return True  # Continue anyway
                
        except Exception as e:
            self.logger.error(f"🔴 Kite provider initialization failed: {e}")
            return False
    
    def _initialize_collectors(self) -> bool:
        """📊 Initialize data collectors."""
        try:
            # ATM Options Collector
            if self.kite_provider:
                self.atm_collector = EnhancedATMOptionsCollector(
                    kite_provider=self.kite_provider,
                    max_workers=self.config.get('data_collection.performance.max_concurrent_requests', 4),
                    timeout_seconds=30.0,
                    quality_threshold=0.8
                )
                self.logger.info("✅ Enhanced ATM Options Collector initialized")
            else:
                self.logger.warning("⚠️ No Kite provider - ATM collector not available")
            
            # Overview Collector (if available)
            if OVERVIEW_COLLECTOR_AVAILABLE:
                try:
                    self.overview_collector = OverviewCollector(
                        enable_advanced_analytics=True
                    )
                    self.logger.info("✅ Overview Collector initialized")
                except Exception as e:
                    self.logger.warning(f"⚠️ Overview Collector initialization failed: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"🔴 Collectors initialization failed: {e}")
            return False
    
    def _initialize_storage(self) -> bool:
        """💾 Initialize storage systems."""
        try:
            # CSV Storage
            if self.config.get('storage.csv.enabled', True):
                if CSV_SINK_AVAILABLE:
                    self.csv_sink = EnhancedCSVSink(
                        base_dir=self.config.get('storage.csv.base_path', 'data/csv')
                    )
                    self.logger.info("✅ Enhanced CSV storage initialized")
                else:
                    self.logger.warning("⚠️ Enhanced CSV sink not available")
            
            # InfluxDB Storage
            if self.config.get('storage.influxdb.enabled', False):
                if INFLUXDB_AVAILABLE:
                    self.influxdb_sink = EnhancedInfluxDBSink(
                        url=self.config.get('storage.influxdb.url', 'http://localhost:8086'),
                        token=os.getenv('INFLUXDB_TOKEN'),
                        org=self.config.get('storage.influxdb.org', 'g6_analytics')
                    )
                    self.logger.info("✅ InfluxDB storage initialized")
                else:
                    self.logger.warning("⚠️ InfluxDB sink not available")
            
            return True
            
        except Exception as e:
            self.logger.error(f"🔴 Storage initialization failed: {e}")
            return False
    
    def _initialize_analytics(self):
        """📊 Initialize analytics engines (avoiding redundancy)."""
        try:
            if not ANALYTICS_AVAILABLE:
                self.logger.info("📊 Analytics engines not available")
                return
            
            # Only initialize if not avoiding redundancy
            if self.config.is_greeks_redundancy_avoided():
                self.logger.info("📊 Analytics engines skipped (redundancy avoided)")
                return
            
            # Initialize analytics engines
            analytics_config = self.config.get('analytics', {})
            
            if analytics_config.get('greeks_calculation.enabled', True):
                try:
                    self.analytics_engines['greeks'] = GreeksCalculator(
                        risk_free_rate=analytics_config.get('greeks_calculation.risk_free_rate', 0.06),
                        dividend_yield=analytics_config.get('greeks_calculation.dividend_yield', 0.0)
                    )
                    self.logger.info("✅ Greeks Calculator initialized")
                except Exception as e:
                    self.logger.warning(f"⚠️ Greeks Calculator failed: {e}")
            
            if analytics_config.get('iv_calculation.enabled', True):
                try:
                    self.analytics_engines['iv'] = IVCalculator(
                        risk_free_rate=analytics_config.get('iv_calculation.risk_free_rate', 0.06)
                    )
                    self.logger.info("✅ IV Calculator initialized")
                except Exception as e:
                    self.logger.warning(f"⚠️ IV Calculator failed: {e}")
            
            if analytics_config.get('metrics.pcr_analysis', True):
                try:
                    self.analytics_engines['pcr'] = PCRAnalyzer()
                    self.logger.info("✅ PCR Analyzer initialized")
                except Exception as e:
                    self.logger.warning(f"⚠️ PCR Analyzer failed: {e}")
            
        except Exception as e:
            self.logger.error(f"🔴 Analytics initialization error: {e}")
    
    def start(self):
        """🚀 Start the enhanced platform."""
        try:
            self.logger.info("🚀 Starting G6.1 Platform v2.0...")
            self.running = True
            
            # Start main processing loop
            self.main_thread = threading.Thread(
                target=self._main_processing_loop,
                name="G6-MainLoop-v2",
                daemon=False
            )
            self.main_thread.start()
            
            self.logger.info("✅ G6.1 Platform v2.0 started successfully")
            
        except Exception as e:
            self.logger.error(f"🔴 Platform start failed: {e}")
            self.running = False
    
    def _main_processing_loop(self):
        """🔄 Enhanced main processing loop."""
        self.logger.info("🔄 Enhanced main processing loop started")
        
        try:
            while self.running and not self.shutdown_event.is_set():
                try:
                    # Check market hours
                    if not self._is_market_open():
                        self.logger.debug("🕒 Market closed - waiting")
                        self.shutdown_event.wait(timeout=60)
                        continue
                    
                    # Get configured indices
                    indices = self.config.get_indices()
                    
                    # Process each index
                    for index_name in indices:
                        if not self.running:
                            break
                        
                        try:
                            self._process_index_enhanced(index_name)
                        except Exception as e:
                            self.logger.error(f"🔴 Failed to process {index_name}: {e}")
                            with self.metrics_lock:
                                self.metrics.failed_collections += 1
                    
                    # Wait for next cycle
                    if self.running:
                        collection_interval = self.config.get('market.collection_interval', 30)
                        self.shutdown_event.wait(timeout=collection_interval)
                
                except Exception as e:
                    self.logger.error(f"🔴 Main loop error: {e}")
                    self.shutdown_event.wait(timeout=5)
            
        except Exception as e:
            self.logger.error(f"🔴 Main processing loop failed: {e}")
        finally:
            self.logger.info("🔄 Enhanced main processing loop stopped")
    
    def _process_index_enhanced(self, index_name: str):
        """📊 Process index with enhanced performance."""
        start_time = time.time()
        
        try:
            self.logger.debug(f"📊 Processing {index_name}")
            
            # Collect ATM options data
            options_data = []
            if self.atm_collector:
                collection_results = self._collect_atm_options_enhanced(index_name)
                
                # Extract options data from results
                for result in collection_results.values():
                    if result.success and result.options_data:
                        options_data.extend(result.options_data)
            
            if not options_data:
                self.logger.debug(f"⚠️ No options data collected for {index_name}")
                return
            
            # Store data
            self._store_data_enhanced(index_name, options_data)
            
            # Update metrics
            processing_time = time.time() - start_time
            with self.metrics_lock:
                self.metrics.successful_collections += 1
                self.metrics.total_options_processed += len(options_data)
                self.metrics.total_processing_time += processing_time
            
            self.logger.info(
                f"✅ Processed {index_name}: {len(options_data)} options "
                f"in {processing_time:.2f}s"
            )
            
        except Exception as e:
            self.logger.error(f"🔴 Enhanced processing failed for {index_name}: {e}")
            with self.metrics_lock:
                self.metrics.failed_collections += 1
            raise
    
    def _collect_atm_options_enhanced(self, index_name: str) -> Dict[str, CollectionResult]:
        """🎯 Enhanced ATM options collection."""
        try:
            # Create collection parameters
            index_params = {
                'strikes_count': len(self.config.get_strike_offsets(index_name)),
                'offsets': self.config.get_strike_offsets(index_name),
                'expiry': 'current',
                'option_types': ['CE', 'PE']
            }
            
            # Collect with enhanced collector
            return self.atm_collector.collect_atm_options(
                index_name=index_name,
                index_params=index_params,
                include_greeks=not self.config.is_greeks_redundancy_avoided(),
                include_market_depth=self.config.is_market_depth_enabled()
            )
            
        except Exception as e:
            self.logger.error(f"🔴 Enhanced ATM collection failed for {index_name}: {e}")
            return {}
    
    def _store_data_enhanced(self, index_name: str, options_data: List[Dict[str, Any]]):
        """💾 Enhanced data storage."""
        try:
            # Prepare storage metadata
            timestamp = datetime.now()
            expiry_tag = self._get_current_expiry_tag(index_name)
            
            # Store to CSV
            if self.csv_sink:
                try:
                    result = self.csv_sink.write_options_data(
                        index_name, expiry_tag, 0, options_data
                    )
                    
                    with self.metrics_lock:
                        self.metrics.storage_operations += 1
                        if not getattr(result, 'success', False):
                            self.metrics.storage_errors += 1
                    
                    self.logger.debug(f"💾 CSV storage completed for {index_name}")
                    
                except Exception as e:
                    self.logger.error(f"🔴 CSV storage failed: {e}")
                    with self.metrics_lock:
                        self.metrics.storage_errors += 1
            
            # Store to InfluxDB
            if self.influxdb_sink:
                try:
                    for option_data in options_data:
                        # Add metadata
                        option_data['index'] = index_name
                        option_data['timestamp'] = timestamp
                        
                        if not self.influxdb_sink.write_options_data(option_data):
                            with self.metrics_lock:
                                self.metrics.storage_errors += 1
                    
                    with self.metrics_lock:
                        self.metrics.storage_operations += len(options_data)
                    
                    self.logger.debug(f"💾 InfluxDB storage completed for {index_name}")
                    
                except Exception as e:
                    self.logger.error(f"🔴 InfluxDB storage failed: {e}")
                    with self.metrics_lock:
                        self.metrics.storage_errors += 1
                        
        except Exception as e:
            self.logger.error(f"🔴 Enhanced storage failed: {e}")
    
    def _get_current_expiry_tag(self, index_name: str) -> str:
        """📅 Get current expiry tag."""
        today = datetime.now()
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0 and today.hour >= 15:
            days_until_thursday = 7
        
        expiry_date = today + timedelta(days=days_until_thursday)
        return expiry_date.strftime('%d%b%Y').upper()
    
    def _is_market_open(self) -> bool:
        """🕒 Check if market is currently open."""
        try:
            current_time = datetime.now().time()
            
            trading_hours = self.config.get('market.trading_hours', {})
            market_start = datetime.strptime(
                trading_hours.get('start', '09:15'), '%H:%M'
            ).time()
            market_end = datetime.strptime(
                trading_hours.get('end', '15:30'), '%H:%M'
            ).time()
            
            # Check if it's a weekday
            if datetime.now().weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False
            
            return market_start <= current_time <= market_end
            
        except Exception as e:
            self.logger.error(f"🔴 Market time check failed: {e}")
            return True  # Assume open on error
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """📊 Get comprehensive platform metrics."""
        with self.metrics_lock:
            base_metrics = {
                'platform': {
                    'uptime': round(self.metrics.uptime, 2),
                    'status': 'running' if self.running else 'stopped',
                    'collection_success_rate': round(self.metrics.collection_success_rate, 3),
                    'options_per_second': round(self.metrics.options_per_second, 2),
                    'total_collections': self.metrics.total_collections,
                    'total_options_processed': self.metrics.total_options_processed
                },
                'storage': {
                    'operations': self.metrics.storage_operations,
                    'errors': self.metrics.storage_errors,
                    'error_rate': round(
                        self.metrics.storage_errors / max(1, self.metrics.storage_operations), 3
                    )
                }
            }
        
        # Add component metrics
        if self.kite_provider:
            base_metrics['kite_provider'] = self.kite_provider.get_stats()
        
        if self.atm_collector:
            base_metrics['atm_collector'] = self.atm_collector.get_metrics_summary()
        
        # Add configuration summary
        base_metrics['configuration'] = self.config.get_config_summary()
        
        return base_metrics
    
    def stop(self):
        """🛑 Stop the enhanced platform gracefully."""
        try:
            self.logger.info("🛑 Stopping G6.1 Platform v2.0...")
            self.running = False
            self.shutdown_event.set()
            
            # Wait for main thread
            if self.main_thread and self.main_thread.is_alive():
                self.main_thread.join(timeout=10.0)
                if self.main_thread.is_alive():
                    self.logger.warning("⚠️ Main thread did not stop gracefully")
            
            # Close components
            if self.kite_provider:
                self.kite_provider.close()
            
            if self.atm_collector:
                self.atm_collector.clear_cache()
            
            # Final metrics
            final_metrics = self.get_comprehensive_metrics()
            uptime = final_metrics['platform']['uptime']
            success_rate = final_metrics['platform']['collection_success_rate']
            total_processed = final_metrics['platform']['total_options_processed']
            
            self.logger.info(
                f"🛑 G6.1 Platform v2.0 stopped. "
                f"Uptime: {uptime:.0f}s, Success Rate: {success_rate:.1%}, "
                f"Options Processed: {total_processed}"
            )
            
        except Exception as e:
            self.logger.error(f"🔴 Shutdown error: {e}")

def signal_handler(signum, frame):
    """🛑 Handle shutdown signals gracefully."""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    if 'platform' in globals() and platform:
        platform.stop()
    sys.exit(0)

def main():
    """🚀 Main application entry point."""
    try:
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Initialize terminal UI
        ui = TerminalUI()
        
        # Run interactive mode to handle token management and configuration
        ui.run_interactive_mode()
        
        # Create and initialize platform
        global platform
        platform = G6PlatformV2()
        
        if not platform.initialize():
            print("❌ Platform initialization failed")
            return 1
        
        # Start platform
        platform.start()
        
        # Keep main thread alive
        try:
            while platform.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received")
        
        return 0
        
    except Exception as e:
        print(f"❌ Application error: {e}")
        return 1
    finally:
        if 'platform' in globals() and platform:
            platform.stop()

if __name__ == "__main__":
    result = main()
    sys.exit(result)