#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Risk Analyzer - G6.1 Platform
Comprehensive risk analysis and portfolio risk management

Features:
- Portfolio risk metrics calculation
- Value at Risk (VaR) estimation
- Greeks-based risk analysis
- Scenario analysis and stress testing
- Risk attribution and decomposition
- Real-time risk monitoring
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from scipy import stats
from collections import defaultdict
import math

@dataclass
class RiskMetrics:
    """Comprehensive risk metrics container."""
    timestamp: datetime
    portfolio_value: float
    var_95: float
    var_99: float
    expected_shortfall_95: float
    expected_shortfall_99: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    beta: float
    alpha: float
    volatility: float
    greeks_exposure: Dict[str, float]
    sector_exposure: Dict[str, float]
    concentration_risk: float
    liquidity_risk: float

@dataclass
class Position:
    """Individual position representation."""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    position_value: float
    unrealized_pnl: float
    position_type: str  # 'stock', 'option', 'future'
    expiry: Optional[datetime] = None
    strike: Optional[float] = None
    option_type: Optional[str] = None  # 'CE', 'PE'
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None

@dataclass
class Portfolio:
    """Portfolio container with positions and metadata."""
    positions: List[Position] = field(default_factory=list)
    cash: float = 0.0
    total_value: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ScenarioResult:
    """Scenario analysis result."""
    scenario_name: str
    underlying_change: float
    portfolio_pnl: float
    portfolio_value: float
    individual_position_pnl: Dict[str, float]
    greeks_contribution: Dict[str, float]

class RiskAnalyzer:
    """Main risk analyzer class."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize risk analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.confidence_levels = config.get('confidence_levels', [0.95, 0.99])
        self.lookback_days = config.get('lookback_days', 252)
        self.risk_free_rate = config.get('risk_free_rate', 0.06)
        self.benchmark_returns = []  # Should be loaded from data source
        
        # Risk limits and thresholds
        self.risk_limits = config.get('risk_limits', {
            'max_portfolio_var': 100000,  # Maximum daily VaR
            'max_position_concentration': 0.20,  # 20% max position size
            'max_sector_concentration': 0.30,  # 30% max sector exposure
            'max_delta_exposure': 50000,  # Maximum delta exposure
            'min_liquidity_ratio': 0.10  # Minimum cash/liquid assets ratio
        })
        
        # Scenario definitions
        self.standard_scenarios = {
            'market_crash': -0.10,  # 10% market decline
            'moderate_decline': -0.05,  # 5% market decline
            'small_decline': -0.02,  # 2% market decline
            'normal': 0.00, # No change
            'small_rally': 0.02,  # 2% market rally
            'moderate_rally': 0.05,  # 5% market rally
            'strong_rally': 0.10  # 10% market rally
        }
    
    def analyze_portfolio_risk(self, portfolio: Portfolio, market_data: Dict[str, Any]) -> RiskMetrics:
        """Perform comprehensive portfolio risk analysis.
        
        Args:
            portfolio: Portfolio object with positions
            market_data: Current market data
            
        Returns:
            RiskMetrics object with complete risk analysis
        """
        # Calculate portfolio returns
        portfolio_returns = self._calculate_portfolio_returns(portfolio)
        
        # Calculate VaR and Expected Shortfall
        var_95, var_99 = self._calculate_var(portfolio_returns)
        es_95, es_99 = self._calculate_expected_shortfall(portfolio_returns)
        
        # Calculate portfolio Greeks
        greeks_exposure = self._calculate_portfolio_greeks(portfolio)
        
        # Calculate risk-adjusted returns
        sharpe_ratio = self._calculate_sharpe_ratio(portfolio_returns)
        sortino_ratio = self._calculate_sortino_ratio(portfolio_returns)
        
        # Calculate market risk metrics
        beta, alpha = self._calculate_beta_alpha(portfolio_returns)
        
        # Calculate concentration and sector risks
        concentration_risk = self._calculate_concentration_risk(portfolio)
        sector_exposure = self._calculate_sector_exposure(portfolio)
        
        # Calculate liquidity risk
        liquidity_risk = self._calculate_liquidity_risk(portfolio)
        
        # Calculate maximum drawdown
        max_drawdown = self._calculate_max_drawdown(portfolio_returns)
        
        # Calculate portfolio volatility
        volatility = np.std(portfolio_returns) * np.sqrt(252) if len(portfolio_returns) > 1 else 0
        
        return RiskMetrics(
            timestamp=datetime.now(),
            portfolio_value=portfolio.total_value,
            var_95=var_95,
            var_99=var_99,
            expected_shortfall_95=es_95,
            expected_shortfall_99=es_99,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            beta=beta,
            alpha=alpha,
            volatility=volatility,
            greeks_exposure=greeks_exposure,
            sector_exposure=sector_exposure,
            concentration_risk=concentration_risk,
            liquidity_risk=liquidity_risk
        )
    
    def _calculate_portfolio_returns(self, portfolio: Portfolio) -> List[float]:
        """Calculate historical portfolio returns.
        
        Args:
            portfolio: Portfolio object
            
        Returns:
            List of daily portfolio returns
        """
        # Mock historical returns for demonstration
        # In real implementation, this would use historical position data
        
        # Generate synthetic portfolio returns with realistic characteristics
        returns = []
        base_return = 0.0001  # Small positive drift
        volatility = 0.015  # ~23% annual volatility
        
        for _ in range(self.lookback_days):
            daily_return = np.random.normal(base_return, volatility)
            returns.append(daily_return)
        
        return returns
    
    def _calculate_var(self, returns: List[float]) -> Tuple[float, float]:
        """Calculate Value at Risk at different confidence levels.
        
        Args:
            returns: List of portfolio returns
            
        Returns:
            Tuple of (VaR_95%, VaR_99%)
        """
        if not returns:
            return 0, 0
        
        returns_array = np.array(returns)
        
        # Calculate VaR using historical simulation
        var_95 = np.percentile(returns_array, 5)  # 5th percentile for 95% confidence
        var_99 = np.percentile(returns_array, 1)  # 1st percentile for 99% confidence
        
        # Convert to absolute values (losses are positive in risk management)
        var_95 = abs(var_95)
        var_99 = abs(var_99)
        
        return var_95, var_99
    
    def _calculate_expected_shortfall(self, returns: List[float]) -> Tuple[float, float]:
        """Calculate Expected Shortfall (Conditional VaR).
        
        Args:
            returns: List of portfolio returns
            
        Returns:
            Tuple of (ES_95%, ES_99%)
        """
        if not returns:
            return 0, 0
        
        returns_array = np.array(returns)
        
        # Calculate ES as mean of returns below VaR threshold
        var_95_threshold = np.percentile(returns_array, 5)
        var_99_threshold = np.percentile(returns_array, 1)
        
        es_95 = np.mean(returns_array[returns_array <= var_95_threshold])
        es_99 = np.mean(returns_array[returns_array <= var_99_threshold])
        
        # Convert to absolute values
        es_95 = abs(es_95)
        es_99 = abs(es_99)
        
        return es_95, es_99
    
    def _calculate_portfolio_greeks(self, portfolio: Portfolio) -> Dict[str, float]:
        """Calculate aggregate portfolio Greeks.
        
        Args:
            portfolio: Portfolio object
            
        Returns:
            Dictionary with portfolio Greeks
        """
        greeks = {
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }
        
        for position in portfolio.positions:
            if position.position_type == 'option':
                # Weight Greeks by position size
                position_weight = position.quantity
                
                if position.delta:
                    greeks['delta'] += position.delta * position_weight
                if position.gamma:
                    greeks['gamma'] += position.gamma * position_weight
                if position.theta:
                    greeks['theta'] += position.theta * position_weight
                if position.vega:
                    greeks['vega'] += position.vega * position_weight
                if position.rho:
                    greeks['rho'] += position.rho * position_weight
        
        return greeks
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio.
        
        Args:
            returns: List of returns
            
        Returns:
            Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return 0
        
        excess_returns = np.array(returns) - (self.risk_free_rate / 252)  # Daily risk-free rate
        
        if np.std(excess_returns) == 0:
            return 0
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        return sharpe
    
    def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """Calculate Sortino ratio (downside deviation).
        
        Args:
            returns: List of returns
            
        Returns:
            Sortino ratio
        """
        if not returns or len(returns) < 2:
            return 0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - (self.risk_free_rate / 252)
        
        # Calculate downside deviation
        negative_returns = excess_returns[excess_returns < 0]
        
        if len(negative_returns) == 0:
            return float('inf')  # No downside volatility
        
        downside_deviation = np.std(negative_returns)
        
        if downside_deviation == 0:
            return 0
        
        sortino = np.mean(excess_returns) / downside_deviation * np.sqrt(252)
        return sortino
    
    def _calculate_beta_alpha(self, portfolio_returns: List[float]) -> Tuple[float, float]:
        """Calculate portfolio beta and alpha relative to benchmark.
        
        Args:
            portfolio_returns: List of portfolio returns
            
        Returns:
            Tuple of (beta, alpha)
        """
        if not portfolio_returns or not self.benchmark_returns:
            return 1.0, 0.0  # Default beta=1, alpha=0
        
        # Mock benchmark returns for demonstration
        # In real implementation, use actual benchmark data (NIFTY, etc.)
        benchmark_returns = self._get_benchmark_returns(len(portfolio_returns))
        
        if len(benchmark_returns) != len(portfolio_returns):
            return 1.0, 0.0
        
        # Calculate beta using linear regression
        port_returns = np.array(portfolio_returns)
        bench_returns = np.array(benchmark_returns)
        
        covariance = np.cov(port_returns, bench_returns)[0, 1]
        benchmark_variance = np.var(bench_returns)
        
        if benchmark_variance == 0:
            beta = 1.0
        else:
            beta = covariance / benchmark_variance
        
        # Calculate alpha (Jensen's alpha)
        portfolio_mean = np.mean(port_returns) * 252  # Annualized
        benchmark_mean = np.mean(bench_returns) * 252  # Annualized
        
        alpha = portfolio_mean - (self.risk_free_rate + beta * (benchmark_mean - self.risk_free_rate))
        
        return beta, alpha
    
    def _get_benchmark_returns(self, length: int) -> List[float]:
        """Generate or retrieve benchmark returns.
        
        Args:
            length: Number of returns needed
            
        Returns:
            List of benchmark returns
        """
        # Mock NIFTY returns for demonstration
        returns = []
        for _ in range(length):
            # Generate returns with market-like characteristics
            daily_return = np.random.normal(0.0005, 0.012)  # ~18% annual vol
            returns.append(daily_return)
        
        return returns
    
    def _calculate_concentration_risk(self, portfolio: Portfolio) -> float:
        """Calculate portfolio concentration risk.
        
        Args:
            portfolio: Portfolio object
            
        Returns:
            Concentration risk metric (0-1, higher is more concentrated)
        """
        if not portfolio.positions or portfolio.total_value == 0:
            return 0
        
        # Calculate position weights
        position_weights = []
        
        for position in portfolio.positions:
            weight = abs(position.position_value) / portfolio.total_value
            position_weights.append(weight)
        
        if not position_weights:
            return 0
        
        # Calculate Herfindahl-Hirschman Index (HHI) for concentration
        hhi = sum(weight ** 2 for weight in position_weights)
        
        # Normalize to 0-1 scale (1 = fully concentrated, 0 = perfectly diversified)
        # For n equal positions, HHI = 1/n, so we can normalize
        return hhi
    
    def _calculate_sector_exposure(self, portfolio: Portfolio) -> Dict[str, float]:
        """Calculate sector-wise exposure.
        
        Args:
            portfolio: Portfolio object
            
        Returns:
            Dictionary with sector exposures
        """
        sector_exposure = defaultdict(float)
        
        if portfolio.total_value == 0:
            return dict(sector_exposure)
        
        # Mock sector classification for demonstration
        sector_mapping = {
            'NIFTY': 'Index',
            'BANKNIFTY': 'Banking',
            'FINNIFTY': 'Financial',
            'MIDCPNIFTY': 'MidCap'
        }
        
        for position in portfolio.positions:
            # Extract underlying from option symbol if needed
            underlying = self._extract_underlying(position.symbol)
            sector = sector_mapping.get(underlying, 'Other')
            
            exposure = abs(position.position_value) / portfolio.total_value
            sector_exposure[sector] += exposure
        
        return dict(sector_exposure)
    
    def _extract_underlying(self, symbol: str) -> str:
        """Extract underlying symbol from option symbol.
        
        Args:
            symbol: Full symbol (e.g., NIFTY24950CE)
            
        Returns:
            Underlying symbol (e.g., NIFTY)
        """
        # Simple extraction logic
        for underlying in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']:
            if symbol.startswith(underlying):
                return underlying
        
        return symbol
    
    def _calculate_liquidity_risk(self, portfolio: Portfolio) -> float:
        """Calculate portfolio liquidity risk.
        
        Args:
            portfolio: Portfolio object
            
        Returns:
            Liquidity risk metric (0-1, higher is less liquid)
        """
        if not portfolio.positions or portfolio.total_value == 0:
            return 0
        
        # Simplified liquidity scoring
        liquidity_scores = {
            'stock': 0.1,    # Stocks are generally liquid
            'option': 0.3,   # Options less liquid
            'future': 0.2    # Futures moderately liquid
        }
        
        weighted_illiquidity = 0
        
        for position in portfolio.positions:
            position_weight = abs(position.position_value) / portfolio.total_value
            illiquidity_score = liquidity_scores.get(position.position_type, 0.5)
            
            # Adjust for time to expiry (options become less liquid near expiry)
            if position.position_type == 'option' and position.expiry:
                days_to_expiry = (position.expiry - datetime.now()).days
                if days_to_expiry < 7:
                    illiquidity_score *= 1.5  # Increase illiquidity for near expiry
            
            weighted_illiquidity += position_weight * illiquidity_score
        
        return weighted_illiquidity
    
    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown.
        
        Args:
            returns: List of returns
            
        Returns:
            Maximum drawdown (positive value)
        """
        if not returns:
            return 0
        
        # Calculate cumulative returns
        cumulative_returns = np.cumprod(1 + np.array(returns))
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(cumulative_returns)
        
        # Calculate drawdowns
        drawdowns = (cumulative_returns - running_max) / running_max
        
        # Return maximum drawdown (as positive value)
        return abs(np.min(drawdowns))
    
    def run_scenario_analysis(self, portfolio: Portfolio, market_data: Dict[str, Any]) -> Dict[str, ScenarioResult]:
        """Run scenario analysis on portfolio.
        
        Args:
            portfolio: Portfolio object
            market_data: Current market data
            
        Returns:
            Dictionary mapping scenario names to results
        """
        scenario_results = {}
        
        for scenario_name, underlying_change in self.standard_scenarios.items():
            result = self._calculate_scenario_pnl(portfolio, underlying_change, market_data)
            scenario_results[scenario_name] = result
        
        return scenario_results
    
    def _calculate_scenario_pnl(self, portfolio: Portfolio, underlying_change: float, market_data: Dict[str, Any]) -> ScenarioResult:
        """Calculate P&L for a specific scenario.
        
        Args:
            portfolio: Portfolio object
            underlying_change: Percentage change in underlying (e.g., -0.05 for -5%)
            market_data: Current market data
            
        Returns:
            ScenarioResult object
        """
        total_pnl = 0
        position_pnl = {}
        greeks_contribution = {
            'delta': 0,
            'gamma': 0,
            'theta': 0,
            'vega': 0
        }
        
        # Simplified scenario calculation using Greeks
        underlying_price_change = underlying_change  # Assume absolute change for simplicity
        
        for position in portfolio.positions:
            if position.position_type == 'option':
                # Calculate P&L using Greeks (first-order approximation)
                delta_pnl = (position.delta or 0) * underlying_price_change * position.quantity
                gamma_pnl = 0.5 * (position.gamma or 0) * (underlying_price_change ** 2) * position.quantity
                
                # Theta decay (assume 1 day)
                theta_pnl = (position.theta or 0) * position.quantity
                
                # Vega (assume no volatility change for base scenario)
                vega_pnl = 0
                
                position_total_pnl = delta_pnl + gamma_pnl + theta_pnl + vega_pnl
                
                # Track contributions
                greeks_contribution['delta'] += delta_pnl
                greeks_contribution['gamma'] += gamma_pnl
                greeks_contribution['theta'] += theta_pnl
                greeks_contribution['vega'] += vega_pnl
                
            else:
                # Stock position - linear P&L
                position_total_pnl = position.quantity * position.current_price * underlying_change
            
            position_pnl[position.symbol] = position_total_pnl
            total_pnl += position_total_pnl
        
        scenario_name = f"Underlying {underlying_change:+.1%}"
        
        return ScenarioResult(
            scenario_name=scenario_name,
            underlying_change=underlying_change,
            portfolio_pnl=total_pnl,
            portfolio_value=portfolio.total_value + total_pnl,
            individual_position_pnl=position_pnl,
            greeks_contribution=greeks_contribution
        )
    
    def stress_test_portfolio(self, portfolio: Portfolio, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive stress tests on portfolio.
        
        Args:
            portfolio: Portfolio object
            market_data: Current market data
            
        Returns:
            Dictionary with stress test results
        """
        stress_scenarios = {
            'black_monday': -0.20,      # 20% crash
            'covid_crash': -0.30,       # 30% crash
            'flash_crash': -0.15,       # 15% flash crash
            'volatility_spike': 0.0,    # No price change but vol spike
            'interest_rate_shock': 0.0   # Rate change scenario
        }
        
        stress_results = {}
        
        for scenario_name, price_change in stress_scenarios.items():
            if scenario_name == 'volatility_spike':
                # Special handling for volatility scenarios
                result = self._stress_test_volatility(portfolio, vol_change=0.5)  # 50% vol increase
            elif scenario_name == 'interest_rate_shock':
                # Special handling for interest rate scenarios
                result = self._stress_test_interest_rates(portfolio, rate_change=0.02)  # 200bp increase
            else:
                # Standard price shock
                result = self._calculate_scenario_pnl(portfolio, price_change, market_data)
            
            stress_results[scenario_name] = result
        
        # Calculate stress test summary
        worst_case_loss = min(result.portfolio_pnl for result in stress_results.values())
        best_case_gain = max(result.portfolio_pnl for result in stress_results.values())
        
        stress_results['summary'] = {
            'worst_case_loss': worst_case_loss,
            'best_case_gain': best_case_gain,
            'stress_ratio': abs(worst_case_loss) / portfolio.total_value if portfolio.total_value > 0 else 0
        }
        
        return stress_results
    
    def _stress_test_volatility(self, portfolio: Portfolio, vol_change: float) -> ScenarioResult:
        """Stress test with volatility change.
        
        Args:
            portfolio: Portfolio object
            vol_change: Percentage change in volatility
            
        Returns:
            ScenarioResult object
        """
        total_pnl = 0
        position_pnl = {}
        greeks_contribution = {'vega': 0, 'delta': 0, 'gamma': 0, 'theta': 0}
        
        for position in portfolio.positions:
            if position.position_type == 'option' and position.vega:
                # Calculate vega P&L
                vega_pnl = position.vega * vol_change * position.quantity
                position_pnl[position.symbol] = vega_pnl
                total_pnl += vega_pnl
                greeks_contribution['vega'] += vega_pnl
        
        return ScenarioResult(
            scenario_name="Volatility Shock",
            underlying_change=0.0,
            portfolio_pnl=total_pnl,
            portfolio_value=portfolio.total_value + total_pnl,
            individual_position_pnl=position_pnl,
            greeks_contribution=greeks_contribution
        )
    
    def _stress_test_interest_rates(self, portfolio: Portfolio, rate_change: float) -> ScenarioResult:
        """Stress test with interest rate change.
        
        Args:
            portfolio: Portfolio object
            rate_change: Change in interest rates (e.g., 0.02 for 200bp)
            
        Returns:
            ScenarioResult object
        """
        total_pnl = 0
        position_pnl = {}
        greeks_contribution = {'rho': 0, 'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
        
        for position in portfolio.positions:
            if position.position_type == 'option' and position.rho:
                # Calculate rho P&L
                rho_pnl = position.rho * rate_change * position.quantity
                position_pnl[position.symbol] = rho_pnl
                total_pnl += rho_pnl
                greeks_contribution['rho'] += rho_pnl
        
        return ScenarioResult(
            scenario_name="Interest Rate Shock",
            underlying_change=0.0,
            portfolio_pnl=total_pnl,
            portfolio_value=portfolio.total_value + total_pnl,
            individual_position_pnl=position_pnl,
            greeks_contribution=greeks_contribution
        )
    
    def check_risk_limits(self, risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """Check portfolio against defined risk limits.
        
        Args:
            risk_metrics: RiskMetrics object
            
        Returns:
            Dictionary with limit check results
        """
        limit_checks = {}
        
        # VaR limit check
        limit_checks['var_95_limit'] = {
            'current': risk_metrics.var_95 * risk_metrics.portfolio_value,
            'limit': self.risk_limits['max_portfolio_var'],
            'breached': (risk_metrics.var_95 * risk_metrics.portfolio_value) > self.risk_limits['max_portfolio_var']
        }
        
        # Concentration limit check
        limit_checks['concentration_limit'] = {
            'current': risk_metrics.concentration_risk,
            'limit': self.risk_limits['max_position_concentration'],
            'breached': risk_metrics.concentration_risk > self.risk_limits['max_position_concentration']
        }
        
        # Delta exposure limit check
        delta_exposure = abs(risk_metrics.greeks_exposure.get('delta', 0))
        limit_checks['delta_limit'] = {
            'current': delta_exposure,
            'limit': self.risk_limits['max_delta_exposure'],
            'breached': delta_exposure > self.risk_limits['max_delta_exposure']
        }
        
        # Liquidity limit check
        limit_checks['liquidity_limit'] = {
            'current': risk_metrics.liquidity_risk,
            'limit': self.risk_limits['min_liquidity_ratio'],
            'breached': risk_metrics.liquidity_risk > (1 - self.risk_limits['min_liquidity_ratio'])
        }
        
        # Overall breach status
        limit_checks['any_breach'] = any(check['breached'] for check in limit_checks.values() if isinstance(check, dict) and 'breached' in check)
        
        return limit_checks
    
    def generate_risk_report(self, risk_metrics: RiskMetrics, scenario_results: Dict[str, ScenarioResult]) -> str:
        """Generate comprehensive risk report.
        
        Args:
            risk_metrics: RiskMetrics object
            scenario_results: Scenario analysis results
            
        Returns:
            Formatted risk report string
        """
        report = []
        report.append("=" * 60)
        report.append("PORTFOLIO RISK ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Report Date: {risk_metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Portfolio Value: ${risk_metrics.portfolio_value:,.2f}")
        report.append("")
        
        # Risk Metrics Section
        report.append("RISK METRICS")
        report.append("-" * 30)
        report.append(f"Daily VaR (95%): ${risk_metrics.var_95 * risk_metrics.portfolio_value:,.2f}")
        report.append(f"Daily VaR (99%): ${risk_metrics.var_99 * risk_metrics.portfolio_value:,.2f}")
        report.append(f"Expected Shortfall (95%): ${risk_metrics.expected_shortfall_95 * risk_metrics.portfolio_value:,.2f}")
        report.append(f"Maximum Drawdown: {risk_metrics.max_drawdown:.2%}")
        report.append(f"Portfolio Volatility: {risk_metrics.volatility:.2%}")
        report.append(f"Sharpe Ratio: {risk_metrics.sharpe_ratio:.2f}")
        report.append(f"Beta: {risk_metrics.beta:.2f}")
        report.append("")
        
        # Greeks Exposure Section
        report.append("GREEKS EXPOSURE")
        report.append("-" * 30)
        for greek, value in risk_metrics.greeks_exposure.items():
            report.append(f"{greek.capitalize()}: {value:,.2f}")
        report.append("")
        
        # Scenario Analysis Section
        report.append("SCENARIO ANALYSIS")
        report.append("-" * 30)
        for scenario_name, result in scenario_results.items():
            if isinstance(result, ScenarioResult):
                pnl_pct = (result.portfolio_pnl / risk_metrics.portfolio_value) * 100 if risk_metrics.portfolio_value > 0 else 0
                report.append(f"{scenario_name}: ${result.portfolio_pnl:,.2f} ({pnl_pct:+.2f}%)")
        report.append("")
        
        # Risk Concentrations
        report.append("RISK CONCENTRATIONS")
        report.append("-" * 30)
        report.append(f"Concentration Risk: {risk_metrics.concentration_risk:.2%}")
        report.append(f"Liquidity Risk: {risk_metrics.liquidity_risk:.2%}")
        report.append("")
        
        # Sector Exposure
        if risk_metrics.sector_exposure:
            report.append("SECTOR EXPOSURE")
            report.append("-" * 30)
            for sector, exposure in risk_metrics.sector_exposure.items():
                report.append(f"{sector}: {exposure:.2%}")
        
        return "\n".join(report)

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        'confidence_levels': [0.95, 0.99],
        'lookback_days': 252,
        'risk_free_rate': 0.06,
        'risk_limits': {
            'max_portfolio_var': 50000,
            'max_position_concentration': 0.25,
            'max_delta_exposure': 25000
        }
    }
    
    # Initialize analyzer
    analyzer = RiskAnalyzer(config)
    
    # Example portfolio
    portfolio = Portfolio(
        positions=[
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
            )
        ],
        cash=50000,
        total_value=65675
    )
    
    # Mock market data
    market_data = {'NIFTY': {'price': 24975}}
    
    # Perform risk analysis
    risk_metrics = analyzer.analyze_portfolio_risk(portfolio, market_data)
    scenario_results = analyzer.run_scenario_analysis(portfolio, market_data)
    
    # Generate report
    report = analyzer.generate_risk_report(risk_metrics, scenario_results)
    print(report)