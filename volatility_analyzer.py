#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Volatility Analyzer - G6.1 Platform
Advanced volatility analysis and surface modeling

Features:
- Implied Volatility (IV) surface construction
- Historical volatility calculation
- Volatility skew and smile analysis
- Term structure analysis
- Volatility forecasting models
- Risk-neutral density estimation
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from scipy import interpolate
from scipy.optimize import minimize_scalar
import statistics
import math

@dataclass
class VolatilityPoint:
    """Individual volatility data point."""
    strike: float
    expiry: datetime
    option_type: str
    implied_vol: float
    moneyness: float
    time_to_expiry: float
    price: float
    delta: Optional[float] = None

@dataclass
class VolatilitySurface:
    """Volatility surface representation."""
    timestamp: datetime
    underlying_price: float
    expiries: List[datetime]
    strikes: List[float]
    iv_matrix: np.ndarray
    term_structure: Dict[str, float]
    skew_parameters: Dict[str, float]
    surface_quality: Dict[str, float]

@dataclass
class VolatilityMetrics:
    """Comprehensive volatility metrics."""
    realized_vol_10d: float
    realized_vol_30d: float
    realized_vol_90d: float
    iv_rank_30d: float
    iv_percentile_30d: float
    vol_of_vol: float
    skew_slope: float
    term_structure_slope: float
    convexity: float
    vol_smile_curvature: float

