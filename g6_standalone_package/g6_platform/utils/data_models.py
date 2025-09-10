#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏗️ Complete Data Models for G6.1 Platform
Author: AI Assistant (Comprehensive data models with validation)

✅ Features:
- Complete option data models with validation
- Instrument models with metadata
- Market data structures
- Analytics result models
- Health and metrics models
- Serialization and deserialization
- Data type validation and conversion
- Model relationships and dependencies
"""

import logging
import datetime
from typing import Dict, List, Any, Optional, Union, Literal
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

# 📊 AI Assistant: Enumerations for type safety
class OptionType(Enum):
    """🎯 Option type enumeration."""
    CALL = "CE"
    PUT = "PE"
    
    def __str__(self):
        return self.value

class InstrumentType(Enum):
    """📊 Instrument type enumeration."""
    EQUITY = "EQ"
    FUTURES = "FUT" 
    OPTION = "OPT"
    INDEX = "IDX"
    COMMODITY = "COM"

class MarketStatus(Enum):
    """🕒 Market status enumeration."""
    OPEN = "open"
    CLOSED = "closed"
    PRE_OPEN = "pre_open"
    POST_CLOSE = "post_close"

class DataQuality(Enum):
    """🧪 Data quality levels."""
    EXCELLENT = "excellent"  # 0.9+
    GOOD = "good"           # 0.7-0.9
    FAIR = "fair"           # 0.5-0.7
    POOR = "poor"           # <0.5

@dataclass
class BaseModel:
    """🏗️ Base model with common functionality."""
    
    def to_dict(self) -> Dict[str, Any]:
        """📊 Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """📄 Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """🔄 Create instance from dictionary."""
        try:
            # Filter unknown fields
            valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in data.items() if k in valid_fields}
            return cls(**filtered_data)
        except Exception as e:
            logger.warning(f"⚠️ Error creating {cls.__name__} from dict: {e}")
            return None

@dataclass
class Instrument(BaseModel):
    """📊 Complete instrument model."""
    
    # 🆔 Core identification
    instrument_token: int
    exchange_token: int = 0
    tradingsymbol: str = ""
    name: str = ""
    
    # 🏢 Exchange and segment
    exchange: str = ""
    segment: str = ""
    
    # 📊 Instrument details
    instrument_type: str = ""
    lot_size: int = 1
    tick_size: float = 0.05
    
    # 🎯 Option-specific fields
    strike: Optional[float] = None
    expiry: Optional[Union[str, datetime.date]] = None
    
    # 💰 Market data
    last_price: float = 0.0
    
    # 🏷️ Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # ⏰ Timestamps
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    def __post_init__(self):
        """🔧 Post-initialization validation."""
        if self.instrument_token <= 0:
            raise ValueError("instrument_token must be positive")
        
        if not self.tradingsymbol:
            raise ValueError("tradingsymbol is required")
        
        # 📅 Normalize expiry to string
        if isinstance(self.expiry, datetime.date):
            self.expiry = self.expiry.strftime('%Y-%m-%d')
    
    @property
    def is_option(self) -> bool:
        """🎯 Check if instrument is an option."""
        return self.instrument_type in ['CE', 'PE'] or 'OPT' in self.segment
    
    @property
    def is_call(self) -> bool:
        """📈 Check if instrument is a call option."""
        return self.instrument_type == 'CE'
    
    @property
    def is_put(self) -> bool:
        """📉 Check if instrument is a put option."""
        return self.instrument_type == 'PE'
    
    @property
    def moneyness(self) -> Optional[str]:
        """💰 Calculate moneyness if option."""
        if not self.is_option or not self.strike or self.last_price <= 0:
            return None
        
        if self.is_call:
            if self.last_price > self.strike:
                return "ITM"
            elif abs(self.last_price - self.strike) < self.strike * 0.02:
                return "ATM"
            else:
                return "OTM"
        else:  # PUT
            if self.last_price < self.strike:
                return "ITM"
            elif abs(self.last_price - self.strike) < self.strike * 0.02:
                return "ATM"
            else:
                return "OTM"

@dataclass 
class MarketData(BaseModel):
    """📊 Complete market data model."""
    
    # 🆔 Identification
    instrument_token: int
    tradingsymbol: str
    exchange: str
    
    # 💰 Price data
    last_price: float
    last_quantity: int = 0
    average_price: float = 0.0
    
    # 📊 OHLC data
    ohlc: Dict[str, float] = field(default_factory=lambda: {
        'open': 0.0, 'high': 0.0, 'low': 0.0, 'close': 0.0
    })
    
    # 📈 Volume and turnover
    volume: int = 0
    volume_traded: float = 0.0
    
    # 🎯 Option-specific data
    oi: int = 0
    oi_day_high: int = 0
    oi_day_low: int = 0
    
    # 📊 Market depth
    depth: Dict[str, List[Dict[str, Any]]] = field(default_factory=lambda: {
        'buy': [], 'sell': []
    })
    
    # ⏰ Timestamp
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    # 🧪 Data quality
    data_quality_score: float = 1.0
    data_source: str = "live"
    
    def __post_init__(self):
        """🔧 Validation and normalization."""
        if self.instrument_token <= 0:
            raise ValueError("instrument_token must be positive")
        
        if self.last_price < 0:
            self.last_price = 0.0
        
        if self.volume < 0:
            self.volume = 0
        
        if self.oi < 0:
            self.oi = 0
    
    @property
    def bid_price(self) -> float:
        """💰 Get best bid price."""
        try:
            buy_orders = self.depth.get('buy', [])
            return buy_orders[0]['price'] if buy_orders else 0.0
        except (IndexError, KeyError, TypeError):
            return 0.0
    
    @property
    def ask_price(self) -> float:
        """💰 Get best ask price."""
        try:
            sell_orders = self.depth.get('sell', [])
            return sell_orders[0]['price'] if sell_orders else 0.0
        except (IndexError, KeyError, TypeError):
            return 0.0
    
    @property
    def spread(self) -> float:
        """📊 Calculate bid-ask spread."""
        bid = self.bid_price
        ask = self.ask_price
        return ask - bid if bid > 0 and ask > 0 else 0.0
    
    @property
    def spread_percentage(self) -> float:
        """📊 Calculate spread as percentage."""
        mid_price = (self.bid_price + self.ask_price) / 2
        return (self.spread / mid_price * 100) if mid_price > 0 else 0.0

@dataclass
class OptionChainData(BaseModel):
    """🎯 Complete option chain model."""
    
    # 🆔 Identification
    underlying_symbol: str
    underlying_price: float
    atm_strike: float
    
    # 📅 Expiry information
    expiry_date: str
    expiry_tag: str  # 'this_week', 'next_week', etc.
    days_to_expiry: int
    
    # 📊 Option data
    call_options: List[MarketData] = field(default_factory=list)
    put_options: List[MarketData] = field(default_factory=list)
    
    # 📈 Analytics
    total_call_volume: int = 0
    total_put_volume: int = 0
    total_call_oi: int = 0
    total_put_oi: int = 0
    
    pcr_volume: float = 0.0
    pcr_oi: float = 0.0
    
    # ⏰ Collection metadata
    collection_timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    collection_time_ms: float = 0.0
    data_quality_score: float = 1.0
    
    def __post_init__(self):
        """🔧 Calculate derived metrics."""
        self._calculate_aggregates()
    
    def _calculate_aggregates(self):
        """📊 Calculate aggregate metrics."""
        # 📈 Volume aggregates
        self.total_call_volume = sum(opt.volume for opt in self.call_options)
        self.total_put_volume = sum(opt.volume for opt in self.put_options)
        
        # 📊 OI aggregates
        self.total_call_oi = sum(opt.oi for opt in self.call_options)
        self.total_put_oi = sum(opt.oi for opt in self.put_options)
        
        # 📈 PCR calculations
        self.pcr_volume = (self.total_put_volume / self.total_call_volume 
                          if self.total_call_volume > 0 else 0.0)
        self.pcr_oi = (self.total_put_oi / self.total_call_oi 
                      if self.total_call_oi > 0 else 0.0)
    
    def get_option_by_strike(self, strike: float, option_type: str) -> Optional[MarketData]:
        """🎯 Find option by strike and type."""
        options = self.call_options if option_type.upper() == 'CE' else self.put_options
        
        for option in options:
            # Assuming strike is stored in metadata or can be derived from tradingsymbol
            if abs(option.metadata.get('strike', 0) - strike) < 0.01:
                return option
        
        return None
    
    def get_options_by_moneyness(self, moneyness: str, option_type: str) -> List[MarketData]:
        """💰 Get options by moneyness (ITM, ATM, OTM)."""
        options = self.call_options if option_type.upper() == 'CE' else self.put_options
        result = []
        
        for option in options:
            strike = option.metadata.get('strike', 0)
            if not strike:
                continue
            
            # Calculate moneyness
            if option_type.upper() == 'CE':
                is_itm = self.underlying_price > strike
                is_atm = abs(self.underlying_price - strike) < strike * 0.02
            else:  # PE
                is_itm = self.underlying_price < strike
                is_atm = abs(self.underlying_price - strike) < strike * 0.02
            
            if moneyness.upper() == 'ITM' and is_itm and not is_atm:
                result.append(option)
            elif moneyness.upper() == 'ATM' and is_atm:
                result.append(option)
            elif moneyness.upper() == 'OTM' and not is_itm and not is_atm:
                result.append(option)
        
        return result

@dataclass
class Greeks(BaseModel):
    """🧮 Option Greeks model."""
    
    # 🆔 Identification
    instrument_token: int
    tradingsymbol: str
    strike: float
    option_type: str
    
    # 🧮 Greek values
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    rho: float = 0.0
    
    # 📊 Volatility and pricing
    implied_volatility: float = 0.0
    theoretical_price: float = 0.0
    intrinsic_value: float = 0.0
    time_value: float = 0.0
    
    # 🎯 Market parameters used in calculation
    underlying_price: float = 0.0
    risk_free_rate: float = 0.06
    dividend_yield: float = 0.0
    time_to_expiry: float = 0.0
    
    # ⏰ Calculation metadata
    calculation_timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    calculation_method: str = "black_scholes"
    
    def __post_init__(self):
        """🔧 Calculate derived values."""
        self._calculate_intrinsic_time_value()
    
    def _calculate_intrinsic_time_value(self):
        """💰 Calculate intrinsic and time value."""
        if self.underlying_price > 0 and self.strike > 0:
            if self.option_type.upper() == 'CE':
                self.intrinsic_value = max(0, self.underlying_price - self.strike)
            else:  # PE
                self.intrinsic_value = max(0, self.strike - self.underlying_price)
            
            # Time value = Market Price - Intrinsic Value
            # (would need market price from elsewhere)
            self.time_value = max(0, self.theoretical_price - self.intrinsic_value)

@dataclass
class AnalyticsResult(BaseModel):
    """📊 Analytics calculation result model."""
    
    # 🆔 Identification
    analysis_id: str
    analysis_type: str  # 'iv_calculation', 'pcr_analysis', 'greeks', etc.
    underlying_symbol: str
    
    # 📊 Result data
    result_data: Dict[str, Any] = field(default_factory=dict)
    
    # 📈 Metrics
    success: bool = True
    confidence_score: float = 1.0
    data_quality_score: float = 1.0
    
    # 🔄 Processing info
    processing_time_ms: float = 0.0
    input_records_count: int = 0
    output_records_count: int = 0
    
    # ❌ Error information
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # ⏰ Timestamps
    started_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    completed_at: str = ""
    
    def mark_completed(self):
        """✅ Mark analysis as completed."""
        self.completed_at = datetime.datetime.now().isoformat()
    
    def add_error(self, error: str):
        """❌ Add error and mark as failed."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str):
        """⚠️ Add warning."""
        self.warnings.append(warning)

