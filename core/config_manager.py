#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Enhanced Configuration Manager - G6.1 Platform v2.0
Author: AI Assistant (Strict config segregation and validation)

Features:
- JSON configuration with .env override
- No dual setting conflicts
- Validation and defaults
- Dynamic configuration updates
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Union, Optional, List
from datetime import datetime
import threading
from dotenv import load_dotenv

class ConfigurationManager:
    """🔧 Enhanced configuration manager with strict segregation."""
    
    # Environment variables that are allowed (security-sensitive only)
    ENV_ALLOWED_KEYS = {
        'KITE_API_KEY': str,
        'KITE_API_SECRET': str, 
        'KITE_ACCESS_TOKEN': str,
        'INFLUXDB_TOKEN': str,
        'INFLUXDB_URL': str,
        'DATABASE_PASSWORD': str,
        'WEBHOOK_URL': str,
        'G6_DEBUG_MODE': bool,
        'G6_MOCK_MODE': bool
    }
    
    def __init__(self, config_file: str = "config.json", template_file: str = "config_template.json"):
        """Initialize configuration manager."""
        self.config_file = Path(config_file)
        self.template_file = Path(template_file)
        self.config_lock = threading.RLock()
        
        # Load environment first
        load_dotenv()
        
        # Configuration storage
        self._config = {}
        self._env_overrides = {}
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.ConfigManager")
        
        # Load and validate configuration
        self._load_configuration()
        self._validate_configuration()
        
        self.logger.info("✅ Configuration Manager initialized")
    
    def _load_configuration(self):
        """📖 Load configuration from JSON and environment."""
        try:
            # Load JSON configuration
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
                self.logger.info(f"✅ Loaded configuration from {self.config_file}")
            elif self.template_file.exists():
                # Use template as default
                with open(self.template_file, 'r') as f:
                    self._config = json.load(f)
                self.logger.info(f"⚠️ Using template config from {self.template_file}")
                # Save as actual config
                self.save_configuration()
            else:
                raise FileNotFoundError(f"No configuration file found: {self.config_file}")
            
            # Load environment overrides (only allowed keys)
            self._load_env_overrides()
            
        except Exception as e:
            self.logger.error(f"🔴 Configuration loading failed: {e}")
            raise
    
    def _load_env_overrides(self):
        """🌍 Load environment variable overrides."""
        self._env_overrides = {}
        
        for env_key, expected_type in self.ENV_ALLOWED_KEYS.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                try:
                    # Convert to expected type
                    if expected_type == bool:
                        converted_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif expected_type == int:
                        converted_value = int(env_value)
                    elif expected_type == float:
                        converted_value = float(env_value)
                    else:
                        converted_value = env_value
                    
                    self._env_overrides[env_key] = converted_value
                    self.logger.debug(f"🌍 Environment override: {env_key}")
                    
                except ValueError as e:
                    self.logger.warning(f"⚠️ Invalid environment value for {env_key}: {e}")
        
        if self._env_overrides:
            self.logger.info(f"✅ Loaded {len(self._env_overrides)} environment overrides")
    
    def _validate_configuration(self):
        """✅ Validate configuration structure and values."""
        required_sections = ['platform', 'market', 'data_collection', 'storage']
        
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate indices
        indices = self.get('market.indices', [])
        if not indices:
            raise ValueError("No market indices configured")
        
        # Validate strike configurations
        strike_config = self.get('data_collection.options.strike_configuration', {})
        if not any(config.get('enabled', False) for config in strike_config.values()):
            self.logger.warning("⚠️ No strike configurations enabled")
        
        # Validate storage
        if not self.get('storage.csv.enabled', False) and not self.get('storage.influxdb.enabled', False):
            self.logger.warning("⚠️ No storage backends enabled")
        
        self.logger.info("✅ Configuration validation passed")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """🔍 Get configuration value by dot notation path."""
        try:
            # Check environment overrides first (for security keys only)
            env_key = self._get_env_key_for_path(key_path)
            if env_key and env_key in self._env_overrides:
                return self._env_overrides[env_key]
            
            # Navigate through JSON config
            keys = key_path.split('.')
            value = self._config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.debug(f"🔍 Config get error for '{key_path}': {e}")
            return default
    
    def set(self, key_path: str, value: Any, save: bool = True):
        """📝 Set configuration value (JSON only, not env overrides)."""
        with self.config_lock:
            try:
                keys = key_path.split('.')
                config = self._config
                
                # Navigate to parent
                for key in keys[:-1]:
                    if key not in config:
                        config[key] = {}
                    config = config[key]
                
                # Set final value
                config[keys[-1]] = value
                
                if save:
                    self.save_configuration()
                
                self.logger.debug(f"📝 Set config: {key_path} = {value}")
                
            except Exception as e:
                self.logger.error(f"🔴 Config set error for '{key_path}': {e}")
                raise
    
    def _get_env_key_for_path(self, key_path: str) -> Optional[str]:
        """🌍 Map config path to environment key if allowed."""
        path_to_env = {
            'security.kite.api_key': 'KITE_API_KEY',
            'security.kite.api_secret': 'KITE_API_SECRET',
            'security.kite.access_token': 'KITE_ACCESS_TOKEN',
            'storage.influxdb.token': 'INFLUXDB_TOKEN',
            'storage.influxdb.url': 'INFLUXDB_URL',
            'development.debug_mode': 'G6_DEBUG_MODE',
            'development.mock_data.enabled': 'G6_MOCK_MODE'
        }
        
        return path_to_env.get(key_path)
    
    def get_indices(self) -> List[str]:
        """📊 Get configured market indices."""
        return self.get('market.indices', ['NIFTY', 'BANKNIFTY'])
    
    def get_strike_offsets(self, index_name: str = None) -> List[int]:
        """🎯 Get strike offsets based on configuration."""
        strike_config = self.get('data_collection.options.strike_configuration', {})
        
        # Check custom offsets first
        custom_config = strike_config.get('custom_offsets', {})
        if custom_config.get('enabled', False) and index_name:
            offsets = custom_config.get(index_name, [])
            if offsets:
                return offsets
        
        # Check asymmetric configuration
        asymmetric_config = strike_config.get('asymmetric_otm', {})
        if asymmetric_config.get('enabled', False):
            call_strikes = asymmetric_config.get('call_strikes', [0, 1, 2])
            put_strikes = asymmetric_config.get('put_strikes', [0, -1, -2])
            # Combine and sort unique offsets
            return sorted(set(call_strikes + put_strikes))
        
        # Default to symmetric configuration
        symmetric_config = strike_config.get('symmetric_otm', {})
        if symmetric_config.get('enabled', True):
            return symmetric_config.get('offsets', [-2, -1, 0, 1, 2])
        
        # Fallback
        return [-2, -1, 0, 1, 2]
    
    def get_data_fields(self) -> Dict[str, List[str]]:
        """📋 Get configured data fields for collection."""
        data_fields = self.get('data_collection.options.data_fields', {})
        
        fields = {}
        fields['basic'] = data_fields.get('basic', ['tradingsymbol', 'strike', 'expiry', 'option_type', 'last_price'])
        fields['pricing'] = data_fields.get('pricing', ['volume', 'oi', 'change', 'pchange'])
        
        # Only include greeks if analytics is enabled
        if self.get('analytics.greeks_calculation.enabled', True):
            fields['greeks'] = data_fields.get('greeks', ['delta', 'gamma', 'theta', 'vega'])
        
        # Only include market depth if enabled
        market_depth = data_fields.get('market_depth', {})
        if market_depth.get('enabled', False):
            fields['market_depth'] = market_depth.get('fields', ['bid', 'ask'])
        
        return fields
    
    def get_rate_limits(self) -> Dict[str, int]:
        """🚦 Get API rate limiting configuration."""
        perf_config = self.get('data_collection.performance', {})
        rate_config = perf_config.get('rate_limiting', {})
        
        return {
            'requests_per_minute': rate_config.get('requests_per_minute', 200),
            'burst_allowance': rate_config.get('burst_allowance', 50),
            'max_concurrent': perf_config.get('max_concurrent_requests', 10)
        }
    
    def is_market_depth_enabled(self) -> bool:
        """📊 Check if market depth collection is enabled."""
        return self.get('data_collection.options.data_fields.market_depth.enabled', False)
    
    def is_greeks_redundancy_avoided(self) -> bool:
        """⚖️ Check if Greeks calculation redundancy should be avoided."""
        return self.get('data_collection.options.data_fields.exclude_redundant', True)
    
    def get_log_level(self) -> str:
        """📝 Get logging level."""
        debug_level = self.get('platform.debug_level', 'info')
        
        # Check environment override
        if self._env_overrides.get('G6_DEBUG_MODE', False):
            return 'debug'
        
        return debug_level
    
    def get_log_condensation(self) -> str:
        """📝 Get log condensation setting."""
        return self.get('platform.log_condensation', 'dynamic')
    
    def save_configuration(self):
        """💾 Save current configuration to file."""
        with self.config_lock:
            try:
                # Add metadata
                self._config['_metadata'] = {
                    'saved_at': datetime.now().isoformat(),
                    'version': self.get('platform.version', '2.0.0')
                }
                
                with open(self.config_file, 'w') as f:
                    json.dump(self._config, f, indent=2)
                
                self.logger.info(f"💾 Configuration saved to {self.config_file}")
                
            except Exception as e:
                self.logger.error(f"🔴 Failed to save configuration: {e}")
                raise
    
    def reload_configuration(self):
        """🔄 Reload configuration from file and environment."""
        with self.config_lock:
            self.logger.info("🔄 Reloading configuration...")
            self._load_configuration()
            self._validate_configuration()
            self.logger.info("✅ Configuration reloaded")
    
    def get_all_metrics_computed(self) -> Dict[str, List[str]]:
        """📊 Get comprehensive list of all metrics and stats being computed."""
        return {
            'platform_metrics': [
                'uptime', 'total_requests', 'successful_requests', 'failed_requests',
                'average_response_time', 'memory_usage', 'cpu_usage'
            ],
            'data_collection_metrics': [
                'collection_count', 'successful_collections', 'failed_collections',
                'options_processed', 'data_quality_score', 'api_rate_limit_hits',
                'cache_hit_rate', 'batch_efficiency'
            ],
            'kite_provider_metrics': [
                'api_calls_made', 'api_failures', 'rate_limit_breaches',
                'connection_uptime', 'average_latency', 'data_freshness'
            ],
            'analytics_metrics': [
                'greeks_calculations', 'iv_calculations', 'pcr_values',
                'volatility_surface_points', 'gamma_exposure', 'delta_hedging_signals'
            ],
            'storage_metrics': [
                'records_written', 'storage_errors', 'file_rotations',
                'backup_creations', 'disk_usage', 'write_performance'
            ],
            'health_metrics': [
                'component_health_status', 'alert_triggers', 'error_rates',
                'performance_degradation', 'resource_utilization'
            ]
        }
    
    def get_config_summary(self) -> Dict[str, Any]:
        """📋 Get configuration summary for display."""
        return {
            'platform': {
                'name': self.get('platform.name'),
                'version': self.get('platform.version'),
                'mode': self.get('platform.mode'),
                'debug_level': self.get_log_level()
            },
            'market': {
                'indices': self.get_indices(),
                'collection_interval': self.get('market.collection_interval'),
                'trading_hours': self.get('market.trading_hours')
            },
            'data_collection': {
                'strike_offsets': self.get_strike_offsets(),
                'market_depth_enabled': self.is_market_depth_enabled(),
                'rate_limits': self.get_rate_limits()
            },
            'storage': {
                'csv_enabled': self.get('storage.csv.enabled'),
                'influxdb_enabled': self.get('storage.influxdb.enabled')
            },
            'environment_overrides': len(self._env_overrides)
        }

# Global configuration instance
_config_manager = None

def get_config() -> ConfigurationManager:
    """🔧 Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager

def reload_config():
    """🔄 Reload global configuration."""
    global _config_manager
    if _config_manager:
        _config_manager.reload_configuration()
    else:
        _config_manager = ConfigurationManager()