# G6.1 Platform API Reference

## Overview

The G6.1 Options Analytics Platform provides a comprehensive API for options data collection, analysis, and risk management. This document provides detailed API reference for all platform components.

## Table of Contents

1. [Data Collection APIs](#data-collection-apis)
2. [Analytics APIs](#analytics-apis)
3. [Risk Management APIs](#risk-management-apis)
4. [Storage APIs](#storage-apis)
5. [Monitoring APIs](#monitoring-apis)
6. [Configuration APIs](#configuration-apis)
7. [Error Handling](#error-handling)
8. [Authentication](#authentication)

---

## Data Collection APIs

### Market Data Collector

#### `MarketDataCollector`

Main class for collecting market data from multiple sources.

```python
class MarketDataCollector:
    def __init__(self, config: Dict[str, Any])
    def connect_all_sources() -> bool
    def get_market_data(self, symbol: str, use_cache: bool = True) -> Optional[MarketDataPoint]
    def get_options_chain(self, symbol: str, expiry: str, use_cache: bool = True) -> List[OptionsDataPoint]
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, MarketDataPoint]
    def get_health_status() -> Dict[str, Any]
```

**Parameters:**
- `config`: Configuration dictionary containing data source settings
- `symbol`: Market symbol (e.g., 'NIFTY', 'BANKNIFTY')
- `expiry`: Expiry date in YYYY-MM-DD format
- `use_cache`: Whether to use cached data (default: True)

**Returns:**
- `MarketDataPoint`: Standardized market data structure
- `OptionsDataPoint`: Standardized options data structure

**Example Usage:**
```python
config = {
    'cache_ttl': 60,
    'data_sources': {
        'kite_connect': {
            'api_key': 'your_api_key',
            'access_token': 'your_access_token',
            'primary': True
        }
    }
}

collector = MarketDataCollector(config)
collector.connect_all_sources()

# Get market data
nifty_data = collector.get_market_data('NIFTY')
print(f"NIFTY Price: {nifty_data.price}")

# Get options chain
options = collector.get_options_chain('NIFTY', '2024-12-26')
print(f"Options available: {len(options)}")
```

### Enhanced Kite Provider

#### `EnhancedKiteDataProvider`

Advanced Kite Connect integration with rate limiting and caching.

```python
class EnhancedKiteDataProvider:
    def __init__(self, api_key: str, access_token: str)
    def get_atm_strike(self, index_name: str, expiry: str = None) -> float
    def collect_options_data(self, index_name: str, expiry: str, strikes: List[int]) -> Dict
    def get_health_metrics() -> Dict[str, Any]
```

**Features:**
- Advanced rate limiting (200+ req/min)
- Intelligent caching with TTL
- Connection pooling
- Request prioritization

**Example Usage:**
```python
provider = EnhancedKiteDataProvider('api_key', 'access_token')

# Get ATM strike
atm_strike = provider.get_atm_strike('NIFTY')
print(f"NIFTY ATM Strike: {atm_strike}")

# Collect options data
strikes = [24900, 24950, 25000, 25050, 25100]
options_data = provider.collect_options_data('NIFTY', '2024-12-26', strikes)
```

### Data Structures

#### `MarketDataPoint`

```python
@dataclass
class MarketDataPoint:
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    change: float
    change_percent: float
    source: DataSourceType
    metadata: Dict[str, Any] = None
```

#### `OptionsDataPoint`

```python
@dataclass
class OptionsDataPoint:
    symbol: str
    strike: float
    expiry: datetime
    option_type: str  # CE/PE
    last_price: float
    volume: int
    oi: int  # Open Interest
    change: float
    change_percent: float
    iv: Optional[float] = None  # Implied Volatility
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    source: DataSourceType = DataSourceType.KITE_CONNECT
    metadata: Dict[str, Any] = None
```

---

## Analytics APIs

### Overview Generator

#### `OverviewGenerator`

Generates comprehensive market overview and summary reports.

```python
class OverviewGenerator:
    def __init__(self, config: Dict[str, Any])
    def generate_market_overview(self, data_sources: Dict[str, Any]) -> MarketOverview
    def export_overview(self, overview: MarketOverview, format_type: str = 'json') -> str
```

**Methods:**

##### `generate_market_overview(data_sources)`

Generates comprehensive market overview from data sources.

**Parameters:**
- `data_sources`: Dictionary containing market and options data

**Returns:**
- `MarketOverview`: Complete market analysis object

**Example Usage:**
```python
generator = OverviewGenerator(config)

data_sources = {
    'market_data': {...},
    'options_data': {...}
}

overview = generator.generate_market_overview(data_sources)
print(f"Market Sentiment: {overview.market_sentiment}")
print(f"Overall PCR: {overview.overall_pcr}")
```

### Volatility Analyzer

#### `VolatilityAnalyzer`

Advanced volatility analysis and surface modeling.

```python
class VolatilityAnalyzer:
    def __init__(self, config: Dict[str, Any])
    def analyze_volatility(self, market_data: Dict[str, Any], options_data: List[Dict]) -> VolatilityMetrics
    def forecast_volatility(self, historical_data: List[float], forecast_days: int = 30) -> Dict[str, float]
    def calculate_risk_neutral_density(self, iv_surface: VolatilitySurface, expiry_days: int = 30) -> Dict[str, Any]
```

**Methods:**

##### `analyze_volatility(market_data, options_data)`

Performs comprehensive volatility analysis.

**Parameters:**
- `market_data`: Current market data for underlying
- `options_data`: List of options data points

**Returns:**
- `VolatilityMetrics`: Complete volatility analysis

**Example Usage:**
```python
analyzer = VolatilityAnalyzer(config)

vol_metrics = analyzer.analyze_volatility(market_data, options_data)
print(f"30-day Realized Vol: {vol_metrics.realized_vol_30d:.3f}")
print(f"IV Rank: {vol_metrics.iv_rank_30d:.1f}")
```

### Risk Analyzer

#### `RiskAnalyzer`

Comprehensive risk analysis and portfolio risk management.

```python
class RiskAnalyzer:
    def __init__(self, config: Dict[str, Any])
    def analyze_portfolio_risk(self, portfolio: Portfolio, market_data: Dict[str, Any]) -> RiskMetrics
    def run_scenario_analysis(self, portfolio: Portfolio, market_data: Dict[str, Any]) -> Dict[str, ScenarioResult]
    def stress_test_portfolio(self, portfolio: Portfolio, market_data: Dict[str, Any]) -> Dict[str, Any]
    def check_risk_limits(self, risk_metrics: RiskMetrics) -> Dict[str, Any]
```

**Methods:**

##### `analyze_portfolio_risk(portfolio, market_data)`

Performs comprehensive portfolio risk analysis.

**Parameters:**
- `portfolio`: Portfolio object with positions
- `market_data`: Current market data

**Returns:**
- `RiskMetrics`: Complete risk analysis

**Example Usage:**
```python
analyzer = RiskAnalyzer(config)

risk_metrics = analyzer.analyze_portfolio_risk(portfolio, market_data)
print(f"Portfolio VaR (95%): ${risk_metrics.var_95 * risk_metrics.portfolio_value:,.2f}")
print(f"Sharpe Ratio: {risk_metrics.sharpe_ratio:.2f}")
```

---

## Storage APIs

### Data Archiver

#### `DataArchiver`

Automated data archival, backup, and retention management.

```python
class DataArchiver:
    def __init__(self, config: Dict[str, Any])
    def create_archive_job(self, policy_name: str, force_full_backup: bool = False) -> str
    def run_archive_job(self, job_id: str) -> bool
    def restore_from_archive(self, backup_id: str, restore_path: Path) -> bool
    def cleanup_old_archives() -> Dict[str, Any]
```

**Methods:**

##### `create_archive_job(policy_name, force_full_backup)`

Creates a new archive job based on policy.

**Parameters:**
- `policy_name`: Name of the archival policy
- `force_full_backup`: Force full backup instead of incremental

**Returns:**
- `str`: Job ID for tracking

**Example Usage:**
```python
archiver = DataArchiver(config)

# Create archive job
job_id = archiver.create_archive_job('daily_csv')

# Run archive job
success = archiver.run_archive_job(job_id)
print(f"Archive job {'completed' if success else 'failed'}")
```

---

## Monitoring APIs

### Performance Monitor

#### `PerformanceMonitor`

Comprehensive performance monitoring and profiling.

```python
class PerformanceMonitor:
    def __init__(self, config: Dict[str, Any] = None)
    def start_monitoring(self, interval: int = 5)
    def stop_monitoring()
    def add_metric(self, name: str, value: float, unit: str, category: str, tags: Dict[str, str] = None)
    def get_performance_summary(self, minutes: int = 30) -> Dict[str, Any]
    def get_bottlenecks(self, top_n: int = 10) -> List[Dict[str, Any]]
```

**Decorators:**

##### `@monitor.profile_function(func_name)`

Decorator for profiling function performance.

**Example Usage:**
```python
monitor = PerformanceMonitor()
monitor.start_monitoring()

@monitor.profile_function("data_collection")
def collect_data():
    # Your data collection code
    pass

# Get performance summary
summary = monitor.get_performance_summary(minutes=30)
print(f"Function calls: {summary['function_profiles']}")
```

### Metrics Dashboard

#### `MetricsDashboard`

Real-time metrics visualization and monitoring dashboard.

```python
class MetricsDashboard:
    def __init__(self, config: Optional[DashboardConfig] = None)
    def start_dashboard()
    def add_custom_metric(self, name: str, value: float, description: str = "", unit: str = "")
    def export_metrics(self, format_type: str = 'json') -> str
```

**Example Usage:**
```python
dashboard = MetricsDashboard()

# Add custom metrics
dashboard.add_custom_metric("custom_counter", 100, "Custom Counter", "count")

# Start dashboard (blocking call)
dashboard.start_dashboard()
```

---

## Configuration APIs

### Configuration Manager

#### `load_config(config_path)`

Loads configuration from JSON file with environment variable overrides.

**Parameters:**
- `config_path`: Path to configuration file

**Returns:**
- `Dict[str, Any]`: Loaded configuration

**Example Usage:**
```python
config = load_config('config.json')
print(f"Platform version: {config['platform']['version']}")
```

#### `validate_config(config)`

Validates configuration against schema and business rules.

**Parameters:**
- `config`: Configuration dictionary to validate

**Returns:**
- `List[str]`: List of validation errors (empty if valid)

**Example Usage:**
```python
errors = validate_config(config)
if errors:
    print(f"Configuration errors: {errors}")
else:
    print("Configuration is valid")
```

---

## Error Handling

### Exception Classes

#### `CollectionError`

Raised when data collection fails.

```python
class CollectionError(Exception):
    """Raised when data collection operations fail."""
    pass
```

#### `ValidationError`

Raised when data validation fails.

```python
class ValidationError(Exception):
    """Raised when data validation fails."""
    pass
```

#### `ConfigurationError`

Raised when configuration is invalid.

```python
class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass
```

### Error Response Format

All API methods that can fail return errors in a consistent format:

```python
{
    "success": False,
    "error": {
        "type": "CollectionError",
        "message": "Failed to collect market data",
        "details": {
            "symbol": "NIFTY",
            "timestamp": "2024-12-26T15:30:00Z",
            "retry_after": 60
        }
    }
}
```

---

## Authentication

### Kite Connect Authentication

The platform uses Kite Connect API for market data. Authentication requires:

1. **API Key**: Your Kite Connect app's API key
2. **Access Token**: Valid access token (obtained through login flow)

**Setup:**
```python
# Environment variables
export KITE_API_KEY="your_api_key"
export KITE_ACCESS_TOKEN="your_access_token"

# Or in configuration
{
  "data_sources": {
    "kite_connect": {
      "api_key": "your_api_key",
      "access_token": "your_access_token"
    }
  }
}
```

### Rate Limiting

The platform implements sophisticated rate limiting:

- **Base Rate**: 200 requests per minute
- **Burst Capacity**: 50 requests
- **Exponential Backoff**: Automatic retry with increasing delays
- **Priority Queues**: CRITICAL → HIGH → NORMAL → LOW

---

## Response Formats

### Success Response

```python
{
    "success": True,
    "data": {
        # Response data
    },
    "metadata": {
        "timestamp": "2024-12-26T15:30:00Z",
        "request_id": "req_123456",
        "processing_time_ms": 150
    }
}
```

### Error Response

```python
{
    "success": False,
    "error": {
        "type": "ErrorType",
        "message": "Human readable error message",
        "code": "ERROR_CODE",
        "details": {
            # Additional error details
        }
    },
    "metadata": {
        "timestamp": "2024-12-26T15:30:00Z",
        "request_id": "req_123456"
    }
}
```

---

## SDK Usage Examples

### Complete Data Collection Example

```python
from collections import MarketDataCollector
from analytics import OverviewGenerator, VolatilityAnalyzer
from risk import RiskAnalyzer

# Initialize components
config = load_config('config.json')
collector = MarketDataCollector(config)
overview_gen = OverviewGenerator(config)
vol_analyzer = VolatilityAnalyzer(config)
risk_analyzer = RiskAnalyzer(config)

# Connect to data sources
collector.connect_all_sources()

# Collect market data
market_data = {}
indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']

for index in indices:
    market_data[index] = collector.get_market_data(index)

# Collect options data
options_data = {}
for index in indices:
    options_data[index] = collector.get_options_chain(index, '2024-12-26')

# Generate analytics
data_sources = {
    'market_data': market_data,
    'options_data': options_data
}

# Market overview
overview = overview_gen.generate_market_overview(data_sources)
print(f"Market Sentiment: {overview.market_sentiment}")

# Volatility analysis
for index in indices:
    vol_metrics = vol_analyzer.analyze_volatility(
        market_data[index].__dict__, 
        options_data[index]
    )
    print(f"{index} IV Rank: {vol_metrics.iv_rank_30d:.1f}")

# Export results
overview_json = overview_gen.export_overview(overview, 'json')
with open('market_overview.json', 'w') as f:
    f.write(overview_json)
```

### Portfolio Risk Analysis Example

```python
from risk import RiskAnalyzer, Portfolio, Position

# Create portfolio
positions = [
    Position(
        symbol='NIFTY25000CE',
        quantity=100,
        entry_price=150,
        current_price=156.75,
        position_value=15675,
        unrealized_pnl=675,
        position_type='option',
        delta=0.6,
        gamma=0.001,
        theta=-0.5,
        vega=0.12
    )
]

portfolio = Portfolio(
    positions=positions,
    cash=50000,
    total_value=65675
)

# Analyze risk
risk_analyzer = RiskAnalyzer(config)
risk_metrics = risk_analyzer.analyze_portfolio_risk(portfolio, market_data)

# Run scenarios
scenarios = risk_analyzer.run_scenario_analysis(portfolio, market_data)

# Check risk limits
limit_checks = risk_analyzer.check_risk_limits(risk_metrics)

# Generate report
report = risk_analyzer.generate_risk_report(risk_metrics, scenarios)
print(report)
```

---

## API Versioning

The G6.1 Platform API follows semantic versioning:

- **Major Version**: Breaking changes (2.x.x)
- **Minor Version**: New features, backward compatible (2.1.x)
- **Patch Version**: Bug fixes (2.1.1)

Current Version: **2.0.0**

---

## Support and Documentation

- **GitHub Repository**: [G6.1 Platform](https://github.com/ayushrajani07/G6)
- **Documentation**: See README.md for comprehensive documentation
- **Issues**: Report bugs and feature requests via GitHub Issues
- **License**: MIT License

For additional support, refer to the troubleshooting guide and configuration documentation.