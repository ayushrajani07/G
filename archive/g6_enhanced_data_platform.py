#!/usr/bin/env python3
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
        print(f"\n[STOP] Received signal {signum}, shutting down gracefully...")
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
        print(f"\n[CYCLE] === Cycle {self.cycle_count} Started at {timestamp} ===")
        
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
        
        print(f"\n[SUMMARY] === Performance Report ===")
        print(f"[INFO] Runtime: {uptime_min:.1f} minutes | Cycles: {self.cycle_count}")
        print(f"[INFO] Total Options: {self.total_options} | Rate: {self.total_options/uptime_min:.1f}/min")
        
        # Index breakdown
        for index in self.indices:
            stats = self.index_stats[index]
            print(f"[INFO] {index}: {stats['options']} options | Avg: ₹{stats['avg_price']:.1f} | Vol: {stats['total_volume']:,}")
        
        print(f"[SUMMARY] === End Report ===\n")
    
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
            print("\n[STOP] Keyboard interrupt received")
        except Exception as e:
            print(f"\n[ERROR] Platform error: {e}")
        finally:
            self.running = False
            print("\n[SHUTDOWN] Stopping enhanced data collection...")
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
