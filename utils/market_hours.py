#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕒 FIXED Market Hours & Calendar System for G6.1 Platform
Author: AI Assistant (Fixed missing imports)

✅ Features:
- Complete Indian market calendar with holidays
- NSE/BSE trading hours support
- Pre-market and post-market sessions
- Holiday calendar integration
- Timezone-aware operations
- Market status detection
- Session timing calculations
- FIXED: All import issues resolved
"""

import logging
import datetime
import time
from typing import Dict, List, Any, Optional, Tuple, Union  # FIXED: Added missing imports
import pytz
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class MarketSession(Enum):
    """🕒 Market session types."""
    PRE_MARKET = "pre_market"
    REGULAR = "regular"
    POST_MARKET = "post_market"
    CLOSED = "closed"

class ExchangeType(Enum):
    """🏢 Exchange types."""
    NSE = "NSE"
    BSE = "BSE"
    MCX = "MCX"

@dataclass
class TradingSession:
    """📊 Trading session definition."""
    name: str
    start_time: datetime.time
    end_time: datetime.time
    session_type: MarketSession
    exchanges: List[ExchangeType] = field(default_factory=list)
    
    def is_active_at(self, check_time: datetime.time) -> bool:
        """🕒 Check if session is active at given time."""
        return self.start_time <= check_time <= self.end_time
    
    def duration_minutes(self) -> int:
        """⏱️ Get session duration in minutes."""
        start_dt = datetime.datetime.combine(datetime.date.today(), self.start_time)
        end_dt = datetime.datetime.combine(datetime.date.today(), self.end_time)
        return int((end_dt - start_dt).total_seconds() / 60)

@dataclass
class MarketDay:
    """📅 Market day information."""
    date: datetime.date
    is_trading_day: bool
    sessions: List[TradingSession] = field(default_factory=list)
    holiday_name: Optional[str] = None
    special_notes: Optional[str] = None
    
    def get_active_session(self, check_time: datetime.time) -> Optional[TradingSession]:
        """🕒 Get active session at given time."""
        for session in self.sessions:
            if session.is_active_at(check_time):
                return session
        return None
    
    def is_market_open_at(self, check_time: datetime.time) -> bool:
        """🕒 Check if market is open at given time."""
        if not self.is_trading_day:
            return False
        
        active_session = self.get_active_session(check_time)
        return active_session is not None and active_session.session_type == MarketSession.REGULAR

class MarketHours:
    """
    🕒 AI Assistant: Comprehensive Market Hours & Calendar System.
    
    FIXED VERSION - All imports properly handled
    
    Provides complete Indian market timing with:
    - NSE/BSE trading hours
    - Holiday calendar integration
    - Pre/post market sessions
    - Timezone handling
    - Session management
    """
    
    def __init__(self, timezone: str = 'Asia/Kolkata', exchange: str = 'NSE'):
        """
        🆕 Initialize Market Hours system.
        
        Args:
            timezone: Market timezone (default: Asia/Kolkata)
            exchange: Primary exchange (default: NSE)
        """
        self.timezone = timezone
        self.exchange = ExchangeType(exchange) if isinstance(exchange, str) else exchange
        self.logger = logging.getLogger(f"{__name__}.MarketHours")
        
        try:
            self.tz = pytz.timezone(self.timezone)
        except Exception:
            self.tz = pytz.UTC
            self.logger.warning(f"⚠️ Invalid timezone {timezone}, using UTC")
        
        # 🕒 Standard NSE trading sessions
        self.standard_sessions = [
            TradingSession(
                name="Pre-Market",
                start_time=datetime.time(9, 0),
                end_time=datetime.time(9, 15),
                session_type=MarketSession.PRE_MARKET,
                exchanges=[ExchangeType.NSE, ExchangeType.BSE]
            ),
            TradingSession(
                name="Regular Trading",
                start_time=datetime.time(9, 15),
                end_time=datetime.time(15, 30),
                session_type=MarketSession.REGULAR,
                exchanges=[ExchangeType.NSE, ExchangeType.BSE]
            ),
            TradingSession(
                name="Post-Market",
                start_time=datetime.time(15, 40),
                end_time=datetime.time(16, 0),
                session_type=MarketSession.POST_MARKET,
                exchanges=[ExchangeType.NSE]
            )
        ]
        
        # 📅 Initialize holiday calendar
        self.holiday_calendar = self._initialize_holiday_calendar()
        
        # 📊 Cache for market days
        self.market_day_cache: Dict[datetime.date, MarketDay] = {}
        self.cache_expiry_days = 30
        
        self.logger.info(f"✅ Market Hours initialized for {exchange} in {timezone}")
    
    def _initialize_holiday_calendar(self) -> Dict[int, List[datetime.date]]:
        """📅 Initialize Indian market holiday calendar."""
        try:
            # 2025 Indian Market Holidays (NSE/BSE)
            holidays_2025 = [
                # Fixed holidays
                datetime.date(2025, 1, 26),   # Republic Day
                datetime.date(2025, 3, 14),   # Holi
                datetime.date(2025, 3, 31),   # Ram Navami  
                datetime.date(2025, 4, 14),   # Mahavir Jayanti
                datetime.date(2025, 4, 18),   # Good Friday
                datetime.date(2025, 5, 1),    # Maharashtra Day
                datetime.date(2025, 8, 15),   # Independence Day
                datetime.date(2025, 8, 16),   # Parsi New Year
                datetime.date(2025, 10, 2),   # Gandhi Jayanti
                datetime.date(2025, 10, 20),  # Dussehra
                datetime.date(2025, 11, 1),   # Diwali Balipratipada
                datetime.date(2025, 11, 5),   # Bhai Dooj
                datetime.date(2025, 12, 25),  # Christmas
            ]
            
            # 2024 holidays for reference
            holidays_2024 = [
                datetime.date(2024, 1, 26),   # Republic Day
                datetime.date(2024, 3, 8),    # Holi
                datetime.date(2024, 3, 25),   # Holi
                datetime.date(2024, 3, 29),   # Good Friday
                datetime.date(2024, 4, 11),   # Eid al-Fitr
                datetime.date(2024, 4, 17),   # Ram Navami
                datetime.date(2024, 5, 1),    # Maharashtra Day
                datetime.date(2024, 8, 15),   # Independence Day
                datetime.date(2024, 10, 2),   # Gandhi Jayanti
                datetime.date(2024, 10, 12),  # Dussehra
                datetime.date(2024, 11, 1),   # Diwali
                datetime.date(2024, 11, 2),   # Diwali Balipratipada
                datetime.date(2024, 12, 25),  # Christmas
            ]
            
            return {
                2024: holidays_2024,
                2025: holidays_2025,
            }
            
        except Exception as e:
            self.logger.error(f"🔴 Error initializing holiday calendar: {e}")
            return {}
    
    def is_market_open(self, check_datetime: Optional[datetime.datetime] = None) -> bool:
        """
        🕒 Check if market is currently open.
        
        Args:
            check_datetime: Datetime to check (default: now in market timezone)
            
        Returns:
            bool: True if market is open for regular trading
        """
        try:
            # 🕒 Get current time in market timezone
            if check_datetime is None:
                check_datetime = datetime.datetime.now(self.tz)
            elif check_datetime.tzinfo is None:
                check_datetime = self.tz.localize(check_datetime)
            else:
                check_datetime = check_datetime.astimezone(self.tz)
            
            # 📅 Get market day information
            market_day = self.get_market_day(check_datetime.date())
            
            if not market_day.is_trading_day:
                return False
            
            # 🕒 Check if current time falls within regular trading session
            return market_day.is_market_open_at(check_datetime.time())
            
        except Exception as e:
            self.logger.error(f"🔴 Error checking market status: {e}")
            return False
    
    def get_market_day(self, date: datetime.date) -> MarketDay:
        """
        📅 Get market day information for given date.
        
        Args:
            date: Date to check
            
        Returns:
            MarketDay: Market day information
        """
        try:
            # 📊 Check cache first
            if date in self.market_day_cache:
                return self.market_day_cache[date]
            
            # 🗓️ Check if it's a weekend
            if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                market_day = MarketDay(
                    date=date,
                    is_trading_day=False,
                    sessions=[],
                    special_notes="Weekend"
                )
            # 🎉 Check if it's a holiday
            elif self.is_holiday(date):
                holiday_name = self.get_holiday_name(date)
                market_day = MarketDay(
                    date=date,
                    is_trading_day=False,
                    sessions=[],
                    holiday_name=holiday_name
                )
            # 📊 Regular trading day
            else:
                market_day = MarketDay(
                    date=date,
                    is_trading_day=True,
                    sessions=self.standard_sessions.copy()
                )
            
            # 📊 Cache the result
            self.market_day_cache[date] = market_day
            
            return market_day
            
        except Exception as e:
            self.logger.error(f"🔴 Error getting market day for {date}: {e}")
            # 🆘 Return conservative default
            return MarketDay(
                date=date,
                is_trading_day=False,
                sessions=[],
                special_notes="Error retrieving market day info"
            )
    
    def is_holiday(self, date: datetime.date) -> bool:
        """
        🎉 Check if given date is a market holiday.
        
        Args:
            date: Date to check
            
        Returns:
            bool: True if date is a holiday
        """
        try:
            year_holidays = self.holiday_calendar.get(date.year, [])
            return date in year_holidays
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error checking holiday status for {date}: {e}")
            return False
    
    def get_holiday_name(self, date: datetime.date) -> Optional[str]:
        """
        🎉 Get holiday name for given date.
        
        Args:
            date: Date to check
            
        Returns:
            Optional[str]: Holiday name or None
        """
        try:
            if not self.is_holiday(date):
                return None
            
            # 📅 Holiday name mapping (simplified)
            holiday_names = {
                (1, 26): "Republic Day",
                (3, 8): "Holi", (3, 14): "Holi", (3, 25): "Holi",
                (3, 29): "Good Friday", (4, 18): "Good Friday",
                (3, 31): "Ram Navami", (4, 17): "Ram Navami",
                (4, 14): "Mahavir Jayanti",
                (5, 1): "Maharashtra Day",
                (8, 15): "Independence Day",
                (8, 16): "Parsi New Year",
                (10, 2): "Gandhi Jayanti",
                (10, 12): "Dussehra", (10, 20): "Dussehra",
                (11, 1): "Diwali/Balipratipada",
                (11, 2): "Diwali Balipratipada",
                (11, 5): "Bhai Dooj",
                (12, 25): "Christmas"
            }
            
            return holiday_names.get((date.month, date.day), "Market Holiday")
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error getting holiday name for {date}: {e}")
            return "Market Holiday"
    
    def get_current_session(self, check_datetime: Optional[datetime.datetime] = None) -> Optional[TradingSession]:
        """
        🕒 Get current active trading session.
        
        Args:
            check_datetime: Datetime to check (default: now)
            
        Returns:
            Optional[TradingSession]: Current active session or None
        """
        try:
            # 🕒 Get current time in market timezone
            if check_datetime is None:
                check_datetime = datetime.datetime.now(self.tz)
            elif check_datetime.tzinfo is None:
                check_datetime = self.tz.localize(check_datetime)
            else:
                check_datetime = check_datetime.astimezone(self.tz)
            
            # 📅 Get market day
            market_day = self.get_market_day(check_datetime.date())
            
            if not market_day.is_trading_day:
                return None
            
            return market_day.get_active_session(check_datetime.time())
            
        except Exception as e:
            self.logger.error(f"🔴 Error getting current session: {e}")
            return None
    
    def get_market_status(self, detailed: bool = False) -> Dict[str, Any]:
        """
        📊 Get comprehensive market status.
        
        Args:
            detailed: Include detailed session information
            
        Returns:
            Dict[str, Any]: Market status information
        """
        try:
            now = datetime.datetime.now(self.tz)
            current_session = self.get_current_session(now)
            is_open = self.is_market_open(now)
            
            status = {
                'is_open': is_open,
                'current_time': now.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'exchange': self.exchange.value,
                'timezone': self.timezone
            }
            
            if current_session:
                status['current_session'] = {
                    'name': current_session.name,
                    'type': current_session.session_type.value,
                    'start_time': current_session.start_time.strftime('%H:%M'),
                    'end_time': current_session.end_time.strftime('%H:%M')
                }
            else:
                status['current_session'] = None
            
            # 📅 Add market day info
            market_day = self.get_market_day(now.date())
            status['is_trading_day'] = market_day.is_trading_day
            
            if market_day.holiday_name:
                status['holiday'] = market_day.holiday_name
            
            if market_day.special_notes:
                status['notes'] = market_day.special_notes
            
            return status
            
        except Exception as e:
            self.logger.error(f"🔴 Error getting market status: {e}")
            return {
                'is_open': False,
                'error': str(e),
                'exchange': self.exchange.value if hasattr(self, 'exchange') else 'NSE',
                'timezone': self.timezone if hasattr(self, 'timezone') else 'Asia/Kolkata'
            }

def get_trading_calendar(year: int = None) -> Dict[str, Any]:  # FIXED: Proper type annotation
    """
    📅 Get complete trading calendar for given year.
    
    Args:
        year: Year for calendar (default: current year)
        
    Returns:
        Dict[str, Any]: Trading calendar information
    """
    if year is None:
        year = datetime.date.today().year
    
    try:
        market_hours = MarketHours()
        
        # 📅 Generate calendar for the year
        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year, 12, 31)
        
        trading_days = []
        holidays = []
        
        current_date = start_date
        while current_date <= end_date:
            market_day = market_hours.get_market_day(current_date)
            
            if market_day.is_trading_day:
                trading_days.append(current_date.isoformat())
            elif market_day.holiday_name:
                holidays.append({
                    'date': current_date.isoformat(),
                    'name': market_day.holiday_name
                })
            
            current_date += datetime.timedelta(days=1)
        
        return {
            'year': year,
            'total_trading_days': len(trading_days),
            'total_holidays': len(holidays),
            'trading_days': trading_days[:10],  # Show first 10 to avoid huge output
            'holidays': holidays,
            'generated_at': datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"🔴 Error generating trading calendar: {e}")
        return {
            'year': year,
            'error': str(e),
            'generated_at': datetime.datetime.now().isoformat()
        }

# 🧪 AI Assistant: Testing functions
def test_market_hours():
    """🧪 Test Market Hours functionality."""
    print("🧪 Testing Market Hours...")
    
    try:
        # 📊 Initialize market hours
        market_hours = MarketHours()
        print("✅ Market Hours initialized")
        
        # 🕒 Test current market status
        status = market_hours.get_market_status(detailed=True)
        print(f"✅ Market Status: {'Open' if status['is_open'] else 'Closed'}")
        print(f"   Exchange: {status['exchange']}")
        
        # 📅 Test specific date
        test_date = datetime.date(2025, 1, 26)  # Republic Day
        market_day = market_hours.get_market_day(test_date)
        print(f"✅ {test_date}: {'Trading Day' if market_day.is_trading_day else 'Holiday'}")
        
        if market_day.holiday_name:
            print(f"   Holiday: {market_day.holiday_name}")
        
        print("🎉 Market Hours test completed!")
        return True
        
    except Exception as e:
        print(f"🔴 Market Hours test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_market_hours()