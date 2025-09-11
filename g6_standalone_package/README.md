# G6 Options Analytics Platform - Standalone Package

**Professional Options Trading Platform for Indian Markets**

This is a clean, standalone version of the G6 Options Analytics Platform, reorganized from the original scattered codebase into a maintainable, enterprise-grade package.

## 🎯 What's Different from Original Repository

**Before**: 60+ scattered Python files with mixed logic, redundant code, and multiple experimental implementations.

**After**: Clean, focused package with only essential, production-ready components.

### Removed Redundant Files
- 20+ duplicate launcher implementations
- Multiple experimental versions of the same functionality  
- Test files and development iterations
- Outdated/non-functional implementations

### Retained Essential Components
- Core platform orchestration
- Kite API integration and token management
- Data collection and analytics engines
- Storage backends (CSV and InfluxDB)
- Monitoring and health systems
- Configuration management

## 🏗️ Package Structure

```
g6_standalone_package/
├── g6_platform/              # Core package
│   ├── __init__.py
│   ├── core/                 # Platform orchestration
│   ├── api/                  # Kite Connect integration
│   ├── collectors/           # Data collection modules
│   ├── storage/              # Storage backends
│   ├── analytics/            # Analytics engines
│   ├── monitoring/           # Health and performance monitoring
│   ├── config/               # Configuration management
│   └── utils/                # Utilities
├── setup.py                  # Package installation
├── requirements.txt          # Dependencies
├── config_template.json      # Configuration template
├── examples/                 # Usage examples
└── docs/                     # Documentation
```

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure**:
   ```bash
   cp config_template.json config.json
   # Edit config.json with your settings
   ```

3. **Run**:
   ```bash
   python -m g6_platform
   ```

## 📋 Features

- Real-time options data collection from NSE/BSE
- Support for NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY
- Advanced analytics: Greeks, volatility, PCR analysis
- Multiple storage options: CSV files and InfluxDB
- Comprehensive monitoring and health checks
- Production-ready error handling and recovery

## 📄 License

MIT License - See LICENSE file for details.