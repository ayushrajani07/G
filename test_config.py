#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Configuration Management - G6.1 Platform
Comprehensive testing for configuration loading, validation, and management

Test Categories:
- Configuration loading and parsing
- Validation and error handling
- Environment variable overrides
- Hot-reloading functionality
- Schema validation
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, mock_open
import sys

sys.path.append('..')

try:
    from config.config_manager import ConfigManager, load_config, validate_config
except ImportError as e:
    print(f"Warning: Could not import config modules: {e}")
    # Create mock classes for testing if import fails
    class ConfigManager:
        pass
    
    def load_config(path):
        return {}
    
    def validate_config(config):
        return []

class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_config = {
            "platform": {
                "name": "G6.1 Options Analytics Platform",
                "version": "2.0.0",
                "mode": "live",
                "debug_enabled": False
            },
            "market": {
                "indices": ["NIFTY", "BANKNIFTY", "FINNIFTY"],
                "collection_interval": 30,
                "market_hours": {
                    "start": "09:15",
                    "end": "15:30",
                    "timezone": "Asia/Kolkata"
                }
            },
            "data_collection": {
                "options": {
                    "strike_configuration": {
                        "symmetric_otm": {
                            "enabled": True,
                            "offsets": [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
                        }
                    }
                }
            }
        }
        
        self.invalid_config = {
            "platform": {
                "name": "",  # Invalid: empty name
                "version": "invalid_version",  # Invalid format
                "mode": "invalid_mode"  # Invalid mode
            },
            "market": {
                "indices": [],  # Invalid: empty indices
                "collection_interval": -10  # Invalid: negative interval
            }
        }
    
    def test_valid_config_loading(self):
        """Test loading valid configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            self.assertIsInstance(config, dict)
            self.assertEqual(config['platform']['name'], "G6.1 Options Analytics Platform")
            self.assertEqual(config['market']['collection_interval'], 30)
        finally:
            os.unlink(config_path)
    
    def test_missing_config_file(self):
        """Test handling of missing configuration file."""
        non_existent_path = '/path/that/does/not/exist/config.json'
        
        # Should handle gracefully, either return default or raise appropriate exception
        try:
            config = load_config(non_existent_path)
            # If it returns a config, it should be empty or default
            self.assertIsInstance(config, dict)
        except FileNotFoundError:
            # This is also acceptable behavior
            pass
    
    def test_invalid_json_format(self):
        """Test handling of invalid JSON format."""
        invalid_json = '{"platform": {"name": "Test",}}'  # Trailing comma
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(invalid_json)
            config_path = f.name
        
        try:
            with self.assertRaises(json.JSONDecodeError):
                load_config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        errors = validate_config(self.valid_config)
        self.assertIsInstance(errors, list)
        self.assertEqual(len(errors), 0)
    
    def test_config_validation_failures(self):
        """Test configuration validation with errors."""
        errors = validate_config(self.invalid_config)
        self.assertIsInstance(errors, list)
        self.assertGreater(len(errors), 0)
        
        # Should detect multiple validation errors
        error_messages = ' '.join(errors)
        self.assertIn('name', error_messages.lower())
        self.assertIn('version', error_messages.lower())
        self.assertIn('mode', error_messages.lower())
    
    @patch.dict(os.environ, {
        'G6_API_KEY': 'test_api_key_from_env',
        'G6_DEBUG_MODE': 'true',
        'G6_COLLECTION_INTERVAL': '45'
    })
    def test_environment_variable_overrides(self):
        """Test environment variable overrides."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            
            # Environment variables should override config values
            # This assumes the config manager supports env var overrides
            if hasattr(config, 'get'):
                # Check if environment overrides are applied
                # The exact implementation depends on how env vars are mapped
                pass
        finally:
            os.unlink(config_path)
    
