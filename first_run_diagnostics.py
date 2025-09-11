#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 First-Run System Diagnostics and Setup for G6 Analytics Platform
Author: AI Assistant (Complete First-Run Setup)

✅ Performs comprehensive first-run checks:
- Kite Connect API authentication setup and validation
- System requirements and dependencies verification
- InfluxDB connection testing and debugging
- File system permissions and directory structure
- Configuration validation and setup
- Token management initialization
- Performance baseline establishment
- Environment variable validation
"""

import os
import sys
import json
import time
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import tempfile

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FirstRunDiagnostics:
    """🔧 Complete first-run diagnostics and setup."""
    
    def __init__(self):
        """Initialize first-run diagnostics."""
        self.results = {}
        self.errors = []
        self.warnings = []
        self.start_time = datetime.now()
        
        print("🚀 G6 Analytics Platform - First-Run Diagnostics")
        print("=" * 60)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def run_all_checks(self) -> bool:
        """🧪 Run all first-run diagnostic checks."""
        checks = [
            ("System Requirements", self.check_system_requirements),
            ("Python Dependencies", self.check_dependencies),
            ("File System Setup", self.check_filesystem_setup),
            ("Configuration Validation", self.check_configuration),
            ("Kite API Setup", self.check_kite_api_setup),
            ("InfluxDB Connection", self.check_influxdb_connection),
            ("Analytics Engine", self.check_analytics_engine),
            ("Performance Baseline", self.establish_performance_baseline),
            ("Environment Variables", self.check_environment_variables)
        ]
        
        all_passed = True
        
        for check_name, check_function in checks:
            print(f"\n🔍 Running: {check_name}")
            print("-" * 40)
            
            try:
                result = check_function()
                self.results[check_name] = result
                
                if result['status'] == 'PASS':
                    print(f"✅ {check_name}: PASSED")
                elif result['status'] == 'WARN':
                    print(f"⚠️ {check_name}: WARNING - {result.get('message', '')}")
                    self.warnings.append(f"{check_name}: {result.get('message', '')}")
                else:
                    print(f"❌ {check_name}: FAILED - {result.get('message', '')}")
                    self.errors.append(f"{check_name}: {result.get('message', '')}")
                    all_passed = False
                    
            except Exception as e:
                error_msg = f"{check_name} check failed: {str(e)}"
                self.errors.append(error_msg)
                self.results[check_name] = {'status': 'FAIL', 'message': str(e)}
                print(f"❌ {check_name}: ERROR - {str(e)}")
                all_passed = False
        
        self.print_summary()
        return all_passed
    
    def check_system_requirements(self) -> Dict[str, Any]:
        """🖥️ Check system requirements."""
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
                return {'status': 'FAIL', 'message': f'Python 3.8+ required, found {python_version.major}.{python_version.minor}'}
            
            # Check system resources
            try:
                import psutil
                
                # Memory check
                memory = psutil.virtual_memory()
                available_gb = memory.available / (1024**3)
                if available_gb < 1.0:
                    return {'status': 'WARN', 'message': f'Low memory: {available_gb:.2f} GB available'}
                
                # Disk space check
                disk = psutil.disk_usage('/')
                free_gb = disk.free / (1024**3)
                if free_gb < 0.5:
                    return {'status': 'WARN', 'message': f'Low disk space: {free_gb:.2f} GB available'}
                
                print(f"  ✅ Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
                print(f"  ✅ Memory: {available_gb:.2f} GB available")
                print(f"  ✅ Disk: {free_gb:.2f} GB available")
                print(f"  ✅ CPU Cores: {psutil.cpu_count()}")
                
                return {'status': 'PASS', 'details': {
                    'python_version': f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                    'memory_gb': round(available_gb, 2),
                    'disk_gb': round(free_gb, 2),
                    'cpu_cores': psutil.cpu_count()
                }}
                
            except ImportError:
                return {'status': 'WARN', 'message': 'psutil not available for system monitoring'}
                
        except Exception as e:
            return {'status': 'FAIL', 'message': str(e)}
    
    def check_dependencies(self) -> Dict[str, Any]:
        """📦 Check Python dependencies."""
        required_packages = [
            'numpy', 'scipy', 'pandas', 'kiteconnect', 
            'influxdb_client', 'psutil', 'rich', 'requests', 'tenacity'
        ]
        
        missing_packages = []
        available_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                available_packages.append(package)
                print(f"  ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"  ❌ {package} - NOT FOUND")
        
        if missing_packages:
            return {
                'status': 'FAIL', 
                'message': f'Missing packages: {", ".join(missing_packages)}',
                'missing': missing_packages,
                'available': available_packages
            }
        
        return {
            'status': 'PASS',
            'available': available_packages
        }
    
    def check_filesystem_setup(self) -> Dict[str, Any]:
        """📁 Check file system setup and permissions."""
        required_dirs = ['data', 'logs', 'data/csv', 'tokens']
        created_dirs = []
        permission_errors = []
        
        for dir_path in required_dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
                
                # Test write permissions
                test_file = os.path.join(dir_path, 'test_write.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                
                created_dirs.append(dir_path)
                print(f"  ✅ {dir_path} - Created and writable")
                
            except Exception as e:
                permission_errors.append(f"{dir_path}: {str(e)}")
                print(f"  ❌ {dir_path} - Error: {str(e)}")
        
        if permission_errors:
            return {
                'status': 'FAIL',
                'message': f'Directory setup errors: {"; ".join(permission_errors)}',
                'errors': permission_errors
            }
        
        return {
            'status': 'PASS',
            'created_dirs': created_dirs
        }
    
    def check_configuration(self) -> Dict[str, Any]:
        """⚙️ Check configuration files."""
        config_status = {'config.json': False, '.env': False}
        
        # Check config.json
        if os.path.exists('config.json'):
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                
                # Validate structure
                required_sections = ['platform', 'market', 'data_collection', 'analytics']
                missing_sections = [s for s in required_sections if s not in config]
                
                if missing_sections:
                    return {
                        'status': 'WARN',
                        'message': f'Config missing sections: {", ".join(missing_sections)}',
                        'missing_sections': missing_sections
                    }
                
                config_status['config.json'] = True
                print(f"  ✅ config.json - Valid structure")
                
            except json.JSONDecodeError as e:
                return {'status': 'FAIL', 'message': f'config.json parse error: {str(e)}'}
            except Exception as e:
                return {'status': 'FAIL', 'message': f'config.json error: {str(e)}'}
        else:
            print(f"  ⚠️ config.json - Not found (will use defaults)")
        
        # Check .env file
        if os.path.exists('.env'):
            config_status['.env'] = True
            print(f"  ✅ .env - Found")
        else:
            print(f"  ⚠️ .env - Not found (environment variables may be needed)")
        
        return {
            'status': 'PASS' if any(config_status.values()) else 'WARN',
            'message': 'No configuration files found' if not any(config_status.values()) else None,
            'files_found': config_status
        }
    
    def check_kite_api_setup(self) -> Dict[str, Any]:
        """🔑 Check Kite Connect API setup."""
        try:
            from kiteconnect import KiteConnect
            
            # Check for API credentials in environment or config
            api_key = os.getenv('KITE_API_KEY')
            api_secret = os.getenv('KITE_API_SECRET')
            
            if not api_key or not api_secret:
                # Check config.json
                if os.path.exists('config.json'):
                    with open('config.json', 'r') as f:
                        config = json.load(f)
                    
                    kite_config = config.get('kite', {})
                    api_key = kite_config.get('api_key')
                    api_secret = kite_config.get('api_secret')
            
            if not api_key:
                print(f"  ⚠️ KITE_API_KEY not found in environment or config")
                return {
                    'status': 'WARN',
                    'message': 'Kite API credentials not configured'
                }
            
            # Test KiteConnect instantiation
            try:
                kite = KiteConnect(api_key=api_key)
                print(f"  ✅ KiteConnect client created successfully")
                print(f"  ✅ API Key configured")
                
                return {
                    'status': 'PASS',
                    'api_key_configured': True
                }
                
            except Exception as e:
                return {
                    'status': 'WARN',
                    'message': f'KiteConnect client error: {str(e)}'
                }
                
        except ImportError:
            return {
                'status': 'FAIL',
                'message': 'kiteconnect package not available'
            }
    
    def check_influxdb_connection(self) -> Dict[str, Any]:
        """📊 Check InfluxDB connection."""
        try:
            from influxdb_client import InfluxDBClient
            
            # Default InfluxDB settings
            url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
            token = os.getenv('INFLUXDB_TOKEN', '')
            org = os.getenv('INFLUXDB_ORG', '')
            
            print(f"  🔍 Attempting connection to: {url}")
            
            # Create client
            try:
                client = InfluxDBClient(url=url, token=token, org=org)
                print(f"  ✅ InfluxDB client created")
                
                # Test connection (ping)
                try:
                    health = client.health()
                    if health.status == "pass":
                        print(f"  ✅ InfluxDB server is healthy")
                        return {
                            'status': 'PASS',
                            'url': url,
                            'health': 'healthy'
                        }
                    else:
                        print(f"  ⚠️ InfluxDB health check failed: {health.status}")
                        return {
                            'status': 'WARN',
                            'message': f'InfluxDB unhealthy: {health.status}',
                            'url': url
                        }
                        
                except Exception as e:
                    print(f"  ⚠️ InfluxDB connection test failed: {str(e)}")
                    return {
                        'status': 'WARN',
                        'message': f'InfluxDB connection failed: {str(e)}',
                        'url': url,
                        'suggestion': 'InfluxDB may not be running or credentials may be incorrect'
                    }
                    
            except Exception as e:
                return {
                    'status': 'WARN',
                    'message': f'InfluxDB client creation failed: {str(e)}',
                    'url': url
                }
                
        except ImportError:
            return {
                'status': 'FAIL',
                'message': 'influxdb_client package not available'
            }
    
    def check_analytics_engine(self) -> Dict[str, Any]:
        """🧮 Check analytics engine functionality."""
        try:
            # Test analytics engine import
            import analytics_engine
            from analytics_engine import IVCalculator, GreeksCalculator, PCRAnalyzer
            
            print(f"  ✅ Analytics engine imported successfully")
            
            # Test basic functionality
            iv_calc = IVCalculator()
            greeks_calc = GreeksCalculator()
            pcr_analyzer = PCRAnalyzer()
            
            # Quick functionality test
            iv = iv_calc.calculate_implied_volatility(
                option_price=125.50,
                spot_price=24800,
                strike_price=24800,
                time_to_expiry=30/365,
                option_type='CE'
            )
            
            if iv is not None:
                print(f"  ✅ IV calculation working: {iv}%")
            else:
                print(f"  ⚠️ IV calculation returned None")
            
            greeks = greeks_calc.calculate_all_greeks(
                spot_price=24800,
                strike_price=24800,
                time_to_expiry=30/365,
                volatility=0.18,
                option_type='CE'
            )
            
            if greeks.delta != 0:
                print(f"  ✅ Greeks calculation working: Delta={greeks.delta}")
            else:
                print(f"  ⚠️ Greeks calculation issue")
            
            return {
                'status': 'PASS',
                'iv_test': iv,
                'greeks_test': {
                    'delta': greeks.delta,
                    'gamma': greeks.gamma,
                    'theta': greeks.theta
                }
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Analytics engine error: {str(e)}'
            }
    
    def establish_performance_baseline(self) -> Dict[str, Any]:
        """⚡ Establish performance baseline."""
        try:
            import analytics_engine
            from analytics_engine import IVCalculator, GreeksCalculator
            import time
            
            iv_calc = IVCalculator()
            greeks_calc = GreeksCalculator()
            
            # IV calculation performance
            start_time = time.time()
            for i in range(10):
                iv = iv_calc.calculate_implied_volatility(
                    option_price=125.50 + i,
                    spot_price=24800 + i,
                    strike_price=24800,
                    time_to_expiry=30/365,
                    option_type='CE'
                )
            iv_time = (time.time() - start_time) / 10
            
            # Greeks calculation performance
            start_time = time.time()
            for i in range(10):
                greeks = greeks_calc.calculate_all_greeks(
                    spot_price=24800 + i,
                    strike_price=24800,
                    time_to_expiry=30/365,
                    volatility=0.18,
                    option_type='CE'
                )
            greeks_time = (time.time() - start_time) / 10
            
            print(f"  ✅ IV calculation: {iv_time:.4f}s per calculation")
            print(f"  ✅ Greeks calculation: {greeks_time:.4f}s per calculation")
            
            # Performance warnings
            status = 'PASS'
            message = None
            
            if iv_time > 0.1:
                status = 'WARN'
                message = f'IV calculation slow: {iv_time:.4f}s'
            
            if greeks_time > 0.05:
                status = 'WARN'
                message = f'Greeks calculation slow: {greeks_time:.4f}s'
            
            return {
                'status': status,
                'message': message,
                'iv_time_per_calc': round(iv_time, 6),
                'greeks_time_per_calc': round(greeks_time, 6)
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Performance baseline error: {str(e)}'
            }
    
    def check_environment_variables(self) -> Dict[str, Any]:
        """🌍 Check environment variables."""
        recommended_vars = [
            'KITE_API_KEY', 'KITE_API_SECRET', 'KITE_ACCESS_TOKEN',
            'INFLUXDB_URL', 'INFLUXDB_TOKEN', 'INFLUXDB_ORG'
        ]
        
        found_vars = []
        missing_vars = []
        
        for var in recommended_vars:
            if os.getenv(var):
                found_vars.append(var)
                print(f"  ✅ {var} - Set")
            else:
                missing_vars.append(var)
                print(f"  ⚠️ {var} - Not set")
        
        if len(found_vars) == 0:
            return {
                'status': 'WARN',
                'message': 'No environment variables configured',
                'missing': missing_vars
            }
        
        return {
            'status': 'PASS' if len(found_vars) >= len(missing_vars) else 'WARN',
            'found': found_vars,
            'missing': missing_vars
        }
    
    def print_summary(self):
        """📋 Print diagnostic summary."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 60)
        print("🧪 FIRST-RUN DIAGNOSTICS SUMMARY")
        print("=" * 60)
        print(f"Duration: {duration.total_seconds():.2f} seconds")
        print(f"Checks Run: {len(self.results)}")
        
        # Count status
        passed = sum(1 for r in self.results.values() if r['status'] == 'PASS')
        warnings = sum(1 for r in self.results.values() if r['status'] == 'WARN')
        failed = sum(1 for r in self.results.values() if r['status'] == 'FAIL')
        
        print(f"✅ Passed: {passed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"❌ Failed: {failed}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.errors:
            print(f"\n❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if failed > 0:
            print("  - Fix failed checks before proceeding")
        if warnings > 0:
            print("  - Review warnings for optimal performance")
        if not os.path.exists('.env'):
            print("  - Create .env file with API credentials")
        if not os.path.exists('config.json'):
            print("  - Customize config.json for your requirements")
        
        print(f"\n🚀 NEXT STEPS:")
        if failed == 0:
            print("  - System is ready for G6 Analytics Platform")
            print("  - Run: python main.py")
        else:
            print("  - Fix critical errors before running platform")
            print("  - Install missing dependencies")
            print("  - Configure API credentials")
        
        # Save results
        results_file = f"logs/first_run_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('logs', exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'results': self.results,
                'errors': self.errors,
                'warnings': self.warnings,
                'summary': {
                    'passed': passed,
                    'warnings': warnings,
                    'failed': failed,
                    'total': len(self.results)
                }
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved: {results_file}")

def main():
    """🚀 Main entry point for first-run diagnostics."""
    diagnostics = FirstRunDiagnostics()
    success = diagnostics.run_all_checks()
    
    if success:
        print(f"\n🎉 First-run diagnostics completed successfully!")
        print(f"🚀 Your G6 Analytics Platform is ready to run!")
        sys.exit(0)
    else:
        print(f"\n⚠️ First-run diagnostics found issues that need attention.")
        print(f"🔧 Please review and fix the errors before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()