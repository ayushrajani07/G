#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultimate Storage-Enhanced Launcher - G6.1 Platform (FIXED EXIT VERSION)
Fixed exit handling with proper signal handlers and market hours awareness
"""

import os
import sys
import time
import random
import statistics
import signal
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque

# Rich imports
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich.align import Align
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Rich not available - using basic output")

# Global console and exit flag
CONSOLE = Console() if RICH_AVAILABLE else None
EXIT_FLAG = threading.Event()

@dataclass
class ColorCodedWarning:
    """Color-coded warning entry."""
    timestamp: datetime
    level: str
    category: str
    message: str
    
    def get_color_code(self) -> str:
        colors = {"INFO": "blue", "WARNING": "yellow", "ERROR": "red", "CRITICAL": "bold red"}
        return colors.get(self.level, "white")

@dataclass
class StorageMetrics:
    """Storage metrics with cumulative tracking."""
    timestamp: datetime
    
    # CSV Storage
    csv_files_created: int = 45
    csv_records_written: int = 45230
    csv_write_errors: int = 2
    csv_disk_usage_mb: float = 128.7
    total_csv_write_errors: int = 0  # Cumulative errors
    
    # InfluxDB Storage
    influxdb_points_written: int = 89450
    influxdb_write_success_rate: float = 99.8
    influxdb_success_rates: List[float] = field(default_factory=list)
    influxdb_connection_status: str = "healthy"
    influxdb_query_performance: float = 45.2
    
    # Backup Status
    backup_files_created: int = 12
    last_backup_time: str = "2024-12-26 14:30"
    backup_size_mb: float = 234.5

@dataclass
class EnhancedRollingDataPoint:
    """Enhanced data point with spot price."""
    timestamp: datetime
    index: str
    spot: float  # Spot price
    legs: int
    avg_legs: float
    success_rate: float
    symmetric_offsets: int
    asymmetric_offsets: int
    status: str
    description: str
    cycle_color: str

class MarketHoursManager:
    """Manages market hours and trading session awareness."""
    
    def __init__(self):
        """Initialize market hours manager."""
        self.market_start = "09:15"
        self.market_end = "15:30"
        
    def is_market_hours(self) -> bool:
        """Check if current time is within market hours."""
        now = datetime.now()
        current_time = now.time()
        
        # Skip weekends
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
            
        # Parse market hours
        start_time = datetime.strptime(self.market_start, "%H:%M").time()
        end_time = datetime.strptime(self.market_end, "%H:%M").time()
        
        return start_time <= current_time <= end_time
    
    def get_market_status(self) -> str:
        """Get current market status description."""
        if self.is_market_hours():
            return "🟢 MARKET OPEN"
        else:
            now = datetime.now()
            if now.weekday() >= 5:
                return "🔴 WEEKEND - Markets Closed"
            else:
                return "🔴 AFTER HOURS - Markets Closed"
    
    def time_to_market_open(self) -> str:
        """Get time remaining until market opens."""
        now = datetime.now()
        
        # If weekend, calculate time to Monday
        if now.weekday() >= 5:
            days_to_monday = 7 - now.weekday()
            next_monday = now + timedelta(days=days_to_monday)
            market_open = datetime.combine(next_monday.date(), 
                                         datetime.strptime(self.market_start, "%H:%M").time())
        else:
            # Same day or next day
            today_market = datetime.combine(now.date(), 
                                          datetime.strptime(self.market_start, "%H:%M").time())
            if now.time() > datetime.strptime(self.market_end, "%H:%M").time():
                # After market close, next day
                tomorrow = now + timedelta(days=1)
                market_open = datetime.combine(tomorrow.date(), 
                                             datetime.strptime(self.market_start, "%H:%M").time())
            else:
                market_open = today_market
        
        time_diff = market_open - now
        hours = int(time_diff.total_seconds() // 3600)
        minutes = int((time_diff.total_seconds() % 3600) // 60)
        
        return f"{hours}h {minutes}m"

class EnhancedRollingDataStream:
    """Enhanced rolling data stream with market hours awareness."""
    
    def __init__(self, max_entries: int = 35):
        """Initialize enhanced rolling data stream."""
        self.max_entries = max_entries
        self.data_points: deque = deque(maxlen=max_entries)
        self.indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
        self.cycle_count = 0
        self.market_manager = MarketHoursManager()
        
        # Day averages for each index
        self.day_averages = {
            'NIFTY': 47.3,
            'BANKNIFTY': 35.8,
            'FINNIFTY': 29.2,
            'MIDCPNIFTY': 25.7
        }
        
        # Spot price ranges for each index
        self.spot_ranges = {
            'NIFTY': (24000, 25500),
            'BANKNIFTY': (51000, 54000),
            'FINNIFTY': (23000, 24500),
            'MIDCPNIFTY': (12000, 13500)
        }
        
        # Alternating cycle colors
        self.cycle_colors = ["cyan", "white", "green", "yellow", "magenta", "blue"]
        
        # Failure reasons
        self.failure_reasons = [
            "API timeout", "Rate limit hit", "Data validation failed",
            "Network connectivity", "Market volatility", "Insufficient liquidity",
            "System overload", "Cache miss", "Processing delay", "Quality check failed"
        ]
    
    def get_cycle_color(self) -> str:
        """Get alternating color for cycle."""
        return self.cycle_colors[self.cycle_count % len(self.cycle_colors)]
    
    def simulate_enhanced_data_stream(self):
        """Simulate enhanced data stream with market hours consideration."""
        self.cycle_count += 1
        is_market_hours = self.market_manager.is_market_hours()
        
        for index in self.indices:
            # Generate spot price
            min_spot, max_spot = self.spot_ranges[index]
            if is_market_hours:
                # Normal volatility during market hours
                spot_price = random.uniform(min_spot, max_spot)
            else:
                # Reduced volatility outside market hours
                mid_price = (min_spot + max_spot) / 2
                spot_price = random.uniform(mid_price * 0.998, mid_price * 1.002)
            
            # Generate other metrics
            base_legs = int(self.day_averages[index])
            if is_market_hours:
                legs = base_legs + random.randint(-8, 12)
                success_rate = random.uniform(0.85, 0.99)
            else:
                # Reduced activity outside market hours
                legs = int(base_legs * 0.3) + random.randint(-3, 5)
                success_rate = random.uniform(0.80, 0.95)
            
            legs = max(5, legs)  # Minimum 5 legs
            
            # Generate offsets based on index
            if index == 'NIFTY':
                sym_offsets = random.randint(9, 13)
                asym_offsets = random.randint(4, 8)
            elif index == 'BANKNIFTY':
                sym_offsets = random.randint(9, 13)
                asym_offsets = random.randint(4, 7)
            elif index == 'FINNIFTY':
                sym_offsets = random.randint(7, 11)
                asym_offsets = random.randint(3, 6)
            else:  # MIDCPNIFTY
                sym_offsets = random.randint(7, 11)
                asym_offsets = random.randint(3, 6)
            
            # Determine status and description
            status = "✅" if success_rate >= 0.90 else "❌"
            description = ""
            if status == "❌":
                if not is_market_hours:
                    description = "Low activity" if random.random() < 0.5 else random.choice(self.failure_reasons)
                else:
                    description = random.choice(self.failure_reasons)
            
            # Create data point
            cycle_color = self.get_cycle_color()
            data_point = EnhancedRollingDataPoint(
                timestamp=datetime.now(),
                index=index,
                spot=spot_price,
                legs=legs,
                avg_legs=self.day_averages[index],
                success_rate=success_rate,
                symmetric_offsets=sym_offsets,
                asymmetric_offsets=asym_offsets,
                status=status,
                description=description,
                cycle_color=cycle_color
            )
            
            self.data_points.append(data_point)
    
    def get_recent_data(self, count: int = 35) -> List[EnhancedRollingDataPoint]:
        """Get recent data points for display."""
        return list(self.data_points)[-count:] if self.data_points else []

class StableMetricsCollector:
    """Stable metrics collector with proper exit handling."""
    
    def __init__(self):
        """Initialize stable metrics collector."""
        self.storage_metrics: deque = deque(maxlen=100)
        self.warnings: deque = deque(maxlen=200)
        self.running = False
        self.collector_thread = None
        self.csv_total_errors = 0
        self.influxdb_success_history = []
        self.start_time = time.time()
        
    def start_collection(self, interval: int = 15):
        """Start stable metrics collection."""
        if self.running:
            return
        
        self.running = True
        self.start_time = time.time()
        
        def collect_loop():
            while self.running and not EXIT_FLAG.is_set():
                try:
                    # Collect storage metrics
                    storage_metrics = self._collect_storage_metrics()
                    self.storage_metrics.append(storage_metrics)
                    
                    # Generate some warnings occasionally
                    if random.random() < 0.1:  # 10% chance
                        self._generate_sample_warning()
                    
                    # Check exit condition
                    if EXIT_FLAG.wait(timeout=interval):
                        break
                        
                except Exception as e:
                    self.add_warning("ERROR", "METRICS", f"Collection error: {str(e)}")
                    if EXIT_FLAG.wait(timeout=interval):
                        break
        
        self.collector_thread = threading.Thread(target=collect_loop, daemon=True)
        self.collector_thread.start()
    
    def stop_collection(self):
        """Stop metrics collection gracefully."""
        self.running = False
        EXIT_FLAG.set()
        
        # Wait for collector thread to finish
        if self.collector_thread and self.collector_thread.is_alive():
            self.collector_thread.join(timeout=2)
    
    def _collect_storage_metrics(self) -> StorageMetrics:
        """Collect realistic storage metrics."""
        uptime_hours = (time.time() - self.start_time) / 3600
        
        # CSV errors (occasional)
        current_csv_errors = random.randint(0, 2) if random.random() < 0.2 else 0
        self.csv_total_errors += current_csv_errors
        
        # InfluxDB success rate
        current_success_rate = random.uniform(99.2, 99.9)
        self.influxdb_success_history.append(current_success_rate)
        
        # Keep only recent history (last 100 samples)
        if len(self.influxdb_success_history) > 100:
            self.influxdb_success_history = self.influxdb_success_history[-100:]
        
        return StorageMetrics(
            timestamp=datetime.now(),
            
            # CSV Storage - grows over time
            csv_files_created=int(45 + uptime_hours * 5),
            csv_records_written=int(45230 + uptime_hours * 2000),
            csv_write_errors=current_csv_errors,
            csv_disk_usage_mb=round(128.7 + uptime_hours * 10.5, 1),
            total_csv_write_errors=self.csv_total_errors,
            
            # InfluxDB Storage
            influxdb_points_written=int(89450 + uptime_hours * 15000),
            influxdb_write_success_rate=current_success_rate,
            influxdb_success_rates=self.influxdb_success_history.copy(),
            influxdb_connection_status=random.choice(["healthy", "healthy", "healthy", "warning"]),
            influxdb_query_performance=random.uniform(35.0, 65.0),
            
            # Backup Status
            backup_files_created=int(12 + uptime_hours * 0.5),
            last_backup_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
            backup_size_mb=round(234.5 + uptime_hours * 25.0, 1)
        )
    
    def _generate_sample_warning(self):
        """Generate sample warnings for demonstration."""
        warning_types = [
            ("INFO", "SYSTEM", "System health check completed"),
            ("WARNING", "PERFORMANCE", f"API response time elevated: {random.uniform(2.0, 4.0):.2f}s"),
            ("ERROR", "DATA", f"Data validation failed for {random.choice(['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY'])}"),
            ("WARNING", "CACHE", f"Cache hit rate below optimal: {random.uniform(0.60, 0.75):.1%}"),
            ("INFO", "STORAGE", f"CSV backup completed: {random.randint(100, 500)} records"),
            ("WARNING", "STORAGE", "InfluxDB connection warning: high latency"),
            ("ERROR", "STORAGE", "CSV write error: permission denied"),
            ("INFO", "BACKUP", f"Automated backup created: {random.uniform(50, 200):.1f}MB"),
        ]
        
        level, category, message = random.choice(warning_types)
        self.add_warning(level, category, message)
    
    def add_warning(self, level: str, category: str, message: str):
        """Add color-coded warning to log."""
        try:
            warning = ColorCodedWarning(
                timestamp=datetime.now(),
                level=level,
                category=category,
                message=message
            )
            self.warnings.append(warning)
        except Exception:
            pass
    
    def get_current_storage_metrics(self) -> Optional[StorageMetrics]:
        """Get most recent storage metrics."""
        return self.storage_metrics[-1] if self.storage_metrics else None
    
    def get_recent_warnings(self, count: int = 20) -> List[ColorCodedWarning]:
        """Get recent color-coded warning entries."""
        return list(self.warnings)[-count:] if self.warnings else []

class UltimateFixedLauncher:
    """Ultimate launcher with proper exit handling and market hours awareness."""
    
    def __init__(self):
        """Initialize the fixed launcher."""
        self.console = CONSOLE if RICH_AVAILABLE else None
        self.data_stream = EnhancedRollingDataStream()
        self.metrics_collector = StableMetricsCollector()
        self.market_manager = MarketHoursManager()
        
        # Runtime state
        self.running = False
        self.data_collection_active = False
        
        # Layout components
        self.layout = None
        self.live_display = None
        
        # Display update control
        self.last_update = time.time()
        
        # Setup signal handlers for graceful exit
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful exit."""
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}. Initiating graceful shutdown...")
            self.running = False
            EXIT_FLAG.set()
            
            # Stop metrics collection
            if self.metrics_collector:
                self.metrics_collector.stop_collection()
            
            # Exit after a short delay to allow cleanup
            import threading
            def delayed_exit():
                time.sleep(2)
                if RICH_AVAILABLE and CONSOLE:
                    CONSOLE.print("\n✅ [green]Platform shutdown complete[/green]")
                    CONSOLE.print("👋 [cyan]Thanks for using G6.1 Platform![/cyan]")
                else:
                    print("\n✅ Platform shutdown complete")
                    print("👋 Thanks for using G6.1 Platform!")
                os._exit(0)
            
            threading.Thread(target=delayed_exit, daemon=True).start()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
        
        # For Windows compatibility
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)  # Ctrl+Break on Windows
    
    def setup_layout(self):
        """Setup the enhanced monitoring layout."""
        if not RICH_AVAILABLE:
            return None
        
        try:
            self.layout = Layout()
            
            # Split main layout into header, body, and footer
            self.layout.split_column(
                Layout(name="header", size=3),
                Layout(name="body"),
                Layout(name="footer", size=3)
            )
            
            # Split body into 3 columns: data (3), metrics (2), warnings (1.5)
            self.layout["body"].split_row(
                Layout(name="left_panel", ratio=3),      # Data stream
                Layout(name="middle_panel", ratio=2),    # Metrics tables 
                Layout(name="right_panel", ratio=1.5)    # Warnings (wider for full logs)
            )
            
            # Middle panel: Split for two metrics tables
            self.layout["middle_panel"].split_column(
                Layout(name="sys_metrics", ratio=1),     # System metrics
                Layout(name="storage_metrics", ratio=1)  # Storage metrics
            )
            
            # Initialize with empty panels
            self.layout["header"].update(Panel("", title="Header", border_style="blue"))
            self.layout["left_panel"].update(Panel("", title="📈 Enhanced Rolling Live Data Stream", border_style="blue"))
            self.layout["sys_metrics"].update(Panel("", title="⚡ System & Performance Metrics", border_style="green"))
            self.layout["storage_metrics"].update(Panel("", title="💾 Storage Metrics", border_style="magenta"))
            self.layout["right_panel"].update(Panel("", title="⚠️  Color-Coded Warnings Log", border_style="yellow"))
            self.layout["footer"].update(Panel("", title="Footer", border_style="blue"))
            
            return self.layout
        except Exception as e:
            print(f"❌ Error setting up layout: {e}")
            return None
    
    def _create_header(self) -> Panel:
        """Create header panel with market status."""
        try:
            market_status = self.market_manager.get_market_status()
            
            header_text = Text()
            header_text.append("🚀 G6.1 Fixed Platform", style="bold blue")
            header_text.append(" | ")
            header_text.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
            header_text.append(" | ")
            header_text.append(market_status, style="green" if "OPEN" in market_status else "red")
            
            if not self.market_manager.is_market_hours():
                time_to_open = self.market_manager.time_to_market_open()
                header_text.append(f" | Opens in: {time_to_open}", style="yellow")
            
            return Panel(Align.center(header_text), box=box.HEAVY)
        except Exception:
            return Panel(Align.center("🚀 G6.1 Fixed Platform"), box=box.HEAVY)
    
    def _create_footer(self) -> Panel:
        """Create footer panel with exit instructions."""
        try:
            footer_text = "[dim]Press Ctrl+C to exit gracefully | Enhanced data stream + storage metrics active | Updates every 15s[/dim]"
            return Panel(Align.center(footer_text), box=box.HEAVY)
        except Exception:
            return Panel(Align.center("[dim]Press Ctrl+C to exit gracefully[/dim]"), box=box.HEAVY)
    
    def _update_data_panel(self):
        """Update rolling data stream panel with spot prices."""
        try:
            # Get recent data points (35 updates)
            recent_data = self.data_stream.get_recent_data(35)
            
            if not recent_data:
                empty_panel = Panel(
                    Align.center("📊 Waiting for enhanced data stream...\n\n[dim]No data points yet[/dim]"),
                    title="📈 Enhanced Rolling Live Data Stream", 
                    border_style="blue"
                )
                return empty_panel
            
            # Create rolling data table with spot prices
            data_table = Table(
                title=f"Enhanced Rolling Live Data Stream - Last {len(recent_data)} Updates",
                box=box.SIMPLE,
                show_lines=False,
                title_justify="center"
            )
            
            # Add columns with spot price after index
            data_table.add_column("Time", style="dim", width=8)
            data_table.add_column("Index", style="cyan bold", width=10)
            data_table.add_column("Spot", style="bright_green bold", width=8)  # NEW spot column
            data_table.add_column("Legs", style="green", width=6)
            data_table.add_column("AVG", style="blue", width=6)
            data_table.add_column("Success", style="yellow", width=8)
            data_table.add_column("Sym Off", style="magenta", width=7)
            data_table.add_column("Asym Off", style="cyan", width=8)
            data_table.add_column("Status", style="bold", width=6)
            data_table.add_column("Description", style="red", width=15)
            
            # Add data rows
            for data_point in recent_data:
                time_str = data_point.timestamp.strftime("%H:%M:%S")
                spot_str = f"{data_point.spot:.0f}"  # Format spot price
                legs_str = str(data_point.legs)
                avg_str = f"{data_point.avg_legs:.1f}"
                success_str = f"{data_point.success_rate:.1%}"
                sym_off_str = str(data_point.symmetric_offsets)
                asym_off_str = str(data_point.asymmetric_offsets)
                description_str = data_point.description if data_point.description else "-"
                
                data_table.add_row(
                    time_str,
                    data_point.index,
                    spot_str,  # Spot price
                    legs_str,
                    avg_str,
                    success_str,
                    sym_off_str,
                    asym_off_str,
                    data_point.status,
                    description_str,
                    style=data_point.cycle_color
                )
            
            # Enhanced summary
            if recent_data:
                total_legs = sum(dp.legs for dp in recent_data)
                avg_success = sum(dp.success_rate for dp in recent_data) / len(recent_data)
                total_sym_offsets = sum(dp.symmetric_offsets for dp in recent_data)
                total_asym_offsets = sum(dp.asymmetric_offsets for dp in recent_data)
                avg_throughput = total_legs / len(recent_data)
                
                summary_text = Text()
                summary_text.append(f"📊 Enhanced Stream Summary: ", style="dim")
                summary_text.append(f"{total_legs} legs", style="bold green")
                summary_text.append(f" | {avg_success:.1%} success", style="bold yellow")
                summary_text.append(f" | {total_sym_offsets} sym offs", style="bold magenta")
                summary_text.append(f" | {total_asym_offsets} asym offs", style="bold cyan")
                summary_text.append(f" | {avg_throughput:.1f} avg legs/update", style="bold white")
                
                stream_panel = Panel(
                    data_table,
                    title="📈 Enhanced Rolling Live Data Stream",
                    border_style="blue",
                    subtitle=summary_text
                )
            else:
                stream_panel = Panel(
                    data_table,
                    title="📈 Enhanced Rolling Live Data Stream",
                    border_style="blue"
                )
            
            return stream_panel
        
        except Exception as e:
            error_panel = Panel(
                f"⚠️ Data stream error\n\n[dim]{str(e)[:100]}...[/dim]",
                title="📈 Enhanced Rolling Live Data Stream",
                border_style="red"
            )
            return error_panel
    
    def _update_sys_metrics_panel(self):
        """Update system metrics panel (reduced width)."""
        try:
            # Create system metrics table (reduced width by 10 chars)
            metrics_table = Table(
                title="System & Performance", 
                box=box.SIMPLE, 
                show_lines=False,
                title_justify="center",
                width=40  # Reduced from 50
            )
            metrics_table.add_column("Category", style="cyan bold", width=10)
            metrics_table.add_column("Metric", style="white", width=12)  # Reduced
            metrics_table.add_column("Value", style="green bold", width=8)  # Reduced
            metrics_table.add_column("Status", style="yellow", width=6)
            
            # Sample system metrics
            metrics_table.add_row("Resource", "CPU Usage", f"{random.uniform(10, 25):.1f}%", "🟢")
            metrics_table.add_row("", "Memory", f"{random.uniform(45, 75):.1f}%", "🟢")
            metrics_table.add_row("", "Threads", str(random.randint(6, 12)), "🟢")
            
            metrics_table.add_row("Timing", "API Resp", f"{random.uniform(0.5, 2.5):.2f}s", "🟢")
            metrics_table.add_row("", "Collection", f"{random.uniform(12, 18):.1f}s", "🟢")
            
            metrics_table.add_row("Throughput", "Opts/Sec", f"{random.uniform(15, 30):.1f}", "🟢")
            metrics_table.add_row("", "Req/Min", f"{random.randint(80, 120)}", "🟢")
            
            metrics_table.add_row("Success", "API Succ", f"{random.uniform(0.95, 0.99):.1%}", "🟢")
            metrics_table.add_row("", "Overall", f"{random.uniform(0.92, 0.98):.1%}", "🟢")
            
            metrics_table.add_row("Cache", "Hit Rate", f"{random.uniform(0.78, 0.92):.1%}", "🟢")
            
            uptime_hours = (time.time() - self.metrics_collector.start_time) / 3600
            summary_text = Text()
            summary_text.append(f"🕐 Uptime: ", style="dim")
            summary_text.append(f"{uptime_hours:.1f}h", style="bold green")
            
            return Panel(
                metrics_table, 
                title="⚡ System & Performance Metrics", 
                border_style="green",
                subtitle=summary_text
            )
        
        except Exception as e:
            return Panel(f"⚠️ System metrics error\n\n[dim]{str(e)[:50]}...[/dim]", 
                        title="⚡ System & Performance Metrics", border_style="red")
    
    def _update_storage_metrics_panel(self):
        """Update storage metrics panel (reduced width)."""
        try:
            storage_metrics = self.metrics_collector.get_current_storage_metrics()
            
            if not storage_metrics:
                return Panel("💾 Collecting storage metrics...", 
                           title="💾 Storage Metrics", border_style="magenta")
            
            # Create storage metrics table (reduced width by 10 chars)
            storage_table = Table(
                title="Storage & Backup", 
                box=box.SIMPLE, 
                show_lines=False,
                title_justify="center",
                width=40  # Reduced from 50
            )
            storage_table.add_column("Category", style="magenta bold", width=8)
            storage_table.add_column("Metric", style="white", width=12)  # Reduced
            storage_table.add_column("Value", style="green bold", width=10)  # Reduced
            storage_table.add_column("Status", style="yellow", width=6)
            
            # CSV Storage Metrics
            storage_table.add_row("CSV", "Files", str(storage_metrics.csv_files_created), "🟢")
            storage_table.add_row("", "Records", f"{storage_metrics.csv_records_written:,}", "🟢")
            storage_table.add_row("", "Tot Errors", str(storage_metrics.total_csv_write_errors),  # NEW: Total CSV errors
                                "🟢" if storage_metrics.total_csv_write_errors == 0 else "🟡" if storage_metrics.total_csv_write_errors < 10 else "🔴")
            storage_table.add_row("", "Disk MB", f"{storage_metrics.csv_disk_usage_mb:.1f}", "🟢")
            
            # InfluxDB Storage Metrics
            influx_status_icon = "🟢" if storage_metrics.influxdb_connection_status == "healthy" else "🟡"
            storage_table.add_row("InfluxDB", "Points", f"{storage_metrics.influxdb_points_written:,}", "🟢")
            
            # Calculate average success rate
            if storage_metrics.influxdb_success_rates:
                avg_success = sum(storage_metrics.influxdb_success_rates) / len(storage_metrics.influxdb_success_rates)
                storage_table.add_row("", "Avg Succ", f"{avg_success:.1f}%",  # NEW: Average InfluxDB success
                                    "🟢" if avg_success > 99.0 else "🟡" if avg_success > 95.0 else "🔴")
            else:
                storage_table.add_row("", "Avg Succ", "N/A", "🟡")
            
            storage_table.add_row("", "Connection", storage_metrics.influxdb_connection_status, influx_status_icon)
            storage_table.add_row("", "Query ms", f"{storage_metrics.influxdb_query_performance:.1f}", 
                                "🟢" if storage_metrics.influxdb_query_performance < 100 else "🟡")
            
            # Backup Status
            storage_table.add_row("Backup", "Files", str(storage_metrics.backup_files_created), "🟢")
            storage_table.add_row("", "Size MB", f"{storage_metrics.backup_size_mb:.1f}", "🟢")
            
            # Storage summary
            total_storage = storage_metrics.csv_disk_usage_mb + storage_metrics.backup_size_mb
            summary_text = Text()
            summary_text.append(f"💾 Total: ", style="dim")
            summary_text.append(f"{total_storage:.1f}MB", style="bold magenta")
            summary_text.append(f" | ", style="dim")
            summary_text.append(f"{storage_metrics.influxdb_connection_status}", 
                               style="bold green" if storage_metrics.influxdb_connection_status == "healthy" else "bold yellow")
            
            return Panel(
                storage_table, 
                title="💾 Storage Metrics", 
                border_style="magenta",
                subtitle=summary_text
            )
        
        except Exception as e:
            return Panel(f"⚠️ Storage error\n\n[dim]{str(e)[:50]}...[/dim]", 
                        title="💾 Storage Metrics", border_style="red")
    
    def _update_warnings_panel(self):
        """Update warnings panel (increased width for full logs)."""
        try:
            warnings = self.metrics_collector.get_recent_warnings(25)  # More warnings due to wider panel
            
            if not warnings:
                no_warnings_text = Text()
                no_warnings_text.append("✅ No warnings detected\n", style="green bold")
                no_warnings_text.append("🔍 All systems normal\n", style="dim")
                no_warnings_text.append("📊 Monitoring active", style="blue")
                
                return Panel(
                    no_warnings_text,
                    title="⚠️  Color-Coded Warnings Log",
                    border_style="yellow"
                )
            
            # Count warnings by level
            warning_counts = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
            for warning in warnings:
                warning_counts[warning.level] += 1
            
            # Create warning content (wider panel for full messages)
            warning_content = Text()
            
            # Summary header
            summary_parts = []
            if warning_counts["CRITICAL"] > 0:
                summary_parts.append(f"🚨 {warning_counts['CRITICAL']} CRITICAL")
            if warning_counts["ERROR"] > 0:
                summary_parts.append(f"❌ {warning_counts['ERROR']} ERROR")
            if warning_counts["WARNING"] > 0:
                summary_parts.append(f"⚠️ {warning_counts['WARNING']} WARNING")
            if warning_counts["INFO"] > 0:
                summary_parts.append(f"ℹ️ {warning_counts['INFO']} INFO")
            
            if summary_parts:
                warning_content.append(" ".join(summary_parts), style="bold")
                warning_content.append("\n" + "─" * 50 + "\n", style="dim")
            
            # Recent warnings with full messages (wider panel allows full text)
            for warning in warnings[-20:]:  # Show more warnings
                color = warning.get_color_code()
                time_str = warning.timestamp.strftime("%H:%M:%S")
                
                warning_content.append(f"{warning.level}", style=f"{color} bold")
                warning_content.append(f" [{warning.category}] ", style="cyan")
                warning_content.append(f"{time_str}: ", style="dim")
                warning_content.append(f"{warning.message}\n", style="white")  # Full message now fits
            
            return Panel(
                warning_content, 
                title="⚠️  Color-Coded Warnings Log", 
                border_style="yellow"
            )
        
        except Exception as e:
            return Panel(f"⚠️ Warning error\n\n[dim]{str(e)[:50]}...[/dim]", 
                        title="⚠️  Color-Coded Warnings Log", border_style="red")
    
    def _safe_update_panel(self, panel_name: str, new_panel: Panel):
        """Safely update panel to prevent flickering."""
        try:
            if self.layout and new_panel:
                self.layout[panel_name].update(new_panel)
        except Exception:
            pass
    
    def run_monitoring_loop(self):
        """Run the fixed monitoring loop with proper exit handling."""
        if not RICH_AVAILABLE:
            self._run_basic_monitoring()
            return
        
        # Setup layout
        layout = self.setup_layout()
        if not layout:
            print("❌ Failed to setup layout")
            return
        
        # Start metrics collection
        self.metrics_collector.start_collection(interval=15)
        self.data_collection_active = True
        
        try:
            # Use Rich Live display
            with Live(
                layout, 
                refresh_per_second=0.25,
                screen=False,
                auto_refresh=False
            ) as live:
                self.live_display = live
                
                while self.running and not EXIT_FLAG.is_set():
                    try:
                        current_time = time.time()
                        
                        # Update display every 15 seconds
                        if current_time - self.last_update >= 15.0:
                            
                            # Generate data stream
                            self.data_stream.simulate_enhanced_data_stream()
                            
                            # Create new panels
                            new_header = self._create_header()
                            new_data_panel = self._update_data_panel()
                            new_sys_metrics = self._update_sys_metrics_panel()
                            new_storage_metrics = self._update_storage_metrics_panel()
                            new_warnings = self._update_warnings_panel()
                            new_footer = self._create_footer()
                            
                            # Update panels
                            self._safe_update_panel("header", new_header)
                            self._safe_update_panel("left_panel", new_data_panel)
                            self._safe_update_panel("sys_metrics", new_sys_metrics)
                            self._safe_update_panel("storage_metrics", new_storage_metrics)
                            self._safe_update_panel("right_panel", new_warnings)
                            self._safe_update_panel("footer", new_footer)
                            
                            live.refresh()
                            self.last_update = current_time
                        
                        # Check exit condition
                        if EXIT_FLAG.wait(timeout=2.0):
                            break
                            
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        self.metrics_collector.add_warning("ERROR", "DISPLAY", f"Display error: {str(e)}")
                        if EXIT_FLAG.wait(timeout=5.0):
                            break
                        
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
        finally:
            self.running = False
            EXIT_FLAG.set()
            self.metrics_collector.stop_collection()
    
    def _run_basic_monitoring(self):
        """Run basic monitoring without Rich."""
        print("\n" + "="*60)
        print("📊 G6.1 FIXED PLATFORM MONITORING (Basic Mode)")
        print("="*60)
        print("Enhanced data stream + storage metrics + market hours active")
        print("Press Ctrl+C to exit gracefully\n")
        
        self.metrics_collector.start_collection(interval=15)
        self.data_collection_active = True
        
        try:
            cycle = 0
            while self.running and not EXIT_FLAG.is_set():
                cycle += 1
                market_status = self.market_manager.get_market_status()
                print(f"\n--- Fixed Update {cycle} at {datetime.now().strftime('%H:%M:%S')} | {market_status} ---")
                
                # Generate data
                self.data_stream.simulate_enhanced_data_stream()
                
                # Show recent data
                recent_data = self.data_stream.get_recent_data(3)
                if recent_data:
                    print("📈 Enhanced Data with Spot Prices:")
                    for dp in recent_data:
                        time_str = dp.timestamp.strftime("%H:%M:%S")
                        print(f"  {time_str} | {dp.index} | Spot: {dp.spot:.0f} | {dp.legs} legs | {dp.success_rate:.1%} | {dp.status}")
                
                # Storage metrics
                storage_metrics = self.metrics_collector.get_current_storage_metrics()
                if storage_metrics:
                    avg_influx = sum(storage_metrics.influxdb_success_rates) / len(storage_metrics.influxdb_success_rates) if storage_metrics.influxdb_success_rates else 0
                    print(f"💾 Storage: CSV Total Errors {storage_metrics.total_csv_write_errors} | InfluxDB Avg Success {avg_influx:.1f}%")
                
                # Check exit condition
                if EXIT_FLAG.wait(timeout=15.0):
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            EXIT_FLAG.set()
            self.metrics_collector.stop_collection()
            print("\n✅ Fixed platform shutdown complete")
    
    def launch(self):
        """Main launch method with proper exit handling."""
        try:
            # Print startup message
            if RICH_AVAILABLE:
                self.console.print("\n🚀 [bold green]Starting G6.1 Fixed Platform...[/bold green]")
                self.console.print("📊 [cyan]Enhanced data stream + spot prices + market hours awareness[/cyan]")
                self.console.print("💾 [magenta]CSV total errors + InfluxDB avg success tracking[/magenta]")
                self.console.print("⚠️  [yellow]Wider warning panel for complete logs[/yellow]")
                self.console.print("🛑 [red]Press Ctrl+C for graceful exit[/red]\n")
            else:
                print("\n🚀 Starting G6.1 Fixed Platform...")
                print("📊 Enhanced data stream + storage metrics active")
                print("🛑 Press Ctrl+C for graceful exit\n")
            
            self.running = True
            
            # Launch monitoring interface
            self.run_monitoring_loop()
            
            return True
            
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested by user")
            return True
        except Exception as e:
            print(f"\n❌ Launch error: {str(e)}")
            return False

def main():
    """Main entry point with proper exit handling."""
    try:
        launcher = UltimateFixedLauncher()
        success = launcher.launch()
        
        if success:
            print("\n👋 Thanks for using G6.1 Fixed Platform!")
        else:
            print("\n❌ Platform failed to start properly")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Graceful shutdown complete")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()