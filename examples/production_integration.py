#!/usr/bin/env python3
"""
G6 Analytics Platform - Production Integration Example

This example demonstrates how to integrate the G6 Platform
into a production trading system with proper error handling
and monitoring.
"""

import sys
import os
import time
import signal
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from g6_platform.core.platform import G6Platform
from g6_platform.config.manager import ConfigManager
from g6_platform.monitoring.health import HealthMonitor
from g6_platform.monitoring.metrics import MetricsCollector

class ProductionG6Platform:
    """Production-ready G6 Platform integration."""
    
    def __init__(self):
        self.platform = None
        self.health_monitor = None
        self.metrics_collector = None
        self.running = False
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.stop()
        
    def start(self):
        """Start the production platform."""
        try:
            print("🚀 Starting G6 Analytics Platform - Production Mode")
            print("=" * 55)
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Initialize configuration
            config_manager = ConfigManager()
            config = config_manager.load_config()
            
            # Initialize platform components
            self.platform = G6Platform(config)
            self.health_monitor = HealthMonitor()
            self.metrics_collector = MetricsCollector()
            
            # Start monitoring
            self.health_monitor.start()
            self.metrics_collector.start()
            
            # Start platform
            self.platform.start()
            
            self.running = True
            print("✅ Platform started successfully in production mode!")
            
            # Main monitoring loop
            self._monitoring_loop()
            
        except Exception as e:
            print(f"❌ Production startup error: {e}")
            self.stop()
            
    def _monitoring_loop(self):
        """Main monitoring and health check loop."""
        while self.running:
            try:
                # Check system health
                health_status = self.health_monitor.get_status()
                if not health_status.get('healthy', True):
                    print(f"⚠️ Health check failed: {health_status}")
                
                # Collect metrics
                metrics = self.metrics_collector.get_current_metrics()
                
                # Log status every 5 minutes
                current_time = datetime.now()
                if current_time.minute % 5 == 0 and current_time.second < 10:
                    print(f"📊 [{current_time.strftime('%H:%M:%S')}] "
                          f"Platform running - Metrics: {metrics}")
                
                time.sleep(10)  # Check every 10 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ Monitoring error: {e}")
                time.sleep(30)  # Wait longer on errors
                
    def stop(self):
        """Stop the platform gracefully."""
        self.running = False
        
        print("🛑 Stopping platform components...")
        
        if self.platform:
            self.platform.stop()
            
        if self.health_monitor:
            self.health_monitor.stop()
            
        if self.metrics_collector:
            self.metrics_collector.stop()
            
        print("✅ Platform stopped gracefully")

def main():
    """Production integration example."""
    
    production_platform = ProductionG6Platform()
    
    try:
        production_platform.start()
    except Exception as e:
        print(f"❌ Production error: {e}")
    finally:
        production_platform.stop()

if __name__ == "__main__":
    main()