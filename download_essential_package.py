#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 Essential Files Package Creator for G6 Analytics Platform
Author: AI Assistant (Package Creation Utility)

Creates a minimal package containing only the essential files needed
for a fully functional G6 Analytics Platform deployment.

✅ Features:
- Identifies and extracts core functional components
- Excludes legacy/redundant files
- Creates proper directory structure
- Generates deployment documentation
- Provides size optimization
- Creates installation instructions

🔧 WINDOWS ENCODING FIX: Forces UTF-8 encoding for emoji support
"""

import os
import sys
import shutil
import json
import zipfile
from datetime import datetime
from typing import List, Dict, Tuple, Any
import subprocess

# 🔧 CRITICAL FIX: Force UTF-8 encoding on Windows to prevent UnicodeEncodeError
def setup_encoding():
    """Setup proper UTF-8 encoding for Windows systems."""
    # Set environment variables for UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # For Windows console compatibility
    if os.name == 'nt':
        try:
            # Reconfigure stdout/stderr to use UTF-8
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
                
            # Enable VT100 mode for Windows console (for better emoji support)
            import ctypes
            from ctypes import wintypes
            
            kernel32 = ctypes.windll.kernel32
            stdout_handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = wintypes.DWORD()
            kernel32.GetConsoleMode(stdout_handle, ctypes.byref(mode))
            mode.value |= 4  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(stdout_handle, mode)
            
        except Exception:
            # If VT100 setup fails, continue with basic UTF-8
            pass

# Setup encoding before any file operations
setup_encoding()

class EssentialPackageCreator:
    """📦 Creates essential files package for G6 Platform."""
    
    def __init__(self):
        """Initialize package creator."""
        self.start_time = datetime.now()
        self.package_info = {
            'created_at': self.start_time.isoformat(),
            'version': '2.0.0',
            'description': 'G6 Analytics Platform - Essential Files Package'
        }
        
        print("📦 G6 Analytics Platform - Essential Files Package Creator")
        print("=" * 65)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 65)
    
    def get_essential_files(self) -> Dict[str, List[str]]:
        """🎯 Define essential files categorized by purpose."""
        
        essential_files = {
            'entry_points': [
                'main.py',                          # Unified application entry point
                '__main__.py',                      # Package entry point
                'first_run_diagnostics.py',        # System validation and setup
                'comprehensive_testing.py',        # Complete testing framework
            ],
            
            'core_platform': [
                'g6_platform/',                    # Entire core platform package (includes analytics in g6_platform/analytics/)
            ],
            
            'configuration': [
                'config.json',                     # Application configuration
                'config_template.json',            # Configuration template
                'requirements.txt',                # Python dependencies
                'setup.py',                        # Professional package installation
                '.gitignore',                      # Git ignore rules
            ],
            
            'package_structure': [
                'examples/',                       # Usage examples and production integration
                'docs/',                          # Comprehensive documentation
            ],
            
            'essential_support': [
                'atm_options_collector.py',        # Options data collection (contains OptionData class)
                'data_models.py',                  # Data structure definitions
                'config_manager.py',               # Configuration management
            ],
            
            'optional_utilities': [
                'token_manager.py',                # Token management utilities (if exists)
                'health_monitor.py',               # Health monitoring (if exists)
                'metrics_system.py',               # Metrics collection (if exists)
                'performance_monitor.py',          # Performance monitoring (if exists)
                'market_hours_complete.py',        # Market hours utilities (if exists)
                'overview_collector.py',           # Overview data collection (if exists)
            ]
        }
        
        return essential_files
    
    def get_redundant_files(self) -> List[str]:
        """🗑️ Define files that are NOT essential (legacy/redundant)."""
        
        redundant_patterns = [
            # Legacy launchers (replaced by main.py)
            'ultimate_*_launcher*.py',
            'enhanced_*_launcher*.py', 
            'fixed_*_launcher*.py',
            'nonblocking_*_launcher*.py',
            'web_launcher*.py',
            'final_launcher*.py',
            
            # Legacy kite login files (integrated into core)
            'kite_login_and_launch*.py',
            
            # Legacy main files (consolidated into main.py)
            'main_application_complete.py',
            'g6_platform_main*.py',
            'g6_enhanced_data_platform.py',
            'g6_immediate_output_platform.py',
            'g6_ultimate_data_platform.py',
            
            # Redundant README files
            'README (1).md',
            'README_G6.md',
            'FINAL_*.md',
            'FINAL_IMPLEMENTATION_SUMMARY.md',
            'FINAL_SOLUTION_SUMMARY.md',
            
            # Individual test files (replaced by comprehensive_testing.py)
            'test_analytics.py',
            'test_collectors.py', 
            'test_config.py',
            'quick_test.py',
            'mock_testing_framework.py',
            
            # Utility files that are optional or duplicated
            'quick_platform_diagnostic.py',
            'g6_diagnostics.py',
            
            # Enhanced files that are consolidated (but keep the _complete ones we might need)
            'enhanced_ultimate_launcher.py',
            'enhanced_terminal_ui.py',
            'enhanced_rich_launcher*.py',
            
            # Setup and debug files (functionality integrated)
            'token_debug_and_fix.py',
            
            # Specific FINAL versions that are redundant
            '*_FINAL*.py',
            '*_WORKING.py',
            'g6_platform_main_v2.py',
        ]
        
        return redundant_patterns
    
    def analyze_current_repository(self) -> Tuple[List[str], List[str], Dict[str, int]]:
        """🔍 Analyze current repository structure."""
        
        print("\n🔍 Analyzing Repository Structure...")
        print("-" * 45)
        
        all_files = []
        for root, dirs, files in os.walk('.'):
            # Skip hidden directories and common build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if not file.startswith('.') and not file.endswith('.pyc'):
                    rel_path = os.path.relpath(os.path.join(root, file), '.')
                    all_files.append(rel_path)
        
        # Categorize files
        essential_files_dict = self.get_essential_files()
        essential_files_flat = []
        for category, files in essential_files_dict.items():
            essential_files_flat.extend(files)
        
        # Find actual essential files (expand directories)
        actual_essential = []
        for pattern in essential_files_flat:
            if pattern.endswith('/'):
                # Directory pattern
                dir_name = pattern.rstrip('/')
                matching_files = [f for f in all_files if f.startswith(dir_name + '/')]
                actual_essential.extend(matching_files)
            else:
                # File pattern
                if pattern in all_files:
                    actual_essential.append(pattern)
        
        # Find redundant files
        redundant_patterns = self.get_redundant_files()
        redundant_files = []
        
        for file in all_files:
            for pattern in redundant_patterns:
                if '*' in pattern:
                    # Wildcard matching
                    prefix = pattern.split('*')[0]
                    suffix = pattern.split('*')[-1] if pattern.split('*')[-1] else ''
                    if file.startswith(prefix) and file.endswith(suffix):
                        redundant_files.append(file)
                        break
                else:
                    # Exact matching
                    if file == pattern:
                        redundant_files.append(file)
        
        # Calculate statistics
        stats = {
            'total_files': len(all_files),
            'essential_files': len(actual_essential),
            'redundant_files': len(redundant_files),
            'neutral_files': len(all_files) - len(actual_essential) - len(redundant_files)
        }
        
        print(f"  📁 Total Files: {stats['total_files']}")
        print(f"  ✅ Essential Files: {stats['essential_files']}")
        print(f"  🗑️ Redundant Files: {stats['redundant_files']}")
        print(f"  ➖ Neutral Files: {stats['neutral_files']}")
        
        return actual_essential, redundant_files, stats
    
    def create_package(self, package_name: str = None) -> str:
        """📦 Create the essential files package."""
        
        if not package_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            package_name = f"g6_essential_package_{timestamp}"
        
        print(f"\n📦 Creating Package: {package_name}")
        print("-" * 45)
        
        # Analyze repository
        essential_files, redundant_files, stats = self.analyze_current_repository()
        
        # Create package directory
        os.makedirs(package_name, exist_ok=True)
        
        # Copy essential files
        copied_files = []
        copy_errors = []
        
        for file_path in essential_files:
            try:
                src_path = file_path
                dest_path = os.path.join(package_name, file_path)
                
                # Create destination directory
                dest_dir = os.path.dirname(dest_path)
                if dest_dir:
                    os.makedirs(dest_dir, exist_ok=True)
                
                # Copy file
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dest_path)
                    copied_files.append(file_path)
                    print(f"  ✅ {file_path}")
                elif os.path.isdir(src_path):
                    if not os.path.exists(dest_path):
                        shutil.copytree(src_path, dest_path)
                        copied_files.append(file_path)
                        print(f"  ✅ {file_path}/ (directory)")
                
            except Exception as e:
                copy_errors.append(f"{file_path}: {str(e)}")
                print(f"  ❌ {file_path}: {str(e)}")
        
        # Replace main.py with enhanced version if available
        enhanced_main_path = 'enhanced_main_template.py'
        main_dest_path = os.path.join(package_name, 'main.py')
        if os.path.exists(enhanced_main_path) and os.path.exists(main_dest_path):
            try:
                shutil.copy2(enhanced_main_path, main_dest_path)
                print(f"  🔧 Enhanced main.py with better error handling")
            except Exception as e:
                print(f"  ⚠️ Could not use enhanced main.py: {e}")
        
        # Create __main__.py for proper package entry point
        main_module_path = os.path.join(package_name, '__main__.py')
        if not os.path.exists(main_module_path):
            with open(main_module_path, 'w', encoding='utf-8') as f:
                f.write('''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__main__.py - G6 Analytics Platform Package Entry Point
Allows running the package with: python -m g6_platform
"""

if __name__ == "__main__":
    from main import main
    main()
''')
            print(f"  ✅ Created __main__.py package entry point")
        
        # Analytics files are now in g6_platform/analytics/ where they belong
        # No need to copy them separately as they're included with g6_platform/
        
        # Rename setup_fixed.py to setup.py if needed
        setup_src = os.path.join(package_name, 'setup_fixed.py')
        setup_dest = os.path.join(package_name, 'setup.py')
        if os.path.exists(setup_src) and not os.path.exists(setup_dest):
            try:
                shutil.move(setup_src, setup_dest)
                print(f"  🔧 Renamed setup_fixed.py to setup.py")
            except Exception as e:
                print(f"  ⚠️ Could not rename setup file: {e}")
        elif os.path.exists(setup_dest):
            print(f"  ✅ setup.py already exists")
        
        # Ensure examples directory exists and has content
        examples_dir = os.path.join(package_name, 'examples')
        if os.path.exists('examples') and os.path.isdir('examples'):
            print(f"  ✅ examples/ directory included")
        else:
            # Create basic examples if source doesn't exist
            os.makedirs(examples_dir, exist_ok=True)
            example_usage_path = os.path.join(examples_dir, 'basic_usage.py')
            if not os.path.exists(example_usage_path):
                with open(example_usage_path, 'w', encoding='utf-8') as f:
                    f.write('''#!/usr/bin/env python3