@dataclass
class HealthStatus(BaseModel):
    """❤️ Health status model."""
    
    # 🆔 Component identification
    component_name: str
    component_type: str  # 'collector', 'provider', 'storage', 'analytics'
    
    # ❤️ Health status
    status: str  # 'healthy', 'degraded', 'unhealthy'
    health_score: float = 1.0  # 0.0 to 1.0
    
    # 📊 Detailed metrics
    uptime_seconds: float = 0.0
    last_activity: str = ""
    
    # 📈 Performance metrics
    success_rate: float = 1.0
    error_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    
    # 💾 Resource usage (optional)
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    
    # 🔍 Specific checks
    checks_passed: int = 0
    total_checks: int = 0
    failed_checks: List[str] = field(default_factory=list)
    
    # ⏰ Timestamps
    check_timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    last_healthy_time: str = ""
    
    @property
    def is_healthy(self) -> bool:
        """❤️ Check if component is healthy."""
        return self.status == 'healthy' and self.health_score >= 0.8
    
    @property
    def check_success_rate(self) -> float:
        """📊 Calculate check success rate."""
        return self.checks_passed / self.total_checks if self.total_checks > 0 else 1.0

@dataclass
class MetricsData(BaseModel):
    """📊 Metrics data model."""
    
    # 🆔 Identification
    metric_name: str
    metric_type: str  # 'counter', 'gauge', 'histogram', 'timing'
    component: str
    
    # 📊 Metric value(s)
    value: Union[float, int] = 0
    tags: Dict[str, str] = field(default_factory=dict)
    
    # 📈 Additional data for histograms/timings
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None
    count: int = 1
    
    # ⏰ Timing
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    time_window: str = "1m"  # 1m, 5m, 15m, 1h, etc.
    
    def __post_init__(self):
        """🔧 Validation."""
        if not self.metric_name:
            raise ValueError("metric_name is required")
        
        if self.metric_type not in ['counter', 'gauge', 'histogram', 'timing']:
            raise ValueError(f"Invalid metric_type: {self.metric_type}")

