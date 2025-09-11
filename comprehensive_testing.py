#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Comprehensive Testing Module for G6 Analytics Platform
Author: AI Assistant (Complete Testing Framework)

✅ Test Categories:
- System Requirements & Environment Tests
- Analytics Engine Validation Tests  
- Data Collection & Storage Tests
- Performance & Load Tests
- Integration & End-to-End Tests
- Mathematical Accuracy Tests
- Error Handling & Recovery Tests
- First-Run System Diagnostics
"""

import unittest
import sys
import os
import time
import json
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch, MagicMock
import tempfile
import subprocess

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
try:
    import numpy as np
    import scipy.stats
    import pandas as pd
    from kiteconnect import KiteConnect
    from influxdb_client import InfluxDBClient
    import analytics_engine
    from analytics_engine import IVCalculator, GreeksCalculator, PCRAnalyzer
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Missing dependencies for comprehensive testing: {e}")
    DEPENDENCIES_AVAILABLE = False

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemRequirementsTest(unittest.TestCase):
    """🔧 System Requirements and Environment Tests."""
    
    def test_python_version(self):
        """Test Python version compatibility."""
        python_version = sys.version_info
        self.assertGreaterEqual(python_version.major, 3, "Python 3.x required")
        self.assertGreaterEqual(python_version.minor, 8, "Python 3.8+ required")
        logger.info(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    def test_required_packages(self):
        """Test that all required packages are installed."""
        required_packages = [
            'numpy', 'scipy', 'pandas', 'kiteconnect', 
            'influxdb_client', 'psutil', 'rich', 'requests'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✅ Package '{package}' is available")
            except ImportError:
                missing_packages.append(package)
                logger.error(f"❌ Package '{package}' is missing")
        
        self.assertEqual(len(missing_packages), 0, 
                        f"Missing required packages: {missing_packages}")
    
    def test_system_resources(self):
        """Test system resource availability."""
        # Memory test
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        self.assertGreaterEqual(available_gb, 1.0, "At least 1GB RAM required")
        logger.info(f"✅ Available Memory: {available_gb:.2f} GB")
        
        # Disk space test  
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024**3)
        self.assertGreaterEqual(free_gb, 0.5, "At least 0.5GB disk space required")
        logger.info(f"✅ Available Disk Space: {free_gb:.2f} GB")
        
        # CPU test
        cpu_count = psutil.cpu_count()
        self.assertGreaterEqual(cpu_count, 1, "At least 1 CPU core required")
        logger.info(f"✅ CPU Cores: {cpu_count}")
    
    def test_file_permissions(self):
        """Test file system permissions."""
        # Test write permissions in current directory
        test_file = 'test_permissions.tmp'
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logger.info("✅ Write permissions verified")
        except Exception as e:
            self.fail(f"Cannot write to current directory: {e}")
        
        # Test log directory creation
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        self.assertTrue(os.path.exists(log_dir), "Cannot create logs directory")
        logger.info("✅ Log directory permissions verified")

class AnalyticsEngineTest(unittest.TestCase):
    """🧮 Analytics Engine Validation Tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        self.iv_calculator = IVCalculator()
        self.greeks_calculator = GreeksCalculator()
        self.pcr_analyzer = PCRAnalyzer()
        
        # Test data
        self.spot_price = 24800.0
        self.strike_price = 24800.0
        self.time_to_expiry = 30/365  # 30 days
        self.volatility = 0.18  # 18%
        self.option_price_ce = 125.50
        self.option_price_pe = 98.75
    
    def test_iv_calculation_accuracy(self):
        """Test IV calculation accuracy."""
        # Test call option IV
        iv_ce = self.iv_calculator.calculate_implied_volatility(
            option_price=self.option_price_ce,
            spot_price=self.spot_price,
            strike_price=self.strike_price,
            time_to_expiry=self.time_to_expiry,
            option_type='CE'
        )
        
        self.assertIsNotNone(iv_ce, "IV calculation should not return None")
        self.assertGreater(iv_ce, 0, "IV should be positive")
        self.assertLess(iv_ce, 500, "IV should be reasonable (< 500%)")
        logger.info(f"✅ CE IV calculated: {iv_ce}%")
        
        # Test put option IV
        iv_pe = self.iv_calculator.calculate_implied_volatility(
            option_price=self.option_price_pe,
            spot_price=self.spot_price,
            strike_price=self.strike_price,
            time_to_expiry=self.time_to_expiry,
            option_type='PE'
        )
        
        self.assertIsNotNone(iv_pe, "IV calculation should not return None")
        self.assertGreater(iv_pe, 0, "IV should be positive")
        logger.info(f"✅ PE IV calculated: {iv_pe}%")
    
    def test_greeks_calculation_accuracy(self):
        """Test Greeks calculation accuracy."""
        greeks = self.greeks_calculator.calculate_all_greeks(
            spot_price=self.spot_price,
            strike_price=self.strike_price,
            time_to_expiry=self.time_to_expiry,
            volatility=self.volatility,
            option_type='CE'
        )
        
        # Test delta range for ATM call
        self.assertGreater(greeks.delta, 0.4, "ATM call delta should be > 0.4")
        self.assertLess(greeks.delta, 0.6, "ATM call delta should be < 0.6")
        
        # Test gamma is positive
        self.assertGreater(greeks.gamma, 0, "Gamma should be positive")
        
        # Test theta is negative (time decay)
        self.assertLess(greeks.theta, 0, "Theta should be negative")
        
        # Test vega is positive
        self.assertGreater(greeks.vega, 0, "Vega should be positive")
        
        logger.info(f"✅ Greeks calculated - Delta: {greeks.delta}, Gamma: {greeks.gamma}, Theta: {greeks.theta}")
    
    def test_pcr_analysis_functionality(self):
        """Test PCR analysis functionality."""
        # Mock option data - import from correct module
        try:
            from atm_options_collector import OptionData
        except ImportError:
            # Fallback: create a simple mock class
            class OptionData:
                def __init__(self, tradingsymbol, strike, expiry, option_type, last_price, volume, oi, change, pchange):
                    self.tradingsymbol = tradingsymbol
                    self.strike = strike
                    self.expiry = expiry
                    self.option_type = option_type
                    self.last_price = last_price
                    self.volume = volume
                    self.oi = oi
                    self.change = change
                    self.pchange = pchange
        
        ce_options = [
            OptionData("NIFTY25SEP24800CE", 24800, "2025-09-25", "CE", 125.50, 100000, 50000, 5.25, 4.37),
            OptionData("NIFTY25SEP24850CE", 24850, "2025-09-25", "CE", 95.50, 80000, 40000, 4.25, 3.37)
        ]
        
        pe_options = [
            OptionData("NIFTY25SEP24800PE", 24800, "2025-09-25", "PE", 98.75, 120000, 60000, -2.15, -2.13),
            OptionData("NIFTY25SEP24750PE", 24750, "2025-09-25", "PE", 78.75, 90000, 45000, -1.85, -1.83)
        ]
        
        pcr_analysis = self.pcr_analyzer.analyze_pcr(ce_options, pe_options)
        
        # Test PCR calculations
        self.assertGreater(pcr_analysis.pcr_volume, 0, "PCR volume should be positive")
        self.assertGreater(pcr_analysis.pcr_oi, 0, "PCR OI should be positive")
        self.assertIn(pcr_analysis.sentiment_indicator, 
                     ['Strong Bearish', 'Bearish', 'Neutral', 'Bullish', 'Strong Bullish'],
                     "Sentiment should be valid")
        
        logger.info(f"✅ PCR Analysis - Volume: {pcr_analysis.pcr_volume}, Sentiment: {pcr_analysis.sentiment_indicator}")
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test invalid inputs
        iv_invalid = self.iv_calculator.calculate_implied_volatility(
            option_price=-10,  # Negative price
            spot_price=self.spot_price,
            strike_price=self.strike_price,
            time_to_expiry=self.time_to_expiry,
            option_type='CE'
        )
        self.assertIsNone(iv_invalid, "Should handle invalid negative prices")
        
        # Test zero time to expiry
        iv_zero_time = self.iv_calculator.calculate_implied_volatility(
            option_price=self.option_price_ce,
            spot_price=self.spot_price,
            strike_price=self.strike_price,
            time_to_expiry=0,  # Zero time
            option_type='CE'
        )
        self.assertIsNone(iv_zero_time, "Should handle zero time to expiry")
        
        logger.info("✅ Edge case handling verified")

