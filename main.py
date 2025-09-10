#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 G6 Platform Main Entry Point - v3.0
Unified application launcher with clean architecture.

This is the single entry point that replaces the scattered launcher files:
- ultimate_storage_launcher.py
- g6_platform_main_FINAL_WORKING.py  
- main_application_complete.py
- All other launcher variants

Features:
- Clean separation of UI from business logic
- Comprehensive error handling and recovery
- Signal handling for graceful shutdown
- Rich terminal interface with live metrics
- Configuration management and validation
- Health monitoring integration
"""

import os
import sys
import signal
import logging
import argparse
from datetime import datetime
from typing import Optional

# Add package to path for development
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import G6 platform components
try:
    from g6_platform import G6Platform, ConfigurationManager, get_version, get_package_info
    from g6_platform.config.manager import get_config_manager
    from g6_platform.utils.path_resolver import PathResolver
    from g6_platform.ui.terminal_interface import TerminalInterface
except ImportError as e:
    print(f"🔴 Failed to import G6 platform components: {e}")
    print("🔧 Please ensure the platform is properly installed")
    sys.exit(1)

# Rich UI imports with fallback
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.columns import Columns
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

logger = logging.getLogger(__name__)

class G6Launcher:
    """
    🚀 Main application launcher for the G6 Platform.
    
    Provides a unified entry point with proper separation of concerns,
    comprehensive error handling, and rich user interface.
    """
    
    def __init__(self):
        """Initialize the G6 launcher."""
        self.console = Console() if RICH_AVAILABLE else None
        self.platform: Optional[G6Platform] = None
        self.config_manager: Optional[ConfigurationManager] = None
        self.path_resolver: Optional[PathResolver] = None
        self.terminal_ui: Optional[TerminalInterface] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.shutdown()
        sys.exit(0)
    
    def display_banner(self):
        """Display application banner."""
        package_info = get_package_info()
        version = get_version()
        
        if self.console:
            # Rich banner
            banner_text = Text()
            banner_text.append("🚀 G6 Options Analytics Platform\n", style="bold blue")
            banner_text.append(f"Version {version}\n", style="green")
            banner_text.append(f"Professional Options Trading Platform for Indian Markets\n", style="white")
            banner_text.append(f"Supported Indices: {', '.join(package_info['supported_instruments'])}", style="yellow")
            
            panel = Panel(
                banner_text,
                title="G6 Platform",
                title_align="center",
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            # Fallback text banner
            print("=" * 60)
            print("🚀 G6 Options Analytics Platform")
            print(f"Version {version}")
            print("Professional Options Trading Platform for Indian Markets")
            print(f"Supported Indices: {', '.join(package_info['supported_instruments'])}")
            print("=" * 60)
    
    def setup_logging(self, log_level: str = "INFO", log_file: str = None):
        """Setup logging configuration."""
        # Create logs directory
        logs_dir = self.path_resolver.get_log_path() if self.path_resolver else "logs"
        os.makedirs(logs_dir, exist_ok=True)
        
        # Configure logging
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Setup root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Add file handler if specified
        if log_file:
            file_handler = logging.FileHandler(
                os.path.join(logs_dir, log_file),
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(log_format))
            logging.getLogger().addHandler(file_handler)
        
        logger.info("✅ Logging configured")
    
    def initialize_components(self, config_path: str = None):
        """Initialize all platform components."""
        try:
            # Initialize path resolver
            self.path_resolver = PathResolver()
            logger.info("✅ Path resolver initialized")
            
            # Initialize configuration manager
            self.config_manager = get_config_manager()
            logger.info("✅ Configuration manager initialized")
            
            # Initialize terminal UI
            if RICH_AVAILABLE:
                from g6_platform.ui.terminal_interface import TerminalInterface
                self.terminal_ui = TerminalInterface(
                    config_manager=self.config_manager
                )
                logger.info("✅ Terminal UI initialized")
            
            # Initialize main platform
            self.platform = G6Platform(
                config_manager=self.config_manager,
                auto_start_monitoring=True
            )
            logger.info("✅ G6 Platform initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"🔴 Component initialization failed: {e}")
            return False
    
    def show_main_menu(self) -> str:
        """Show main menu and get user choice."""
        if self.console:
            # Rich menu
            menu_options = [
                "[1] 🚀 Start Data Collection Platform",
                "[2] 📊 View Platform Status",
                "[3] ⚙️ Configuration Management", 
                "[4] 📈 Live Metrics Dashboard",
                "[5] 🔧 Platform Diagnostics",
                "[6] 📋 Export Data",
                "[7] 🛑 Stop Platform",
                "[8] ❌ Exit"
            ]
            
            menu_text = "\n".join(menu_options)
            menu_panel = Panel(
                menu_text,
                title="Main Menu",
                title_align="center"
            )
            
            self.console.print(menu_panel)
        else:
            # Fallback text menu
            print("\n" + "=" * 50)
            print("Main Menu")
            print("=" * 50)
            print("[1] 🚀 Start Data Collection Platform")
            print("[2] 📊 View Platform Status")
            print("[3] ⚙️ Configuration Management")
            print("[4] 📈 Live Metrics Dashboard")
            print("[5] 🔧 Platform Diagnostics")
            print("[6] 📋 Export Data")
            print("[7] 🛑 Stop Platform")
            print("[8] ❌ Exit")
            print("=" * 50)
        
        return input("\nSelect option [1-8]: ").strip()
    
    def handle_menu_choice(self, choice: str) -> bool:
        """Handle menu choice and execute corresponding action."""
        try:
            if choice == "1":
                return self.start_data_collection()
            elif choice == "2":
                return self.show_platform_status()
            elif choice == "3":
                return self.configuration_management()
            elif choice == "4":
                return self.show_live_metrics()
            elif choice == "5":
                return self.platform_diagnostics()
            elif choice == "6":
                return self.export_data()
            elif choice == "7":
                return self.stop_platform()
            elif choice == "8":
                return self.exit_application()
            else:
                if self.console:
                    self.console.print("❌ Invalid choice. Please select 1-8.", style="red")
                else:
                    print("❌ Invalid choice. Please select 1-8.")
                return True
                
        except Exception as e:
            logger.error(f"🔴 Error handling menu choice {choice}: {e}")
            if self.console:
                self.console.print(f"🔴 Error: {e}", style="red")
            else:
                print(f"🔴 Error: {e}")
            return True
    
    def start_data_collection(self) -> bool:
        """Start the data collection platform."""
        try:
            if not self.platform:
                print("🔴 Platform not initialized")
                return True
            
            if self.console:
                self.console.print("🚀 Starting data collection platform...", style="green")
            else:
                print("🚀 Starting data collection platform...")
            
            # Start the platform
            success = self.platform.start()
            
            if success:
                if self.console:
                    self.console.print("✅ Platform started successfully!", style="green")
                else:
                    print("✅ Platform started successfully!")
                
                # Show live dashboard if terminal UI is available
                if self.terminal_ui:
                    self.terminal_ui.show_live_dashboard(self.platform)
                else:
                    print("📊 Platform running... Press Ctrl+C to stop")
                    try:
                        while True:
                            status = self.platform.get_status()
                            print(f"Status: {status['status']}, Cycles: {status['cycles_completed']}", end='\r')
                            import time
                            time.sleep(5)
                    except KeyboardInterrupt:
                        print("\n🛑 Stopping platform...")
                        self.platform.stop()
            else:
                if self.console:
                    self.console.print("🔴 Failed to start platform", style="red")
                else:
                    print("🔴 Failed to start platform")
            
            return True
            
        except Exception as e:
            logger.error(f"🔴 Failed to start data collection: {e}")
            return True
    
    def show_platform_status(self) -> bool:
        """Show current platform status."""
        try:
            if not self.platform:
                print("🔴 Platform not initialized")
                return True
            
            status = self.platform.get_status()
            health = self.platform.get_health()
            
            if self.console:
                # Rich status display
                status_text = Text()
                status_text.append(f"Status: {status['status']}\n", style="green" if status['status'] == 'running' else "yellow")
                status_text.append(f"Uptime: {status['uptime_seconds']:.0f} seconds\n", style="white")
                status_text.append(f"Cycles Completed: {status['cycles_completed']}\n", style="blue")
                status_text.append(f"Success Rate: {status['success_rate']:.1f}%\n", style="green")
                status_text.append(f"Options Processed: {status['total_options_processed']}\n", style="cyan")
                status_text.append(f"Average Cycle Time: {status['average_cycle_time']:.2f}s\n", style="magenta")
                
                panel = Panel(status_text, title="Platform Status", title_align="center")
                self.console.print(panel)
            else:
                # Fallback text display
                print("\n" + "=" * 40)
                print("Platform Status")
                print("=" * 40)
                print(f"Status: {status['status']}")
                print(f"Uptime: {status['uptime_seconds']:.0f} seconds")
                print(f"Cycles Completed: {status['cycles_completed']}")
                print(f"Success Rate: {status['success_rate']:.1f}%")
                print(f"Options Processed: {status['total_options_processed']}")
                print(f"Average Cycle Time: {status['average_cycle_time']:.2f}s")
                print("=" * 40)
            
            input("\nPress Enter to continue...")
            return True
            
        except Exception as e:
            logger.error(f"🔴 Failed to show platform status: {e}")
            return True
    
    def configuration_management(self) -> bool:
        """Handle configuration management."""
        print("⚙️ Configuration Management")
        print("[1] View Current Configuration")
        print("[2] Reload Configuration")
        print("[3] Validate Configuration")
        print("[4] Back to Main Menu")
        
        choice = input("Select option [1-4]: ").strip()
        
        if choice == "1":
            config = self.config_manager.get_all()
            print(f"\nCurrent Configuration:")
            print(f"Platform: {config.get('platform', {}).get('name', 'Unknown')}")
            print(f"Indices: {config.get('market', {}).get('indices', [])}")
            print(f"Collection Interval: {config.get('market', {}).get('collection_interval', 0)}s")
        elif choice == "2":
            success = self.config_manager.reload()
            print(f"✅ Configuration reloaded" if success else "🔴 Reload failed")
        elif choice == "3":
            errors = self.config_manager.get_validation_errors()
            if errors:
                print("🔴 Configuration validation errors:")
                for error in errors:
                    print(f"  - {error.field}: {error.message}")
            else:
                print("✅ Configuration is valid")
        elif choice == "4":
            return True
        
        input("\nPress Enter to continue...")
        return True
    
    def show_live_metrics(self) -> bool:
        """Show live metrics dashboard."""
        if self.terminal_ui and self.platform:
            self.terminal_ui.show_metrics_dashboard(self.platform)
        else:
            print("📈 Live metrics not available (requires Rich terminal)")
            input("Press Enter to continue...")
        return True
    
    def platform_diagnostics(self) -> bool:
        """Show platform diagnostics."""
        print("🔧 Platform Diagnostics")
        
        if self.platform:
            health = self.platform.get_health()
            print(f"Health Status: {health.get('status', 'unknown')}")
            
            if 'checks' in health:
                print("\nComponent Health:")
                for name, check in health['checks'].items():
                    status = check.get('status', 'unknown')
                    print(f"  - {name}: {status}")
        
        input("\nPress Enter to continue...")
        return True
    
    def export_data(self) -> bool:
        """Handle data export."""
        print("📋 Data Export")
        print("[1] Export CSV Data")
        print("[2] Export Metrics")
        print("[3] Export Configuration")
        print("[4] Back to Main Menu")
        
        choice = input("Select option [1-4]: ").strip()
        
        if choice == "4":
            return True
        else:
            print(f"Export option {choice} not implemented yet")
            input("Press Enter to continue...")
        
        return True
    
    def stop_platform(self) -> bool:
        """Stop the platform."""
        if self.platform:
            print("🛑 Stopping platform...")
            self.platform.stop()
            print("✅ Platform stopped")
        else:
            print("⚠️ Platform not running")
        
        input("Press Enter to continue...")
        return True
    
    def exit_application(self) -> bool:
        """Exit the application."""
        print("👋 Goodbye!")
        return False
    
    def run_interactive_mode(self):
        """Run the launcher in interactive mode."""
        self.display_banner()
        
        # Initialize components
        if not self.initialize_components():
            print("🔴 Failed to initialize platform components")
            return
        
        # Main menu loop
        try:
            while True:
                choice = self.show_main_menu()
                if not self.handle_menu_choice(choice):
                    break
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        finally:
            self.shutdown()
    
    def run_direct_mode(self, action: str):
        """Run the launcher in direct mode (non-interactive)."""
        # Initialize components
        if not self.initialize_components():
            print("🔴 Failed to initialize platform components")
            return
        
        try:
            if action == "start":
                print("🚀 Starting platform in direct mode...")
                if self.platform.start():
                    print("✅ Platform started successfully")
                    # Keep running until interrupted
                    try:
                        while True:
                            import time
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\n🛑 Stopping platform...")
                        self.platform.stop()
                else:
                    print("🔴 Failed to start platform")
            elif action == "status":
                if self.platform:
                    status = self.platform.get_status()
                    print(f"Platform Status: {status['status']}")
                    print(f"Cycles: {status['cycles_completed']}")
                    print(f"Success Rate: {status['success_rate']:.1f}%")
            else:
                print(f"🔴 Unknown action: {action}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown all platform components gracefully."""
        try:
            if self.platform:
                self.platform.stop()
                logger.info("✅ Platform stopped")
            
            if self.terminal_ui:
                self.terminal_ui.cleanup()
                logger.info("✅ Terminal UI cleaned up")
            
        except Exception as e:
            logger.error(f"🔴 Error during shutdown: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="G6 Options Analytics Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--action",
        choices=["start", "status", "interactive"],
        default="interactive",
        help="Action to perform (default: interactive)"
    )
    
    parser.add_argument(
        "--config",
        help="Configuration file path"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        help="Log file path (optional)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"G6 Platform {get_version()}"
    )
    
    args = parser.parse_args()
    
    # Create launcher
    launcher = G6Launcher()
    
    # Setup logging
    launcher.setup_logging(args.log_level, args.log_file)
    
    # Run in appropriate mode
    if args.action == "interactive":
        launcher.run_interactive_mode()
    else:
        launcher.run_direct_mode(args.action)

if __name__ == "__main__":
    main()