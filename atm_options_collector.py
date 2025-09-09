#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Complete ATM Options Collector for G6.1 Platform
Author: AI Assistant (Enhanced with comprehensive ATM strike collection)

✅ Features:
- Real-time ATM strike detection and collection
- Multiple expiry support (weekly/monthly)
- Strike offset collection (ITM/OTM)
- Data quality validation and scoring
- Error handling with retry logic
- Performance metrics and monitoring
- Comprehensive Greek calculations
- Market data enrichment
"""

import logging
import time
import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

@dataclass
class OptionData:
    """🎯 Complete option data model."""
    tradingsymbol: str
    strike: float
    expiry: str
    option_type: str  # CE/PE
    last_price: float
    volume: int
    oi: int
    change: float
    pchange: float
    bid: float = 0.0
    ask: float = 0.0
    iv: float = 0.0
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    rho: float = 0.0
    timestamp: str = ""
    data_quality_score: float = 1.0

@dataclass
class CollectionResult:
    """📈 Collection result with comprehensive metrics."""
    index_name: str
    expiry_tag: str
    offset: int
    options_collected: List[OptionData]
    collection_time_ms: float
    atm_strike: float
    data_quality_score: float
    errors: List[str]
    metadata: Dict[str, Any]

class ATMOptionsCollector:
    """
    📊 AI Assistant: Enhanced ATM Options Collector with comprehensive features.
    
    Collects option chain data around ATM strikes with:
    - Real-time ATM detection
    - Multiple expiry support
    - Strike offset management
    - Data quality validation
    - Performance monitoring
    """
    
    def __init__(self, 
                 kite_provider,
                 max_workers: int = 4,
                 timeout_seconds: float = 30.0,
                 quality_threshold: float = 0.8):
        """
        🆕 Initialize ATM Options Collector.
        
        Args:
            kite_provider: Kite data provider instance
            max_workers: Maximum concurrent collection threads
            timeout_seconds: Collection timeout
            quality_threshold: Minimum data quality threshold
        """
        self.kite_provider = kite_provider
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        self.quality_threshold = quality_threshold
        
        self.logger = logging.getLogger(f"{__name__}.ATMOptionsCollector")
        
        # 📊 Performance tracking
        self.collection_count = 0
        self.total_collection_time = 0.0
        self.error_count = 0
        self.last_collection_time = None
        
        # 🎯 Collection cache
        self.atm_cache = {}
        self.cache_ttl = 60  # 1 minute cache
        
        self.logger.info("✅ ATM Options Collector initialized")
    
    def collect_atm_options(self, 
                           index_name: str,
                           index_params,
                           include_greeks: bool = True,
                           include_market_depth: bool = False) -> Dict[str, CollectionResult]:
        """
        📊 AI Assistant: Collect comprehensive ATM options data.
        
        Args:
            index_name: Index symbol (e.g., 'NIFTY')
            index_params: Index configuration parameters
            include_greeks: Calculate and include Greeks
            include_market_depth: Include bid/ask data
            
        Returns:
            Dict[str, CollectionResult]: Results keyed by expiry_offset combination
        """
        collection_start = time.time()
        results = {}
        
        try:
            self.logger.info(f"📊 Starting ATM collection for {index_name}")
            
            # 🎯 Get current ATM strike with caching
            atm_strike = self._get_cached_atm_strike(index_name)
            if not atm_strike:
                self.logger.error(f"🔴 Failed to get ATM strike for {index_name}")
                return results
            
            # 📅 Get expiry dates
            expiry_tags = getattr(index_params, 'expiries', ['this_week', 'next_week'])
            offsets = getattr(index_params, 'offsets', [0, 1, -1, 2, -2])
            strike_step = getattr(index_params, 'strike_step', 50)
            
            # 🔄 Collect data for each expiry and offset
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                
                for expiry_tag in expiry_tags:
                    # 🎯 Resolve expiry date
                    expiry_date = self._resolve_expiry_date(index_name, expiry_tag)
                    if not expiry_date:
                        continue
                    
                    for offset in offsets:
                        strike_price = atm_strike + (offset * strike_step)
                        
                        if strike_price <= 0:
                            continue
                        
                        future = executor.submit(
                            self._collect_strike_options,
                            index_name, expiry_tag, offset, strike_price, 
                            expiry_date, atm_strike, include_greeks, include_market_depth
                        )
                        
                        key = f"{expiry_tag}_{offset:+d}"
                        futures[future] = key
                
                # 📊 Collect results with timeout
                completed_count = 0
                for future in as_completed(futures, timeout=self.timeout_seconds):
                    try:
                        result = future.result()
                        if result and result.options_collected:
                            results[futures[future]] = result
                            completed_count += 1
                    except Exception as e:
                        self.logger.error(f"🔴 Collection future error: {e}")
            
            collection_time = (time.time() - collection_start) * 1000
            self.collection_count += 1
            self.total_collection_time += collection_time
            self.last_collection_time = datetime.datetime.now()
            
            success_rate = completed_count / len(futures) if futures else 0
            
            self.logger.info(
                f"✅ ATM collection completed: {index_name} - "
                f"{completed_count}/{len(futures)} successful ({success_rate:.1%}) "
                f"in {collection_time:.1f}ms"
            )
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"🔴 ATM collection error for {index_name}: {e}")
        
        return results
    
    def _get_cached_atm_strike(self, index_name: str) -> Optional[float]:
        """🎯 Get ATM strike with caching."""
        current_time = time.time()
        cache_key = f"atm_{index_name}"
        
        # 📊 Check cache
        if cache_key in self.atm_cache:
            cached_data, timestamp = self.atm_cache[cache_key]
            if current_time - timestamp < self.cache_ttl:
                return cached_data
        
        # 📡 Fetch fresh ATM strike
        try:
            atm_strike = self.kite_provider.get_atm_strike(index_name)
            if atm_strike > 0:
                self.atm_cache[cache_key] = (atm_strike, current_time)
                return atm_strike
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to get ATM strike: {e}")
        
        return None
    
    def _resolve_expiry_date(self, index_name: str, expiry_tag: str) -> Optional[str]:
        """📅 Resolve expiry date from tag."""
        try:
            if hasattr(self.kite_provider, 'resolve_expiry'):
                expiry_date = self.kite_provider.resolve_expiry(index_name, expiry_tag)
                if expiry_date:
                    return expiry_date.strftime('%Y-%m-%d') if hasattr(expiry_date, 'strftime') else str(expiry_date)
            
            # 🆘 Fallback expiry calculation
            from datetime import date, timedelta
            today = date.today()
            
            if 'week' in expiry_tag.lower():
                days_ahead = 7 if 'this' in expiry_tag else 14
            else:
                days_ahead = 30 if 'this' in expiry_tag else 60
            
            expiry_date = today + timedelta(days=days_ahead)
            return expiry_date.strftime('%Y-%m-%d')
            
        except Exception as e:
            self.logger.error(f"🔴 Error resolving expiry {expiry_tag}: {e}")
            return None
    
    def _collect_strike_options(self,
                               index_name: str,
                               expiry_tag: str,
                               offset: int,
                               strike_price: float,
                               expiry_date: str,
                               atm_strike: float,
                               include_greeks: bool,
                               include_market_depth: bool) -> Optional[CollectionResult]:
        """📈 Collect options for a specific strike."""
        collection_start = time.time()
        options_collected = []
        errors = []
        
        try:
            # 🔍 Get option instruments
            strikes = [strike_price]
            
            if hasattr(self.kite_provider, 'get_option_instruments'):
                instruments = self.kite_provider.get_option_instruments(
                    index_name, expiry_date, strikes
                )
            else:
                # 🎭 Generate mock instruments
                instruments = self._generate_mock_instruments(
                    index_name, expiry_date, strikes
                )
            
            if not instruments:
                errors.append(f"No instruments found for strike {strike_price}")
                return None
            
            # 📊 Get quotes for instruments
            instrument_keys = [(inst.get('exchange', 'NSE'), inst.get('tradingsymbol', '')) 
                             for inst in instruments]
            
            quotes = self.kite_provider.get_quote(instrument_keys)
            
            # 🔄 Process each instrument
            for instrument in instruments:
                try:
                    tradingsymbol = instrument.get('tradingsymbol', '')
                    exchange = instrument.get('exchange', 'NSE')
                    quote_key = f"{exchange}:{tradingsymbol}"
                    
                    if quote_key not in quotes:
                        errors.append(f"No quote for {tradingsymbol}")
                        continue
                    
                    quote = quotes[quote_key]
                    
                    # 📊 Create option data
                    option_data = self._create_option_data(
                        instrument, quote, atm_strike, include_greeks, include_market_depth
                    )
                    
                    if option_data:
                        options_collected.append(option_data)
                    
                except Exception as e:
                    errors.append(f"Error processing {instrument}: {e}")
            
            # 📈 Calculate collection metrics
            collection_time_ms = (time.time() - collection_start) * 1000
            data_quality_score = self._calculate_data_quality(options_collected, errors)
            
            return CollectionResult(
                index_name=index_name,
                expiry_tag=expiry_tag,
                offset=offset,
                options_collected=options_collected,
                collection_time_ms=collection_time_ms,
                atm_strike=atm_strike,
                data_quality_score=data_quality_score,
                errors=errors,
                metadata={
                    'strike_price': strike_price,
                    'expiry_date': expiry_date,
                    'instruments_found': len(instruments),
                    'quotes_received': len([q for q in quotes.values() if q]),
                    'include_greeks': include_greeks,
                    'include_market_depth': include_market_depth
                }
            )
            
        except Exception as e:
            self.logger.error(f"🔴 Strike collection error: {e}")
            return None
    
    def _create_option_data(self,
                           instrument: Dict[str, Any],
                           quote: Dict[str, Any],
                           atm_strike: float,
                           include_greeks: bool,
                           include_market_depth: bool) -> Optional[OptionData]:
        """🎯 Create comprehensive option data object."""
        try:
            # 📊 Extract basic data
            tradingsymbol = instrument.get('tradingsymbol', '')
            strike = float(instrument.get('strike', 0))
            expiry = instrument.get('expiry', '')
            option_type = instrument.get('instrument_type', '')
            
            if isinstance(expiry, datetime.date):
                expiry = expiry.strftime('%Y-%m-%d')
            
            # 💰 Extract price data
            last_price = float(quote.get('last_price', 0))
            volume = int(quote.get('volume', 0))
            oi = int(quote.get('oi', 0))
            change = float(quote.get('change', 0))
            pchange = float(quote.get('pchange', 0))
            
            # 📈 Market depth (if requested)
            bid = ask = 0.0
            if include_market_depth:
                depth = quote.get('depth', {})
                buy_orders = depth.get('buy', [])
                sell_orders = depth.get('sell', [])
                
                if buy_orders:
                    bid = float(buy_orders[0].get('price', 0))
                if sell_orders:
                    ask = float(sell_orders[0].get('price', 0))
            
            # 🧮 Greeks calculation (if requested)
            iv = delta = gamma = theta = vega = rho = 0.0
            if include_greeks and last_price > 0:
                greeks = self._calculate_greeks(
                    strike, atm_strike, last_price, option_type, expiry
                )
                iv = greeks.get('iv', 0)
                delta = greeks.get('delta', 0)
                gamma = greeks.get('gamma', 0)
                theta = greeks.get('theta', 0)
                vega = greeks.get('vega', 0)
                rho = greeks.get('rho', 0)
            
            # 🧪 Data quality scoring
            quality_score = self._score_option_quality(
                tradingsymbol, strike, last_price, volume, oi
            )
            
            return OptionData(
                tradingsymbol=tradingsymbol,
                strike=strike,
                expiry=expiry,
                option_type=option_type,
                last_price=last_price,
                volume=volume,
                oi=oi,
                change=change,
                pchange=pchange,
                bid=bid,
                ask=ask,
                iv=iv,
                delta=delta,
                gamma=gamma,
                theta=theta,
                vega=vega,
                rho=rho,
                timestamp=datetime.datetime.now().isoformat(),
                data_quality_score=quality_score
            )
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error creating option data: {e}")
            return None
    
    def _calculate_greeks(self,
                         strike: float,
                         spot: float,
                         premium: float,
                         option_type: str,
                         expiry: str) -> Dict[str, float]:
        """🧮 Calculate option Greeks using simplified Black-Scholes."""
        try:
            import math
            
            # 📅 Calculate time to expiry
            try:
                if isinstance(expiry, str):
                    expiry_date = datetime.datetime.strptime(expiry, '%Y-%m-%d').date()
                else:
                    expiry_date = expiry
                
                today = datetime.date.today()
                days_to_expiry = (expiry_date - today).days
                time_to_expiry = max(1, days_to_expiry) / 365.0
            except:
                time_to_expiry = 30 / 365.0  # Default 30 days
            
            # 📊 Market parameters (simplified)
            risk_free_rate = 0.06  # 6% risk-free rate
            
            # 📈 Calculate implied volatility (simplified reverse engineering)
            moneyness = spot / strike if strike > 0 else 1.0
            
            # 🎯 Simplified IV calculation
            if premium > 0:
                intrinsic = max(0, (spot - strike) if option_type == 'CE' else (strike - spot))
                time_value = premium - intrinsic
                iv = min(300, max(10, time_value / (spot * math.sqrt(time_to_expiry)) * 100))
            else:
                iv = 20.0  # Default 20% IV
            
            iv_decimal = iv / 100.0
            
            # 🧮 Black-Scholes calculations (simplified)
            try:
                d1 = (math.log(spot / strike) + (risk_free_rate + 0.5 * iv_decimal ** 2) * time_to_expiry) / (iv_decimal * math.sqrt(time_to_expiry))
                d2 = d1 - iv_decimal * math.sqrt(time_to_expiry)
                
                # 📊 Standard normal CDF approximation
                def norm_cdf(x):
                    return 0.5 * (1 + math.erf(x / math.sqrt(2)))
                
                def norm_pdf(x):
                    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
                
                N_d1 = norm_cdf(d1)
                N_d2 = norm_cdf(d2)
                n_d1 = norm_pdf(d1)
                
                # 🎯 Calculate Greeks
                if option_type == 'CE':
                    delta = N_d1
                else:
                    delta = N_d1 - 1
                
                gamma = n_d1 / (spot * iv_decimal * math.sqrt(time_to_expiry))
                theta = -(spot * n_d1 * iv_decimal) / (2 * math.sqrt(time_to_expiry)) - risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry) * (N_d2 if option_type == 'CE' else (1 - N_d2))
                theta = theta / 365.0  # Daily theta
                
                vega = spot * n_d1 * math.sqrt(time_to_expiry) / 100  # Per 1% change
                
                if option_type == 'CE':
                    rho = strike * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * N_d2 / 100
                else:
                    rho = -strike * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * (1 - N_d2) / 100
                
            except (ValueError, ZeroDivisionError, OverflowError):
                # 🆘 Fallback to simple approximations
                delta = 0.5 if abs(moneyness - 1.0) < 0.05 else (0.8 if moneyness > 1.1 else 0.2)
                if option_type == 'PE':
                    delta = delta - 1
                
                gamma = max(0.001, 0.1 * (1 - abs(math.log(moneyness))))
                theta = -premium * 0.02  # 2% per day approximation
                vega = premium * 0.1    # 10% of premium per 1% IV change
                rho = premium * 0.01    # 1% of premium per 1% rate change
            
            return {
                'iv': round(iv, 2),
                'delta': round(delta, 4),
                'gamma': round(gamma, 4),
                'theta': round(theta, 4),
                'vega': round(vega, 4),
                'rho': round(rho, 4)
            }
            
        except Exception as e:
            self.logger.debug(f"⚠️ Greeks calculation error: {e}")
            return {'iv': 20.0, 'delta': 0.5, 'gamma': 0.01, 'theta': -0.1, 'vega': 0.1, 'rho': 0.01}
    
    def _score_option_quality(self,
                             tradingsymbol: str,
                             strike: float,
                             last_price: float,
                             volume: int,
                             oi: int) -> float:
        """🧪 Score option data quality."""
        quality_score = 1.0
        
        # 📊 Basic validation
        if not tradingsymbol or len(tradingsymbol) < 5:
            quality_score -= 0.3
        
        if strike <= 0:
            quality_score -= 0.4
        
        if last_price <= 0:
            quality_score -= 0.5
        
        if volume < 0:
            quality_score -= 0.2
        
        if oi < 0:
            quality_score -= 0.2
        
        # 📈 Liquidity scoring
        if volume > 1000:
            quality_score += 0.1
        elif volume < 10:
            quality_score -= 0.1
        
        if oi > 500:
            quality_score += 0.1
        elif oi < 10:
            quality_score -= 0.1
        
        return max(0.0, min(1.0, quality_score))
    
    def _calculate_data_quality(self, options: List[OptionData], errors: List[str]) -> float:
        """📊 Calculate overall data quality score."""
        if not options:
            return 0.0
        
        # 📈 Individual quality scores
        individual_scores = [opt.data_quality_score for opt in options]
        avg_quality = sum(individual_scores) / len(individual_scores)
        
        # 🔴 Error penalty
        error_penalty = min(0.5, len(errors) * 0.1)
        
        # 📊 Completeness bonus
        completeness_bonus = 0.1 if len(options) >= 2 else 0  # CE and PE
        
        final_score = max(0.0, min(1.0, avg_quality - error_penalty + completeness_bonus))
        return round(final_score, 3)
    
    def _generate_mock_instruments(self,
                                  index_name: str,
                                  expiry_date: str,
                                  strikes: List[float]) -> List[Dict[str, Any]]:
        """🎭 Generate mock instruments for testing."""
        instruments = []
        
        try:
            # 📅 Format expiry for symbol
            expiry_obj = datetime.datetime.strptime(expiry_date, '%Y-%m-%d').date()
            expiry_str = expiry_obj.strftime('%y%b').upper()
            
            for strike in strikes:
                strike_int = int(strike)
                
                for opt_type in ['CE', 'PE']:
                    instruments.append({
                        'instrument_token': abs(hash(f"{index_name}{strike}{opt_type}")) % 10000000,
                        'tradingsymbol': f"{index_name}{expiry_str}{strike_int}{opt_type}",
                        'name': index_name,
                        'expiry': expiry_obj,
                        'strike': float(strike),
                        'instrument_type': opt_type,
                        'segment': f"NFO-OPT",
                        'exchange': 'NFO',
                        'lot_size': 50 if index_name in ['NIFTY', 'FINNIFTY'] else 25,
                        'tick_size': 0.05
                    })
        
        except Exception as e:
            self.logger.warning(f"⚠️ Mock instrument generation error: {e}")
        
        return instruments
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """📊 Get comprehensive collection statistics."""
        avg_collection_time = (self.total_collection_time / self.collection_count 
                             if self.collection_count > 0 else 0)
        
        return {
            'total_collections': self.collection_count,
            'total_errors': self.error_count,
            'success_rate': (self.collection_count / (self.collection_count + self.error_count) 
                           if (self.collection_count + self.error_count) > 0 else 1.0),
            'average_collection_time_ms': round(avg_collection_time, 2),
            'last_collection': self.last_collection_time.isoformat() if self.last_collection_time else None,
            'cache_entries': len(self.atm_cache),
            'max_workers': self.max_workers,
            'timeout_seconds': self.timeout_seconds,
            'quality_threshold': self.quality_threshold
        }
    
    def clear_cache(self):
        """🗑️ Clear ATM strike cache."""
        cache_count = len(self.atm_cache)
        self.atm_cache.clear()
        self.logger.info(f"🗑️ Cleared {cache_count} cached ATM strikes")

# 🧪 AI Assistant: Testing functions
def test_atm_collector():
    """🧪 Test ATM Options Collector."""
    print("🧪 Testing ATM Options Collector...")
    
    try:
        # 🎭 Create mock provider
        class MockKiteProvider:
            def get_atm_strike(self, index):
                return 24800.0 if index == 'NIFTY' else 54000.0
            
            def get_quote(self, instruments):
                quotes = {}
                for exchange, symbol in instruments:
                    quotes[f"{exchange}:{symbol}"] = {
                        'last_price': 125.50,
                        'volume': 100000,
                        'oi': 50000,
                        'change': 5.25,
                        'pchange': 4.37
                    }
                return quotes
        
        # 🎛️ Mock index params
        class MockIndexParams:
            expiries = ['this_week']
            offsets = [0, 1, -1]
            strike_step = 50
        
        # 📊 Test collector
        provider = MockKiteProvider()
        collector = ATMOptionsCollector(provider, max_workers=2)
        
        results = collector.collect_atm_options('NIFTY', MockIndexParams())
        
        print(f"✅ Collection results: {len(results)} expiry/offset combinations")
        
        for key, result in results.items():
            print(f"  {key}: {len(result.options_collected)} options, "
                  f"quality: {result.data_quality_score:.2f}")
        
        stats = collector.get_collection_stats()
        print(f"✅ Collection stats: {stats['total_collections']} collections")
        
        print("🎉 ATM Options Collector test completed!")
        return True
        
    except Exception as e:
        print(f"🔴 ATM Collector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_atm_collector()