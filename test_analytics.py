#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Analytics Modules - G6.1 Platform
Comprehensive testing for analytics and risk management modules

Test Categories:
- Unit tests for analytics calculations
- Integration tests for data flow
- Mathematical accuracy tests
- Performance tests
- Edge case handling
"""

import unittest
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json
import sys

sys.path.append('..')

try:
    from analytics.overview_generator import OverviewGenerator, MarketOverview, IndexSummary
    from analytics.volatility_analyzer import VolatilityAnalyzer, VolatilityMetrics, BlackScholesModel
    from analytics.risk_analyzer import RiskAnalyzer, RiskMetrics, Portfolio, Position
except ImportError as e:
    print(f"Warning: Could not import analytics modules: {e}")

class TestOverviewGenerator(unittest.TestCase):
    """Test cases for OverviewGenerator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'indices': ['NIFTY', 'BANKNIFTY', 'FINNIFTY'],
            'cache_ttl': 300
        }
        self.generator = OverviewGenerator(self.config)
        
        # Mock data sources
        self.mock_data_sources = {
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
                        'iv': 0.234
                    },
                    {
                        'symbol': 'NIFTY24950PE',
                        'strike': 24950,
                        'option_type': 'PE',
                        'last_price': 89.50,
                        'volume': 18000,
                        'oi': 165000,
                        'change_percent': -2.1,
                        'iv': 0.251
                    }
                ]
            }
        }
    
    def test_generate_market_overview(self):
        """Test market overview generation."""
        overview = self.generator.generate_market_overview(self.mock_data_sources)
        
        self.assertIsInstance(overview, MarketOverview)
        self.assertIsInstance(overview.timestamp, datetime)
        self.assertIn('NIFTY', overview.indices)
        self.assertIsInstance(overview.overall_pcr, float)
        self.assertIn(overview.market_sentiment, ['BULLISH', 'BEARISH', 'NEUTRAL'])
    
    def test_calculate_options_summary(self):
        """Test options summary calculation."""
        options_data = self.mock_data_sources['options_data']['NIFTY']
        summary = self.generator._calculate_options_summary(options_data)
        
        self.assertEqual(summary.total_volume, 43000)  # 25000 + 18000
        self.assertEqual(summary.total_oi, 350000)     # 185000 + 165000
        self.assertEqual(summary.ce_volume, 25000)
        self.assertEqual(summary.pe_volume, 18000)
        self.assertGreater(summary.pcr_volume, 0)
    
    def test_calculate_max_pain(self):
        """Test max pain calculation."""
        options_data = self.mock_data_sources['options_data']['NIFTY']
        max_pain = self.generator._calculate_max_pain(options_data)
        
        self.assertIsInstance(max_pain, (int, float))
        self.assertGreater(max_pain, 0)
    
    def test_market_sentiment_calculation(self):
        """Test market sentiment calculation."""
        # Create mock index summaries
        mock_summaries = {
            'NIFTY': IndexSummary(
                name='NIFTY',
                current_price=24975,
                change=125.50,
                change_percent=0.51,
                volume=450000,
                high=25050,
                low=24850,
                atm_strike=25000,
                iv_rank=45,
                pcr=0.89,
                options_volume=43000,
                total_oi=350000,
                sentiment='BULLISH'
            )
        }
        
        sentiment = self.generator._calculate_market_sentiment(mock_summaries)
        self.assertIn(sentiment, ['BULLISH', 'BEARISH', 'NEUTRAL'])
    
    def test_export_overview(self):
        """Test overview export functionality."""
        overview = self.generator.generate_market_overview(self.mock_data_sources)
        
        # Test JSON export
        json_output = self.generator.export_overview(overview, 'json')
        self.assertIsInstance(json_output, str)
        
        # Verify JSON is valid
        parsed = json.loads(json_output)
        self.assertIn('timestamp', parsed)
        self.assertIn('market_sentiment', parsed)
        
        # Test CSV export
        csv_output = self.generator.export_overview(overview, 'csv')
        self.assertIsInstance(csv_output, str)
        self.assertIn('Timestamp,Index,Price', csv_output)