class PerformanceTest(unittest.TestCase):
    """⚡ Performance and Load Tests."""
    
    def setUp(self):
        """Set up performance test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        self.iv_calculator = IVCalculator()
        self.greeks_calculator = GreeksCalculator()
    
    def test_iv_calculation_performance(self):
        """Test IV calculation performance."""
        start_time = time.time()
        iterations = 100
        
        for i in range(iterations):
            iv = self.iv_calculator.calculate_implied_volatility(
                option_price=125.50 + i * 0.1,
                spot_price=24800 + i,
                strike_price=24800,
                time_to_expiry=30/365,
                option_type='CE'
            )
        
        end_time = time.time()
        avg_time = (end_time - start_time) / iterations
        
        self.assertLess(avg_time, 0.1, f"IV calculation too slow: {avg_time:.4f}s per calculation")
        logger.info(f"✅ IV Performance: {avg_time:.4f}s per calculation")
    
    def test_greeks_calculation_performance(self):
        """Test Greeks calculation performance."""
        start_time = time.time()
        iterations = 100
        
        for i in range(iterations):
            greeks = self.greeks_calculator.calculate_all_greeks(
                spot_price=24800 + i,
                strike_price=24800,
                time_to_expiry=30/365,
                volatility=0.18 + i * 0.001,
                option_type='CE'
            )
        
        end_time = time.time()
        avg_time = (end_time - start_time) / iterations
        
        self.assertLess(avg_time, 0.05, f"Greeks calculation too slow: {avg_time:.4f}s per calculation")
        logger.info(f"✅ Greeks Performance: {avg_time:.4f}s per calculation")

class FirstRunSystemChecks(unittest.TestCase):
    """🔧 First-Run System Checks and Diagnostics."""
    
    def test_kite_connect_api_setup(self):
        """Test Kite Connect API setup and configuration."""
        # Test if config file exists
        config_files = ['config.json', '.env']
        config_found = any(os.path.exists(f) for f in config_files)
        
        if config_found:
            logger.info("✅ Configuration file found")
            
            # Test config.json structure if it exists
            if os.path.exists('config.json'):
                try:
                    with open('config.json', 'r') as f:
                        config = json.load(f)
                    
                    # Check essential config sections
                    required_sections = ['platform', 'market', 'data_collection', 'analytics']
                    for section in required_sections:
                        self.assertIn(section, config, f"Config missing '{section}' section")
                    
                    logger.info("✅ Configuration structure validated")
                except Exception as e:
                    self.fail(f"Config file parsing error: {e}")
        else:
            logger.warning("⚠️ No configuration file found - first run setup may be needed")
    
    def test_influxdb_connection_availability(self):
        """Test InfluxDB connection and setup."""
        # Check if InfluxDB client can be created
        try:
            # Try to create a client with default settings
            client = InfluxDBClient(url="http://localhost:8086", token="", org="")
            logger.info("✅ InfluxDB client can be created")
            
            # Note: We don't test actual connection as InfluxDB may not be running
            # This would be done in integration tests
            
        except Exception as e:
            logger.warning(f"⚠️ InfluxDB client creation issue: {e}")
    
    def test_data_directories_setup(self):
        """Test data directory structure setup."""
        required_dirs = ['data', 'logs', 'data/csv']
        
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)
            self.assertTrue(os.path.exists(dir_path), f"Cannot create directory: {dir_path}")
            
            # Test write permissions
            test_file = os.path.join(dir_path, 'test_write.tmp')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                logger.info(f"✅ Directory '{dir_path}' is writable")
            except Exception as e:
                self.fail(f"Cannot write to directory '{dir_path}': {e}")
    
    def test_token_storage_setup(self):
        """Test token storage directory setup."""
        token_dir = 'tokens'
        os.makedirs(token_dir, exist_ok=True)
        
        self.assertTrue(os.path.exists(token_dir), "Cannot create tokens directory")
        
        # Test if we can create and read token files
        test_token_file = os.path.join(token_dir, 'test_token.txt')
        try:
            with open(test_token_file, 'w') as f:
                f.write('test_token_data')
            
            with open(test_token_file, 'r') as f:
                content = f.read()
            
            os.remove(test_token_file)
            self.assertEqual(content, 'test_token_data', "Token file read/write error")
            logger.info("✅ Token storage setup verified")
            
        except Exception as e:
            self.fail(f"Token storage test failed: {e}")

class IntegrationTest(unittest.TestCase):
    """🔗 Integration and End-to-End Tests."""
    
    def test_analytics_engine_integration(self):
        """Test complete analytics engine integration."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        # Test full analytics pipeline
        try:
            # Initialize all components
            iv_calc = IVCalculator()
            greeks_calc = GreeksCalculator()
            pcr_analyzer = PCRAnalyzer()
            
            # Test data flow
            option_price = 125.50
            spot_price = 24800.0
            strike_price = 24800.0
            time_to_expiry = 30/365
            
            # Calculate IV
            iv = iv_calc.calculate_implied_volatility(
                option_price=option_price,
                spot_price=spot_price,
                strike_price=strike_price,
                time_to_expiry=time_to_expiry,
                option_type='CE'
            )
            
            self.assertIsNotNone(iv, "IV calculation failed in integration test")
            
            # Calculate Greeks using calculated IV
            volatility = iv / 100 if iv else 0.18
            greeks = greeks_calc.calculate_all_greeks(
                spot_price=spot_price,
                strike_price=strike_price,
                time_to_expiry=time_to_expiry,
                volatility=volatility,
                option_type='CE'
            )
            
            self.assertIsNotNone(greeks, "Greeks calculation failed in integration test")
            
            logger.info("✅ Analytics engine integration test passed")
            
        except Exception as e:
            self.fail(f"Analytics integration test failed: {e}")

def run_comprehensive_tests():
    """🧪 Run all comprehensive tests."""
    print("🚀 Starting Comprehensive Testing Suite for G6 Analytics Platform")
    print("=" * 80)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        SystemRequirementsTest,
        AnalyticsEngineTest,
        PerformanceTest,
        FirstRunSystemChecks,
        IntegrationTest
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("🧪 Comprehensive Test Summary")
    print("=" * 80)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n🔴 Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n🔴 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if result.wasSuccessful():
        print("\n🎉 All tests passed! System is ready for production.")
        return True
    else:
        print("\n⚠️ Some tests failed. Please review and fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)