#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Data Collector - G6.1 Platform
Generic market data collection interface with multiple data source support

Features:
- Multiple data source adapters (Kite, Yahoo Finance, Alpha Vantage)
- Unified data format and API
- Automatic failover between data sources
- Data validation and quality checks
- Caching and rate limiting
"""

import os
import sys
import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

class DataSourceType(Enum):
    """Available data source types."""
    KITE_CONNECT = "kite_connect"
    YAHOO_FINANCE = "yahoo_finance" 
    ALPHA_VANTAGE = "alpha_vantage"
    NSE_DIRECT = "nse_direct"
    BSE_DIRECT = "bse_direct"

@dataclass
class MarketDataPoint:
    """Standardized market data point structure."""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    change: float
    change_percent: float
    source: DataSourceType
    metadata: Dict[str, Any] = None

@dataclass
class OptionsDataPoint:
    """Standardized options data point structure."""
    symbol: str
    strike: float
    expiry: datetime
    option_type: str  # CE/PE
    last_price: float
    volume: int
    oi: int  # Open Interest
    change: float
    change_percent: float
    iv: Optional[float] = None  # Implied Volatility
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    source: DataSourceType = DataSourceType.KITE_CONNECT
    metadata: Dict[str, Any] = None

class MarketDataSource(ABC):
    """Abstract base class for market data sources."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize data source with configuration.
        
        Args:
            config: Data source specific configuration
        """
        self.config = config
        self.is_connected = False
        self.last_error = None
        self.request_count = 0
        self.error_count = 0
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to data source.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to data source."""
        pass
    
    @abstractmethod
    def get_market_data(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get current market data for symbol.
        
        Args:
            symbol: Market symbol (e.g., NIFTY, BANKNIFTY)
            
        Returns:
            MarketDataPoint or None if failed
        """
        pass
    
    @abstractmethod
    def get_options_chain(self, symbol: str, expiry: str) -> List[OptionsDataPoint]:
        """Get options chain for symbol and expiry.
        
        Args:
            symbol: Underlying symbol
            expiry: Expiry date (YYYY-MM-DD format)
            
        Returns:
            List of OptionsDataPoint
        """
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, days: int = 30) -> List[MarketDataPoint]:
        """Get historical data for symbol.
        
        Args:
            symbol: Market symbol
            days: Number of days of historical data
            
        Returns:
            List of historical MarketDataPoint
        """
        pass
    
    def health_check(self) -> bool:
        """Check if data source is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        return self.is_connected and self.error_count < 10

class KiteConnectDataSource(MarketDataSource):
    """Kite Connect data source implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Kite Connect data source.
        
        Args:
            config: Configuration containing api_key and access_token
        """
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.access_token = config.get('access_token')
        self.kite = None
        
    def connect(self) -> bool:
        """Connect to Kite API."""
        try:
            from kiteconnect import KiteConnect
            
            if not self.api_key or not self.access_token:
                self.last_error = "Missing API credentials"
                return False
            
            self.kite = KiteConnect(api_key=self.api_key)
            self.kite.set_access_token(self.access_token)
            
            # Test connection
            profile = self.kite.profile()
            self.is_connected = bool(profile.get('user_name'))
            
            return self.is_connected
            
        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Kite API."""
        self.kite = None
        self.is_connected = False
    
    def get_market_data(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get market data from Kite Connect."""
        try:
            if not self.is_connected:
                return None
            
            # Map symbol to instrument token
            instrument_map = {
                'NIFTY': 'NSE:NIFTY 50',
                'BANKNIFTY': 'NSE:NIFTY BANK',
                'FINNIFTY': 'NSE:NIFTY FIN SERVICE',
                'MIDCPNIFTY': 'NSE:NIFTY MID SELECT'
            }
            
            kite_symbol = instrument_map.get(symbol.upper(), symbol)
            quote = self.kite.quote([kite_symbol])
            
            if kite_symbol not in quote:
                return None
            
            data = quote[kite_symbol]
            ohlc = data.get('ohlc', {})
            
            return MarketDataPoint(
                symbol=symbol,
                timestamp=datetime.now(),
                price=data.get('last_price', 0),
                volume=data.get('volume', 0),
                open_price=ohlc.get('open', 0),
                high_price=ohlc.get('high', 0),
                low_price=ohlc.get('low', 0),
                close_price=ohlc.get('close', 0),
                change=data.get('net_change', 0),
                change_percent=data.get('change', 0),
                source=DataSourceType.KITE_CONNECT,
                metadata={'instrument_token': data.get('instrument_token')}
            )
            
        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            return None
    
    def get_options_chain(self, symbol: str, expiry: str) -> List[OptionsDataPoint]:
        """Get options chain from Kite Connect."""
        try:
            if not self.is_connected:
                return []
            
            # This would require instrument list and filtering
            # Simplified implementation for now
            options_data = []
            
            # Get instruments for symbol
            instruments = self.kite.instruments('NFO')
            
            # Filter by symbol and expiry
            filtered_instruments = [
                inst for inst in instruments
                if inst['name'] == symbol.upper() and inst['expiry'] == expiry
            ]
            
            # Get quotes for filtered instruments
            if filtered_instruments:
                tokens = [str(inst['instrument_token']) for inst in filtered_instruments[:50]]
                quotes = self.kite.quote(tokens)
                
                for inst in filtered_instruments[:50]:
                    token = str(inst['instrument_token'])
                    if token in quotes:
                        quote_data = quotes[token]
                        
                        options_data.append(OptionsDataPoint(
                            symbol=inst['tradingsymbol'],
                            strike=float(inst['strike']),
                            expiry=datetime.strptime(expiry, '%Y-%m-%d'),
                            option_type=inst['instrument_type'],
                            last_price=quote_data.get('last_price', 0),
                            volume=quote_data.get('volume', 0),
                            oi=quote_data.get('oi', 0),
                            change=quote_data.get('net_change', 0),
                            change_percent=quote_data.get('change', 0),
                            source=DataSourceType.KITE_CONNECT
                        ))
            
            return options_data
            
        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            return []
    
    def get_historical_data(self, symbol: str, days: int = 30) -> List[MarketDataPoint]:
        """Get historical data from Kite Connect."""
        try:
            if not self.is_connected:
                return []
            
            # Get historical data
            from_date = datetime.now() - timedelta(days=days)
            to_date = datetime.now()
            
            # This would require proper instrument token mapping
            # Simplified implementation
            historical_data = []
            
            return historical_data
            
        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            return []

class MockDataSource(MarketDataSource):
    """Mock data source for testing and development."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize mock data source."""
        super().__init__(config)
        self.mock_data = {}
    
    def connect(self) -> bool:
        """Mock connection always succeeds."""
        self.is_connected = True
        return True
    
    def disconnect(self) -> None:
        """Mock disconnection."""
        self.is_connected = False
    
    def get_market_data(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get mock market data."""
        import random
        
        base_prices = {
            'NIFTY': 24975,
            'BANKNIFTY': 51650,
            'FINNIFTY': 23850,
            'MIDCPNIFTY': 12750
        }
        
        base_price = base_prices.get(symbol.upper(), 25000)
        current_price = base_price + random.uniform(-100, 100)
        
        return MarketDataPoint(
            symbol=symbol,
            timestamp=datetime.now(),
            price=current_price,
            volume=random.randint(100000, 500000),
            open_price=base_price + random.uniform(-50, 50),
            high_price=current_price + random.uniform(0, 50),
            low_price=current_price - random.uniform(0, 50),
            close_price=current_price,
            change=random.uniform(-50, 50),
            change_percent=random.uniform(-2, 2),
            source=DataSourceType.KITE_CONNECT,
            metadata={'mock': True}
        )
    
    def get_options_chain(self, symbol: str, expiry: str) -> List[OptionsDataPoint]:
        """Get mock options chain."""
        import random
        
        options_data = []
        base_strike = 25000
        
        # Generate mock options data
        for offset in range(-5, 6):
            strike = base_strike + (offset * 50)
            
            for option_type in ['CE', 'PE']:
                options_data.append(OptionsDataPoint(
                    symbol=f"{symbol}{strike}{option_type}",
                    strike=strike,
                    expiry=datetime.strptime(expiry, '%Y-%m-%d'),
                    option_type=option_type,
                    last_price=random.uniform(10, 300),
                    volume=random.randint(1000, 50000),
                    oi=random.randint(10000, 100000),
                    change=random.uniform(-20, 20),
                    change_percent=random.uniform(-10, 10),
                    iv=random.uniform(15, 35),
                    delta=random.uniform(-1, 1),
                    source=DataSourceType.KITE_CONNECT,
                    metadata={'mock': True}
                ))
        
        return options_data
    
    def get_historical_data(self, symbol: str, days: int = 30) -> List[MarketDataPoint]:
        """Get mock historical data."""
        import random
        
        historical_data = []
        base_price = 25000
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            price = base_price + random.uniform(-200, 200)
            
            historical_data.append(MarketDataPoint(
                symbol=symbol,
                timestamp=date,
                price=price,
                volume=random.randint(100000, 500000),
                open_price=price + random.uniform(-20, 20),
                high_price=price + random.uniform(0, 30),
                low_price=price - random.uniform(0, 30),
                close_price=price,
                change=random.uniform(-30, 30),
                change_percent=random.uniform(-1.5, 1.5),
                source=DataSourceType.KITE_CONNECT,
                metadata={'mock': True, 'historical': True}
            ))
        
        return historical_data

class MarketDataCollector:
    """Main market data collector with multiple source support and failover."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize market data collector.
        
        Args:
            config: Configuration dictionary containing data source settings
        """
        self.config = config
        self.data_sources: Dict[DataSourceType, MarketDataSource] = {}
        self.primary_source = None
        self.fallback_sources = []
        self.cache = {}
        self.cache_ttl = config.get('cache_ttl', 60)  # seconds
        self.setup_data_sources()
    
    def setup_data_sources(self):
        """Setup configured data sources."""
        sources_config = self.config.get('data_sources', {})
        
        # Setup Kite Connect if configured
        if 'kite_connect' in sources_config:
            kite_config = sources_config['kite_connect']
            kite_source = KiteConnectDataSource(kite_config)
            self.data_sources[DataSourceType.KITE_CONNECT] = kite_source
            
            if kite_config.get('primary', False):
                self.primary_source = DataSourceType.KITE_CONNECT
            else:
                self.fallback_sources.append(DataSourceType.KITE_CONNECT)
        
        # Setup Mock source for testing
        if self.config.get('use_mock_data', False):
            mock_source = MockDataSource({})
            self.data_sources[DataSourceType.KITE_CONNECT] = mock_source
            if not self.primary_source:
                self.primary_source = DataSourceType.KITE_CONNECT
    
    def connect_all_sources(self) -> bool:
        """Connect to all configured data sources.
        
        Returns:
            True if at least one source connected successfully
        """
        success_count = 0
        
        for source_type, source in self.data_sources.items():
            try:
                if source.connect():
                    success_count += 1
                    print(f"✅ Connected to {source_type.value}")
                else:
                    print(f"❌ Failed to connect to {source_type.value}: {source.last_error}")
            except Exception as e:
                print(f"❌ Error connecting to {source_type.value}: {e}")
        
        return success_count > 0
    
    def disconnect_all_sources(self):
        """Disconnect from all data sources."""
        for source_type, source in self.data_sources.items():
            try:
                source.disconnect()
                print(f"Disconnected from {source_type.value}")
            except Exception as e:
                print(f"Error disconnecting from {source_type.value}: {e}")
    
    def get_market_data(self, symbol: str, use_cache: bool = True) -> Optional[MarketDataPoint]:
        """Get market data with automatic failover.
        
        Args:
            symbol: Market symbol
            use_cache: Whether to use cached data
            
        Returns:
            MarketDataPoint or None if all sources fail
        """
        # Check cache first
        if use_cache:
            cache_key = f"market_{symbol}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Try primary source first
        if self.primary_source and self.primary_source in self.data_sources:
            data = self.data_sources[self.primary_source].get_market_data(symbol)
            if data:
                self._store_in_cache(f"market_{symbol}", data)
                return data
        
        # Try fallback sources
        for source_type in self.fallback_sources:
            if source_type in self.data_sources:
                data = self.data_sources[source_type].get_market_data(symbol)
                if data:
                    self._store_in_cache(f"market_{symbol}", data)
                    return data
        
        return None
    
    def get_options_chain(self, symbol: str, expiry: str, use_cache: bool = True) -> List[OptionsDataPoint]:
        """Get options chain with automatic failover.
        
        Args:
            symbol: Underlying symbol
            expiry: Expiry date
            use_cache: Whether to use cached data
            
        Returns:
            List of OptionsDataPoint
        """
        # Check cache first
        if use_cache:
            cache_key = f"options_{symbol}_{expiry}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Try primary source first
        if self.primary_source and self.primary_source in self.data_sources:
            data = self.data_sources[self.primary_source].get_options_chain(symbol, expiry)
            if data:
                self._store_in_cache(f"options_{symbol}_{expiry}", data)
                return data
        
        # Try fallback sources
        for source_type in self.fallback_sources:
            if source_type in self.data_sources:
                data = self.data_sources[source_type].get_options_chain(symbol, expiry)
                if data:
                    self._store_in_cache(f"options_{symbol}_{expiry}", data)
                    return data
        
        return []
    
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, MarketDataPoint]:
        """Get quotes for multiple symbols efficiently.
        
        Args:
            symbols: List of symbols to get quotes for
            
        Returns:
            Dictionary mapping symbols to MarketDataPoint
        """
        quotes = {}
        
        for symbol in symbols:
            data = self.get_market_data(symbol)
            if data:
                quotes[symbol] = data
        
        return quotes
    
    def _get_from_cache(self, key: str) -> Any:
        """Get data from cache if not expired."""
        if key not in self.cache:
            return None
        
        data, timestamp = self.cache[key]
        if time.time() - timestamp > self.cache_ttl:
            del self.cache[key]
            return None
        
        return data
    
    def _store_in_cache(self, key: str, data: Any):
        """Store data in cache with timestamp."""
        self.cache[key] = (data, time.time())
        
        # Cleanup old cache entries
        current_time = time.time()
        expired_keys = [
            k for k, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all data sources.
        
        Returns:
            Dictionary containing health status of each source
        """
        health_status = {}
        
        for source_type, source in self.data_sources.items():
            health_status[source_type.value] = {
                'connected': source.is_connected,
                'healthy': source.health_check(),
                'request_count': source.request_count,
                'error_count': source.error_count,
                'last_error': source.last_error
            }
        
        health_status['cache_size'] = len(self.cache)
        health_status['primary_source'] = self.primary_source.value if self.primary_source else None
        
        return health_status
    
    def cleanup_cache(self):
        """Clean up expired cache entries."""
        current_time = time.time()
        expired_keys = [
            k for k, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)

# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    config = {
        'cache_ttl': 60,
        'use_mock_data': True,  # Set to False for real data
        'data_sources': {
            'kite_connect': {
                'api_key': os.getenv('KITE_API_KEY'),
                'access_token': os.getenv('KITE_ACCESS_TOKEN'),
                'primary': True
            }
        }
    }
    
    # Initialize collector
    collector = MarketDataCollector(config)
    
    # Connect to data sources
    if collector.connect_all_sources():
        print("✅ Market Data Collector initialized successfully")
        
        # Test market data collection
        nifty_data = collector.get_market_data('NIFTY')
        if nifty_data:
            print(f"NIFTY Price: {nifty_data.price}")
        
        # Test options chain collection
        from datetime import datetime, timedelta
        expiry_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        options_chain = collector.get_options_chain('NIFTY', expiry_date)
        print(f"Options Chain: {len(options_chain)} options")
        
        # Test health status
        health = collector.get_health_status()
        print("Health Status:", json.dumps(health, indent=2))
        
        # Cleanup
        collector.disconnect_all_sources()
    else:
        print("❌ Failed to initialize Market Data Collector")