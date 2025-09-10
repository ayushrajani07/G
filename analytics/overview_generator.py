#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Overview Generator - G6.1 Platform
Generates comprehensive market overview and summary reports

Features:
- Multi-index market overview generation
- Options flow analysis and summary
- Market sentiment indicators
- Put-Call Ratio (PCR) analysis
- Volatility surface overview
- Performance metrics compilation
"""

import os
import sys
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics

@dataclass
class MarketOverview:
    """Market overview data structure."""
    timestamp: datetime
    indices: Dict[str, Any]
    market_sentiment: str
    overall_pcr: float
    volatility_summary: Dict[str, float]
    top_movers: Dict[str, List[Dict]]
    options_flow: Dict[str, Any]
    risk_metrics: Dict[str, float]
    session_summary: Dict[str, Any]

@dataclass
class IndexSummary:
    """Individual index summary."""
    name: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    high: float
    low: float
    atm_strike: float
    iv_rank: float
    pcr: float
    options_volume: int
    total_oi: int
    sentiment: str

@dataclass
class OptionsSummary:
    """Options trading summary."""
    total_volume: int
    total_oi: int
    ce_volume: int
    pe_volume: int
    ce_oi: int
    pe_oi: int
    pcr_volume: float
    pcr_oi: float
    max_pain: float
    iv_percentile: float
    top_strikes: List[Dict]

class OverviewGenerator:
    """Main overview generator class."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize overview generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.data_cache = {}
        self.calculation_cache = {}
        self.cache_ttl = config.get('cache_ttl', 300)  # 5 minutes
        
        # Market hours configuration
        self.market_start = time(9, 15)  # 9:15 AM
        self.market_end = time(15, 30)   # 3:30 PM
        
        # Sentiment thresholds
        self.sentiment_thresholds = {
            'pcr': {'bullish': 0.7, 'bearish': 1.3},
            'iv': {'low': 15, 'high': 30},
            'volume': {'low': 0.8, 'high': 1.2}  # Relative to average
        }
    
    def generate_market_overview(self, data_sources: Dict[str, Any]) -> MarketOverview:
        """Generate comprehensive market overview.
        
        Args:
            data_sources: Dictionary containing market data from various sources
            
        Returns:
            MarketOverview object with complete market analysis
        """
        timestamp = datetime.now()
        
        # Generate individual index summaries
        indices_summary = self._generate_indices_summary(data_sources)
        
        # Calculate overall market sentiment
        market_sentiment = self._calculate_market_sentiment(indices_summary)
        
        # Calculate overall PCR
        overall_pcr = self._calculate_overall_pcr(data_sources)
        
        # Generate volatility summary
        volatility_summary = self._generate_volatility_summary(data_sources)
        
        # Identify top movers
        top_movers = self._identify_top_movers(data_sources)
        
        # Analyze options flow
        options_flow = self._analyze_options_flow(data_sources)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(data_sources)
        
        # Generate session summary
        session_summary = self._generate_session_summary(data_sources)
        
        return MarketOverview(
            timestamp=timestamp,
            indices=indices_summary,
            market_sentiment=market_sentiment,
            overall_pcr=overall_pcr,
            volatility_summary=volatility_summary,
            top_movers=top_movers,
            options_flow=options_flow,
            risk_metrics=risk_metrics,
            session_summary=session_summary
        )
    
    def _generate_indices_summary(self, data_sources: Dict[str, Any]) -> Dict[str, IndexSummary]:
        """Generate summary for each index.
        
        Args:
            data_sources: Market data sources
            
        Returns:
            Dictionary mapping index names to IndexSummary objects
        """
        indices_summary = {}
        
        indices = self.config.get('indices', ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY'])
        
        for index in indices:
            try:
                # Get market data for index
                market_data = data_sources.get('market_data', {}).get(index, {})
                options_data = data_sources.get('options_data', {}).get(index, [])
                
                if not market_data:
                    continue
                
                # Calculate options metrics
                options_summary = self._calculate_options_summary(options_data)
                
                # Determine sentiment
                sentiment = self._determine_index_sentiment(market_data, options_summary)
                
                # Create index summary
                summary = IndexSummary(
                    name=index,
                    current_price=market_data.get('price', 0),
                    change=market_data.get('change', 0),
                    change_percent=market_data.get('change_percent', 0),
                    volume=market_data.get('volume', 0),
                    high=market_data.get('high', 0),
                    low=market_data.get('low', 0),
                    atm_strike=self._calculate_atm_strike(market_data.get('price', 0), index),
                    iv_rank=self._calculate_iv_rank(options_data),
                    pcr=options_summary.pcr_oi,
                    options_volume=options_summary.total_volume,
                    total_oi=options_summary.total_oi,
                    sentiment=sentiment
                )
                
                indices_summary[index] = summary
                
            except Exception as e:
                print(f"Error generating summary for {index}: {e}")
                continue
        
        return indices_summary
    
    def _calculate_options_summary(self, options_data: List[Dict]) -> OptionsSummary:
        """Calculate options summary metrics.
        
        Args:
            options_data: List of options data points
            
        Returns:
            OptionsSummary object
        """
        if not options_data:
            return OptionsSummary(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, [])
        
        ce_volume = sum(opt.get('volume', 0) for opt in options_data if opt.get('option_type') == 'CE')
        pe_volume = sum(opt.get('volume', 0) for opt in options_data if opt.get('option_type') == 'PE')
        
        ce_oi = sum(opt.get('oi', 0) for opt in options_data if opt.get('option_type') == 'CE')
        pe_oi = sum(opt.get('oi', 0) for opt in options_data if opt.get('option_type') == 'PE')
        
        total_volume = ce_volume + pe_volume
        total_oi = ce_oi + pe_oi
        
        # Calculate PCR
        pcr_volume = pe_volume / max(ce_volume, 1)
        pcr_oi = pe_oi / max(ce_oi, 1)
        
        # Calculate max pain
        max_pain = self._calculate_max_pain(options_data)
        
        # Calculate IV percentile
        iv_percentile = self._calculate_iv_percentile(options_data)
        
        # Get top strikes by volume
        top_strikes = self._get_top_strikes(options_data, 5)
        
        return OptionsSummary(
            total_volume=total_volume,
            total_oi=total_oi,
            ce_volume=ce_volume,
            pe_volume=pe_volume,
            ce_oi=ce_oi,
            pe_oi=pe_oi,
            pcr_volume=pcr_volume,
            pcr_oi=pcr_oi,
            max_pain=max_pain,
            iv_percentile=iv_percentile,
            top_strikes=top_strikes
        )
    
    def _calculate_max_pain(self, options_data: List[Dict]) -> float:
        """Calculate max pain point.
        
        Args:
            options_data: Options data list
            
        Returns:
            Max pain strike price
        """
        if not options_data:
            return 0
        
        # Group by strike
        strike_data = defaultdict(lambda: {'ce_oi': 0, 'pe_oi': 0})
        
        for option in options_data:
            strike = option.get('strike', 0)
            oi = option.get('oi', 0)
            option_type = option.get('option_type', '')
            
            if option_type == 'CE':
                strike_data[strike]['ce_oi'] = oi
            elif option_type == 'PE':
                strike_data[strike]['pe_oi'] = oi
        
        # Calculate pain for each strike
        strikes = sorted(strike_data.keys())
        max_pain_strike = 0
        min_pain = float('inf')
        
        for test_strike in strikes:
            total_pain = 0
            
            for strike, data in strike_data.items():
                if strike > test_strike:
                    # ITM calls
                    total_pain += (strike - test_strike) * data['ce_oi']
                elif strike < test_strike:
                    # ITM puts
                    total_pain += (test_strike - strike) * data['pe_oi']
            
            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_strike = test_strike
        
        return max_pain_strike
    
    def _calculate_iv_percentile(self, options_data: List[Dict]) -> float:
        """Calculate IV percentile.
        
        Args:
            options_data: Options data list
            
        Returns:
            IV percentile (0-100)
        """
        iv_values = [opt.get('iv', 0) for opt in options_data if opt.get('iv', 0) > 0]
        
        if not iv_values:
            return 0
        
        current_iv = statistics.mean(iv_values)
        
        # Simplified percentile calculation
        # In real implementation, this would use historical IV data
        if current_iv < 15:
            return 20
        elif current_iv < 20:
            return 40
        elif current_iv < 25:
            return 60
        elif current_iv < 30:
            return 80
        else:
            return 95
    
    def _get_top_strikes(self, options_data: List[Dict], count: int = 5) -> List[Dict]:
        """Get top strikes by volume.
        
        Args:
            options_data: Options data list
            count: Number of top strikes to return
            
        Returns:
            List of top strikes with volume data
        """
        strike_volumes = defaultdict(int)
        
        for option in options_data:
            strike = option.get('strike', 0)
            volume = option.get('volume', 0)
            strike_volumes[strike] += volume
        
        # Sort by volume and return top strikes
        sorted_strikes = sorted(strike_volumes.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'strike': strike, 'volume': volume}
            for strike, volume in sorted_strikes[:count]
        ]
    
    def _calculate_market_sentiment(self, indices_summary: Dict[str, IndexSummary]) -> str:
        """Calculate overall market sentiment.
        
        Args:
            indices_summary: Dictionary of index summaries
            
        Returns:
            Market sentiment string ('BULLISH', 'BEARISH', 'NEUTRAL')
        """
        if not indices_summary:
            return 'NEUTRAL'
        
        bullish_count = 0
        bearish_count = 0
        
        for summary in indices_summary.values():
            if summary.sentiment == 'BULLISH':
                bullish_count += 1
            elif summary.sentiment == 'BEARISH':
                bearish_count += 1
        
        total_indices = len(indices_summary)
        
        if bullish_count > total_indices * 0.6:
            return 'BULLISH'
        elif bearish_count > total_indices * 0.6:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _determine_index_sentiment(self, market_data: Dict, options_summary: OptionsSummary) -> str:
        """Determine sentiment for individual index.
        
        Args:
            market_data: Market data for the index
            options_summary: Options summary for the index
            
        Returns:
            Sentiment string ('BULLISH', 'BEARISH', 'NEUTRAL')
        """
        sentiment_score = 0
        
        # Price change contribution
        change_percent = market_data.get('change_percent', 0)
        if change_percent > 0.5:
            sentiment_score += 1
        elif change_percent < -0.5:
            sentiment_score -= 1
        
        # PCR contribution
        pcr = options_summary.pcr_oi
        if pcr < self.sentiment_thresholds['pcr']['bullish']:
            sentiment_score += 1
        elif pcr > self.sentiment_thresholds['pcr']['bearish']:
            sentiment_score -= 1
        
        # Volume contribution
        volume_ratio = market_data.get('volume', 0) / market_data.get('avg_volume', 1)
        if volume_ratio > self.sentiment_thresholds['volume']['high']:
            # High volume amplifies the price movement sentiment
            if change_percent > 0:
                sentiment_score += 0.5
            else:
                sentiment_score -= 0.5
        
        # Final sentiment determination
        if sentiment_score >= 1:
            return 'BULLISH'
        elif sentiment_score <= -1:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _calculate_overall_pcr(self, data_sources: Dict[str, Any]) -> float:
        """Calculate overall market PCR.
        
        Args:
            data_sources: Market data sources
            
        Returns:
            Overall PCR value
        """
        total_ce_oi = 0
        total_pe_oi = 0
        
        options_data = data_sources.get('options_data', {})
        
        for index, options in options_data.items():
            for option in options:
                oi = option.get('oi', 0)
                option_type = option.get('option_type', '')
                
                if option_type == 'CE':
                    total_ce_oi += oi
                elif option_type == 'PE':
                    total_pe_oi += oi
        
        return total_pe_oi / max(total_ce_oi, 1)
    
    def _generate_volatility_summary(self, data_sources: Dict[str, Any]) -> Dict[str, float]:
        """Generate volatility summary across indices.
        
        Args:
            data_sources: Market data sources
            
        Returns:
            Dictionary with volatility metrics
        """
        volatility_data = {}
        options_data = data_sources.get('options_data', {})
        
        for index, options in options_data.items():
            iv_values = [opt.get('iv', 0) for opt in options if opt.get('iv', 0) > 0]
            
            if iv_values:
                volatility_data[f'{index}_avg_iv'] = statistics.mean(iv_values)
                volatility_data[f'{index}_iv_range'] = max(iv_values) - min(iv_values)
        
        # Calculate overall metrics
        all_iv_values = []
        for options in options_data.values():
            all_iv_values.extend([opt.get('iv', 0) for opt in options if opt.get('iv', 0) > 0])
        
        if all_iv_values:
            volatility_data['market_avg_iv'] = statistics.mean(all_iv_values)
            volatility_data['market_iv_std'] = statistics.stdev(all_iv_values) if len(all_iv_values) > 1 else 0
        
        return volatility_data
    
    def _identify_top_movers(self, data_sources: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Identify top moving options and indices.
        
        Args:
            data_sources: Market data sources
            
        Returns:
            Dictionary with top gainers and losers
        """
        top_movers = {
            'indices_gainers': [],
            'indices_losers': [],
            'options_gainers': [],
            'options_losers': []
        }
        
        # Process indices
        market_data = data_sources.get('market_data', {})
        indices_changes = []
        
        for index, data in market_data.items():
            change_percent = data.get('change_percent', 0)
            indices_changes.append({
                'symbol': index,
                'change_percent': change_percent,
                'price': data.get('price', 0),
                'volume': data.get('volume', 0)
            })
        
        # Sort and get top movers
        indices_changes.sort(key=lambda x: x['change_percent'], reverse=True)
        top_movers['indices_gainers'] = indices_changes[:3]
        top_movers['indices_losers'] = indices_changes[-3:]
        
        # Process options
        all_options = []
        options_data = data_sources.get('options_data', {})
        
        for index, options in options_data.items():
            for option in options:
                change_percent = option.get('change_percent', 0)
                if abs(change_percent) > 0:  # Only options with price changes
                    all_options.append({
                        'symbol': option.get('symbol', ''),
                        'strike': option.get('strike', 0),
                        'option_type': option.get('option_type', ''),
                        'change_percent': change_percent,
                        'volume': option.get('volume', 0),
                        'oi': option.get('oi', 0)
                    })
        
        # Sort options by change percent
        all_options.sort(key=lambda x: x['change_percent'], reverse=True)
        top_movers['options_gainers'] = all_options[:10]
        top_movers['options_losers'] = all_options[-10:]
        
        return top_movers
    
    def _analyze_options_flow(self, data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze options flow patterns.
        
        Args:
            data_sources: Market data sources
            
        Returns:
            Dictionary with options flow analysis
        """
        flow_analysis = {
            'net_premium_flow': 0,
            'call_put_ratio': 0,
            'high_volume_strikes': [],
            'unusual_activity': [],
            'premium_distribution': {}
        }
        
        options_data = data_sources.get('options_data', {})
        total_call_premium = 0
        total_put_premium = 0
        high_volume_threshold = 10000  # Configurable threshold
        
        all_options = []
        for index, options in options_data.items():
            all_options.extend(options)
        
        # Calculate premium flows
        for option in all_options:
            premium = option.get('last_price', 0) * option.get('volume', 0)
            option_type = option.get('option_type', '')
            
            if option_type == 'CE':
                total_call_premium += premium
            elif option_type == 'PE':
                total_put_premium += premium
            
            # Identify high volume options
            volume = option.get('volume', 0)
            if volume > high_volume_threshold:
                flow_analysis['high_volume_strikes'].append({
                    'symbol': option.get('symbol', ''),
                    'strike': option.get('strike', 0),
                    'volume': volume,
                    'oi': option.get('oi', 0),
                    'type': option_type
                })
        
        # Calculate ratios and flows
        flow_analysis['net_premium_flow'] = total_call_premium - total_put_premium
        flow_analysis['call_put_ratio'] = total_call_premium / max(total_put_premium, 1)
        
        # Sort high volume strikes
        flow_analysis['high_volume_strikes'].sort(key=lambda x: x['volume'], reverse=True)
        flow_analysis['high_volume_strikes'] = flow_analysis['high_volume_strikes'][:20]
        
        # Premium distribution
        flow_analysis['premium_distribution'] = {
            'call_premium': total_call_premium,
            'put_premium': total_put_premium,
            'call_percentage': (total_call_premium / max(total_call_premium + total_put_premium, 1)) * 100
        }
        
        return flow_analysis
    
    def _calculate_risk_metrics(self, data_sources: Dict[str, Any]) -> Dict[str, float]:
        """Calculate various risk metrics.
        
        Args:
            data_sources: Market data sources
            
        Returns:
            Dictionary with risk metrics
        """
        risk_metrics = {}
        
        # VIX-like volatility index (simplified)
        options_data = data_sources.get('options_data', {})
        all_iv_values = []
        
        for options in options_data.values():
            all_iv_values.extend([opt.get('iv', 0) for opt in options if opt.get('iv', 0) > 0])
        
        if all_iv_values:
            risk_metrics['fear_greed_index'] = min(100, max(0, 100 - statistics.mean(all_iv_values) * 2))
            risk_metrics['volatility_risk'] = statistics.mean(all_iv_values)
        
        # Market correlation risk (simplified)
        market_data = data_sources.get('market_data', {})
        price_changes = [data.get('change_percent', 0) for data in market_data.values()]
        
        if len(price_changes) > 1:
            risk_metrics['market_correlation'] = abs(statistics.mean(price_changes))
        
        # Liquidity risk
        total_volume = sum(data.get('volume', 0) for data in market_data.values())
        avg_volume = total_volume / max(len(market_data), 1)
        risk_metrics['liquidity_score'] = min(100, avg_volume / 10000)  # Normalized
        
        return risk_metrics
    
    def _generate_session_summary(self, data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading session summary.
        
        Args:
            data_sources: Market data sources
            
        Returns:
            Dictionary with session summary
        """
        session_summary = {
            'session_type': self._get_session_type(),
            'market_breadth': {},
            'sector_performance': {},
            'key_levels': {},
            'session_highlights': []
        }
        
        # Market breadth
        market_data = data_sources.get('market_data', {})
        advances = sum(1 for data in market_data.values() if data.get('change_percent', 0) > 0)
        declines = sum(1 for data in market_data.values() if data.get('change_percent', 0) < 0)
        
        session_summary['market_breadth'] = {
            'advances': advances,
            'declines': declines,
            'unchanged': len(market_data) - advances - declines,
            'advance_decline_ratio': advances / max(declines, 1)
        }
        
        # Key levels (support/resistance) - simplified
        for index, data in market_data.items():
            current_price = data.get('price', 0)
            high = data.get('high', 0)
            low = data.get('low', 0)
            
            session_summary['key_levels'][index] = {
                'support': low,
                'resistance': high,
                'current': current_price,
                'distance_to_support': ((current_price - low) / current_price) * 100,
                'distance_to_resistance': ((high - current_price) / current_price) * 100
            }
        
        return session_summary
    
    def _get_session_type(self) -> str:
        """Determine current session type.
        
        Returns:
            Session type string
        """
        now = datetime.now().time()
        
        if now < time(10, 0):
            return "OPENING_SESSION"
        elif now < time(13, 0):
            return "MORNING_SESSION"
        elif now < time(15, 0):
            return "AFTERNOON_SESSION"
        elif now <= time(15, 30):
            return "CLOSING_SESSION"
        else:
            return "POST_MARKET"
    
    def _calculate_atm_strike(self, price: float, index: str) -> float:
        """Calculate ATM strike for given price and index.
        
        Args:
            price: Current price
            index: Index name
            
        Returns:
            ATM strike price
        """
        intervals = {
            'NIFTY': 50,
            'BANKNIFTY': 100,
            'FINNIFTY': 50,
            'MIDCPNIFTY': 25
        }
        
        interval = intervals.get(index, 50)
        return round(price / interval) * interval
    
    def _calculate_iv_rank(self, options_data: List[Dict]) -> float:
        """Calculate IV rank for options.
        
        Args:
            options_data: List of options data
            
        Returns:
            IV rank (0-100)
        """
        iv_values = [opt.get('iv', 0) for opt in options_data if opt.get('iv', 0) > 0]
        
        if not iv_values:
            return 0
        
        # Simplified IV rank calculation
        current_iv = statistics.mean(iv_values)
        
        # This would normally use historical IV data for proper ranking
        if current_iv < 15:
            return 10
        elif current_iv < 20:
            return 30
        elif current_iv < 25:
            return 50
        elif current_iv < 30:
            return 70
        else:
            return 90
    
    def export_overview(self, overview: MarketOverview, format_type: str = 'json') -> str:
        """Export market overview to specified format.
        
        Args:
            overview: MarketOverview object
            format_type: Export format ('json', 'csv', 'html')
            
        Returns:
            Formatted string representation
        """
        if format_type == 'json':
            return json.dumps(asdict(overview), indent=2, default=str)
        elif format_type == 'csv':
            return self._export_to_csv(overview)
        elif format_type == 'html':
            return self._export_to_html(overview)
        else:
            return str(overview)
    
    def _export_to_csv(self, overview: MarketOverview) -> str:
        """Export overview to CSV format."""
        # Simplified CSV export
        lines = []
        lines.append("Timestamp,Index,Price,Change,Change%,Volume,PCR,Sentiment")
        
        for index_name, summary in overview.indices.items():
            lines.append(f"{overview.timestamp},{index_name},{summary.current_price},"
                        f"{summary.change},{summary.change_percent},{summary.volume},"
                        f"{summary.pcr},{summary.sentiment}")
        
        return "\n".join(lines)
    
    def _export_to_html(self, overview: MarketOverview) -> str:
        """Export overview to HTML format."""
        html = f"""
        <html>
        <head><title>Market Overview - {overview.timestamp}</title></head>
        <body>
        <h1>Market Overview</h1>
        <p>Generated: {overview.timestamp}</p>
        <p>Market Sentiment: <strong>{overview.market_sentiment}</strong></p>
        <p>Overall PCR: {overview.overall_pcr:.2f}</p>
        
        <h2>Index Summary</h2>
        <table border="1">
        <tr><th>Index</th><th>Price</th><th>Change</th><th>Change%</th><th>PCR</th><th>Sentiment</th></tr>
        """
        
        for index_name, summary in overview.indices.items():
            html += f"""
            <tr>
                <td>{index_name}</td>
                <td>{summary.current_price}</td>
                <td>{summary.change}</td>
                <td>{summary.change_percent}%</td>
                <td>{summary.pcr:.2f}</td>
                <td>{summary.sentiment}</td>
            </tr>
            """
        
        html += """
        </table>
        </body>
        </html>
        """
        
        return html

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        'indices': ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY'],
        'cache_ttl': 300
    }
    
    # Initialize generator
    generator = OverviewGenerator(config)
    
    # Example data sources (normally from data collectors)
    mock_data_sources = {
        'market_data': {
            'NIFTY': {
                'price': 24975,
                'change': 125.50,
                'change_percent': 0.51,
                'volume': 450000,
                'high': 25050,
                'low': 24850
            }
        },
        'options_data': {
            'NIFTY': [
                {
                    'symbol': 'NIFTY24950CE',
                    'strike': 24950,
                    'option_type': 'CE',
                    'last_price': 156.75,
                    'volume': 25000,
                    'oi': 185000,
                    'change_percent': 8.5,
                    'iv': 23.4
                }
            ]
        }
    }
    
    # Generate overview
    overview = generator.generate_market_overview(mock_data_sources)
    
    # Export to JSON
    json_output = generator.export_overview(overview, 'json')
    print("Market Overview Generated:")
    print(json_output[:500] + "..." if len(json_output) > 500 else json_output)