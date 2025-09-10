#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Data Collectors - G6.1 Platform
Comprehensive testing for all data collection modules

Test Categories:
- Unit tests for individual collectors
- Integration tests for data flow
- Performance tests for throughput
- Mock data validation tests
- Error handling and recovery tests
"""

import unittest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import os
import json

# Import modules to test
import sys
sys.path.append('..')

try:
    from collectors.market_data_collector import (
        MarketDataCollector, KiteConnectDataSource, MockDataSource,
        MarketDataPoint, OptionsDataPoint, DataSourceType
    )
    from collectors.enhanced_kite_provider import EnhancedKiteDataProvider
    from collectors.enhanced_atm_collector import EnhancedATMCollector
except ImportError as e:
    print(f"Warning: Could not import collectors: {e}")

class TestMarketDataCollector(unittest.TestCase):
    """Test cases for MarketDataCollector."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'cache_ttl': 60,
            'use_mock_data': True,
            'data_sources': {
                'kite_connect': {
                    'api_key': 'test_api_key',
                    'access_token': 'test_access_token',
                    'primary': True
                }
            }
        }
        self.collector = MarketDataCollector(self.config)
    
    def test_collector_initialization(self):
        """Test collector initialization."""
        self.assertIsNotNone(self.collector)
        self.assertEqual(len(self.collector.data_sources), 1)
        self.assertIsNotNone(self.collector.primary_source)
    
    def test_connect_all_sources(self):
        """Test connecting to all data sources."""
        result = self.collector.connect_all_sources()
        self.assertTrue(result)
    
    def test_get_market_data(self):
        """Test market data retrieval."""
        # Connect first
        self.collector.connect_all_sources()
        
        # Get market data
        data = self.collector.get_market_data('NIFTY')
        
        self.assertIsNotNone(data)
        self.assertIsInstance(data, MarketDataPoint)
        self.assertEqual(data.symbol, 'NIFTY')
        self.assertGreater(data.price, 0)
        self.assertIsNotNone(data.timestamp)
    
    def test_get_market_data_caching(self):
        """Test market data caching functionality."""
        # Connect first
        self.collector.connect_all_sources()
        
        # First call
        start_time = time.time()
        data1 = self.collector.get_market_data('NIFTY', use_cache=True)
        first_call_time = time.time() - start_time
        
        # Second call (should be faster due to caching)
        start_time = time.time()
        data2 = self.collector.get_market_data('NIFTY', use_cache=True)
        second_call_time = time.time() - start_time
        
        self.assertIsNotNone(data1)
        self.assertIsNotNone(data2)
        # Cache should make second call faster
        self.assertLess(second_call_time, first_call_time * 0.5)
    
    def test_get_options_chain(self):
        """Test options chain retrieval."""
        # Connect first
        self.collector.connect_all_sources()
        
        # Get options chain
        expiry_date = '2024-12-26'
        options = self.collector.get_options_chain('NIFTY', expiry_date)
        
        self.assertIsInstance(options, list)
        
        if options:  # If mock data returns options
            self.assertIsInstance(options[0], OptionsDataPoint)
            self.assertIn(options[0].option_type, ['CE', 'PE'])
            self.assertGreater(options[0].strike, 0)
    
    def test_get_multiple_quotes(self):
        """Test multiple symbol quotes."""
        # Connect first
        self.collector.connect_all_sources()
        
        symbols = ['NIFTY', 'BANKNIFTY']
        quotes = self.collector.get_multiple_quotes(symbols)
        
        self.assertIsInstance(quotes, dict)
        
        for symbol in symbols:
            if symbol in quotes:
                self.assertIsInstance(quotes[symbol], MarketDataPoint)
    
    def test_health_status(self):
        """Test health status reporting."""
        # Connect first
        self.collector.connect_all_sources()
        
        health = self.collector.get_health_status()
        
        self.assertIsInstance(health, dict)
        self.assertIn('cache_size', health)
        self.assertIn('primary_source', health)
    
    def test_cache_cleanup(self):
        """Test cache cleanup functionality."""
        # Connect and add some cached data
        self.collector.connect_all_sources()
        self.collector.get_market_data('NIFTY')
        
        # Check cache has data
        initial_cache_size = len(self.collector.cache)
        
        # Cleanup
        cleaned_count = self.collector.cleanup_cache()
        
        # Should return number of cleaned entries (may be 0 if TTL not expired)
        self.assertIsInstance(cleaned_count, int)

