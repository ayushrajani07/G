#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 G6 Platform Main Entry Point - v3.0 (Enhanced Package Version)
Unified application launcher with enhanced dependency handling and fallbacks.

This is the single entry point that replaces scattered launcher files with:
- Robust dependency checking and error reporting
- Graceful fallbacks for missing components
- Clear setup instructions for users
- Enhanced error handling and recovery
"""

import os
import sys
import signal
import logging
from datetime import datetime
from typing import Optional

# Add package to path for development
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_and_install_dependencies():
    """Check critical dependencies and provide installation guidance."""
    missing_deps = []
    critical_deps = [
        ('numpy', 'numpy'),
        ('requests', 'requests'), 
        ('rich', 'rich'),
        ('dotenv', 'python-dotenv'),
        ('kiteconnect', 'kiteconnect')
    ]
    
    print("🔍 Checking dependencies...")
    for module_name, pip_name in critical_deps:
        try:
            __import__(module_name)
            print(f"  ✅ {module_name}")
        except ImportError:
            missing_deps.append(pip_name)
            print(f"  ❌ {module_name} (install: pip install {pip_name})")
    
    if missing_deps:
        print(f"\n🔴 Missing {len(missing_deps)} critical dependencies!")
        print("🔧 Run one of these commands to install missing dependencies:")
        print(f"   pip install {' '.join(missing_deps)}")
        print("   OR")
        print("   pip install -r requirements.txt")
        print("\n📖 Then run this script again.")
        return False
    
    print("✅ All critical dependencies available!")
    return True

def safe_import_platform():
    """Safely import G6 platform components with detailed error reporting."""
    try:
        from g6_platform import G6Platform, ConfigurationManager, get_version, get_package_info
        from g6_platform.config.manager import get_config_manager
        from g6_platform.utils.path_resolver import PathResolver
        return {
            'G6Platform': G6Platform,
            'ConfigurationManager': ConfigurationManager,
            'get_config_manager': get_config_manager,
            'PathResolver': PathResolver,
            'get_version': get_version,
            'get_package_info': get_package_info
        }
    except ImportError as e:
        print(f"🔴 Failed to import G6 platform components: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Ensure you're running from the package directory")
        print("2. Install missing dependencies: pip install -r requirements.txt")
        print("3. Run first-run diagnostics: python first_run_diagnostics.py")
        return None

def safe_import_ui():
    """Safely import UI components with fallback."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        return {'Console': Console, 'Panel': Panel, 'Text': Text, 'available': True}
    except ImportError:
        print("⚠️ Rich UI not available - using basic text interface")
        return {'available': False}

class G6Launcher:
    """Enhanced G6 Platform launcher with robust error handling."""
    
    def __init__(self):
        """Initialize the launcher with dependency checking."""
        self.platform_components = None
        self.ui_components = None
        self.platform = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.shutdown()
        sys.exit(0)
    
    def initialize(self):
        """Initialize all components with proper error handling."""
        print("🚀 G6 Analytics Platform - Enhanced Package Edition")
        print("=" * 60)
        
        # Check dependencies first
        if not check_and_install_dependencies():
            return False
        
        # Import platform components
        self.platform_components = safe_import_platform()
        if not self.platform_components:
            return False
        
        # Import UI components
        self.ui_components = safe_import_ui()
        
        # Display banner
        self.display_banner()
        
        return True
    
    def display_banner(self):
        """Display application banner."""
        if not self.platform_components:
            return
            
        version = self.platform_components['get_version']()
        package_info = self.platform_components['get_package_info']()
        
        if self.ui_components['available']:
            # Rich banner
            console = self.ui_components['Console']()
            text = self.ui_components['Text']()
            text.append("🚀 G6 Options Analytics Platform\n", style="bold blue")
            text.append(f"Version {version}\n", style="green")
            text.append("Professional Options Trading Platform for Indian Markets\n", style="white")
            text.append(f"Supported Indices: {', '.join(package_info['supported_instruments'])}", style="yellow")
            
            panel = self.ui_components['Panel'](
                text,
                title="G6 Platform",
                title_align="center",
                padding=(1, 2)
            )
            console.print(panel)
        else:
            # Fallback text banner
            print("🚀 G6 Options Analytics Platform")
            print(f"Version {version}")
            print("Professional Options Trading Platform for Indian Markets")
            print(f"Supported Indices: {', '.join(package_info['supported_instruments'])}")
            print("=" * 60)
    
    def run_setup_wizard(self):
        """Run setup wizard for first-time users."""
        print("\n🔧 First-time Setup Wizard")
        print("-" * 30)
        
        # Check if .env exists
        if not os.path.exists('.env'):
            print("📝 Creating .env template file...")
            with open('.env', 'w', encoding='utf-8') as f:
                f.write("""# Kite Connect API Credentials
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
KITE_ACCESS_TOKEN=your_access_token_here

# Optional: InfluxDB Configuration
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_token_here
INFLUXDB_ORG=your_org_here
""")
            print("✅ .env file created. Please edit it with your API credentials.")
        
        print("\n📋 Next steps:")
        print("1. Edit .env file with your Kite Connect API credentials")
        print("2. Run diagnostics: python first_run_diagnostics.py")
        print("3. Run tests: python comprehensive_testing.py")
        print("4. Start platform: python main.py --action start")
    
    def run_interactive_mode(self):
        """Run in interactive mode."""
        if not self.platform_components:
            print("🔴 Cannot run - platform components not available")
            return
        
        try:
            # Initialize platform
            config_manager = self.platform_components['get_config_manager']()
            G6Platform = self.platform_components['G6Platform']
            
            self.platform = G6Platform(
                config_manager=config_manager,
                auto_start_monitoring=True
            )
            
            print("\n🎛️ G6 Platform Interactive Mode")
            print("Available commands:")
            print("  start  - Start data collection")
            print("  status - Show platform status")
            print("  stop   - Stop platform")
            print("  exit   - Exit application")
            
            while True:
                try:
                    command = input("\ng6> ").strip().lower()
                    
                    if command == 'start':
                        self.start_platform()
                    elif command == 'status':
                        self.show_status()
                    elif command == 'stop':
                        self.stop_platform()
                    elif command in ['exit', 'quit']:
                        break
                    elif command == 'help':
                        print("Available: start, status, stop, exit")
                    else:
                        print("Unknown command. Type 'help' for available commands.")
                        
                except (KeyboardInterrupt, EOFError):
                    break
            
        except Exception as e:
            print(f"🔴 Interactive mode error: {e}")
        finally:
            self.shutdown()
    
    def start_platform(self):
        """Start the platform."""
        if not self.platform:
            print("🔴 Platform not initialized")
            return
        
        print("🚀 Starting G6 Platform...")
        success = self.platform.start()
        
        if success:
            print("✅ Platform started successfully!")
            print("📊 Platform is now collecting data...")
            print("Press Ctrl+C to stop")
            try:
                while True:
                    import time
                    time.sleep(5)
                    status = self.platform.get_status()
                    print(f"Status: {status['status']}, Cycles: {status['cycles_completed']}", end='\r')
            except KeyboardInterrupt:
                print("\n🛑 Stopping platform...")
                self.platform.stop()
        else:
            print("🔴 Failed to start platform")
    
    def show_status(self):
        """Show platform status."""
        if not self.platform:
            print("🔴 Platform not initialized")
            return
            
        status = self.platform.get_status()
        print(f"\n📊 Platform Status:")
        print(f"  Status: {status['status']}")
        print(f"  Uptime: {status['uptime_seconds']:.0f} seconds")
        print(f"  Cycles: {status['cycles_completed']}")
        print(f"  Success Rate: {status['success_rate']:.1f}%")
    
    def stop_platform(self):
        """Stop the platform."""
        if self.platform:
            print("🛑 Stopping platform...")
            self.platform.stop()
            print("✅ Platform stopped")
        else:
            print("⚠️ Platform not running")
    
    def shutdown(self):
        """Shutdown gracefully."""
        if self.platform:
            self.platform.stop()

def main():
    """Main entry point with enhanced error handling."""
    import argparse
    
    parser = argparse.ArgumentParser(description="G6 Options Analytics Platform")
    parser.add_argument('--action', choices=['interactive', 'start', 'setup'], 
                       default='interactive', help='Action to perform')
    parser.add_argument('--version', action='version', version='G6 Platform 3.0')
    
    args = parser.parse_args()
    
    launcher = G6Launcher()
    
    # Initialize launcher
    if not launcher.initialize():
        print("\n🔴 Initialization failed!")
        print("🔧 Run the setup wizard: python main.py --action setup")
        return 1
    
    # Execute based on action
    if args.action == 'setup':
        launcher.run_setup_wizard()
    elif args.action == 'start':
        launcher.start_platform()
    else:
        launcher.run_interactive_mode()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())