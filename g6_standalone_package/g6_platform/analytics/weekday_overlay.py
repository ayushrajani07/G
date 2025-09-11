#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Weekday Master Overlay Module - G6 Platform v3.0

Creates and maintains historical weekday overlays for options data analysis.
This module enables plotting live prices overlayed on historical averages 
based on time for all (index*expiry_tag*offset) combinations.

Features:
- Separate master files for each weekday (Monday-Sunday)
- Rolling average calculations for total premiums
- Data integrity counters for validation
- Historical overlay plotting capabilities
- ATM options data aggregation (ce, pe, tp, avg_ce, avg_pe, avg_tp)
"""

import os
import csv
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class WeekdayDataPoint:
    """Single data point for weekday overlay."""
    timestamp: str
    tp_avg: float  # Total premium average
    counter_tp: int  # TP average process count
    avg_tp_avg: float  # Average total premium average
    counter_avg_tp: int  # Average TP process count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV writing."""
        return {
            'timestamp': self.timestamp,
            'tp_avg': self.tp_avg,
            'counter_tp': self.counter_tp,
            'avg_tp_avg': self.avg_tp_avg,
            'counter_avg_tp': self.counter_avg_tp
        }

@dataclass
class ATMOptionsData:
    """ATM options data structure for processing."""
    ce: float  # ATM call option last_price
    pe: float  # ATM put option last_price
    tp: float  # Total premium (ce + pe)
    avg_ce: float  # ATM call option avg_price
    avg_pe: float  # ATM put option avg_price
    avg_tp: float  # Total premium (avg_ce + avg_pe)
    timestamp: str
    index: str
    expiry_tag: str
    offset: int

