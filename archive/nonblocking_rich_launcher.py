#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Non-Blocking Rich Launcher - G6.1 Platform v2.0
Author: AI Assistant (Fixes hanging launch with real-time feedback)

SOLUTION: Non-blocking launch with live output streaming
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path
from queue import Queue, Empty

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
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from dotenv import load_dotenv, set_key
load_dotenv()

class NonBlockingRichLauncher:
    """🚀 Non-blocking launcher with real-time feedback."""
    
    def __init__(self):
        """Initialize non-blocking launcher."""
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
        """📊 Show system status."""
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
                
                platform_status = "[yellow]⚠ READY[/yellow]" if not self.is_running else "[green]✓ RUNNING[/green]"
                table.add_row("Platform", platform_status, "G6.1 Core")
                
                self.console.print(table)
            except Exception:
                self.show_simple_status()
        else:
            self.show_simple_status()
    
    def show_simple_status(self):
        """📊 Simple status display."""
        print("\nSYSTEM STATUS")
        print("-" * 20)
        print(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
        print(f"API Key: {'SET' if self.api_key else 'MISSING'}")
        print(f"Access Token: {'SET' if self.access_token else 'MISSING'}")
        print(f"Platform: {'RUNNING' if self.is_running else 'READY'}")
    
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
    
    def create_minimal_test_platform(self):
        """🧪 Create minimal test platform."""
        test_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G6.1 Minimal Test Platform
"""

import os
import sys
import time
from datetime import datetime

def main():
    """Minimal test platform."""
    print("[LAUNCH] G6.1 Test Platform Starting")
    print("=" * 40)
    
    # Check environment
    api_key = os.getenv('KITE_API_KEY')
    access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    print(f"[OK] API Key: {'SET' if api_key else 'MISSING'}")
    print(f"[OK] Access Token: {'SET' if access_token else 'MISSING'}")
    
    if not api_key or not access_token:
        print("[WARNING] Missing credentials - running in demo mode")
    
    print("[OK] Platform initialization complete")
    print("[OK] Starting main loop...")
    
    try:
        count = 0
        while True:
            count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[DATA] Collection cycle {count} at {timestamp}")
            
            # Simulate some processing
            print(f"[OK] Processing NIFTY options...")
            time.sleep(2)
            print(f"[OK] Processing BANKNIFTY options...")
            time.sleep(2)
            print(f"[OK] Cycle {count} completed")
            
            # Wait for next cycle
            time.sleep(10)
            
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
            with open('g6_minimal_test.py', 'w', encoding='utf-8') as f:
                f.write(test_content)
            return Path('g6_minimal_test.py')
        except Exception:
            return None
    
    def start_output_reader(self, process):
        """📖 Start reading output in background thread."""
        def read_output():
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        self.output_queue.put(('stdout', line.rstrip()))
                    if process.poll() is not None:
                        break
            except Exception as e:
                self.output_queue.put(('error', f"Output reading error: {e}"))
            finally:
                self.output_queue.put(('end', None))
        
        self.output_thread = threading.Thread(target=read_output, daemon=True)
        self.output_thread.start()
    
    def launch_platform_nonblocking(self):
        """🚀 Launch platform with non-blocking output."""
        if self.is_running:
            if self.use_rich:
                self.console.print("[yellow]⚠️ Platform already running[/yellow]")
            else:
                print("Platform already running")
            return
        
        # Find platform file
        platform_file = self.find_platform_file()
        
        if not platform_file:
            if self.use_rich:
                create_test = Confirm.ask("No platform file found. Create test platform?")
            else:
                create_test = input("No platform file found. Create test platform? [y/N]: ").lower() == 'y'
            
            if create_test:
                platform_file = self.create_minimal_test_platform()
                if platform_file:
                    if self.use_rich:
                        self.console.print(f"[green]✅ Created test platform: {platform_file}[/green]")
                    else:
                        print(f"Created test platform: {platform_file}")
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
    
    def stream_output_rich(self):
        """📺 Stream output with Rich UI."""
        try:
            with Live(console=self.console, refresh_per_second=4) as live:
                output_lines = []
                
                while self.is_running:
                    try:
                        msg_type, content = self.output_queue.get(timeout=0.1)
                        
                        if msg_type == 'stdout' and content:
                            # Clean content for display
                            clean_content = content.replace('🚀', '[LAUNCH]').replace('✅', '[OK]').replace('❌', '[ERROR]')
                            output_lines.append(f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim] {clean_content}")
                            
                            # Keep only last 15 lines
                            if len(output_lines) > 15:
                                output_lines = output_lines[-15:]
                        
                        elif msg_type == 'end':
                            break
                        elif msg_type == 'error':
                            output_lines.append(f"[red]ERROR: {content}[/red]")
                    
                    except Empty:
                        pass
                    
                    # Update display
                    if output_lines:
                        output_text = "\n".join(output_lines)
                        panel = Panel(
                            output_text,
                            title="[bold]Platform Output[/bold]",
                            border_style="green" if self.is_running else "red"
                        )
                        live.update(panel)
                    
                    # Check if process ended
                    if self.platform_process and self.platform_process.poll() is not None:
                        exit_code = self.platform_process.poll()
                        output_lines.append(f"[yellow]Platform exited with code: {exit_code}[/yellow]")
                        self.is_running = False
                        
                        # Final display
                        final_text = "\n".join(output_lines)
                        final_panel = Panel(
                            final_text,
                            title="[bold]Platform Output (Complete)[/bold]",
                            border_style="yellow"
                        )
                        live.update(final_panel)
                        break
            
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
                    msg_type, content = self.output_queue.get(timeout=0.1)
                    
                    if msg_type == 'stdout' and content:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"[{timestamp}] {content}")
                    elif msg_type == 'end':
                        break
                    elif msg_type == 'error':
                        print(f"ERROR: {content}")
                
                except Empty:
                    pass
                
                # Check if process ended
                if self.platform_process and self.platform_process.poll() is not None:
                    exit_code = self.platform_process.poll()
                    print(f"Platform exited with code: {exit_code}")
                    self.is_running = False
                    break
            
            print("=== OUTPUT COMPLETE ===")
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
                        self.console.print("[yellow]Token management coming soon...[/yellow]")
                    else:
                        print("Token management coming soon...")
                elif choice == "2":
                    if self.use_rich:
                        self.console.print("[yellow]Configuration coming soon...[/yellow]")
                    else:
                        print("Configuration coming soon...")
                elif choice == "3":
                    self.launch_platform_nonblocking()
                elif choice == "4":
                    if self.use_rich:
                        self.console.print("[yellow]Metrics coming soon...[/yellow]")
                    else:
                        print("Metrics coming soon...")
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
                
                if choice not in ["3", "6"]:
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
        launcher = NonBlockingRichLauncher()
        launcher.run_launcher()
        return 0
    except Exception as e:
        print(f"Launcher error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())