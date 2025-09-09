#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Fixed Non-Blocking Rich Launcher - G6.1 Platform v2.0
Author: AI Assistant (Fixed datetime error + metrics + proper monitoring)

FIXES:
1. ✅ Fixed datetime import error
2. ✅ Added working metrics dashboard  
3. ✅ Better process monitoring
4. ✅ Real data collection indicators
5. ✅ No more hanging on menu options
"""

import os
import sys
import time
import signal
import subprocess
import threading
import json
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime  # ✅ FIXED: Added missing import

# Setup encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Enable VT100 on Windows
if os.name == 'nt':
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        stdout_handle = kernel32.GetStdHandle(-11)
        mode = wintypes.DWORD()
        kernel32.GetConsoleMode(stdout_handle, ctypes.byref(mode))
        mode.value |= 4
        kernel32.SetConsoleMode(stdout_handle, mode)
    except:
        pass

# Rich imports with fallback
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.live import Live
    from rich.text import Text
    from rich import box
    from rich.status import Status
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    from rich.layout import Layout
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from dotenv import load_dotenv, set_key
load_dotenv()

class FixedNonBlockingLauncher:
    """🚀 Fixed launcher with proper monitoring and metrics."""
    
    def __init__(self):
        """Initialize fixed launcher."""
        # Rich console setup
        if RICH_AVAILABLE:
            try:
                self.console = Console(
                    color_system="auto",
                    force_terminal=True,
                    width=120
                )
                self.use_rich = True
                self.console.print("[green]✅ Enhanced Launcher initialized[/green]")
            except Exception:
                self.use_rich = False
                print("Enhanced Launcher initialized (fallback mode)")
        else:
            self.use_rich = False
            print("Enhanced Launcher initialized (basic mode)")
        
        # Platform state
        self.platform_process = None
        self.is_running = False
        self.output_queue = Queue()
        self.output_thread = None
        self.last_activity = None
        
        # Metrics tracking
        self.platform_metrics = {
            'start_time': None,
            'collections': 0,
            'errors': 0,
            'api_calls': 0,
            'last_collection': None,
            'status': 'stopped'
        }
        
        # Environment
        self.api_key = os.getenv('KITE_API_KEY')
        self.access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    def print_banner(self):
        """🎨 Print beautiful banner."""
        if self.use_rich:
            banner = """[bold cyan]G6.1 OPTIONS ANALYTICS PLATFORM[/bold cyan]
[dim]Version 2.0 - Enhanced Performance Edition[/dim]"""
            self.console.print(Panel(banner, box=box.DOUBLE))
        else:
            print("=" * 50)
            print("G6.1 OPTIONS ANALYTICS PLATFORM v2.0")
            print("Enhanced Performance Edition")
            print("=" * 50)
    
    def show_system_status(self):
        """📊 Show system status with real-time updates."""
        if self.use_rich:
            try:
                table = Table(title="[bold]System Status[/bold]", box=box.ROUNDED)
                table.add_column("Component", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Details")
                
                # Add status rows
                python_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
                table.add_row("Python", "[green]✓ Ready[/green]", python_ver)
                
                api_status = "[green]✓ SET[/green]" if self.api_key else "[red]✗ MISSING[/red]"
                table.add_row("API Key", api_status, "Kite Connect")
                
                token_status = "[green]✓ SET[/green]" if self.access_token else "[red]✗ MISSING[/red]"
                table.add_row("Access Token", token_status, "Authentication")
                
                # Platform status with activity indicator
                if self.is_running:
                    if self.is_platform_active():
                        platform_status = "[green]✓ ACTIVE[/green]"
                        details = f"Collecting data"
                    else:
                        platform_status = "[yellow]⚠ IDLE[/yellow]"
                        details = "No recent activity"
                else:
                    platform_status = "[yellow]⚠ READY[/yellow]"
                    details = "G6.1 Core"
                
                table.add_row("Platform", platform_status, details)
                
                # Add metrics row if running
                if self.is_running and self.platform_metrics['collections'] > 0:
                    collections = self.platform_metrics['collections']
                    table.add_row("Collections", f"[blue]{collections}[/blue]", "Data cycles")
                
                self.console.print(table)
            except Exception:
                self.show_simple_status()
        else:
            self.show_simple_status()
    
    def is_platform_active(self):
        """🔍 Check if platform is actively collecting data."""
        if not self.last_activity:
            return False
        
        # Consider active if activity within last 2 minutes
        time_since_activity = time.time() - self.last_activity
        return time_since_activity < 120
    
    def show_simple_status(self):
        """📊 Simple status display."""
        print("\nSYSTEM STATUS")
        print("-" * 20)
        print(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
        print(f"API Key: {'SET' if self.api_key else 'MISSING'}")
        print(f"Access Token: {'SET' if self.access_token else 'MISSING'}")
        
        if self.is_running:
            if self.is_platform_active():
                print("Platform: ACTIVE (collecting data)")
            else:
                print("Platform: RUNNING (idle)")
        else:
            print("Platform: READY")
    
    def show_main_menu(self):
        """📋 Show main menu."""
        if self.use_rich:
            try:
                menu_text = """[bold]Main Menu[/bold]

