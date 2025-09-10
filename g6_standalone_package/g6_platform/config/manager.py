#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Configuration Manager - G6 Platform v3.0
Unified configuration management with enhanced validation and security.

Features:
- Strict separation: JSON for app config, env vars for secrets
- Comprehensive validation with detailed error reporting  
- Hot-reloading with change detection
- Environment override with security controls
- Thread-safe configuration access
- Path resolution and validation
"""

import os
import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Union, Optional, List, Set
from datetime import datetime
from dataclasses import dataclass, field
from dotenv import load_dotenv
import copy

logger = logging.getLogger(__name__)

@dataclass
class ValidationError:
    """Configuration validation error details."""
    field: str
    message: str
    value: Any = None
    severity: str = "error"  # error, warning, info

@dataclass 
class ConfigState:
    """Configuration state tracking."""
    loaded_at: datetime
    file_path: Optional[Path] = None
    file_mtime: Optional[float] = None
    env_overrides: Dict[str, Any] = field(default_factory=dict)
    validation_errors: List[ValidationError] = field(default_factory=list)
    last_reload: Optional[datetime] = None

class ConfigurationManager:
    """
    🔧 Enhanced configuration manager with enterprise-grade features.
    
    Provides thread-safe, validated configuration management with automatic
    reloading, environment overrides, and comprehensive error handling.
    """
    
    # Security-sensitive environment variables (only these can override config)
    ENV_SECURITY_VARS = {
        'KITE_API_KEY', 'KITE_API_SECRET', 'KITE_ACCESS_TOKEN',
        'INFLUXDB_TOKEN', 'INFLUXDB_URL', 'DATABASE_PASSWORD', 
        'WEBHOOK_URL', 'REDIS_PASSWORD', 'SSL_CERT_PATH'
    }
    
    # Control environment variables (non-sensitive overrides)
    ENV_CONTROL_VARS = {
        'G6_DEBUG_MODE': bool,
        'G6_MOCK_MODE': bool, 
        'G6_LOG_LEVEL': str,
        'G6_MAX_WORKERS': int,
        'G6_RATE_LIMIT_RPM': int,
        'G6_CACHE_TTL': int,
        'G6_BATCH_SIZE': int
    }
    
    def __init__(self, 
                 config_file: Union[str, Path] = "config.json",
                 template_file: Union[str, Path] = "config_template.json",
                 auto_reload: bool = True,
                 strict_validation: bool = True):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to main configuration file
            template_file: Path to configuration template  
            auto_reload: Enable automatic configuration reloading
            strict_validation: Enable strict validation mode
        """
        self.config_file = Path(config_file).resolve()
        self.template_file = Path(template_file).resolve()
        self.auto_reload = auto_reload
        self.strict_validation = strict_validation
        
        # Thread safety
        self._lock = threading.RLock()
        self._config: Dict[str, Any] = {}
        self._state = ConfigState(loaded_at=datetime.now())
        
        # Load environment variables
        load_dotenv(override=False)  # Don't override existing env vars
        
        # Initialize configuration
        self._load_configuration()
        
        # Start auto-reload if enabled
        if auto_reload:
            self._start_auto_reload()
    
    def _load_configuration(self) -> None:
        """Load and validate configuration from file and environment."""
        with self._lock:
            try:
                # Load base configuration
                config = self._load_config_file()
                
                # Apply environment overrides
                config = self._apply_env_overrides(config)
                
                # Validate configuration
                errors = self._validate_configuration(config)
                
                # Handle validation errors
                if errors and self.strict_validation:
                    error_msg = "Configuration validation failed:\n" + "\n".join(
                        f"  - {err.field}: {err.message}" for err in errors
                    )
                    raise ValueError(error_msg)
                
                # Update state
                self._config = config
                self._state.validation_errors = errors
                self._state.last_reload = datetime.now()
                
                if self.config_file.exists():
                    self._state.file_mtime = self.config_file.stat().st_mtime
                
                logger.info(f"Configuration loaded successfully from {self.config_file}")
                if errors:
                    logger.warning(f"Configuration has {len(errors)} validation warnings")
                
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                if not self._config:  # No fallback config available
                    raise
    
    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration from JSON file with fallbacks."""
        # Try main config file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.debug(f"Loaded config from {self.config_file}")
                return config
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load {self.config_file}: {e}")
        
        # Try template file as fallback  
        if self.template_file.exists():
            try:
                with open(self.template_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.warning(f"Using template config from {self.template_file}")
                return config
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load template {self.template_file}: {e}")
        
        # Return minimal default configuration
        logger.warning("No config files found, using minimal defaults")
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get minimal default configuration."""
        return {
            "platform": {
                "name": "G6 Platform",
                "version": "3.0.0",
                "mode": "development"
            },
            "market": {
                "indices": ["NIFTY", "BANKNIFTY"],
                "collection_interval": 60,
                "trading_hours": {
                    "start": "09:15",
                    "end": "15:30", 
                    "timezone": "Asia/Kolkata"
                }
            },
            "data_collection": {
                "performance": {
                    "rate_limiting": {
                        "requests_per_minute": 100
                    }
                }
            },
            "storage": {
                "csv": {
                    "enabled": True,
                    "base_path": "data/csv"
                }
            },
            "logging": {
                "level": "INFO",
                "console_output": True
            }
        }
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        config = copy.deepcopy(config)
        overrides = {}
        
        # Security-sensitive overrides (direct replacement)
        for env_var in self.ENV_SECURITY_VARS:
            value = os.getenv(env_var)
            if value:
                overrides[env_var.lower()] = value
        
        # Control overrides (typed conversion)
        for env_var, var_type in self.ENV_CONTROL_VARS.items():
            value = os.getenv(env_var)
            if value:
                try:
                    if var_type == bool:
                        typed_value = value.lower() in ('true', '1', 'yes', 'on')
                    elif var_type == int:
                        typed_value = int(value)
                    else:
                        typed_value = value
                    
                    # Map to config path
                    config_key = env_var.replace('G6_', '').lower()
                    overrides[config_key] = typed_value
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid environment variable {env_var}={value}: {e}")
        
        # Store overrides in state
        self._state.env_overrides = overrides
        
        # Apply overrides to config
        for key, value in overrides.items():
            if key.startswith('kite_'):
                # API credentials
                config.setdefault('api', {}).setdefault('kite', {})[key.replace('kite_', '')] = value
            elif key in ('debug_mode', 'log_level'):
                # Logging configuration
                config.setdefault('logging', {})[key] = value
            elif key in ('rate_limit_rpm', 'cache_ttl', 'batch_size', 'max_workers'):
                # Performance settings
                config.setdefault('data_collection', {}).setdefault('performance', {})[key] = value
        
        return config
    
    def _validate_configuration(self, config: Dict[str, Any]) -> List[ValidationError]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Required sections
        required_sections = ['platform', 'market', 'data_collection', 'storage']
        for section in required_sections:
            if section not in config:
                errors.append(ValidationError(
                    field=section,
                    message=f"Required section '{section}' is missing"
                ))
        
        # Platform validation
        if 'platform' in config:
            platform = config['platform']
            if 'name' not in platform:
                errors.append(ValidationError(
                    field='platform.name',
                    message="Platform name is required"
                ))
            if 'version' not in platform:
                errors.append(ValidationError(
                    field='platform.version', 
                    message="Platform version is required"
                ))
        
        # Market validation
        if 'market' in config:
            market = config['market']
            if 'indices' not in market or not market['indices']:
                errors.append(ValidationError(
                    field='market.indices',
                    message="At least one market index must be configured"
                ))
            
            # Collection interval validation
            interval = market.get('collection_interval', 0)
            if not isinstance(interval, int) or interval <= 0:
                errors.append(ValidationError(
                    field='market.collection_interval',
                    message="Collection interval must be a positive integer",
                    value=interval
                ))
        
        # Storage validation
        if 'storage' in config:
            storage = config['storage']
            csv_config = storage.get('csv', {})
            influx_config = storage.get('influxdb', {})
            
            # At least one storage backend must be enabled
            csv_enabled = csv_config.get('enabled', False)
            influx_enabled = influx_config.get('enabled', False)
            
            if not csv_enabled and not influx_enabled:
                errors.append(ValidationError(
                    field='storage',
                    message="At least one storage backend (CSV or InfluxDB) must be enabled"
                ))
        
        # Rate limiting validation
        rate_config = config.get('data_collection', {}).get('performance', {}).get('rate_limiting', {})
        rpm = rate_config.get('requests_per_minute', 0)
        if rpm > 300:  # Kite API hard limit
            errors.append(ValidationError(
                field='data_collection.performance.rate_limiting.requests_per_minute',
                message="Rate limit exceeds Kite API maximum (300 req/min)",
                value=rpm,
                severity="warning"
            ))
        
        return errors
    
    def _start_auto_reload(self) -> None:
        """Start automatic configuration reloading in background thread."""
        def reload_worker():
            while True:
                try:
                    # Check file modification time
                    if self.config_file.exists():
                        current_mtime = self.config_file.stat().st_mtime
                        if (self._state.file_mtime and 
                            current_mtime > self._state.file_mtime):
                            logger.info("Configuration file changed, reloading...")
                            self._load_configuration()
                    
                    # Sleep for 5 seconds before next check
                    threading.Event().wait(5)
                    
                except Exception as e:
                    logger.error(f"Auto-reload error: {e}")
                    threading.Event().wait(30)  # Wait longer on error
        
        reload_thread = threading.Thread(target=reload_worker, daemon=True)
        reload_thread.start()
        logger.debug("Auto-reload thread started")
    
    # Public API methods
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.
        
        Args:
            key: Configuration key in dot notation (e.g., 'market.indices')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        with self._lock:
            try:
                keys = key.split('.')
                value = self._config
                
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default
                
                return value
            except Exception:
                return default
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration as a dictionary."""
        with self._lock:
            return copy.deepcopy(self._config)
    
    def reload(self) -> bool:
        """
        Manually reload configuration.
        
        Returns:
            True if reload was successful, False otherwise
        """
        try:
            self._load_configuration()
            return True
        except Exception as e:
            logger.error(f"Manual reload failed: {e}")
            return False
    
    def get_validation_errors(self) -> List[ValidationError]:
        """Get current configuration validation errors."""
        with self._lock:
            return copy.deepcopy(self._state.validation_errors)
    
    def get_state(self) -> Dict[str, Any]:
        """Get configuration manager state information."""
        with self._lock:
            return {
                'loaded_at': self._state.loaded_at.isoformat(),
                'file_path': str(self._state.file_path) if self._state.file_path else None,
                'last_reload': self._state.last_reload.isoformat() if self._state.last_reload else None,
                'env_overrides_count': len(self._state.env_overrides),
                'validation_errors_count': len(self._state.validation_errors),
                'auto_reload_enabled': self.auto_reload
            }
    
    def is_valid(self) -> bool:
        """Check if current configuration is valid (no errors)."""
        errors = self.get_validation_errors()
        return not any(err.severity == 'error' for err in errors)

# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None

def get_config_manager() -> ConfigurationManager:
    """Get or create global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager

def get_config() -> Dict[str, Any]:
    """Get current configuration dictionary."""
    return get_config_manager().get_all()

def get_config_value(key: str, default: Any = None) -> Any:
    """Get specific configuration value."""
    return get_config_manager().get(key, default)

def reload_config() -> bool:
    """Reload configuration from files."""
    return get_config_manager().reload()