@dataclass
class OverlayConfig:
    """Configuration for weekday overlay processing."""
    base_path: str = "data/weekday_overlays"
    indices: List[str] = field(default_factory=lambda: ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"])
    expiry_tags: List[str] = field(default_factory=lambda: ["current_week", "next_week"])
    offsets: List[int] = field(default_factory=lambda: [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5])
    
    # File format settings
    file_extension: str = ".csv"
    backup_enabled: bool = True
    max_backup_files: int = 10

class WeekdayMasterOverlay:
    """
    📊 Weekday Master Overlay System
    
    Manages historical weekday overlays for options data analysis with
    rolling averages and data integrity tracking.
    """
    
    # Weekday mapping
    WEEKDAYS = {
        0: 'Monday',
        1: 'Tuesday', 
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    }
    
    # CSV column headers
    CSV_HEADERS = ['timestamp', 'tp_avg', 'counter_tp', 'avg_tp_avg', 'counter_avg_tp']
    
    def __init__(self, config: OverlayConfig = None):
        """
        Initialize Weekday Master Overlay system.
        
        Args:
            config: Configuration for overlay processing
        """
        self.config = config or OverlayConfig()
        self._lock = threading.RLock()
        
        # Create base directory structure
        self._ensure_directory_structure()
        
        # In-memory cache for quick access
        self._overlay_cache: Dict[str, Dict[str, WeekdayDataPoint]] = defaultdict(dict)
        
        logger.info("📊 Weekday Master Overlay system initialized")
        logger.info(f"📁 Base path: {self.config.base_path}")
        logger.info(f"📈 Tracking {len(self.config.indices)} indices, {len(self.config.expiry_tags)} expiries, {len(self.config.offsets)} offsets")
    
    def _ensure_directory_structure(self):
        """Create directory structure for weekday overlays."""
        base_path = Path(self.config.base_path)
        
        # Create weekday directories
        for weekday_name in self.WEEKDAYS.values():
            weekday_dir = base_path / weekday_name.lower()
            weekday_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for each index/expiry/offset combination
            for index in self.config.indices:
                for expiry_tag in self.config.expiry_tags:
                    for offset in self.config.offsets:
                        combo_dir = weekday_dir / index / expiry_tag / str(offset)
                        combo_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"📁 Directory structure created at {base_path}")
    
    def process_atm_data(self, atm_data: ATMOptionsData) -> bool:
        """
        Process ATM options data and update weekday overlays.
        
        Args:
            atm_data: ATM options data to process
            
        Returns:
            bool: Success status
        """
        try:
            with self._lock:
                # Get current weekday
                current_time = datetime.fromisoformat(atm_data.timestamp)
                weekday_num = current_time.weekday()
                weekday_name = self.WEEKDAYS[weekday_num]
                
                # Create cache key
                cache_key = self._create_cache_key(
                    atm_data.index, 
                    atm_data.expiry_tag, 
                    atm_data.offset, 
                    weekday_name
                )
                
                # Get or create master data point for this timestamp
                timestamp_key = current_time.strftime("%H:%M")
                master_data = self._get_or_create_master_data(
                    cache_key, 
                    timestamp_key, 
                    atm_data.index, 
                    atm_data.expiry_tag, 
                    atm_data.offset, 
                    weekday_name
                )
                
                # Update rolling averages
                updated_data = self._update_rolling_averages(master_data, atm_data)
                
                # Save to cache and file
                self._overlay_cache[cache_key][timestamp_key] = updated_data
                self._save_master_file(
                    atm_data.index, 
                    atm_data.expiry_tag, 
                    atm_data.offset, 
                    weekday_name, 
                    updated_data
                )
                
                logger.debug(f"📊 Updated {weekday_name} overlay for {atm_data.index}|{atm_data.expiry_tag}|{atm_data.offset} at {timestamp_key}")
                return True
                
        except Exception as e:
            logger.error(f"🔴 Failed to process ATM data: {e}")
            return False
    
    def _create_cache_key(self, index: str, expiry_tag: str, offset: int, weekday_name: str) -> str:
        """Create cache key for overlay data."""
        return f"{index}|{expiry_tag}|{offset}|{weekday_name}"
    
    def _get_or_create_master_data(self, 
                                 cache_key: str, 
                                 timestamp_key: str,
                                 index: str, 
                                 expiry_tag: str, 
                                 offset: int,
                                 weekday_name: str) -> WeekdayDataPoint:
        """Get existing or create new master data point."""
        # Check cache first
        if cache_key in self._overlay_cache and timestamp_key in self._overlay_cache[cache_key]:
            return self._overlay_cache[cache_key][timestamp_key]
        
        # Try to load from file
        master_data = self._load_master_data(index, expiry_tag, offset, weekday_name, timestamp_key)
        
        if master_data is None:
            # Create new data point
            master_data = WeekdayDataPoint(
                timestamp=timestamp_key,
                tp_avg=0.0,
                counter_tp=0,
                avg_tp_avg=0.0,
                counter_avg_tp=0
            )
        
        return master_data
    
    def _update_rolling_averages(self, 
                               master_data: WeekdayDataPoint, 
                               atm_data: ATMOptionsData) -> WeekdayDataPoint:
        """
        Update rolling averages with new data.
        
        Rolling average formula:
        - tp_avg = (old tp_avg + todays tp) / 2
        - avg_tp_avg = (old avg_tp_avg + todays avg_tp) / 2
        """
        # Update TP average
        if master_data.counter_tp == 0:
            new_tp_avg = atm_data.tp
        else:
            new_tp_avg = (master_data.tp_avg + atm_data.tp) / 2
        
        # Update AVG TP average
        if master_data.counter_avg_tp == 0:
            new_avg_tp_avg = atm_data.avg_tp
        else:
            new_avg_tp_avg = (master_data.avg_tp_avg + atm_data.avg_tp) / 2
        
        # Create updated data point
        updated_data = WeekdayDataPoint(
            timestamp=master_data.timestamp,
            tp_avg=new_tp_avg,
            counter_tp=master_data.counter_tp + 1,
            avg_tp_avg=new_avg_tp_avg,
            counter_avg_tp=master_data.counter_avg_tp + 1
        )
        
        logger.debug(f"🔄 Rolling avg updated: tp_avg {master_data.tp_avg:.2f} → {new_tp_avg:.2f}, avg_tp_avg {master_data.avg_tp_avg:.2f} → {new_avg_tp_avg:.2f}")
        
        return updated_data
    
    def _load_master_data(self, 
                        index: str, 
                        expiry_tag: str, 
                        offset: int, 
                        weekday_name: str, 
                        timestamp_key: str) -> Optional[WeekdayDataPoint]:
        """Load master data from file for specific timestamp."""
        master_file = self._get_master_file_path(index, expiry_tag, offset, weekday_name)
        
        if not master_file.exists():
            return None
        
        try:
            df = pd.read_csv(master_file)
            matching_rows = df[df['timestamp'] == timestamp_key]
            
            if len(matching_rows) == 0:
                return None
            
            row = matching_rows.iloc[-1]  # Take the latest entry if multiple
            
            return WeekdayDataPoint(
                timestamp=row['timestamp'],
                tp_avg=float(row['tp_avg']),
                counter_tp=int(row['counter_tp']),
                avg_tp_avg=float(row['avg_tp_avg']),
                counter_avg_tp=int(row['counter_avg_tp'])
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load master data from {master_file}: {e}")
            return None
    
    def _save_master_file(self, 
                        index: str, 
                        expiry_tag: str, 
                        offset: int, 
                        weekday_name: str, 
                        data_point: WeekdayDataPoint):
        """Save/update master file with new data point."""
        master_file = self._get_master_file_path(index, expiry_tag, offset, weekday_name)
        
        try:
            # Create backup if file exists
            if master_file.exists() and self.config.backup_enabled:
                self._create_backup(master_file)
            
            # Read existing data
            existing_data = []
            if master_file.exists():
                try:
                    df = pd.read_csv(master_file)
                    existing_data = df.to_dict('records')
                except Exception as e:
                    logger.warning(f"⚠️ Failed to read existing master file: {e}")
            
            # Update or add new data point
            updated = False
            for i, row in enumerate(existing_data):
                if row['timestamp'] == data_point.timestamp:
                    existing_data[i] = data_point.to_dict()
                    updated = True
                    break
            
            if not updated:
                existing_data.append(data_point.to_dict())
            
            # Sort by timestamp
            existing_data.sort(key=lambda x: x['timestamp'])
            
            # Write updated data
            with open(master_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
                writer.writeheader()
                writer.writerows(existing_data)
            
            logger.debug(f"💾 Saved master file: {master_file}")
            
        except Exception as e:
            logger.error(f"🔴 Failed to save master file {master_file}: {e}")
    
    def _get_master_file_path(self, 
                            index: str, 
                            expiry_tag: str, 
                            offset: int, 
                            weekday_name: str) -> Path:
        """Get path to master file for given parameters."""
        return (Path(self.config.base_path) / 
                weekday_name.lower() / 
                index / 
                expiry_tag / 
                str(offset) / 
                f"master{self.config.file_extension}")
    
    def _create_backup(self, file_path: Path):
        """Create backup of master file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = file_path.with_suffix(f".backup_{timestamp}.csv")
            
            import shutil
            shutil.copy2(file_path, backup_path)
            
            # Clean old backups
            self._cleanup_old_backups(file_path.parent)
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to create backup: {e}")
    
    def _cleanup_old_backups(self, directory: Path):
        """Clean up old backup files."""
        try:
            backup_files = list(directory.glob("*.backup_*.csv"))
            if len(backup_files) > self.config.max_backup_files:
                # Sort by creation time and remove oldest
                backup_files.sort(key=lambda x: x.stat().st_mtime)
                for old_backup in backup_files[:-self.config.max_backup_files]:
                    old_backup.unlink()
                    logger.debug(f"🗑️ Removed old backup: {old_backup}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to cleanup backups: {e}")
    
    def get_overlay_data(self, 
                       index: str, 
                       expiry_tag: str, 
                       offset: int, 
                       weekday_name: str = None) -> Dict[str, List[WeekdayDataPoint]]:
        """
        Get overlay data for plotting.
        
        Args:
            index: Index name (NIFTY, BANKNIFTY, etc.)
            expiry_tag: Expiry tag (current_week, next_week, etc.)
            offset: Strike offset
            weekday_name: Specific weekday or None for all weekdays
            
        Returns:
            Dictionary of weekday data points
        """
        result = {}
        
        weekdays_to_check = [weekday_name] if weekday_name else list(self.WEEKDAYS.values())
        
        for weekday in weekdays_to_check:
            master_file = self._get_master_file_path(index, expiry_tag, offset, weekday)
            
            if master_file.exists():
                try:
                    df = pd.read_csv(master_file)
                    data_points = []
                    
                    for _, row in df.iterrows():
                        data_point = WeekdayDataPoint(
                            timestamp=row['timestamp'],
                            tp_avg=float(row['tp_avg']),
                            counter_tp=int(row['counter_tp']),
                            avg_tp_avg=float(row['avg_tp_avg']),
                            counter_avg_tp=int(row['counter_avg_tp'])
                        )
                        data_points.append(data_point)
                    
                    result[weekday] = data_points
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load overlay data for {weekday}: {e}")
                    result[weekday] = []
            else:
                result[weekday] = []
        
        return result
    
    def get_current_overlay(self, 
                          index: str, 
                          expiry_tag: str, 
                          offset: int, 
                          current_time: datetime = None) -> Optional[WeekdayDataPoint]:
        """
        Get current overlay data for real-time comparison.
        
        Args:
            index: Index name
            expiry_tag: Expiry tag
            offset: Strike offset
            current_time: Current time (defaults to now)
            
        Returns:
            Current overlay data point or None
        """
        if current_time is None:
            current_time = datetime.now()
        
        weekday_num = current_time.weekday()
        weekday_name = self.WEEKDAYS[weekday_num]
        timestamp_key = current_time.strftime("%H:%M")
        
        cache_key = self._create_cache_key(index, expiry_tag, offset, weekday_name)
        
        # Check cache first
        if cache_key in self._overlay_cache and timestamp_key in self._overlay_cache[cache_key]:
            return self._overlay_cache[cache_key][timestamp_key]
        
        # Load from file
        return self._load_master_data(index, expiry_tag, offset, weekday_name, timestamp_key)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overlay system statistics."""
        stats = {
            'configuration': {
                'indices': self.config.indices,
                'expiry_tags': self.config.expiry_tags,
                'offsets': self.config.offsets,
                'base_path': self.config.base_path
            },
            'cache_status': {
                'cached_combinations': len(self._overlay_cache),
                'total_data_points': sum(len(data) for data in self._overlay_cache.values())
            },
            'file_status': {}
        }
        
        # Count master files for each weekday
        for weekday_name in self.WEEKDAYS.values():
            weekday_dir = Path(self.config.base_path) / weekday_name.lower()
            master_files = list(weekday_dir.glob("**/master.csv"))
            stats['file_status'][weekday_name] = {
                'master_files': len(master_files),
                'directory_exists': weekday_dir.exists()
            }
        
        return stats
    
    def clear_cache(self):
        """Clear in-memory cache."""
        with self._lock:
            self._overlay_cache.clear()
        logger.info("🧹 Weekday overlay cache cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on overlay system."""
        health = {
            'status': 'healthy',
            'base_directory_exists': Path(self.config.base_path).exists(),
            'cache_size': len(self._overlay_cache),
            'weekday_directories': {}
        }
        
        # Check weekday directories
        issues = []
        for weekday_name in self.WEEKDAYS.values():
            weekday_dir = Path(self.config.base_path) / weekday_name.lower()
            health['weekday_directories'][weekday_name] = weekday_dir.exists()
            
            if not weekday_dir.exists():
                issues.append(f"Missing {weekday_name} directory")
        
        if issues:
            health['status'] = 'degraded'
            health['issues'] = issues
        
        return health

# Utility functions for integration

def create_atm_data_from_collector_result(result_data: Dict[str, Any], 
                                        index: str, 
                                        expiry_tag: str, 
                                        offset: int) -> Optional[ATMOptionsData]:
    """
    Create ATMOptionsData from collector result.
    
    Args:
        result_data: Data from ATM collector
        index: Index name
        expiry_tag: Expiry tag
        offset: Strike offset
        
    Returns:
        ATMOptionsData instance or None if invalid
    """
    try:
        # Extract CE and PE data
        ce_data = next((item for item in result_data if item.get('option_type') == 'CE'), None)
        pe_data = next((item for item in result_data if item.get('option_type') == 'PE'), None)
        
        if not ce_data or not pe_data:
            return None
        
        # Calculate values
        ce = ce_data.get('last_price', 0.0)
        pe = pe_data.get('last_price', 0.0)
        tp = ce + pe
        
        # For avg prices, use bid-ask average if available, otherwise use last_price
        avg_ce = _calculate_avg_price(ce_data)
        avg_pe = _calculate_avg_price(pe_data)
        avg_tp = avg_ce + avg_pe
        
        return ATMOptionsData(
            ce=ce,
            pe=pe,
            tp=tp,
            avg_ce=avg_ce,
            avg_pe=avg_pe,
            avg_tp=avg_tp,
            timestamp=datetime.now().isoformat(),
            index=index,
            expiry_tag=expiry_tag,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"🔴 Failed to create ATM data: {e}")
        return None

def _calculate_avg_price(option_data: Dict[str, Any]) -> float:
    """Calculate average price from option data."""
    last_price = option_data.get('last_price', 0.0)
    
    # If market depth is available, use bid-ask average
    if 'bid' in option_data and 'ask' in option_data:
        bid = option_data.get('bid', 0.0)
        ask = option_data.get('ask', 0.0)
        if bid > 0 and ask > 0:
            return (bid + ask) / 2
    
    # Fallback to last price
    return last_price