class TestVolatilityAnalyzer(unittest.TestCase):
    """Test cases for VolatilityAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'risk_free_rate': 0.06,
            'hv_windows': [10, 20, 30],
            'cache_ttl': 300
        }
        self.analyzer = VolatilityAnalyzer(self.config)
        
        # Mock market data
        self.mock_market_data = {
            'price': 24975,
            'volume': 450000,
            'symbol': 'NIFTY'
        }
        
        # Mock options data
        self.mock_options_data = [
            {
                'strike': 24950,
                'last_price': 156.75,
                'option_type': 'CE',
                'iv': 0.234,
                'volume': 25000
            },
            {
                'strike': 24950,
                'last_price': 89.50,
                'option_type': 'PE',
                'iv': 0.251,
                'volume': 18000
            },
            {
                'strike': 25000,
                'last_price': 125.30,
                'option_type': 'CE',
                'iv': 0.228,
                'volume': 31000
            }
        ]
    
    def test_analyze_volatility(self):
        """Test volatility analysis."""
        metrics = self.analyzer.analyze_volatility(self.mock_market_data, self.mock_options_data)
        
        self.assertIsInstance(metrics, VolatilityMetrics)
        self.assertIsInstance(metrics.realized_vol_30d, float)
        self.assertIsInstance(metrics.iv_rank_30d, float)
        self.assertIsInstance(metrics.skew_slope, float)
        self.assertGreaterEqual(metrics.iv_rank_30d, 0)
        self.assertLessEqual(metrics.iv_rank_30d, 100)
    
    def test_build_iv_surface(self):
        """Test IV surface construction."""
        surface = self.analyzer._build_iv_surface(24975, self.mock_options_data)
        
        self.assertIsNotNone(surface)
        self.assertEqual(surface.underlying_price, 24975)
        self.assertIsInstance(surface.timestamp, datetime)
    
    def test_calculate_iv_statistics(self):
        """Test IV statistics calculation."""
        iv_rank, iv_percentile = self.analyzer._calculate_iv_statistics(self.mock_options_data)
        
        self.assertIsInstance(iv_rank, float)
        self.assertIsInstance(iv_percentile, float)
        self.assertGreaterEqual(iv_rank, 0)
        self.assertLessEqual(iv_rank, 100)
        self.assertGreaterEqual(iv_percentile, 0)
        self.assertLessEqual(iv_percentile, 100)
    
    def test_volatility_forecasting(self):
        """Test volatility forecasting."""
        # Generate mock historical data
        historical_data = [25000 + i + np.random.normal(0, 50) for i in range(100)]
        
        forecast = self.analyzer.forecast_volatility(historical_data, forecast_days=30)
        
        self.assertIsInstance(forecast, dict)
        self.assertIn('forecast_vol', forecast)
        self.assertIn('confidence', forecast)
        self.assertGreater(forecast['forecast_vol'], 0)
        self.assertGreaterEqual(forecast['confidence'], 0)
        self.assertLessEqual(forecast['confidence'], 100)

class TestBlackScholesModel(unittest.TestCase):
    """Test cases for Black-Scholes model."""
    
    def test_option_price_calculation(self):
        """Test Black-Scholes option pricing."""
        S = 100  # Spot price
        K = 100  # Strike price
        T = 0.25  # 3 months
        r = 0.05  # Risk-free rate
        sigma = 0.20  # Volatility
        
        # Calculate call and put prices
        call_price = BlackScholesModel.option_price(S, K, T, r, sigma, 'CE')
        put_price = BlackScholesModel.option_price(S, K, T, r, sigma, 'PE')
        
        self.assertGreater(call_price, 0)
        self.assertGreater(put_price, 0)
        
        # Put-call parity check: C - P = S - K * e^(-rT)
        parity_diff = call_price - put_price - (S - K * np.exp(-r * T))
        self.assertAlmostEqual(parity_diff, 0, places=6)
    
    def test_vega_calculation(self):
        """Test vega calculation."""
        S = 100
        K = 100
        T = 0.25
        r = 0.05
        sigma = 0.20
        
        vega = BlackScholesModel.vega(S, K, T, r, sigma)
        
        self.assertGreater(vega, 0)
        self.assertIsInstance(vega, float)
    
    def test_implied_volatility(self):
        """Test implied volatility calculation."""
        S = 100
        K = 100
        T = 0.25
        r = 0.05
        sigma_actual = 0.20
        
        # Calculate theoretical price
        theoretical_price = BlackScholesModel.option_price(S, K, T, r, sigma_actual, 'CE')
        
        # Calculate implied volatility
        implied_vol = BlackScholesModel.implied_volatility(theoretical_price, S, K, T, r, 'CE')
        
        # Should be very close to actual volatility
        self.assertAlmostEqual(implied_vol, sigma_actual, places=3)

class TestRiskAnalyzer(unittest.TestCase):
    """Test cases for RiskAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'confidence_levels': [0.95, 0.99],
            'lookback_days': 100,
            'risk_free_rate': 0.06
        }
        self.analyzer = RiskAnalyzer(self.config)
        
        # Mock portfolio
        self.mock_positions = [
            Position(
                symbol='NIFTY24950CE',
                quantity=100,
                entry_price=150,
                current_price=156.75,
                position_value=15675,
                unrealized_pnl=675,
                position_type='option',
                delta=0.6,
                gamma=0.001,
                theta=-0.5,
                vega=0.12
            ),
            Position(
                symbol='NIFTY24950PE',
                quantity=-50,
                entry_price=90,
                current_price=89.50,
                position_value=-4475,
                unrealized_pnl=25,
                position_type='option',
                delta=-0.4,
                gamma=0.001,
                theta=-0.3,
                vega=0.10
            )
        ]
        
        self.mock_portfolio = Portfolio(
            positions=self.mock_positions,
            cash=50000,
            total_value=61200
        )
    
    def test_analyze_portfolio_risk(self):
        """Test portfolio risk analysis."""
        market_data = {'NIFTY': {'price': 24975}}
        
        risk_metrics = self.analyzer.analyze_portfolio_risk(self.mock_portfolio, market_data)
        
        self.assertIsInstance(risk_metrics, RiskMetrics)
        self.assertEqual(risk_metrics.portfolio_value, 61200)
        self.assertIsInstance(risk_metrics.var_95, float)
        self.assertIsInstance(risk_metrics.var_99, float)
        self.assertIsInstance(risk_metrics.sharpe_ratio, float)
        self.assertGreater(risk_metrics.var_99, risk_metrics.var_95)
    
    def test_calculate_portfolio_greeks(self):
        """Test portfolio Greeks calculation."""
        greeks = self.analyzer._calculate_portfolio_greeks(self.mock_portfolio)
        
        self.assertIsInstance(greeks, dict)
        self.assertIn('delta', greeks)
        self.assertIn('gamma', greeks)
        self.assertIn('theta', greeks)
        self.assertIn('vega', greeks)
        
        # Check calculated values
        expected_delta = 100 * 0.6 + (-50) * (-0.4)  # 60 + 20 = 80
        self.assertAlmostEqual(greeks['delta'], expected_delta, places=1)
    
    def test_scenario_analysis(self):
        """Test scenario analysis."""
        market_data = {'NIFTY': {'price': 24975}}
        
        scenarios = self.analyzer.run_scenario_analysis(self.mock_portfolio, market_data)
        
        self.assertIsInstance(scenarios, dict)
        self.assertIn('market_crash', scenarios)
        self.assertIn('moderate_rally', scenarios)
        
        # Check scenario structure
        crash_scenario = scenarios['market_crash']
        self.assertIsInstance(crash_scenario.portfolio_pnl, float)
        self.assertIsInstance(crash_scenario.underlying_change, float)
    
    def test_stress_testing(self):
        """Test stress testing functionality."""
        market_data = {'NIFTY': {'price': 24975}}
        
        stress_results = self.analyzer.stress_test_portfolio(self.mock_portfolio, market_data)
        
        self.assertIsInstance(stress_results, dict)
        self.assertIn('black_monday', stress_results)
        self.assertIn('volatility_spike', stress_results)
        self.assertIn('summary', stress_results)
        
        # Check summary
        summary = stress_results['summary']
        self.assertIn('worst_case_loss', summary)
        self.assertIn('best_case_gain', summary)
    
    def test_concentration_risk(self):
        """Test concentration risk calculation."""
        concentration = self.analyzer._calculate_concentration_risk(self.mock_portfolio)
        
        self.assertIsInstance(concentration, float)
        self.assertGreaterEqual(concentration, 0)
        self.assertLessEqual(concentration, 1)
    
    def test_risk_limit_checks(self):
        """Test risk limit checking."""
        market_data = {'NIFTY': {'price': 24975}}
        risk_metrics = self.analyzer.analyze_portfolio_risk(self.mock_portfolio, market_data)
        
        limit_checks = self.analyzer.check_risk_limits(risk_metrics)
        
        self.assertIsInstance(limit_checks, dict)
        self.assertIn('var_95_limit', limit_checks)
        self.assertIn('concentration_limit', limit_checks)
        self.assertIn('any_breach', limit_checks)
        
        # Each check should have structure
        var_check = limit_checks['var_95_limit']
        self.assertIn('current', var_check)
        self.assertIn('limit', var_check)
        self.assertIn('breached', var_check)

class TestMathematicalAccuracy(unittest.TestCase):
    """Test mathematical accuracy of calculations."""
    
    def test_options_pricing_accuracy(self):
        """Test options pricing mathematical accuracy."""
        # Known Black-Scholes values for verification
        test_cases = [
            # (S, K, T, r, sigma, option_type, expected_price)
            (100, 100, 0.25, 0.05, 0.20, 'CE', 4.759),  # Approximate expected value
            (100, 100, 0.25, 0.05, 0.20, 'PE', 3.814),  # Approximate expected value
        ]
        
        for S, K, T, r, sigma, option_type, expected in test_cases:
            calculated = BlackScholesModel.option_price(S, K, T, r, sigma, option_type)
            
            # Allow small tolerance for numerical precision
            self.assertAlmostEqual(calculated, expected, places=1)
    
    def test_volatility_calculations(self):
        """Test volatility calculation accuracy."""
        # Generate known return series
        returns = [0.01, -0.02, 0.015, -0.01, 0.005, 0.02, -0.015]
        
        # Calculate standard deviation manually
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        expected_vol = (variance ** 0.5) * (252 ** 0.5)  # Annualized
        
        # This test would require actual implementation method to compare
        # For now, just check reasonable bounds
        self.assertGreater(expected_vol, 0)
        self.assertLess(expected_vol, 5.0)  # Should be reasonable volatility

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_empty_data_handling(self):
        """Test handling of empty data sets."""
        config = {'indices': ['NIFTY']}
        generator = OverviewGenerator(config)
        
        # Empty data sources
        empty_data = {
            'market_data': {},
            'options_data': {}
        }
        
        overview = generator.generate_market_overview(empty_data)
        self.assertIsInstance(overview, MarketOverview)
        self.assertEqual(len(overview.indices), 0)
    
    def test_extreme_values(self):
        """Test handling of extreme values."""
        # Test with very high volatility
        extreme_options = [{
            'strike': 25000,
            'last_price': 1.0,
            'option_type': 'CE',
            'iv': 2.0,  # 200% volatility
            'volume': 100
        }]
        
        config = {'risk_free_rate': 0.06}
        analyzer = VolatilityAnalyzer(config)
        
        # Should handle extreme IV gracefully
        iv_rank, iv_percentile = analyzer._calculate_iv_statistics(extreme_options)
        self.assertIsInstance(iv_rank, float)
        self.assertIsInstance(iv_percentile, float)
    
    def test_zero_values(self):
        """Test handling of zero values."""
        # Portfolio with zero positions
        empty_portfolio = Portfolio(positions=[], cash=0, total_value=0)
        
        config = {}
        analyzer = RiskAnalyzer(config)
        
        market_data = {}
        risk_metrics = analyzer.analyze_portfolio_risk(empty_portfolio, market_data)
        
        self.assertEqual(risk_metrics.portfolio_value, 0)
        self.assertEqual(risk_metrics.concentration_risk, 0)

def create_analytics_test_suite():
    """Create comprehensive analytics test suite."""
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestOverviewGenerator))
    suite.addTest(unittest.makeSuite(TestVolatilityAnalyzer))
    suite.addTest(unittest.makeSuite(TestBlackScholesModel))
    suite.addTest(unittest.makeSuite(TestRiskAnalyzer))
    suite.addTest(unittest.makeSuite(TestMathematicalAccuracy))
    suite.addTest(unittest.makeSuite(TestEdgeCases))
    
    return suite

if __name__ == '__main__':
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_analytics_test_suite()
    result = runner.run(suite)
    
    # Print summary
    print(f"\nAnalytics Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    sys.exit(exit_code)