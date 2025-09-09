#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 Enhanced ATM Options Collector - G6.1 Platform v2.0
Author: AI Assistant (Optimized, no redundant data/Greeks)

Features:
- Eliminated bid/ask/market depth collection
- Avoided redundant Greeks calculations
- Streamlined data collection
- Enhanced performance metrics
- Configurable strike patterns
- Batch processing optimization
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

from config_manager import get_config
from enhanced_kite_provider import EnhancedKiteDataProvider, RequestPriority

@dataclass
class CollectionResult:
    """📊 Collection result with metrics."""
    success: bool
    options_data: List[Dict[str, Any]] = field(default_factory=list)
    collection_time: float = 0.0
    total_instruments: int = 0
    successful_instruments: int = 0
    failed_instruments: int = 0
    error_message: Optional[str] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return self.successful_instruments / max(1, self.total_instruments)

@dataclass
class CollectionMetrics:
    """📊 Comprehensive collection metrics."""
    total_collections: int = 0
    successful_collections: int = 0
    failed_collections: int = 0
    total_options_processed: int = 0
    total_collection_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    rate_limit_hits: int = 0
    
    @property
    def success_rate(self) -> float:
        return self.successful_collections / max(1, self.total_collections)
    
    @property
    def average_collection_time(self) -> float:
        return self.total_collection_time / max(1, self.successful_collections)
    
    @property
    def options_per_second(self) -> float:
        return self.total_options_processed / max(1, self.total_collection_time)

