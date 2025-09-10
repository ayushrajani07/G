#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 ATM Options Collector - G6 Platform v3.0
Consolidated data collection for At-The-Money options with enhanced performance.

Restructured from: enhanced_atm_collector.py, atm_options_collector.py
Features:
- Streamlined data collection with no redundant calculations
- Enhanced performance metrics and monitoring
- Configurable strike patterns and batch processing
- Thread-safe operations with proper error handling
- Memory management and resource cleanup
"""

import time
import logging
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class CollectionResult:
    """Data collection result with comprehensive metrics."""
    success: bool
    data: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    collection_time: float = 0.0
    total_instruments: int = 0
    successful_instruments: int = 0
    failed_instruments: int = 0
    
    # Error information
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate collection success rate."""
        if self.total_instruments == 0:
            return 0.0
        return (self.successful_instruments / self.total_instruments) * 100

@dataclass
class StrikeConfig:
    """Strike configuration for options collection."""
    center_strike: float
    offsets: List[int]
    strike_interval: int
    option_types: List[str] = field(default_factory=lambda: ['CE', 'PE'])
    
    def get_strikes(self) -> List[float]:
        """Get all strike prices based on configuration."""
        strikes = []
        for offset in self.offsets:
            strike = self.center_strike + (offset * self.strike_interval)
            strikes.append(strike)
        return sorted(strikes)

@dataclass
class CollectionStats:
    """Collection statistics tracking."""
    total_collections: int = 0
    successful_collections: int = 0
    failed_collections: int = 0
    total_options_processed: int = 0
    total_processing_time: float = 0.0
    
    # Index-specific stats
    index_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Error tracking
    error_count: int = 0
    last_error: Optional[str] = None
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        total = self.successful_collections + self.failed_collections
        if total == 0:
            return 0.0
        return (self.successful_collections / total) * 100
    
    @property
    def average_collection_time(self) -> float:
        """Calculate average collection time."""
        if self.total_collections == 0:
            return 0.0
        return self.total_processing_time / self.total_collections
    
    def add_error(self, error_msg: str, error_details: Dict[str, Any] = None):
        """Add error to tracking."""
        self.error_count += 1
        self.last_error = error_msg
        
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': error_msg,
            'details': error_details or {}
        }
        
        self.error_history.append(error_entry)
        
        # Keep only last 50 errors
        if len(self.error_history) > 50:
            self.error_history = self.error_history[-50:]