@dataclass
class CollectionMetadata(BaseModel):
    """📋 Collection metadata model."""
    
    # 🆔 Collection identification
    collection_id: str
    index_name: str
    collection_type: str  # 'atm_options', 'overview', 'full_chain'
    
    # ⏰ Timing information
    started_at: str
    completed_at: str = ""
    duration_ms: float = 0.0
    
    # 📊 Collection statistics
    total_instruments_requested: int = 0
    total_instruments_collected: int = 0
    total_quotes_requested: int = 0
    total_quotes_received: int = 0
    
    # 🧪 Quality metrics
    data_quality_score: float = 1.0
    completeness_percentage: float = 100.0
    
    # ❌ Error tracking
    errors_encountered: List[str] = field(default_factory=list)
    warnings_encountered: List[str] = field(default_factory=list)
    
    # 📈 Performance metrics
    api_calls_made: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def mark_completed(self):
        """✅ Mark collection as completed."""
        if not self.completed_at:
            self.completed_at = datetime.datetime.now().isoformat()
            
            # Calculate duration if started_at is available
            if self.started_at:
                try:
                    start_time = datetime.datetime.fromisoformat(self.started_at)
                    end_time = datetime.datetime.fromisoformat(self.completed_at)
                    self.duration_ms = (end_time - start_time).total_seconds() * 1000
                except Exception:
                    pass
    
    @property
    def success_rate(self) -> float:
        """📊 Calculate collection success rate."""
        if self.total_instruments_requested == 0:
            return 1.0
        return self.total_instruments_collected / self.total_instruments_requested
    
    @property
    def quote_success_rate(self) -> float:
        """📊 Calculate quote success rate."""
        if self.total_quotes_requested == 0:
            return 1.0
        return self.total_quotes_received / self.total_quotes_requested