class BlackScholesModel:
    """Black-Scholes model for option pricing and Greeks."""
    
    @staticmethod
    def calculate_d1_d2(S: float, K: float, T: float, r: float, sigma: float) -> Tuple[float, float]:
        """Calculate d1 and d2 parameters."""
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return d1, d2
    
    @staticmethod
    def option_price(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """Calculate theoretical option price."""
        from scipy.stats import norm
        
        if T <= 0:
            return max(0, S - K) if option_type.upper() == 'CE' else max(0, K - S)
        
        d1, d2 = BlackScholesModel.calculate_d1_d2(S, K, T, r, sigma)
        
        if option_type.upper() == 'CE':
            return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    @staticmethod
    def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate option vega."""
        from scipy.stats import norm
        
        if T <= 0:
            return 0
        
        d1, _ = BlackScholesModel.calculate_d1_d2(S, K, T, r, sigma)
        return S * np.sqrt(T) * norm.pdf(d1)
    
    @staticmethod
    def implied_volatility(market_price: float, S: float, K: float, T: float, r: float, option_type: str) -> float:
        """Calculate implied volatility using Newton-Raphson method."""
        if T <= 0:
            return 0
        
        # Initial guess
        sigma = 0.25
        
        for _ in range(100):  # Maximum iterations
            theoretical_price = BlackScholesModel.option_price(S, K, T, r, sigma, option_type)
            vega_value = BlackScholesModel.vega(S, K, T, r, sigma)
            
            if abs(vega_value) < 1e-10:
                break
            
            price_diff = theoretical_price - market_price
            
            if abs(price_diff) < 1e-6:
                break
            
            # Newton-Raphson update
            sigma = sigma - price_diff / vega_value
            
            # Ensure sigma stays positive
            sigma = max(0.001, min(5.0, sigma))
        
        return sigma

class VolatilityAnalyzer:
    """Main volatility analyzer class."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize volatility analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.risk_free_rate = config.get('risk_free_rate', 0.06)  # 6% default
        self.historical_data = {}
        self.iv_surfaces = {}
        self.cache = {}
        
        # Volatility model parameters
        self.hv_windows = config.get('hv_windows', [10, 20, 30, 60, 90])
        self.iv_smoothing = config.get('iv_smoothing', True)
        self.min_time_to_expiry = config.get('min_time_to_expiry', 7)  # days
        self.max_time_to_expiry = config.get('max_time_to_expiry', 365)  # days
    
    def analyze_volatility(self, market_data: Dict[str, Any], options_data: List[Dict]) -> VolatilityMetrics:
        """Perform comprehensive volatility analysis.
        
        Args:
            market_data: Current market data for underlying
            options_data: List of options data points
            
        Returns:
            VolatilityMetrics object with complete analysis
        """
        underlying_price = market_data.get('price', 0)
        
        # Calculate historical volatility
        hv_metrics = self._calculate_historical_volatility(market_data)
        
        # Build implied volatility surface
        iv_surface = self._build_iv_surface(underlying_price, options_data)
        
        # Calculate IV rank and percentile
        iv_rank, iv_percentile = self._calculate_iv_statistics(options_data)
        
        # Calculate volatility skew metrics
        skew_metrics = self._calculate_skew_metrics(iv_surface, underlying_price)
        
        # Calculate term structure metrics
        term_metrics = self._calculate_term_structure_metrics(iv_surface)
        
        # Calculate vol of vol
        vol_of_vol = self._calculate_vol_of_vol(options_data)
        
        return VolatilityMetrics(
            realized_vol_10d=hv_metrics.get('10d', 0),
            realized_vol_30d=hv_metrics.get('30d', 0),
            realized_vol_90d=hv_metrics.get('90d', 0),
            iv_rank_30d=iv_rank,
            iv_percentile_30d=iv_percentile,
            vol_of_vol=vol_of_vol,
            skew_slope=skew_metrics.get('slope', 0),
            term_structure_slope=term_metrics.get('slope', 0),
            convexity=skew_metrics.get('convexity', 0),
            vol_smile_curvature=skew_metrics.get('curvature', 0)
        )
    
    def _calculate_historical_volatility(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate historical volatility for different time windows.
        
        Args:
            market_data: Market data containing price history
            
        Returns:
            Dictionary mapping time windows to volatility values
        """
        hv_metrics = {}
        
        # Get historical prices (mock data for now)
        prices = self._get_historical_prices(market_data)
        
        if len(prices) < 10:
            # Return default values if insufficient data
            return {f'{window}d': 0.20 for window in self.hv_windows}
        
        # Calculate returns
        returns = np.diff(np.log(prices))
        
        for window in self.hv_windows:
            if len(returns) >= window:
                # Use last 'window' days
                window_returns = returns[-window:]
                
                # Calculate annualized volatility
                daily_vol = np.std(window_returns, ddof=1)
                annualized_vol = daily_vol * np.sqrt(252)  # 252 trading days
                
                hv_metrics[f'{window}d'] = annualized_vol
        
        return hv_metrics
    
    def _get_historical_prices(self, market_data: Dict[str, Any]) -> List[float]:
        """Get historical prices for volatility calculation.
        
        Args:
            market_data: Current market data
            
        Returns:
            List of historical prices
        """
        # Mock historical price generation
        current_price = market_data.get('price', 25000)
        
        # Generate synthetic historical prices with realistic volatility
        prices = []
        price = current_price
        
        for i in range(100):  # 100 days of history
            # Random daily return with mean reversion
            daily_return = np.random.normal(0.0005, 0.015)  # ~20% annual vol
            price = price * (1 + daily_return)
            prices.append(price)
        
        return list(reversed(prices))  # Chronological order
    
    def _build_iv_surface(self, underlying_price: float, options_data: List[Dict]) -> VolatilitySurface:
        """Build implied volatility surface from options data.
        
        Args:
            underlying_price: Current price of underlying
            options_data: List of options data points
            
        Returns:
            VolatilitySurface object
        """
        # Convert options data to volatility points
        vol_points = []
        
        for option in options_data:
            try:
                strike = float(option.get('strike', 0))
                price = float(option.get('last_price', 0))
                option_type = option.get('option_type', 'CE')
                
                # Calculate time to expiry (mock - use 30 days for now)
                time_to_expiry = 30 / 365.0
                
                # Calculate implied volatility
                if price > 0.01 and strike > 0:  # Valid option
                    iv = BlackScholesModel.implied_volatility(
                        price, underlying_price, strike, time_to_expiry, 
                        self.risk_free_rate, option_type
                    )
                    
                    moneyness = strike / underlying_price
                    
                    vol_points.append(VolatilityPoint(
                        strike=strike,
                        expiry=datetime.now() + timedelta(days=30),
                        option_type=option_type,
                        implied_vol=iv,
                        moneyness=moneyness,
                        time_to_expiry=time_to_expiry,
                        price=price
                    ))
                    
            except (ValueError, ZeroDivisionError, Exception):
                continue
        
        if not vol_points:
            # Return empty surface if no valid points
            return VolatilitySurface(
                timestamp=datetime.now(),
                underlying_price=underlying_price,
                expiries=[],
                strikes=[],
                iv_matrix=np.array([]),
                term_structure={},
                skew_parameters={},
                surface_quality={}
            )
        
        # Create surface structure
        expiries = list(set(point.expiry for point in vol_points))
        strikes = sorted(set(point.strike for point in vol_points))
        
        # Build IV matrix
        iv_matrix = np.zeros((len(expiries), len(strikes)))
        
        for i, expiry in enumerate(expiries):
            for j, strike in enumerate(strikes):
                # Find matching volatility point
                matching_points = [
                    p for p in vol_points 
                    if p.expiry == expiry and p.strike == strike
                ]
                
                if matching_points:
                    # Use average if multiple points
                    iv_matrix[i, j] = np.mean([p.implied_vol for p in matching_points])
                else:
                    # Interpolate or use NaN
                    iv_matrix[i, j] = np.nan
        
        # Calculate term structure
        term_structure = self._calculate_term_structure(vol_points, underlying_price)
        
        # Calculate skew parameters
        skew_parameters = self._calculate_skew_parameters(vol_points, underlying_price)
        
        # Assess surface quality
        surface_quality = self._assess_surface_quality(vol_points)
        
        return VolatilitySurface(
            timestamp=datetime.now(),
            underlying_price=underlying_price,
            expiries=expiries,
            strikes=strikes,
            iv_matrix=iv_matrix,
            term_structure=term_structure,
            skew_parameters=skew_parameters,
            surface_quality=surface_quality
        )
    
    def _calculate_term_structure(self, vol_points: List[VolatilityPoint], underlying_price: float) -> Dict[str, float]:
        """Calculate volatility term structure.
        
        Args:
            vol_points: List of volatility points
            underlying_price: Current underlying price
            
        Returns:
            Dictionary with term structure metrics
        """
        # Group points by expiry and filter ATM options
        atm_tolerance = 0.05  # 5% tolerance for ATM
        
        expiry_vols = {}
        
        for point in vol_points:
            moneyness = point.strike / underlying_price
            
            # Consider ATM options (within tolerance)
            if abs(moneyness - 1.0) <= atm_tolerance:
                expiry_key = point.time_to_expiry
                
                if expiry_key not in expiry_vols:
                    expiry_vols[expiry_key] = []
                
                expiry_vols[expiry_key].append(point.implied_vol)
        
        # Calculate average volatility for each expiry
        term_structure = {}
        
        for expiry, vols in expiry_vols.items():
            term_structure[f'{expiry:.3f}'] = np.mean(vols)
        
        return term_structure
    
    def _calculate_skew_parameters(self, vol_points: List[VolatilityPoint], underlying_price: float) -> Dict[str, float]:
        """Calculate volatility skew parameters.
        
        Args:
            vol_points: List of volatility points
            underlying_price: Current underlying price
            
        Returns:
            Dictionary with skew parameters
        """
        skew_params = {}
        
        # Filter points for same expiry (use nearest term for now)
        if not vol_points:
            return skew_params
        
        # Use points with same expiry (simplified - use all for now)
        strikes = [p.strike for p in vol_points]
        vols = [p.implied_vol for p in vol_points]
        moneyness_values = [p.moneyness for p in vol_points]
        
        if len(strikes) < 3:
            return skew_params
        
        try:
            # Calculate skew slope (regression of IV vs moneyness)
            slope, intercept = np.polyfit(moneyness_values, vols, 1)
            skew_params['slope'] = slope
            skew_params['intercept'] = intercept
            
            # Calculate ATM volatility
            atm_moneyness_idx = np.argmin(np.abs(np.array(moneyness_values) - 1.0))
            skew_params['atm_vol'] = vols[atm_moneyness_idx]
            
            # Calculate 25-delta skew (approximation)
            sorted_pairs = sorted(zip(moneyness_values, vols))
            n = len(sorted_pairs)
            
            if n >= 3:
                # 25-delta put approximation (75% moneyness)
                put_25d_idx = int(n * 0.25)
                # 25-delta call approximation (125% moneyness) 
                call_25d_idx = int(n * 0.75)
                
                put_25d_vol = sorted_pairs[put_25d_idx][1]
                call_25d_vol = sorted_pairs[call_25d_idx][1]
                
                skew_params['25d_skew'] = put_25d_vol - call_25d_vol
            
        except Exception:
            pass
        
        return skew_params
    
    def _assess_surface_quality(self, vol_points: List[VolatilityPoint]) -> Dict[str, float]:
        """Assess the quality of the volatility surface.
        
        Args:
            vol_points: List of volatility points
            
        Returns:
            Dictionary with quality metrics
        """
        quality_metrics = {}
        
        if not vol_points:
            return {'data_points': 0, 'quality_score': 0}
        
        # Number of data points
        quality_metrics['data_points'] = len(vol_points)
        
        # Moneyness coverage
        moneyness_values = [p.moneyness for p in vol_points]
        quality_metrics['moneyness_range'] = max(moneyness_values) - min(moneyness_values)
        
        # Volatility smoothness (measure of arbitrage-free surface)
        vols = [p.implied_vol for p in vol_points]
        vol_std = np.std(vols) if len(vols) > 1 else 0
        quality_metrics['vol_smoothness'] = 1.0 / (1.0 + vol_std)  # Inverse relationship
        
        # Price accuracy (how well options are priced)
        pricing_errors = []
        underlying_price = vol_points[0].strike / vol_points[0].moneyness  # Approximate
        
        for point in vol_points:
            try:
                theoretical_price = BlackScholesModel.option_price(
                    underlying_price, point.strike, point.time_to_expiry,
                    self.risk_free_rate, point.implied_vol, point.option_type
                )
                
                if theoretical_price > 0:
                    pricing_error = abs(theoretical_price - point.price) / theoretical_price
                    pricing_errors.append(pricing_error)
                    
            except Exception:
                continue
        
        if pricing_errors:
            quality_metrics['pricing_accuracy'] = 1.0 - np.mean(pricing_errors)
        
        # Overall quality score
        quality_score = 0
        weights = {'data_points': 0.3, 'moneyness_range': 0.3, 'vol_smoothness': 0.2, 'pricing_accuracy': 0.2}
        
        # Normalize and weight components
        if quality_metrics.get('data_points', 0) > 10:
            quality_score += weights['data_points']
        
        if quality_metrics.get('moneyness_range', 0) > 0.3:  # Good moneyness coverage
            quality_score += weights['moneyness_range']
        
        quality_score += weights['vol_smoothness'] * quality_metrics.get('vol_smoothness', 0)
        quality_score += weights['pricing_accuracy'] * quality_metrics.get('pricing_accuracy', 0)
        
        quality_metrics['quality_score'] = quality_score
        
        return quality_metrics
    
    def _calculate_iv_statistics(self, options_data: List[Dict]) -> Tuple[float, float]:
        """Calculate IV rank and percentile.
        
        Args:
            options_data: List of options data
            
        Returns:
            Tuple of (iv_rank, iv_percentile)
        """
        # Extract current IV values
        current_ivs = []
        
        for option in options_data:
            iv = option.get('iv')
            if iv and iv > 0:
                current_ivs.append(iv)
        
        if not current_ivs:
            return 0, 0
        
        current_avg_iv = np.mean(current_ivs)
        
        # Mock historical IV data for ranking
        # In real implementation, this would use historical IV database
        historical_ivs = self._get_historical_iv_data()
        
        if not historical_ivs:
            return 50, 50  # Default middle values
        
        # Calculate rank (percentage of time current IV is higher than historical)
        iv_rank = (np.sum(np.array(historical_ivs) < current_avg_iv) / len(historical_ivs)) * 100
        
        # Calculate percentile (current position in historical distribution)
        iv_percentile = (np.sum(np.array(historical_ivs) <= current_avg_iv) / len(historical_ivs)) * 100
        
        return iv_rank, iv_percentile
    
    def _get_historical_iv_data(self) -> List[float]:
        """Get historical IV data for ranking calculations.
        
        Returns:
            List of historical IV values
        """
        # Mock historical IV data generation
        # In real implementation, this would query historical database
        
        # Generate 252 days of historical IV (1 year)
        historical_ivs = []
        base_iv = 0.20
        
        for _ in range(252):
            # Add some random variation to create realistic IV history
            iv = base_iv + np.random.normal(0, 0.05)
            iv = max(0.05, min(0.60, iv))  # Clamp between 5% and 60%
            historical_ivs.append(iv)
            
            # Add some mean reversion
            base_iv = 0.9 * base_iv + 0.1 * iv
        
        return historical_ivs
    
    def _calculate_skew_metrics(self, iv_surface: VolatilitySurface, underlying_price: float) -> Dict[str, float]:
        """Calculate volatility skew metrics.
        
        Args:
            iv_surface: Volatility surface object
            underlying_price: Current underlying price
            
        Returns:
            Dictionary with skew metrics
        """
        return iv_surface.skew_parameters
    
    def _calculate_term_structure_metrics(self, iv_surface: VolatilitySurface) -> Dict[str, float]:
        """Calculate term structure metrics.
        
        Args:
            iv_surface: Volatility surface object
            
        Returns:
            Dictionary with term structure metrics
        """
        term_metrics = {}
        
        if len(iv_surface.term_structure) < 2:
            return {'slope': 0}
        
        # Extract time and volatility values
        times = []
        vols = []
        
        for time_key, vol in iv_surface.term_structure.items():
            try:
                time_val = float(time_key)
                times.append(time_val)
                vols.append(vol)
            except ValueError:
                continue
        
        if len(times) >= 2:
            # Calculate term structure slope
            slope, _ = np.polyfit(times, vols, 1)
            term_metrics['slope'] = slope
            
            # Calculate term structure curvature (if enough points)
            if len(times) >= 3:
                # Fit quadratic and get curvature
                coeffs = np.polyfit(times, vols, 2)
                term_metrics['curvature'] = 2 * coeffs[0]  # Second derivative
        
        return term_metrics
    
    def _calculate_vol_of_vol(self, options_data: List[Dict]) -> float:
        """Calculate volatility of volatility.
        
        Args:
            options_data: List of options data
            
        Returns:
            Vol of vol metric
        """
        # Extract IV values
        iv_values = []
        
        for option in options_data:
            iv = option.get('iv')
            if iv and iv > 0:
                iv_values.append(iv)
        
        if len(iv_values) < 2:
            return 0
        
        # Calculate standard deviation of IV values
        vol_of_vol = np.std(iv_values)
        
        return vol_of_vol
    
    def forecast_volatility(self, historical_data: List[float], forecast_days: int = 30) -> Dict[str, float]:
        """Forecast future volatility using simple models.
        
        Args:
            historical_data: Historical price data
            forecast_days: Number of days to forecast
            
        Returns:
            Dictionary with forecast results
        """
        if len(historical_data) < 30:
            return {'forecast_vol': 0.20, 'confidence': 0}
        
        # Calculate historical returns
        returns = np.diff(np.log(historical_data))
        
        # Simple EWMA (Exponentially Weighted Moving Average) forecast
        decay_factor = 0.94
        weights = np.array([decay_factor ** i for i in range(len(returns))])
        weights = weights[::-1] / np.sum(weights)
        
        ewma_variance = np.sum(weights * returns ** 2)
        ewma_vol = np.sqrt(ewma_variance * 252)  # Annualized
        
        # Simple GARCH(1,1) approximation
        long_run_var = np.var(returns)
        alpha = 0.1  # Simplified parameters
        beta = 0.85
        
        garch_variance = long_run_var * (1 - alpha - beta) + alpha * returns[-1] ** 2 + beta * long_run_var
        garch_vol = np.sqrt(garch_variance * 252)
        
        # Combine forecasts
        forecast_vol = 0.6 * ewma_vol + 0.4 * garch_vol
        
        # Calculate confidence based on data quality
        confidence = min(100, len(historical_data) / 252 * 100)  # Higher confidence with more data
        
        return {
            'forecast_vol': forecast_vol,
            'ewma_vol': ewma_vol,
            'garch_vol': garch_vol,
            'confidence': confidence,
            'forecast_horizon_days': forecast_days
        }
    
    def calculate_risk_neutral_density(self, iv_surface: VolatilitySurface, expiry_days: int = 30) -> Dict[str, Any]:
        """Calculate risk-neutral probability density from options prices.
        
        Args:
            iv_surface: Volatility surface
            expiry_days: Days to expiry for calculation
            
        Returns:
            Dictionary with density calculation results
        """
        if iv_surface.iv_matrix.size == 0:
            return {'strikes': [], 'probabilities': [], 'mean': 0, 'std': 0}
        
        # Simplified risk-neutral density calculation
        # In practice, this would use more sophisticated methods
        
        underlying_price = iv_surface.underlying_price
        time_to_expiry = expiry_days / 365.0
        
        # Generate strike range around current price
        strike_range = np.linspace(
            underlying_price * 0.8, 
            underlying_price * 1.2, 
            50
        )
        
        # Calculate option prices for each strike
        call_prices = []
        
        for strike in strike_range:
            # Use interpolated IV from surface (simplified)
            moneyness = strike / underlying_price
            
            if 0.8 <= moneyness <= 1.2:
                # Linear interpolation for IV
                iv = 0.20 + (moneyness - 1.0) * -0.10  # Simple skew approximation
            else:
                iv = 0.20
            
            call_price = BlackScholesModel.option_price(
                underlying_price, strike, time_to_expiry, 
                self.risk_free_rate, iv, 'CE'
            )
            call_prices.append(call_price)
        
        # Numerical differentiation to get density
        # d²C/dK² approximates risk-neutral density
        
        strike_step = strike_range[1] - strike_range[0]
        densities = []
        
        for i in range(1, len(call_prices) - 1):
            # Second derivative approximation
            second_derivative = (call_prices[i+1] - 2*call_prices[i] + call_prices[i-1]) / (strike_step ** 2)
            density = second_derivative * np.exp(self.risk_free_rate * time_to_expiry)
            densities.append(max(0, density))  # Ensure non-negative
        
        # Adjust strike range for density points
        density_strikes = strike_range[1:-1]
        
        # Normalize to probability distribution
        if sum(densities) > 0:
            total_prob = sum(densities) * strike_step
            probabilities = [d / total_prob for d in densities]
        else:
            probabilities = [0] * len(densities)
        
        # Calculate moments
        if sum(probabilities) > 0:
            mean_price = sum(s * p * strike_step for s, p in zip(density_strikes, probabilities))
            variance = sum((s - mean_price) ** 2 * p * strike_step for s, p in zip(density_strikes, probabilities))
            std_dev = np.sqrt(variance)
        else:
            mean_price = underlying_price
            std_dev = 0
        
        return {
            'strikes': density_strikes.tolist(),
            'probabilities': probabilities,
            'mean': mean_price,
            'std': std_dev,
            'skewness': 0,  # Could calculate higher moments
            'kurtosis': 0
        }

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        'risk_free_rate': 0.06,
        'hv_windows': [10, 20, 30, 60, 90],
        'iv_smoothing': True,
        'cache_ttl': 300
    }
    
    # Initialize analyzer
    analyzer = VolatilityAnalyzer(config)
    
    # Example market data
    market_data = {
        'price': 24975,
        'volume': 450000,
        'symbol': 'NIFTY'
    }
    
    # Example options data
    options_data = [
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
        }
    ]
    
    # Perform analysis
    vol_metrics = analyzer.analyze_volatility(market_data, options_data)
    
    print("Volatility Analysis Results:")
    print(f"30-day Realized Vol: {vol_metrics.realized_vol_30d:.3f}")
    print(f"IV Rank: {vol_metrics.iv_rank_30d:.1f}")
    print(f"Skew Slope: {vol_metrics.skew_slope:.4f}")
    print(f"Vol of Vol: {vol_metrics.vol_of_vol:.4f}")
    
    # Build volatility surface
    iv_surface = analyzer._build_iv_surface(market_data['price'], options_data)
    print(f"Surface Quality Score: {iv_surface.surface_quality.get('quality_score', 0):.2f}")