class EnhancedATMOptionsCollector:
    """🎯 High-performance ATM options collector with optimized data collection."""
    
    def __init__(self, kite_provider: EnhancedKiteDataProvider, 
                 max_workers: int = 4, timeout_seconds: float = 30.0, 
                 quality_threshold: float = 0.8):
        """Initialize enhanced ATM options collector."""
        self.config = get_config()
        self.kite_provider = kite_provider
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        self.quality_threshold = quality_threshold
        
        self.logger = logging.getLogger(f"{__name__}.EnhancedATMCollector")
        
        # Performance tracking
        self.metrics = CollectionMetrics()
        self.collection_lock = threading.RLock()
        
        # Configuration
        self.data_fields = self.config.get_data_fields()
        self.include_market_depth = self.config.is_market_depth_enabled()
        self.avoid_greeks_redundancy = self.config.is_greeks_redundancy_avoided()
        
        # Thread pool for concurrent collection
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Cache for instrument mappings
        self.instrument_cache = {}
        self.cache_lock = threading.RLock()
        
        self.logger.info("✅ Enhanced ATM Options Collector initialized")
        self.logger.info(f"🎛️ Max workers: {max_workers}, Timeout: {timeout_seconds}s")
        self.logger.info(f"🎛️ Market depth: {'✅ Enabled' if self.include_market_depth else '❌ Disabled'}")
        self.logger.info(f"🎛️ Greeks redundancy avoided: {'✅ Yes' if self.avoid_greeks_redundancy else '❌ No'}")
    
    def collect_atm_options(self, index_name: str, index_params: Dict[str, Any],
                           include_greeks: bool = True, 
                           include_market_depth: bool = False) -> Dict[str, CollectionResult]:
        """🎯 Collect ATM options with enhanced performance and no redundancy."""
        
        start_time = time.time()
        collection_id = f"{index_name}_{int(start_time)}"
        
        self.logger.info(f"📊 Starting ATM collection for {index_name}")
        
        try:
            with self.collection_lock:
                self.metrics.total_collections += 1
            
            # Override parameters based on configuration
            actual_include_greeks = include_greeks and not self.avoid_greeks_redundancy
            actual_include_market_depth = include_market_depth and self.include_market_depth
            
            # Get strike offsets from configuration
            strike_offsets = self.config.get_strike_offsets(index_name)
            
            # Get ATM strike
            try:
                atm_strike = self.kite_provider.get_atm_strike(index_name)
            except Exception as e:
                self.logger.error(f"🔴 Failed to get ATM strike for {index_name}: {e}")
                return self._create_failed_result(collection_id, str(e))
            
            # Calculate strikes to collect
            strikes_to_collect = self._calculate_strikes(index_name, atm_strike, strike_offsets)
            
            # Build instrument list
            instruments = self._build_instrument_list(index_name, strikes_to_collect)
            
            if not instruments:
                self.logger.warning(f"⚠️ No instruments found for {index_name}")
                return self._create_failed_result(collection_id, "No instruments found")
            
            # Collect data using optimized batch processing
            collection_result = self._collect_options_batch(
                index_name,
                instruments,
                actual_include_greeks,
                actual_include_market_depth
            )
            
            # Record metrics
            collection_time = time.time() - start_time
            with self.collection_lock:
                if collection_result.success:
                    self.metrics.successful_collections += 1
                    self.metrics.total_options_processed += len(collection_result.options_data)
                else:
                    self.metrics.failed_collections += 1
                
                self.metrics.total_collection_time += collection_time
            
            # Log results
            success_rate = collection_result.success_rate
            self.logger.info(
                f"✅ ATM collection completed: {index_name} - "
                f"{collection_result.successful_instruments}/{collection_result.total_instruments} "
                f"successful ({success_rate:.1%}) in {collection_time*1000:.1f}ms"
            )
            
            return {collection_id: collection_result}
            
        except Exception as e:
            self.logger.error(f"🔴 ATM collection failed for {index_name}: {e}")
            with self.collection_lock:
                self.metrics.failed_collections += 1
            
            return self._create_failed_result(collection_id, str(e))
    
    def _calculate_strikes(self, index_name: str, atm_strike: float, offsets: List[int]) -> List[float]:
        """🎯 Calculate strikes based on ATM and offsets."""
        # Determine strike interval based on index
        strike_intervals = {
            'NIFTY': 50,
            'BANKNIFTY': 100,
            'FINNIFTY': 50,
            'MIDCPNIFTY': 25
        }
        
        interval = strike_intervals.get(index_name.upper(), 50)
        strikes = []
        
        for offset in offsets:
            strike = atm_strike + (offset * interval)
            strikes.append(strike)
        
        self.logger.debug(f"🎯 Calculated strikes for {index_name}: {strikes}")
        return sorted(strikes)
    
    def _build_instrument_list(self, index_name: str, strikes: List[float]) -> List[str]:
        """🔧 Build instrument list for collection."""
        instruments = []
        
        # Get current expiry
        expiry_date = self._get_current_expiry(index_name)
        
        for strike in strikes:
            for option_type in ['CE', 'PE']:
                instrument_symbol = self._build_instrument_symbol(
                    index_name, expiry_date, strike, option_type
                )
                instruments.append(instrument_symbol)
        
        return instruments
    
    def _build_instrument_symbol(self, index_name: str, expiry_date: str, 
                                strike: float, option_type: str) -> str:
        """🔧 Build instrument symbol."""
        # Format: INDEX + EXPIRY + STRIKE + TYPE
        # Example: NIFTY2409812500CE
        
        expiry_formatted = expiry_date.replace('-', '')[2:]  # YYMMDD format
        strike_formatted = f"{int(strike)}"
        
        return f"{index_name}{expiry_formatted}{strike_formatted}{option_type}"
    
    def _get_current_expiry(self, index_name: str) -> str:
        """📅 Get current weekly expiry."""
        # Find next Thursday
        today = datetime.now()
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0 and today.hour >= 15:  # After market close
            days_until_thursday = 7
        
        expiry_date = today + timedelta(days=days_until_thursday)
        return expiry_date.strftime('%Y-%m-%d')
    
    def _collect_options_batch(self, index_name: str, instruments: List[str], 
                              include_greeks: bool, include_market_depth: bool) -> CollectionResult:
        """📊 Collect options data using batch processing."""
        
        start_time = time.time()
        total_instruments = len(instruments)
        
        try:
            # Use batch quotes for better performance
            quotes_data = self.kite_provider.get_quotes_batch(
                instruments, 
                priority=RequestPriority.HIGH
            )
            
            # Process quotes into options data
            options_data = []
            successful_count = 0
            
            for instrument in instruments:
                quote = quotes_data.get(instrument)
                if quote and quote.get('last_price', 0) > 0:
                    option_data = self._process_quote_to_option(
                        instrument, quote, include_greeks, include_market_depth
                    )
                    if option_data:
                        options_data.append(option_data)
                        successful_count += 1
            
            collection_time = time.time() - start_time
            
            # Determine if collection was successful
            success_rate = successful_count / max(1, total_instruments)
            success = success_rate >= self.quality_threshold
            
            return CollectionResult(
                success=success,
                options_data=options_data,
                collection_time=collection_time,
                total_instruments=total_instruments,
                successful_instruments=successful_count,
                failed_instruments=total_instruments - successful_count
            )
            
        except Exception as e:
            self.logger.error(f"🔴 Batch collection error: {e}")
            return CollectionResult(
                success=False,
                collection_time=time.time() - start_time,
                total_instruments=total_instruments,
                error_message=str(e)
            )
    
    def _process_quote_to_option(self, instrument: str, quote: Dict[str, Any], 
                                include_greeks: bool, include_market_depth: bool) -> Optional[Dict[str, Any]]:
        """📊 Process quote data to option data format."""
        try:
            # Parse instrument symbol
            parsed = self._parse_instrument_symbol(instrument)
            if not parsed:
                return None
            
            # Build basic option data (only essential fields)
            option_data = {
                'tradingsymbol': instrument,
                'strike': float(parsed['strike']),
                'expiry': parsed['expiry'],
                'option_type': parsed['option_type'],
                'last_price': float(quote.get('last_price', 0)),
            }
            
            # Add pricing fields if configured
            if 'pricing' in self.data_fields:
                pricing_fields = self.data_fields['pricing']
                if 'volume' in pricing_fields:
                    option_data['volume'] = int(quote.get('volume', 0))
                if 'oi' in pricing_fields:
                    option_data['oi'] = int(quote.get('oi', 0))
                if 'change' in pricing_fields:
                    option_data['change'] = float(quote.get('net_change', 0))
                if 'pchange' in pricing_fields:
                    option_data['pchange'] = float(quote.get('percentage_change', 0))
                if 'iv' in pricing_fields and 'iv' in quote:
                    option_data['iv'] = float(quote.get('iv', 0))
            
            # Add Greeks only if not avoiding redundancy and specifically requested
            if include_greeks and 'greeks' in self.data_fields and not self.avoid_greeks_redundancy:
                greeks_fields = self.data_fields['greeks']
                ohlc = quote.get('ohlc', {})
                
                # Only add Greeks if they exist in the quote
                if 'delta' in greeks_fields and 'delta' in ohlc:
                    option_data['delta'] = float(ohlc.get('delta', 0))
                if 'gamma' in greeks_fields and 'gamma' in ohlc:
                    option_data['gamma'] = float(ohlc.get('gamma', 0))
                if 'theta' in greeks_fields and 'theta' in ohlc:
                    option_data['theta'] = float(ohlc.get('theta', 0))
                if 'vega' in greeks_fields and 'vega' in ohlc:
                    option_data['vega'] = float(ohlc.get('vega', 0))
            
            # Deliberately SKIP market depth (bid/ask) unless specifically enabled
            # This eliminates unnecessary API load and data volume
            if include_market_depth and 'market_depth' in self.data_fields:
                depth_fields = self.data_fields['market_depth']
                depth = quote.get('depth', {})
                
                if 'bid' in depth_fields and 'buy' in depth and depth['buy']:
                    option_data['bid'] = float(depth['buy'][0].get('price', 0))
                if 'ask' in depth_fields and 'sell' in depth and depth['sell']:
                    option_data['ask'] = float(depth['sell'][0].get('price', 0))
            
            # Add offset for analysis
            option_data['offset'] = self._calculate_offset(
                parsed['index'], parsed['strike'], parsed['option_type']
            )
            
            return option_data
            
        except Exception as e:
            self.logger.debug(f"🔴 Failed to process quote for {instrument}: {e}")
            return None
    
    def _parse_instrument_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """🔧 Parse instrument symbol to components."""
        try:
            # Cache parsed results
            with self.cache_lock:
                if symbol in self.instrument_cache:
                    return self.instrument_cache[symbol]
            
            # Parse format: INDEX + EXPIRY + STRIKE + TYPE
            # Example: NIFTY2409812500CE
            
            # Extract option type (last 2 characters)
            option_type = symbol[-2:]
            if option_type not in ['CE', 'PE']:
                return None
            
            # Extract everything before option type
            base_symbol = symbol[:-2]
            
            # Find where numbers start (expiry)
            index_name = ""
            numbers_part = ""
            
            for i, char in enumerate(base_symbol):
                if char.isdigit():
                    index_name = base_symbol[:i]
                    numbers_part = base_symbol[i:]
                    break
            
            if not index_name or not numbers_part:
                return None
            
            # Parse expiry (first 6 digits) and strike (remaining)
            if len(numbers_part) < 6:
                return None
            
            expiry_part = numbers_part[:6]  # YYMMDD
            strike_part = numbers_part[6:]  # Strike price
            
            # Convert expiry to standard format
            expiry_date = f"20{expiry_part[:2]}-{expiry_part[2:4]}-{expiry_part[4:6]}"
            
            # Parse strike
            strike = float(strike_part) if strike_part else 0
            
            result = {
                'index': index_name,
                'expiry': expiry_date,
                'strike': strike,
                'option_type': option_type
            }
            
            # Cache the result
            with self.cache_lock:
                self.instrument_cache[symbol] = result
            
            return result
            
        except Exception as e:
            self.logger.debug(f"🔴 Failed to parse symbol {symbol}: {e}")
            return None
    
    def _calculate_offset(self, index_name: str, strike: float, option_type: str) -> int:
        """🎯 Calculate offset from ATM."""
        try:
            # Get current ATM strike
            atm_strike = self.kite_provider.get_atm_strike(index_name)
            
            # Calculate strike intervals
            intervals = {
                'NIFTY': 50,
                'BANKNIFTY': 100,
                'FINNIFTY': 50,
                'MIDCPNIFTY': 25
            }
            
            interval = intervals.get(index_name.upper(), 50)
            
            # Calculate offset
            offset = int((strike - atm_strike) / interval)
            
            return offset
            
        except Exception:
            return 0
    
    def _create_failed_result(self, collection_id: str, error: str) -> Dict[str, CollectionResult]:
        """❌ Create failed collection result."""
        return {
            collection_id: CollectionResult(
                success=False,
                error_message=error,
                collection_time=0.0
            )
        }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """📊 Get comprehensive collection statistics."""
        with self.collection_lock:
            return {
                'performance': {
                    'total_collections': self.metrics.total_collections,
                    'success_rate': round(self.metrics.success_rate, 3),
                    'average_collection_time': round(self.metrics.average_collection_time, 3),
                    'options_per_second': round(self.metrics.options_per_second, 1),
                    'total_options_processed': self.metrics.total_options_processed
                },
                'configuration': {
                    'max_workers': self.max_workers,
                    'timeout_seconds': self.timeout_seconds,
                    'quality_threshold': self.quality_threshold,
                    'include_market_depth': self.include_market_depth,
                    'avoid_greeks_redundancy': self.avoid_greeks_redundancy
                },
                'cache': {
                    'instrument_cache_size': len(self.instrument_cache)
                },
                'data_fields': self.data_fields
            }
    
    def clear_cache(self):
        """🧹 Clear collector cache."""
        with self.cache_lock:
            self.instrument_cache.clear()
        self.logger.info("🧹 Collector cache cleared")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """📊 Get metrics summary for monitoring."""
        stats = self.get_collection_stats()
        
        return {
            'collector_type': 'ATM Options',
            'status': 'healthy' if stats['performance']['success_rate'] > 0.8 else 'degraded',
            'success_rate': stats['performance']['success_rate'],
            'average_time': stats['performance']['average_collection_time'],
            'total_processed': stats['performance']['total_options_processed'],
            'throughput': stats['performance']['options_per_second']
        }
    
    def __del__(self):
        """🔒 Cleanup on destruction."""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
        except Exception:
            pass  # Ignore cleanup errors