# 🧪 AI Assistant: Model validation utilities
class ModelValidator:
    """🧪 Utility class for model validation."""
    
    @staticmethod
    def validate_instrument(instrument: Instrument) -> List[str]:
        """🔍 Validate instrument model."""
        issues = []
        
        if instrument.instrument_token <= 0:
            issues.append("instrument_token must be positive")
        
        if not instrument.tradingsymbol:
            issues.append("tradingsymbol is required")
        
        if instrument.lot_size <= 0:
            issues.append("lot_size must be positive")
        
        if instrument.tick_size <= 0:
            issues.append("tick_size must be positive")
        
        if instrument.is_option:
            if not instrument.strike or instrument.strike <= 0:
                issues.append("options must have positive strike price")
            
            if not instrument.expiry:
                issues.append("options must have expiry date")
        
        return issues
    
    @staticmethod
    def validate_market_data(market_data: MarketData) -> List[str]:
        """🔍 Validate market data model."""
        issues = []
        
        if market_data.instrument_token <= 0:
            issues.append("instrument_token must be positive")
        
        if market_data.last_price < 0:
            issues.append("last_price cannot be negative")
        
        if market_data.volume < 0:
            issues.append("volume cannot be negative")
        
        if market_data.oi < 0:
            issues.append("oi cannot be negative")
        
        # Validate OHLC consistency
        ohlc = market_data.ohlc
        if ohlc.get('high', 0) < ohlc.get('low', 0):
            issues.append("high cannot be less than low")
        
        return issues

