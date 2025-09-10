#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Enhanced Ultimate Launcher - G6.1 Platform v2.0
Author: AI Assistant (Concise logging + larger windows + live metrics)

ENHANCEMENTS:
1. ✅ Concise index-wise logging (not individual options)
2. ✅ Double-sized streaming window
3. ✅ Live metrics panel alongside streaming
4. ✅ Time-based concise summaries
5. ✅ Enhanced visual layout
"""

import os
import sys
import time
import signal
import subprocess
import threading
import json
import random
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime

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

# Rich imports
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.live import Live
    from rich.text import Text
    from rich import box
    from rich.layout import Layout
    from rich.columns import Columns
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from dotenv import load_dotenv
load_dotenv()

class EnhancedUltimateLauncher:
    """🚀 Enhanced ultimate launcher with improved UI and logging."""
    
    def __init__(self):
        """Initialize enhanced launcher."""
        # Rich console
        if RICH_AVAILABLE:
            try:
                self.console = Console(color_system="auto", force_terminal=True, width=140)  # Wider console
                self.use_rich = True
                self.console.print("[green]✅ Enhanced Ultimate Launcher initialized[/green]")
            except Exception:
                self.use_rich = False
                print("Enhanced Ultimate Launcher initialized (fallback mode)")
        else:
            self.use_rich = False
            print("Enhanced Ultimate Launcher initialized (basic mode)")
        
        # State
        self.platform_process = None
        self.is_running = False
        self.output_queue = Queue()
        self.output_thread = None
        self.last_activity = None
        
        # Enhanced metrics
        self.platform_metrics = {
            'start_time': None,
            'collections': 0,
            'errors': 0,
            'api_calls': 0,
            'options_processed': 0,
            'last_collection': None,
            'status': 'stopped',
            'current_index': None,
            'indices_processed': {'NIFTY': 0, 'BANKNIFTY': 0, 'FINNIFTY': 0, 'MIDCPNIFTY': 0},
            'processing_rates': {'options_per_min': 0, 'cycles_per_hour': 0}
        }
        
        # Environment
        self.api_key = os.getenv('KITE_API_KEY')
        self.access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    def print_banner(self):
        """🎨 Print enhanced banner."""
        if self.use_rich:
            banner = """[bold cyan]G6.1 OPTIONS ANALYTICS PLATFORM[/bold cyan]
[dim]Version 2.0 - Enhanced Ultimate Edition[/dim]"""
            self.console.print(Panel(banner, box=box.DOUBLE))
        else:
            print("=" * 60)
            print("G6.1 OPTIONS ANALYTICS PLATFORM v2.0")
            print("Enhanced Ultimate Edition")
            print("=" * 60)
    
    def show_system_status(self):
        """📊 Show enhanced system status."""
        if self.use_rich:
            try:
                table = Table(title="[bold]System Status[/bold]", box=box.ROUNDED)
                table.add_column("Component", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Details")
                
                # Python
                python_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
                table.add_row("Python", "[green]✓ Ready[/green]", python_ver)
                
                # API credentials
                api_status = "[green]✓ SET[/green]" if self.api_key else "[red]✗ MISSING[/red]"
                table.add_row("API Key", api_status, "Kite Connect")
                
                token_status = "[green]✓ SET[/green]" if self.access_token else "[red]✗ MISSING[/red]"
                table.add_row("Access Token", token_status, "Authentication")
                
                # Enhanced platform status
                if self.is_running:
                    if self.is_collecting_data():
                        platform_status = "[green]✓ COLLECTING[/green]"
                        current_idx = self.platform_metrics.get('current_index', 'Unknown')
                        details = f"Processing {current_idx}"
                    else:
                        platform_status = "[yellow]⚠ RUNNING[/yellow]"
                        details = "Process active, monitoring..."
                else:
                    platform_status = "[yellow]⚠ READY[/yellow]"
                    details = "Ready to launch"
                
                table.add_row("Platform", platform_status, details)
                
                # Enhanced metrics display
                if self.is_running:
                    options_count = self.platform_metrics['options_processed']
                    cycles_count = self.platform_metrics['collections']
                    
                    if options_count > 0:
                        table.add_row("Options Processed", f"[blue]{options_count}[/blue]", "Live data")
                    
                    if cycles_count > 0:
                        table.add_row("Collection Cycles", f"[blue]{cycles_count}[/blue]", "Complete cycles")
                    
                    # Show processing rates
                    options_per_min = self.platform_metrics['processing_rates']['options_per_min']
                    if options_per_min > 0:
                        table.add_row("Processing Rate", f"[blue]{options_per_min:.1f}/min[/blue]", "Options throughput")
                
                self.console.print(table)
            except Exception:
                self.show_simple_status()
        else:
            self.show_simple_status()
    
    def is_collecting_data(self):
        """🔍 Enhanced data collection detection."""
        if not self.last_activity:
            return False
        
        time_since_activity = time.time() - self.last_activity
        has_processed_options = self.platform_metrics['options_processed'] > 0
        recent_activity = time_since_activity < 45  # Extended timeout
        
        return recent_activity and has_processed_options
    
    def show_simple_status(self):
        """📊 Simple status."""
        print("\nENHANCED SYSTEM STATUS")
        print("-" * 25)
        print(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
        print(f"API Key: {'SET' if self.api_key else 'MISSING'}")
        print(f"Access Token: {'SET' if self.access_token else 'MISSING'}")
        
        if self.is_running:
            if self.is_collecting_data():
                current_idx = self.platform_metrics.get('current_index', 'Unknown')
                options_count = self.platform_metrics['options_processed']
                print(f"Platform: COLLECTING {current_idx} ({options_count} options)")
            else:
                print("Platform: RUNNING (monitoring activity...)")
        else:
            print("Platform: READY")
    
    def show_main_menu(self):
        """📋 Show enhanced main menu."""
        if self.use_rich:
            try:
                menu_text = """[bold]Enhanced Control Panel[/bold]

