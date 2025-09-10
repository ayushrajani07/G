# G6.1 Options Analytics Platform - Project Organization

## Core Project Files (Final Working Components)

### Main Application Core
- `g6_platform_main_FINAL_WORKING.py` - **PRIMARY ENTRY POINT** 
- `config.json` - Main configuration file
- `config_manager.py` - Configuration management
- `requirements.txt` - Dependencies

### Data Collection (collectors/)
- `atm_options_collector.py` - ATM options data collection
- `overview_collector.py` - Market overview generation  
- `kite_provider_complete.py` - Kite Connect API integration
- `market_data_collector.py` - Generic market data collection

### Analytics Engine (analytics/)
- `analytics_engine.py` - Core analytics (IV, Greeks, PCR)
- `volatility_analyzer.py` - Volatility surface analysis
- `risk_analyzer.py` - Risk metrics calculation
- `overview_generator.py` - Market overview analytics

### Data Storage (storage/)
- `enhanced_csv_sink_complete.py` - Enhanced CSV storage
- `influxdb_sink.py` - InfluxDB time-series storage
- `data_archiver.py` - Data archival and backup
- `data_models.py` - Data structure definitions

### Monitoring & Health (monitoring/)
- `health_monitor.py` - System health monitoring
- `metrics_system.py` - Performance metrics collection
- `performance_monitor.py` - Performance tracking
- `metrics_dashboard.py` - Metrics display

### User Interface (ui/)
- `kite_login_and_launch_FINAL_WORKING.py` - **MAIN LAUNCHER**
- `enhanced_terminal_ui.py` - Rich terminal interface
- `web_launcher_beautiful.py` - Web-based interface

### Utilities (utils/)
- `token_manager.py` - Token management and security
- `path_resolver_complete.py` - Cross-platform path handling
- `market_hours_complete.py` - Market hours and calendar
- `quick_platform_diagnostic.py` - Platform diagnostics

### Configuration & Setup (core/)
- `enhanced_config_complete.py` - Advanced configuration
- `setup_fixed.py` - Setup and installation

### Testing (tests/)
- `test_analytics.py` - Analytics tests
- `test_collectors.py` - Collector tests  
- `test_config.py` - Configuration tests
- `mock_testing_framework.py` - Mock testing framework
- `quick_test.py` - Quick validation tests

## Development/Experimental Files (archive/)

### Launcher Iterations
- `kite_login_and_launch.py` - Original launcher
- `kite_login_and_launch_v2.py` - Version 2
- `final_launcher_solution.py` - Alternative solution
- `ultimate_*_launcher.py` - Various experimental launchers
- `enhanced_*_launcher.py` - Enhanced versions
- `fixed_*_launcher.py` - Bug fix versions
- `nonblocking_rich_launcher.py` - Non-blocking version

### Platform Iterations  
- `g6_platform_main.py` - Original platform
- `g6_platform_main_v2.py` - Version 2
- `g6_platform_main_fixed.py` - Bug fixes
- `g6_enhanced_data_platform.py` - Enhanced version
- `g6_ultimate_data_platform.py` - Ultimate version
- `main_application_complete.py` - Complete application

### Other Development Files
- `enhanced_atm_collector.py` - Enhanced ATM collector
- `enhanced_kite_provider.py` - Enhanced Kite provider
- `enhanced_csv_sink_complete_FINAL.py` - Alternative CSV sink
- `token_debug_and_fix.py` - Token debugging
- Various other `enhanced_*`, `ultimate_*`, `fixed_*` files

## Recommended Organization

```
G6-Platform/
├── core/                          # Main application and config
│   ├── g6_platform_main.py       # Renamed from FINAL_WORKING
│   ├── config_manager.py
│   ├── enhanced_config_complete.py
│   └── setup.py                   # Renamed from setup_fixed
│
├── collectors/                    # Data collection modules
│   ├── atm_options_collector.py
│   ├── overview_collector.py
│   ├── kite_provider.py           # Renamed from complete
│   └── market_data_collector.py
│
├── analytics/                     # Analytics and calculations
│   ├── analytics_engine.py
│   ├── volatility_analyzer.py
│   ├── risk_analyzer.py
│   └── overview_generator.py
│
├── storage/                       # Data persistence
│   ├── csv_sink.py               # Renamed from enhanced_complete
│   ├── influxdb_sink.py
│   ├── data_archiver.py
│   └── data_models.py
│
├── monitoring/                    # Health and metrics
│   ├── health_monitor.py
│   ├── metrics_system.py
│   ├── performance_monitor.py
│   └── metrics_dashboard.py
│
├── ui/                           # User interfaces
│   ├── launcher.py               # Renamed from FINAL_WORKING
│   ├── terminal_ui.py            # Renamed from enhanced
│   └── web_launcher.py           # Renamed from beautiful
│
├── utils/                        # Utilities and helpers
│   ├── token_manager.py
│   ├── path_resolver.py          # Renamed from complete
│   ├── market_hours.py           # Renamed from complete
│   └── diagnostics.py            # Renamed from quick_platform
│
├── tests/                        # Test suites
│   ├── test_analytics.py
│   ├── test_collectors.py
│   ├── test_config.py
│   ├── mock_framework.py         # Renamed from testing
│   └── quick_test.py
│
├── archive/                      # Development iterations
│   └── [all experimental/dev files]
│
├── data/                         # Data storage
│   ├── csv/
│   ├── logs/
│   └── cache/
│
├── docs/                         # Documentation
│   ├── README.md
│   ├── API_REFERENCE.md
│   ├── CONFIGURATION_GUIDE.md
│   └── TROUBLESHOOTING.md
│
├── config.json                   # Main configuration
├── requirements.txt              # Dependencies
└── .env.template                 # Environment template
```

## Benefits of This Organization

1. **Clear Structure** - Easy to navigate and understand
2. **Separation of Concerns** - Each folder has a specific purpose
3. **Maintainability** - Easier to maintain and update components
4. **Development Workflow** - Clear distinction between final and experimental code
5. **Production Ready** - Clean structure for deployment and packaging