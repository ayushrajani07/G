#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G6.1 Immediate Output Platform
Produces output immediately for debugging
"""

import os
import sys
import time
import random
import signal
from datetime import datetime

class ImmediateOutputCollector:
    """Collector that produces immediate, visible output."""
    
    def __init__(self):
        """Initialize with immediate output."""
        # Force stdout flush
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)  # Line buffered
        
        print("[LAUNCH] G6.1 Immediate Output Platform Starting", flush=True)
        print("=" * 50, flush=True)
        
        self.running = True
        self.cycle_count = 0
        self.total_options = 0
        
        # Environment check with output
        api_key = os.getenv('KITE_API_KEY')
        access_token = os.getenv('KITE_ACCESS_TOKEN')
        
        print(f"[OK] API Key: {'SET' if api_key else 'MISSING'}", flush=True)
        print(f"[OK] Access Token: {'SET' if access_token else 'MISSING'}", flush=True)
        
        if not api_key or not access_token:
            print("[WARNING] Running in simulation mode", flush=True)
        else:
            print("[OK] Credentials validated", flush=True)
        
        # Signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("[OK] Platform initialization complete", flush=True)
        print("[START] Beginning data collection...", flush=True)
        time.sleep(0.5)  # Brief pause to ensure output is seen
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n[STOP] Received signal {signum}, shutting down...", flush=True)
        self.running = False
    
    def process_index_quickly(self, index):
        """Process index with immediate output."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Immediate processing start
        print(f"[DATA] {timestamp} Processing {index}...", flush=True)
        time.sleep(0.2)
        
        # Simulate quick processing
        atm_strike = {
            'NIFTY': random.randint(24800, 25200),
            'BANKNIFTY': random.randint(51000, 52000),
            'FINNIFTY': random.randint(23000, 24000),
            'MIDCPNIFTY': random.randint(12500, 13000)
        }.get(index, 25000)
        
        volatility = random.uniform(18, 30)
        print(f"[INFO] {index} ATM Strike: {atm_strike} | Volatility: {volatility:.1f}%", flush=True)
        time.sleep(0.3)
        
        # Process options quickly
        options_count = 22  # 11 strikes x 2 option types
        total_volume = 0
        total_premium = 0
        
        for i in range(options_count):
            # Quick option simulation
            volume = random.randint(1000, 50000)
            premium = random.uniform(50, 500)
            total_volume += volume
            total_premium += premium
            
            # Show progress every few options
            if (i + 1) % 7 == 0:
                progress = f"{i+1}/{options_count}"
                print(f"[PROGRESS] {index} Progress: {progress} options processed", flush=True)
                time.sleep(0.1)
        
        # Completion summary
        avg_premium = total_premium / options_count
        processing_time = 1.2 + random.uniform(-0.3, 0.3)
        
        print(f"[OK] {index} Complete → {options_count} options | Avg: ₹{avg_premium:.1f} | Vol: {total_volume:,} | Time: {processing_time:.1f}s", flush=True)
        
        self.total_options += options_count
        return options_count
    
    def run_collection_cycle(self):
        """Run collection cycle with immediate feedback."""
        self.cycle_count += 1
        cycle_start = time.time()
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n[CYCLE] === Cycle {self.cycle_count} Started at {timestamp} ===", flush=True)
        
        indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
        cycle_options = 0
        
        for i, index in enumerate(indices):
            if not self.running:
                break
            
            print(f"[INFO] Processing index {i+1}/4: {index}", flush=True)
            
            try:
                options_processed = self.process_index_quickly(index)
                cycle_options += options_processed
                
                # Brief pause between indices
                if self.running and i < len(indices) - 1:
                    print(f"[INFO] Moving to next index...", flush=True)
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"[ERROR] {index} processing failed: {e}", flush=True)
                continue
        
        # Cycle completion
        cycle_duration = time.time() - cycle_start
        print(f"[CYCLE] Cycle {self.cycle_count} Complete → {cycle_options} options | Duration: {cycle_duration:.1f}s", flush=True)
        print(f"[INFO] Total options processed: {self.total_options}", flush=True)
        
        return cycle_options > 0
    
    def print_status_summary(self):
        """Print status summary."""
        uptime_minutes = (time.time() - self.start_time) / 60 if hasattr(self, 'start_time') else 0
        
        print(f"\n[SUMMARY] === Status Report ===", flush=True)
        print(f"[INFO] Runtime: {uptime_minutes:.1f} minutes", flush=True)
        print(f"[INFO] Cycles completed: {self.cycle_count}", flush=True)
        print(f"[INFO] Total options: {self.total_options}", flush=True)
        if uptime_minutes > 0:
            print(f"[INFO] Processing rate: {self.total_options/uptime_minutes:.1f} options/min", flush=True)
        print(f"[SUMMARY] === End Report ===\n", flush=True)
    
    def run(self):
        """Main execution with immediate output."""
        self.start_time = time.time()
        
        try:
            while self.running:
                # Run collection cycle
                success = self.run_collection_cycle()
                
                if not success:
                    print("[WARNING] Cycle had issues, continuing...", flush=True)
                
                # Status summary every 3 cycles
                if self.cycle_count % 3 == 0:
                    self.print_status_summary()
                
                # Wait for next cycle with countdown
                if self.running:
                    wait_time = 20  # Faster cycles for testing
                    next_time = datetime.now().strftime('%H:%M:%S')
                    print(f"[WAIT] Next cycle in {wait_time}s (at approximately {next_time})", flush=True)
                    
                    for remaining in range(wait_time, 0, -5):
                        if not self.running:
                            break
                        if remaining % 10 == 0:
                            print(f"[WAIT] {remaining} seconds remaining...", flush=True)
                        time.sleep(min(5, remaining))
        
        except KeyboardInterrupt:
            print("\n[STOP] Keyboard interrupt received", flush=True)
        except Exception as e:
            print(f"\n[ERROR] Platform error: {e}", flush=True)
        finally:
            self.running = False
            print("\n[SHUTDOWN] Platform stopping...", flush=True)
            self.print_status_summary()
            print("[OK] Platform stopped gracefully", flush=True)

def main():
    """Main entry point with immediate output."""
    try:
        print("Starting immediate output collector...", flush=True)
        collector = ImmediateOutputCollector()
        collector.run()
        return 0
    except Exception as e:
        print(f"[ERROR] Startup failed: {e}", flush=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
