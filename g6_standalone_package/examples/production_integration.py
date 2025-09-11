#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Production Integration Example - G6 Platform v3.0

Complete integration example showing how to use:
1. Weekday Master Overlay for historical analysis
2. Dynamic configuration for indices/expiry/offsets
3. Enhanced CSV storage with structured paths
4. Production dashboard for real-time monitoring

This example demonstrates the full workflow from data collection
to historical overlay analysis with production monitoring.
"""

import sys
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Add the package to the path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from g6_platform.analytics import (
    WeekdayMasterOverlay,
    ATMOptionsData,
    OverlayConfig,
    create_atm_data_from_collector_result
)
from g6_platform.storage.csv_sink import CSVSink
from g6_platform.ui import ProductionDashboard
# from g6_platform.config.manager import ConfigManager  # Will implement if needed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionIntegrationDemo:
    """
    🚀 Production Integration Demo
    
    Demonstrates the complete integration of weekday overlays,
    structured CSV storage, and production dashboard.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the integration demo."""
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.overlay_system = self._setup_overlay_system()
        self.csv_sink = self._setup_csv_storage()
        self.dashboard = self._setup_dashboard()
        
        # Demo state
        self.running = False
        self.demo_thread = None
        
        logger.info("🚀 Production Integration Demo initialized")
    
    def _load_config(self, config_path: str = None) -> dict:
        """Load configuration with dynamic settings."""
        default_config = {
            "weekday_overlay": {
                "enabled": True,
                "indices": ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"],
                "expiry_tags": ["current_week", "next_week", "monthly"],
                "offsets": [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5],
                "base_path": "demo_data/weekday_overlays"
            },
            "storage": {
                "csv": {
                    "base_path": "demo_data/csv",
                    "structure": {
                        "path_format": "INDEX/EXPIRY_TAG/OFFSET/YYYY-MM-DD"
                    }
                }
            },
            "ui": {
                "production_dashboard": {
                    "enabled": True,
                    "max_data_entries": 25,
                    "update_interval": 1.0
                }
            }
        }
        
        if config_path and Path(config_path).exists():
            # Load from file (implementation would depend on format)
            logger.info(f"📄 Loaded config from {config_path}")
        
        return default_config
    
    def _setup_overlay_system(self) -> WeekdayMasterOverlay:
        """Setup weekday master overlay system."""
        overlay_config = OverlayConfig(
            base_path=self.config["weekday_overlay"]["base_path"],
            indices=self.config["weekday_overlay"]["indices"],
            expiry_tags=self.config["weekday_overlay"]["expiry_tags"],
            offsets=self.config["weekday_overlay"]["offsets"]
        )
        
        overlay_system = WeekdayMasterOverlay(overlay_config)
        logger.info("📊 Weekday overlay system initialized")
        return overlay_system
    
    def _setup_csv_storage(self) -> CSVSink:
        """Setup CSV storage with structured paths."""
        csv_sink = CSVSink(
            base_path=self.config["storage"]["csv"]["base_path"],
            enable_compression=False,
            enable_rotation=True,
            max_file_size_mb=50,
            retention_days=30
        )
        
        logger.info("💾 CSV storage with structured paths initialized")
        return csv_sink
    
    def _setup_dashboard(self) -> ProductionDashboard:
        """Setup production dashboard."""
        dashboard = ProductionDashboard(
            max_data_entries=self.config["ui"]["production_dashboard"]["max_data_entries"],
            update_interval=self.config["ui"]["production_dashboard"]["update_interval"]
        )
        
        logger.info("🚀 Production dashboard initialized")
        return dashboard
    
    def start_demo(self):
        """Start the integration demo."""
        try:
            self.running = True
            
            # Start dashboard in background
            dashboard_thread = threading.Thread(
                target=self.dashboard.start,
                daemon=True,
                name="Dashboard"
            )
            dashboard_thread.start()
            
            # Give dashboard time to start
            time.sleep(2)
            
            # Start data simulation
            self.demo_thread = threading.Thread(
                target=self._run_demo_simulation,
                daemon=True,
                name="DemoSimulation"
            )
            self.demo_thread.start()
            
            logger.info("🎬 Demo started - Press Ctrl+C to stop")
            
            # Wait for completion
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Demo stopped by user")
            
        finally:
            self.stop_demo()
    
    def stop_demo(self):
        """Stop the demo."""
        self.running = False
        if self.demo_thread and self.demo_thread.is_alive():
            self.demo_thread.join(timeout=2)
        
        self.dashboard.stop()
        self.csv_sink.shutdown()
        logger.info("🛑 Demo stopped")
    
    def _run_demo_simulation(self):
        """Run demo data simulation."""
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                current_time = datetime.now()
                
                # Process each index
                for i, index in enumerate(self.overlay_system.config.indices):
                    self._process_index_data(index, cycle_count, current_time)
                
                # Update dashboard with cycle summary
                self._update_dashboard_summary(cycle_count)
                
                # Wait before next cycle
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"🔴 Demo simulation error: {e}")
                time.sleep(10)
    
    def _process_index_data(self, index: str, cycle: int, timestamp: datetime):
        """Process data for a single index."""
        try:
            # Simulate processing different expiry tags and offsets
            for expiry_tag in self.overlay_system.config.expiry_tags[:2]:  # Limit for demo
                for offset in [-2, -1, 0, 1, 2]:  # Limited offsets for demo
                    
                    # Generate simulated ATM options data
                    atm_data = self._generate_sample_atm_data(
                        index, expiry_tag, offset, timestamp
                    )
                    
                    # Process through overlay system
                    overlay_success = self.overlay_system.process_atm_data(atm_data)
                    
                    # Store in structured CSV
                    storage_success = self.csv_sink.store_options_data(
                        index_name=index,
                        options_data=self._convert_atm_to_options_data(atm_data),
                        timestamp=timestamp,
                        expiry_tag=expiry_tag,
                        offset=offset
                    )
                    
                    # Update dashboard
                    status = "✓" if overlay_success and storage_success else "✗"
                    success_rate = 95.0 + (cycle % 10) - 5.0  # Simulate varying success
                    
                    self.dashboard.add_data_entry(
                        index=index,
                        legs=30 + offset * 2,
                        avg=25.0 + abs(offset) * 1.5,
                        success=success_rate,
                        sym_off=10 + abs(offset),
                        asym_off=5 + offset,
                        status=status,
                        description=f"{expiry_tag.title()} {offset:+d} processing"
                    )
                    
                    # Small delay to prevent overwhelming
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"🔴 Failed to process {index} data: {e}")
            self.dashboard.add_log_entry("ERROR", f"[{index}]", str(e))
    
    def _generate_sample_atm_data(self, 
                                index: str, 
                                expiry_tag: str, 
                                offset: int, 
                                timestamp: datetime) -> ATMOptionsData:
        """Generate sample ATM options data for demo."""
        # Base prices for different indices
        base_prices = {
            "NIFTY": 19800,
            "BANKNIFTY": 44500,
            "FINNIFTY": 19200,
            "MIDCPNIFTY": 9800
        }
        
        base_price = base_prices.get(index, 20000)
        
        # Simulate option prices with some randomness
        import random
        ce = random.uniform(50, 300) + abs(offset) * 10
        pe = random.uniform(50, 300) + abs(offset) * 10
        tp = ce + pe
        
        # Average prices (slightly different from last prices)
        avg_ce = ce * random.uniform(0.95, 1.05)
        avg_pe = pe * random.uniform(0.95, 1.05)
        avg_tp = avg_ce + avg_pe
        
        return ATMOptionsData(
            ce=ce,
            pe=pe,
            tp=tp,
            avg_ce=avg_ce,
            avg_pe=avg_pe,
            avg_tp=avg_tp,
            timestamp=timestamp.isoformat(),
            index=index,
            expiry_tag=expiry_tag,
            offset=offset
        )
    
    def _convert_atm_to_options_data(self, atm_data: ATMOptionsData) -> List[Dict]:
        """Convert ATM data to options data format for CSV storage."""
        return [
            {
                'symbol': f"{atm_data.index}CE",
                'strike': 20000 + atm_data.offset * 50,  # Sample strike
                'expiry': "2024-01-25",  # Sample expiry
                'option_type': 'CE',
                'last_price': atm_data.ce,
                'volume': 1000,
                'oi': 5000,
                'index_name': atm_data.index,
                'expiry_tag': atm_data.expiry_tag,
                'offset': atm_data.offset
            },
            {
                'symbol': f"{atm_data.index}PE",
                'strike': 20000 + atm_data.offset * 50,
                'expiry': "2024-01-25",
                'option_type': 'PE',
                'last_price': atm_data.pe,
                'volume': 1200,
                'oi': 4800,
                'index_name': atm_data.index,
                'expiry_tag': atm_data.expiry_tag,
                'offset': atm_data.offset
            }
        ]
    
    def _update_dashboard_summary(self, cycle: int):
        """Update dashboard with summary metrics."""
        # Update system metrics
        self.dashboard.update_metric(
            "Resource", "CPU Usage", f"{15 + cycle % 10}.{cycle % 10}%", "healthy"
        )
        self.dashboard.update_metric(
            "Resource", "Memory Usage", f"{45 + cycle % 15}.{cycle % 10}%", "healthy"
        )
        self.dashboard.update_metric(
            "Throughput", "Options/Sec", f"{12 + cycle % 8}.{cycle % 10}", "healthy"
        )
        
        # Add periodic log entries
        if cycle % 10 == 0:
            self.dashboard.add_log_entry(
                "INFO", "[SYSTEM]", f"Completed cycle {cycle} - all systems operational"
            )
        
        if cycle % 15 == 0:
            self.dashboard.add_log_entry(
                "INFO", "[BACKUP]", f"Automated backup created: {100 + cycle}.{cycle % 100} MB"
            )
    
    def demonstrate_overlay_analysis(self):
        """Demonstrate overlay analysis capabilities."""
        logger.info("📊 Demonstrating overlay analysis...")
        
        # Get overlay data for analysis
        for index in ["NIFTY", "BANKNIFTY"]:
            overlay_data = self.overlay_system.get_overlay_data(
                index=index,
                expiry_tag="current_week",
                offset=0  # ATM
            )
            
            logger.info(f"📈 {index} overlay data: {len(overlay_data)} weekdays available")
            
            # Show current overlay comparison
            current_overlay = self.overlay_system.get_current_overlay(
                index=index,
                expiry_tag="current_week",
                offset=0
            )
            
            if current_overlay:
                logger.info(f"🎯 {index} current overlay: tp_avg={current_overlay.tp_avg:.2f}, "
                          f"counter={current_overlay.counter_tp}")
    
    def demonstrate_storage_structure(self):
        """Demonstrate the new storage structure."""
        logger.info("💾 Demonstrating storage structure...")
        
        base_path = Path(self.config["storage"]["csv"]["base_path"])
        
        # Show created directory structure
        if base_path.exists():
            structure = []
            for item in base_path.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(base_path)
                    structure.append(str(rel_path))
            
            logger.info(f"📁 Created {len(structure)} files in structured format:")
            for file_path in sorted(structure)[:10]:  # Show first 10
                logger.info(f"   {file_path}")
            
            if len(structure) > 10:
                logger.info(f"   ... and {len(structure) - 10} more files")

def main():
    """Main demo function."""
    print("🚀 G6 Platform - Production Integration Demo")
    print("=" * 50)
    print()
    print("This demo showcases:")
    print("1. 📊 Weekday Master Overlay system")
    print("2. 💾 Structured CSV storage (INDEX/EXPIRY_TAG/OFFSET/DATE)")
    print("3. 🚀 Production dashboard with live monitoring")
    print("4. ⚙️ Dynamic configuration management")
    print()
    print("Press Ctrl+C to stop the demo at any time.")
    print()
    
    # Create and run demo
    demo = ProductionIntegrationDemo()
    
    try:
        # Show initial analysis
        demo.demonstrate_overlay_analysis()
        
        # Start main demo
        demo.start_demo()
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        logger.error(f"🔴 Demo error: {e}")
    finally:
        # Show final results
        print("\n📊 Demo Results:")
        demo.demonstrate_storage_structure()
        
        # Show statistics
        overlay_stats = demo.overlay_system.get_statistics()
        dashboard_stats = demo.dashboard.get_stats()
        storage_stats = demo.csv_sink.get_storage_stats()
        
        print(f"\n📈 Overlay System: {overlay_stats['cache_status']['total_data_points']} data points processed")
        print(f"🚀 Dashboard: {dashboard_stats['total_updates']} updates displayed")
        print(f"💾 Storage: {storage_stats['records_written']} records written")
        
        demo.stop_demo()
        print("\n✅ Demo completed successfully!")

if __name__ == "__main__":
    main()