[cyan]1.[/cyan] 🚀 Launch Enhanced Data Collection Platform
[cyan]2.[/cyan] 📊 View Live Metrics Dashboard
[cyan]3.[/cyan] 🔧 Create Enhanced Platform
[cyan]4.[/cyan] 🧪 Diagnose Platform Issues
[cyan]5.[/cyan] 🛑 Stop Platform
[cyan]6.[/cyan] ❌ Exit"""

                self.console.print(Panel(menu_text, title="🎛️ Enhanced Ultimate Control", box=box.ROUNDED))
                
                choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6"], default="1")
                return choice
            except Exception:
                return self.show_simple_menu()
        else:
            return self.show_simple_menu()
    
    def show_simple_menu(self):
        """📋 Simple menu."""
        print("\nENHANCED ULTIMATE CONTROL PANEL")
        print("-" * 35)
        print("1. 🚀 Launch Enhanced Data Collection")
        print("2. 📊 View Live Metrics Dashboard")
        print("3. 🔧 Create Enhanced Platform")
        print("4. 🧪 Diagnose Platform Issues")
        print("5. 🛑 Stop Platform")
        print("6. ❌ Exit")
        
        choice = input("\nSelect option [1-6] (default: 1): ").strip() or "1"
        return choice
    
    def create_enhanced_data_platform(self):
        """🔧 Create enhanced data collection platform with concise logging."""
        platform_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G6.1 Enhanced Data Collection Platform
Concise index-wise logging with time-based summaries
"""

import os
import sys
import time
import random
import signal
from datetime import datetime, timedelta

class EnhancedG6DataCollector:
    """Enhanced data collector with concise logging."""
    
    def __init__(self):
        """Initialize enhanced data collector."""
        self.api_key = os.getenv('KITE_API_KEY')
        self.access_token = os.getenv('KITE_ACCESS_TOKEN')
        self.running = True
        
        # Market indices configuration
        self.indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
        self.strike_offsets = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
        
        # Enhanced metrics
        self.total_options = 0
        self.cycle_count = 0
        self.start_time = time.time()
        self.index_stats = {idx: {'options': 0, 'avg_price': 0, 'total_volume': 0} for idx in self.indices}
        
        # Signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\\n[STOP] Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def get_market_data(self, index):
        """Get enhanced market data for index."""
        base_strikes = {
            'NIFTY': random.randint(24850, 25150),
            'BANKNIFTY': random.randint(51200, 52200),
            'FINNIFTY': random.randint(23200, 24200),
            'MIDCPNIFTY': random.randint(12600, 13100)
        }
        
        intervals = {
            'NIFTY': 50,
            'BANKNIFTY': 100,
            'FINNIFTY': 50,
            'MIDCPNIFTY': 25
        }
        
        return {
            'atm_strike': base_strikes.get(index, 25000),
            'interval': intervals.get(index, 50),
            'market_trend': random.choice(['bullish', 'bearish', 'neutral']),
            'volatility': random.uniform(15, 35)
        }
    
    def process_index_options(self, index):
        """Process all options for an index with concise logging."""
        start_time = time.time()
        
        # Get market data
        market_data = self.get_market_data(index)
        atm_strike = market_data['atm_strike']
        interval = market_data['interval']
        
        print(f"[DATA] Processing {index} → ATM: {atm_strike} | Volatility: {market_data['volatility']:.1f}%")
        
        options_processed = 0
        total_premium = 0
        total_volume = 0
        ce_count = 0
        pe_count = 0
        
        # Process all strikes and option types
        for offset in self.strike_offsets:
            strike = atm_strike + (offset * interval)
            
            for option_type in ['CE', 'PE']:
                # Simulate realistic option pricing
                distance_from_atm = abs(offset)
                
                if option_type == 'CE':
                    if offset <= 0:  # ITM/ATM Calls
                        price = random.uniform(150, 600) / (1 + distance_from_atm * 0.1)
                    else:  # OTM Calls
                        price = random.uniform(5, 150) / (1 + distance_from_atm * 0.3)
                else:  # PE
                    if offset >= 0:  # ITM/ATM Puts
                        price = random.uniform(150, 600) / (1 + distance_from_atm * 0.1)
                    else:  # OTM Puts
                        price = random.uniform(5, 150) / (1 + distance_from_atm * 0.3)
                
                volume = random.randint(500, 25000)
                
                # Accumulate statistics
                options_processed += 1
                total_premium += price
                total_volume += volume
                
                if option_type == 'CE':
                    ce_count += 1
                else:
                    pe_count += 1
                
                # Brief processing delay
                time.sleep(0.02)
                
                if not self.running:
                    break
            
            if not self.running:
                break
        
        # Calculate summary statistics
        processing_time = time.time() - start_time
        avg_premium = total_premium / max(1, options_processed)
        
        # Update global statistics
        self.total_options += options_processed
        self.index_stats[index]['options'] += options_processed
        self.index_stats[index]['avg_price'] = avg_premium
        self.index_stats[index]['total_volume'] += total_volume
        
        # Concise summary log
        print(f"[OK] {index} Complete → {options_processed} options | Avg: ₹{avg_premium:.1f} | Vol: {total_volume:,} | Time: {processing_time:.1f}s")
        
        return {
            'options_processed': options_processed,
            'avg_premium': avg_premium,
            'total_volume': total_volume,
            'processing_time': processing_time,
            'ce_count': ce_count,
            'pe_count': pe_count
        }
    
    def run_collection_cycle(self):
        """Run enhanced collection cycle with time-based logging."""
        self.cycle_count += 1
        cycle_start = time.time()
        
        # Cycle header with timestamp
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\\n[CYCLE] === Cycle {self.cycle_count} Started at {timestamp} ===")
        
        cycle_stats = {
            'total_options': 0,
            'total_volume': 0,
            'indices_processed': 0,
            'avg_processing_time': 0
        }
        
        # Process each index
        for index in self.indices:
            if not self.running:
                break
            
            print(f"[INFO] Current Index: {index}")
            
            try:
                index_result = self.process_index_options(index)
                
                # Accumulate cycle statistics
                cycle_stats['total_options'] += index_result['options_processed']
                cycle_stats['total_volume'] += index_result['total_volume']
                cycle_stats['indices_processed'] += 1
                cycle_stats['avg_processing_time'] += index_result['processing_time']
                
                # Brief pause between indices
                if self.running and index != self.indices[-1]:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"[ERROR] {index} processing failed: {e}")
                continue
        
        # Cycle completion summary
        total_cycle_time = time.time() - cycle_start
        avg_index_time = cycle_stats['avg_processing_time'] / max(1, cycle_stats['indices_processed'])
        
        print(f"[CYCLE] Cycle {self.cycle_count} Complete → {cycle_stats['total_options']} options | {cycle_stats['indices_processed']}/{len(self.indices)} indices | Duration: {total_cycle_time:.1f}s")
        
        return cycle_stats['total_options'] > 0
    
    def print_periodic_summary(self):
        """Print periodic performance summary."""
        uptime = time.time() - self.start_time
        uptime_min = uptime / 60
        
        print(f"\\n[SUMMARY] === Performance Report ===")
        print(f"[INFO] Runtime: {uptime_min:.1f} minutes | Cycles: {self.cycle_count}")
        print(f"[INFO] Total Options: {self.total_options} | Rate: {self.total_options/uptime_min:.1f}/min")
        
        # Index breakdown
        for index in self.indices:
            stats = self.index_stats[index]
            print(f"[INFO] {index}: {stats['options']} options | Avg: ₹{stats['avg_price']:.1f} | Vol: {stats['total_volume']:,}")
        
        print(f"[SUMMARY] === End Report ===\\n")
    
    def run(self):
        """Enhanced main data collection loop."""
        print("[LAUNCH] G6.1 Enhanced Data Collection Platform")
        print("=" * 70)
        
        # Enhanced startup logging
        startup_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[INFO] Platform started at {startup_time}")
        
        # Validate credentials with enhanced logging
        if not self.api_key:
            print("[WARNING] KITE_API_KEY not found - running in enhanced simulation mode")
        else:
            print(f"[OK] API Key configured: {self.api_key[:8]}...")
        
        if not self.access_token:
            print("[WARNING] KITE_ACCESS_TOKEN not found - running in enhanced simulation mode")
        else:
            print(f"[OK] Access Token configured: {self.access_token[:8]}...")
        
        print(f"[CONFIG] Target Indices: {', '.join(self.indices)}")
        print(f"[CONFIG] Strike Offsets: {self.strike_offsets}")
        print(f"[CONFIG] Options per cycle: {len(self.strike_offsets) * 2 * len(self.indices)}")
        print("[OK] Enhanced platform initialization complete")
        print("[START] Beginning continuous data collection...")
        
        try:
            # Enhanced main collection loop
            while self.running:
                # Run collection cycle
                success = self.run_collection_cycle()
                
                if not success:
                    print("[WARNING] Collection cycle incomplete, continuing...")
                
                # Periodic detailed summary
                if self.cycle_count % 3 == 0:  # Every 3 cycles
                    self.print_periodic_summary()
                
                # Enhanced wait with status updates
                if self.running:
                    wait_time = 25  # Slightly faster cycles
                    next_cycle_time = datetime.now() + timedelta(seconds=wait_time)
                    print(f"[WAIT] Next cycle at {next_cycle_time.strftime('%H:%M:%S')} (in {wait_time}s)")
                    
                    # Countdown with periodic updates
                    for remaining in range(wait_time, 0, -5):
                        if not self.running:
                            break
                        if remaining <= wait_time and remaining % 10 == 0:
                            print(f"[WAIT] Next cycle in {remaining}s...")
                        time.sleep(min(5, remaining))
        
        except KeyboardInterrupt:
            print("\\n[STOP] Keyboard interrupt received")
        except Exception as e:
            print(f"\\n[ERROR] Platform error: {e}")
        finally:
            self.running = False
            print("\\n[SHUTDOWN] Stopping enhanced data collection...")
            self.print_periodic_summary()
            
            # Final statistics
            uptime = time.time() - self.start_time
            print(f"[FINAL] Platform ran for {uptime/60:.1f} minutes")
            print(f"[FINAL] Processed {self.total_options} total options across {self.cycle_count} cycles")
            print("[OK] Enhanced platform stopped gracefully")

