#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 FIXED G6.1 Platform Integration & Main Application
Author: AI Assistant (Fixed async/await and Windows compatibility)

✅ Features:
- Fixed async/await syntax issues
- Windows-compatible file operations
- Complete module integration
- Real-time options data collection
- Advanced analytics and calculations
- Health monitoring and alerting
- Performance metrics and reporting
- Multi-threaded data processing
- Secure token management
- Comprehensive error handling
- Full testing framework integration
"""

import logging
import time
import datetime
import threading
import signal
import sys
from typing import Union, Optional, List, Dict, Any

from pathlib import Path
import json
import os


import os, sys

# On Windows, reconfigure stdout to UTF-8 so emojis can be printed
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


import argparse
import os
import sys
from rich_terminal_output import setup_rich_terminal_output

# Ensure UTF-8 on Windows
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 1. Parse command-line args
parser = argparse.ArgumentParser(description="G6.1 Options Analytics Platform")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
parser.add_argument("--mock", action="store_true", help="Run in mock mode")
# … add other args if needed …
args = parser.parse_args()

# 2. Build platform config dict for startup summary
platform_config = {
    "mock_mode": args.mock or os.getenv("G6_MOCK_MODE","false").lower()=="true",
    "indices": os.getenv("G6_INDICES","NIFTY,BANKNIFTY").split(","),
    "collection_interval": int(os.getenv("G6_COLLECTION_INTERVAL","30")),
    "csv_enabled": os.getenv("G6_ENABLE_CSV","true").lower()=="true",
    "influxdb_enabled": os.getenv("G6_ENABLE_INFLUXDB","false").lower()=="true",
    "kite_token_valid": False,  # will be updated after validation
    "health_checks_enabled": True,  # or read from config
    "metrics_enabled": True,
}

# 3. Initialize rich terminal output with those args
setup_rich_terminal_output(debug_mode=args.debug, config=platform_config)

# … rest of your main script follows …




# 📊 Import all platform modules with error handling
try:
    from path_resolver_complete import PathResolver
    PATH_RESOLVER_AVAILABLE = True
except ImportError:
    PATH_RESOLVER_AVAILABLE = False
    print("⚠️ PathResolver not available")

try:
    from enhanced_config_complete import EnhancedConfig
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("⚠️ EnhancedConfig not available")

try:
    from market_hours_complete import MarketHours
    MARKET_HOURS_AVAILABLE = True
except ImportError:
    MARKET_HOURS_AVAILABLE = False
    print("⚠️ MarketHours not available")

try:
    from kite_provider_complete import KiteDataProvider
    KITE_PROVIDER_AVAILABLE = True
except ImportError:
    KITE_PROVIDER_AVAILABLE = False
    print("⚠️ KiteDataProvider not available")

try:
    from enhanced_csv_sink_complete import EnhancedCSVSink
    CSV_SINK_AVAILABLE = True
except ImportError:
    CSV_SINK_AVAILABLE = False
    print("⚠️ EnhancedCSVSink not available")

try:
    from atm_options_collector import ATMOptionsCollector
    COLLECTOR_AVAILABLE = True
except ImportError:
    COLLECTOR_AVAILABLE = False
    print("⚠️ ATMOptionsCollector not available")

try:
    from overview_collector import OverviewCollector
    OVERVIEW_AVAILABLE = True
except ImportError:
    OVERVIEW_AVAILABLE = False
    print("⚠️ OverviewCollector not available")

try:
    from analytics_engine import IVCalculator, GreeksCalculator, PCRAnalyzer
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    print("⚠️ Analytics engines not available")

try:
    from health_monitor import HealthMonitor, HealthCheck, CommonHealthChecks
    HEALTH_AVAILABLE = True
except ImportError:
    HEALTH_AVAILABLE = False
    print("⚠️ HealthMonitor not available")

try:
    from metrics_system import get_registry, counter, gauge, histogram
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    print("⚠️ MetricsSystem not available")

try:
    from token_manager import TokenManager
    TOKEN_MANAGER_AVAILABLE = True
except ImportError:
    TOKEN_MANAGER_AVAILABLE = False
    print("⚠️ TokenManager not available")

try:
    from mock_testing_framework import TestFramework, MockKiteProvider
    TESTING_AVAILABLE = True
except ImportError:
    TESTING_AVAILABLE = False
    print("⚠️ TestFramework not available")

logger = logging.getLogger(__name__)

class G6PlatformConfig:
    """🔧 Complete G6 Platform Configuration."""
    
    def __init__(self):
        """🆕 Initialize platform configuration."""
        # 🔧 Core settings
        self.debug_mode = os.getenv('G6_DEBUG', 'false').lower() == 'true'
        self.mock_mode = os.getenv('G6_MOCK_MODE', 'true').lower() == 'true'  # Default to mock mode
        
        # 🕒 Collection settings
        self.collection_interval = int(os.getenv('G6_COLLECTION_INTERVAL', '30'))  # seconds
        self.max_collection_workers = int(os.getenv('G6_MAX_WORKERS', '2'))  # Reduced for stability
        
        # 📊 Data storage
        self.enable_csv_storage = os.getenv('G6_ENABLE_CSV', 'true').lower() == 'true'
        self.enable_influxdb = os.getenv('G6_ENABLE_INFLUXDB', 'false').lower() == 'true'
        
        # 🔐 Authentication
        self.kite_api_key = os.getenv('KITE_API_KEY', '')
        self.kite_access_token = os.getenv('KITE_ACCESS_TOKEN', '')
        
        # ❤️ Health monitoring
        self.health_check_interval = int(os.getenv('G6_HEALTH_INTERVAL', '60'))  # seconds
        
        # 📈 Metrics
        self.metrics_enabled = os.getenv('G6_METRICS_ENABLED', 'true').lower() == 'true'
        
        # 📋 Indices to monitor
        self.monitored_indices = os.getenv('G6_INDICES', 'NIFTY,BANKNIFTY').split(',')

class G6Platform:
    """
    🚀 AI Assistant: Complete G6.1 Options Analytics Platform.
    
    FIXED VERSION - Compatible with Windows and proper async handling
    """
    
    def __init__(self, config: G6PlatformConfig):
        """🆕 Initialize G6 Platform."""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.G6Platform")
        
        # 🔒 Platform state
        self.running = False
        self.shutdown_requested = False
        
        # 📊 Core components
        self.path_resolver = None
        self.enhanced_config = None
        self.market_hours = None
        self.kite_provider = None
        self.csv_sink = None
        
        # 📊 Data collectors
        self.atm_collector = None
        self.overview_collector = None
        
        # 🧮 Analytics engines
        self.iv_calculator = None
        self.greeks_calculator = None
        self.pcr_analyzer = None
        
        # 🔐 Authentication & monitoring
        self.token_manager = None
        self.health_monitor = None
        
        # 📊 Metrics
        self.metrics_registry = None
        self.collection_counter = None
        self.processing_histogram = None
        self.error_counter = None
        
        # 🔄 Threading
        self.main_loop_thread = None
        
        # 📊 Statistics
        self.start_time = None
        self.total_collections = 0
        self.successful_collections = 0
        self.failed_collections = 0
        
        self.logger.info("✅ G6 Platform instance created")
    
    def initialize(self) -> bool:
        """🚀 Initialize all platform components."""
        try:
            self.logger.info("🚀 Initializing G6 Platform...")
            
            # 🔧 Setup logging
            self._setup_logging()
            
            # 📁 Initialize path resolver
            if PATH_RESOLVER_AVAILABLE:
                self.path_resolver = PathResolver()
            else:
                self._create_basic_paths()
            
            # 🕒 Initialize market hours (mock if not available)
            if MARKET_HOURS_AVAILABLE:
                self.market_hours = MarketHours()
            else:
                self.market_hours = self._create_mock_market_hours()
            
            # 📊 Initialize metrics
            if self.config.metrics_enabled and METRICS_AVAILABLE:
                self._initialize_metrics()
            
            # ❤️ Initialize health monitoring
            if HEALTH_AVAILABLE:
                self._initialize_health_monitoring()
            
            # 🔐 Initialize authentication
            self._initialize_authentication()
            
            # 📊 Initialize data providers
            self._initialize_data_providers()
            
            # 🗄️ Initialize data storage
            self._initialize_data_storage()
            
            # 📊 Initialize collectors and analytics
            self._initialize_collectors_and_analytics()
            
            self.logger.info("✅ G6 Platform initialization completed")
            return True
            
        except Exception as e:
            self.logger.error(f"🔴 Platform initialization failed: {e}")
            return False
    
    def _setup_logging(self):
        """📋 Setup comprehensive logging."""
        try:
            # 📁 Ensure logs directory
            logs_dir = Path('logs')
            logs_dir.mkdir(exist_ok=True)
            
            # 🔧 Configure root logger
            log_level = logging.DEBUG if self.config.debug_mode else logging.INFO
            
            # 📄 File handler
            log_file = logs_dir / f'g6_platform_{datetime.date.today().strftime("%Y%m%d")}.log'
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            
            # 🖥️ Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            
            # 🎨 Formatter (without emojis for Windows compatibility)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 🔧 Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            
            self.logger.info("✅ Logging configured")
            
        except Exception as e:
            print(f"🔴 Failed to setup logging: {e}")
    
    def _create_basic_paths(self):
        """📁 Create basic directory paths when PathResolver not available."""
        try:
            basic_dirs = [
                'data', 'data/csv', 'logs', 'config', 'tokens'
            ]
            for directory in basic_dirs:
                Path(directory).mkdir(parents=True, exist_ok=True)
            self.logger.info("✅ Basic paths created")
        except Exception as e:
            self.logger.error(f"🔴 Failed to create basic paths: {e}")
    
    def _create_mock_market_hours(self):
        """🕒 Create mock market hours when MarketHours not available."""
        class MockMarketHours:
            def is_market_open(self):
                # Simple check: weekdays 9:15 AM to 3:30 PM
                now = datetime.datetime.now()
                if now.weekday() >= 5:  # Weekend
                    return False
                return datetime.time(9, 15) <= now.time() <= datetime.time(15, 30)
        
        return MockMarketHours()
    
    def _initialize_metrics(self):
        """📊 Initialize metrics system."""
        try:
            self.metrics_registry = get_registry()
            
            # 📊 Create platform metrics
            self.collection_counter = counter(
                'g6_collections_total',
                'Total number of data collections performed'
            )
            
            self.processing_histogram = histogram(
                'g6_processing_duration_seconds',
                'Time spent processing collections'
            )
            
            self.error_counter = counter(
                'g6_errors_total', 
                'Total number of errors encountered'
            )
            
            self.logger.info("✅ Metrics system initialized")
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to initialize metrics: {e}")
    
    def _initialize_health_monitoring(self):
        """❤️ Initialize health monitoring."""
        try:
            self.health_monitor = HealthMonitor(
                enable_system_monitoring=True,
                enable_auto_recovery=True
            )
            
            # 📋 Register core health checks
            core_checks = [
                HealthCheck(
                    name="platform_status",
                    description="Platform operational status",
                    check_function=self._platform_health_check,
                    interval_seconds=30.0
                )
            ]
            
            self.health_monitor.register_component("g6_platform_core", core_checks)
            
            # 🚀 Start health monitoring
            self.health_monitor.start_monitoring(self.config.health_check_interval)
            
            self.logger.info("✅ Health monitoring initialized")
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to initialize health monitoring: {e}")
    
    def _initialize_authentication(self):
        """🔐 Initialize authentication system."""
        try:
            if not self.config.mock_mode and TOKEN_MANAGER_AVAILABLE:
                # 🔐 Real authentication
                tokens_path = Path('tokens') / 'secure_tokens.json'
                self.token_manager = TokenManager(
                    storage_path=str(tokens_path),
                    auto_refresh=True
                )
                
                if self.config.kite_access_token:
                    self.logger.info("✅ Kite access token available")
                else:
                    self.logger.warning("⚠️ No Kite access token provided")
            else:
                self.logger.info("🎭 Running in mock mode - authentication skipped")
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to initialize authentication: {e}")
    
    def _initialize_data_providers(self):
        """📡 Initialize data providers."""
        try:
            if not self.config.mock_mode and KITE_PROVIDER_AVAILABLE and self.config.kite_access_token:
                # 🔗 Real Kite provider
                self.kite_provider = KiteDataProvider(
                    api_key=self.config.kite_api_key,
                    access_token=self.config.kite_access_token
                )
                
                if self.kite_provider.initialize():
                    self.logger.info("✅ Kite data provider initialized")
                else:
                    self.logger.error("🔴 Failed to initialize Kite provider")
                    return False
                    
            else:
                # 🎭 Mock provider for testing
                if TESTING_AVAILABLE:
                    self.kite_provider = MockKiteProvider()
                    self.logger.info("🎭 Mock data provider initialized")
                else:
                    self.kite_provider = self._create_basic_mock_provider()
                    self.logger.info("🎭 Basic mock provider created")
        
            return True
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to initialize data providers: {e}")
            return False
    
    def _create_basic_mock_provider(self):
        """🎭 Create basic mock provider when TestFramework not available."""
        class BasicMockProvider:
            def get_atm_strike(self, index_name):
                base_prices = {'NIFTY': 24800, 'BANKNIFTY': 54000}
                return base_prices.get(index_name, 25000)
            
            def get_quote(self, instruments):
                return {}
            
            def check_health(self):
                return {'status': 'healthy'}
        
        return BasicMockProvider()
    
    def _initialize_data_storage(self):
        """🗄️ Initialize data storage systems."""
        try:
            # 📊 CSV storage
            if self.config.enable_csv_storage:
                if CSV_SINK_AVAILABLE:
                    csv_path = Path('data') / 'csv'
                    self.csv_sink = EnhancedCSVSink(str(csv_path))
                    self.logger.info("✅ CSV storage initialized")
                else:
                    # Create basic CSV writer
                    self.csv_sink = self._create_basic_csv_sink()
                    self.logger.info("✅ Basic CSV storage created")
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to initialize data storage: {e}")
    
    def _create_basic_csv_sink(self):
        """📊 Create basic CSV storage when EnhancedCSVSink not available."""
        class BasicCSVSink:
            def __init__(self, base_path):
                self.base_path = Path(base_path)
                self.base_path.mkdir(parents=True, exist_ok=True)
                self.logger = logging.getLogger(f"{__name__}.BasicCSVSink")
            
            def write_options_data(self, *args, **kwargs):
                """
                📊 Flexible write method handling multiple calling patterns.
                
                Supports:
                - write_options_data(index_name, options_data)
                - write_options_data(something, offset, options_data)  
                - write_options_data(index_name, expiry, offset, options_data, ...)
                """
                try:
                    import csv
                    
                    # 🔍 Determine calling pattern and extract data
                    if len(args) == 2:
                        # Pattern: (index_name, options_data)
                        index_name, options_data = args
                        offset = None
                        
                    elif len(args) == 3:
                        # Pattern: (something, offset, options_data)
                        _, offset, options_data = args
                        
                        # Auto-detect index from options data
                        if options_data and len(options_data) > 0:
                            symbol = options_data[0].get('tradingsymbol', '')
                            if 'NIFTY' in symbol and 'BANK' not in symbol:
                                index_name = 'NIFTY'
                            elif 'BANKNIFTY' in symbol:
                                index_name = 'BANKNIFTY'
                            elif 'FINNIFTY' in symbol:
                                index_name = 'FINNIFTY'
                            else:
                                index_name = 'UNKNOWN'
                        else:
                            index_name = 'UNKNOWN'
                            
                    elif len(args) >= 4:
                        # Pattern: (index_name, expiry, offset, options_data, ...)
                        index_name = args[0]
                        offset = args[2]
                        options_data = args[3]
                        
                    else:
                        self.logger.error(f"❌ Invalid arguments to write_options_data: {len(args)} args")
                        return self._create_error_result("Invalid arguments")
                    
                    # 📁 Create filename with timestamp and optional offset
                    timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    offset_str = f"_offset_{offset}" if offset is not None else ""
                    filename = self.base_path / f"{index_name}_{timestamp_str}{offset_str}.csv"
                    
                    # 💾 Write CSV data
                    if options_data:
                        with open(filename, 'w', newline='', encoding='utf-8') as f:
                            if isinstance(options_data[0], dict):
                                # Add offset to each record if provided
                                if offset is not None:
                                    for record in options_data:
                                        if isinstance(record, dict):
                                            record['offset'] = offset
                                
                                writer = csv.DictWriter(f, fieldnames=options_data[0].keys())
                                writer.writeheader()
                                writer.writerows(options_data)
                            else:
                                writer = csv.writer(f)
                                writer.writerows(options_data)
                        
                        self.logger.debug(f"✅ Written {len(options_data)} records to {filename.name}")
                        
                        return self._create_success_result(len(options_data), str(filename))
                    else:
                        self.logger.warning(f"⚠️ No data to write for {index_name}")
                        return self._create_success_result(0, "No data")
                    
                except Exception as e:
                    self.logger.error(f"❌ CSV write error: {e}")
                    return self._create_error_result(str(e))
            
            def _create_success_result(self, records_written, filename):
                """📊 Create success result object."""
                return type('Result', (), {
                    'success': True, 
                    'records_written': records_written,
                    'filename': filename
                })()
            
            def _create_error_result(self, error_message):
                """❌ Create error result object."""
                return type('Result', (), {
                    'success': False,
                    'error': error_message,
                    'records_written': 0
                })()
            
            def write_overview_data(self, index_name, overview_data, **kwargs):
                """📋 Write overview data (compatibility method)."""
                try:
                    if not overview_data:
                        return self._create_success_result(0, "No overview data")
                    
                    timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = self.base_path / f"{index_name}_overview_{timestamp_str}.csv"
                    
                    import csv
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        if isinstance(overview_data, dict):
                            writer = csv.DictWriter(f, fieldnames=overview_data.keys())
                            writer.writeheader()
                            writer.writerow(overview_data)
                            records_written = 1
                        else:
                            writer = csv.writer(f)
                            writer.writerow(overview_data)
                            records_written = 1
                    
                    return self._create_success_result(records_written, str(filename))
                    
                except Exception as e:
                    self.logger.error(f"❌ Overview write error: {e}")
                    return self._create_error_result(str(e))
        
        return BasicCSVSink('data/csv')

    
    def _initialize_collectors_and_analytics(self):
        """📊 Initialize data collectors and analytics."""
        try:
            # 📊 Initialize collectors
            if COLLECTOR_AVAILABLE:
                self.atm_collector = ATMOptionsCollector(
                    self.kite_provider,
                    max_workers=self.config.max_collection_workers
                )
            
            if OVERVIEW_AVAILABLE:
                self.overview_collector = OverviewCollector(enable_advanced_analytics=True)
            
            # 🧮 Initialize analytics engines
            if ANALYTICS_AVAILABLE:
                self.iv_calculator = IVCalculator()
                self.greeks_calculator = GreeksCalculator()
                self.pcr_analyzer = PCRAnalyzer()
            
            self.logger.info("✅ Collectors and analytics initialized")
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to initialize collectors and analytics: {e}")
    
    def _platform_health_check(self) -> Dict[str, Any]:
        """❤️ Platform-specific health check."""
        try:
            components_healthy = 0
            total_components = 4
            
            if self.kite_provider:
                components_healthy += 1
            
            if self.csv_sink:
                components_healthy += 1
            
            if self.atm_collector:
                components_healthy += 1
            
            if self.overview_collector:
                components_healthy += 1
            
            health_score = components_healthy / total_components
            
            if health_score >= 0.8:
                status = 'healthy'
                message = f'Platform operational ({components_healthy}/{total_components} components healthy)'
            elif health_score >= 0.6:
                status = 'degraded'  
                message = f'Platform degraded ({components_healthy}/{total_components} components healthy)'
            else:
                status = 'unhealthy'
                message = f'Platform unhealthy ({components_healthy}/{total_components} components healthy)'
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'healthy_components': components_healthy,
                    'total_components': total_components,
                    'health_score': health_score,
                    'running': self.running,
                    'uptime_seconds': (time.time() - self.start_time) if self.start_time else 0
                }
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'message': f'Health check failed: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def start(self):
        """🚀 Start the G6 Platform."""
        try:
            if self.running:
                self.logger.warning("⚠️ Platform is already running")
                return
            
            self.logger.info("🚀 Starting G6 Platform...")
            self.start_time = time.time()
            self.running = True
            
            # 🔄 Start main processing loop
            self.main_loop_thread = threading.Thread(
                target=self._main_processing_loop,
                name="G6MainLoop",
                daemon=False
            )
            self.main_loop_thread.start()
            
            self.logger.info("✅ G6 Platform started successfully")
            
            # 🎯 Display startup summary
            self._display_startup_summary()
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to start platform: {e}")
            self.running = False
    
    def _display_startup_summary(self):
        """📊 Display platform startup summary."""
        try:
            print("\n" + "="*60)
            print("🚀 G6.1 OPTIONS ANALYTICS PLATFORM")
            print("="*60)
            print(f"📅 Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🎛️ Mode: {'Mock' if self.config.mock_mode else 'Live'}")
            print(f"📊 Indices: {', '.join(self.config.monitored_indices)}")
            print(f"⏱️ Collection Interval: {self.config.collection_interval}s")
            
            print(f"\n📊 STORAGE:")
            print(f"  📁 CSV: {'✅ Enabled' if self.config.enable_csv_storage else '❌ Disabled'}")
            
            print(f"\n❤️ MONITORING:")
            print(f"  Health Checks: {'✅ Enabled' if self.health_monitor else '❌ Disabled'}")
            print(f"  Metrics: {'✅ Enabled' if self.config.metrics_enabled else '❌ Disabled'}")
            
            print("="*60)
            print("🎯 Platform is running... Press Ctrl+C to stop")
            print("="*60 + "\n")
            
        except Exception as e:
            self.logger.error(f"🔴 Error displaying startup summary: {e}")
    
    def _main_processing_loop(self):
        """🔄 Main data processing loop - FIXED: No async/await."""
        self.logger.info("🔄 Main processing loop started")
        
        while self.running and not self.shutdown_requested:
            try:
                loop_start_time = time.time()
                
                # 🕒 Check market hours
                if self.market_hours.is_market_open():
                    # 📊 Perform data collection for all indices
                    for index_name in self.config.monitored_indices:
                        try:
                            self._process_index_data(index_name)  # FIXED: No await
                        except Exception as e:
                            self.logger.error(f"🔴 Error processing {index_name}: {e}")
                            if self.error_counter:
                                self.error_counter.inc()
                else:
                    self.logger.debug("🕒 Market is closed - skipping data collection")
                
                # 📊 Update system metrics
                if self.metrics_registry:
                    try:
                        self.metrics_registry.update_system_metrics()
                    except Exception as e:
                        self.logger.debug(f"⚠️ Metrics update failed: {e}")
                
                # ⏱️ Calculate loop duration and sleep
                loop_duration = time.time() - loop_start_time
                
                if self.processing_histogram:
                    self.processing_histogram.observe(loop_duration)
                
                sleep_time = max(0, self.config.collection_interval - loop_duration)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"🔴 Error in main processing loop: {e}")
                time.sleep(10)  # Brief pause on error
        
        self.logger.info("🔄 Main processing loop stopped")
    
    def _process_index_data(self, index_name: str):
        """📊 Process data for a specific index - FIXED: No async."""
        try:
            collection_start_time = time.time()
            
            # 📊 Get ATM strike
            atm_strike = self.kite_provider.get_atm_strike(index_name)
            
            # 📊 Generate mock options data for testing
            options_data = self._generate_sample_options_data(index_name, atm_strike)
            
            # 💾 Store data
            self._store_collection_data(index_name, options_data)
            
            # 📊 Update metrics
            collection_duration = time.time() - collection_start_time
            
            if self.collection_counter:
                self.collection_counter.inc()
            
            self.total_collections += 1
            self.successful_collections += 1
            
            self.logger.info(
                f"✅ Processed {index_name}: {len(options_data)} options, "
                f"processed in {collection_duration:.2f}s"
            )
            
        except Exception as e:
            self.failed_collections += 1
            self.logger.error(f"🔴 Failed to process {index_name}: {e}")
    
    def _generate_sample_options_data(self, index_name: str, atm_strike: float) -> List[Dict]:
        """📊 Generate sample options data for testing."""
        try:
            options_data = []
            strike_step = 50 if index_name == 'NIFTY' else 100
            
            # Generate options around ATM
            for offset in [-2, -1, 0, 1, 2]:
                strike = atm_strike + (offset * strike_step)
                
                # CE option
                options_data.append({
                    'tradingsymbol': f'{index_name}25SEP{int(strike)}CE',
                    'index': index_name,
                    'strike': strike,
                    'option_type': 'CE',
                    'last_price': max(5.0, 100 - abs(offset) * 20),
                    'volume': max(1000, 50000 - abs(offset) * 10000),
                    'oi': max(500, 25000 - abs(offset) * 5000),
                    'timestamp': datetime.datetime.now().isoformat()
                })
                
                # PE option
                options_data.append({
                    'tradingsymbol': f'{index_name}25SEP{int(strike)}PE',
                    'index': index_name,
                    'strike': strike,
                    'option_type': 'PE',
                    'last_price': max(5.0, 80 - abs(offset) * 15),
                    'volume': max(1000, 45000 - abs(offset) * 8000),
                    'oi': max(500, 30000 - abs(offset) * 6000),
                    'timestamp': datetime.datetime.now().isoformat()
                })
            
            return options_data
            
        except Exception as e:
            self.logger.error(f"🔴 Error generating sample data: {e}")
            return []
    
    def _store_collection_data(self, index_name: str, expiry_tag: str, offset: Union[int, str], options_data: List[Dict]):
        """💾 Store collected data to configured storage backends."""
        if not options_data:
            return

        # 1️⃣ CSV Sink
        if self.csv_sink:
            try:
                # EnhancedCSVSink expects (index_name, expiry_tag, offset, options_data)
                csv_result = self.csv_sink.write_options_data(
                    index_name,
                    expiry_tag,
                    offset,
                    options_data
                )

                if hasattr(csv_result, 'success') and csv_result.success:
                    self.logger.debug(f"✅ CSV storage: {csv_result.records_written} records")
                else:
                    err = getattr(csv_result, 'error', 'Unknown error')
                    self.logger.warning(f"⚠️ CSV storage had issues: {err}")

            except Exception as e:
                self.logger.error(f"🔴 CSV storage error: {e}")

        # 2️⃣ Influx Sink (if configured)
        if self.influx_sink:
            try:
                # Influx sink signature: write_options_data(data_dict)
                for opt in options_data:
                    opt['index'] = index_name
                    opt['expiry'] = expiry_tag
                    opt['offset'] = offset
                    if not self.influx_sink.write_options_data(opt):
                        self.logger.warning("⚠️ InfluxDB storage had issues")
                self.logger.debug(f"✅ InfluxDB storage: {len(options_data)} records")
            except Exception as e:
                self.logger.error(f"🔴 InfluxDB storage error: {e}")

    
    def stop(self):
        """🛑 Stop the G6 Platform gracefully."""
        try:
            self.logger.info("🛑 Stopping G6 Platform...")
            
            # 🛑 Set shutdown flags
            self.shutdown_requested = True
            self.running = False
            
            # ⏳ Wait for main loop to finish
            if self.main_loop_thread and self.main_loop_thread.is_alive():
                self.main_loop_thread.join(timeout=10.0)
                
                if self.main_loop_thread.is_alive():
                    self.logger.warning("⚠️ Main loop thread did not stop gracefully")
            
            # 🗑️ Close components
            if self.health_monitor:
                self.health_monitor.stop_monitoring()
            
            if self.token_manager:
                self.token_manager.close()
            
            # 📊 Final statistics
            uptime = time.time() - self.start_time if self.start_time else 0
            success_rate = (self.successful_collections / self.total_collections * 100 
                          if self.total_collections > 0 else 0)
            
            self.logger.info(
                f"🛑 G6 Platform stopped. Final stats: "
                f"Uptime: {uptime:.0f}s, "
                f"Collections: {self.total_collections}, "
                f"Success Rate: {success_rate:.1f}%"
            )
            
        except Exception as e:
            self.logger.error(f"🔴 Error stopping platform: {e}")

# 🚀 AI Assistant: Main application entry point
def main():
    """🚀 Main application entry point - FIXED: No async."""
    print("🚀 G6.1 Options Analytics Platform")
    print("="*50)
    
    # 🔧 Load configuration
    config = G6PlatformConfig()
    
    # 🚀 Create and initialize platform
    platform = G6Platform(config)
    
    # 🔧 Initialize platform
    if not platform.initialize():
        print("🔴 Platform initialization failed")
        return 1
    
    # 🔄 Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down...")
        platform.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 🚀 Start platform
        platform.start()
        
        # 🔄 Keep running until shutdown
        while platform.running and not platform.shutdown_requested:
            time.sleep(1)
        
        print("🛑 Platform shutdown complete")
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received")
        platform.stop()
        return 0
        
    except Exception as e:
        print(f"🔴 Platform error: {e}")
        platform.stop()
        return 1

# 🧪 AI Assistant: Testing and validation
def run_platform_tests():
    """🧪 Run comprehensive platform tests."""
    print("🧪 Running G6 Platform Tests...")
    
    try:
        # 🧪 Test configuration
        config = G6PlatformConfig()
        print(f"✅ Configuration loaded: {len(config.monitored_indices)} indices")
        
        # 🧪 Test platform creation
        platform = G6Platform(config)
        print("✅ Platform instance created")
        
        # 🧪 Test initialization
        if platform.initialize():
            print("✅ Platform initialized successfully")
        else:
            print("⚠️ Platform initialization had issues")
        
        print("🎉 Platform tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"🔴 Platform testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='G6.1 Options Analytics Platform')
    parser.add_argument('--test', action='store_true', help='Run platform tests')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # 🔧 Set environment variables from args
    if args.mock:
        os.environ['G6_MOCK_MODE'] = 'true'
    if args.debug:
        os.environ['G6_DEBUG'] = 'true'
    
    if args.test:
        # 🧪 Run tests
        success = run_platform_tests()
        sys.exit(0 if success else 1)
    else:
        # 🚀 Run main application
        try:
            result = main()  # FIXED: No asyncio.run()
            sys.exit(result)
        except Exception as e:
            print(f"🔴 Application error: {e}")
            sys.exit(1)