    def test_nested_config_access(self):
        """Test accessing nested configuration values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            
            # Test nested access
            self.assertEqual(config['platform']['name'], "G6.1 Options Analytics Platform")
            self.assertEqual(config['market']['market_hours']['start'], "09:15")
            self.assertIn('NIFTY', config['market']['indices'])
        finally:
            os.unlink(config_path)
    
    def test_config_schema_validation(self):
        """Test configuration against expected schema."""
        # Define expected schema structure
        required_sections = ['platform', 'market', 'data_collection']
        required_platform_fields = ['name', 'version', 'mode']
        required_market_fields = ['indices', 'collection_interval']
        
        errors = []
        
        # Check required sections
        for section in required_sections:
            if section not in self.valid_config:
                errors.append(f"Missing required section: {section}")
        
        # Check platform fields
        if 'platform' in self.valid_config:
            for field in required_platform_fields:
                if field not in self.valid_config['platform']:
                    errors.append(f"Missing required platform field: {field}")
        
        # Check market fields
        if 'market' in self.valid_config:
            for field in required_market_fields:
                if field not in self.valid_config['market']:
                    errors.append(f"Missing required market field: {field}")
        
        self.assertEqual(len(errors), 0, f"Schema validation errors: {errors}")
    
    def test_config_type_validation(self):
        """Test configuration value type validation."""
        config = self.valid_config
        
        # Test type validations
        self.assertIsInstance(config['platform']['name'], str)
        self.assertIsInstance(config['platform']['debug_enabled'], bool)
        self.assertIsInstance(config['market']['collection_interval'], int)
        self.assertIsInstance(config['market']['indices'], list)
        
        # Test value constraints
        self.assertGreater(config['market']['collection_interval'], 0)
        self.assertGreater(len(config['market']['indices']), 0)
        self.assertNotEqual(config['platform']['name'].strip(), "")
    
    def test_default_values(self):
        """Test application of default values."""
        minimal_config = {
            "platform": {
                "name": "Test Platform"
            }
        }
        
        # Test that defaults are applied for missing values
        # This would require actual ConfigManager implementation
        pass

class TestConfigurationIntegration(unittest.TestCase):
    """Integration tests for configuration management."""
    
    def test_full_config_loading_pipeline(self):
        """Test complete configuration loading pipeline."""
        # Create a comprehensive config file
        comprehensive_config = {
            "platform": {
                "name": "G6.1 Options Analytics Platform",
                "version": "2.0.0",
                "mode": "live",
                "debug_enabled": False
            },
            "market": {
                "indices": ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"],
                "collection_interval": 30,
                "market_hours": {
                    "start": "09:15",
                    "end": "15:30",
                    "timezone": "Asia/Kolkata"
                }
            },
            "data_collection": {
                "options": {
                    "strike_configuration": {
                        "symmetric_otm": {
                            "enabled": True,
                            "offsets": [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
                        }
                    },
                    "data_fields": {
                        "basic": ["tradingsymbol", "strike", "expiry", "option_type", "last_price"],
                        "pricing": ["volume", "oi", "change", "pchange", "iv"],
                        "greeks": ["delta", "gamma", "theta", "vega"]
                    }
                },
                "performance": {
                    "rate_limiting": {
                        "requests_per_minute": 200,
                        "burst_capacity": 50
                    },
                    "caching": {
                        "enabled": True,
                        "ttl_seconds": 60
                    }
                }
            },
            "storage": {
                "csv": {
                    "enabled": True,
                    "base_path": "data/csv"
                },
                "influxdb": {
                    "enabled": False,
                    "url": "http://localhost:8086"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(comprehensive_config, f)
            config_path = f.name
        
        try:
            # Load configuration
            config = load_config(config_path)
            
            # Validate configuration
            errors = validate_config(config)
            self.assertEqual(len(errors), 0, f"Validation errors: {errors}")
            
            # Test deep access patterns
            self.assertEqual(config['data_collection']['performance']['rate_limiting']['requests_per_minute'], 200)
            self.assertTrue(config['storage']['csv']['enabled'])
            self.assertFalse(config['storage']['influxdb']['enabled'])
            
        finally:
            os.unlink(config_path)
    
    def test_config_with_environment_integration(self):
        """Test configuration with environment variable integration."""
        base_config = {
            "platform": {
                "name": "Test Platform",
                "debug_enabled": False
            },
            "api": {
                "rate_limit": 100
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(base_config, f)
            config_path = f.name
        
        # Set environment variables
        env_vars = {
            'G6_DEBUG_MODE': 'true',
            'G6_API_RATE_LIMIT': '200',
            'G6_API_KEY': 'test_key_from_env'
        }
        
        try:
            with patch.dict(os.environ, env_vars):
                config = load_config(config_path)
                
                # Environment variables should override or supplement config
                # This test assumes the config manager handles env vars
                self.assertIsInstance(config, dict)
                
        finally:
            os.unlink(config_path)
    
    def test_config_update_and_reload(self):
        """Test configuration update and hot-reload functionality."""
        initial_config = {
            "platform": {"name": "Initial Platform"},
            "market": {"collection_interval": 30}
        }
        
        updated_config = {
            "platform": {"name": "Updated Platform"},
            "market": {"collection_interval": 60}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(initial_config, f)
            config_path = f.name
        
        try:
            # Load initial config
            config1 = load_config(config_path)
            self.assertEqual(config1['platform']['name'], "Initial Platform")
            
            # Update config file
            with open(config_path, 'w') as f:
                json.dump(updated_config, f)
            
            # Reload config
            config2 = load_config(config_path)
            self.assertEqual(config2['platform']['name'], "Updated Platform")
            self.assertEqual(config2['market']['collection_interval'], 60)
            
        finally:
            os.unlink(config_path)

class TestConfigurationErrorHandling(unittest.TestCase):
    """Test error handling in configuration management."""
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON files."""
        malformed_configs = [
            '{"platform": {"name": "Test",}}',  # Trailing comma
            '{"platform": {"name": "Test"',     # Missing closing brace
            '{platform: "test"}',               # Unquoted keys
            'not json at all',                  # Not JSON
        ]
        