[cyan]1.[/cyan] 🔌 Token Management
[cyan]2.[/cyan] ⚙️  Configuration  
[cyan]3.[/cyan] 🚀 Start Platform
[cyan]4.[/cyan] 📊 View Metrics
[cyan]5.[/cyan] 🛑 Stop Platform
[cyan]6.[/cyan] ❌ Exit"""

                self.console.print(Panel(menu_text, title="🎛️ Control Panel", box=box.ROUNDED))
                
                choice = Prompt.ask(
                    "Select option",
                    choices=["1", "2", "3", "4", "5", "6"],
                    default="3"
                )
                return choice
            except Exception:
                return self.show_simple_menu()
        else:
            return self.show_simple_menu()
    
    def show_simple_menu(self):
        """📋 Simple menu."""
        print("\nMAIN MENU")
        print("-" * 20)
        print("1. 🔌 Token Management")
        print("2. ⚙️  Configuration")
        print("3. 🚀 Start Platform")
        print("4. 📊 View Metrics")
        print("5. 🛑 Stop Platform")
        print("6. ❌ Exit")
        
        choice = input("\nSelect option [1-6] (default: 3): ").strip() or "3"
        return choice
    
    def show_metrics_dashboard(self):
        """📊 Show comprehensive metrics dashboard."""
        if not self.use_rich:
            self.show_simple_metrics()
            return
        
        try:
            # Create metrics layout
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="body"),
                Layout(name="footer", size=3)
            )
            
            layout["body"].split_row(
                Layout(name="left"),
                Layout(name="right")
            )
            
            # Header
            header_text = "[bold cyan]📊 PLATFORM METRICS DASHBOARD[/bold cyan]"
            layout["header"].update(Panel(header_text, box=box.HEAVY))
            
            # Left panel - Platform Metrics
            platform_table = Table(title="Platform Performance", box=box.ROUNDED)
            platform_table.add_column("Metric", style="cyan")
            platform_table.add_column("Value", style="green")
            platform_table.add_column("Status")
            
            # Calculate uptime
            if self.platform_metrics['start_time']:
                uptime = time.time() - self.platform_metrics['start_time']
                uptime_str = f"{uptime/60:.1f} minutes"
            else:
                uptime_str = "Not started"
            
            platform_table.add_row("Uptime", uptime_str, "🕐")
            platform_table.add_row("Status", self.platform_metrics['status'].upper(), "✅" if self.is_running else "⚠️")
            platform_table.add_row("Collections", str(self.platform_metrics['collections']), "📊")
            platform_table.add_row("API Calls", str(self.platform_metrics['api_calls']), "🔌")
            platform_table.add_row("Errors", str(self.platform_metrics['errors']), "❌" if self.platform_metrics['errors'] > 0 else "✅")
            
            if self.platform_metrics['last_collection']:
                last_collection_str = self.platform_metrics['last_collection']
            else:
                last_collection_str = "None yet"
            
            platform_table.add_row("Last Collection", last_collection_str, "🕒")
            
            layout["left"].update(Panel(platform_table, title="📊 Performance"))
            
            # Right panel - System Info
            system_table = Table(title="System Information", box=box.ROUNDED)
            system_table.add_column("Component", style="cyan")
            system_table.add_column("Status", style="green")
            
            system_table.add_row("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
            system_table.add_row("Platform Process", "Running" if self.is_running else "Stopped")
            system_table.add_row("API Credentials", "Valid" if (self.api_key and self.access_token) else "Missing")
            system_table.add_row("Rich UI", "Active" if self.use_rich else "Fallback")
            system_table.add_row("Encoding", "UTF-8")
            
            layout["right"].update(Panel(system_table, title="🖥️ System"))
            
            # Footer
            footer_text = "[dim]Press any key to return to main menu...[/dim]"
            layout["footer"].update(Panel(footer_text, box=box.HEAVY))
            
            # Display dashboard
            self.console.print(layout)
            
            # Wait for input
            input()
            
        except Exception as e:
            self.console.print(f"[red]❌ Metrics display error: {e}[/red]")
            self.show_simple_metrics()
    
    def show_simple_metrics(self):
        """📊 Simple metrics display."""
        print("\n📊 PLATFORM METRICS")
        print("=" * 30)
        
        if self.platform_metrics['start_time']:
            uptime = time.time() - self.platform_metrics['start_time']
            print(f"Uptime: {uptime/60:.1f} minutes")
        else:
            print("Uptime: Not started")
        
        print(f"Status: {self.platform_metrics['status'].upper()}")
        print(f"Collections: {self.platform_metrics['collections']}")
        print(f"API Calls: {self.platform_metrics['api_calls']}")
        print(f"Errors: {self.platform_metrics['errors']}")
        print(f"Last Collection: {self.platform_metrics['last_collection'] or 'None yet'}")
        
        input("\nPress Enter to continue...")
    
    def find_platform_file(self):
        """🔍 Find the best platform file."""
        candidates = [
            'g6_platform_main_v2.py',
            'g6_platform_main_FINAL_WORKING.py',
            'kite_login_and_launch_FINAL_WORKING.py',
            'g6_platform_main_fixed_FINAL.py'
        ]
        
        for filename in candidates:
            if Path(filename).exists():
                return Path(filename)
        return None
    
    def create_working_test_platform(self):
        """🧪 Create a working test platform with proper data simulation."""
        test_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G6.1 Working Test Platform with Data Collection Simulation
"""

