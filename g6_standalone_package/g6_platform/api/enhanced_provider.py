#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Enhanced KiteDataProvider - G6.1 Platform v2.0
Author: AI Assistant (Optimized for 10x scaling and performance)

Features:
- Advanced rate limiting with exponential backoff
- Connection pooling and concurrent requests
- Intelligent caching with TTL
- Batch processing optimization
- Health monitoring and metrics
- Auto-recovery mechanisms
"""

import os
import time
import logging
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union, Optional, Tuple
from collections import defaultdict, deque
import json
import hashlib
from dataclasses import dataclass
from enum import Enum

try:
    from kiteconnect import KiteConnect
    KITECONNECT_AVAILABLE = True
except ImportError:
    KITECONNECT_AVAILABLE = False

from config_manager import get_config

class RequestPriority(Enum):
    """📊 Request priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class CacheEntry:
    """📦 Cache entry with TTL."""
    data: Any
    timestamp: float
    ttl: float
    
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl

@dataclass
class RequestMetrics:
    """📊 Request performance metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_latency: float = 0.0
    
    @property
    def success_rate(self) -> float:
        return self.successful_requests / max(1, self.total_requests)
    
    @property
    def average_latency(self) -> float:
        return self.total_latency / max(1, self.successful_requests)
    
    @property
    def cache_hit_rate(self) -> float:
        total_cache_requests = self.cache_hits + self.cache_misses
        return self.cache_hits / max(1, total_cache_requests)

class EnhancedKiteDataProvider:
    """🚀 High-performance KiteDataProvider with 10x scaling capability."""
    
    def __init__(self, api_key: str, access_token: str, **kwargs):
        """Initialize enhanced data provider."""
        self.config = get_config()
        self.logger = logging.getLogger(f"{__name__}.EnhancedKiteProvider")
        
        # Core Kite connection
        if not KITECONNECT_AVAILABLE:
            raise ImportError("KiteConnect library not available")
        
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        
        # Rate limiting configuration
        rate_limits = self.config.get_rate_limits()
        self.requests_per_minute = rate_limits['requests_per_minute']
        self.burst_allowance = rate_limits['burst_allowance']
        self.max_concurrent = rate_limits['max_concurrent']
        
        # Rate limiting state
        self.request_queue = deque()
        self.rate_limit_lock = threading.RLock()
        self.last_request_time = 0
        self.request_count_window = 0
        self.window_start_time = time.time()
        self.backoff_until = 0
        
        # Caching system
        cache_config = self.config.get('data_collection.performance.caching', {})
        self.cache_enabled = cache_config.get('enabled', True)
        self.cache_ttl = cache_config.get('ttl_seconds', 5)
        self.max_cache_size = cache_config.get('max_cache_size', 1000)
        self.cache = {}
        self.cache_lock = threading.RLock()
        
        # Concurrent execution
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent)
        
        # Metrics and monitoring
        self.metrics = RequestMetrics()
        self.health_status = {
            'connected': False,
            'last_successful_request': None,
            'consecutive_failures': 0,
            'rate_limit_breaches': 0
        }
        
        # Batch processing
        batch_config = self.config.get('data_collection.performance.batch_processing', {})
        self.batch_enabled = batch_config.get('enabled', True)
        self.batch_size = batch_config.get('batch_size', 25)
        self.batch_delay = batch_config.get('batch_delay_ms', 100) / 1000.0
        
        # Initialize connection
        self._initialize_connection()
        
        self.logger.info("✅ Enhanced KiteDataProvider initialized")
        self.logger.info(f"🎛️ Rate limits: {self.requests_per_minute}/min, {self.max_concurrent} concurrent")
        self.logger.info(f"🎛️ Cache: {'✅ Enabled' if self.cache_enabled else '❌ Disabled'} (TTL: {self.cache_ttl}s)")
        self.logger.info(f"🎛️ Batching: {'✅ Enabled' if self.batch_enabled else '❌ Disabled'} (Size: {self.batch_size})")
    
    def _initialize_connection(self):
        """🔌 Initialize and test Kite connection."""
        try:
            profile = self.kite.profile()
            self.health_status['connected'] = True
            self.health_status['last_successful_request'] = time.time()
            self.logger.info(f"✅ Connected to Kite as: {profile.get('user_name', 'Unknown')}")
        except Exception as e:
            self.health_status['connected'] = False
            self.health_status['consecutive_failures'] += 1
            self.logger.error(f"🔴 Kite connection failed: {e}")
            raise
    
    def _get_cache_key(self, method: str, params: Any) -> str:
        """🔑 Generate cache key for request."""
        if isinstance(params, (list, dict)):
            params_str = json.dumps(params, sort_keys=True)
        else:
            params_str = str(params)
        
        cache_input = f"{method}:{params_str}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """📦 Get data from cache if valid."""
        if not self.cache_enabled:
            return None
        
        with self.cache_lock:
            entry = self.cache.get(cache_key)
            if entry and not entry.is_expired():
                self.metrics.cache_hits += 1
                return entry.data
            elif entry:
                # Remove expired entry
                del self.cache[cache_key]
        
        self.metrics.cache_misses += 1
        return None
    
    def _set_cache(self, cache_key: str, data: Any, ttl: Optional[float] = None):
        """📦 Set data in cache."""
        if not self.cache_enabled:
            return
        
        ttl = ttl or self.cache_ttl
        
        with self.cache_lock:
            # Evict oldest entries if cache is full
            if len(self.cache) >= self.max_cache_size:
                oldest_key = min(self.cache.keys(), 
                               key=lambda k: self.cache[k].timestamp)
                del self.cache[oldest_key]
            
            self.cache[cache_key] = CacheEntry(
                data=data,
                timestamp=time.time(),
                ttl=ttl
            )
    
    def _check_rate_limit(self, priority: RequestPriority = RequestPriority.NORMAL) -> bool:
        """🚦 Check if request can proceed based on rate limits."""
        with self.rate_limit_lock:
            current_time = time.time()
            
            # Check if we're in backoff period
            if current_time < self.backoff_until:
                return False
            
            # Reset window if needed
            if current_time - self.window_start_time >= 60:
                self.request_count_window = 0
                self.window_start_time = current_time
            
            # Check rate limits based on priority
            if priority == RequestPriority.CRITICAL:
                # Critical requests always allowed if not in backoff
                return True
            elif priority == RequestPriority.HIGH:
                # High priority gets 80% of rate limit
                limit = int(self.requests_per_minute * 0.8)
            elif priority == RequestPriority.NORMAL:
                # Normal gets 60% of rate limit
                limit = int(self.requests_per_minute * 0.6)
            else:  # LOW priority
                # Low priority gets remaining 40%
                limit = int(self.requests_per_minute * 0.4)
            
            if self.request_count_window >= limit:
                return False
            
            # Check minimum interval between requests
            min_interval = 60.0 / self.requests_per_minute
            if current_time - self.last_request_time < min_interval:
                return False
            
            return True
    
    def _wait_for_rate_limit(self, priority: RequestPriority = RequestPriority.NORMAL):
        """⏱️ Wait until rate limit allows request."""
        max_wait = 60  # Maximum wait time in seconds
        wait_start = time.time()
        
        while not self._check_rate_limit(priority):
            if time.time() - wait_start > max_wait:
                raise Exception("Rate limit wait timeout")
            time.sleep(0.1)
    
    def _record_request(self, success: bool, latency: float = 0, rate_limited: bool = False):
        """📊 Record request metrics."""
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
            self.metrics.total_latency += latency
            self.health_status['last_successful_request'] = time.time()
            self.health_status['consecutive_failures'] = 0
        else:
            self.metrics.failed_requests += 1
            self.health_status['consecutive_failures'] += 1
        
        if rate_limited:
            self.metrics.rate_limited_requests += 1
            self.health_status['rate_limit_breaches'] += 1
        
        with self.rate_limit_lock:
            self.last_request_time = time.time()
            self.request_count_window += 1
    
    def _handle_rate_limit_response(self, error: Exception):
        """🚫 Handle rate limit responses with exponential backoff."""
        if "Too many requests" in str(error) or "rate limit" in str(error).lower():
            self.health_status['rate_limit_breaches'] += 1
            
            # Exponential backoff
            backoff_time = min(2 ** self.health_status['rate_limit_breaches'], 60)
            self.backoff_until = time.time() + backoff_time
            
            self.logger.warning(f"⚠️ Rate limited, backing off for {backoff_time}s")
            return True
        return False
    
    def _make_api_request(self, method: str, params: Any, 
                         priority: RequestPriority = RequestPriority.NORMAL,
                         cache_ttl: Optional[float] = None) -> Any:
        """🌐 Make API request with rate limiting, caching, and error handling."""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(method, params)
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Wait for rate limit
            self._wait_for_rate_limit(priority)
            
            # Make API call
            if method == "ltp":
                result = self.kite.ltp(params)
            elif method == "quote":
                result = self.kite.quote(params)
            elif method == "instruments":
                result = self.kite.instruments(params)
            elif method == "ohlc":
                result = self.kite.ohlc(params)
            else:
                raise ValueError(f"Unknown API method: {method}")
            
            # Record success
            latency = time.time() - start_time
            self._record_request(success=True, latency=latency)
            
            # Cache result
            self._set_cache(cache_key, result, cache_ttl)
            
            return result
            
        except Exception as e:
            latency = time.time() - start_time
            rate_limited = self._handle_rate_limit_response(e)
            self._record_request(success=False, latency=latency, rate_limited=rate_limited)
            
            if rate_limited:
                # Retry once after backoff
                time.sleep(min(2, (time.time() - start_time) * 2))
                try:
                    return self._make_api_request(method, params, priority, cache_ttl)
                except Exception as retry_error:
                    self.logger.error(f"🔴 API retry failed: {retry_error}")
                    raise retry_error
            else:
                self.logger.error(f"🔴 API request failed: {e}")
                raise e
    
    def get_ltp(self, instruments: Union[str, List[str]], 
                priority: RequestPriority = RequestPriority.NORMAL) -> Dict[str, float]:
        """💰 Get Last Traded Price with enhanced performance."""
        try:
            if isinstance(instruments, str):
                instruments = [instruments]
            
            result = self._make_api_request("ltp", instruments, priority)
            
            # Extract LTP values
            ltp_values = {}
            for instrument, data in result.items():
                if 'last_price' in data:
                    ltp_values[instrument] = data['last_price']
            
            self.logger.debug(f"✅ Retrieved LTP for {len(ltp_values)} instruments")
            return ltp_values
            
        except Exception as e:
            self.logger.error(f"🔴 LTP request failed: {e}")
            return {}
    
    def get_quote(self, instruments: Union[str, List[str]],
                  priority: RequestPriority = RequestPriority.NORMAL) -> Dict[str, Any]:
        """📊 Get quotes with enhanced performance."""
        try:
            if isinstance(instruments, str):
                instruments = [instruments]
            
            result = self._make_api_request("quote", instruments, priority)
            
            self.logger.debug(f"✅ Retrieved quotes for {len(instruments)} instruments")
            return result
            
        except Exception as e:
            self.logger.error(f"🔴 Quote request failed: {e}")
            return {}
    
    def get_quotes_batch(self, instruments: List[str], 
                        priority: RequestPriority = RequestPriority.NORMAL) -> Dict[str, Any]:
        """📊 Get quotes in optimized batches."""
        if not self.batch_enabled or len(instruments) <= self.batch_size:
            return self.get_quote(instruments, priority)
        
        all_quotes = {}
        
        # Process in batches
        for i in range(0, len(instruments), self.batch_size):
            batch = instruments[i:i + self.batch_size]
            
            try:
                batch_quotes = self.get_quote(batch, priority)
                all_quotes.update(batch_quotes)
                
                # Delay between batches (except last one)
                if i + self.batch_size < len(instruments):
                    time.sleep(self.batch_delay)
                    
            except Exception as e:
                self.logger.error(f"🔴 Batch {i//self.batch_size + 1} failed: {e}")
        
        return all_quotes
    
    def get_quotes_concurrent(self, instrument_batches: List[List[str]]) -> Dict[str, Any]:
        """🚀 Get quotes using concurrent requests for maximum throughput."""
        all_quotes = {}
        
        # Submit concurrent requests
        futures = []
        for batch in instrument_batches:
            future = self.executor.submit(self.get_quote, batch, RequestPriority.HIGH)
            futures.append(future)
        
        # Collect results
        for future in as_completed(futures, timeout=30):
            try:
                batch_result = future.result()
                all_quotes.update(batch_result)
            except Exception as e:
                self.logger.error(f"🔴 Concurrent batch failed: {e}")
        
        return all_quotes
    
    def get_atm_strike(self, index_name: str, expiry: Optional[str] = None) -> float:
        """🎯 Get ATM strike price for index."""
        try:
            # Map index name to instrument
            instrument_map = {
                'NIFTY': 'NSE:NIFTY 50',
                'BANKNIFTY': 'NSE:NIFTY BANK',
                'FINNIFTY': 'NSE:NIFTY FIN SERVICE',
                'MIDCPNIFTY': 'NSE:NIFTY MID SELECT'
            }
            
            instrument = instrument_map.get(index_name.upper())
            if not instrument:
                raise ValueError(f"Unknown index: {index_name}")
            
            # Get current price
            ltp_data = self.get_ltp([instrument], RequestPriority.HIGH)
            spot_price = ltp_data.get(instrument, 0)
            
            if spot_price == 0:
                raise ValueError(f"Could not get spot price for {index_name}")
            
            # Calculate ATM strike based on index
            if index_name.upper() == 'NIFTY':
                strike_interval = 50
            elif index_name.upper() == 'BANKNIFTY':
                strike_interval = 100
            else:
                strike_interval = 50  # Default
            
            atm_strike = round(spot_price / strike_interval) * strike_interval
            
            self.logger.debug(f"🎯 ATM strike for {index_name}: {atm_strike} (spot: {spot_price})")
            return atm_strike
            
        except Exception as e:
            self.logger.error(f"🔴 ATM strike calculation failed for {index_name}: {e}")
            raise
    
    def check_health(self) -> Dict[str, Any]:
        """❤️ Check provider health and return metrics."""
        current_time = time.time()
        
        # Calculate health score
        health_score = 1.0
        if self.health_status['consecutive_failures'] > 0:
            health_score *= max(0.1, 1.0 - (self.health_status['consecutive_failures'] * 0.1))
        
        if self.metrics.success_rate < 0.9:
            health_score *= self.metrics.success_rate
        
        # Determine connection status
        last_success = self.health_status.get('last_successful_request', 0)
        connection_healthy = (current_time - last_success) < 300  # 5 minutes
        
        return {
            'status': 'healthy' if connection_healthy and health_score > 0.7 else 'degraded',
            'connected': self.health_status['connected'],
            'health_score': round(health_score, 2),
            'metrics': {
                'total_requests': self.metrics.total_requests,
                'success_rate': round(self.metrics.success_rate, 3),
                'average_latency': round(self.metrics.average_latency, 3),
                'cache_hit_rate': round(self.metrics.cache_hit_rate, 3),
                'rate_limited_requests': self.metrics.rate_limited_requests,
                'consecutive_failures': self.health_status['consecutive_failures']
            },
            'rate_limiting': {
                'requests_per_minute': self.requests_per_minute,
                'current_window_count': self.request_count_window,
                'backoff_until': max(0, self.backoff_until - current_time)
            },
            'cache': {
                'enabled': self.cache_enabled,
                'size': len(self.cache),
                'max_size': self.max_cache_size
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """📊 Get detailed performance statistics."""
        health = self.check_health()
        
        return {
            'performance': health['metrics'],
            'configuration': {
                'rate_limit': self.requests_per_minute,
                'max_concurrent': self.max_concurrent,
                'batch_size': self.batch_size,
                'cache_ttl': self.cache_ttl
            },
            'health': {
                'status': health['status'],
                'health_score': health['health_score'],
                'connected': health['connected']
            }
        }
    
    def clear_cache(self):
        """🧹 Clear all cached data."""
        with self.cache_lock:
            self.cache.clear()
        self.logger.info("🧹 Cache cleared")
    
    def close(self):
        """🔒 Close provider and cleanup resources."""
        try:
            self.executor.shutdown(wait=True, timeout=5)
            self.clear_cache()
            self.logger.info("🔒 Enhanced KiteDataProvider closed")
        except Exception as e:
            self.logger.error(f"🔴 Error during close: {e}")