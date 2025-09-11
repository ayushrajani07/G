#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔗 Kite Data Provider - G6 Platform v3.0
Consolidated and enhanced API integration with comprehensive error handling.

Restructured from: enhanced_kite_provider.py
Features:
- Advanced rate limiting with exponential backoff
- Intelligent caching with TTL management
- Connection pooling and retry mechanisms
- Thread-safe operations
- Comprehensive error handling and resilience
- Memory management and cleanup
"""

import os
import time
import logging
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union, Optional, Tuple, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import weakref

# Kite Connect integration
try:
    from kiteconnect import KiteConnect
    from kiteconnect.exceptions import KiteException, TokenException, NetworkException
    KITECONNECT_AVAILABLE = True
except ImportError:
    KITECONNECT_AVAILABLE = False
    KiteConnect = None
    KiteException = Exception
    TokenException = Exception  
    NetworkException = Exception

logger = logging.getLogger(__name__)

class RequestPriority(Enum):
    """Request priority levels for queue management."""
    LOW = 1
    NORMAL = 2  
    HIGH = 3
    CRITICAL = 4

@dataclass
class CacheEntry:
    """Cache entry with TTL and metadata."""
    data: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.timestamp > self.ttl
    
    def access(self) -> Any:
        """Access cache entry and update statistics."""
        self.access_count += 1
        self.last_access = time.time()
        return self.data

@dataclass
class RateLimitState:
    """Rate limiting state tracking."""
    tokens: float
    last_refill: float
    request_count: int = 0
    rate_limit_hits: int = 0
    backoff_factor: float = 1.0
    last_request: float = 0.0

@dataclass
class ConnectionMetrics:
    """Connection and performance metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_latency: float = 0.0
    connection_errors: int = 0
    timeout_errors: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate request success rate."""
        return (self.successful_requests / max(1, self.total_requests)) * 100
    
    @property
    def average_latency(self) -> float:
        """Calculate average request latency."""
        return self.total_latency / max(1, self.successful_requests)
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_cache_requests = self.cache_hits + self.cache_misses
        return (self.cache_hits / max(1, total_cache_requests)) * 100

class TokenBucketRateLimiter:
    """
    Advanced token bucket rate limiter with exponential backoff.
    """
    
    def __init__(self, 
                 requests_per_minute: int = 200,
                 burst_capacity: int = 50,
                 backoff_factor: float = 2.0,
                 max_backoff: float = 300.0):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Base rate limit
            burst_capacity: Burst allowance
            backoff_factor: Exponential backoff multiplier
            max_backoff: Maximum backoff time
        """
        self.capacity = requests_per_minute
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.burst_capacity = burst_capacity
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff
        
        self.state = RateLimitState(
            tokens=float(requests_per_minute),
            last_refill=time.time()
        )
        
        self._lock = threading.Lock()
    
    def acquire(self, priority: RequestPriority = RequestPriority.NORMAL) -> bool:
        """
        Acquire a rate limit token.
        
        Args:
            priority: Request priority level
            
        Returns:
            True if token acquired, False if rate limited
        """
        with self._lock:
            now = time.time()
            
            # Refill tokens based on elapsed time
            elapsed = now - self.state.last_refill
            tokens_to_add = elapsed * self.refill_rate
            self.state.tokens = min(self.capacity + self.burst_capacity, 
                                  self.state.tokens + tokens_to_add)
            self.state.last_refill = now
            
            # Priority-based token allocation
            required_tokens = self._get_required_tokens(priority)
            
            if self.state.tokens >= required_tokens:
                self.state.tokens -= required_tokens
                self.state.request_count += 1
                self.state.last_request = now
                
                # Reset backoff on successful acquisition
                self.state.backoff_factor = 1.0
                
                return True
            else:
                # Rate limited - apply exponential backoff
                self.state.rate_limit_hits += 1
                self.state.backoff_factor = min(
                    self.max_backoff,
                    self.state.backoff_factor * self.backoff_factor
                )
                
                return False
    
    def _get_required_tokens(self, priority: RequestPriority) -> float:
        """Get required tokens based on priority."""
        token_map = {
            RequestPriority.LOW: 1.0,
            RequestPriority.NORMAL: 1.0,
            RequestPriority.HIGH: 0.8,
            RequestPriority.CRITICAL: 0.5
        }
        return token_map.get(priority, 1.0)
    
    def get_wait_time(self) -> float:
        """Get recommended wait time before next request."""
        if self.state.tokens >= 1.0:
            return 0.0
        
        # Calculate time until next token is available
        tokens_needed = 1.0 - self.state.tokens
        wait_time = tokens_needed / self.refill_rate
        
        # Apply backoff if we've been rate limited recently
        if self.state.backoff_factor > 1.0:
            wait_time *= self.state.backoff_factor
        
        return min(wait_time, self.max_backoff)
    
    def get_status(self) -> Dict[str, Any]:
        """Get rate limiter status."""
        with self._lock:
            return {
                'tokens': self.state.tokens,
                'capacity': self.capacity,
                'requests': self.state.request_count,
                'rate_limit_hits': self.state.rate_limit_hits,
                'backoff_factor': self.state.backoff_factor,
                'time_since_last_request': time.time() - self.state.last_request
            }

class IntelligentCache:
    """
    Intelligent caching system with TTL, LRU eviction, and automatic cleanup.
    """
    
    def __init__(self, 
                 max_size: int = 1000,
                 default_ttl: float = 60.0,
                 cleanup_interval: float = 300.0):
        """
        Initialize cache system.
        
        Args:
            max_size: Maximum cache size
            default_ttl: Default TTL in seconds
            cleanup_interval: Cleanup interval in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order = deque()  # For LRU tracking
        self._lock = threading.RLock()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True,
            name="CacheCleanup"
        )
        self._cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            
            if entry.is_expired():
                self._remove_entry(key)
                return None
            
            # Update access statistics
            data = entry.access()
            
            # Move to end of access order (most recently used)
            try:
                self._access_order.remove(key)
            except ValueError:
                pass  # Key not in order, that's ok
            self._access_order.append(key)
            
            return data
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put item in cache."""
        with self._lock:
            ttl = ttl or self.default_ttl
            
            # Create cache entry
            entry = CacheEntry(
                data=value,
                timestamp=time.time(),
                ttl=ttl
            )
            
            # Check if we need to evict entries
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            # Store entry
            self._cache[key] = entry
            
            # Update access order
            try:
                self._access_order.remove(key)
            except ValueError:
                pass
            self._access_order.append(key)
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache."""
        self._cache.pop(key, None)
        try:
            self._access_order.remove(key)
        except ValueError:
            pass
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self._access_order:
            lru_key = self._access_order.popleft()
            self._cache.pop(lru_key, None)
    
    def _cleanup_worker(self) -> None:
        """Background cleanup worker."""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    def _cleanup_expired(self) -> None:
        """Clean up expired entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                self._remove_entry(key)
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_accesses = sum(entry.access_count for entry in self._cache.values())
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'utilization': (len(self._cache) / self.max_size) * 100,
                'total_accesses': total_accesses,
                'average_accesses': total_accesses / max(1, len(self._cache))
            }

class KiteDataProvider:
    """
    🔗 Enhanced Kite Connect data provider with production-grade features.
    
    Provides high-performance, resilient access to Kite Connect API with:
    - Advanced rate limiting with exponential backoff
    - Intelligent caching with TTL management  
    - Connection pooling and retry mechanisms
    - Comprehensive error handling and recovery
    - Memory management and resource cleanup
    """
    
    # Market instrument mappings
    INSTRUMENT_MAPPING = {
        'NIFTY': 'NSE:NIFTY 50',
        'BANKNIFTY': 'NSE:NIFTY BANK', 
        'FINNIFTY': 'NSE:NIFTY FIN SERVICE',
        'MIDCPNIFTY': 'NSE:NIFTY MID SELECT',
        'SENSEX': 'BSE:SENSEX',
        'BANKEX': 'BSE:BANKEX'
    }
    
    def __init__(self,
                 api_key: str,
                 access_token: str,
                 requests_per_minute: int = 200,
                 burst_capacity: int = 50,
                 cache_ttl: int = 60,
                 cache_size: int = 1000,
                 max_retries: int = 3,
                 connection_timeout: int = 30,
                 read_timeout: int = 60):
        """
        Initialize Kite data provider.
        
        Args:
            api_key: Kite Connect API key
            access_token: Kite Connect access token
            requests_per_minute: Rate limit for requests
            burst_capacity: Burst allowance for rate limiting
            cache_ttl: Cache TTL in seconds
            cache_size: Maximum cache size
            max_retries: Maximum retry attempts
            connection_timeout: Connection timeout
            read_timeout: Read timeout
        """
        if not KITECONNECT_AVAILABLE:
            raise ImportError("KiteConnect library not available. Install with: pip install kiteconnect")
        
        self.api_key = api_key
        self.access_token = access_token
        self.max_retries = max_retries
        self.connection_timeout = connection_timeout
        self.read_timeout = read_timeout
        
        # Initialize Kite Connect
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        
        # Rate limiting
        self.rate_limiter = TokenBucketRateLimiter(
            requests_per_minute=requests_per_minute,
            burst_capacity=burst_capacity
        )
        
        # Caching
        self.cache = IntelligentCache(
            max_size=cache_size,
            default_ttl=cache_ttl
        )
        
        # Metrics tracking
        self.metrics = ConnectionMetrics()
        
        # Thread pool for concurrent requests
        self.thread_pool = ThreadPoolExecutor(
            max_workers=10,
            thread_name_prefix="KiteAPI"
        )
        
        # Connection state
        self._connected = False
        self._last_health_check = 0
        self._health_check_interval = 300  # 5 minutes
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.info("🔗 Kite data provider initialized")
        
        # Perform initial health check
        self._perform_health_check()
    
    def _perform_health_check(self) -> bool:
        """Perform API health check."""
        try:
            now = time.time()
            if now - self._last_health_check < self._health_check_interval:
                return self._connected
            
            # Simple API call to check connectivity
            profile = self.kite.profile()
            self._connected = bool(profile.get('user_id'))
            self._last_health_check = now
            
            if self._connected:
                logger.debug("✅ Kite API health check passed")
            else:
                logger.warning("⚠️ Kite API health check failed")
            
            return self._connected
            
        except Exception as e:
            logger.error(f"🔴 Kite API health check error: {e}")
            self._connected = False
            return False
    
    def _make_request(self, 
                     request_func: Callable,
                     cache_key: Optional[str] = None,
                     cache_ttl: Optional[float] = None,
                     priority: RequestPriority = RequestPriority.NORMAL,
                     retry_count: int = 0) -> Any:
        """
        Make API request with rate limiting, caching, and error handling.
        
        Args:
            request_func: Function to execute API request
            cache_key: Cache key (if caching enabled)
            cache_ttl: Cache TTL override
            priority: Request priority
            retry_count: Current retry count
            
        Returns:
            API response data
        """
        # Check cache first
        if cache_key:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                self.metrics.cache_hits += 1
                return cached_data
            else:
                self.metrics.cache_misses += 1
        
        # Check rate limiting
        if not self.rate_limiter.acquire(priority):
            wait_time = self.rate_limiter.get_wait_time()
            logger.warning(f"⏱️ Rate limited, waiting {wait_time:.2f}s")
            time.sleep(wait_time)
            
            # Retry after waiting
            if not self.rate_limiter.acquire(priority):
                self.metrics.rate_limited_requests += 1
                raise Exception("Rate limit exceeded after wait")
        
        # Execute request
        start_time = time.time()
        try:
            self.metrics.total_requests += 1
            
            # Execute the actual API call
            response = request_func()
            
            # Track timing
            latency = time.time() - start_time
            self.metrics.total_latency += latency
            self.metrics.successful_requests += 1
            
            # Cache response if cache key provided
            if cache_key and response is not None:
                self.cache.put(cache_key, response, cache_ttl)
            
            return response
            
        except TokenException as e:
            logger.error(f"🔴 Kite token error: {e}")
            self.metrics.failed_requests += 1
            raise
            
        except NetworkException as e:
            logger.warning(f"🌐 Network error: {e}")
            self.metrics.connection_errors += 1
            
            # Retry on network errors
            if retry_count < self.max_retries:
                backoff_time = 2 ** retry_count
                logger.info(f"🔄 Retrying in {backoff_time}s (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(backoff_time)
                return self._make_request(request_func, cache_key, cache_ttl, priority, retry_count + 1)
            
            self.metrics.failed_requests += 1
            raise
            
        except KiteException as e:
            logger.error(f"🔴 Kite API error: {e}")
            self.metrics.failed_requests += 1
            raise
            
        except Exception as e:
            logger.error(f"🔴 Unexpected error: {e}")
            self.metrics.failed_requests += 1
            raise
    
    def get_quote(self, instruments: Union[str, List[str]], priority: RequestPriority = RequestPriority.NORMAL) -> Dict[str, Any]:
        """
        Get quote data for instruments.
        
        Args:
            instruments: Instrument symbol(s)
            priority: Request priority
            
        Returns:
            Quote data dictionary
        """
        if isinstance(instruments, str):
            instruments = [instruments]
        
        cache_key = f"quote:{':'.join(sorted(instruments))}"
        
        def request_func():
            return self.kite.quote(instruments)
        
        return self._make_request(
            request_func=request_func,
            cache_key=cache_key,
            cache_ttl=30,  # Short TTL for quotes
            priority=priority
        )
    
    def get_instruments(self, exchange: str = None, priority: RequestPriority = RequestPriority.LOW) -> List[Dict[str, Any]]:
        """
        Get instruments list.
        
        Args:
            exchange: Exchange filter
            priority: Request priority
            
        Returns:
            List of instruments
        """
        cache_key = f"instruments:{exchange or 'all'}"
        
        def request_func():
            if exchange:
                return self.kite.instruments(exchange)
            else:
                return self.kite.instruments()
        
        return self._make_request(
            request_func=request_func,
            cache_key=cache_key,
            cache_ttl=3600,  # Long TTL for instruments
            priority=priority
        )
    
    def get_historical_data(self, 
                          instrument_token: int,
                          from_date: datetime,
                          to_date: datetime,
                          interval: str = "day",
                          priority: RequestPriority = RequestPriority.NORMAL) -> List[Dict[str, Any]]:
        """
        Get historical data.
        
        Args:
            instrument_token: Instrument token
            from_date: Start date
            to_date: End date  
            interval: Data interval
            priority: Request priority
            
        Returns:
            Historical data list
        """
        cache_key = f"historical:{instrument_token}:{from_date.date()}:{to_date.date()}:{interval}"
        
        def request_func():
            return self.kite.historical_data(instrument_token, from_date, to_date, interval)
        
        return self._make_request(
            request_func=request_func,
            cache_key=cache_key,
            cache_ttl=1800,  # 30 minute TTL for historical data
            priority=priority
        )
    
    def get_atm_strike(self, index_name: str) -> float:
        """
        Get ATM strike for an index.
        
        Args:
            index_name: Index name (NIFTY, BANKNIFTY, etc.)
            
        Returns:
            ATM strike price
        """
        instrument = self.INSTRUMENT_MAPPING.get(index_name)
        if not instrument:
            raise ValueError(f"Unknown index: {index_name}")
        
        # Get current market price
        quote_data = self.get_quote(instrument, RequestPriority.HIGH)
        
        if instrument not in quote_data:
            raise ValueError(f"No quote data for {instrument}")
        
        current_price = quote_data[instrument]['last_price']
        
        # Calculate ATM strike based on index-specific intervals
        strike_intervals = {
            'NIFTY': 50,
            'BANKNIFTY': 100,
            'FINNIFTY': 50,
            'MIDCPNIFTY': 25,
            'SENSEX': 100,
            'BANKEX': 100
        }
        
        interval = strike_intervals.get(index_name, 50)
        atm_strike = round(current_price / interval) * interval
        
        logger.debug(f"📍 {index_name} ATM strike: {atm_strike} (current: {current_price})")
        
        return atm_strike
    
    def get_options_data(self, 
                        index_name: str,
                        strikes: List[float],
                        expiry: str = None,
                        option_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get options data for specified strikes.
        
        Args:
            index_name: Index name
            strikes: List of strike prices
            expiry: Expiry date (YYYY-MM-DD)
            option_types: Option types (CE, PE)
            
        Returns:
            List of options data
        """
        option_types = option_types or ['CE', 'PE']
        
        # Build instrument symbols
        instruments = []
        for strike in strikes:
            for option_type in option_types:
                # Format: NIFTY24950CE, BANKNIFTY45000PE, etc.
                if expiry:
                    # Extract year and date from expiry for symbol
                    year = expiry[2:4]  # Last 2 digits of year
                    month_day = expiry[5:].replace('-', '')
                    symbol = f"{index_name}{year}{month_day}{int(strike)}{option_type}"
                else:
                    # Use nearest expiry
                    symbol = f"{index_name}{int(strike)}{option_type}"
                
                instruments.append(symbol)
        
        # Get quote data for all instruments
        if instruments:
            try:
                quote_data = self.get_quote(instruments, RequestPriority.HIGH)
                
                # Process and structure the data
                options_data = []
                for symbol, data in quote_data.items():
                    if data:  # Valid data received
                        options_data.append({
                            'symbol': symbol,
                            'strike': data.get('instrument_token'),
                            'option_type': symbol[-2:],  # CE or PE
                            'last_price': data.get('last_price'),
                            'volume': data.get('volume'),
                            'oi': data.get('oi'),
                            'change': data.get('net_change'),
                            'timestamp': datetime.now().isoformat()
                        })
                
                return options_data
                
            except Exception as e:
                logger.error(f"🔴 Failed to get options data: {e}")
                return []
        
        return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Health status dictionary
        """
        health = {
            'connected': False,
            'api_functional': False,
            'rate_limiter_status': self.rate_limiter.get_status(),
            'cache_stats': self.cache.get_stats(),
            'metrics': {
                'success_rate': self.metrics.success_rate,
                'average_latency': self.metrics.average_latency,
                'cache_hit_rate': self.metrics.cache_hit_rate,
                'total_requests': self.metrics.total_requests
            },
            'errors': []
        }
        
        try:
            # Check connection
            self._perform_health_check()
            health['connected'] = self._connected
            
            # Test API functionality with lightweight call
            profile = self.kite.profile()
            health['api_functional'] = bool(profile.get('user_id'))
            health['user_id'] = profile.get('user_id')
            
        except Exception as e:
            health['errors'].append(str(e))
            logger.error(f"🔴 Health check failed: {e}")
        
        return health
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics."""
        return {
            'connection': {
                'total_requests': self.metrics.total_requests,
                'successful_requests': self.metrics.successful_requests,
                'failed_requests': self.metrics.failed_requests,
                'success_rate': self.metrics.success_rate,
                'average_latency': self.metrics.average_latency,
                'connection_errors': self.metrics.connection_errors,
                'timeout_errors': self.metrics.timeout_errors
            },
            'rate_limiting': self.rate_limiter.get_status(),
            'cache': self.cache.get_stats(),
            'health': {
                'connected': self._connected,
                'last_health_check': self._last_health_check
            }
        }
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            if hasattr(self, 'thread_pool'):
                self.thread_pool.shutdown(wait=True, timeout=30)
            logger.info("✅ Kite data provider cleanup completed")
        except Exception as e:
            logger.error(f"🔴 Cleanup error: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore cleanup errors in destructor