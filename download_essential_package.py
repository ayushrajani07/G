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
"""

import os
import shutil
import json
import zipfile
from datetime import datetime
from typing import List, Dict, Tuple
import subprocess

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
                'first_run_diagnostics.py',        # System validation and setup
                'comprehensive_testing.py',        # Complete testing framework
            ],
            
            'analytics_engine': [
                'analytics_engine.py',             # Complete analytics implementation
            ],
            
            'core_platform': [
                'g6_platform/',                    # Entire core platform package
            ],
            
            'configuration': [
                'config.json',                     # Application configuration
                'config_template.json',            # Configuration template
                'requirements.txt',                # Python dependencies
                '.gitignore',                      # Git ignore rules
            ],
            
            'documentation': [
                'COMPLETE_README.md',              # Comprehensive documentation
                'API_REFERENCE.md',                # API documentation
                'CONFIGURATION_GUIDE.md',          # Configuration guide
                'TROUBLESHOOTING.md',              # Troubleshooting guide
            ],
            
            'essential_support': [
                'atm_options_collector.py',        # Options data collection (contains OptionData class)
                'data_models.py',                  # Data structure definitions
                'config_manager.py',               # Configuration management
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
            
            # Legacy kite login files (integrated into core)
            'kite_login_and_launch*.py',
            
            # Legacy main files (consolidated)
            'main_application_complete.py',
            'g6_platform_main*.py',
            'g6_enhanced_data_platform.py',
            'g6_immediate_output_platform.py',
            'g6_ultimate_data_platform.py',
            
            # Redundant README files
            'README (1).md',
            'README_G6.md',
            'FINAL_*.md',
            
            # Individual test files (replaced by comprehensive_testing.py)
            'test_analytics.py',
            'test_collectors.py', 
            'test_config.py',
            'quick_test.py',
            'mock_testing_framework.py',
            
            # Utility files that are optional
            'overview_collector.py',
            'overview_generator.py',
            'quick_platform_diagnostic.py',
            'g6_diagnostics.py',
            
            # Enhanced files that are consolidated
            'enhanced_*.py',
            
            # Setup and token debug files
            'setup_fixed.py',
            'token_debug_and_fix.py',
            
            # Complete versions (functionality integrated)
            '*_complete.py',
            '*_FINAL*.py',
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
        
        # Create essential directories
        essential_dirs = ['data', 'data/csv', 'logs', 'tokens']
        for dir_path in essential_dirs:
            full_path = os.path.join(package_name, dir_path)
            os.makedirs(full_path, exist_ok=True)
            
            # Create .gitkeep file
            gitkeep_path = os.path.join(full_path, '.gitkeep')
            with open(gitkeep_path, 'w') as f:
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
        
        return package_name
    
    def create_package_documentation(self, package_name: str, essential_files: List[str], 
                                   redundant_files: List[str], stats: Dict[str, int], 
                                   copy_errors: List[str]):
        """📚 Create package documentation."""
        
        package_info_path = os.path.join(package_name, 'PACKAGE_INFO.md')
        
        with open(package_info_path, 'w') as f:
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

#### Core Platform
- `g6_platform/` - Complete core platform package

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
        with open(file_list_path, 'w') as f:
            f.write("G6 Analytics Platform - Essential Files List\n")
            f.write("=" * 50 + "\n\n")
            
            for file_path in sorted(essential_files):
                if os.path.exists(os.path.join(package_name, file_path)):
                    size = os.path.getsize(os.path.join(package_name, file_path))
                    f.write(f"{file_path:<40} {size:>10} bytes\n")
        
        # Create setup log
        if copy_errors:
            error_log_path = os.path.join(package_name, 'SETUP_ERRORS.log')
            with open(error_log_path, 'w') as f:
                f.write("Package Creation Errors\n")
                f.write("=" * 30 + "\n\n")
                for error in copy_errors:
                    f.write(f"{error}\n")
    
    def create_deployment_scripts(self, package_name: str):
        """🚀 Create deployment scripts."""
        
        # Create setup script for Unix/Linux
        setup_script_path = os.path.join(package_name, 'setup.sh')
        with open(setup_script_path, 'w') as f:
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
        with open(setup_bat_path, 'w') as f:
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