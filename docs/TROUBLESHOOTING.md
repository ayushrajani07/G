# G6.1 Platform Troubleshooting Guide

## Overview

This comprehensive troubleshooting guide helps you diagnose and resolve common issues with the G6.1 Options Analytics Platform. Issues are organized by category with step-by-step solutions.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [Configuration Issues](#configuration-issues)
4. [API Connection Issues](#api-connection-issues)
5. [Data Collection Issues](#data-collection-issues)
6. [Performance Issues](#performance-issues)
7. [UI and Display Issues](#ui-and-display-issues)
8. [Storage Issues](#storage-issues)
9. [Memory and Resource Issues](#memory-and-resource-issues)
10. [Advanced Troubleshooting](#advanced-troubleshooting)

---

## Quick Diagnostics

### System Health Check

Run the built-in diagnostic tool first:

```bash
python utils/quick_platform_diagnostic.py
```

**Expected Output:**
```
✅ Python version: 3.8+
✅ Required packages installed
✅ Configuration file valid
✅ API credentials present
✅ Data directories accessible
✅ System resources sufficient
```

### Common Quick Fixes

Before diving into detailed troubleshooting, try these quick fixes:

1. **Restart the platform**:
   ```bash
   # Stop any running instances
   pkill -f "python.*launcher"
   
   # Start fresh
   python fixed_enhanced_launcher.py
   ```

2. **Check environment variables**:
   ```bash
   echo $KITE_API_KEY
   echo $KITE_ACCESS_TOKEN
   ```

3. **Verify file permissions**:
   ```bash
   ls -la config.json
   ls -la .env
   chmod 644 config.json
   chmod 600 .env
   ```

4. **Clear cache**:
   ```bash
   rm -rf data/cache/*
   rm -rf __pycache__/
   ```

---

## Installation Issues

### Issue 1: Python Version Compatibility

**Symptoms:**
- `SyntaxError` on startup
- `ModuleNotFoundError` for typing features
- Unexpected behavior with f-strings

**Cause:** Python version < 3.8

**Solution:**
```bash
# Check Python version
python --version

# If < 3.8, install Python 3.8+
# Ubuntu/Debian:
sudo apt update
sudo apt install python3.8 python3.8-pip

# Windows: Download from python.org
# macOS: Use Homebrew
brew install python@3.8
```

### Issue 2: Missing Dependencies

**Symptoms:**
```
ModuleNotFoundError: No module named 'rich'
ModuleNotFoundError: No module named 'kiteconnect'
```

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install individually
pip install rich kiteconnect python-dotenv influxdb-client psutil numpy pandas scipy

# For development
pip install pytest unittest2 mock
```

### Issue 3: Package Conflicts

**Symptoms:**
- Import errors despite packages being installed
- Version mismatch warnings
- Unexpected behavior

**Solution:**
```bash
# Create clean virtual environment
python -m venv g6_env
source g6_env/bin/activate  # Linux/Mac
# or
g6_env\Scripts\activate     # Windows

# Install fresh dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Issue 4: Unicode/Encoding Issues on Windows

**Symptoms:**
- Garbled text output
- `UnicodeDecodeError`
- Missing emoji/symbols

**Solution:**
1. **Use Windows Terminal** (not Command Prompt)
2. **Set environment variables**:
   ```cmd
   set PYTHONIOENCODING=utf-8
   set PYTHONUTF8=1
   ```
3. **Use the Unicode-free launcher**:
   ```bash
   python robust_launcher_unicode_free.py
   ```

---

## Configuration Issues

### Issue 1: Configuration File Not Found

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'config.json'
```

**Solution:**
```bash
# Create config file from template
cp config_template.json config.json

# Or download from repository
wget https://raw.githubusercontent.com/ayushrajani07/G6/main/config_template.json -O config.json
```

### Issue 2: Invalid JSON Format

**Symptoms:**
```
json.decoder.JSONDecodeError: Expecting ',' delimiter
```

**Solution:**
1. **Validate JSON online**: Copy config content to jsonlint.com
2. **Common JSON errors**:
   ```json
   // ❌ Incorrect (trailing comma)
   {
     "platform": {
       "name": "G6.1",
     }
   }
   
   // ✅ Correct
   {
     "platform": {
       "name": "G6.1"
     }
   }
   ```
3. **Use JSON validator**:
   ```bash
   python -c "import json; json.load(open('config.json'))"
   ```

### Issue 3: Environment Variables Not Loading

**Symptoms:**
- API credentials not found
- Configuration overrides not working
- Environment-specific settings ignored

**Solution:**
1. **Check .env file location**: Must be in project root
2. **Verify .env format**:
   ```bash
   # ✅ Correct format
   KITE_API_KEY=your_key_here
   KITE_ACCESS_TOKEN=your_token_here
   
   # ❌ Incorrect (spaces around =)
   KITE_API_KEY = your_key_here
   ```
3. **Load environment manually**:
   ```bash
   export $(cat .env | xargs)
   python fixed_enhanced_launcher.py
   ```

### Issue 4: Configuration Validation Errors

**Symptoms:**
```
Configuration validation failed:
- Missing required field: platform.name
- Invalid collection_interval: must be positive
```

**Solution:**
1. **Run validation manually**:
   ```bash
   python -c "from config.config_manager import validate_config, load_config; print(validate_config(load_config('config.json')))"
   ```
2. **Fix common validation errors**:
   ```json
   {
     "platform": {
       "name": "G6.1 Platform",  // Must not be empty
       "version": "2.0.0",       // Must be semantic version
       "mode": "live"            // Must be: live, paper, or simulation
     },
     "market": {
       "indices": ["NIFTY"],     // Must not be empty array
       "collection_interval": 30  // Must be positive integer
     }
   }
   ```

---

## API Connection Issues

### Issue 1: Invalid API Credentials

**Symptoms:**
```
❌ Failed to connect to kite_connect: Invalid API credentials
TokenException: Invalid `api_key` or `access_token`
```

**Solution:**
1. **Verify credentials in Kite Developer Console**:
   - Visit: https://developers.kite.trade/
   - Check API key and secret
   - Ensure access token is valid (regenerate if needed)

2. **Update credentials**:
   ```bash
   # In .env file
   KITE_API_KEY=your_correct_api_key
   KITE_ACCESS_TOKEN=your_correct_access_token
   ```

3. **Test credentials manually**:
   ```python
   from kiteconnect import KiteConnect
   
   kite = KiteConnect(api_key="your_api_key")
   kite.set_access_token("your_access_token")
   
   try:
       profile = kite.profile()
       print(f"Connected as: {profile['user_name']}")
   except Exception as e:
       print(f"Connection failed: {e}")
   ```

### Issue 2: Rate Limiting Errors

**Symptoms:**
```
❌ Rate limit exceeded
TooManyRequestsException: Rate limit exceeded
```

**Solution:**
1. **Reduce rate limits in config.json**:
   ```json
   {
     "data_collection": {
       "performance": {
         "rate_limiting": {
           "requests_per_minute": 150,  // Reduce from 200
           "burst_capacity": 30         // Reduce from 50
         }
       }
     }
   }
   ```

2. **Enable caching**:
   ```json
   {
     "data_collection": {
       "performance": {
         "caching": {
           "enabled": true,
           "ttl_seconds": 120  // Increase cache time
         }
       }
     }
   }
   ```

3. **Check for multiple instances**:
   ```bash
   # Kill other instances
   ps aux | grep python | grep launcher
   pkill -f "python.*launcher"
   ```

### Issue 3: Network Connectivity Issues

**Symptoms:**
```
requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
```

**Solution:**
1. **Check internet connection**:
   ```bash
   ping google.com
   curl -I https://api.kite.trade/
   ```

2. **Check proxy settings**:
   ```bash
   # If behind corporate proxy
   export https_proxy=http://proxy.company.com:8080
   export http_proxy=http://proxy.company.com:8080
   ```

3. **Configure firewall**:
   ```bash
   # Allow outbound HTTPS traffic
   sudo ufw allow out 443
   ```

### Issue 4: SSL/TLS Issues

**Symptoms:**
```
requests.exceptions.SSLError: HTTPSConnectionPool
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution:**
1. **Update certificates**:
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install ca-certificates
   
   # Windows: Update Windows, restart
   
   # macOS
   brew install ca-certificates
   ```

2. **Temporary SSL bypass** (development only):
   ```python
   import ssl
   ssl._create_default_https_context = ssl._create_unverified_context
   ```

---

## Data Collection Issues

### Issue 1: No Data Being Collected

**Symptoms:**
- Platform shows "0 options processed"
- No CSV files created
- Empty streaming output

**Troubleshooting Steps:**

1. **Check market hours**:
   ```python
   from datetime import datetime
   import pytz
   
   ist = pytz.timezone('Asia/Kolkata')
   now = datetime.now(ist)
   print(f"Current IST time: {now}")
   print(f"Market hours: 09:15 - 15:30")
   ```

2. **Verify API connectivity**:
   ```python
   # Test in Python console
   from collectors.enhanced_kite_provider import EnhancedKiteDataProvider
   
   provider = EnhancedKiteDataProvider("api_key", "access_token")
   data = provider.get_market_data("NIFTY")
   print(data)
   ```

3. **Check configuration**:
   ```json
   {
     "market": {
       "indices": ["NIFTY"],  // Ensure not empty
       "collection_interval": 30  // Reasonable interval
     }
   }
   ```

### Issue 2: Incomplete Options Data

**Symptoms:**
- Only partial options chain collected
- Missing strike prices
- Inconsistent data

**Solution:**
1. **Check strike configuration**:
   ```json
   {
     "data_collection": {
       "options": {
         "strike_configuration": {
           "symmetric_otm": {
             "enabled": true,
             "offsets": [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
           }
         }
       }
     }
   }
   ```

2. **Verify expiry dates**:
   ```bash
   # Check if using valid expiry dates
   python -c "
   from datetime import datetime, timedelta
   # Next Thursday (typical expiry)
   today = datetime.now()
   days_until_thursday = (3 - today.weekday()) % 7
   if days_until_thursday == 0:
       days_until_thursday = 7
   next_expiry = today + timedelta(days=days_until_thursday)
   print(f'Next expiry: {next_expiry.strftime(\"%Y-%m-%d\")}')"
   ```

### Issue 3: Data Quality Issues

**Symptoms:**
- Zero prices for options
- Negative volumes
- Missing implied volatility

**Solution:**
1. **Enable data validation**:
   ```json
   {
     "data_collection": {
       "validation": {
         "enabled": true,
         "reject_zero_prices": true,
         "reject_negative_values": true
       }
     }
   }
   ```

2. **Check data field configuration**:
   ```json
   {
     "data_fields": {
       "basic": ["tradingsymbol", "strike", "expiry", "option_type", "last_price"],
       "pricing": ["volume", "oi", "change", "pchange", "iv"]
     }
   }
   ```

---

## Performance Issues

### Issue 1: Slow Data Collection

**Symptoms:**
- Collection cycles taking > 2 minutes
- High response times
- Timeout errors

**Solution:**
1. **Optimize batch processing**:
   ```json
   {
     "data_collection": {
       "performance": {
         "batch_processing": {
           "enabled": true,
           "batch_size": 25,  // Increase if stable
           "batch_timeout": 5
         }
       }
     }
   }
   ```

2. **Enable connection pooling**:
   ```json
   {
     "data_collection": {
       "performance": {
         "connection_pooling": {
           "enabled": true,
           "max_concurrent_requests": 10
         }
       }
     }
   }
   ```

3. **Reduce data collection scope**:
   ```json
   {
     "market": {
       "indices": ["NIFTY"],  // Start with one index
     },
     "data_collection": {
       "options": {
         "strike_configuration": {
           "symmetric_otm": {
             "offsets": [-2, -1, 0, 1, 2]  // Fewer strikes
           }
         }
       }
     }
   }
   ```

### Issue 2: High Memory Usage

**Symptoms:**
- Memory usage constantly increasing
- System becoming slow
- Out of memory errors

**Solution:**
1. **Enable cache cleanup**:
   ```json
   {
     "data_collection": {
       "performance": {
         "caching": {
           "max_cache_size": 500,  // Reduce cache size
           "cache_cleanup_interval": 60  // More frequent cleanup
         }
       }
     }
   }
   ```

2. **Monitor memory usage**:
   ```bash
   # Check memory usage
   python -c "
   import psutil
   process = psutil.Process()
   print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
   print(f'Memory percent: {process.memory_percent():.1f}%')"
   ```

3. **Use performance monitor**:
   ```python
   from utils.performance_monitor import PerformanceMonitor
   
   monitor = PerformanceMonitor()
   monitor.start_monitoring()
   ```

### Issue 3: High CPU Usage

**Symptoms:**
- CPU usage > 80%
- System fan running constantly
- Slow response to user input

**Solution:**
1. **Increase collection interval**:
   ```json
   {
     "market": {
       "collection_interval": 60  // Increase from 30
     }
   }
   ```

2. **Reduce concurrent requests**:
   ```json
   {
     "data_collection": {
       "performance": {
         "connection_pooling": {
           "max_concurrent_requests": 5  // Reduce from 10
         }
       }
     }
   }
   ```

---

## UI and Display Issues

### Issue 1: Rich UI Not Displaying Properly

**Symptoms:**
- Garbled text output
- Missing colors/formatting
- Layout issues

**Solution:**
1. **Check terminal compatibility**:
   ```bash
   # Test Rich compatibility
   python -c "
   from rich.console import Console
   console = Console()
   console.print('[bold red]Testing Rich output[/bold red]')
   console.print('✅ Rich is working properly')"
   ```

2. **Use fallback launcher**:
   ```bash
   python robust_launcher_unicode_free.py
   ```

3. **Force color mode**:
   ```bash
   export FORCE_COLOR=1
   python fixed_enhanced_launcher.py
   ```

### Issue 2: Layout Problems

**Symptoms:**
- Overlapping text
- Incorrect column widths
- Misaligned tables

**Solution:**
1. **Adjust terminal width**:
   ```json
   {
     "ui": {
       "rich_terminal": {
         "width": 120  // Reduce from 140
       }
     }
   }
   ```

2. **Use smaller terminal window**
3. **Switch to basic mode**:
   ```bash
   export G6_UI_MODE=basic
   ```

### Issue 3: No Output Visible

**Symptoms:**
- Platform appears to start but no output
- Cursor just blinking
- No response to input

**Solution:**
1. **Check stdout buffering**:
   ```bash
   python -u fixed_enhanced_launcher.py
   ```

2. **Enable debug mode**:
   ```bash
   export G6_DEBUG_MODE=true
   python fixed_enhanced_launcher.py
   ```

3. **Use immediate output platform**:
   ```bash
   python -c "
   from launchers.fixed_enhanced_launcher import FixedEnhancedLauncher
   launcher = FixedEnhancedLauncher()
   platform_file = launcher.create_immediate_output_platform()
   print(f'Created: {platform_file}')
   "
   ```

---

## Storage Issues

### Issue 1: CSV Files Not Created

**Symptoms:**
- No files in data/csv directory
- Permission denied errors
- Disk space errors

**Solution:**
1. **Check directory permissions**:
   ```bash
   mkdir -p data/csv
   chmod 755 data/csv
   ls -la data/
   ```

2. **Check disk space**:
   ```bash
   df -h .
   ```

3. **Verify storage configuration**:
   ```json
   {
     "storage": {
       "csv": {
         "enabled": true,
         "base_path": "data/csv"
       }
     }
   }
   ```

### Issue 2: InfluxDB Connection Issues

**Symptoms:**
```
ConnectionError: Unable to connect to InfluxDB
```

**Solution:**
1. **Check InfluxDB service**:
   ```bash
   # Check if InfluxDB is running
   sudo systemctl status influxdb
   
   # Start if not running
   sudo systemctl start influxdb
   ```

2. **Verify connection settings**:
   ```json
   {
     "storage": {
       "influxdb": {
         "enabled": true,
         "url": "http://localhost:8086",
         "database": "g6_analytics"
       }
     }
   }
   ```

3. **Test connection manually**:
   ```python
   from influxdb import InfluxDBClient
   
   client = InfluxDBClient(host='localhost', port=8086)
   print(client.ping())
   ```

---

## Memory and Resource Issues

### Issue 1: Memory Leaks

**Symptoms:**
- Memory usage increasing over time
- System becoming slower
- Eventually crashes

**Diagnostic Steps:**
1. **Monitor memory over time**:
   ```bash
   # Run this in separate terminal
   while true; do
     ps aux | grep python | grep launcher | awk '{print $6}' | head -1
     sleep 60
   done
   ```

2. **Use memory profiler**:
   ```bash
   pip install memory-profiler
   python -m memory_profiler fixed_enhanced_launcher.py
   ```

**Solution:**
```python
# Enable memory monitoring
from utils.performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.start_monitoring(interval=60)

# Check for memory leaks
leak_analysis = monitor.memory_tracker.detect_memory_leaks()
print(leak_analysis)
```

### Issue 2: File Handle Exhaustion

**Symptoms:**
```
OSError: [Errno 24] Too many open files
```

**Solution:**
1. **Check file limits**:
   ```bash
   ulimit -n
   ```

2. **Increase file limits**:
   ```bash
   # Temporary
   ulimit -n 4096
   
   # Permanent (add to ~/.bashrc)
   echo "ulimit -n 4096" >> ~/.bashrc
   ```

3. **Fix file handle leaks in code**:
   ```python
   # Ensure files are properly closed
   with open('file.txt', 'r') as f:
       data = f.read()
   # File automatically closed
   ```

---

## Advanced Troubleshooting

### Debug Mode Activation

Enable comprehensive debugging:

```bash
export G6_DEBUG_MODE=true
export G6_LOG_LEVEL=DEBUG
export PYTHONVERBOSE=1
python fixed_enhanced_launcher.py 2>&1 | tee debug.log
```

### Performance Profiling

```python
import cProfile
import pstats

# Profile the platform
cProfile.run('main()', 'profile_stats')

# Analyze results
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Network Debugging

```bash
# Monitor network traffic
sudo tcpdump -i any -n host api.kite.trade

# Check DNS resolution
nslookup api.kite.trade

# Test HTTPS connectivity
openssl s_client -connect api.kite.trade:443
```

### System Resource Monitoring

```bash
# Monitor system resources
top -p $(pgrep -f "python.*launcher")

# I/O monitoring
iotop -p $(pgrep -f "python.*launcher")

# Network monitoring
nethogs
```

### Log Analysis

```bash
# Enable detailed logging
export G6_LOG_LEVEL=DEBUG

# Analyze logs
tail -f logs/platform.log | grep ERROR
grep -i "rate limit" logs/platform.log
grep -i "memory" logs/platform.log
```

### Database Debugging

```bash
# InfluxDB query debugging
influx -precision rfc3339 -database g6_analytics
> SHOW MEASUREMENTS
> SELECT * FROM options_data LIMIT 5

# CSV file analysis
head -20 data/csv/NIFTY_$(date +%Y-%m-%d)_options.csv
wc -l data/csv/*.csv
```

---

## Emergency Procedures

### Complete System Reset

If all else fails, perform a complete reset:

```bash
# 1. Stop all processes
pkill -f "python.*launcher"
pkill -f "python.*platform"

# 2. Clear all cache and temporary files
rm -rf data/cache/*
rm -rf __pycache__/
rm -rf *.pyc
find . -name "*.pyc" -delete

# 3. Reset configuration to defaults
cp config_template.json config.json

# 4. Reinstall dependencies
pip uninstall -y rich kiteconnect python-dotenv
pip install rich kiteconnect python-dotenv

# 5. Restart platform
python fixed_enhanced_launcher.py
```

### Recovery from Corrupted State

```bash
# 1. Backup current state
mkdir backup_$(date +%Y%m%d_%H%M%S)
cp -r data/ backup_*/
cp config.json backup_*/

# 2. Reset data directories
rm -rf data/csv/*
rm -rf data/cache/*
mkdir -p data/csv data/cache data/logs

# 3. Verify configuration
python -c "
import json
with open('config.json') as f:
    config = json.load(f)
print('Configuration loaded successfully')
"

# 4. Test minimal functionality
python -c "
from launchers.fixed_enhanced_launcher import FixedEnhancedLauncher
launcher = FixedEnhancedLauncher()
print('Launcher initialized successfully')
"
```

---

## Getting Help

### Information to Include in Bug Reports

When seeking help, include:

1. **System Information**:
   ```bash
   python --version
   pip list | grep -E "(rich|kiteconnect|dotenv)"
   uname -a  # Linux/Mac
   systeminfo  # Windows
   ```

2. **Configuration** (sanitized):
   ```bash
   # Remove sensitive data before sharing
   cat config.json | sed 's/"api_key": ".*"/"api_key": "REDACTED"/'
   ```

3. **Error Messages**:
   ```bash
   # Full error output
   python fixed_enhanced_launcher.py 2>&1 | tee error.log
   ```

4. **Debug Information**:
   ```bash
   export G6_DEBUG_MODE=true
   python fixed_enhanced_launcher.py > debug.log 2>&1
   ```

### Self-Help Resources

1. **Configuration Validator**:
   ```bash
   python -c "from config.config_manager import validate_config, load_config; print(validate_config(load_config('config.json')))"
   ```

2. **System Diagnostic**:
   ```bash
   python utils/quick_platform_diagnostic.py
   ```

3. **API Connectivity Test**:
   ```bash
   python -c "
   import os
   from kiteconnect import KiteConnect
   kite = KiteConnect(os.getenv('KITE_API_KEY'))
   kite.set_access_token(os.getenv('KITE_ACCESS_TOKEN'))
   print(kite.profile())
   "
   ```

### Contact and Support

- **GitHub Issues**: [G6.1 Platform Issues](https://github.com/ayushrajani07/G6/issues)
- **Documentation**: README.md and API Reference
- **Configuration Guide**: CONFIGURATION_GUIDE.md

When reporting issues:
- Use descriptive titles
- Include system information
- Provide reproducible steps
- Attach relevant logs (sanitized)
- Specify expected vs. actual behavior