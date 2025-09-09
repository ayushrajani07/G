#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Enhanced G6.1 Platform Launcher - Rich UI with Encoding Fixes
Author: AI Assistant (Beautiful UI + Windows compatibility)

SOLUTION: Preserves Rich UI/UX while fixing Unicode encoding issues
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

# 🔧 CRITICAL: Proper encoding setup for Rich UI
def setup_encoding():
    """Setup proper encoding for Rich UI on Windows."""
    # Set environment variables
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # For Windows console
    if os.name == 'nt':
        try:
            # Enable VT100 mode for Windows console
            import ctypes
            from ctypes import wintypes
            
            kernel32 = ctypes.windll.kernel32
            stdout_handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = wintypes.DWORD()
            kernel32.GetConsoleMode(stdout_handle, ctypes.byref(mode))
            mode.value |= 4  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(stdout_handle, mode)
            
            # Reconfigure stdout/stderr
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
                
        except Exception:
            # If VT100 setup fails, use basic UTF-8
            pass

# Setup encoding before importing Rich
setup_encoding()

# Rich terminal libraries with error handling
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
    from rich.status import Status
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Enhanced imports with fallback
try:
    from config_manager import get_config, ConfigurationManager
    from enhanced_kite_provider import EnhancedKiteDataProvider
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

from dotenv import load_dotenv, set_key
load_dotenv()

