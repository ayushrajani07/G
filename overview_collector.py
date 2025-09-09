#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📋 Complete Overview Data Collector for G6.1 Platform
Author: AI Assistant (Enhanced with comprehensive market overview analytics)

✅ Features:
- Real-time market overview generation
- PCR (Put-Call Ratio) calculation
- IV (Implied Volatility) analysis
- Volume and OI analysis
- Max Pain calculation
- Market sentiment indicators
- Performance metrics tracking
- Data aggregation and summarization
"""

import logging
import time
import datetime
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math

logger = logging.getLogger(__name__)

@dataclass
class MarketOverview:
    """📊 Complete market overview data structure."""
    index_name: str
    timestamp: str
    date: str
    time: str
    
    # 🎯 ATM and Strike Info
    atm_strike: float
    current_price: float
    
    # 📊 Option Counts
    total_options_collected: int
    ce_count: int
    pe_count: int
    active_strikes: int
    
    # 💰 Volume and OI
    total_volume: int
    total_oi: int
    ce_volume: int
    pe_volume: int
    ce_oi: int
    pe_oi: int
    
    # 📈 Ratios and Indicators
    pcr_volume: float  # Put-Call Ratio by Volume
    pcr_oi: float      # Put-Call Ratio by OI
    pcr_premium: float # Put-Call Ratio by Premium
    
    # 🌊 Volatility Metrics
    avg_iv: float
    ce_avg_iv: float
    pe_avg_iv: float
    iv_skew: float
    
    # 🎯 Max Pain Analysis
    max_pain_strike: float
    max_pain_value: float
    
    # 📊 Price Metrics
    total_premium: float
    ce_premium: float
    pe_premium: float
    avg_premium: float
    
    # 📈 Market Sentiment
    sentiment_score: float  # -1 to +1 (bearish to bullish)
    momentum_score: float
    
    # ⏱️ Performance Metrics
    collection_time_ms: float
    data_quality_score: float
    
    # 🔄 Processing Stats
    strikes_processed: int
    errors_encountered: int
    
    # 📊 Additional Analytics
    gamma_exposure: float
    delta_exposure: float
    theta_decay: float

class OverviewCollector:
    """
    📋 AI Assistant: Enhanced Overview Collector with comprehensive market analytics.
    
    Generates detailed market overviews with:
    - PCR calculations across multiple dimensions
    - Implied volatility analysis
    - Max pain calculations
    - Market sentiment indicators
    - Performance tracking
    """
    
    def __init__(self, enable_advanced_analytics: bool = True):
        """
        🆕 Initialize Overview Collector.
        
        Args:
            enable_advanced_analytics: Enable advanced calculations (Greeks, Max Pain)
        """
        self.enable_advanced_analytics = enable_advanced_analytics
        self.logger = logging.getLogger(f"{__name__}.OverviewCollector")
        
        # 📊 Performance tracking
        self.collection_count = 0
        self.total_processing_time = 0.0
        self.error_count = 0
        
        # 📈 Analytics cache
        self.max_pain_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        self.logger.info(f"✅ Overview Collector initialized (advanced_analytics: {enable_advanced_analytics})")
    
    def generate_overview(self,
                         index_name: str,
                         collection_results: Dict[str, Any],
                         current_price: Optional[float] = None) -> Optional[MarketOverview]:
        """
        📊 Generate comprehensive market overview from collection results.
        
        Args:
            index_name: Index name
            collection_results: Results from ATM collector
            current_price: Current index price (optional)
            
        Returns:
            MarketOverview: Comprehensive market overview data
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"📊 Generating overview for {index_name}")
            
            # 🔄 Aggregate all options data
            all_options = []
            errors_encountered = 0
            strikes_processed = 0
            atm_strike = 0.0
            
            for key, result in collection_results.items():
                if hasattr(result, 'options_collected'):
                    all_options.extend(result.options_collected)
                    strikes_processed += 1
                    if hasattr(result, 'atm_strike') and result.atm_strike > 0:
                        atm_strike = result.atm_strike
                if hasattr(result, 'errors'):
                    errors_encountered += len(result.errors)
            
            if not all_options:
                self.logger.warning(f"⚠️ No options data available for {index_name}")
                return None
            
            # 🕒 Timestamp information
            now = datetime.datetime.now()
            timestamp = now.isoformat()
            date_str = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H:%M:%S')
            
            # 📊 Basic metrics
            total_options = len(all_options)
            ce_options = [opt for opt in all_options if opt.option_type == 'CE']
            pe_options = [opt for opt in all_options if opt.option_type == 'PE']
            
            ce_count = len(ce_options)
            pe_count = len(pe_options)
            
            # 🎯 Strike analysis
            unique_strikes = len(set(opt.strike for opt in all_options))
            
            # 💰 Volume and OI calculations
            volume_metrics = self._calculate_volume_metrics(all_options, ce_options, pe_options)
            
            # 📈 PCR calculations
            pcr_metrics = self._calculate_pcr_metrics(ce_options, pe_options)
            
            # 🌊 Volatility metrics
            iv_metrics = self._calculate_iv_metrics(all_options, ce_options, pe_options)
            
            # 💰 Premium calculations
            premium_metrics = self._calculate_premium_metrics(all_options, ce_options, pe_options)
            
            # 🎯 Advanced analytics
            max_pain_strike, max_pain_value = 0.0, 0.0
            gamma_exposure = delta_exposure = theta_decay = 0.0
            
            if self.enable_advanced_analytics:
                max_pain_strike, max_pain_value = self._calculate_max_pain(all_options)
                gamma_exposure = self._calculate_gamma_exposure(all_options)
                delta_exposure = self._calculate_delta_exposure(all_options)
                theta_decay = self._calculate_theta_decay(all_options)
            
            # 📊 Market sentiment
            sentiment_metrics = self._calculate_sentiment_metrics(
                ce_options, pe_options, pcr_metrics, iv_metrics
            )
            
            # 🧪 Data quality assessment
            quality_scores = [opt.data_quality_score for opt in all_options if hasattr(opt, 'data_quality_score') and opt.data_quality_score]
            avg_quality = statistics.mean(quality_scores) if quality_scores else 0.8
            
            # ⏱️ Processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # 📊 Create comprehensive overview
            overview = MarketOverview(
                # 📋 Basic Info
                index_name=index_name,
                timestamp=timestamp,
                date=date_str,
                time=time_str,
                
                # 🎯 Strike Info
                atm_strike=atm_strike,
                current_price=current_price or atm_strike,
                
                # 📊 Counts
                total_options_collected=total_options,
                ce_count=ce_count,
                pe_count=pe_count,
                active_strikes=unique_strikes,
                
                # 💰 Volume and OI
                **volume_metrics,
                
                # 📈 PCR Ratios
                **pcr_metrics,
                
                # 🌊 Volatility
                **iv_metrics,
                
                # 🎯 Max Pain
                max_pain_strike=max_pain_strike,
                max_pain_value=max_pain_value,
                
                # 💰 Premium
                **premium_metrics,
                
                # 📊 Sentiment
                **sentiment_metrics,
                
                # ⏱️ Performance
                collection_time_ms=processing_time_ms,
                data_quality_score=avg_quality,
                
                # 🔄 Processing
                strikes_processed=strikes_processed,
                errors_encountered=errors_encountered,
                
                # 📈 Advanced Analytics
                gamma_exposure=gamma_exposure,
                delta_exposure=delta_exposure,
                theta_decay=theta_decay
            )
            
            # 📊 Update performance metrics
            self.collection_count += 1
            self.total_processing_time += processing_time_ms
            
            self.logger.info(
                f"✅ Overview generated for {index_name}: "
                f"{total_options} options, PCR: {pcr_metrics.get('pcr_oi', 0):.2f}, "
                f"Quality: {avg_quality:.2f} in {processing_time_ms:.1f}ms"
            )
            
            return overview
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"🔴 Overview generation error for {index_name}: {e}")
            return None
    
    def _calculate_volume_metrics(self, 
                                 all_options: List, 
                                 ce_options: List, 
                                 pe_options: List) -> Dict[str, int]:
        """💰 Calculate comprehensive volume and OI metrics."""
        try:
            # 📊 Total metrics
            total_volume = sum(getattr(opt, 'volume', 0) for opt in all_options)
            total_oi = sum(getattr(opt, 'oi', 0) for opt in all_options)
            
            # 📈 CE metrics
            ce_volume = sum(getattr(opt, 'volume', 0) for opt in ce_options)
            ce_oi = sum(getattr(opt, 'oi', 0) for opt in ce_options)
            
            # 📉 PE metrics
            pe_volume = sum(getattr(opt, 'volume', 0) for opt in pe_options)
            pe_oi = sum(getattr(opt, 'oi', 0) for opt in pe_options)
            
            return {
                'total_volume': total_volume,
                'total_oi': total_oi,
                'ce_volume': ce_volume,
                'pe_volume': pe_volume,
                'ce_oi': ce_oi,
                'pe_oi': pe_oi
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ Volume metrics calculation error: {e}")
            return {
                'total_volume': 0, 'total_oi': 0,
                'ce_volume': 0, 'pe_volume': 0,
                'ce_oi': 0, 'pe_oi': 0
            }
    
    def _calculate_pcr_metrics(self, ce_options: List, pe_options: List) -> Dict[str, float]:
        """📈 Calculate Put-Call Ratios across multiple dimensions."""
        try:
            # 💰 Volume PCR
            ce_volume = sum(getattr(opt, 'volume', 0) for opt in ce_options)
            pe_volume = sum(getattr(opt, 'volume', 0) for opt in pe_options)
            pcr_volume = pe_volume / ce_volume if ce_volume > 0 else 0.0
            
            # 📊 OI PCR
            ce_oi = sum(getattr(opt, 'oi', 0) for opt in ce_options)
            pe_oi = sum(getattr(opt, 'oi', 0) for opt in pe_options)
            pcr_oi = pe_oi / ce_oi if ce_oi > 0 else 0.0
            
            # 💰 Premium PCR
            ce_premium = sum(getattr(opt, 'last_price', 0) * getattr(opt, 'oi', 0) for opt in ce_options)
            pe_premium = sum(getattr(opt, 'last_price', 0) * getattr(opt, 'oi', 0) for opt in pe_options)
            pcr_premium = pe_premium / ce_premium if ce_premium > 0 else 0.0
            
            return {
                'pcr_volume': round(pcr_volume, 3),
                'pcr_oi': round(pcr_oi, 3),
                'pcr_premium': round(pcr_premium, 3)
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ PCR calculation error: {e}")
            return {'pcr_volume': 0.0, 'pcr_oi': 0.0, 'pcr_premium': 0.0}
    
    def _calculate_iv_metrics(self, 
                             all_options: List, 
                             ce_options: List, 
                             pe_options: List) -> Dict[str, float]:
        """🌊 Calculate comprehensive IV metrics."""
        try:
            # 📊 All options IV
            all_ivs = [getattr(opt, 'iv', 0) for opt in all_options if getattr(opt, 'iv', 0) > 0]
            avg_iv = statistics.mean(all_ivs) if all_ivs else 0.0
            
            # 📈 CE IV
            ce_ivs = [getattr(opt, 'iv', 0) for opt in ce_options if getattr(opt, 'iv', 0) > 0]
            ce_avg_iv = statistics.mean(ce_ivs) if ce_ivs else 0.0
            
            # 📉 PE IV  
            pe_ivs = [getattr(opt, 'iv', 0) for opt in pe_options if getattr(opt, 'iv', 0) > 0]
            pe_avg_iv = statistics.mean(pe_ivs) if pe_ivs else 0.0
            
            # 📊 IV Skew (PE IV - CE IV)
            iv_skew = pe_avg_iv - ce_avg_iv
            
            return {
                'avg_iv': round(avg_iv, 2),
                'ce_avg_iv': round(ce_avg_iv, 2),
                'pe_avg_iv': round(pe_avg_iv, 2),
                'iv_skew': round(iv_skew, 2)
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ IV calculation error: {e}")
            return {'avg_iv': 0.0, 'ce_avg_iv': 0.0, 'pe_avg_iv': 0.0, 'iv_skew': 0.0}
    
    def _calculate_premium_metrics(self, 
                                  all_options: List, 
                                  ce_options: List, 
                                  pe_options: List) -> Dict[str, float]:
        """💰 Calculate premium-based metrics."""
        try:
            # 📊 Total premium (weighted by OI)
            total_premium = sum(
                getattr(opt, 'last_price', 0) * getattr(opt, 'oi', 0) 
                for opt in all_options
            )
            
            # 📈 CE premium
            ce_premium = sum(
                getattr(opt, 'last_price', 0) * getattr(opt, 'oi', 0) 
                for opt in ce_options
            )
            
            # 📉 PE premium
            pe_premium = sum(
                getattr(opt, 'last_price', 0) * getattr(opt, 'oi', 0) 
                for opt in pe_options
            )
            
            # 📊 Average premium
            total_oi = sum(getattr(opt, 'oi', 0) for opt in all_options)
            avg_premium = total_premium / total_oi if total_oi > 0 else 0.0
            
            return {
                'total_premium': round(total_premium, 2),
                'ce_premium': round(ce_premium, 2),
                'pe_premium': round(pe_premium, 2),
                'avg_premium': round(avg_premium, 2)
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ Premium calculation error: {e}")
            return {'total_premium': 0.0, 'ce_premium': 0.0, 'pe_premium': 0.0, 'avg_premium': 0.0}
    
    def _calculate_max_pain(self, all_options: List) -> Tuple[float, float]:
        """🎯 Calculate Max Pain strike and value."""
        try:
            if not all_options:
                return 0.0, 0.0
            
            # 📊 Group options by strike
            strikes_data = defaultdict(lambda: {'ce_oi': 0, 'pe_oi': 0})
            
            for opt in all_options:
                strike = getattr(opt, 'strike', 0)
                oi = getattr(opt, 'oi', 0)
                opt_type = getattr(opt, 'option_type', '')
                
                if strike > 0 and oi > 0:
                    if opt_type == 'CE':
                        strikes_data[strike]['ce_oi'] += oi
                    elif opt_type == 'PE':
                        strikes_data[strike]['pe_oi'] += oi
            
            if not strikes_data:
                return 0.0, 0.0
            
            # 🎯 Calculate pain for each potential expiry price
            strikes = sorted(strikes_data.keys())
            min_strike = min(strikes)
            max_strike = max(strikes)
            
            max_pain_strike = 0.0
            max_pain_value = float('inf')
            
            # 📊 Test each strike as potential expiry price
            for test_strike in strikes:
                total_pain = 0.0
                
                # 📈 Calculate CE pain (ITM CEs)
                for strike, data in strikes_data.items():
                    if strike < test_strike:  # ITM CEs
                        ce_pain = (test_strike - strike) * data['ce_oi']
                        total_pain += ce_pain
                
                # 📉 Calculate PE pain (ITM PEs)
                for strike, data in strikes_data.items():
                    if strike > test_strike:  # ITM PEs
                        pe_pain = (strike - test_strike) * data['pe_oi']
                        total_pain += pe_pain
                
                # 🎯 Track minimum pain
                if total_pain < max_pain_value:
                    max_pain_value = total_pain
                    max_pain_strike = test_strike
            
            return float(max_pain_strike), float(max_pain_value)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Max Pain calculation error: {e}")
            return 0.0, 0.0
    
    def _calculate_gamma_exposure(self, all_options: List) -> float:
        """📊 Calculate total gamma exposure."""
        try:
            total_gamma_exposure = 0.0
            
            for opt in all_options:
                gamma = getattr(opt, 'gamma', 0)
                oi = getattr(opt, 'oi', 0)
                strike = getattr(opt, 'strike', 0)
                
                if gamma > 0 and oi > 0 and strike > 0:
                    # 📊 Gamma exposure = Gamma * OI * Strike^2 * 0.01
                    exposure = gamma * oi * (strike ** 2) * 0.01
                    total_gamma_exposure += exposure
            
            return round(total_gamma_exposure, 0)
            
        except Exception as e:
            self.logger.debug(f"⚠️ Gamma exposure calculation error: {e}")
            return 0.0
    
    def _calculate_delta_exposure(self, all_options: List) -> float:
        """📈 Calculate total delta exposure."""
        try:
            total_delta_exposure = 0.0
            
            for opt in all_options:
                delta = getattr(opt, 'delta', 0)
                oi = getattr(opt, 'oi', 0)
                strike = getattr(opt, 'strike', 0)
                
                if oi > 0 and strike > 0:
                    # 📊 Delta exposure = Delta * OI * Strike
                    exposure = delta * oi * strike
                    total_delta_exposure += exposure
            
            return round(total_delta_exposure, 0)
            
        except Exception as e:
            self.logger.debug(f"⚠️ Delta exposure calculation error: {e}")
            return 0.0
    
    def _calculate_theta_decay(self, all_options: List) -> float:
        """⏰ Calculate total theta decay."""
        try:
            total_theta_decay = 0.0
            
            for opt in all_options:
                theta = getattr(opt, 'theta', 0)
                oi = getattr(opt, 'oi', 0)
                
                if oi > 0:
                    # ⏰ Theta decay = Theta * OI
                    decay = theta * oi
                    total_theta_decay += decay
            
            return round(total_theta_decay, 2)
            
        except Exception as e:
            self.logger.debug(f"⚠️ Theta decay calculation error: {e}")
            return 0.0
    
    def _calculate_sentiment_metrics(self, 
                                   ce_options: List, 
                                   pe_options: List, 
                                   pcr_metrics: Dict, 
                                   iv_metrics: Dict) -> Dict[str, float]:
        """📊 Calculate market sentiment indicators."""
        try:
            # 🎯 PCR-based sentiment (-1 bearish, +1 bullish)
            pcr_oi = pcr_metrics.get('pcr_oi', 1.0)
            
            # PCR > 1.5 = bearish, PCR < 0.7 = bullish
            if pcr_oi > 1.5:
                pcr_sentiment = -min(1.0, (pcr_oi - 1.0) / 1.0)
            elif pcr_oi < 0.7:
                pcr_sentiment = min(1.0, (1.0 - pcr_oi) / 0.3)
            else:
                pcr_sentiment = 0.0
            
            # 🌊 IV Skew sentiment
            iv_skew = iv_metrics.get('iv_skew', 0.0)
            # Positive skew (PE IV > CE IV) = bearish
            skew_sentiment = -min(1.0, max(-1.0, iv_skew / 5.0))
            
            # 📊 Volume momentum
            ce_volume = sum(getattr(opt, 'volume', 0) for opt in ce_options)
            pe_volume = sum(getattr(opt, 'volume', 0) for opt in pe_options)
            
            total_volume = ce_volume + pe_volume
            if total_volume > 0:
                volume_momentum = (ce_volume - pe_volume) / total_volume
            else:
                volume_momentum = 0.0
            
            # 📈 Combined sentiment
            sentiment_score = (pcr_sentiment * 0.4 + skew_sentiment * 0.3 + volume_momentum * 0.3)
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            
            # 📊 Momentum score (based on volume patterns)
            momentum_score = min(1.0, max(-1.0, volume_momentum))
            
            return {
                'sentiment_score': round(sentiment_score, 3),
                'momentum_score': round(momentum_score, 3)
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ Sentiment calculation error: {e}")
            return {'sentiment_score': 0.0, 'momentum_score': 0.0}
    
    def get_collector_stats(self) -> Dict[str, Any]:
        """📊 Get comprehensive collector statistics."""
        avg_processing_time = (self.total_processing_time / self.collection_count 
                             if self.collection_count > 0 else 0)
        
        return {
            'total_overviews_generated': self.collection_count,
            'total_errors': self.error_count,
            'success_rate': (self.collection_count / (self.collection_count + self.error_count) 
                           if (self.collection_count + self.error_count) > 0 else 1.0),
            'average_processing_time_ms': round(avg_processing_time, 2),
            'advanced_analytics_enabled': self.enable_advanced_analytics,
            'max_pain_cache_size': len(self.max_pain_cache)
        }

# 🧪 AI Assistant: Testing functions
def test_overview_collector():
    """🧪 Test Overview Collector functionality."""
    print("🧪 Testing Overview Collector...")
    
    try:
        # 🎭 Create mock collection results
        from atm_options_collector import OptionData, CollectionResult
        
        # Create mock options data
        mock_options = [
            OptionData(
                tradingsymbol="NIFTY25SEP24800CE",
                strike=24800, expiry="2025-09-25", option_type="CE",
                last_price=125.50, volume=100000, oi=50000,
                change=5.25, pchange=4.37, iv=18.5,
                delta=0.52, gamma=0.015, theta=-0.85,
                data_quality_score=0.95
            ),
            OptionData(
                tradingsymbol="NIFTY25SEP24800PE",
                strike=24800, expiry="2025-09-25", option_type="PE",
                last_price=98.75, volume=120000, oi=60000,
                change=-2.15, pchange=-2.13, iv=19.2,
                delta=-0.48, gamma=0.015, theta=-0.78,
                data_quality_score=0.92
            )
        ]
        
        mock_results = {
            'this_week_+0': CollectionResult(
                index_name='NIFTY',
                expiry_tag='this_week',
                offset=0,
                options_collected=mock_options,
                collection_time_ms=150.0,
                atm_strike=24800.0,
                data_quality_score=0.93,
                errors=[],
                metadata={}
            )
        }
        
        # 📊 Test collector
        collector = OverviewCollector(enable_advanced_analytics=True)
        
        overview = collector.generate_overview('NIFTY', mock_results, 24825.0)
        
        if overview:
            print(f"✅ Overview generated successfully:")
            print(f"  Total Options: {overview.total_options_collected}")
            print(f"  PCR (OI): {overview.pcr_oi}")
            print(f"  Avg IV: {overview.avg_iv}%")
            print(f"  Max Pain: {overview.max_pain_strike}")
            print(f"  Sentiment: {overview.sentiment_score}")
            print(f"  Quality: {overview.data_quality_score}")
        else:
            print("🔴 Overview generation failed")
            return False
        
        # 📊 Test stats
        stats = collector.get_collector_stats()
        print(f"✅ Collector stats: {stats['total_overviews_generated']} overviews generated")
        
        print("🎉 Overview Collector test completed!")
        return True
        
    except Exception as e:
        print(f"🔴 Overview Collector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_overview_collector()