class ATMOptionsCollector:
    """
    🎯 Enhanced ATM Options Collector with streamlined processing.
    
    Collects At-The-Money options data with configurable strike ranges,
    batch processing, and comprehensive error handling.
    """
    
    # Index-specific strike intervals
    STRIKE_INTERVALS = {
        'NIFTY': 50,
        'BANKNIFTY': 100,
        'FINNIFTY': 50,
        'MIDCPNIFTY': 25,
        'SENSEX': 100,
        'BANKEX': 100
    }
    
    def __init__(self,
                 api_provider,
                 max_workers: int = 4,
                 timeout_seconds: float = 30.0,
                 quality_threshold: float = 0.8,
                 batch_size: int = 10,
                 cache_ttl: int = 30):
        """
        Initialize ATM Options Collector.
        
        Args:
            api_provider: Data provider instance (KiteDataProvider)
            max_workers: Maximum worker threads
            timeout_seconds: Request timeout
            quality_threshold: Minimum data quality threshold
            batch_size: Batch size for processing
            cache_ttl: Cache TTL in seconds
        """
        self.api_provider = api_provider
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        self.quality_threshold = quality_threshold
        self.batch_size = batch_size
        self.cache_ttl = cache_ttl
        
        # Statistics tracking
        self.stats = CollectionStats()
        
        # Thread management
        self.thread_pool = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="ATMCollector"
        )
        
        # Cache for ATM strikes
        self._atm_cache: Dict[str, Tuple[float, float]] = {}  # index -> (strike, timestamp)
        self._cache_lock = threading.RLock()
        
        # Configuration
        self._default_offsets = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
        
        logger.info("🎯 ATM Options Collector initialized")
        logger.info(f"⚙️ Config: {max_workers} workers, {timeout_seconds}s timeout, {quality_threshold} quality threshold")
    
    def get_atm_strike(self, index_name: str, use_cache: bool = True) -> float:
        """
        Get ATM strike for an index with caching.
        
        Args:
            index_name: Index name (NIFTY, BANKNIFTY, etc.)
            use_cache: Whether to use cached value
            
        Returns:
            ATM strike price
        """
        # Check cache first
        if use_cache:
            with self._cache_lock:
                cached_data = self._atm_cache.get(index_name)
                if cached_data:
                    strike, timestamp = cached_data
                    if time.time() - timestamp < self.cache_ttl:
                        logger.debug(f"📍 Using cached ATM strike for {index_name}: {strike}")
                        return strike
        
        try:
            # Get fresh ATM strike from API
            atm_strike = self.api_provider.get_atm_strike(index_name)
            
            # Cache the result
            with self._cache_lock:
                self._atm_cache[index_name] = (atm_strike, time.time())
            
            logger.debug(f"📍 Fresh ATM strike for {index_name}: {atm_strike}")
            return atm_strike
            
        except Exception as e:
            error_msg = f"Failed to get ATM strike for {index_name}: {e}"
            logger.error(f"🔴 {error_msg}")
            self.stats.add_error(error_msg, {'index': index_name})
            raise
    
    def collect_atm_options(self,
                           index_name: str,
                           index_params: Dict[str, Any] = None,
                           include_greeks: bool = True,
                           include_market_depth: bool = False,
                           custom_offsets: List[int] = None) -> CollectionResult:
        """
        Collect ATM options data for an index.
        
        Args:
            index_name: Index name (NIFTY, BANKNIFTY, etc.)
            index_params: Additional index parameters
            include_greeks: Whether to include Greeks data
            include_market_depth: Whether to include market depth
            custom_offsets: Custom strike offsets
            
        Returns:
            CollectionResult with options data
        """
        start_time = time.time()
        result = CollectionResult()
        
        try:
            logger.info(f"🎯 Starting ATM options collection for {index_name}")
            
            # Get ATM strike
            atm_strike = self.get_atm_strike(index_name)
            
            # Get strike configuration
            strike_config = self._build_strike_config(
                index_name=index_name,
                atm_strike=atm_strike,
                custom_offsets=custom_offsets,
                index_params=index_params
            )
            
            # Collect options data
            options_data = self._collect_options_batch(
                index_name=index_name,
                strike_config=strike_config,
                include_greeks=include_greeks,
                include_market_depth=include_market_depth
            )
            
            # Process and validate data
            processed_data = self._process_options_data(
                index_name=index_name,
                raw_data=options_data,
                strike_config=strike_config
            )
            
            # Build result
            result.success = True
            result.data = processed_data
            result.total_instruments = len(strike_config.get_strikes()) * len(strike_config.option_types)
            result.successful_instruments = len(processed_data)
            result.failed_instruments = result.total_instruments - result.successful_instruments
            result.collection_time = time.time() - start_time
            
            # Add metadata
            result.metadata = {
                'index_name': index_name,
                'atm_strike': atm_strike,
                'strike_interval': strike_config.strike_interval,
                'offsets': strike_config.offsets,
                'option_types': strike_config.option_types,
                'collection_timestamp': datetime.now().isoformat(),
                'include_greeks': include_greeks,
                'include_market_depth': include_market_depth
            }
            
            # Update statistics
            self._update_stats(index_name, result)
            
            logger.info(f"✅ {index_name} collection completed: {result.successful_instruments}/{result.total_instruments} options in {result.collection_time:.2f}s")
            
        except Exception as e:
            error_msg = f"ATM options collection failed for {index_name}: {e}"
            logger.error(f"🔴 {error_msg}")
            
            result.success = False
            result.error_message = error_msg
            result.error_details = {
                'index_name': index_name,
                'exception_type': type(e).__name__,
                'exception_args': str(e)
            }
            result.collection_time = time.time() - start_time
            
            self.stats.add_error(error_msg, result.error_details)
        
        return result
    
    def _build_strike_config(self,
                           index_name: str,
                           atm_strike: float,
                           custom_offsets: List[int] = None,
                           index_params: Dict[str, Any] = None) -> StrikeConfig:
        """Build strike configuration for collection."""
        strike_interval = self.STRIKE_INTERVALS.get(index_name, 50)
        offsets = custom_offsets or self._default_offsets
        
        # Apply index-specific parameters if provided
        if index_params:
            strike_interval = index_params.get('strike_interval', strike_interval)
            offsets = index_params.get('offsets', offsets)
        
        return StrikeConfig(
            center_strike=atm_strike,
            offsets=offsets,
            strike_interval=strike_interval
        )
    
    def _collect_options_batch(self,
                             index_name: str,
                             strike_config: StrikeConfig,
                             include_greeks: bool = True,
                             include_market_depth: bool = False) -> List[Dict[str, Any]]:
        """Collect options data in batches."""
        all_strikes = strike_config.get_strikes()
        option_types = strike_config.option_types
        
        # Build list of all instruments to collect
        instruments = []
        for strike in all_strikes:
            for option_type in option_types:
                instruments.append({
                    'index': index_name,
                    'strike': strike,
                    'option_type': option_type
                })
        
        # Process in batches
        options_data = []
        for i in range(0, len(instruments), self.batch_size):
            batch = instruments[i:i + self.batch_size]
            batch_data = self._process_instrument_batch(
                batch=batch,
                include_greeks=include_greeks,
                include_market_depth=include_market_depth
            )
            options_data.extend(batch_data)
        
        return options_data
    
    def _process_instrument_batch(self,
                                batch: List[Dict[str, Any]],
                                include_greeks: bool = True,
                                include_market_depth: bool = False) -> List[Dict[str, Any]]:
        """Process a batch of instruments concurrently."""
        batch_data = []
        
        # Submit all batch requests concurrently
        future_to_instrument = {}
        for instrument in batch:
            future = self.thread_pool.submit(
                self._collect_single_option,
                instrument,
                include_greeks,
                include_market_depth
            )
            future_to_instrument[future] = instrument
        
        # Collect results
        for future in as_completed(future_to_instrument, timeout=self.timeout_seconds):
            instrument = future_to_instrument[future]
            try:
                option_data = future.result()
                if option_data:
                    batch_data.append(option_data)
            except Exception as e:
                logger.warning(f"⚠️ Failed to collect {instrument}: {e}")
        
        return batch_data
    
    def _collect_single_option(self,
                             instrument: Dict[str, Any],
                             include_greeks: bool = True,
                             include_market_depth: bool = False) -> Optional[Dict[str, Any]]:
        """Collect data for a single option instrument."""
        try:
            index_name = instrument['index']
            strike = instrument['strike']
            option_type = instrument['option_type']
            
            # Get options data from API
            options_data = self.api_provider.get_options_data(
                index_name=index_name,
                strikes=[strike],
                option_types=[option_type]
            )
            
            if not options_data:
                return None
            
            # Take the first (and should be only) result
            option_data = options_data[0]
            
            # Enhance with additional data if requested
            if include_greeks and hasattr(self.api_provider, 'get_option_greeks'):
                try:
                    greeks = self.api_provider.get_option_greeks(
                        index_name, strike, option_type
                    )
                    option_data.update(greeks)
                except Exception as e:
                    logger.debug(f"Greeks calculation failed for {index_name} {strike} {option_type}: {e}")
            
            if include_market_depth and hasattr(self.api_provider, 'get_market_depth'):
                try:
                    market_depth = self.api_provider.get_market_depth(
                        index_name, strike, option_type
                    )
                    option_data['market_depth'] = market_depth
                except Exception as e:
                    logger.debug(f"Market depth failed for {index_name} {strike} {option_type}: {e}")
            
            return option_data
            
        except Exception as e:
            logger.warning(f"⚠️ Single option collection failed: {e}")
            return None
    
    def _process_options_data(self,
                            index_name: str,
                            raw_data: List[Dict[str, Any]],
                            strike_config: StrikeConfig) -> List[Dict[str, Any]]:
        """Process and validate collected options data."""
        processed_data = []
        
        for option_data in raw_data:
            try:
                # Validate data quality
                if self._validate_option_data(option_data):
                    # Enhance with calculated fields
                    enhanced_data = self._enhance_option_data(
                        option_data=option_data,
                        index_name=index_name,
                        strike_config=strike_config
                    )
                    processed_data.append(enhanced_data)
                else:
                    logger.debug(f"⚠️ Option data failed validation: {option_data.get('symbol', 'unknown')}")
            
            except Exception as e:
                logger.warning(f"⚠️ Failed to process option data: {e}")
        
        return processed_data
    
    def _validate_option_data(self, option_data: Dict[str, Any]) -> bool:
        """Validate option data quality."""
        required_fields = ['symbol', 'last_price', 'strike', 'option_type']
        
        # Check required fields
        for field in required_fields:
            if field not in option_data or option_data[field] is None:
                return False
        
        # Check data ranges
        last_price = option_data.get('last_price', 0)
        if last_price < 0:
            return False
        
        # Check option type
        option_type = option_data.get('option_type', '')
        if option_type not in ['CE', 'PE']:
            return False
        
        return True
    
    def _enhance_option_data(self,
                           option_data: Dict[str, Any],
                           index_name: str,
                           strike_config: StrikeConfig) -> Dict[str, Any]:
        """Enhance option data with calculated fields."""
        enhanced_data = option_data.copy()
        
        # Add metadata
        enhanced_data['index_name'] = index_name
        enhanced_data['collection_timestamp'] = datetime.now().isoformat()
        enhanced_data['atm_strike'] = strike_config.center_strike
        
        # Calculate moneyness
        strike = option_data.get('strike', 0)
        atm_strike = strike_config.center_strike
        
        if atm_strike > 0:
            enhanced_data['moneyness'] = (strike - atm_strike) / atm_strike * 100
            
            # Classify option position
            if strike == atm_strike:
                enhanced_data['position_type'] = 'ATM'
            elif (strike > atm_strike and option_data.get('option_type') == 'CE') or \
                 (strike < atm_strike and option_data.get('option_type') == 'PE'):
                enhanced_data['position_type'] = 'ITM'
            else:
                enhanced_data['position_type'] = 'OTM'
        
        # Calculate time value (if we have intrinsic value data)
        last_price = option_data.get('last_price', 0)
        if last_price > 0 and 'intrinsic_value' in option_data:
            intrinsic_value = option_data['intrinsic_value']
            enhanced_data['time_value'] = max(0, last_price - intrinsic_value)
        
        return enhanced_data
    
    def _update_stats(self, index_name: str, result: CollectionResult):
        """Update collection statistics."""
        self.stats.total_collections += 1
        self.stats.total_processing_time += result.collection_time
        
        if result.success:
            self.stats.successful_collections += 1
            self.stats.total_options_processed += result.successful_instruments
        else:
            self.stats.failed_collections += 1
        
        # Update index-specific stats
        if index_name not in self.stats.index_stats:
            self.stats.index_stats[index_name] = {
                'collections': 0,
                'successful_collections': 0,
                'total_processing_time': 0.0,
                'options_processed': 0
            }
        
        index_stats = self.stats.index_stats[index_name]
        index_stats['collections'] += 1
        index_stats['total_processing_time'] += result.collection_time
        
        if result.success:
            index_stats['successful_collections'] += 1
            index_stats['options_processed'] += result.successful_instruments
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get comprehensive collection statistics."""
        return {
            'overall': {
                'total_collections': self.stats.total_collections,
                'success_rate': self.stats.success_rate,
                'average_collection_time': self.stats.average_collection_time,
                'total_options_processed': self.stats.total_options_processed,
                'error_count': self.stats.error_count,
                'last_error': self.stats.last_error
            },
            'by_index': {
                index: {
                    'collections': stats['collections'],
                    'success_rate': (stats['successful_collections'] / max(1, stats['collections'])) * 100,
                    'avg_processing_time': stats['total_processing_time'] / max(1, stats['collections']),
                    'options_processed': stats['options_processed']
                }
                for index, stats in self.stats.index_stats.items()
            },
            'configuration': {
                'max_workers': self.max_workers,
                'timeout_seconds': self.timeout_seconds,
                'quality_threshold': self.quality_threshold,
                'batch_size': self.batch_size,
                'cache_ttl': self.cache_ttl
            }
        }
    
    def clear_cache(self):
        """Clear ATM strike cache."""
        with self._cache_lock:
            self._atm_cache.clear()
        logger.info("🧹 ATM strike cache cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = {
            'status': 'healthy',
            'thread_pool_active': not self.thread_pool._shutdown,
            'cache_size': len(self._atm_cache),
            'stats': self.get_collection_stats()['overall']
        }
        
        # Check if too many recent errors
        if self.stats.error_count > 10:
            health['status'] = 'degraded'
            health['warning'] = f"High error count: {self.stats.error_count}"
        
        return health
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            self.thread_pool.shutdown(wait=True, timeout=30)
            self.clear_cache()
            logger.info("✅ ATM Options Collector cleanup completed")
        except Exception as e:
            logger.error(f"🔴 Cleanup error: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass