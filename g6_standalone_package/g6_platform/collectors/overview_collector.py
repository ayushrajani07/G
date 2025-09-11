#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Overview Collector - G6 Platform v3.0
Market overview and summary data collection with enhanced analytics.

Restructured from: overview_collector.py, overview_generator.py
Features:
- Comprehensive market overview generation
- Real-time market sentiment analysis
- Put-Call Ratio (PCR) calculations
- Volatility analysis and trending
- Index correlation analysis
- Performance optimization with caching
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import json

logger = logging.getLogger(__name__)

@dataclass
class MarketOverview:
    """Market overview data structure."""
    index_name: str
    timestamp: datetime
    
    # Current market data
    current_price: float
    change: float
    change_percent: float
    
    # ATM and strike data
    atm_strike: float
    total_ce_oi: int = 0
    total_pe_oi: int = 0
    total_ce_volume: int = 0
    total_pe_volume: int = 0
    
    # Calculated metrics
    pcr_oi: float = 0.0  # Put-Call Ratio by Open Interest
    pcr_volume: float = 0.0  # Put-Call Ratio by Volume
    max_pain: float = 0.0
    implied_volatility: float = 0.0
    
    # Market sentiment
    sentiment: str = "neutral"  # bullish, bearish, neutral
    sentiment_score: float = 0.0  # -1 to 1
    
    # Additional metrics
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    key_strikes: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'index_name': self.index_name,
            'timestamp': self.timestamp.isoformat(),
            'current_price': self.current_price,
            'change': self.change,
            'change_percent': self.change_percent,
            'atm_strike': self.atm_strike,
            'total_ce_oi': self.total_ce_oi,
            'total_pe_oi': self.total_pe_oi,
            'total_ce_volume': self.total_ce_volume,
            'total_pe_volume': self.total_pe_volume,
            'pcr_oi': self.pcr_oi,
            'pcr_volume': self.pcr_volume,
            'max_pain': self.max_pain,
            'implied_volatility': self.implied_volatility,
            'sentiment': self.sentiment,
            'sentiment_score': self.sentiment_score,
            'support_levels': self.support_levels,
            'resistance_levels': self.resistance_levels,
            'key_strikes': self.key_strikes
        }

@dataclass
class AnalyticsResult:
    """Analytics calculation result."""
    metric_name: str
    value: Union[float, int, str]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # 0 to 1

@dataclass
class OverviewStats:
    """Overview collection statistics."""
    total_overviews_generated: int = 0
    successful_generations: int = 0
    failed_generations: int = 0
    total_processing_time: float = 0.0
    
    # Index-specific stats
    index_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Analytics stats
    analytics_calculated: int = 0
    analytics_failed: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.successful_generations + self.failed_generations
        if total == 0:
            return 0.0
        return (self.successful_generations / total) * 100
    
    @property
    def average_processing_time(self) -> float:
        """Calculate average processing time."""
        if self.successful_generations == 0:
            return 0.0
        return self.total_processing_time / self.successful_generations

class OverviewCollector:
    """
    📊 Enhanced Overview Collector for comprehensive market analysis.
    
    Generates market overviews with advanced analytics including:
    - Put-Call Ratio analysis
    - Max Pain calculation
    - Volatility analysis
    - Market sentiment evaluation
    - Support/resistance level identification
    """
    
    def __init__(self,
                 api_provider,
                 enable_advanced_analytics: bool = True,
                 cache_duration: int = 60,
                 volatility_window: int = 20,
                 sentiment_threshold: float = 0.1):
        """
        Initialize Overview Collector.
        
        Args:
            api_provider: Data provider instance
            enable_advanced_analytics: Enable advanced calculations
            cache_duration: Cache duration in seconds
            volatility_window: Window for volatility calculations
            sentiment_threshold: Threshold for sentiment classification
        """
        self.api_provider = api_provider
        self.enable_advanced_analytics = enable_advanced_analytics
        self.cache_duration = cache_duration
        self.volatility_window = volatility_window
        self.sentiment_threshold = sentiment_threshold
        
        # Statistics tracking
        self.stats = OverviewStats()
        
        # Data storage for calculations
        self._price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=volatility_window))
        self._overview_cache: Dict[str, Tuple[MarketOverview, float]] = {}
        self._analytics_cache: Dict[str, Dict[str, AnalyticsResult]] = defaultdict(dict)
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.info("📊 Overview Collector initialized")
        logger.info(f"⚙️ Advanced analytics: {'✅ Enabled' if enable_advanced_analytics else '❌ Disabled'}")
        logger.info(f"⚙️ Cache duration: {cache_duration}s, Volatility window: {volatility_window}")
    
    def generate_market_overview(self,
                                index_name: str,
                                options_data: List[Dict[str, Any]],
                                use_cache: bool = True) -> MarketOverview:
        """
        Generate comprehensive market overview.
        
        Args:
            index_name: Index name (NIFTY, BANKNIFTY, etc.)
            options_data: Options data from collection
            use_cache: Whether to use cached data
            
        Returns:
            MarketOverview with comprehensive analysis
        """
        start_time = time.time()
        
        try:
            # Check cache first
            if use_cache:
                cached_overview = self._get_cached_overview(index_name)
                if cached_overview:
                    logger.debug(f"📊 Using cached overview for {index_name}")
                    return cached_overview
            
            logger.info(f"📊 Generating market overview for {index_name}")
            
            # Get current market data
            current_data = self._get_current_market_data(index_name)
            
            # Create base overview
            overview = MarketOverview(
                index_name=index_name,
                timestamp=datetime.now(),
                current_price=current_data['price'],
                change=current_data['change'],
                change_percent=current_data['change_percent'],
                atm_strike=current_data['atm_strike']
            )
            
            # Process options data
            self._process_options_data(overview, options_data)
            
            # Calculate analytics
            if self.enable_advanced_analytics:
                self._calculate_advanced_analytics(overview, options_data)
            
            # Cache the result
            self._cache_overview(index_name, overview)
            
            # Update statistics
            self._update_stats(index_name, start_time, True)
            
            logger.info(f"✅ Market overview generated for {index_name} in {time.time() - start_time:.2f}s")
            return overview
            
        except Exception as e:
            error_msg = f"Failed to generate overview for {index_name}: {e}"
            logger.error(f"🔴 {error_msg}")
            self._update_stats(index_name, start_time, False)
            raise
    
    def _get_current_market_data(self, index_name: str) -> Dict[str, Any]:
        """Get current market data for index."""
        try:
            # Get current price from API
            quote = self.api_provider.get_quote([index_name])
            
            if index_name not in quote:
                raise ValueError(f"No quote data for {index_name}")
            
            quote_data = quote[index_name]
            current_price = quote_data['last_price']
            
            # Get ATM strike
            atm_strike = self.api_provider.get_atm_strike(index_name)
            
            # Calculate change
            change = quote_data.get('net_change', 0)
            change_percent = quote_data.get('net_change_percentage', 0)
            
            # Store price history for volatility calculations
            with self._lock:
                self._price_history[index_name].append(current_price)
            
            return {
                'price': current_price,
                'change': change,
                'change_percent': change_percent,
                'atm_strike': atm_strike
            }
            
        except Exception as e:
            logger.error(f"🔴 Failed to get market data for {index_name}: {e}")
            raise
    
    def _process_options_data(self, overview: MarketOverview, options_data: List[Dict[str, Any]]):
        """Process options data to calculate basic metrics."""
        ce_oi_total = 0
        pe_oi_total = 0
        ce_volume_total = 0
        pe_volume_total = 0
        
        strike_oi_map = defaultdict(lambda: {'CE': 0, 'PE': 0})
        strike_volume_map = defaultdict(lambda: {'CE': 0, 'PE': 0})
        
        for option in options_data:
            option_type = option.get('option_type', '')
            strike = option.get('strike', 0)
            oi = option.get('oi', 0)
            volume = option.get('volume', 0)
            
            if option_type == 'CE':
                ce_oi_total += oi
                ce_volume_total += volume
                strike_oi_map[strike]['CE'] = oi
                strike_volume_map[strike]['CE'] = volume
            elif option_type == 'PE':
                pe_oi_total += oi
                pe_volume_total += volume
                strike_oi_map[strike]['PE'] = oi
                strike_volume_map[strike]['PE'] = volume
        
        # Update overview with totals
        overview.total_ce_oi = ce_oi_total
        overview.total_pe_oi = pe_oi_total
        overview.total_ce_volume = ce_volume_total
        overview.total_pe_volume = pe_volume_total
        
        # Calculate Put-Call Ratios
        overview.pcr_oi = pe_oi_total / max(1, ce_oi_total)
        overview.pcr_volume = pe_volume_total / max(1, ce_volume_total)
        
        # Store strike maps for advanced calculations
        overview.key_strikes = {
            'strike_oi_map': dict(strike_oi_map),
            'strike_volume_map': dict(strike_volume_map)
        }
    
    def _calculate_advanced_analytics(self, overview: MarketOverview, options_data: List[Dict[str, Any]]):
        """Calculate advanced analytics metrics."""
        try:
            # Calculate Max Pain
            overview.max_pain = self._calculate_max_pain(overview, options_data)
            
            # Calculate Implied Volatility (average)
            overview.implied_volatility = self._calculate_average_iv(options_data)
            
            # Calculate market sentiment
            sentiment_result = self._calculate_market_sentiment(overview, options_data)
            overview.sentiment = sentiment_result['sentiment']
            overview.sentiment_score = sentiment_result['score']
            
            # Identify support and resistance levels
            levels = self._identify_support_resistance(overview, options_data)
            overview.support_levels = levels['support']
            overview.resistance_levels = levels['resistance']
            
            self.stats.analytics_calculated += 1
            
        except Exception as e:
            logger.warning(f"⚠️ Advanced analytics calculation failed: {e}")
            self.stats.analytics_failed += 1
    
    def _calculate_max_pain(self, overview: MarketOverview, options_data: List[Dict[str, Any]]) -> float:
        """Calculate max pain strike price."""
        try:
            strike_pain = defaultdict(float)
            
            for option in options_data:
                strike = option.get('strike', 0)
                oi = option.get('oi', 0)
                option_type = option.get('option_type', '')
                
                if oi == 0 or strike == 0:
                    continue
                
                # Calculate pain at each strike
                for test_strike in range(int(strike * 0.8), int(strike * 1.2), 50):
                    if option_type == 'CE' and test_strike < strike:
                        pain = (strike - test_strike) * oi
                        strike_pain[test_strike] += pain
                    elif option_type == 'PE' and test_strike > strike:
                        pain = (test_strike - strike) * oi
                        strike_pain[test_strike] += pain
            
            # Find strike with minimum pain
            if strike_pain:
                max_pain_strike = min(strike_pain.keys(), key=lambda x: strike_pain[x])
                return float(max_pain_strike)
            
            return overview.atm_strike
            
        except Exception as e:
            logger.warning(f"⚠️ Max pain calculation failed: {e}")
            return overview.atm_strike
    
    def _calculate_average_iv(self, options_data: List[Dict[str, Any]]) -> float:
        """Calculate average implied volatility."""
        try:
            iv_values = []
            
            for option in options_data:
                iv = option.get('iv')
                if iv is not None and iv > 0:
                    iv_values.append(iv)
            
            if iv_values:
                return statistics.mean(iv_values)
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"⚠️ IV calculation failed: {e}")
            return 0.0
    
    def _calculate_market_sentiment(self, overview: MarketOverview, options_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate market sentiment based on multiple factors."""
        try:
            sentiment_factors = []
            
            # Factor 1: Put-Call Ratio
            pcr_oi = overview.pcr_oi
            if pcr_oi > 1.2:
                sentiment_factors.append(-0.3)  # Bearish
            elif pcr_oi < 0.8:
                sentiment_factors.append(0.3)   # Bullish
            else:
                sentiment_factors.append(0.0)   # Neutral
            
            # Factor 2: ATM vs Current Price
            price_diff = (overview.current_price - overview.atm_strike) / overview.atm_strike
            sentiment_factors.append(price_diff * 2)  # Amplify the signal
            
            # Factor 3: Volume analysis
            ce_volume_ratio = overview.total_ce_volume / max(1, overview.total_ce_volume + overview.total_pe_volume)
            if ce_volume_ratio > 0.6:
                sentiment_factors.append(0.2)   # Bullish
            elif ce_volume_ratio < 0.4:
                sentiment_factors.append(-0.2)  # Bearish
            else:
                sentiment_factors.append(0.0)   # Neutral
            
            # Calculate overall sentiment score
            sentiment_score = statistics.mean(sentiment_factors)
            sentiment_score = max(-1.0, min(1.0, sentiment_score))  # Clamp to [-1, 1]
            
            # Classify sentiment
            if sentiment_score > self.sentiment_threshold:
                sentiment = "bullish"
            elif sentiment_score < -self.sentiment_threshold:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            
            return {
                'sentiment': sentiment,
                'score': sentiment_score
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Sentiment calculation failed: {e}")
            return {'sentiment': 'neutral', 'score': 0.0}
    
    def _identify_support_resistance(self, overview: MarketOverview, options_data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """Identify support and resistance levels based on OI concentration."""
        try:
            strike_oi = defaultdict(int)
            
            # Aggregate OI by strike
            for option in options_data:
                strike = option.get('strike', 0)
                oi = option.get('oi', 0)
                if strike > 0 and oi > 0:
                    strike_oi[strike] += oi
            
            if not strike_oi:
                return {'support': [], 'resistance': []}
            
            # Find high OI strikes
            sorted_strikes = sorted(strike_oi.items(), key=lambda x: x[1], reverse=True)
            top_strikes = [strike for strike, oi in sorted_strikes[:5]]
            
            current_price = overview.current_price
            
            # Classify as support or resistance
            support_levels = [s for s in top_strikes if s < current_price][:3]
            resistance_levels = [s for s in top_strikes if s > current_price][:3]
            
            return {
                'support': sorted(support_levels, reverse=True),
                'resistance': sorted(resistance_levels)
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Support/resistance calculation failed: {e}")
            return {'support': [], 'resistance': []}
    
    def _get_cached_overview(self, index_name: str) -> Optional[MarketOverview]:
        """Get cached overview if still valid."""
        with self._lock:
            cached_data = self._overview_cache.get(index_name)
            if cached_data:
                overview, timestamp = cached_data
                if time.time() - timestamp < self.cache_duration:
                    return overview
                else:
                    # Remove expired cache
                    del self._overview_cache[index_name]
        return None
    
    def _cache_overview(self, index_name: str, overview: MarketOverview):
        """Cache overview for future use."""
        with self._lock:
            self._overview_cache[index_name] = (overview, time.time())
    
    def _update_stats(self, index_name: str, start_time: float, success: bool):
        """Update statistics."""
        processing_time = time.time() - start_time
        
        with self._lock:
            self.stats.total_overviews_generated += 1
            
            if success:
                self.stats.successful_generations += 1
                self.stats.total_processing_time += processing_time
            else:
                self.stats.failed_generations += 1
            
            # Update index-specific stats
            if index_name not in self.stats.index_stats:
                self.stats.index_stats[index_name] = {
                    'generations': 0,
                    'successful': 0,
                    'total_time': 0.0
                }
            
            index_stats = self.stats.index_stats[index_name]
            index_stats['generations'] += 1
            index_stats['total_time'] += processing_time
            
            if success:
                index_stats['successful'] += 1
    
    def get_historical_volatility(self, index_name: str, window: int = None) -> Optional[float]:
        """Calculate historical volatility from price data."""
        window = window or self.volatility_window
        
        with self._lock:
            prices = list(self._price_history.get(index_name, []))
            
            if len(prices) < 2:
                return None
            
            # Calculate returns
            returns = []
            for i in range(1, len(prices)):
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
            
            if len(returns) < 2:
                return None
            
            # Calculate volatility (annualized)
            volatility = statistics.stdev(returns) * (252 ** 0.5) * 100  # 252 trading days
            return volatility
    
    def get_pcr_trend(self, index_name: str, lookback_minutes: int = 60) -> Dict[str, Any]:
        """Get PCR trend analysis."""
        # This would require storing historical PCR data
        # For now, return current PCR with trend indication
        try:
            cached_overview = self._get_cached_overview(index_name)
            if cached_overview:
                return {
                    'current_pcr_oi': cached_overview.pcr_oi,
                    'current_pcr_volume': cached_overview.pcr_volume,
                    'trend': 'stable',  # Would need historical data
                    'timestamp': cached_overview.timestamp.isoformat()
                }
        except Exception:
            pass
        
        return {'error': 'No data available'}
    
    def clear_cache(self):
        """Clear all cached data."""
        with self._lock:
            self._overview_cache.clear()
            self._analytics_cache.clear()
        logger.info("🧹 Overview cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics."""
        with self._lock:
            return {
                'overall': {
                    'total_overviews': self.stats.total_overviews_generated,
                    'success_rate': self.stats.success_rate,
                    'average_processing_time': self.stats.average_processing_time,
                    'analytics_calculated': self.stats.analytics_calculated,
                    'analytics_failed': self.stats.analytics_failed
                },
                'by_index': {
                    index: {
                        'generations': stats['generations'],
                        'success_rate': (stats['successful'] / max(1, stats['generations'])) * 100,
                        'avg_processing_time': stats['total_time'] / max(1, stats['successful'])
                    }
                    for index, stats in self.stats.index_stats.items()
                },
                'cache': {
                    'overview_cache_size': len(self._overview_cache),
                    'analytics_cache_size': sum(len(cache) for cache in self._analytics_cache.values())
                }
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            'status': 'healthy',
            'advanced_analytics_enabled': self.enable_advanced_analytics,
            'cache_size': len(self._overview_cache),
            'stats': self.get_stats()['overall']
        }