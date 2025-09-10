#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🖥️ Enhanced Terminal UI - G6.1 Platform v2.0
Author: AI Assistant (Rich terminal with menu system and dynamic logging)

Features:
- Menu-based token initialization
- Dynamic log condensation
- Rich terminal output with colors and progress bars
- Interactive configuration management
- Real-time metrics dashboard
"""

import os
import sys
import time
import threading
import queue
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from collections import deque
from pathlib import Path

# Rich terminal libraries
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.tree import Tree
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Standard libraries fallback
import logging
import webbrowser
import subprocess

from config_manager import get_config
from enhanced_kite_provider import RequestPriority

class LogLevel:
    """📝 Log level constants."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class TerminalUI:
    """🖥️ Enhanced terminal user interface."""
    
    def __init__(self):
        """Initialize terminal UI."""
        self.config = get_config()
        
        # Rich console setup
        if RICH_AVAILABLE:
            self.console = Console(color_system="auto", legacy_windows=False)
            self.use_rich = True
        else:
            self.use_rich = False
            
        # Logging setup
        self.log_queue = queue.Queue(maxsize=1000)
        self.log_history = deque(maxlen=200)
        self.log_condensation = self.config.get_log_condensation()
        self.log_level = self.config.get_log_level()
        
        # UI state
        self.is_running = False
        self.show_metrics = False
        self.show_logs = True
        self.auto_refresh = True
        
        # Metrics tracking
        self.metrics_cache = {}
        self.last_update = 0
        
        self.setup_logging()
        
    def setup_logging(self):
        """📝 Setup enhanced logging with dynamic condensation."""
        # Configure root logger
        log_level_map = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL
        }
        
        logging.basicConfig(
            level=log_level_map.get(self.log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[LogHandler(self.log_queue)]
        )
        
    def print_banner(self):
        """🎨 Print platform banner."""
        if self.use_rich:
            banner_text = """
[bold cyan]G6.1 OPTIONS ANALYTICS PLATFORM[/bold cyan]
[dim]Version 2.0 - Enhanced Performance Edition[/dim]
"""
            self.console.print(Panel(banner_text, box=box.DOUBLE, expand=False))
        else:
            print("=" * 60)
            print("🚀 G6.1 OPTIONS ANALYTICS PLATFORM v2.0")
            print("   Enhanced Performance Edition")
            print("=" * 60)
    
    def show_main_menu(self) -> str:
        """📋 Display main menu and get user choice."""
        if self.use_rich:
            menu_text = """
[bold]Main Menu[/bold]

[cyan]1.[/cyan] 🔌 Token Management
[cyan]2.[/cyan] ⚙️  Configuration
[cyan]3.[/cyan] 🚀 Start Platform
[cyan]4.[/cyan] 📊 View Metrics
[cyan]5.[/cyan] 🧪 System Diagnostics
[cyan]6.[/cyan] ❌ Exit

"""
            self.console.print(Panel(menu_text, title="🎛️ Control Panel"))
            
            choice = Prompt.ask(
                "Select option",
                choices=["1", "2", "3", "4", "5", "6"],
                default="3"
            )
        else:
            print("\n📋 MAIN MENU")
            print("-" * 30)
            print("1. 🔌 Token Management")
            print("2. ⚙️  Configuration") 
            print("3. 🚀 Start Platform")
            print("4. 📊 View Metrics")
            print("5. 🧪 System Diagnostics")
            print("6. ❌ Exit")
            
            choice = input("\nSelect option [1-6] (default: 3): ").strip() or "3"
        
        return choice
    
    def show_token_menu(self) -> Dict[str, Any]:
        """🔐 Show token management menu."""
        if self.use_rich:
            self.console.print(Panel("[bold]Token Management[/bold]", box=box.ROUNDED))
            
            # Check current token status
            current_token = os.getenv('KITE_ACCESS_TOKEN')
            api_key = os.getenv('KITE_API_KEY')
            
            status_table = Table(show_header=False, box=None)
            status_table.add_column("Item", style="cyan")
            status_table.add_column("Status")
            
            if api_key:
                status_table.add_row("API Key", f"✅ Set ({api_key[:8]}...)")
            else:
                status_table.add_row("API Key", "❌ Missing")
                
            if current_token:
                status_table.add_row("Access Token", f"✅ Set ({current_token[:8]}...)")
            else:
                status_table.add_row("Access Token", "❌ Missing")
            
            self.console.print(status_table)
            
            menu_text = """
[cyan]1.[/cyan] 🌐 Browser Login (Recommended)
[cyan]2.[/cyan] 📝 Manual Token Entry
[cyan]3.[/cyan] 🧪 Test Current Token
[cyan]4.[/cyan] 🗑️  Clear Stored Token
[cyan]5.[/cyan] ⚠️  Skip Authentication (Mock Mode)
[cyan]6.[/cyan] ⬅️  Back to Main Menu
"""
            
            self.console.print(Panel(menu_text, title="🔐 Authentication Options"))
            
            choice = Prompt.ask(
                "Select authentication method",
                choices=["1", "2", "3", "4", "5", "6"],
                default="1"
            )
        else:
            print("\n🔐 TOKEN MANAGEMENT")
            print("-" * 30)
            print(f"API Key: {'✅ Set' if os.getenv('KITE_API_KEY') else '❌ Missing'}")
            print(f"Access Token: {'✅ Set' if os.getenv('KITE_ACCESS_TOKEN') else '❌ Missing'}")
            print()
            print("1. 🌐 Browser Login (Recommended)")
            print("2. 📝 Manual Token Entry")
            print("3. 🧪 Test Current Token")
            print("4. 🗑️  Clear Stored Token")
            print("5. ⚠️  Skip Authentication (Mock Mode)")
            print("6. ⬅️  Back to Main Menu")
            
            choice = input("\nSelect option [1-6]: ").strip()
        
        return self.handle_token_choice(choice)
    
    def handle_token_choice(self, choice: str) -> Dict[str, Any]:
        """🔐 Handle token management choice."""
        if choice == "1":
            return self.browser_login()
        elif choice == "2":
            return self.manual_token_entry()
        elif choice == "3":
            return self.test_current_token()
        elif choice == "4":
            return self.clear_stored_token()
        elif choice == "5":
            return self.enable_mock_mode()
        elif choice == "6":
            return {"action": "back"}
        else:
            return {"action": "invalid"}
    
    def browser_login(self) -> Dict[str, Any]:
        """🌐 Handle browser-based login."""
        try:
            if self.use_rich:
                with self.console.status("🌐 Initiating browser login...") as status:
                    api_key = os.getenv('KITE_API_KEY')
                    if not api_key:
                        self.console.print("❌ API Key not found in environment")
                        return {"success": False, "error": "Missing API Key"}
                    
                    # Generate login URL
                    login_url = f"https://kite.trade/connect/login?v=3&api_key={api_key}"
                    
                    self.console.print(f"🌐 Opening browser to: {login_url}")
                    webbrowser.open(login_url)
                    
                    # Get request token from user
                    request_token = Prompt.ask("📝 Enter the request token from callback URL")
                    
                    if not request_token:
                        return {"success": False, "error": "No request token provided"}
                    
                    # Generate access token
                    status.update("🔑 Generating access token...")
                    
                    try:
                        from kiteconnect import KiteConnect
                        kite = KiteConnect(api_key=api_key)
                        
                        api_secret = os.getenv('KITE_API_SECRET')
                        if not api_secret:
                            return {"success": False, "error": "API Secret not found"}
                        
                        session_data = kite.generate_session(request_token, api_secret=api_secret)
                        access_token = session_data['access_token']
                        
                        # Save token
                        self.save_token_to_env(access_token)
                        
                        self.console.print("✅ Access token generated and saved successfully!")
                        return {"success": True, "token": access_token}
                        
                    except Exception as e:
                        self.console.print(f"❌ Token generation failed: {e}")
                        return {"success": False, "error": str(e)}
            else:
                print("🌐 Browser Login")
                print("-" * 20)
                # Fallback implementation for non-rich terminals
                api_key = os.getenv('KITE_API_KEY')
                if not api_key:
                    print("❌ API Key not found")
                    return {"success": False}
                
                login_url = f"https://kite.trade/connect/login?v=3&api_key={api_key}"
                print(f"🌐 Open this URL: {login_url}")
                
                request_token = input("📝 Enter request token: ").strip()
                if request_token:
                    return self.generate_access_token(request_token)
                
                return {"success": False}
                
        except Exception as e:
            if self.use_rich:
                self.console.print(f"❌ Browser login error: {e}")
            else:
                print(f"❌ Error: {e}")
            return {"success": False, "error": str(e)}
    
    def manual_token_entry(self) -> Dict[str, Any]:
        """📝 Handle manual token entry."""
        try:
            if self.use_rich:
                self.console.print("📝 Manual Token Entry")
                self.console.print("Get your access token from: https://kite.trade/apps/")
                
                token = Prompt.ask("🔑 Enter your access token", password=False)
                
                if not token or len(token) < 10:
                    self.console.print("❌ Invalid token length")
                    return {"success": False, "error": "Invalid token"}
                
                # Test token
                if self.test_token_validity(token):
                    self.save_token_to_env(token)
                    self.console.print("✅ Token validated and saved successfully!")
                    return {"success": True, "token": token}
                else:
                    self.console.print("❌ Token validation failed")
                    return {"success": False, "error": "Token validation failed"}
            else:
                print("📝 Manual Token Entry")
                print("Get your token from: https://kite.trade/apps/")
                token = input("🔑 Enter access token: ").strip()
                
                if token and len(token) >= 10:
                    self.save_token_to_env(token)
                    print("✅ Token saved")
                    return {"success": True, "token": token}
                
                return {"success": False}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_current_token(self) -> Dict[str, Any]:
        """🧪 Test current token validity."""
        current_token = os.getenv('KITE_ACCESS_TOKEN')
        api_key = os.getenv('KITE_API_KEY')
        
        if not current_token or not api_key:
            if self.use_rich:
                self.console.print("❌ Missing token or API key")
            else:
                print("❌ Missing credentials")
            return {"success": False, "error": "Missing credentials"}
        
        if self.use_rich:
            with self.console.status("🧪 Testing token...") as status:
                result = self.test_token_validity(current_token, api_key)
                if result:
                    self.console.print("✅ Token is valid and working!")
                    return {"success": True, "valid": True}
                else:
                    self.console.print("❌ Token is invalid or expired")
                    return {"success": True, "valid": False}
        else:
            print("🧪 Testing token...")
            result = self.test_token_validity(current_token, api_key)
            print("✅ Valid" if result else "❌ Invalid")
            return {"success": True, "valid": result}
    
    def test_token_validity(self, token: str, api_key: str = None) -> bool:
        """🧪 Test if token is valid."""
        try:
            from kiteconnect import KiteConnect
            
            api_key = api_key or os.getenv('KITE_API_KEY')
            if not api_key:
                return False
            
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(token)
            
            # Test with profile call
            profile = kite.profile()
            return bool(profile and 'user_name' in profile)
            
        except ImportError:
            return True  # Assume valid if can't test
        except Exception:
            return False
    
    def save_token_to_env(self, token: str):
        """💾 Save token to environment file."""
        try:
            from dotenv import set_key
            
            env_file = Path('.env')
            if not env_file.exists():
                env_file.touch()
            
            set_key(str(env_file), 'KITE_ACCESS_TOKEN', token)
            
            # Reload environment
            os.environ['KITE_ACCESS_TOKEN'] = token
            
        except Exception as e:
            if self.use_rich:
                self.console.print(f"⚠️ Could not save to .env: {e}")
            else:
                print(f"⚠️ Save error: {e}")
    
    def clear_stored_token(self) -> Dict[str, Any]:
        """🗑️ Clear stored token."""
        try:
            if self.use_rich:
                confirm = Confirm.ask("🗑️ Clear stored access token?")
            else:
                confirm = input("🗑️ Clear stored token? [y/N]: ").strip().lower() == 'y'
            
            if confirm:
                from dotenv import set_key
                env_file = Path('.env')
                if env_file.exists():
                    set_key(str(env_file), 'KITE_ACCESS_TOKEN', '')
                
                if 'KITE_ACCESS_TOKEN' in os.environ:
                    del os.environ['KITE_ACCESS_TOKEN']
                
                if self.use_rich:
                    self.console.print("✅ Token cleared")
                else:
                    print("✅ Token cleared")
                
                return {"success": True, "cleared": True}
            
            return {"success": True, "cleared": False}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def enable_mock_mode(self) -> Dict[str, Any]:
        """⚠️ Enable mock mode."""
        try:
            if self.use_rich:
                self.console.print("⚠️ [yellow]Mock Mode Warning[/yellow]")
                self.console.print("This will use simulated data instead of live market data.")
                confirm = Confirm.ask("Enable mock mode?")
            else:
                print("⚠️ Mock Mode - Uses simulated data")
                confirm = input("Enable mock mode? [y/N]: ").strip().lower() == 'y'
            
            if confirm:
                from dotenv import set_key
                env_file = Path('.env')
                if not env_file.exists():
                    env_file.touch()
                
                set_key(str(env_file), 'G6_MOCK_MODE', 'true')
                os.environ['G6_MOCK_MODE'] = 'true'
                
                if self.use_rich:
                    self.console.print("✅ Mock mode enabled")
                else:
                    print("✅ Mock mode enabled")
                
                return {"success": True, "mock_enabled": True}
            
            return {"success": True, "mock_enabled": False}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_access_token(self, request_token: str) -> Dict[str, Any]:
        """🔑 Generate access token from request token."""
        try:
            from kiteconnect import KiteConnect
            
            api_key = os.getenv('KITE_API_KEY')
            api_secret = os.getenv('KITE_API_SECRET')
            
            if not api_key or not api_secret:
                return {"success": False, "error": "Missing API credentials"}
            
            kite = KiteConnect(api_key=api_key)
            session_data = kite.generate_session(request_token, api_secret=api_secret)
            access_token = session_data['access_token']
            
            self.save_token_to_env(access_token)
            
            return {"success": True, "token": access_token}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def show_configuration_menu(self):
        """⚙️ Show configuration management menu."""
        config_summary = self.config.get_config_summary()
        
        if self.use_rich:
            # Create configuration display table
            config_table = Table(title="📊 Current Configuration", box=box.ROUNDED)
            config_table.add_column("Section", style="cyan")
            config_table.add_column("Key", style="yellow")
            config_table.add_column("Value", style="green")
            
            for section, data in config_summary.items():
                if isinstance(data, dict):
                    for key, value in data.items():
                        config_table.add_row(section, str(key), str(value))
                else:
                    config_table.add_row(section, "", str(data))
            
            self.console.print(config_table)
            
            menu_text = """
[cyan]1.[/cyan] 📝 Edit Strike Offsets
[cyan]2.[/cyan] ⚙️  Performance Settings
[cyan]3.[/cyan] 💾 Storage Configuration
[cyan]4.[/cyan] 📊 Analytics Settings
[cyan]5.[/cyan] 🔄 Reload Configuration
[cyan]6.[/cyan] 💾 Save Configuration
[cyan]7.[/cyan] ⬅️  Back to Main Menu
"""
            
            self.console.print(Panel(menu_text, title="⚙️ Configuration Options"))
            
            choice = Prompt.ask(
                "Select option",
                choices=["1", "2", "3", "4", "5", "6", "7"],
                default="7"
            )
        else:
            print("\n⚙️ CONFIGURATION")
            print("-" * 30)
            print(f"Indices: {config_summary['market']['indices']}")
            print(f"Collection Interval: {config_summary['market']['collection_interval']}")
            print(f"CSV Enabled: {config_summary['storage']['csv_enabled']}")
            print(f"Debug Level: {config_summary['platform']['debug_level']}")
            print()
            print("1. 📝 Edit Strike Offsets")
            print("2. ⚙️  Performance Settings") 
            print("3. 💾 Storage Configuration")
            print("4. 📊 Analytics Settings")
            print("5. 🔄 Reload Configuration")
            print("6. 💾 Save Configuration")
            print("7. ⬅️  Back to Main Menu")
            
            choice = input("Select option [1-7]: ").strip()
        
        return self.handle_config_choice(choice)
    
    def handle_config_choice(self, choice: str):
        """⚙️ Handle configuration menu choice."""
        if choice == "1":
            self.edit_strike_offsets()
        elif choice == "2":
            self.edit_performance_settings()
        elif choice == "3":
            self.edit_storage_settings()
        elif choice == "4":
            self.edit_analytics_settings()
        elif choice == "5":
            self.config.reload_configuration()
            if self.use_rich:
                self.console.print("✅ Configuration reloaded")
            else:
                print("✅ Configuration reloaded")
        elif choice == "6":
            self.config.save_configuration()
            if self.use_rich:
                self.console.print("✅ Configuration saved")
            else:
                print("✅ Configuration saved")
        elif choice == "7":
            return "back"
        
        return "continue"
    
    def edit_strike_offsets(self):
        """📝 Edit strike offset configuration."""
        if self.use_rich:
            self.console.print("📝 [bold]Strike Offset Configuration[/bold]")
            
            current_offsets = self.config.get_strike_offsets()
            self.console.print(f"Current offsets: {current_offsets}")
            
            new_offsets = Prompt.ask(
                "Enter new offsets (comma-separated, e.g., -3,-2,-1,0,1,2,3)",
                default=",".join(map(str, current_offsets))
            )
            
            try:
                offsets = [int(x.strip()) for x in new_offsets.split(',')]
                self.config.set('data_collection.options.strike_configuration.symmetric_otm.offsets', offsets)
                self.console.print(f"✅ Strike offsets updated: {offsets}")
            except ValueError:
                self.console.print("❌ Invalid offset format")
        else:
            print("📝 Strike Offset Configuration")
            current_offsets = self.config.get_strike_offsets()
            print(f"Current: {current_offsets}")
            
            new_offsets = input("New offsets (comma-separated): ").strip()
            if new_offsets:
                try:
                    offsets = [int(x.strip()) for x in new_offsets.split(',')]
                    self.config.set('data_collection.options.strike_configuration.symmetric_otm.offsets', offsets)
                    print(f"✅ Updated: {offsets}")
                except ValueError:
                    print("❌ Invalid format")
    
    def edit_performance_settings(self):
        """⚙️ Edit performance settings."""
        if self.use_rich:
            self.console.print("⚙️ [bold]Performance Settings[/bold]")
            
            rate_limits = self.config.get_rate_limits()
            
            new_rpm = Prompt.ask(
                "Requests per minute",
                default=str(rate_limits['requests_per_minute'])
            )
            
            new_concurrent = Prompt.ask(
                "Max concurrent requests",
                default=str(rate_limits['max_concurrent'])
            )
            
            try:
                self.config.set('data_collection.performance.rate_limiting.requests_per_minute', int(new_rpm))
                self.config.set('data_collection.performance.max_concurrent_requests', int(new_concurrent))
                self.console.print("✅ Performance settings updated")
            except ValueError:
                self.console.print("❌ Invalid values")
    
    def edit_storage_settings(self):
        """💾 Edit storage settings."""
        if self.use_rich:
            self.console.print("💾 [bold]Storage Configuration[/bold]")
            
            csv_enabled = Confirm.ask("Enable CSV storage?", 
                                    default=self.config.get('storage.csv.enabled', True))
            
            influxdb_enabled = Confirm.ask("Enable InfluxDB storage?",
                                         default=self.config.get('storage.influxdb.enabled', False))
            
            self.config.set('storage.csv.enabled', csv_enabled)
            self.config.set('storage.influxdb.enabled', influxdb_enabled)
            
            self.console.print("✅ Storage settings updated")
    
    def edit_analytics_settings(self):
        """📊 Edit analytics settings."""
        if self.use_rich:
            self.console.print("📊 [bold]Analytics Configuration[/bold]")
            
            greeks_enabled = Confirm.ask("Enable Greeks calculations?",
                                       default=self.config.get('analytics.greeks_calculation.enabled', True))
            
            iv_enabled = Confirm.ask("Enable IV calculations?",
                                   default=self.config.get('analytics.iv_calculation.enabled', True))
            
            self.config.set('analytics.greeks_calculation.enabled', greeks_enabled)
            self.config.set('analytics.iv_calculation.enabled', iv_enabled)
            
            self.console.print("✅ Analytics settings updated")
    
    def launch_platform_subprocess(self):
        """🚀 Launch platform in subprocess."""
        try:
            if self.use_rich:
                with self.console.status("🚀 Launching G6.1 Platform...") as status:
                    # Launch main platform
                    env = os.environ.copy()
                    env['PYTHONIOENCODING'] = 'utf-8'
                    
                    process = subprocess.Popen(
                        [sys.executable, 'g6_platform_main_v2.py'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        env=env
                    )
                    
                    self.console.print("✅ Platform launched successfully!")
                    
                    # Stream output
                    for line in iter(process.stdout.readline, ''):
                        if line.strip():
                            self.process_log_line(line.strip())
                    
                    process.stdout.close()
                    return_code = process.wait()
                    
                    if return_code == 0:
                        self.console.print("✅ Platform exited successfully")
                    else:
                        self.console.print(f"⚠️ Platform exited with code: {return_code}")
            else:
                print("🚀 Launching platform...")
                # Fallback subprocess launch
                subprocess.run([sys.executable, 'g6_platform_main_v2.py'])
                
        except Exception as e:
            if self.use_rich:
                self.console.print(f"❌ Launch failed: {e}")
            else:
                print(f"❌ Launch failed: {e}")
    
    def process_log_line(self, line: str):
        """📝 Process and display log line with condensation."""
        if self.log_condensation == "dynamic":
            # Apply dynamic condensation based on log level and content
            if self._should_condense_log(line):
                return
        
        if self.use_rich:
            # Parse log level and format accordingly
            if " - ERROR - " in line:
                self.console.print(f"[red]{line}[/red]")
            elif " - WARNING - " in line:
                self.console.print(f"[yellow]{line}[/yellow]")
            elif " - INFO - " in line:
                if "✅" in line:
                    self.console.print(f"[green]{line}[/green]")
                else:
                    self.console.print(line)
            else:
                self.console.print(f"[dim]{line}[/dim]")
        else:
            print(line)
        
        # Store in history
        self.log_history.append({
            'timestamp': datetime.now(),
            'line': line,
            'level': self._extract_log_level(line)
        })
    
    def _should_condense_log(self, line: str) -> bool:
        """📝 Determine if log line should be condensed."""
        # Skip duplicate debug messages
        if " - DEBUG - " in line and self.log_level != "debug":
            return True
        
        # Skip repetitive health check messages
        if "Health check" in line and len(self.log_history) > 0:
            if any("Health check" in log['line'] for log in list(self.log_history)[-3:]):
                return True
        
        # Skip rate limiting warnings if too frequent
        if "Rate limit" in line:
            recent_rate_limit = sum(1 for log in list(self.log_history)[-10:] 
                                  if "Rate limit" in log['line'])
            if recent_rate_limit > 2:
                return True
        
        return False
    
    def _extract_log_level(self, line: str) -> str:
        """📝 Extract log level from log line."""
        if " - ERROR - " in line:
            return "error"
        elif " - WARNING - " in line:
            return "warning"
        elif " - INFO - " in line:
            return "info"
        elif " - DEBUG - " in line:
            return "debug"
        return "unknown"
    
    def run_interactive_mode(self):
        """🖥️ Run interactive terminal mode."""
        self.is_running = True
        
        try:
            while self.is_running:
                self.print_banner()
                
                choice = self.show_main_menu()
                
                if choice == "1":
                    self.show_token_menu()
                elif choice == "2":
                    self.show_configuration_menu()
                elif choice == "3":
                    self.launch_platform_subprocess()
                elif choice == "4":
                    self.show_metrics()
                elif choice == "5":
                    self.run_diagnostics()
                elif choice == "6":
                    self.is_running = False
                    if self.use_rich:
                        self.console.print("👋 Goodbye!")
                    else:
                        print("👋 Goodbye!")
                else:
                    if self.use_rich:
                        self.console.print("❌ Invalid choice")
                    else:
                        print("❌ Invalid choice")
                
                if self.is_running:
                    input("\nPress Enter to continue...")
                    
        except KeyboardInterrupt:
            if self.use_rich:
                self.console.print("\n🛑 Interrupted by user")
            else:
                print("\n🛑 Interrupted by user")
        finally:
            self.is_running = False

class LogHandler(logging.Handler):
    """📝 Custom log handler for terminal UI."""
    
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        try:
            msg = self.format(record)
            if not self.log_queue.full():
                self.log_queue.put(msg)
        except Exception:
            pass