# 🧪 AI Assistant: Testing functions
def test_data_models():
    """🧪 Test all data models."""
    print("🧪 Testing Data Models...")
    
    try:
        # 📊 Test Instrument model
        instrument = Instrument(
            instrument_token=12345,
            tradingsymbol="NIFTY25SEP24800CE",
            name="NIFTY",
            exchange="NFO",
            segment="NFO-OPT",
            instrument_type="CE",
            strike=24800,
            expiry="2025-09-25",
            lot_size=50
        )
        print(f"✅ Instrument created: {instrument.tradingsymbol} (is_option: {instrument.is_option})")
        
        # 📊 Test MarketData model
        market_data = MarketData(
            instrument_token=12345,
            tradingsymbol="NIFTY25SEP24800CE",
            exchange="NFO",
            last_price=125.50,
            volume=100000,
            oi=50000,
            ohlc={'open': 120.0, 'high': 130.0, 'low': 118.0, 'close': 125.50}
        )
        print(f"✅ MarketData created: {market_data.tradingsymbol} @ {market_data.last_price}")
        
        # 📊 Test Greeks model
        greeks = Greeks(
            instrument_token=12345,
            tradingsymbol="NIFTY25SEP24800CE",
            strike=24800,
            option_type="CE",
            delta=0.52,
            gamma=0.015,
            theta=-0.85,
            underlying_price=24825
        )
        print(f"✅ Greeks created: Delta={greeks.delta}, Intrinsic={greeks.intrinsic_value}")
        
        # 🧪 Test validation
        validator = ModelValidator()
        issues = validator.validate_instrument(instrument)
        print(f"✅ Instrument validation: {len(issues)} issues found")
        
        issues = validator.validate_market_data(market_data)
        print(f"✅ MarketData validation: {len(issues)} issues found")
        
        # 📄 Test serialization
        instrument_dict = instrument.to_dict()
        instrument_json = instrument.to_json()
        print(f"✅ Serialization: dict has {len(instrument_dict)} fields")
        
        # 🔄 Test deserialization
        recreated_instrument = Instrument.from_dict(instrument_dict)
        if recreated_instrument:
            print("✅ Deserialization successful")
        else:
            print("🔴 Deserialization failed")
        
        print("🎉 Data Models test completed!")
        return True
        
    except Exception as e:
        print(f"🔴 Data Models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_data_models()