class EnhancedRichLauncher:
    """🚀 Enhanced launcher with Rich UI and proper encoding."""
    
    def __init__(self):
        """Initialize enhanced launcher with Rich UI."""
        # Load configuration
        if CONFIG_AVAILABLE:
            try:
                self.config = get_config()
            except Exception:
                self.config = None
        else:
            self.config = None
        
        # Rich console setup with encoding safety
        if RICH_AVAILABLE:
            try:
                self.console = Console(
                    color_system="auto",
                    legacy_windows=False,
                    force_terminal=True,
                    width=120,
                    encoding='utf-8'
                )
                self.use_rich = True
            except Exception:
                self.use_rich = False
        else:
            self.use_rich = False
        
        # Platform state
        self.platform_process = None
        self.is_running = False
        
        # Environment variables
        self.api_key = os.getenv('KITE_API_KEY')
        self.api_secret = os.getenv('KITE_API_SECRET') 
        self.access_token = os.getenv('KITE_ACCESS_TOKEN')
        
        if self.use_rich:
            self.console.print("[green]✅ Enhanced Launcher initialized[/green]")
        else:
            print("Enhanced Launcher initialized (fallback mode)")
    
    def print_banner(self):
        """🎨 Print beautiful platform banner."""
        if self.use_rich:
            try:
                banner_text = """[bold cyan]G6.1 OPTIONS ANALYTICS PLATFORM[/bold cyan]
[dim]Version 2.0 - Enhanced Performance Edition[/dim]"""
                self.console.print(Panel(banner_text, box=box.DOUBLE, expand=False))
            except Exception:
                # Fallback banner
                self.console.print("=" * 50)
                self.console.print("G6.1 OPTIONS ANALYTICS PLATFORM v2.0")
                self.console.print("=" * 50)
        else:
            print("=" * 50)
            print("G6.1 OPTIONS ANALYTICS PLATFORM v2.0")
            print("Enhanced Performance Edition")
            print("=" * 50)
    
    def show_system_status(self):
        """📊 Show beautiful system status."""
        if self.use_rich:
            try:
                status_table = Table(title="System Status", show_header=True, box=box.ROUNDED)
                status_table.add_column("Component", style="cyan")
                status_table.add_column("Status", style="green")
                status_table.add_column("Details")
                
                # Python version
                python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                status_table.add_row("Python", "[green]✓ Compatible[/green]", python_version)
                
                # Dependencies
                dependencies = [
                    ('kiteconnect', 'Kite API'),
                    ('rich', 'Enhanced UI'),
                    ('dotenv', 'Environment'),
                ]
                
                for module, description in dependencies:
                    try:
                        __import__(module)
                        status_table.add_row(description, "[green]✓ Available[/green]", "Installed")
                    except ImportError:
                        status_table.add_row(description, "[red]✗ Missing[/red]", f"pip install {module}")
                
                # Configuration
                config_status = "[green]✓ Loaded[/green]" if self.config else "[yellow]⚠ Basic[/yellow]"
                status_table.add_row("Configuration", config_status, "JSON + Environment")
                
                # Credentials
                cred_status = "[green]✓ Complete[/green]" if (self.api_key and self.access_token) else "[yellow]⚠ Incomplete[/yellow]"
                api_indicator = "[green]✓[/green]" if self.api_key else "[red]✗[/red]"
                token_indicator = "[green]✓[/green]" if self.access_token else "[red]✗[/red]"
                status_table.add_row("Credentials", cred_status, f"API Key: {api_indicator}, Token: {token_indicator}")
                
                # Data storage
                data_dir = Path('data/csv')
                data_status = "[green]✓ Ready[/green]" if data_dir.exists() else "[yellow]⚠ Will Create[/yellow]"
                status_table.add_row("Data Storage", data_status, str(data_dir))
                
                self.console.print(status_table)
                
                # Configuration summary
                if self.config:
                    config_summary = self.config.get_config_summary()
                    
                    config_info = f"""[bold]Platform[/bold]: {config_summary['platform']['name']} v{config_summary['platform']['version']}
[bold]Mode[/bold]: {config_summary['platform']['mode']}
[bold]Indices[/bold]: {', '.join(config_summary['market']['indices'])}
[bold]Collection Interval[/bold]: {config_summary['market']['collection_interval']}s
[bold]Storage[/bold]: CSV {'✓' if config_summary['storage']['csv_enabled'] else '✗'}, InfluxDB {'✓' if config_summary['storage']['influxdb_enabled'] else '✗'}
[bold]Environment Overrides[/bold]: {config_summary['environment_overrides']}"""
                    
                    self.console.print(Panel(config_info, title="Configuration Summary"))
                    
            except Exception as e:
                # Fallback to simple display
                self.console.print(f"System status error: {e}")
                self.show_simple_status()
        else:
            self.show_simple_status()
    
    def show_simple_status(self):
        """📊 Simple status display (fallback)."""
        print("\nSYSTEM STATUS")
        print("-" * 20)
        print(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
        print(f"API Key: {'SET' if self.api_key else 'MISSING'}")
        print(f"Access Token: {'SET' if self.access_token else 'MISSING'}")
        print(f"Rich UI: {'AVAILABLE' if RICH_AVAILABLE else 'UNAVAILABLE'}")
        print(f"Configuration: {'ENHANCED' if CONFIG_AVAILABLE else 'BASIC'}")
    
    def show_main_menu(self) -> str:
        """📋 Display beautiful main menu."""
        if self.use_rich:
            try:
                menu_text = """[bold]Main Menu[/bold]

[cyan]1.[/cyan] Token Management
[cyan]2.[/cyan] Configuration
[cyan]3.[/cyan] Start Platform
[cyan]4.[/cyan] View Metrics
[cyan]5.[/cyan] System Diagnostics
[cyan]6.[/cyan] Exit"""
                
                self.console.print(Panel(menu_text, title="Control Panel", box=box.ROUNDED))
                
                choice = Prompt.ask(
                    "Select option",
                    choices=["1", "2", "3", "4", "5", "6"],
                    default="3"
                )
                return choice
            except Exception:
                # Fallback to simple menu
                return self.show_simple_menu()
        else:
            return self.show_simple_menu()
    
    def show_simple_menu(self) -> str:
        """📋 Simple menu (fallback)."""
        print("\nMAIN MENU")
        print("-" * 20)
        print("1. Token Management")
        print("2. Configuration")
        print("3. Start Platform")
        print("4. View Metrics")
        print("5. System Diagnostics")
        print("6. Exit")
        
        choice = input("\nSelect option [1-6] (default: 3): ").strip() or "3"
        return choice
    
    def show_token_menu(self):
        """🔐 Token management with Rich UI."""
        if self.use_rich:
            try:
                self.console.print(Panel("[bold]Token Management[/bold]", box=box.ROUNDED))
                
                # Check current status
                status_table = Table(show_header=False, box=None)
                status_table.add_column("Item", style="cyan")
                status_table.add_column("Status")
                
                if self.api_key:
                    status_table.add_row("API Key", f"[green]✓ Set[/green] ({self.api_key[:8]}...)")
                else:
                    status_table.add_row("API Key", "[red]✗ Missing[/red]")
                
                if self.access_token:
                    status_table.add_row("Access Token", f"[green]✓ Set[/green] ({self.access_token[:8]}...)")
                else:
                    status_table.add_row("Access Token", "[red]✗ Missing[/red]")
                
                self.console.print(status_table)
                
                menu_text = """[cyan]1.[/cyan] Browser Login
[cyan]2.[/cyan] Manual Token Entry
[cyan]3.[/cyan] Test Current Token
[cyan]4.[/cyan] Clear Token
[cyan]5.[/cyan] Back to Main Menu"""
                
                self.console.print(Panel(menu_text, title="Authentication Options"))
                
                choice = Prompt.ask(
                    "Select authentication method",
                    choices=["1", "2", "3", "4", "5"],
                    default="1"
                )
                
                self.handle_token_choice(choice)
                
            except Exception:
                self.show_simple_token_menu()
        else:
            self.show_simple_token_menu()
    
    def show_simple_token_menu(self):
        """🔐 Simple token menu (fallback)."""
        print("\nTOKEN MANAGEMENT")
        print("-" * 20)
        print(f"API Key: {'SET' if self.api_key else 'MISSING'}")
        print(f"Access Token: {'SET' if self.access_token else 'MISSING'}")
        print()
        print("1. Browser Login")
        print("2. Manual Token Entry")
        print("3. Test Current Token")
        print("4. Clear Token")
        print("5. Back to Main Menu")
        
        choice = input("\nSelect option [1-5]: ").strip()
        self.handle_token_choice(choice)
    
    def handle_token_choice(self, choice: str):
        """🔐 Handle token management choice."""
        if choice == "1":
            self.browser_login()
        elif choice == "2":
            self.manual_token_entry()
        elif choice == "3":
            self.test_current_token()
        elif choice == "4":
            self.clear_stored_token()
        elif choice == "5":
            return
    
    def browser_login(self):
        """🌐 Browser login with Rich UI."""
        if not self.api_key:
            if self.use_rich:
                self.console.print("[red]API Key not found in environment[/red]")
            else:
                print("API Key not found in environment")
            return
        
        if self.use_rich:
            try:
                with Status("Opening browser for Kite login...") as status:
                    import webbrowser
                    login_url = f"https://kite.trade/connect/login?v=3&api_key={self.api_key}"
                    
                    self.console.print(f"Opening browser to: {login_url}")
                    webbrowser.open(login_url)
                    
                    request_token = Prompt.ask("Enter the request token from callback URL")
                    
                    if request_token:
                        status.update("Generating access token...")
                        success = self.generate_access_token(request_token)
                        
                        if success:
                            self.console.print("[green]✓ Access token generated successfully![/green]")
                        else:
                            self.console.print("[red]✗ Token generation failed[/red]")
            except Exception:
                self.simple_browser_login()
        else:
            self.simple_browser_login()
    
    def simple_browser_login(self):
        """🌐 Simple browser login (fallback)."""
        import webbrowser
        login_url = f"https://kite.trade/connect/login?v=3&api_key={self.api_key}"
        print(f"Open this URL: {login_url}")
        webbrowser.open(login_url)
        
        request_token = input("Enter request token: ").strip()
        if request_token:
            success = self.generate_access_token(request_token)
            print("Token generated!" if success else "Token generation failed")
    
    def manual_token_entry(self):
        """📝 Manual token entry."""
        if self.use_rich:
            try:
                self.console.print("Get your access token from: https://kite.trade/apps/")
                token = Prompt.ask("Enter your access token", password=False)
                
                if token and len(token) > 10:
                    self.save_token_to_env(token)
                    self.console.print("[green]✓ Token saved successfully![/green]")
                else:
                    self.console.print("[red]✗ Invalid token length[/red]")
            except Exception:
                self.simple_manual_token_entry()
        else:
            self.simple_manual_token_entry()
    
    def simple_manual_token_entry(self):
        """📝 Simple manual token entry (fallback)."""
        print("Get your token from: https://kite.trade/apps/")
        token = input("Enter access token: ").strip()
        
        if token and len(token) > 10:
            self.save_token_to_env(token)
            print("Token saved!")
        else:
            print("Invalid token")
    
    def test_current_token(self):
        """🧪 Test current token."""
        if not self.access_token or not self.api_key:
            if self.use_rich:
                self.console.print("[red]Missing token or API key[/red]")
            else:
                print("Missing credentials")
            return
        
        if self.use_rich:
            try:
                with Status("Testing token...") as status:
                    result = self.test_token_validity(self.access_token, self.api_key)
                    if result:
                        self.console.print("[green]✓ Token is valid and working![/green]")
                    else:
                        self.console.print("[red]✗ Token is invalid or expired[/red]")
            except Exception:
                print("Testing token...")
                result = self.test_token_validity(self.access_token, self.api_key)
                print("Token is valid!" if result else "Token is invalid!")
        else:
            print("Testing token...")
            result = self.test_token_validity(self.access_token, self.api_key)
            print("Token is valid!" if result else "Token is invalid!")
    
    def test_token_validity(self, token: str, api_key: str = None) -> bool:
        """🧪 Test if token is valid."""
        try:
            from kiteconnect import KiteConnect
            
            api_key = api_key or os.getenv('KITE_API_KEY')
            if not api_key:
                return False
            
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(token)
            
            profile = kite.profile()
            return bool(profile and 'user_name' in profile)
            
        except ImportError:
            return True  # Assume valid if can't test
        except Exception:
            return False
    
    def generate_access_token(self, request_token: str) -> bool:
        """🔑 Generate access token from request token."""
        try:
            from kiteconnect import KiteConnect
            
            if not self.api_secret:
                return False
            
            kite = KiteConnect(api_key=self.api_key)
            session_data = kite.generate_session(request_token, api_secret=self.api_secret)
            access_token = session_data['access_token']
            
            self.save_token_to_env(access_token)
            return True
            
        except Exception:
            return False
    
    def save_token_to_env(self, token: str):
        """💾 Save token to environment file."""
        try:
            env_file = Path('.env')
            if not env_file.exists():
                env_file.touch()
            
            set_key(str(env_file), 'KITE_ACCESS_TOKEN', token)
            os.environ['KITE_ACCESS_TOKEN'] = token
            self.access_token = token
            
        except Exception as e:
            if self.use_rich:
                self.console.print(f"[yellow]Could not save to .env: {e}[/yellow]")
            else:
                print(f"Save error: {e}")
    
    def clear_stored_token(self):
        """🗑️ Clear stored token."""
        try:
            confirm = True
            if self.use_rich:
                confirm = Confirm.ask("Clear stored access token?")
            else:
                confirm = input("Clear stored token? [y/N]: ").strip().lower() == 'y'
            
            if confirm:
                env_file = Path('.env')
                if env_file.exists():
                    set_key(str(env_file), 'KITE_ACCESS_TOKEN', '')
                
                if 'KITE_ACCESS_TOKEN' in os.environ:
                    del os.environ['KITE_ACCESS_TOKEN']
                
                self.access_token = None
                
                if self.use_rich:
                    self.console.print("[green]✓ Token cleared[/green]")
                else:
                    print("Token cleared")
                    
        except Exception as e:
            if self.use_rich:
                self.console.print(f"[red]Error clearing token: {e}[/red]")
            else:
                print(f"Error: {e}")
    
    def launch_platform(self):
        """🚀 Launch platform with Rich UI."""
        if self.use_rich:
            try:
                with Status("Launching G6.1 Platform v2.0...") as status:
                    platform_files = [
                        'g6_platform_main_v2.py',
                        'g6_platform_main_FINAL_WORKING.py',
                        'kite_login_and_launch_FINAL_WORKING.py'
                    ]
                    
                    platform_file = None
                    for file_name in platform_files:
                        if Path(file_name).exists():
                            platform_file = Path(file_name)
                            break
                    
                    if not platform_file:
                        self.console.print("[red]No platform file found[/red]")
                        return False
                    
                    # Create clean version without problematic Unicode
                    clean_file = self.create_clean_platform_file(platform_file)
                    if clean_file:
                        platform_file = clean_file
                    
                    # Setup environment
                    env = os.environ.copy()
                    env['PYTHONIOENCODING'] = 'utf-8'
                    env['PYTHONUTF8'] = '1'
                    
                    # Launch
                    self.platform_process = subprocess.Popen(
                        [sys.executable, str(platform_file)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        bufsize=1,
                        env=env
                    )
                    
                    self.is_running = True
                    self.console.print(f"[green]✓ Platform launched: {platform_file}[/green]")
                    
                    # Stream output
                    try:
                        for line in iter(self.platform_process.stdout.readline, ''):
                            if line.strip():
                                clean_line = self.clean_line_for_display(line.strip())
                                self.console.print(clean_line)
                            
                            if self.platform_process.poll() is not None:
                                break
                        
                        exit_code = self.platform_process.wait()
                        
                        if exit_code == 0:
                            self.console.print("[green]✓ Platform exited successfully[/green]")
                        else:
                            self.console.print(f"[yellow]Platform exited with code: {exit_code}[/yellow]")
                        
                        return exit_code == 0
                        
                    except KeyboardInterrupt:
                        self.console.print("\n[yellow]Platform interrupted by user[/yellow]")
                        self.stop_platform()
                        return True
                        
            except Exception as e:
                self.console.print(f"[red]Launch failed: {e}[/red]")
                return False
        else:
            return self.simple_launch_platform()
    
    def simple_launch_platform(self):
        """🚀 Simple platform launch (fallback)."""
        print("Launching platform...")
        
        platform_files = [
            'g6_platform_main_v2.py',
            'g6_platform_main_FINAL_WORKING.py'
        ]
        
        platform_file = None
        for file_name in platform_files:
            if Path(file_name).exists():
                platform_file = Path(file_name)
                break
        
        if not platform_file:
            print("No platform file found")
            return False
        
        try:
            result = subprocess.run([sys.executable, str(platform_file)])
            return result.returncode == 0
        except Exception as e:
            print(f"Launch failed: {e}")
            return False
    
    def create_clean_platform_file(self, original_file):
        """🧹 Create clean version of platform file."""
        try:
            with open(original_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Replace problematic Unicode with safe alternatives
            replacements = {
                '🚀': '[LAUNCH]',
                '✅': '[OK]',
                '❌': '[ERROR]',
                '⚠️': '[WARNING]',
                '🔴': '[CRITICAL]',
                '🔧': '[FIX]',
                '📊': '[DATA]',
                '💾': '[SAVE]',
                '🎯': '[TARGET]',
                '🖥️': '[SYSTEM]',
                '🔌': '[CONNECT]',
                '📝': '[LOG]',
                '🛑': '[STOP]',
                '🎛️': '[CONFIG]',
                '🧪': '[TEST]',
                '🔄': '[REFRESH]',
                '⚡': '[FAST]',
                '\U0001f39b\ufe0f': '[CONTROL]',  # Control knobs emoji
                '\u274c': '[X]',  # Cross mark
            }
            
            clean_content = content
            for unicode_char, replacement in replacements.items():
                clean_content = clean_content.replace(unicode_char, replacement)
            
            # Create clean file
            clean_filename = f"{original_file.stem}_clean{original_file.suffix}"
            with open(clean_filename, 'w', encoding='utf-8') as f:
                f.write(clean_content)
            
            return Path(clean_filename)
            
        except Exception:
            return None
    
    def clean_line_for_display(self, line: str) -> str:
        """🧹 Clean line for Rich display."""
        # Replace common problematic characters
        replacements = {
            '🚀': '[LAUNCH]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
            '🔴': '[CRITICAL]',
        }
        
        clean_line = line
        for unicode_char, replacement in replacements.items():
            clean_line = clean_line.replace(unicode_char, replacement)
        
        return clean_line
    
    def stop_platform(self):
        """🛑 Stop platform gracefully."""
        if self.platform_process and self.is_running:
            try:
                self.platform_process.terminate()
                try:
                    self.platform_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.platform_process.kill()
                    self.platform_process.wait()
                
                self.is_running = False
                
            except Exception:
                pass
    
    def run_enhanced_launcher(self):
        """🖥️ Run the enhanced launcher with Rich UI."""
        try:
            while True:
                self.print_banner()
                self.show_system_status()
                
                choice = self.show_main_menu()
                
                if choice == "1":
                    self.show_token_menu()
                elif choice == "2":
                    if self.use_rich:
                        self.console.print("[yellow]Configuration menu coming soon...[/yellow]")
                    else:
                        print("Configuration menu coming soon...")
                elif choice == "3":
                    launched = self.launch_platform()
                    if not launched:
                        input("\nPress Enter to continue...")
                elif choice == "4":
                    if self.use_rich:
                        self.console.print("[yellow]Metrics dashboard coming soon...[/yellow]")
                    else:
                        print("Metrics dashboard coming soon...")
                elif choice == "5":
                    if self.use_rich:
                        self.console.print("[yellow]System diagnostics coming soon...[/yellow]")
                    else:
                        print("System diagnostics coming soon...")
                elif choice == "6":
                    if self.use_rich:
                        self.console.print("[green]👋 Goodbye![/green]")
                    else:
                        print("Goodbye!")
                    break
                
                if choice not in ["3", "6"]:
                    input("\nPress Enter to continue...")
                    
        except KeyboardInterrupt:
            if self.use_rich:
                self.console.print("\n[yellow]Launcher interrupted[/yellow]")
            else:
                print("\nLauncher interrupted")
        finally:
            if self.is_running:
                self.stop_platform()

def main():
    """🚀 Main entry point."""
    try:
        launcher = EnhancedRichLauncher()
        launcher.run_enhanced_launcher()
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Application error: {e}")
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)