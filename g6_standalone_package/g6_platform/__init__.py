#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 G6 Options Analytics Platform - Standalone Package
Professional Options Trading Platform for Indian Markets

This is a clean, standalone version of the G6 Options Analytics Platform,
reorganized from the original scattered codebase into a maintainable, 
enterprise-grade package.

Main package initialization with clean architecture and proper separation of concerns.
"""

__version__ = "3.0.0-standalone"
__author__ = "G6 Development Team"
__description__ = "Professional Options Analytics Platform for Indian Markets - Standalone Package"

# Version information
VERSION_INFO = {
    "major": 3,
    "minor": 0,
    "patch": 0,
    "release": "standalone"
}

# Package metadata
PACKAGE_INFO = {
    "name": "g6_platform_standalone",
    "version": __version__,
    "description": __description__,
    "supported_markets": ["NSE", "BSE"],
    "supported_instruments": ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"],
    "features": [
        "Real-time options data collection",
        "Advanced analytics and Greeks calculation", 
        "Multiple storage backends (CSV, InfluxDB)",
        "Rich terminal UI with live metrics",
        "Comprehensive monitoring and health checks",
        "Production-ready error handling and resilience",
        "Clean, standalone package architecture",
        "Removed redundant/experimental code"
    ],
    "improvements": [
        "Reduced from 60+ scattered files to focused modules",
        "Eliminated redundant launcher implementations", 
        "Consolidated duplicate functionality",
        "Enhanced error handling and recovery",
        "Simplified configuration management"
    ]
}

# Import core components for easy access
try:
    from .core.platform import G6Platform
    from .config.manager import ConfigurationManager
    from .api.kite_provider import KiteDataProvider
    from .monitoring.health import HealthMonitor
    
    __all__ = [
        'G6Platform',
        'ConfigurationManager', 
        'KiteDataProvider',
        'HealthMonitor',
        'VERSION_INFO',
        'PACKAGE_INFO'
    ]
    
except ImportError as e:
    # Allow partial imports during package construction
    __all__ = ['VERSION_INFO', 'PACKAGE_INFO']
    
def get_version() -> str:
    """Get the current version string."""
    return __version__

def get_package_info() -> dict:
    """Get comprehensive package information."""
    return PACKAGE_INFO.copy()