class TestKiteConnectDataSource(unittest.TestCase):
    """Test cases for KiteConnectDataSource."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'api_key': 'test_api_key',
            'access_token': 'test_access_token'
        }
    
    @patch('kiteconnect.KiteConnect')
    def test_kite_connect_initialization(self, mock_kite):
        """Test KiteConnect data source initialization."""
        source = KiteConnectDataSource(self.config)
        
        self.assertEqual(source.api_key, 'test_api_key')
        self.assertEqual(source.access_token, 'test_access_token')
        self.assertFalse(source.is_connected)
    
    @patch('kiteconnect.KiteConnect')
    def test_kite_connect_connection(self, mock_kite):
        """Test KiteConnect connection."""
        # Mock successful connection
        mock_instance = Mock()
        mock_instance.profile.return_value = {'user_name': 'test_user'}
        mock_kite.return_value = mock_instance
        
        source = KiteConnectDataSource(self.config)
        result = source.connect()
        
        self.assertTrue(result)
        self.assertTrue(source.is_connected)
    
    @patch('kiteconnect.KiteConnect')
    def test_kite_connect_market_data(self, mock_kite):
        """Test market data retrieval from KiteConnect."""
        # Mock KiteConnect responses
        mock_instance = Mock()
        mock_instance.profile.return_value = {'user_name': 'test_user'}
        mock_instance.quote.return_value = {
            'NSE:NIFTY 50': {
                'last_price': 24975.50,
                'volume': 450000,
                'net_change': 125.50,
                'change': 0.51,
                'ohlc': {
                    'open': 24850.0,
                    'high': 25050.0,
                    'low': 24825.0,
                    'close': 24975.50
                },
                'instrument_token': 256265
            }
        }
        mock_kite.return_value = mock_instance
        
        source = KiteConnectDataSource(self.config)
        source.connect()
        
        data = source.get_market_data('NIFTY')
        
        self.assertIsNotNone(data)
        self.assertEqual(data.symbol, 'NIFTY')
        self.assertEqual(data.price, 24975.50)
        self.assertEqual(data.source, DataSourceType.KITE_CONNECT)

class TestMockDataSource(unittest.TestCase):
    """Test cases for MockDataSource."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {}
        self.source = MockDataSource(self.config)
    
    def test_mock_source_connection(self):
        """Test mock source connection."""
        result = self.source.connect()
        self.assertTrue(result)
        self.assertTrue(self.source.is_connected)
    
    def test_mock_market_data(self):
        """Test mock market data generation."""
        self.source.connect()
        
        data = self.source.get_market_data('NIFTY')
        
        self.assertIsNotNone(data)
        self.assertEqual(data.symbol, 'NIFTY')
        self.assertGreater(data.price, 0)
        self.assertGreater(data.volume, 0)
        self.assertEqual(data.source, DataSourceType.KITE_CONNECT)
    
    def test_mock_options_chain(self):
        """Test mock options chain generation."""
        self.source.connect()
        
        options = self.source.get_options_chain('NIFTY', '2024-12-26')
        
        self.assertIsInstance(options, list)
        self.assertGreater(len(options), 0)
        
        # Check first option
        option = options[0]
        self.assertIsInstance(option, OptionsDataPoint)
        self.assertIn(option.option_type, ['CE', 'PE'])
        self.assertGreater(option.last_price, 0)
    
    def test_mock_historical_data(self):
        """Test mock historical data generation."""
        self.source.connect()
        
        historical = self.source.get_historical_data('NIFTY', days=10)
        
        self.assertIsInstance(historical, list)
        self.assertEqual(len(historical), 10)
        
        if historical:
            data_point = historical[0]
            self.assertIsInstance(data_point, MarketDataPoint)
            self.assertEqual(data_point.symbol, 'NIFTY')

class TestEnhancedKiteProvider(unittest.TestCase):
    """Test cases for EnhancedKiteDataProvider."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'rate_limiting': {'requests_per_minute': 200},
            'caching': {'enabled': True, 'ttl_seconds': 60}
        }
    
    @patch('kiteconnect.KiteConnect')
    def test_enhanced_provider_initialization(self, mock_kite):
        """Test enhanced provider initialization."""
        provider = EnhancedKiteDataProvider('test_key', 'test_token')
        
        self.assertIsNotNone(provider)
        # Add more specific tests based on actual implementation

class TestPerformanceAndStress(unittest.TestCase):
    """Performance and stress tests for collectors."""
    
    def setUp(self):
        """Set up performance test fixtures."""
        self.config = {
            'cache_ttl': 60,
            'use_mock_data': True
        }
        self.collector = MarketDataCollector(self.config)
        self.collector.connect_all_sources()
    
    def test_concurrent_data_requests(self):
        """Test concurrent data requests performance."""
        import threading
        import time
        
        results = []
        errors = []
        
        def fetch_data(symbol):
            try:
                start_time = time.time()
                data = self.collector.get_market_data(symbol)
                end_time = time.time()
                
                results.append({
                    'symbol': symbol,
                    'success': data is not None,
                    'time': end_time - start_time
                })
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY'] * 10
        threads = []
        
        start_time = time.time()
        
        for symbol in symbols:
            thread = threading.Thread(target=fetch_data, args=(symbol,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Assertions
        self.assertEqual(len(results), len(symbols))
        self.assertEqual(len(errors), 0)
        
        # Performance assertions
        avg_time = sum(r['time'] for r in results) / len(results)
        self.assertLess(avg_time, 1.0)  # Average request should be under 1 second
        self.assertLess(total_time, 10.0)  # Total time should be reasonable
    
    def test_memory_usage_stability(self):
        """Test memory usage stability over many requests."""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Make many requests
        for i in range(1000):
            data = self.collector.get_market_data('NIFTY')
            
            # Occasional garbage collection
            if i % 100 == 0:
                gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024)
    
    def test_cache_performance(self):
        """Test cache performance under load."""
        # Warm up cache
        self.collector.get_market_data('NIFTY', use_cache=True)
        
        # Time cached requests
        start_time = time.time()
        
        for _ in range(100):
            data = self.collector.get_market_data('NIFTY', use_cache=True)
        
        cached_time = time.time() - start_time
        
        # Time non-cached requests
        start_time = time.time()
        
        for _ in range(100):
            data = self.collector.get_market_data('BANKNIFTY', use_cache=False)
        
        non_cached_time = time.time() - start_time
        
        # Cached requests should be significantly faster
        self.assertLess(cached_time, non_cached_time * 0.1)

class TestErrorHandling(unittest.TestCase):
    """Test error handling and recovery."""
    
    def setUp(self):
        """Set up error handling test fixtures."""
        self.config = {
            'cache_ttl': 60,
            'use_mock_data': False,  # Use real sources for error testing
            'data_sources': {
                'kite_connect': {
                    'api_key': 'invalid_key',
                    'access_token': 'invalid_token',
                    'primary': True
                }
            }
        }
        self.collector = MarketDataCollector(self.config)
    
    def test_invalid_credentials_handling(self):
        """Test handling of invalid API credentials."""
        # Should handle connection failure gracefully
        result = self.collector.connect_all_sources()
        
        # May return False due to invalid credentials
        self.assertIsInstance(result, bool)
    
    def test_network_error_handling(self):
        """Test network error handling."""
        # Mock network failure
        with patch('kiteconnect.KiteConnect') as mock_kite:
            mock_instance = Mock()
            mock_instance.profile.side_effect = Exception("Network error")
            mock_kite.return_value = mock_instance
            
            source = KiteConnectDataSource(self.config['data_sources']['kite_connect'])
            result = source.connect()
            
            self.assertFalse(result)
            self.assertIsNotNone(source.last_error)
    
    def test_malformed_data_handling(self):
        """Test handling of malformed data responses."""
        with patch('kiteconnect.KiteConnect') as mock_kite:
            mock_instance = Mock()
            mock_instance.profile.return_value = {'user_name': 'test'}
            mock_instance.quote.return_value = {'invalid': 'data'}  # Malformed response
            mock_kite.return_value = mock_instance
            
            source = KiteConnectDataSource(self.config['data_sources']['kite_connect'])
            source.connect()
            
            data = source.get_market_data('NIFTY')
            
            # Should handle gracefully and return None
            self.assertIsNone(data)

class TestDataValidation(unittest.TestCase):
    """Test data validation and quality checks."""
    
    def setUp(self):
        """Set up data validation test fixtures."""
        self.config = {'use_mock_data': True}
        self.collector = MarketDataCollector(self.config)
        self.collector.connect_all_sources()
    
    def test_market_data_validation(self):
        """Test market data validation."""
        data = self.collector.get_market_data('NIFTY')
        
        if data:
            # Validate required fields
            self.assertIsNotNone(data.symbol)
            self.assertIsNotNone(data.timestamp)
            self.assertIsInstance(data.price, (int, float))
            self.assertIsInstance(data.volume, int)
            
            # Validate reasonable values
            self.assertGreater(data.price, 0)
            self.assertGreaterEqual(data.volume, 0)
            self.assertIsInstance(data.source, DataSourceType)
    
    def test_options_data_validation(self):
        """Test options data validation."""
        options = self.collector.get_options_chain('NIFTY', '2024-12-26')
        
        for option in options:
            # Validate required fields
            self.assertIsNotNone(option.symbol)
            self.assertIsInstance(option.strike, (int, float))
            self.assertIn(option.option_type, ['CE', 'PE'])
            self.assertIsInstance(option.last_price, (int, float))
            
            # Validate reasonable values
            self.assertGreater(option.strike, 0)
            self.assertGreaterEqual(option.last_price, 0)
            self.assertGreaterEqual(option.volume, 0)
            self.assertGreaterEqual(option.oi, 0)

def create_test_suite():
    """Create comprehensive test suite."""
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestMarketDataCollector))
    suite.addTest(unittest.makeSuite(TestKiteConnectDataSource))
    suite.addTest(unittest.makeSuite(TestMockDataSource))
    suite.addTest(unittest.makeSuite(TestEnhancedKiteProvider))
    suite.addTest(unittest.makeSuite(TestPerformanceAndStress))
    suite.addTest(unittest.makeSuite(TestErrorHandling))
    suite.addTest(unittest.makeSuite(TestDataValidation))
    
    return suite

if __name__ == '__main__':
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    sys.exit(exit_code)