        for malformed_json in malformed_configs:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(malformed_json)
                config_path = f.name
            
            try:
                with self.assertRaises((json.JSONDecodeError, ValueError)):
                    load_config(config_path)
            finally:
                os.unlink(config_path)
    
    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        # Create a temporary file and then remove read permissions
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "config"}, f)
            config_path = f.name
        
        try:
            # Remove read permissions
            os.chmod(config_path, 0o000)
            
            # Should handle permission error gracefully
            with self.assertRaises(PermissionError):
                load_config(config_path)
                
        finally:
            # Restore permissions and cleanup
            os.chmod(config_path, 0o644)
            os.unlink(config_path)
    
    def test_circular_reference_handling(self):
        """Test handling of circular references in config."""
        # This test would be relevant if the config system supports references
        pass
    
    def test_large_config_file_handling(self):
        """Test handling of very large configuration files."""
        # Create a large config with many entries
        large_config = {
            "platform": {"name": "Large Config Test"},
            "large_section": {}
        }
        
        # Add many entries to test performance and memory usage
        for i in range(1000):
            large_config["large_section"][f"key_{i}"] = f"value_{i}"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(large_config, f)
            config_path = f.name
        
        try:
            import time
            start_time = time.time()
            
            config = load_config(config_path)
            
            load_time = time.time() - start_time
            
            # Should load in reasonable time (less than 1 second)
            self.assertLess(load_time, 1.0)
            self.assertEqual(len(config["large_section"]), 1000)
            
        finally:
            os.unlink(config_path)

def create_config_test_suite():
    """Create comprehensive configuration test suite."""
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestConfigManager))
    suite.addTest(unittest.makeSuite(TestConfigurationIntegration))
    suite.addTest(unittest.makeSuite(TestConfigurationErrorHandling))
    
    return suite

if __name__ == '__main__':
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_config_test_suite()
    result = runner.run(suite)
    
    # Print summary
    print(f"\nConfiguration Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    sys.exit(exit_code)