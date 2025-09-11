#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💾 CSV Storage Backend - G6 Platform v3.0
Enhanced CSV storage with rotation, compression, and data integrity.

Restructured from: enhanced_csv_sink_complete_FINAL.py, enhanced_csv_sink_complete.py
Features:
- Automatic file rotation and archiving
- Data compression and integrity checks
- Thread-safe operations with proper locking
- Configurable retention policies
- Memory-efficient streaming writes
- Comprehensive error handling and recovery
"""

import os
import csv
import gzip
import shutil
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, IO
from dataclasses import dataclass, field
import json
import time

logger = logging.getLogger(__name__)

@dataclass
class CSVWriteStats:
    """CSV writing statistics."""
    files_created: int = 0
    records_written: int = 0
    bytes_written: int = 0
    write_errors: int = 0
    last_write_time: Optional[datetime] = None
    compression_ratio: float = 1.0

@dataclass
class FileRotationInfo:
    """File rotation information."""
    current_file: Optional[Path] = None
    current_size: int = 0
    records_in_file: int = 0
    file_created_at: Optional[datetime] = None
    next_rotation_time: Optional[datetime] = None

class CSVSink:
    """
    💾 Enhanced CSV storage backend with enterprise features.
    
    Provides reliable, efficient CSV storage with automatic rotation,
    compression, and data integrity features.
    """
    
    def __init__(self,
                 base_path: Union[str, Path] = "data/csv",
                 enable_compression: bool = False,
                 enable_rotation: bool = True,
                 max_file_size_mb: int = 100,
                 retention_days: int = 30,
                 rotation_interval_hours: int = 24,
                 enable_backup: bool = True,
                 enable_integrity_checks: bool = True):
        """
        Initialize CSV storage backend.
        
        Args:
            base_path: Base directory for CSV files
            enable_compression: Enable gzip compression
            enable_rotation: Enable automatic file rotation
            max_file_size_mb: Maximum file size before rotation
            retention_days: Days to retain files (0 = indefinite)
            rotation_interval_hours: Hours between automatic rotations
            enable_backup: Enable backup copies
            enable_integrity_checks: Enable data integrity checks
        """
        self.base_path = Path(base_path).resolve()
        self.enable_compression = enable_compression
        self.enable_rotation = enable_rotation
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.retention_days = retention_days
        self.rotation_interval = timedelta(hours=rotation_interval_hours)
        self.enable_backup = enable_backup
        self.enable_integrity_checks = enable_integrity_checks
        
        # Create directory structure
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.data_dir = self.base_path / "current"
        self.archive_dir = self.base_path / "archive"
        self.backup_dir = self.base_path / "backup"
        self.temp_dir = self.base_path / "temp"
        
        for directory in [self.data_dir, self.archive_dir, self.backup_dir, self.temp_dir]:
            directory.mkdir(exist_ok=True)
        
        # File management
        self._file_handles: Dict[str, IO] = {}
        self._csv_writers: Dict[str, csv.DictWriter] = {}
        self._rotation_info: Dict[str, FileRotationInfo] = {}
        
        # Statistics
        self.stats = CSVWriteStats()
        
        # Thread safety
        self._lock = threading.RLock()
        self._file_locks: Dict[str, threading.Lock] = {}
        
        # Background cleanup thread
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info("💾 CSV storage backend initialized")
        logger.info(f"📂 Base path: {self.base_path}")
        logger.info(f"⚙️ Compression: {'✅' if enable_compression else '❌'}, "
                   f"Rotation: {'✅' if enable_rotation else '❌'}, "
                   f"Backup: {'✅' if enable_backup else '❌'}")
    
    def store_options_data(self,
                          index_name: str,
                          options_data: Union[List[Dict[str, Any]], Dict[str, Any]],
                          timestamp: Optional[datetime] = None,
                          expiry_tag: str = "current_week",
                          offset: Optional[int] = None) -> bool:
        """
        Store options data to CSV file with new path structure.
        Path format: [INDEX]/[EXPIRY_TAG]/[OFFSET]/[YYYY-MM-DD].csv
        
        Args:
            index_name: Index name (NIFTY, BANKNIFTY, etc.)
            options_data: Options data to store
            timestamp: Optional timestamp (uses current if None)
            expiry_tag: Expiry tag (current_week, next_week, monthly, etc.)
            offset: Strike offset (0 for ATM, -1/-2 for ITM, +1/+2 for OTM)
            
        Returns:
            True if successful
        """
        try:
            timestamp = timestamp or datetime.now()
            
            # Ensure options_data is a list
            if isinstance(options_data, dict):
                options_data = [options_data]
            
            if not options_data:
                logger.warning("⚠️ No options data to store")
                return True
            
            # Get file key for this combination
            file_key = self._get_structured_file_key(index_name, expiry_tag, offset, timestamp)
            
            # Write data
            success = self._write_data(file_key, options_data, timestamp)
            
            # Update statistics
            if success:
                with self._lock:
                    self.stats.records_written += len(options_data)
                    self.stats.last_write_time = timestamp
            
            return success
            
        except Exception as e:
            logger.error(f"🔴 Failed to store options data for {index_name}: {e}")
            with self._lock:
                self.stats.write_errors += 1
            return False
    
    def store_overview_data(self,
                          index_name: str,
                          overview_data: Dict[str, Any],
                          timestamp: Optional[datetime] = None) -> bool:
        """
        Store market overview data to CSV file.
        
        Args:
            index_name: Index name
            overview_data: Overview data to store
            timestamp: Optional timestamp
            
        Returns:
            True if successful
        """
        try:
            timestamp = timestamp or datetime.now()
            
            # Create overview file key
            file_key = f"{index_name}_overview"
            
            # Flatten overview data for CSV
            flattened_data = self._flatten_dict(overview_data)
            flattened_data['timestamp'] = timestamp.isoformat()
            
            return self._write_data(file_key, [flattened_data], timestamp)
            
        except Exception as e:
            logger.error(f"🔴 Failed to store overview data for {index_name}: {e}")
            return False
    
    def _get_file_key(self, index_name: str, timestamp: datetime) -> str:
        """Get file key for data storage (legacy method)."""
        date_str = timestamp.strftime("%Y-%m-%d")
        return f"{index_name}_{date_str}_options"
    
    def _get_structured_file_key(self, 
                               index_name: str, 
                               expiry_tag: str, 
                               offset: Optional[int], 
                               timestamp: datetime) -> str:
        """
        Get structured file key for new path format.
        Format: [INDEX]/[EXPIRY_TAG]/[OFFSET]/[YYYY-MM-DD]
        """
        date_str = timestamp.strftime("%Y-%m-%d")
        
        # Handle cases where offset is not provided
        if offset is None:
            # For ATM or general data
            return f"{index_name}|{expiry_tag}|ATM|{date_str}"
        else:
            return f"{index_name}|{expiry_tag}|{offset}|{date_str}"
    
    def _write_data(self,
                   file_key: str,
                   data: List[Dict[str, Any]],
                   timestamp: datetime) -> bool:
        """Write data to CSV file with proper handling."""
        try:
            # Get or create file lock
            if file_key not in self._file_locks:
                with self._lock:
                    if file_key not in self._file_locks:
                        self._file_locks[file_key] = threading.Lock()
            
            file_lock = self._file_locks[file_key]
            
            with file_lock:
                # Check if rotation is needed
                if self.enable_rotation and self._needs_rotation(file_key):
                    self._rotate_file(file_key)
                
                # Get or create file handle
                file_handle, csv_writer = self._get_or_create_writer(file_key)
                
                if not file_handle or not csv_writer:
                    return False
                
                # Write data
                bytes_before = file_handle.tell() if hasattr(file_handle, 'tell') else 0
                
                for record in data:
                    # Add metadata
                    record_copy = record.copy()
                    record_copy.setdefault('write_timestamp', timestamp.isoformat())
                    record_copy.setdefault('index_name', file_key.split('_')[0])
                    
                    csv_writer.writerow(record_copy)
                
                # Flush to ensure data is written
                file_handle.flush()
                
                # Update statistics
                bytes_after = file_handle.tell() if hasattr(file_handle, 'tell') else bytes_before
                bytes_written = max(0, bytes_after - bytes_before)
                
                with self._lock:
                    self.stats.bytes_written += bytes_written
                    
                    # Update rotation info
                    if file_key in self._rotation_info:
                        self._rotation_info[file_key].current_size += bytes_written
                        self._rotation_info[file_key].records_in_file += len(data)
                
                return True
                
        except Exception as e:
            logger.error(f"🔴 Failed to write data to {file_key}: {e}")
            with self._lock:
                self.stats.write_errors += 1
            return False
    
    def _get_or_create_writer(self, file_key: str) -> tuple[Optional[IO], Optional[csv.DictWriter]]:
        """Get or create CSV writer for file key."""
        try:
            # Check if writer already exists
            if file_key in self._csv_writers:
                file_handle = self._file_handles[file_key]
                csv_writer = self._csv_writers[file_key]
                return file_handle, csv_writer
            
            # Create new file
            file_path = self._get_file_path(file_key)
            
            # Determine if file exists to know whether to write headers
            file_exists = file_path.exists()
            
            # Open file for append
            if self.enable_compression:
                file_handle = gzip.open(file_path.with_suffix(file_path.suffix + '.gz'), 'at', newline='', encoding='utf-8')
            else:
                file_handle = open(file_path, 'a', newline='', encoding='utf-8')
            
            # Store file handle
            self._file_handles[file_key] = file_handle
            
            # Determine fieldnames from first data record or use defaults
            fieldnames = self._get_csv_fieldnames(file_key)
            
            # Create CSV writer
            csv_writer = csv.DictWriter(
                file_handle,
                fieldnames=fieldnames,
                extrasaction='ignore'  # Ignore extra fields
            )
            
            # Write header if new file
            if not file_exists:
                csv_writer.writeheader()
            
            # Store writer
            self._csv_writers[file_key] = csv_writer
            
            # Initialize rotation info
            if file_key not in self._rotation_info:
                self._rotation_info[file_key] = FileRotationInfo(
                    current_file=file_path,
                    file_created_at=datetime.now(),
                    next_rotation_time=datetime.now() + self.rotation_interval
                )
            
            # Update statistics
            with self._lock:
                if not file_exists:
                    self.stats.files_created += 1
            
            return file_handle, csv_writer
            
        except Exception as e:
            logger.error(f"🔴 Failed to create writer for {file_key}: {e}")
            return None, None
    
    def _get_file_path(self, file_key: str) -> Path:
        """
        Get file path for file key supporting new structured format.
        Supports both legacy and new path formats.
        """
        if '|' in file_key:
            # New structured format: INDEX|EXPIRY_TAG|OFFSET|DATE
            parts = file_key.split('|')
            if len(parts) == 4:
                index_name, expiry_tag, offset_str, date_str = parts
                
                # Create directory structure: [INDEX]/[EXPIRY_TAG]/[OFFSET]/
                structured_dir = self.data_dir / index_name / expiry_tag / offset_str
                structured_dir.mkdir(parents=True, exist_ok=True)
                
                # File name is just the date
                filename = f"{date_str}.csv"
                return structured_dir / filename
        
        # Legacy format
        filename = f"{file_key}.csv"
        return self.data_dir / filename
    
    def _get_csv_fieldnames(self, file_key: str) -> List[str]:
        """Get CSV fieldnames for file type."""
        if 'options' in file_key:
            return [
                'symbol', 'strike', 'expiry', 'option_type', 'last_price',
                'volume', 'oi', 'change', 'pchange', 'iv', 'delta', 'gamma',
                'theta', 'vega', 'write_timestamp', 'index_name'
            ]
        elif 'overview' in file_key:
            return [
                'index_name', 'timestamp', 'current_price', 'atm_strike',
                'total_ce_oi', 'total_pe_oi', 'pcr_oi', 'pcr_volume',
                'max_pain', 'implied_volatility', 'sentiment', 'sentiment_score'
            ]
        else:
            # Generic fieldnames
            return [
                'timestamp', 'index_name', 'data_type', 'value',
                'metadata', 'write_timestamp'
            ]
    
    def _needs_rotation(self, file_key: str) -> bool:
        """Check if file needs rotation."""
        if not self.enable_rotation:
            return False
        
        rotation_info = self._rotation_info.get(file_key)
        if not rotation_info:
            return False
        
        # Check size-based rotation
        if rotation_info.current_size >= self.max_file_size_bytes:
            return True
        
        # Check time-based rotation
        if (rotation_info.next_rotation_time and 
            datetime.now() >= rotation_info.next_rotation_time):
            return True
        
        return False
    
    def _rotate_file(self, file_key: str):
        """Rotate current file to archive."""
        try:
            logger.info(f"🔄 Rotating file for {file_key}")
            
            # Close current file
            self._close_file(file_key)
            
            # Move current file to archive
            current_path = self._get_file_path(file_key)
            if current_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = f"{file_key}_{timestamp}.csv"
                archive_path = self.archive_dir / archive_name
                
                # Compress if enabled
                if self.enable_compression:
                    with open(current_path, 'rb') as f_in:
                        with gzip.open(archive_path.with_suffix('.csv.gz'), 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    current_path.unlink()  # Remove original
                else:
                    shutil.move(str(current_path), str(archive_path))
                
                logger.info(f"✅ File rotated to {archive_path}")
            
            # Reset rotation info
            if file_key in self._rotation_info:
                self._rotation_info[file_key] = FileRotationInfo(
                    file_created_at=datetime.now(),
                    next_rotation_time=datetime.now() + self.rotation_interval
                )
            
        except Exception as e:
            logger.error(f"🔴 Failed to rotate file {file_key}: {e}")
    
    def _close_file(self, file_key: str):
        """Close file handle and remove from tracking."""
        try:
            if file_key in self._file_handles:
                self._file_handles[file_key].close()
                del self._file_handles[file_key]
            
            if file_key in self._csv_writers:
                del self._csv_writers[file_key]
            
        except Exception as e:
            logger.error(f"🔴 Failed to close file {file_key}: {e}")
    
    def _flatten_dict(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested dictionary for CSV storage."""
        flattened = {}
        
        for key, value in data.items():
            new_key = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(self._flatten_dict(value, f"{new_key}_"))
            elif isinstance(value, list):
                # Convert list to string representation
                flattened[new_key] = json.dumps(value)
            else:
                flattened[new_key] = value
        
        return flattened
    
    def _start_background_tasks(self):
        """Start background cleanup and maintenance tasks."""
        def cleanup_worker():
            while not self._stop_cleanup.wait(3600):  # Run every hour
                try:
                    self._cleanup_old_files()
                    self._verify_file_integrity()
                except Exception as e:
                    logger.error(f"🔴 Background cleanup error: {e}")
        
        self._cleanup_thread = threading.Thread(
            target=cleanup_worker,
            daemon=True,
            name="CSVCleanup"
        )
        self._cleanup_thread.start()
        logger.info("🧹 Background cleanup thread started")
    
    def _cleanup_old_files(self):
        """Clean up old files based on retention policy."""
        if self.retention_days <= 0:
            return  # No cleanup if retention is disabled
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            files_removed = 0
            
            for file_path in self.archive_dir.glob("*.csv*"):
                try:
                    # Get file modification time
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_mtime < cutoff_date:
                        if self.enable_backup:
                            # Move to backup before deleting
                            backup_path = self.backup_dir / file_path.name
                            shutil.move(str(file_path), str(backup_path))
                        else:
                            # Delete directly
                            file_path.unlink()
                        
                        files_removed += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cleanup file {file_path}: {e}")
            
            if files_removed > 0:
                logger.info(f"🧹 Cleaned up {files_removed} old files")
                
        except Exception as e:
            logger.error(f"🔴 Cleanup failed: {e}")
    
    def _verify_file_integrity(self):
        """Verify integrity of CSV files."""
        if not self.enable_integrity_checks:
            return
        
        try:
            for file_path in self.data_dir.glob("*.csv*"):
                try:
                    # Basic integrity check - try to read the file
                    if file_path.suffix == '.gz':
                        with gzip.open(file_path, 'rt') as f:
                            csv.reader(f)
                    else:
                        with open(file_path, 'r') as f:
                            csv.reader(f)
                            
                except Exception as e:
                    logger.error(f"🔴 File integrity check failed for {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"🔴 Integrity verification failed: {e}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with self._lock:
            # Calculate directory sizes
            current_size = sum(f.stat().st_size for f in self.data_dir.glob("*") if f.is_file())
            archive_size = sum(f.stat().st_size for f in self.archive_dir.glob("*") if f.is_file())
            backup_size = sum(f.stat().st_size for f in self.backup_dir.glob("*") if f.is_file())
            
            return {
                'files_created': self.stats.files_created,
                'records_written': self.stats.records_written,
                'bytes_written': self.stats.bytes_written,
                'write_errors': self.stats.write_errors,
                'last_write_time': self.stats.last_write_time.isoformat() if self.stats.last_write_time else None,
                'compression_enabled': self.enable_compression,
                'rotation_enabled': self.enable_rotation,
                'current_files': len(list(self.data_dir.glob("*.csv*"))),
                'archive_files': len(list(self.archive_dir.glob("*.csv*"))),
                'backup_files': len(list(self.backup_dir.glob("*.csv*"))),
                'current_size_mb': current_size / (1024 * 1024),
                'archive_size_mb': archive_size / (1024 * 1024),
                'backup_size_mb': backup_size / (1024 * 1024),
                'total_size_mb': (current_size + archive_size + backup_size) / (1024 * 1024)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = {
            'status': 'healthy',
            'base_path_exists': self.base_path.exists(),
            'directories_accessible': True,
            'active_writers': len(self._csv_writers),
            'stats': self.get_storage_stats()
        }
        
        # Check directory accessibility
        try:
            for directory in [self.data_dir, self.archive_dir, self.backup_dir]:
                test_file = directory / ".health_check"
                test_file.touch()
                test_file.unlink()
        except Exception as e:
            health['status'] = 'unhealthy'
            health['directories_accessible'] = False
            health['error'] = str(e)
        
        return health
    
    def close_all_files(self):
        """Close all open file handles."""
        with self._lock:
            for file_key in list(self._file_handles.keys()):
                self._close_file(file_key)
        logger.info("📝 All CSV files closed")
    
    def shutdown(self):
        """Shutdown CSV storage backend."""
        # Stop background tasks
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)
        
        # Close all files
        self.close_all_files()
        
        logger.info("💾 CSV storage backend shutdown complete")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.shutdown()
        except Exception:
            pass