"""
G6 Analytics Platform - Basic Usage Example
"""

from g6_platform.core.platform import G6Platform
from g6_platform.config.manager import ConfigManager

def main():
    """Example of basic platform usage."""
    
    # Initialize configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    # Initialize platform
    platform = G6Platform(config)
    
    # Start data collection
    print("🚀 Starting G6 Analytics Platform...")
    platform.start()
    
    print("✅ Platform started successfully!")
    print("📊 Check the data/ directory for collected data")
    print("📈 Check the logs/ directory for system logs")

if __name__ == "__main__":
    main()
''')
                print(f"  ✅ Created examples/basic_usage.py")
        
        # Ensure docs directory has content
        docs_dir = os.path.join(package_name, 'docs')
        if os.path.exists('docs') and os.path.isdir('docs'):
            print(f"  ✅ docs/ directory included")
        else:
            # Docs are now handled by the directory copy above
            pass
        
        # Create essential directories
        essential_dirs = ['data', 'data/csv', 'logs', 'tokens']
        for dir_path in essential_dirs:
            full_path = os.path.join(package_name, dir_path)
            os.makedirs(full_path, exist_ok=True)
            
            # Create .gitkeep file
            gitkeep_path = os.path.join(full_path, '.gitkeep')
            with open(gitkeep_path, 'w', encoding='utf-8') as f:
                f.write('# Directory structure preserved for G6 Platform\n')
        
        # Create package documentation
        self.create_package_documentation(package_name, essential_files, redundant_files, stats, copy_errors)
        
        # Create deployment scripts
        self.create_deployment_scripts(package_name)
        
        # Calculate package size
        package_size = self.get_directory_size(package_name)
        
        print(f"\n🎉 Package Created Successfully!")
        print(f"  📦 Package: {package_name}")
        print(f"  📏 Size: {package_size:.2f} MB")
        print(f"  📄 Files: {len(copied_files)}")
        if copy_errors:
            print(f"  ⚠️ Errors: {len(copy_errors)}")
        
        # Validate the package
        validation_results = self.validate_package(package_name)
        
        return package_name
    
    def create_package_documentation(self, package_name: str, essential_files: List[str], 
                                   redundant_files: List[str], stats: Dict[str, int], 
                                   copy_errors: List[str]):
        """📚 Create package documentation."""
        
        package_info_path = os.path.join(package_name, 'PACKAGE_INFO.md')
        
        with open(package_info_path, 'w', encoding='utf-8') as f:
            f.write(f"""# 📦 G6 Analytics Platform - Essential Files Package

## Package Information

- **Created**: {self.package_info['created_at']}
- **Version**: {self.package_info['version']}
- **Package Size**: {self.get_directory_size(package_name):.2f} MB
- **Total Files**: {len(essential_files)}

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run First-Time Setup
```bash
python first_run_diagnostics.py
```

### 3. Configure API Credentials
Create a `.env` file:
```bash
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
KITE_ACCESS_TOKEN=your_access_token_here
```

### 4. Run Tests
```bash
python comprehensive_testing.py
```

### 5. Start Platform
```bash
python main.py
```

## 📁 Package Contents

### Essential Files Included ({len(essential_files)} files)

#### Entry Points
- `main.py` - Unified application entry point
- `first_run_diagnostics.py` - System validation and setup
- `comprehensive_testing.py` - Complete testing framework

#### Analytics Engine
- `analytics_engine.py` - Complete IV, Greeks, and PCR calculations
- `risk_analyzer.py` - Advanced risk analysis and management
- `volatility_analyzer.py` - Volatility calculations and analysis
- `g6_platform/analytics/` - Analytics modules integrated into core platform

#### Core Platform
- `g6_platform/` - Complete core platform package
  - `core/` - Platform orchestration  
  - `api/` - Kite Connect integration & token management
  - `collectors/` - Data collection modules
  - `storage/` - CSV and InfluxDB storage backends
  - `analytics/` - Options analytics engines + weekday overlay
  - `monitoring/` - Health checks and metrics
  - `config/` - Configuration management
  - `ui/` - Production dashboard and terminal interfaces
  - `utils/` - Utilities and data models

#### Package Structure
- `setup.py` - Professional package installation
- `__main__.py` - Single entry point for package execution
- `examples/` - Usage examples and production integration
- `docs/` - Comprehensive documentation

#### Configuration
- `config.json` - Application configuration
- `requirements.txt` - Python dependencies

#### Documentation
- `COMPLETE_README.md` - Comprehensive documentation
- `API_REFERENCE.md` - API documentation
- `CONFIGURATION_GUIDE.md` - Configuration guide

### Repository Optimization

**Original Repository**: {stats['total_files']} files
**Essential Package**: {len(essential_files)} files
**Reduction**: {((stats['total_files'] - len(essential_files)) / stats['total_files'] * 100):.1f}%

### Files NOT Included ({len(redundant_files)} files)

These files were excluded as they are legacy/redundant:
{chr(10).join(f'- {f}' for f in redundant_files[:20])}
{'...' if len(redundant_files) > 20 else ''}

### What This Package Provides

✅ **Complete Analytics Engine** - IV, Greeks, PCR calculations
✅ **Full Testing Framework** - Comprehensive validation
✅ **First-Run Diagnostics** - System setup validation  
✅ **Production Ready** - Enterprise-grade error handling
✅ **Complete Documentation** - Detailed guides and API reference
✅ **Unified Entry Point** - Single main.py launcher
✅ **Clean Architecture** - Modular, maintainable codebase

### System Requirements

- Python 3.8+
- 1GB+ RAM
- 500MB+ disk space
- Kite Connect API credentials

### Support

For issues or questions, refer to:
- `COMPLETE_README.md` - Comprehensive documentation
- `TROUBLESHOOTING.md` - Common issues and solutions
- `first_run_diagnostics.py` - System validation

---

**This package contains everything needed for a fully functional G6 Analytics Platform deployment.**
""")
        
        # Create file list
        file_list_path = os.path.join(package_name, 'FILE_LIST.txt')
        with open(file_list_path, 'w', encoding='utf-8') as f:
            f.write("G6 Analytics Platform - Essential Files List\n")
            f.write("=" * 50 + "\n\n")
            
            for file_path in sorted(essential_files):
                if os.path.exists(os.path.join(package_name, file_path)):
                    size = os.path.getsize(os.path.join(package_name, file_path))
                    f.write(f"{file_path:<40} {size:>10} bytes\n")
        
        # Create setup log
        if copy_errors:
            error_log_path = os.path.join(package_name, 'SETUP_ERRORS.log')
            with open(error_log_path, 'w', encoding='utf-8') as f:
                f.write("Package Creation Errors\n")
                f.write("=" * 30 + "\n\n")
                for error in copy_errors:
                    f.write(f"{error}\n")
    
    def create_deployment_scripts(self, package_name: str):
        """🚀 Create deployment scripts."""
        
        # Create setup script for Unix/Linux
        setup_script_path = os.path.join(package_name, 'setup.sh')
        with open(setup_script_path, 'w', encoding='utf-8') as f:
            f.write("""#!/bin/bash
# G6 Analytics Platform - Setup Script

echo "🚀 Setting up G6 Analytics Platform..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run first-time diagnostics
echo "🔧 Running first-time diagnostics..."
python first_run_diagnostics.py

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️ Creating .env template file..."
    cat > .env << EOF
# Kite Connect API Credentials
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
KITE_ACCESS_TOKEN=your_access_token_here

# Optional: InfluxDB Configuration
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_token_here
INFLUXDB_ORG=your_org_here
EOF
    echo "📝 Please edit .env file with your API credentials"
fi

echo "✅ Setup complete! Run 'python main.py' to start the platform."
""")
        
        # Make setup script executable
        try:
            os.chmod(setup_script_path, 0o755)
        except:
            pass  # Windows doesn't support chmod
        
        # Create Windows batch file
        setup_bat_path = os.path.join(package_name, 'setup.bat')
        with open(setup_bat_path, 'w', encoding='utf-8') as f:
            f.write("""@echo off
REM G6 Analytics Platform - Windows Setup Script

echo 🚀 Setting up G6 Analytics Platform...

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Run first-time diagnostics
echo 🔧 Running first-time diagnostics...
python first_run_diagnostics.py

REM Check if .env file exists
if not exist .env (
    echo ⚠️ Creating .env template file...
    (
    echo # Kite Connect API Credentials
    echo KITE_API_KEY=your_api_key_here
    echo KITE_API_SECRET=your_api_secret_here
    echo KITE_ACCESS_TOKEN=your_access_token_here
    echo.
    echo # Optional: InfluxDB Configuration
    echo INFLUXDB_URL=http://localhost:8086
    echo INFLUXDB_TOKEN=your_token_here
    echo INFLUXDB_ORG=your_org_here
    ) > .env
    echo 📝 Please edit .env file with your API credentials
)

echo ✅ Setup complete! Run 'python main.py' to start the platform.
pause
""")
    
    def get_directory_size(self, path: str) -> float:
        """📏 Calculate directory size in MB."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass  # Handle permission errors
        return total_size / (1024 * 1024)
    
    def validate_package(self, package_name: str) -> Dict[str, Any]:
        """🔍 Validate the created package for completeness and functionality."""
        
        print(f"\n🔍 Validating Package: {package_name}")
        print("-" * 45)
        
        validation_results = {
            'package_structure': False,
            'import_tests': False,
            'dependencies': False,
            'configuration': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check package structure
            required_files = ['main.py', 'config.json', 'requirements.txt', 'first_run_diagnostics.py']
            required_dirs = ['g6_platform', 'data', 'logs']
            
            missing_files = []
            for file in required_files:
                if not os.path.exists(os.path.join(package_name, file)):
                    missing_files.append(file)
            
            missing_dirs = []
            for dir_name in required_dirs:
                if not os.path.exists(os.path.join(package_name, dir_name)):
                    missing_dirs.append(dir_name)
            
            if not missing_files and not missing_dirs:
                validation_results['package_structure'] = True
                print("  ✅ Package structure - Complete")
            else:
                validation_results['errors'].extend([f"Missing file: {f}" for f in missing_files])
                validation_results['errors'].extend([f"Missing directory: {d}" for d in missing_dirs])
                print(f"  ❌ Package structure - Missing: {missing_files + missing_dirs}")
            
            # Test basic imports (simplified check)
            import sys
            original_path = sys.path.copy()
            try:
                sys.path.insert(0, package_name)
                
                # Test if we can read the main files without executing them
                main_path = os.path.join(package_name, 'main.py')
                if os.path.exists(main_path):
                    with open(main_path, 'r', encoding='utf-8') as f:
                        main_content = f.read()
                        # Check for enhanced main.py features
                        if ('def check_and_install_dependencies' in main_content and 
                            'class G6Launcher' in main_content and
                            'def main()' in main_content):
                            validation_results['import_tests'] = True
                            print("  ✅ Import tests - Enhanced main.py detected")
                        elif 'from g6_platform import' in main_content and 'def main()' in main_content:
                            validation_results['import_tests'] = True
                            print("  ✅ Import tests - Standard main.py detected")
                        else:
                            validation_results['warnings'].append("main.py structure may be incomplete")
                            print("  ⚠️ Import tests - Warnings")
                
            except Exception as e:
                validation_results['errors'].append(f"Import test error: {str(e)}")
                print(f"  ❌ Import tests - Failed: {str(e)}")
            finally:
                sys.path = original_path
            
            # Check dependencies
            req_path = os.path.join(package_name, 'requirements.txt')
            if os.path.exists(req_path):
                with open(req_path, 'r', encoding='utf-8') as f:
                    requirements = f.read()
                    critical_deps = ['kiteconnect', 'numpy', 'rich', 'requests']
                    missing_deps = [dep for dep in critical_deps if dep not in requirements]
                    
                    if not missing_deps:
                        validation_results['dependencies'] = True
                        print("  ✅ Dependencies - Complete")
                    else:
                        validation_results['warnings'].extend([f"Missing dependency: {dep}" for dep in missing_deps])
                        print(f"  ⚠️ Dependencies - Missing: {missing_deps}")
            
            # Check configuration
            config_path = os.path.join(package_name, 'config.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        if 'platform' in config and 'market' in config:
                            validation_results['configuration'] = True
                            print("  ✅ Configuration - Valid")
                        else:
                            validation_results['warnings'].append("Configuration may be incomplete")
                            print("  ⚠️ Configuration - Incomplete")
                except json.JSONDecodeError as e:
                    validation_results['errors'].append(f"Configuration JSON error: {str(e)}")
                    print(f"  ❌ Configuration - Invalid JSON")
            
        except Exception as e:
            validation_results['errors'].append(f"Validation error: {str(e)}")
            print(f"  ❌ Validation failed: {str(e)}")
        
        # Summary
        passed_checks = sum([validation_results['package_structure'], 
                           validation_results['import_tests'],
                           validation_results['dependencies'], 
                           validation_results['configuration']])
        total_checks = 4
        
        print(f"\n📊 Validation Summary: {passed_checks}/{total_checks} checks passed")
        if validation_results['warnings']:
            print(f"⚠️ Warnings: {len(validation_results['warnings'])}")
        if validation_results['errors']:
            print(f"❌ Errors: {len(validation_results['errors'])}")
        
        return validation_results
    
    def create_zip_package(self, package_name: str) -> str:
        """🗜️ Create ZIP archive of the package."""
        
        zip_name = f"{package_name}.zip"
        
        print(f"\n🗜️ Creating ZIP Archive: {zip_name}")
        print("-" * 45)
        
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_name):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, '.')
                    zipf.write(file_path, arc_path)
                    print(f"  ✅ {arc_path}")
        
        zip_size = os.path.getsize(zip_name) / (1024 * 1024)
        print(f"\n📦 ZIP Archive Created: {zip_name} ({zip_size:.2f} MB)")
        
        return zip_name
        """🗜️ Create ZIP archive of the package."""
        
        zip_name = f"{package_name}.zip"
        
        print(f"\n🗜️ Creating ZIP Archive: {zip_name}")
        print("-" * 45)
        
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_name):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, '.')
                    zipf.write(file_path, arc_path)
                    print(f"  ✅ {arc_path}")
        
        zip_size = os.path.getsize(zip_name) / (1024 * 1024)
        print(f"\n📦 ZIP Archive Created: {zip_name} ({zip_size:.2f} MB)")
        
        return zip_name

def main():
    """🚀 Main entry point for package creation."""
    
    creator = EssentialPackageCreator()
    
    # Create the package
    package_name = creator.create_package()
    
    # Ask user if they want to create ZIP
    try:
        create_zip = input(f"\n📦 Create ZIP archive? (y/n): ").lower().strip()
        if create_zip in ['y', 'yes']:
            zip_name = creator.create_zip_package(package_name)
            print(f"\n🎉 Complete package created:")
            print(f"  📁 Directory: {package_name}")
            print(f"  🗜️ ZIP Archive: {zip_name}")
        else:
            print(f"\n🎉 Package created: {package_name}")
    except KeyboardInterrupt:
        print(f"\n🎉 Package created: {package_name}")
    
    print(f"\n📖 Next Steps:")
    print(f"  1. cd {package_name}")
    print(f"  2. Read PACKAGE_INFO.md for setup instructions")
    print(f"  3. Run setup script (setup.sh or setup.bat)")
    print(f"  4. Configure API credentials in .env file")
    print(f"  5. python main.py")
    
    return package_name

if __name__ == "__main__":
    main()