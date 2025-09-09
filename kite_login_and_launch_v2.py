#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Enhanced Kite Login and Platform Launcher - G6.1 v2.0
Author: AI Assistant (Complete integrated launcher)

Features:
- Enhanced terminal UI integration
- Menu-based authentication flow
- Configuration management
- System diagnostics
- Platform monitoring
- Auto-setup and validation
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

# UTF-8 support for Windows
import os
import sys

# 🔧 Windows UTF-8 Fix
if os.name == 'nt':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import enhanced components
try:
    from config_manager import get_config, ConfigurationManager
    from enhanced_terminal_ui import TerminalUI
    from enhanced_kite_provider import EnhancedKiteDataProvider
    ENHANCED_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Enhanced components not available: {e}")
    ENHANCED_COMPONENTS_AVAILABLE = False

# Fallback imports
from dotenv import load_dotenv, set_key
load_dotenv()

class EnhancedLauncher:
    """🚀 Enhanced platform launcher with full UI integration."""
    
    def __init__(self):
        """Initialize enhanced launcher."""
        # Load configuration
        if ENHANCED_COMPONENTS_AVAILABLE:
            self.config = get_config()
            self.ui = TerminalUI()
        else:
            self.config = None
            self.ui = None
        
        # Platform state
        self.platform_process = None
        self.is_running = False
        
        # Environment variables
        self.api_key = os.getenv('KITE_API_KEY')
        self.api_secret = os.getenv('KITE_API_SECRET')
        self.access_token = os.getenv('KITE_ACCESS_TOKEN')
        
        print("✅ Enhanced Launcher initialized")
    
    def show_system_status(self):
        """📊 Show comprehensive system status."""
        if self.ui and self.ui.use_rich:
            from rich.table import Table
            from rich.panel import Panel
            
            status_table = Table(title="🖥️ System Status", show_header=True)
            status_table.add_column("Component", style="cyan")
            status_table.add_column("Status", style="green")
            status_table.add_column("Details")
            
            # Check Python version
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            status_table.add_row("Python", "✅ Compatible", python_version)
            
            # Check dependencies
            dependencies = [
                ('kiteconnect', 'Kite API'),
                ('rich', 'Enhanced UI'),
                ('dotenv', 'Environment'),
                ('pathlib', 'File System')
            ]
            
            for module, description in dependencies:
                try:
                    __import__(module)
                    status_table.add_row(description, "✅ Available", "Installed")
                except ImportError:
                    status_table.add_row(description, "❌ Missing", "pip install " + module)
            
            # Check configuration
            if self.config:
                config_status = "✅ Loaded" if Path('config.json').exists() else "⚠️ Using Template"
                status_table.add_row("Configuration", config_status, "JSON + Environment")
            else:
                status_table.add_row("Configuration", "❌ Failed", "Check config files")
            
            # Check credentials
            cred_status = "✅ Complete" if (self.api_key and self.access_token) else "⚠️ Incomplete"
            status_table.add_row("Credentials", cred_status, f"API Key: {'✅' if self.api_key else '❌'}, Token: {'✅' if self.access_token else '❌'}")
            
            # Check data directories
            data_dir = Path('data/csv')
            data_status = "✅ Ready" if data_dir.exists() else "⚠️ Will Create"
            status_table.add_row("Data Storage", data_status, str(data_dir))
            
            self.ui.console.print(status_table)
            
            # Show configuration summary if available
            if self.config:
                config_summary = self.config.get_config_summary()
                
                config_info = f"""
**Platform**: {config_summary['platform']['name']} v{config_summary['platform']['version']}
**Mode**: {config_summary['platform']['mode']}
**Indices**: {', '.join(config_summary['market']['indices'])}
**Collection Interval**: {config_summary['market']['collection_interval']}s
**Storage**: CSV {'✅' if config_summary['storage']['csv_enabled'] else '❌'}, InfluxDB {'✅' if config_summary['storage']['influxdb_enabled'] else '❌'}
**Environment Overrides**: {config_summary['environment_overrides']}
"""
                
                self.ui.console.print(Panel(config_info, title="📊 Configuration Summary"))
        else:
            # Fallback text display
            print("\n📊 SYSTEM STATUS")
            print("-" * 40)
            print(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
            print(f"API Key: {'✅ Set' if self.api_key else '❌ Missing'}")
            print(f"Access Token: {'✅ Set' if self.access_token else '❌ Missing'}")
            print(f"Configuration: {'✅ Enhanced' if ENHANCED_COMPONENTS_AVAILABLE else '❌ Basic'}")
    
    def run_system_diagnostics(self):
        """🧪 Run comprehensive system diagnostics."""
        if self.ui and self.ui.use_rich:
            with self.ui.console.status("🧪 Running system diagnostics...") as status:
                
                # Test 1: Configuration validation
                status.update("Testing configuration...")
                if self.config:
                    try:
                        summary = self.config.get_config_summary()
                        self.ui.console.print("✅ Configuration validation passed")
                    except Exception as e:
                        self.ui.console.print(f"❌ Configuration error: {e}")
                
                # Test 2: Token validation
                status.update("Validating access token...")
                if self.access_token and self.api_key:
                    token_valid = self.ui.test_token_validity(self.access_token, self.api_key)
                    if token_valid:
                        self.ui.console.print("✅ Access token validation passed")
                    else:
                        self.ui.console.print("❌ Access token validation failed")
                else:
                    self.ui.console.print("⚠️ Access token validation skipped (missing credentials)")
                
                # Test 3: Data provider test
                status.update("Testing data provider...")
                try:
                    if self.api_key and self.access_token:
                        provider = EnhancedKiteDataProvider(self.api_key, self.access_token)
                        health = provider.check_health()
                        
                        if health['status'] == 'healthy':
                            self.ui.console.print("✅ Data provider test passed")
                        else:
                            self.ui.console.print("⚠️ Data provider test partial")
                        
                        provider.close()
                    else:
                        self.ui.console.print("⚠️ Data provider test skipped (missing credentials)")
                except Exception as e:
                    self.ui.console.print(f"❌ Data provider test failed: {e}")
                
                # Test 4: Storage directories
                status.update("Checking storage directories...")
                data_dirs = ['data/csv', 'data/logs', 'data/cache', 'data/backups']
                for dir_path in data_dirs:
                    try:
                        Path(dir_path).mkdir(parents=True, exist_ok=True)
                        self.ui.console.print(f"✅ Storage directory ready: {dir_path}")
                    except Exception as e:
                        self.ui.console.print(f"❌ Storage directory error: {dir_path} - {e}")
                
                # Test 5: Network connectivity
                status.update("Testing network connectivity...")
                try:
                    import urllib.request
                    urllib.request.urlopen('https://api.kite.trade', timeout=5)
                    self.ui.console.print("✅ Network connectivity test passed")
                except Exception as e:
                    self.ui.console.print(f"❌ Network connectivity test failed: {e}")
        else:
            print("🧪 Running basic diagnostics...")
            print(f"✅ Python version: {sys.version_info}")
            print(f"{'✅' if self.api_key else '❌'} API Key present")
            print(f"{'✅' if self.access_token else '❌'} Access Token present")
            print("✅ Basic diagnostics completed")
    
    def create_default_configuration(self):
        """⚙️ Create default configuration files."""
        try:
            # Create config.json from template
            template_file = Path('config_template.json')
            config_file = Path('config.json')
            
            if template_file.exists() and not config_file.exists():
                import shutil
                shutil.copy(template_file, config_file)
                print("✅ Created config.json from template")
            
            # Create .env from template
            env_template = Path('.env.template')
            env_file = Path('.env')
            
            if not env_file.exists():
                with open(env_file, 'w') as f:
                    f.write("""# G6.1 Platform Environment Variables
# Kite Connect API Credentials
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
KITE_ACCESS_TOKEN=your_access_token_here

# Optional: InfluxDB Configuration
# INFLUXDB_URL=http://localhost:8086
# INFLUXDB_TOKEN=your_influxdb_token
# INFLUXDB_ORG=g6_analytics

# Debug Settings
G6_DEBUG_MODE=false
G6_MOCK_MODE=false
""")
                print("✅ Created .env template file")
                print("📝 Please edit .env with your API credentials")
            
            # Create data directories
            data_dirs = ['data/csv', 'data/logs', 'data/cache', 'data/backups']
            for dir_path in data_dirs:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            
            print("✅ Default configuration setup completed")
            
        except Exception as e:
            print(f"❌ Configuration setup failed: {e}")
    
    def launch_platform(self):
        """🚀 Launch the enhanced platform."""
        try:
            if self.ui and self.ui.use_rich:
                with self.ui.console.status("🚀 Launching G6.1 Platform v2.0...") as status:
                    # Check if main platform file exists
                    platform_file = Path('g6_platform_main_v2.py')
                    if not platform_file.exists():
                        # Try fallback files
                        fallback_files = [
                            'g6_platform_main_FINAL_WORKING.py',
                            'g6_platform_main_fixed_FINAL.py',
                            'kite_login_and_launch_FINAL_WORKING.py'
                        ]
                        
                        for fallback in fallback_files:
                            if Path(fallback).exists():
                                platform_file = Path(fallback)
                                break
                    
                    if not platform_file.exists():
                        self.ui.console.print("❌ No platform file found")
                        return False
                    
                    # Setup environment
                    env = os.environ.copy()
                    env['PYTHONIOENCODING'] = 'utf-8'
                    env['PYTHONUTF8'] = '1'
                    
                    # Launch platform
                    self.platform_process = subprocess.Popen(
                        [sys.executable, str(platform_file)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        env=env
                    )
                    
                    self.is_running = True
                    self.ui.console.print(f"✅ Platform launched: {platform_file}")
                    
                    # Stream output
                    try:
                        for line in iter(self.platform_process.stdout.readline, ''):
                            if line.strip():
                                self.ui.process_log_line(line.strip())
                            
                            # Check if process ended
                            if self.platform_process.poll() is not None:
                                break
                        
                        # Get exit code
                        exit_code = self.platform_process.wait()
                        
                        if exit_code == 0:
                            self.ui.console.print("✅ Platform exited successfully")
                        else:
                            self.ui.console.print(f"⚠️ Platform exited with code: {exit_code}")
                        
                        return exit_code == 0
                        
                    except KeyboardInterrupt:
                        self.ui.console.print("\n🛑 Platform interrupted by user")
                        self.stop_platform()
                        return True
            else:
                # Fallback launch
                print("🚀 Launching platform (basic mode)...")
                result = subprocess.run([
                    sys.executable, 'g6_platform_main_v2.py'
                ])
                return result.returncode == 0
                
        except Exception as e:
            if self.ui:
                self.ui.console.print(f"❌ Platform launch failed: {e}")
            else:
                print(f"❌ Launch failed: {e}")
            return False
    
    def stop_platform(self):
        """🛑 Stop the running platform."""
        if self.platform_process and self.is_running:
            try:
                self.platform_process.terminate()
                try:
                    self.platform_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.platform_process.kill()
                    self.platform_process.wait()
                
                self.is_running = False
                print("🛑 Platform stopped")
                
            except Exception as e:
                print(f"❌ Error stopping platform: {e}")
    
    def run_interactive_launcher(self):
        """🖥️ Run the interactive launcher interface."""
        if not ENHANCED_COMPONENTS_AVAILABLE:
            print("❌ Enhanced components not available")
            print("📝 Please install requirements: pip install rich kiteconnect python-dotenv")
            return self.run_basic_launcher()
        
        try:
            while True:
                self.ui.print_banner()
                
                # Show system status
                self.show_system_status()
                
                # Main menu
                if self.ui.use_rich:
                    from rich.panel import Panel
                    
                    menu_text = """
[cyan]1.[/cyan] 🔐 Token Management & Authentication
[cyan]2.[/cyan] ⚙️  Configuration Management
[cyan]3.[/cyan] 🧪 System Diagnostics
[cyan]4.[/cyan] 🚀 Launch Platform
[cyan]5.[/cyan] 📊 View Metrics & Logs
[cyan]6.[/cyan] 🛠️  Setup & Installation
[cyan]7.[/cyan] ❌ Exit

"""
                    
                    self.ui.console.print(Panel(menu_text, title="🚀 G6.1 Platform Launcher v2.0"))
                    
                    from rich.prompt import Prompt
                    choice = Prompt.ask(
                        "Select option",
                        choices=["1", "2", "3", "4", "5", "6", "7"],
                        default="4"
                    )
                else:
                    print("\n🚀 G6.1 PLATFORM LAUNCHER v2.0")
                    print("-" * 40)
                    print("1. 🔐 Token Management")
                    print("2. ⚙️  Configuration")
                    print("3. 🧪 System Diagnostics")
                    print("4. 🚀 Launch Platform")
                    print("5. 📊 View Metrics")
                    print("6. 🛠️  Setup")
                    print("7. ❌ Exit")
                    
                    choice = input("\nSelect option [1-7] (default: 4): ").strip() or "4"
                
                # Handle choices
                if choice == "1":
                    self.ui.show_token_menu()
                elif choice == "2":
                    self.ui.show_configuration_menu()
                elif choice == "3":
                    self.run_system_diagnostics()
                elif choice == "4":
                    launched = self.launch_platform()
                    if not launched:
                        input("\n⚠️ Launch failed. Press Enter to continue...")
                elif choice == "5":
                    # Show metrics placeholder
                    print("📊 Metrics dashboard coming soon...")
                    input("Press Enter to continue...")
                elif choice == "6":
                    self.create_default_configuration()
                    input("Press Enter to continue...")
                elif choice == "7":
                    if self.ui.use_rich:
                        self.ui.console.print("👋 Goodbye!")
                    else:
                        print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice")
                
                if choice != "4":  # Don't pause after platform launch
                    input("\nPress Enter to continue...")
                    
        except KeyboardInterrupt:
            print("\n🛑 Launcher interrupted")
        except Exception as e:
            print(f"❌ Launcher error: {e}")
        finally:
            if self.is_running:
                self.stop_platform()
    
    def run_basic_launcher(self):
        """🔧 Run basic launcher without enhanced UI."""
        print("\n🚀 G6.1 PLATFORM LAUNCHER (Basic Mode)")
        print("=" * 50)
        
        while True:
            print("\n📋 OPTIONS:")
            print("1. Setup Configuration")
            print("2. Test Credentials")
            print("3. Launch Platform")
            print("4. Exit")
            
            choice = input("\nSelect option [1-4]: ").strip()
            
            if choice == "1":
                self.create_default_configuration()
            elif choice == "2":
                print("Testing credentials...")
                print(f"API Key: {'✅' if self.api_key else '❌'}")
                print(f"Access Token: {'✅' if self.access_token else '❌'}")
            elif choice == "3":
                self.launch_platform()
                break
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
            
            input("Press Enter to continue...")

def main():
    """🚀 Main launcher entry point."""
    try:
        # Initialize launcher
        launcher = EnhancedLauncher()
        
        # Run interactive launcher
        launcher.run_interactive_launcher()
        
        return 0
        
    except Exception as e:
        print(f"❌ Launcher error: {e}")
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)