import os
import sys
import time
import random
from datetime import datetime

def simulate_data_collection():
    """Simulate realistic data collection."""
    indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
    
    for index in indices:
        print(f"[DATA] Starting {index} options collection...")
        time.sleep(1)
        
        # Simulate collecting options data
        options_count = random.randint(8, 15)
        for i in range(options_count):
            strike = random.randint(17000, 18000) if index == 'NIFTY' else random.randint(44000, 46000)
            option_type = random.choice(['CE', 'PE'])
            price = random.uniform(50, 300)
            print(f"[OK] {index} {strike}{option_type}: ₹{price:.2f}")
            time.sleep(0.2)
        
        print(f"[OK] {index} collection complete - {options_count} options processed")
    
    print(f"[OK] Collection cycle completed at {datetime.now().strftime('%H:%M:%S')}")

def main():
    """Working test platform main function."""
    print("[LAUNCH] G6.1 Working Test Platform Starting")
    print("=" * 50)
    
    # Check environment
    api_key = os.getenv('KITE_API_KEY')
    access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    print(f"[OK] API Key: {'SET' if api_key else 'MISSING'}")
    print(f"[OK] Access Token: {'SET' if access_token else 'MISSING'}")
    
    if not api_key or not access_token:
        print("[WARNING] Missing credentials - running in simulation mode")
    else:
        print("[OK] Credentials verified")
    
    print("[OK] Platform initialization complete")
    print("[OK] Starting data collection...")
    
    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            print(f"\\n[DATA] === Collection Cycle {cycle_count} ===")
            
            # Simulate data collection
            simulate_data_collection()
            
            print(f"[OK] Cycle {cycle_count} completed successfully")
            print(f"[OK] Waiting 30 seconds for next cycle...")
            
            # Wait for next cycle
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\\n[STOP] Shutdown requested")
        print("[OK] Platform stopped gracefully")
        return 0
    except Exception as e:
        print(f"[ERROR] Platform error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        try:
            with open('g6_working_test.py', 'w', encoding='utf-8') as f:
                f.write(test_content)
            return Path('g6_working_test.py')
        except Exception:
            return None
    
    def start_output_reader(self, process):
        """📖 Start reading output and tracking metrics."""
        def read_output():
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        clean_line = line.rstrip()
                        self.output_queue.put(('stdout', clean_line))
                        
                        # Update metrics based on output
                        self.update_metrics_from_output(clean_line)
                        
                        # Update last activity
                        self.last_activity = time.time()
                    
                    if process.poll() is not None:
                        break
            except Exception as e:
                self.output_queue.put(('error', f"Output reading error: {e}"))
            finally:
                self.output_queue.put(('end', None))
        
        self.output_thread = threading.Thread(target=read_output, daemon=True)
        self.output_thread.start()
    
    def update_metrics_from_output(self, line):
        """📊 Update metrics based on platform output."""
        try:
            # Count collections
            if 'Collection cycle' in line or 'Cycle' in line and 'completed' in line:
                self.platform_metrics['collections'] += 1
                self.platform_metrics['last_collection'] = datetime.now().strftime('%H:%M:%S')
            
            # Count API calls
            if 'API' in line or 'Kite' in line:
                self.platform_metrics['api_calls'] += 1
            
            # Count errors
            if '[ERROR]' in line or 'ERROR' in line or 'failed' in line.lower():
                self.platform_metrics['errors'] += 1
            
            # Update status
            if '[OK]' in line and 'Starting' in line:
                self.platform_metrics['status'] = 'active'
            elif '[STOP]' in line:
                self.platform_metrics['status'] = 'stopping'
                
        except Exception:
            pass  # Ignore metrics update errors
    
    def launch_platform_nonblocking(self):
        """🚀 Launch platform with proper monitoring."""
        if self.is_running:
            if self.use_rich:
                self.console.print("[yellow]⚠️ Platform already running[/yellow]")
            else:
                print("Platform already running")
            return
        
        # Find or create platform file
        platform_file = self.find_platform_file()
        
        if not platform_file:
            if self.use_rich:
                create_test = Confirm.ask("No platform file found. Create working test platform?")
            else:
                create_test = input("No platform file found. Create working test platform? [y/N]: ").lower() == 'y'
            
            if create_test:
                platform_file = self.create_working_test_platform()
                if platform_file:
                    if self.use_rich:
                        self.console.print(f"[green]✅ Created working test platform: {platform_file}[/green]")
                    else:
                        print(f"Created working test platform: {platform_file}")
                else:
                    if self.use_rich:
                        self.console.print("[red]❌ Failed to create test platform[/red]")
                    else:
                        print("Failed to create test platform")
                    return
            else:
                return
        
        try:
            if self.use_rich:
                self.console.print(f"[cyan]🚀 Launching: {platform_file}[/cyan]")
            else:
                print(f"Launching: {platform_file}")
            
            # Setup environment
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            # Start process
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
            self.platform_metrics['start_time'] = time.time()
            self.platform_metrics['status'] = 'starting'
            
            # Start output reader
            self.start_output_reader(self.platform_process)
            
            if self.use_rich:
                self.console.print("[green]✅ Platform launched - streaming output...[/green]")
                self.stream_output_rich()
            else:
                print("Platform launched - streaming output...")
                self.stream_output_simple()
                
        except Exception as e:
            if self.use_rich:
                self.console.print(f"[red]❌ Launch failed: {e}[/red]")
            else:
                print(f"Launch failed: {e}")
            
            # Reset state on failure
            self.is_running = False
            self.platform_metrics['status'] = 'failed'
    
    def stream_output_rich(self):
        """📺 Stream output with Rich UI and metrics tracking."""
        try:
            with Live(console=self.console, refresh_per_second=2) as live:
                output_lines = []
                
                while self.is_running:
                    try:
                        msg_type, content = self.output_queue.get(timeout=0.5)
                        
                        if msg_type == 'stdout' and content:
                            # Clean content for display
                            clean_content = content.replace('🚀', '[LAUNCH]').replace('✅', '[OK]').replace('❌', '[ERROR]')
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            output_lines.append(f"[dim]{timestamp}[/dim] {clean_content}")
                            
                            # Keep only last 12 lines
                            if len(output_lines) > 12:
                                output_lines = output_lines[-12:]
                        
                        elif msg_type == 'end':
                            break
                        elif msg_type == 'error':
                            output_lines.append(f"[red]ERROR: {content}[/red]")
                    
                    except Empty:
                        # Check if process is still alive
                        if self.platform_process and self.platform_process.poll() is not None:
                            exit_code = self.platform_process.poll()
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            output_lines.append(f"[yellow]{timestamp} Platform exited with code: {exit_code}[/yellow]")
                            self.is_running = False
                            self.platform_metrics['status'] = 'stopped'
                            break
                    
                    # Update display
                    if output_lines:
                        output_text = "\n".join(output_lines)
                        
                        # Add metrics info
                        metrics_info = f"Collections: {self.platform_metrics['collections']} | Errors: {self.platform_metrics['errors']} | Status: {self.platform_metrics['status'].upper()}"
                        
                        full_content = f"{output_text}\n\n[dim]{metrics_info}[/dim]"
                        
                        panel = Panel(
                            full_content,
                            title="[bold]📺 Platform Output & Metrics[/bold]",
                            border_style="green" if self.is_running else "red"
                        )
                        live.update(panel)
            
            self.console.print("[cyan]📺 Output streaming completed. Press Enter to continue...[/cyan]")
            input()
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️ Output streaming interrupted[/yellow]")
            self.stop_platform()
    
    def stream_output_simple(self):
        """📺 Stream output simple mode."""
        try:
            print("=== PLATFORM OUTPUT ===")
            
            while self.is_running:
                try:
                    msg_type, content = self.output_queue.get(timeout=0.5)
                    
                    if msg_type == 'stdout' and content:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"[{timestamp}] {content}")
                    elif msg_type == 'end':
                        break
                    elif msg_type == 'error':
                        print(f"ERROR: {content}")
                
                except Empty:
                    # Check if process ended
                    if self.platform_process and self.platform_process.poll() is not None:
                        exit_code = self.platform_process.poll()
                        print(f"Platform exited with code: {exit_code}")
                        self.is_running = False
                        break
            
            print("=== OUTPUT COMPLETE ===")
            print(f"Collections: {self.platform_metrics['collections']}, Errors: {self.platform_metrics['errors']}")
            input("Press Enter to continue...")
            
        except KeyboardInterrupt:
            print("\nOutput streaming interrupted")
            self.stop_platform()
    
    def stop_platform(self):
        """🛑 Stop platform gracefully."""
        if not self.is_running:
            if self.use_rich:
                self.console.print("[yellow]⚠️ Platform not running[/yellow]")
            else:
                print("Platform not running")
            return
        
        try:
            if self.platform_process:
                self.platform_process.terminate()
                try:
                    self.platform_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.platform_process.kill()
                    self.platform_process.wait()
            
            self.is_running = False
            self.platform_metrics['status'] = 'stopped'
            
            if self.use_rich:
                self.console.print("[green]✅ Platform stopped[/green]")
            else:
                print("Platform stopped")
                
        except Exception as e:
            if self.use_rich:
                self.console.print(f"[red]❌ Stop error: {e}[/red]")
            else:
                print(f"Stop error: {e}")
    
    def run_launcher(self):
        """🖥️ Run the main launcher loop."""
        try:
            while True:
                self.print_banner()
                self.show_system_status()
                
                choice = self.show_main_menu()
                
                if choice == "1":
                    if self.use_rich:
                        self.console.print("[yellow]💡 Token management: Edit your .env file with KITE_API_KEY and KITE_ACCESS_TOKEN[/yellow]")
                    else:
                        print("Token management: Edit your .env file with KITE_API_KEY and KITE_ACCESS_TOKEN")
                elif choice == "2":
                    if self.use_rich:
                        self.console.print("[yellow]💡 Configuration: Edit config.json for platform settings[/yellow]")
                    else:
                        print("Configuration: Edit config.json for platform settings")
                elif choice == "3":
                    self.launch_platform_nonblocking()
                elif choice == "4":
                    self.show_metrics_dashboard()  # ✅ FIXED: Now properly implemented
                elif choice == "5":
                    self.stop_platform()
                elif choice == "6":
                    if self.is_running:
                        self.stop_platform()
                    
                    if self.use_rich:
                        self.console.print("[green]👋 Goodbye![/green]")
                    else:
                        print("Goodbye!")
                    break
                
                if choice not in ["3", "4", "6"]:  # Don't pause after platform launch or metrics
                    input("\nPress Enter to continue...")
                    
        except KeyboardInterrupt:
            if self.use_rich:
                self.console.print("\n[yellow]⚠️ Launcher interrupted[/yellow]")
            else:
                print("\nLauncher interrupted")
        finally:
            if self.is_running:
                self.stop_platform()

def main():
    """🚀 Main entry point."""
    try:
        launcher = FixedNonBlockingLauncher()
        launcher.run_launcher()
        return 0
    except Exception as e:
        print(f"Launcher error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())