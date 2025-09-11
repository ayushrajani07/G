# G6 Options Analytics Platform - Standalone Package

## What's This?

This standalone package is a **clean, production-ready version** of the G6 Options Analytics Platform, created by extracting and consolidating the essential components from a cluttered repository of 60+ Python files.

## Architecture Overview

The platform follows a clean, modular architecture:

### Core Components

1. **g6_platform.core**: Platform orchestration and lifecycle management
2. **g6_platform.api**: Kite Connect API integration and secure token management  
3. **g6_platform.collectors**: Data collection modules for options instruments
4. **g6_platform.storage**: Storage backends for CSV and InfluxDB persistence
5. **g6_platform.analytics**: Analytics engines for Greeks, volatility, and PCR calculations
6. **g6_platform.monitoring**: Health checks, performance monitoring, and metrics
7. **g6_platform.config**: Configuration management and validation
8. **g6_platform.utils**: Utility functions and data models

### Key Features

- **Real-time Data Collection**: Continuous options data from NSE/BSE
- **Multi-Index Support**: NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY
- **Advanced Analytics**: Greeks calculation, volatility analysis, PCR analysis
- **Dual Storage**: CSV files with rotation + InfluxDB time-series storage
- **Rich Monitoring**: Health checks, performance metrics, alerting
- **Production Ready**: Comprehensive error handling, logging, recovery

### Supported Markets & Instruments

| Market | Instruments |
|--------|------------|
| **NSE** | NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY |
| **BSE** | SENSEX, BANKEX |

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Configuration

1. Copy the configuration template:
   ```bash
   cp config_template.json config.json
   ```

2. Edit `config.json` with your settings:
   - Kite Connect API credentials
   - Storage preferences
   - Collection intervals
   - Monitoring settings

## Usage

### Command Line

```bash
# Run with default settings
python -m g6_platform

# Run with debug logging
python -m g6_platform --debug

# Use custom config
python -m g6_platform --config custom.json

# Run in mock mode (for testing)
python -m g6_platform --mock
```

### Programmatic Usage

```python
from g6_platform.core.platform import G6Platform

# Create platform instance
platform = G6Platform(config_file='config.json')

# Run the platform
platform.run()
```

## Examples

See the `examples/` directory for sample usage patterns.

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

### Code Style

The codebase follows PEP 8 standards with Black formatting.

## Monitoring

The platform includes comprehensive monitoring:

- **Health Checks**: API connectivity, storage availability, system resources
- **Performance Metrics**: Data collection rates, processing latencies, error rates
- **Alerting**: Configurable thresholds for critical conditions

## Architecture Decisions

### Why This Structure?

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Dependency Injection**: Components are loosely coupled through configuration
3. **Error Resilience**: Comprehensive error handling with graceful degradation
4. **Extensibility**: Easy to add new instruments, storage backends, or analytics
5. **Testing**: Modular design enables effective unit and integration testing

### Removed Components

From the original 60+ file repository, we removed:
- 20+ duplicate launcher implementations
- Multiple experimental versions of the same functionality
- Test files and development iterations  
- Outdated/non-functional implementations
- Redundant utility scripts

### Performance Considerations

- **Async I/O**: Non-blocking operations for API calls and storage
- **Connection Pooling**: Efficient resource utilization for database connections
- **Caching**: Intelligent caching of frequently accessed data
- **Rate Limiting**: Respectful API usage within exchange limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

MIT License - See LICENSE file for details.