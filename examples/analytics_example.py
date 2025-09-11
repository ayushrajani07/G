#!/usr/bin/env python3
"""
G6 Analytics Platform - Analytics Example

This example demonstrates advanced analytics features including
IV calculations, Greeks, and risk analysis.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from g6_platform.analytics.analytics_engine import AnalyticsEngine
from g6_platform.analytics.risk_analyzer import RiskAnalyzer
from g6_platform.analytics.volatility_analyzer import VolatilityAnalyzer

def main():
    """Analytics usage example."""
    
    print("📊 G6 Analytics Platform - Analytics Example")
    print("=" * 50)
    
    try:
        # Sample options data (replace with real data)
        sample_data = {
            'symbol': 'NIFTY',
            'expiry': '2024-01-25',
            'strike': 21000,
            'option_type': 'CE',
            'ltp': 150.5,
            'volume': 1000,
            'oi': 5000
        }
        
        # Initialize analytics engines
        analytics_engine = AnalyticsEngine()
        risk_analyzer = RiskAnalyzer()
        volatility_analyzer = VolatilityAnalyzer()
        
        print("🔧 Analytics engines initialized")
        
        # Perform analytics calculations
        print("\n📈 Running analytics calculations...")
        
        # IV calculation example
        iv_result = analytics_engine.calculate_implied_volatility(sample_data)
        print(f"💹 Implied Volatility: {iv_result}")
        
        # Greeks calculation example  
        greeks_result = analytics_engine.calculate_greeks(sample_data)
        print(f"📊 Greeks: {greeks_result}")
        
        # Risk analysis example
        risk_result = risk_analyzer.analyze_position_risk(sample_data)
        print(f"⚠️ Risk Analysis: {risk_result}")
        
        # Volatility analysis example
        vol_result = volatility_analyzer.analyze_volatility_surface(sample_data)
        print(f"📡 Volatility Analysis: {vol_result}")
        
        print("\n✅ Analytics calculations completed!")
        
    except Exception as e:
        print(f"❌ Analytics Error: {e}")
        print("💡 Please ensure:")
        print("   1. Analytics modules are properly imported")
        print("   2. Input data format is correct")
        print("   3. Market data is available")

if __name__ == "__main__":
    main()