#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🖥️ Terminal Interface - G6 Platform v3.0
Rich terminal user interface for the G6 platform.

Features:
- Live metrics dashboard with real-time updates
- Interactive platform status monitoring
- Rich console output with colors and formatting
- Progress bars and status indicators
- Responsive layout and design
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Rich imports with fallback
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich.columns import Columns
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

import logging

logger = logging.getLogger(__name__)

class TerminalInterface:
    """
    🖥️ Rich terminal interface for G6 platform monitoring and control.
    
    Provides an interactive terminal interface with live updates,
    metrics dashboards, and real-time platform monitoring.
    """
    
    def __init__(self, config_manager=None):
        """Initialize terminal interface."""
        if not RICH_AVAILABLE:
            raise ImportError("Rich library not available. Install with: pip install rich")
        
        self.console = Console()
        self.config_manager = config_manager
        
        # Interface state
        self._stop_updates = threading.Event()
        self._update_thread: Optional[threading.Thread] = None
        
        logger.info("🖥️ Terminal interface initialized")
    
    def show_live_dashboard(self, platform) -> None:
        """Show live platform dashboard."""
        if not RICH_AVAILABLE:
            print("Live dashboard requires Rich library")
            return
        
        # Create layout
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
        
        layout["left"].split_column(
            Layout(name="status"),
            Layout(name="metrics")
        )
        
        layout["right"].split_column(
            Layout(name="indices"),
            Layout(name="health")
        )
        
        def update_dashboard():
            """Update dashboard content."""
            try:
                # Get platform data
                status = platform.get_status()
                health = platform.get_health()
                
                # Header
                header_text = Text()
                header_text.append("🚀 G6 Options Analytics Platform - Live Dashboard", style="bold blue")
                header_text.append(f" | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
                layout["header"].update(Panel(Align.center(header_text)))
                
                # Status panel
                status_table = Table(show_header=False, box=None)
                status_table.add_column("Key", style="cyan")
                status_table.add_column("Value", style="green")
                
                status_color = "green" if status['status'] == 'running' else "yellow"
                status_table.add_row("Status", f"[{status_color}]{status['status'].upper()}[/{status_color}]")
                status_table.add_row("Uptime", f"{status['uptime_seconds']:.0f}s")
                status_table.add_row("Cycles", str(status['cycles_completed']))
                status_table.add_row("Success Rate", f"{status['success_rate']:.1f}%")
                
                layout["status"].update(Panel(status_table, title="Platform Status"))
                
                # Metrics panel
                metrics_table = Table(show_header=False, box=None)
                metrics_table.add_column("Metric", style="cyan")
                metrics_table.add_column("Value", style="magenta")
                
                metrics_table.add_row("Options Processed", str(status['total_options_processed']))
                metrics_table.add_row("Avg Cycle Time", f"{status['average_cycle_time']:.2f}s")
                metrics_table.add_row("Errors", str(status['errors_count']))
                
                if status['last_cycle_at']:
                    last_cycle = datetime.fromisoformat(status['last_cycle_at'])
                    time_since = (datetime.now() - last_cycle).total_seconds()
                    metrics_table.add_row("Last Cycle", f"{time_since:.0f}s ago")
                
                layout["metrics"].update(Panel(metrics_table, title="Performance Metrics"))
                
                # Health panel
                health_status = health.get('status', 'unknown')
                health_color = "green" if health_status == 'healthy' else "red"
                
                health_text = Text()
                health_text.append(f"Overall: ", style="white")
                health_text.append(f"{health_status.upper()}", style=health_color)
                
                if 'checks' in health:
                    health_text.append("\n\nComponents:\n", style="white")
                    for name, check in health['checks'].items():
                        check_status = check.get('status', 'unknown')
                        check_color = "green" if check_status == 'healthy' else "red"
                        health_text.append(f"• {name}: ", style="dim")
                        health_text.append(f"{check_status}", style=check_color)
                        health_text.append("\n")
                
                layout["health"].update(Panel(health_text, title="Health Status"))
                
                # Component status
                components = status.get('components', {})
                comp_table = Table(show_header=True, box=None)
                comp_table.add_column("Component", style="cyan")
                comp_table.add_column("Status", style="green")
                
                comp_table.add_row("API Provider", "✅" if components.get('api_provider') else "❌")
                comp_table.add_row("Collectors", str(components.get('collectors', 0)))
                comp_table.add_row("Storage", str(components.get('storage_backends', 0)))
                comp_table.add_row("Analytics", "✅" if components.get('analytics_engine') else "❌")
                
                monitoring = components.get('monitoring', {})
                comp_table.add_row("Health Monitor", "✅" if monitoring.get('health') else "❌")
                comp_table.add_row("Performance Monitor", "✅" if monitoring.get('performance') else "❌")
                comp_table.add_row("Metrics System", "✅" if monitoring.get('metrics') else "❌")
                
                layout["indices"].update(Panel(comp_table, title="Components"))
                
                # Footer
                footer_text = Text()
                footer_text.append("Press ", style="dim")
                footer_text.append("Ctrl+C", style="bold red")
                footer_text.append(" to stop | ", style="dim")
                footer_text.append("ESC", style="bold yellow")
                footer_text.append(" to exit dashboard", style="dim")
                layout["footer"].update(Panel(Align.center(footer_text)))
                
                return layout
                
            except Exception as e:
                logger.error(f"🔴 Dashboard update error: {e}")
                error_panel = Panel(f"Error updating dashboard: {e}", style="red")
                return Layout(error_panel)
        
        # Show live dashboard
        try:
            with Live(update_dashboard(), refresh_per_second=2, screen=True) as live:
                while True:
                    time.sleep(0.5)
                    live.update(update_dashboard())
        except KeyboardInterrupt:
            self.console.print("\n🛑 Dashboard stopped by user", style="yellow")
    
    def show_metrics_dashboard(self, platform) -> None:
        """Show detailed metrics dashboard."""
        if not RICH_AVAILABLE:
            print("Metrics dashboard requires Rich library")
            return
        
        def create_metrics_layout():
            """Create metrics layout."""
            try:
                # Get metrics
                metrics = platform.get_metrics() if hasattr(platform, 'get_metrics') else {}
                
                # Create main table
                table = Table(title="📈 Platform Metrics", show_header=True)
                table.add_column("Metric", style="cyan", width=30)
                table.add_column("Current Value", style="green", width=15)
                table.add_column("Unit", style="yellow", width=10)
                table.add_column("Description", style="white")
                
                # Add metrics rows
                if metrics:
                    for name, data in metrics.items():
                        current_value = data.get('current_value', 'N/A')
                        unit = data.get('unit', '')
                        description = data.get('description', '')
                        
                        table.add_row(name, str(current_value), unit, description)
                else:
                    table.add_row("No metrics available", "", "", "")
                
                return table
                
            except Exception as e:
                return Panel(f"Error loading metrics: {e}", style="red")
        
        # Show metrics with auto-refresh
        try:
            with Live(create_metrics_layout(), refresh_per_second=1) as live:
                while True:
                    time.sleep(1)
                    live.update(create_metrics_layout())
        except KeyboardInterrupt:
            self.console.print("\n🛑 Metrics dashboard stopped", style="yellow")
    
    def show_progress_bar(self, 
                         description: str,
                         total: int,
                         update_callback: callable = None) -> Progress:
        """Show progress bar for long-running operations."""
        if not RICH_AVAILABLE:
            return None
        
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        )
        
        task = progress.add_task(description, total=total)
        
        return progress, task
    
    def display_table(self, 
                     title: str,
                     headers: List[str],
                     data: List[List[str]],
                     styles: List[str] = None) -> None:
        """Display a formatted table."""
        if not RICH_AVAILABLE:
            # Fallback text table
            print(f"\n{title}")
            print("=" * len(title))
            
            # Print headers
            header_row = " | ".join(headers)
            print(header_row)
            print("-" * len(header_row))
            
            # Print data rows
            for row in data:
                data_row = " | ".join(str(cell) for cell in row)
                print(data_row)
            
            return
        
        # Rich table
        table = Table(title=title, show_header=True)
        
        # Add columns
        for i, header in enumerate(headers):
            style = styles[i] if styles and i < len(styles) else "white"
            table.add_column(header, style=style)
        
        # Add rows
        for row in data:
            table.add_row(*[str(cell) for cell in row])
        
        self.console.print(table)
    
    def display_status_summary(self, status_data: Dict[str, Any]) -> None:
        """Display status summary in a formatted panel."""
        if not RICH_AVAILABLE:
            print("\nStatus Summary:")
            for key, value in status_data.items():
                print(f"  {key}: {value}")
            return
        
        # Create status text
        status_text = Text()
        
        for key, value in status_data.items():
            # Format key
            status_text.append(f"{key}: ", style="cyan")
            
            # Format value based on type
            if isinstance(value, bool):
                value_style = "green" if value else "red"
                value_str = "✅" if value else "❌"
            elif isinstance(value, (int, float)):
                value_style = "magenta"
                value_str = str(value)
            else:
                value_style = "white"
                value_str = str(value)
            
            status_text.append(f"{value_str}\n", style=value_style)
        
        panel = Panel(status_text, title="Status Summary", expand=False)
        self.console.print(panel)
    
    def prompt_user(self, 
                   message: str,
                   choices: List[str] = None,
                   default: str = None) -> str:
        """Prompt user for input with optional choices."""
        if choices:
            choices_str = "/".join(choices)
            if default:
                choices_str = choices_str.replace(default, f"[{default}]")
            prompt = f"{message} ({choices_str}): "
        else:
            prompt = f"{message}: "
        
        if RICH_AVAILABLE:
            response = self.console.input(prompt)
        else:
            response = input(prompt)
        
        return response.strip() or default or ""
    
    def show_error(self, message: str, details: str = None) -> None:
        """Display error message."""
        if RICH_AVAILABLE:
            error_text = Text()
            error_text.append("🔴 Error: ", style="bold red")
            error_text.append(message, style="red")
            
            if details:
                error_text.append(f"\nDetails: {details}", style="dim")
            
            panel = Panel(error_text, title="Error", border_style="red")
            self.console.print(panel)
        else:
            print(f"🔴 Error: {message}")
            if details:
                print(f"Details: {details}")
    
    def show_success(self, message: str) -> None:
        """Display success message."""
        if RICH_AVAILABLE:
            success_text = Text()
            success_text.append("✅ Success: ", style="bold green")
            success_text.append(message, style="green")
            
            panel = Panel(success_text, title="Success", border_style="green")
            self.console.print(panel)
        else:
            print(f"✅ Success: {message}")
    
    def show_warning(self, message: str) -> None:
        """Display warning message."""
        if RICH_AVAILABLE:
            warning_text = Text()
            warning_text.append("⚠️ Warning: ", style="bold yellow")
            warning_text.append(message, style="yellow")
            
            panel = Panel(warning_text, title="Warning", border_style="yellow")
            self.console.print(panel)
        else:
            print(f"⚠️ Warning: {message}")
    
    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        if RICH_AVAILABLE:
            self.console.clear()
        else:
            os.system('cls' if os.name == 'nt' else 'clear')
    
    def cleanup(self) -> None:
        """Cleanup terminal interface resources."""
        self._stop_updates.set()
        
        if self._update_thread and self._update_thread.is_alive():
            self._update_thread.join(timeout=2)
        
        logger.info("🖥️ Terminal interface cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass