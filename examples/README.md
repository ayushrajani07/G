# G6 Analytics Platform - Examples

This directory contains usage examples and integration guides for the G6 Analytics Platform.

## 📁 Available Examples

### 1. `basic_usage.py`
**Basic Platform Usage**

Demonstrates the fundamental usage of the G6 Platform for options data collection:
- Configuration initialization
- Platform startup
- Basic data collection

```bash
python examples/basic_usage.py
```

### 2. `analytics_example.py`
**Advanced Analytics Features**

Shows how to use the analytics engines for:
- Implied Volatility (IV) calculations
- Greeks calculations (Delta, Gamma, Theta, Vega, Rho)
- Risk analysis and management
- Volatility surface analysis

```bash
python examples/analytics_example.py
```

### 3. `production_integration.py`
**Production Integration Example**

Demonstrates enterprise-grade integration with:
- Graceful shutdown handling
- Health monitoring
- Metrics collection
- Error recovery
- Signal handling

```bash
python examples/production_integration.py
```

## 🚀 Quick Start

1. **Ensure dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API credentials:**
   Create a `.env` file with your Kite Connect credentials:
   ```
   KITE_API_KEY=your_api_key
   KITE_API_SECRET=your_api_secret
   KITE_ACCESS_TOKEN=your_access_token
   ```

3. **Run basic validation:**
   ```bash
   python first_run_diagnostics.py
   ```

4. **Run any example:**
   ```bash
   python examples/basic_usage.py
   ```

## 📊 Example Output

The examples will:
- ✅ Initialize platform components
- 📊 Start data collection
- 📈 Display real-time analytics
- 📋 Generate logs and metrics
- 💾 Save data to CSV/InfluxDB

## 🔧 Customization

Each example can be customized by:
- Modifying configuration in `config.json`
- Adjusting analytics parameters
- Changing data collection intervals
- Adding custom monitoring logic

## 💡 Best Practices

1. **Error Handling:** All examples include comprehensive error handling
2. **Graceful Shutdown:** Use Ctrl+C for clean shutdown
3. **Monitoring:** Check logs/ directory for system status
4. **Data:** Output files are saved in data/ directory

## 🆘 Troubleshooting

If examples fail to run:
1. Check API credentials in `.env` file
2. Verify dependencies: `pip install -r requirements.txt`
3. Run diagnostics: `python first_run_diagnostics.py`
4. Check logs in `logs/` directory

For detailed troubleshooting, see `docs/TROUBLESHOOTING.md`.