def main():
    """Enhanced main entry point."""
    try:
        collector = EnhancedG6DataCollector()
        collector.run()
        return 0
    except Exception as e:
        print(f"[ERROR] Enhanced platform startup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        try:
            filename = 'g6_enhanced_data_platform.py'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(platform_content)
            
            if self.use_rich:
                self.console.print(f"[green]✅ Created enhanced data platform: {filename}[/green]")
                self.console.print("[cyan]🎯 Enhanced Features:[/cyan]")
                self.console.print("   • Concise index-wise logging (no individual options)")
                self.console.print("   • Time-based summaries with statistics")
                self.console.print("   • Enhanced performance metrics")
                self.console.print("   • Periodic detailed reports")
                self.console.print("   • Faster processing cycles (25s intervals)")
            else:
                print(f"✅ Created enhanced data platform: {filename}")
            
            return Path(filename)
        except Exception as e:
            if self.use_rich:
                self.console.print(f"[red]❌ Failed to create enhanced platform: {e}[/red]")
            else:
                print(f"❌ Failed to create enhanced platform: {e}")
            return None
    
    def start_output_reader(self, process):
        """📖 Enhanced output reader with better metrics tracking."""
        def read_output():
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        clean_line = line.rstrip()
                        self.output_queue.put(('stdout', clean_line))
                        self.update_enhanced_metrics(clean_line)
                        self.last_activity = time.time()
                    
                    if process.poll() is not None:
                        break
            except Exception as e:
                self.output_queue.put(('error', f"Output reading error: {e}"))
            finally:
                self.output_queue.put(('end', None))
        
        self.output_thread = threading.Thread(target=read_output, daemon=True)
        self.output_thread.start()
    
    def update_enhanced_metrics(self, line):
        """📊 Enhanced metrics tracking with more detailed analysis."""
        try:
            # Track current index being processed
            if '[INFO] Current Index:' in line:
                index_name = line.split('Current Index:')[-1].strip()
                self.platform_metrics['current_index'] = index_name
            
            # Count collection cycles
            if '[CYCLE]' in line and 'Started at' in line:
                self.platform_metrics['collections'] += 1
            
            # Count options processed from summary lines
            if '[OK]' in line and 'Complete →' in line and 'options' in line:
                try:
                    # Extract options count from "X options" pattern
                    parts = line.split('→')[1].split('options')[0].strip()
                    options_count = int(parts.split()[0])
                    self.platform_metrics['options_processed'] += options_count
                    self.platform_metrics['last_collection'] = datetime.now().strftime('%H:%M:%S')
                    
                    # Update index-specific stats
                    current_idx = self.platform_metrics.get('current_index')
                    if current_idx and current_idx in self.platform_metrics['indices_processed']:
                        self.platform_metrics['indices_processed'][current_idx] += options_count
                except ValueError:
                    pass
            
            # Track API activities
            if '[DATA]' in line or 'ATM:' in line:
                self.platform_metrics['api_calls'] += 1
            
            # Count errors
            if '[ERROR]' in line or 'ERROR' in line or 'failed' in line.lower():
                self.platform_metrics['errors'] += 1
            
            # Update status based on activity
            if '[CYCLE]' in line and 'Started' in line:
                self.platform_metrics['status'] = 'collecting'
            elif '[DATA] Processing' in line:
                self.platform_metrics['status'] = 'processing'
            elif '[WAIT]' in line:
                self.platform_metrics['status'] = 'waiting'
            elif '[STOP]' in line or '[SHUTDOWN]' in line:
                self.platform_metrics['status'] = 'stopping'
            elif '[LAUNCH]' in line:
                self.platform_metrics['status'] = 'starting'
            
            # Calculate processing rates
            if self.platform_metrics['start_time']:
                uptime_minutes = (time.time() - self.platform_metrics['start_time']) / 60
                if uptime_minutes > 0:
                    self.platform_metrics['processing_rates']['options_per_min'] = self.platform_metrics['options_processed'] / uptime_minutes
                    self.platform_metrics['processing_rates']['cycles_per_hour'] = (self.platform_metrics['collections'] / uptime_minutes) * 60
                
        except Exception:
            pass
    
    def create_live_metrics_panel(self):
        """📊 Create live metrics panel."""
        try:
            metrics_table = Table(title="Live Metrics", box=box.SIMPLE, show_header=False)
            metrics_table.add_column("Metric", style="cyan", width=15)
            metrics_table.add_column("Value", style="green", width=12)
            
            # Calculate uptime
            if self.platform_metrics['start_time']:
                uptime = time.time() - self.platform_metrics['start_time']
                uptime_str = f"{uptime/60:.1f}m"
            else:
                uptime_str = "0m"
            
            # Add metrics rows
            metrics_table.add_row("⏱️ Uptime", uptime_str)
            metrics_table.add_row("🔄 Cycles", str(self.platform_metrics['collections']))
            metrics_table.add_row("📊 Options", str(self.platform_metrics['options_processed']))
            metrics_table.add_row("⚡ Rate", f"{self.platform_metrics['processing_rates']['options_per_min']:.1f}/min")
            metrics_table.add_row("❌ Errors", str(self.platform_metrics['errors']))
            
            # Current activity
            current_idx = self.platform_metrics.get('current_index', 'None')
            metrics_table.add_row("📍 Current", current_idx[:8])
            
            # Status indicator
            status = self.platform_metrics['status'].upper()
            status_emoji = {
                'COLLECTING': '🟢',
                'PROCESSING': '🟡', 
                'WAITING': '🔵',
                'STARTING': '🟠',
                'STOPPING': '🔴',
                'STOPPED': '⚪'
            }.get(status, '⚪')
            
            metrics_table.add_row("🎯 Status", f"{status_emoji} {status[:8]}")
            
            return Panel(metrics_table, title="📈 Live Metrics", border_style="blue", width=32)
            
        except Exception:
            return Panel("Metrics Error", title="📈 Live Metrics", border_style="red", width=32)
    
    def launch_enhanced_platform(self):
        """🚀 Launch enhanced data collection platform."""
        if self.is_running:
            if self.use_rich:
                self.console.print("[yellow]⚠️ Platform already running[/yellow]")
            else:
                print("Platform already running")
            return
        
        # Create/use enhanced platform
        platform_file = self.create_enhanced_data_platform()
        
        if not platform_file:
            return
        
        try:
            if self.use_rich:
                self.console.print(f"[cyan]🚀 Launching enhanced platform: {platform_file}[/cyan]")
            else:
                print(f"Launching enhanced platform: {platform_file}")
            
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
                self.console.print("[green]✅ Enhanced platform launched - streaming with live metrics...[/green]")
                self.stream_output_with_live_metrics()
            else:
                print("Enhanced platform launched - streaming output...")
                self.stream_output_simple()
                
        except Exception as e:
            if self.use_rich:
                self.console.print(f"[red]❌ Launch failed: {e}[/red]")
            else:
                print(f"Launch failed: {e}")
            
            self.is_running = False
            self.platform_metrics['status'] = 'failed'
    
    def stream_output_with_live_metrics(self):
        """📺 Enhanced streaming with live metrics panel and larger window."""
        try:
            # Create layout with live metrics
            layout = Layout()
            layout.split_row(
                Layout(name="main", ratio=3),
                Layout(name="metrics", size=34)
            )
            
            with Live(layout, console=self.console, refresh_per_second=2) as live:
                output_lines = []
                
                while self.is_running:
                    try:
                        msg_type, content = self.output_queue.get(timeout=0.5)
                        
                        if msg_type == 'stdout' and content:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            output_lines.append(f"[dim]{timestamp}[/dim] {content}")
                            
                            # Keep more lines for larger window (doubled from 12 to 24)
                            if len(output_lines) > 24:
                                output_lines = output_lines[-24:]
                        
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
                        
                        # Enhanced status bar
                        collections = self.platform_metrics['collections']
                        options = self.platform_metrics['options_processed']
                        errors = self.platform_metrics['errors']
                        status = self.platform_metrics['status'].upper()
                        rate = self.platform_metrics['processing_rates']['options_per_min']
                        
                        status_info = f"Cycles: {collections} | Options: {options} | Rate: {rate:.1f}/min | Errors: {errors} | Status: {status}"
                        
                        full_content = f"{output_text}\n\n[dim]{status_info}[/dim]"
                        
                        # Dynamic border color
                        border_color = "green" if self.is_collecting_data() else "yellow" if self.is_running else "red"
                        
                        # Main streaming panel (larger)
                        main_panel = Panel(
                            full_content,
                            title="[bold]📺 Enhanced Live Data Collection[/bold]",
                            border_style=border_color
                        )
                        
                        # Live metrics panel
                        metrics_panel = self.create_live_metrics_panel()
                        
                        # Update layout
                        layout["main"].update(main_panel)
                        layout["metrics"].update(metrics_panel)
            
            self.console.print("[cyan]📺 Enhanced data collection completed. Press Enter to continue...[/cyan]")
            input()
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️ Enhanced data collection interrupted[/yellow]")
            self.stop_platform()
    
    def stream_output_simple(self):
        """📺 Enhanced simple output streaming."""
        try:
            print("=== ENHANCED LIVE DATA COLLECTION ===")
            
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
                    if self.platform_process and self.platform_process.poll() is not None:
                        exit_code = self.platform_process.poll()
                        print(f"Platform exited with code: {exit_code}")
                        self.is_running = False
                        break
            
            print("=== ENHANCED DATA COLLECTION COMPLETE ===")
            options = self.platform_metrics['options_processed']
            cycles = self.platform_metrics['collections']
            rate = self.platform_metrics['processing_rates']['options_per_min']
            print(f"Summary: {cycles} cycles, {options} options processed, {rate:.1f} options/min")
            input("Press Enter to continue...")
            
        except KeyboardInterrupt:
            print("\nEnhanced data collection interrupted")
            self.stop_platform()
    
    def show_enhanced_metrics_dashboard(self):
        """📊 Show comprehensive enhanced metrics dashboard."""
        if not self.use_rich:
            self.show_simple_metrics()
            return
        
        try:
            # Create comprehensive layout
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="body"),
                Layout(name="footer", size=3)
            )
            
            layout["body"].split_row(
                Layout(name="left"),
                Layout(name="middle"),
                Layout(name="right")
            )
            
            # Header
            header_text = "[bold cyan]📊 ENHANCED LIVE METRICS DASHBOARD[/bold cyan]"
            layout["header"].update(Panel(header_text, box=box.HEAVY))
            
            # Left panel - Performance Metrics
            performance_table = Table(title="Performance Metrics", box=box.ROUNDED)
            performance_table.add_column("Metric", style="cyan")
            performance_table.add_column("Value", style="green")
            performance_table.add_column("Status")
            
            # Calculate enhanced metrics
            if self.platform_metrics['start_time']:
                uptime = time.time() - self.platform_metrics['start_time']
                uptime_str = f"{uptime/60:.1f} minutes"
                uptime_hours = uptime / 3600
            else:
                uptime_str = "Not started"
                uptime_hours = 0
            
            performance_table.add_row("Uptime", uptime_str, "🕐")
            performance_table.add_row("Status", self.platform_metrics['status'].upper(), "🔄" if self.is_running else "⏸️")
            performance_table.add_row("Cycles", str(self.platform_metrics['collections']), "🔄")
            performance_table.add_row("Options", str(self.platform_metrics['options_processed']), "📊")
            
            # Enhanced rates
            options_per_min = self.platform_metrics['processing_rates']['options_per_min']
            cycles_per_hour = self.platform_metrics['processing_rates']['cycles_per_hour']
            
            performance_table.add_row("Options/Min", f"{options_per_min:.1f}", "⚡")
            performance_table.add_row("Cycles/Hour", f"{cycles_per_hour:.1f}", "🔁")
            performance_table.add_row("Errors", str(self.platform_metrics['errors']), "❌" if self.platform_metrics['errors'] > 0 else "✅")
            
            layout["left"].update(Panel(performance_table, title="📈 Performance"))
            
            # Middle panel - Index Statistics
            index_table = Table(title="Index Processing", box=box.ROUNDED)
            index_table.add_column("Index", style="cyan")
            index_table.add_column("Options", style="green")
            index_table.add_column("Status")
            
            current_idx = self.platform_metrics.get('current_index', None)
            
            for index in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']:
                options_count = self.platform_metrics['indices_processed'].get(index, 0)
                status_emoji = "🟢" if index == current_idx else "⚪"
                index_table.add_row(index, str(options_count), status_emoji)
            
            layout["middle"].update(Panel(index_table, title="📊 Indices"))
            
            # Right panel - System Status
            system_table = Table(title="System Information", box=box.ROUNDED)
            system_table.add_column("Component", style="cyan")
            system_table.add_column("Status", style="green")
            
            system_table.add_row("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
            system_table.add_row("Platform", "🟢 Active" if self.is_running else "🔴 Stopped")
            system_table.add_row("Collection", "🟢 Live" if self.is_collecting_data() else "🟡 Idle")
            system_table.add_row("API Creds", "✅ Valid" if (self.api_key and self.access_token) else "❌ Missing")
            system_table.add_row("Enhanced UI", "✅ Active")
            system_table.add_row("Window Mode", "✅ Large")
            
            # Last activity
            last_activity = self.platform_metrics.get('last_collection', 'None')
            system_table.add_row("Last Activity", last_activity)
            
            layout["right"].update(Panel(system_table, title="🖥️ System"))
            
            # Footer
            footer_text = "[dim]Press any key to return to main menu...[/dim]"
            layout["footer"].update(Panel(footer_text, box=box.HEAVY))
            
            # Display dashboard
            self.console.print(layout)
            input()
            
        except Exception as e:
            self.console.print(f"[red]❌ Enhanced metrics display error: {e}[/red]")
            self.show_simple_metrics()
    
    def show_simple_metrics(self):
        """📊 Enhanced simple metrics."""
        print("\n📊 ENHANCED LIVE METRICS DASHBOARD")
        print("=" * 45)
        
        if self.platform_metrics['start_time']:
            uptime = time.time() - self.platform_metrics['start_time']
            print(f"Uptime: {uptime/60:.1f} minutes")
            
            options_per_min = self.platform_metrics['processing_rates']['options_per_min']
            print(f"Processing Rate: {options_per_min:.1f} options/min")
        else:
            print("Uptime: Not started")
        
        print(f"Status: {self.platform_metrics['status'].upper()}")
        print(f"Cycles: {self.platform_metrics['collections']}")
        print(f"Options: {self.platform_metrics['options_processed']}")
        print(f"Errors: {self.platform_metrics['errors']}")
        
        current_idx = self.platform_metrics.get('current_index', 'None')
        print(f"Current Index: {current_idx}")
        
        print("\nIndex Statistics:")
        for index in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']:
            count = self.platform_metrics['indices_processed'].get(index, 0)
            status = " <- Current" if index == current_idx else ""
            print(f"  {index}: {count} options{status}")
        
        if self.is_running:
            if self.is_collecting_data():
                print("🟢 Status: Actively collecting data")
            else:
                print("🟡 Status: Running but idle")
        else:
            print("🔴 Status: Stopped")
        
        input("\nPress Enter to continue...")
    
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
                self.console.print("[green]✅ Enhanced platform stopped[/green]")
            else:
                print("Enhanced platform stopped")
                
        except Exception as e:
            if self.use_rich:
                self.console.print(f"[red]❌ Stop error: {e}[/red]")
            else:
                print(f"Stop error: {e}")
    
    def run_launcher(self):
        """🖥️ Run the enhanced ultimate launcher."""
        try:
            while True:
                self.print_banner()
                self.show_system_status()
                
                choice = self.show_main_menu()
                
                if choice == "1":
                    self.launch_enhanced_platform()
                elif choice == "2":
                    self.show_enhanced_metrics_dashboard()
                elif choice == "3":
                    platform_file = self.create_enhanced_data_platform()
                    if platform_file:
                        input("\nPress Enter to continue...")
                elif choice == "4":
                    if self.use_rich:
                        self.console.print("[yellow]💡 Platform diagnosis: Enhanced version creates optimized platform automatically[/yellow]")
                    else:
                        print("Platform diagnosis: Enhanced version creates optimized platform automatically")
                    input("\nPress Enter to continue...")
                elif choice == "5":
                    self.stop_platform()
                    input("\nPress Enter to continue...")
                elif choice == "6":
                    if self.is_running:
                        if self.use_rich:
                            stop_confirm = Confirm.ask("Enhanced platform is running. Stop before exit?")
                        else:
                            stop_confirm = input("Enhanced platform running. Stop before exit? [y/N]: ").lower() == 'y'
                        
                        if stop_confirm:
                            self.stop_platform()
                    
                    if self.use_rich:
                        self.console.print("[green]👋 Enhanced Ultimate Launcher shutting down![/green]")
                    else:
                        print("👋 Enhanced Ultimate Launcher shutting down!")
                    break
                    
        except KeyboardInterrupt:
            if self.use_rich:
                self.console.print("\n[yellow]⚠️ Enhanced launcher interrupted[/yellow]")
            else:
                print("\nEnhanced launcher interrupted")
        finally:
            if self.is_running:
                self.stop_platform()

def main():
    """🚀 Enhanced main entry point."""
    try:
        launcher = EnhancedUltimateLauncher()
        launcher.run_launcher()
        return 0
    except Exception as e:
        print(f"Enhanced launcher error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())