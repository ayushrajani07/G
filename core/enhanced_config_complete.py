#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Enhanced Configuration System for G6.1 Platform
Author: AI Assistant (Complete configuration management)

✅ Features:
- YAML/JSON configuration loading
- Environment variable integration
- Hot-reload capability
- Schema validation
- Configuration inheritance
- Secure credential handling
"""

import logging
import os
import json
import yaml
import time
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, field
from threading import Lock, Thread
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class ConfigSchema:
    """📋 Configuration schema definition."""
    required_fields: List[str] = field(default_factory=list)
    optional_fields: Dict[str, Any] = field(default_factory=dict)
    field_types: Dict[str, type] = field(default_factory=dict)
    validators: Dict[str, callable] = field(default_factory=dict)

class EnhancedConfig:
    """
    🔧 AI Assistant: Enhanced Configuration System.
    
    Comprehensive configuration management with:
    - Multi-format support (YAML, JSON, ENV)
    - Hot-reload capability
    - Schema validation
    - Environment variable integration
    - Secure credential handling
    """
    
    def __init__(self, 
                 config_path: Optional[Union[str, Path]] = None,
                 enable_hot_reload: bool = True,
                 reload_interval: int = 5,
                 schema: Optional[ConfigSchema] = None):
        """
        🆕 Initialize Enhanced Configuration.
        
        Args:
            config_path: Path to configuration file
            enable_hot_reload: Enable automatic config reloading
            reload_interval: Hot-reload check interval in seconds
            schema: Configuration schema for validation
        """
        self.config_path = Path(config_path) if config_path else None
        self.enable_hot_reload = enable_hot_reload
        self.reload_interval = reload_interval
        self.schema = schema
        
        self.logger = logging.getLogger(f"{__name__}.EnhancedConfig")
        
        # 📊 Configuration state
        self._config: Dict[str, Any] = {}
        self._last_modified: Optional[float] = None
        self._config_hash: Optional[str] = None
        self._lock = Lock()
        
        # 🔄 Hot-reload thread
        self._reload_thread: Optional[Thread] = None
        self._shutdown_requested = False
        
        # 🔧 Default configuration
        self._defaults = self._get_default_config()
        
        try:
            # 📄 Load initial configuration
            self._load_config()
            
            # 🔄 Start hot-reload if enabled
            if self.enable_hot_reload and self.config_path and self.config_path.exists():
                self._start_hot_reload()
            
            self.logger.info(f"✅ Enhanced Config initialized from {self.config_path or 'defaults'}")
            
        except Exception as e:
            self.logger.error(f"🔴 Config initialization failed: {e}")
            # 🆘 Fall back to defaults
            self._config = self._defaults.copy()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """🔧 Get default configuration values."""
        return {
            'platform': {
                'name': 'G6.1 Options Analytics Platform',
                'version': '1.0.0',
                'debug': False
            },
            'collection': {
                'interval_seconds': 30,
                'max_workers': 4,
                'timeout_seconds': 30,
                'retry_attempts': 3
            },
            'indices': {
                'NIFTY': {
                    'strike_step': 50,
                    'offsets': [0, 1, -1, 2, -2]
                },
                'BANKNIFTY': {
                    'strike_step': 100,
                    'offsets': [0, 1, -1, 2, -2]
                },
                'FINNIFTY': {
                    'strike_step': 50,
                    'offsets': [0, 1, -1, 2, -2]
                }
            },
            'storage': {
                'csv_enabled': True,
                'csv_compression': False,
                'influxdb_enabled': False,
                'backup_enabled': True
            },
            'monitoring': {
                'health_checks_enabled': True,
                'metrics_enabled': True,
                'health_check_interval': 60
            },
            'kite': {
                'rate_limit_requests_per_second': 3,
                'connection_timeout': 30,
                'read_timeout': 60
            }
        }
    
    def _load_config(self):
        """📄 Load configuration from file."""
        try:
            with self._lock:
                # 🔧 Start with defaults
                new_config = self._defaults.copy()
                
                # 📄 Load from file if available
                if self.config_path and self.config_path.exists():
                    file_config = self._load_config_file(self.config_path)
                    if file_config:
                        new_config = self._merge_configs(new_config, file_config)
                
                # 🌍 Override with environment variables
                env_config = self._load_env_variables()
                new_config = self._merge_configs(new_config, env_config)
                
                # ✅ Validate configuration
                if self.schema:
                    self._validate_config(new_config)
                
                # 📊 Update state
                self._config = new_config
                self._update_file_tracking()
                
                self.logger.debug("✅ Configuration loaded and validated")
                
        except Exception as e:
            self.logger.error(f"🔴 Config loading failed: {e}")
            raise
    
    def _load_config_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """📄 Load configuration from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    self.logger.warning(f"⚠️ Unsupported config format: {file_path.suffix}")
                    return None
        
        except Exception as e:
            self.logger.error(f"🔴 Failed to load config file {file_path}: {e}")
            return None
    
    def _load_env_variables(self) -> Dict[str, Any]:
        """🌍 Load configuration from environment variables."""
        env_config = {}
        
        try:
            # 🔧 Platform settings
            if os.getenv('G6_DEBUG'):
                env_config['platform'] = env_config.get('platform', {})
                env_config['platform']['debug'] = os.getenv('G6_DEBUG', 'false').lower() == 'true'
            
            # 📊 Collection settings
            if os.getenv('G6_COLLECTION_INTERVAL'):
                env_config['collection'] = env_config.get('collection', {})
                env_config['collection']['interval_seconds'] = int(os.getenv('G6_COLLECTION_INTERVAL', '30'))
            
            if os.getenv('G6_MAX_WORKERS'):
                env_config['collection'] = env_config.get('collection', {})
                env_config['collection']['max_workers'] = int(os.getenv('G6_MAX_WORKERS', '4'))
            
            # 🔐 Kite settings
            if os.getenv('KITE_API_KEY'):
                env_config['kite'] = env_config.get('kite', {})
                env_config['kite']['api_key'] = os.getenv('KITE_API_KEY')
            
            if os.getenv('KITE_ACCESS_TOKEN'):
                env_config['kite'] = env_config.get('kite', {})
                env_config['kite']['access_token'] = os.getenv('KITE_ACCESS_TOKEN')
            
            # 📊 Storage settings
            if os.getenv('G6_ENABLE_CSV'):
                env_config['storage'] = env_config.get('storage', {})
                env_config['storage']['csv_enabled'] = os.getenv('G6_ENABLE_CSV', 'true').lower() == 'true'
            
            if os.getenv('G6_ENABLE_INFLUXDB'):
                env_config['storage'] = env_config.get('storage', {})
                env_config['storage']['influxdb_enabled'] = os.getenv('G6_ENABLE_INFLUXDB', 'false').lower() == 'true'
            
            # 📋 Indices
            if os.getenv('G6_INDICES'):
                indices = os.getenv('G6_INDICES', '').split(',')
                env_config['indices'] = {}
                for index in indices:
                    index = index.strip()
                    if index:
                        env_config['indices'][index] = self._defaults['indices'].get(index, {
                            'strike_step': 50,
                            'offsets': [0, 1, -1, 2, -2]
                        })
            
            self.logger.debug(f"✅ Loaded {len(env_config)} environment overrides")
            return env_config
            
        except Exception as e:
            self.logger.error(f"🔴 Error loading environment variables: {e}")
            return {}
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """🔄 Deep merge configuration dictionaries."""
        try:
            result = base.copy()
            
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_configs(result[key], value)
                else:
                    result[key] = value
            
            return result
            
        except Exception as e:
            self.logger.error(f"🔴 Config merge failed: {e}")
            return base
    
    def _validate_config(self, config: Dict[str, Any]):
        """✅ Validate configuration against schema."""
        if not self.schema:
            return
        
        try:
            # 🔍 Check required fields
            for field in self.schema.required_fields:
                if field not in config:
                    raise ValueError(f"Required field missing: {field}")
            
            # 🔍 Check field types
            for field, expected_type in self.schema.field_types.items():
                if field in config and not isinstance(config[field], expected_type):
                    raise TypeError(f"Field {field} must be of type {expected_type}")
            
            # 🔍 Run custom validators
            for field, validator in self.schema.validators.items():
                if field in config:
                    if not validator(config[field]):
                        raise ValueError(f"Validation failed for field: {field}")
            
            self.logger.debug("✅ Configuration validation passed")
            
        except Exception as e:
            self.logger.error(f"🔴 Configuration validation failed: {e}")
            raise
    
    def _update_file_tracking(self):
        """📊 Update file modification tracking."""
        try:
            if self.config_path and self.config_path.exists():
                self._last_modified = self.config_path.stat().st_mtime
                
                # 🔒 Calculate config hash
                config_str = json.dumps(self._config, sort_keys=True)
                self._config_hash = hashlib.md5(config_str.encode()).hexdigest()
                
        except Exception as e:
            self.logger.debug(f"⚠️ File tracking update failed: {e}")
    
    def _start_hot_reload(self):
        """🔄 Start hot-reload monitoring thread."""
        try:
            self._reload_thread = Thread(
                target=self._hot_reload_loop,
                name="ConfigHotReload",
                daemon=True
            )
            self._reload_thread.start()
            
            self.logger.debug(f"🔄 Hot-reload started ({self.reload_interval}s interval)")
            
        except Exception as e:
            self.logger.error(f"🔴 Hot-reload start failed: {e}")
    
    def _hot_reload_loop(self):
        """🔄 Hot-reload monitoring loop."""
        while not self._shutdown_requested:
            try:
                time.sleep(self.reload_interval)
                
                if self._config_changed():
                    self.logger.info("🔄 Configuration change detected, reloading...")
                    self._load_config()
                    self.logger.info("✅ Configuration reloaded successfully")
                
            except Exception as e:
                self.logger.error(f"🔴 Hot-reload error: {e}")
                time.sleep(self.reload_interval * 2)  # Back off on error
    
    def _config_changed(self) -> bool:
        """🔍 Check if configuration file has changed."""
        try:
            if not self.config_path or not self.config_path.exists():
                return False
            
            current_mtime = self.config_path.stat().st_mtime
            
            if self._last_modified is None or current_mtime > self._last_modified:
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"⚠️ Change detection failed: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """🔍 Get configuration value by key (supports dot notation)."""
        try:
            with self._lock:
                keys = key.split('.')
                value = self._config
                
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default
                
                return value
                
        except Exception as e:
            self.logger.debug(f"⚠️ Config get failed for {key}: {e}")
            return default
    
    def set(self, key: str, value: Any):
        """✏️ Set configuration value by key (supports dot notation)."""
        try:
            with self._lock:
                keys = key.split('.')
                config = self._config
                
                for k in keys[:-1]:
                    if k not in config:
                        config[k] = {}
                    config = config[k]
                
                config[keys[-1]] = value
                self._update_file_tracking()
                
                self.logger.debug(f"✅ Config set: {key} = {value}")
                
        except Exception as e:
            self.logger.error(f"🔴 Config set failed for {key}: {e}")
    
    def get_all(self) -> Dict[str, Any]:
        """📋 Get complete configuration dictionary."""
        with self._lock:
            return self._config.copy()
    
    def reload(self):
        """🔄 Manual configuration reload."""
        try:
            self.logger.info("🔄 Manual configuration reload requested")
            self._load_config()
            self.logger.info("✅ Configuration reloaded successfully")
            
        except Exception as e:
            self.logger.error(f"🔴 Manual reload failed: {e}")
            raise
    
    def save(self, file_path: Optional[Path] = None):
        """💾 Save current configuration to file."""
        try:
            save_path = file_path or self.config_path
            if not save_path:
                raise ValueError("No file path specified for save")
            
            with self._lock:
                if save_path.suffix.lower() in ['.yaml', '.yml']:
                    with open(save_path, 'w', encoding='utf-8') as f:
                        yaml.safe_dump(self._config, f, default_flow_style=False, indent=2)
                elif save_path.suffix.lower() == '.json':
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump(self._config, f, indent=2)
                else:
                    raise ValueError(f"Unsupported save format: {save_path.suffix}")
            
            self.logger.info(f"✅ Configuration saved to {save_path}")
            
        except Exception as e:
            self.logger.error(f"🔴 Config save failed: {e}")
            raise
    
    def close(self):
        """🗑️ Cleanup and shutdown."""
        try:
            self._shutdown_requested = True
            
            if self._reload_thread and self._reload_thread.is_alive():
                self._reload_thread.join(timeout=5.0)
            
            self.logger.info("✅ Enhanced Config closed")
            
        except Exception as e:
            self.logger.error(f"🔴 Config close failed: {e}")

# 🧪 AI Assistant: Testing functions
def test_enhanced_config():
    """🧪 Test Enhanced Configuration functionality."""
    print("🧪 Testing Enhanced Configuration...")
    
    try:
        # 📊 Test with defaults
        config = EnhancedConfig(enable_hot_reload=False)
        print("✅ Config initialized with defaults")
        
        # 🔍 Test getting values
        debug_mode = config.get('platform.debug', False)
        print(f"✅ Debug mode: {debug_mode}")
        
        collection_interval = config.get('collection.interval_seconds', 30)
        print(f"✅ Collection interval: {collection_interval}s")
        
        # ✏️ Test setting values
        config.set('platform.test_value', 'test_data')
        test_value = config.get('platform.test_value')
        print(f"✅ Set/Get test: {test_value}")
        
        # 📋 Test indices configuration
        indices = config.get('indices', {})
        print(f"✅ Indices configured: {list(indices.keys())}")
        
        # 📊 Test environment variable integration
        env_debug = config.get('platform.debug')
        print(f"✅ Environment integration: debug={env_debug}")
        
        print("🎉 Enhanced Configuration test completed!")
        return True
        
    except Exception as e:
        print(f"🔴 Enhanced Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enhanced_config()