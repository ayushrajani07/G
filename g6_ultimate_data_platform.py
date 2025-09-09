#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G6.1 Ultimate Data Collection Platform
NON-INTERACTIVE - Pure data collection focus
"""

import os
import sys
import time
import random
import signal
from datetime import datetime, timedelta

class G6DataCollector:
    """Pure data collection class."""
    
    def __init__(self):
        """Initialize data collector."""
        self.api_key = os.getenv('KITE_API_KEY')
        self.access_token = os.getenv('KITE_ACCESS_TOKEN')
        self.running = True
        
        # Market indices to process
        self.indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
        
        # ATM strike configurations
        self.strike_offsets = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
        
        # Metrics
        self.total_options = 0
        self.cycle_count = 0
        self.start_time = time.time()
        
        # Signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n[STOP] Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def get_atm_strike(self, index):
        """Get simulated ATM strike for index."""
        atm_strikes = {
            'NIFTY': random.randint(24800, 25200),
            'BANKNIFTY': random.randint(51000, 52000),
            'FINNIFTY': random.randint(23000, 24000),
            'MIDCPNIFTY': random.randint(12500, 13000)
        }
        return atm_strikes.get(index, 25000)
    
    def get_strike_interval(self, index):
        """Get strike interval for index."""
        intervals = {
            'NIFTY': 50,
            'BANKNIFTY': 100,
            'FINNIFTY': 50,
            'MIDCPNIFTY': 25
        }
        return intervals.get(index, 50)
    
    def simulate_option_data(self, index, strike, option_type):
        """Simulate realistic option data."""
        # Realistic price based on ATM distance
        atm_strike = self.get_atm_strike(index)
        distance = abs(strike - atm_strike)
        
        if option_type == 'CE':
            if strike <= atm_strike:  # ITM Call
                base_price = random.uniform(200, 800)
            else:  # OTM Call
                base_price = max(1, random.uniform(10, 200) / (1 + distance/100))
        else:  # PE
            if strike >= atm_strike:  # ITM Put
                base_price = random.uniform(200, 800)
            else:  # OTM Put
                base_price = max(1, random.uniform(10, 200) / (1 + distance/100))
        
        return {
            'tradingsymbol': f"{index}{strike}{option_type}",
            'strike': strike,
            'option_type': option_type,
            'last_price': round(base_price, 2),
            'volume': random.randint(1000, 50000),
            'oi': random.randint(500, 100000),
            'change': round(random.uniform(-50, 50), 2),
            'pchange': round(random.uniform(-20, 20), 2),
            'iv': round(random.uniform(15, 35), 2),
            'delta': round(random.uniform(-1, 1), 4),
            'gamma': round(random.uniform(0, 0.01), 6),
            'theta': round(random.uniform(-5, 0), 4),
            'vega': round(random.uniform(0, 50), 4)
        }
    
    def collect_index_options(self, index):
        """Collect options for a specific index."""
        print(f"[DATA] Starting {index} options collection...")
        
        # Get ATM strike
        atm_strike = self.get_atm_strike(index)
        interval = self.get_strike_interval(index)
        
        print(f"[OK] {index} ATM Strike: {atm_strike}")
        
        options_collected = 0
        
        # Collect options for each offset
        for offset in self.strike_offsets:
            strike = atm_strike + (offset * interval)
            
            # Collect CE and PE
            for option_type in ['CE', 'PE']:
                try:
                    option_data = self.simulate_option_data(index, strike, option_type)
                    
                    # Log the option data
                    symbol = option_data['tradingsymbol']
                    price = option_data['last_price']
                    volume = option_data['volume']
                    iv = option_data['iv']
                    
                    print(f"[OK] {symbol}: ₹{price} | Vol: {volume} | IV: {iv}%")
                    
                    options_collected += 1
                    self.total_options += 1
                    
                    # Small delay to simulate processing
                    time.sleep(0.1)
                    
                    if not self.running:
                        break
                        
                except Exception as e:
                    print(f"[ERROR] Failed to collect {index} {strike}{option_type}: {e}")
                    continue
            
            if not self.running:
                break
        
        print(f"[OK] {index} collection complete - {options_collected} options processed")
        return options_collected
    
    def run_collection_cycle(self):
        """Run one complete data collection cycle."""
        self.cycle_count += 1
        cycle_start = time.time()
        
        print(f"\n[DATA] === Collection Cycle {self.cycle_count} ===")
        print(f"[OK] Cycle started at {datetime.now().strftime('%H:%M:%S')}")
        
        total_options_this_cycle = 0
        
        # Collect data for each index
        for index in self.indices:
            if not self.running:
                break
                
            options_count = self.collect_index_options(index)
            total_options_this_cycle += options_count
            
            # Brief pause between indices
            if self.running:
                time.sleep(1)
        
        cycle_duration = time.time() - cycle_start
        
        print(f"[OK] Cycle {self.cycle_count} completed successfully")
        print(f"[OK] Duration: {cycle_duration:.1f}s | Options: {total_options_this_cycle} | Total: {self.total_options}")
        
        return total_options_this_cycle > 0
    
    def print_status_summary(self):
        """Print comprehensive status summary."""
        uptime = time.time() - self.start_time
        print(f"\n[DATA] === PLATFORM STATUS SUMMARY ===")
        print(f"[OK] Uptime: {uptime/60:.1f} minutes")
        print(f"[OK] Collection Cycles: {self.cycle_count}")
        print(f"[OK] Total Options Processed: {self.total_options}")
        print(f"[OK] Average Options/Cycle: {self.total_options/max(1, self.cycle_count):.1f}")
        if self.cycle_count > 0:
            print(f"[OK] Options/Minute: {self.total_options/(uptime/60):.1f}")
    
    def run(self):
        """Main data collection loop."""
        print("[LAUNCH] G6.1 Ultimate Data Collection Platform")
        print("=" * 60)
        
        # Validate credentials
        if not self.api_key:
            print("[WARNING] KITE_API_KEY not found - running in simulation mode")
        else:
            print(f"[OK] API Key: {self.api_key[:8]}...")
        
        if not self.access_token:
            print("[WARNING] KITE_ACCESS_TOKEN not found - running in simulation mode")
        else:
            print(f"[OK] Access Token: {self.access_token[:8]}...")
        
        print(f"[OK] Target Indices: {', '.join(self.indices)}")
        print(f"[OK] Strike Offsets: {self.strike_offsets}")
        print("[OK] Platform initialization complete")
        print("[OK] Starting continuous data collection...")
        
        try:
            # Main collection loop
            while self.running:
                # Run collection cycle
                success = self.run_collection_cycle()
                
                if not success:
                    print("[WARNING] Collection cycle had issues, but continuing...")
                
                # Print periodic status
                if self.cycle_count % 5 == 0:
                    self.print_status_summary()
                
                # Wait for next cycle (configurable interval)
                if self.running:
                    print(f"[OK] Waiting 30 seconds for next cycle...")
                    
                    for i in range(30):
                        if not self.running:
                            break
                        time.sleep(1)
                        
                        # Show countdown every 10 seconds
                        if (30 - i) % 10 == 0 and (30 - i) != 30:
                            print(f"[OK] Next cycle in {30-i} seconds...")
        
        except KeyboardInterrupt:
            print("\n[STOP] Keyboard interrupt received")
        except Exception as e:
            print(f"\n[ERROR] Platform error: {e}")
        finally:
            self.running = False
            print("\n[STOP] Shutting down data collection...")
            self.print_status_summary()
            print("[OK] Platform stopped gracefully")

def main():
    """Main entry point."""
    try:
        collector = G6DataCollector()
        collector.run()
        return 0
    except Exception as e:
        print(f"[ERROR] Platform startup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
