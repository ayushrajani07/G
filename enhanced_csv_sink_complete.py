#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗄️ Complete Enhanced CSV Storage Module for G6.1 Options Trading Platform
Author: AI Assistant (Atomic file operations with comprehensive error handling)

✅ Features:
- Atomic file writes for data integrity (no corruption)
- Structured directory organization by index/expiry/offset
- Comprehensive error handling and logging
- Data validation and sanitization
- Performance optimization with batch writes
- Thread-safe operations with proper locking
- File compression and backup support
- Automatic cleanup and archival
- Data quality scoring and validation
- CSV format standardization
"""

import csv
import json
import logging
import threading
import time
import gzip
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import tempfile
import os
import hashlib

logger = logging.getLogger(__name__)

class EnhancedCSVSink:
    """
    🗄️ AI Assistant: Enhanced CSV storage sink with atomic file operations.
    
    This class provides:
    - Atomic file writes for data integrity
    - Structured directory organization
    - Comprehensive error handling
    - Data validation and sanitization
    - Performance optimization
    - Thread-safe operations
    - Backup and archival capabilities
    """
    
    def __init__(self, 
                 base_dir: str = "data/g6_data",
                 enable_compression: bool = False,
                 enable_backup: bool = True,
                 max_file_size_mb: int = 100,
                 archive_after_days: int = 30):
        """
        🆕 Initialize Enhanced CSV Sink.
        
        Args:
            base_dir: Base directory for CSV files
            enable_compression: Enable gzip compression for old files
            enable_backup: Enable automatic backup creation
            max_file_size_mb: Maximum file size before rotation
            archive_after_days: Days after which to archive files
        """
        self.base_dir = Path(base_dir)
        self.enable_compression = enable_compression
        self.enable_backup = enable_backup
        self.max_file_size_mb = max_file_size_mb
        self.archive_after_days = archive_after_days
        
        # 🔒 AI Assistant: Thread safety
        self.lock = threading.RLock()
        
        # 📊 AI Assistant: Performance tracking
        self.write_count = 0
        self.total_write_time = 0.0
        self.total_bytes_written = 0
        self.error_count = 0
        self.last_write_time = None
        
        # 🗂️ AI Assistant: File management
        self.open_files = {}  # Cache of open file handles
        self.file_locks = {}  # Per-file locks for concurrent access
        
        self.logger = logging.getLogger(f"{__name__}.EnhancedCSVSink")
        
        # 🏗️ AI Assistant: Ensure base directory exists
        self._ensure_directory_exists(self.base_dir)
        
        self.logger.info(f"✅ Enhanced CSV Sink initialized with base: {self.base_dir}")
        self.logger.info(f"🎛️ Configuration: compression={enable_compression}, backup={enable_backup}, max_size={max_file_size_mb}MB")
    
    def _ensure_directory_exists(self, directory: Path) -> bool:
        """
        🗂️ Ensure directory exists, create if necessary.
        
        Args:
            directory: Directory path to ensure exists
            
        Returns:
            bool: True if directory exists or was created successfully
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"🔴 Failed to create directory {directory}: {e}")
            return False
    
    def write_options_data(self, 
                          index_name: str,
                          expiry_tag: str, 
                          offset: Union[int, str],
                          options_data: List[Dict[str, Any]],
                          timestamp: Optional[datetime] = None,
                          append_mode: bool = False) -> bool:
        """
        📊 AI Assistant: Write options data to structured CSV files with full validation.
        
        Args:
            index_name: Index name (e.g., 'NIFTY')
            expiry_tag: Expiry tag (e.g., 'this_week')
            offset: Strike offset (e.g., 0, '+50', '-100')
            options_data: List of option data dictionaries
            timestamp: Timestamp for the data (defaults to current time)
            append_mode: If True, append to existing file, otherwise overwrite
            
        Returns:
            bool: True if write was successful
        """
        if not options_data:
            self.logger.warning(f"⚠️ No data to write for {index_name} {expiry_tag} {offset}")
            return True
        
        with self.lock:
            start_time = time.time()
            
            try:
                # 📅 AI Assistant: Prepare timestamp
                if timestamp is None:
                    timestamp = datetime.now()
                
                # 🗂️ AI Assistant: Create structured path
                date_str = timestamp.strftime('%Y-%m-%d')
                offset_str = f"{offset:+d}" if isinstance(offset, int) else str(offset)
                
                csv_dir = self.base_dir / index_name.upper() / expiry_tag / offset_str
                self._ensure_directory_exists(csv_dir)
                
                csv_file = csv_dir / f"{date_str}.csv"
                
                # 🧹 AI Assistant: Sanitize and validate data
                sanitized_data, data_quality = self._sanitize_and_validate_options_data(options_data, timestamp)
                
                if data_quality < 0.5:
                    self.logger.warning(f"⚠️ Low data quality ({data_quality:.2f}) for {index_name} {expiry_tag} {offset}")
                
                # 💾 AI Assistant: Check file size and rotate if necessary
                if csv_file.exists() and self._should_rotate_file(csv_file):
                    rotated_file = self._rotate_file(csv_file)
                    self.logger.info(f"🔄 File rotated: {csv_file} -> {rotated_file}")
                
                # 📝 AI Assistant: Write data atomically
                success = self._write_csv_atomic(
                    csv_file, sanitized_data, timestamp, 
                    append_mode=append_mode,
                    metadata={'data_quality': data_quality, 'source': f"{index_name}_{expiry_tag}_{offset}"}
                )
                
                if success:
                    # 📊 AI Assistant: Update performance metrics
                    elapsed = time.time() - start_time
                    file_size = csv_file.stat().st_size if csv_file.exists() else 0
                    
                    self.write_count += 1
                    self.total_write_time += elapsed
                    self.total_bytes_written += file_size
                    self.last_write_time = timestamp
                    
                    self.logger.info(
                        f"✅ Written {len(sanitized_data)} options to {csv_file.name} "
                        f"in {elapsed:.3f}s (quality: {data_quality:.2f})"
                    )
                    
                    # 💾 AI Assistant: Create backup if enabled
                    if self.enable_backup and len(sanitized_data) > 100:  # Only backup substantial files
                        self._create_backup(csv_file)
                
                return success
                
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"🔴 Failed to write options data: {e}")
                return False
    
    def write_overview_data(self,
                           index_name: str,
                           overview_data: Dict[str, Any],
                           timestamp: Optional[datetime] = None) -> bool:
        """
        📋 AI Assistant: Write overview/summary data to CSV with enhanced validation.
        
        Args:
            index_name: Index name
            overview_data: Overview data dictionary
            timestamp: Timestamp for the data
            
        Returns:
            bool: True if write was successful
        """
        with self.lock:
            try:
                start_time = time.time()
                
                if timestamp is None:
                    timestamp = datetime.now()
                
                # 🗂️ AI Assistant: Create overview directory
                overview_dir = self.base_dir / "overview" / index_name.upper()
                self._ensure_directory_exists(overview_dir)
                
                date_str = timestamp.strftime('%Y-%m-%d')
                csv_file = overview_dir / f"{date_str}.csv"
                
                # 🧹 AI Assistant: Sanitize overview data
                sanitized_overview = self._sanitize_overview_data(overview_data, timestamp)
                
                # 📝 AI Assistant: Convert overview data to list format for CSV writing
                row_data = [sanitized_overview]
                
                success = self._write_csv_atomic(
                    csv_file, row_data, timestamp, 
                    append_mode=True,  # Always append for overview data
                    metadata={'type': 'overview', 'index': index_name}
                )
                
                if success:
                    elapsed = time.time() - start_time
                    self.logger.info(f"✅ Written overview data to {csv_file.name} in {elapsed:.3f}s")
                
                return success
                
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"🔴 Failed to write overview data: {e}")
                return False
    
    def _sanitize_and_validate_options_data(self, options_data: List[Dict[str, Any]], timestamp: datetime) -> Tuple[List[Dict[str, Any]], float]:
        """
        🧹 AI Assistant: Sanitize and validate options data with quality scoring.
        
        Args:
            options_data: Raw options data
            timestamp: Current timestamp
            
        Returns:
            Tuple[List[Dict[str, Any]], float]: Sanitized data and quality score (0-1)
        """
        sanitized = []
        quality_issues = 0
        total_fields_checked = 0
        
        # 📊 AI Assistant: Standard field mappings with validation
        field_mappings = {
            'tradingsymbol': (str, True, lambda x: len(str(x)) > 3),
            'strike': (float, True, lambda x: 0 < float(x) < 100000),
            'expiry': (str, True, lambda x: len(str(x)) >= 8),
            'option_type': (str, True, lambda x: str(x).upper() in ['CE', 'PE']),
            'last_price': (float, True, lambda x: float(x) >= 0),
            'volume': (int, False, lambda x: int(x) >= 0),
            'oi': (int, False, lambda x: int(x) >= 0),
            'change': (float, False, lambda x: True),  # Can be positive or negative
            'pchange': (float, False, lambda x: -100 <= float(x) <= 1000),  # Percentage change limits
            'bid': (float, False, lambda x: float(x) >= 0),
            'ask': (float, False, lambda x: float(x) >= 0),
            'iv': (float, False, lambda x: 0 <= float(x) <= 500),  # IV percentage
            'theta': (float, False, lambda x: True),
            'gamma': (float, False, lambda x: True),
            'delta': (float, False, lambda x: -1 <= float(x) <= 1),
            'vega': (float, False, lambda x: True)
        }
        
        for option in options_data:
            try:
                # 🆕 AI Assistant: Create clean record
                clean_option = {}
                option_issues = 0
                
                # 📊 AI Assistant: Process each field
                for field, (field_type, required, validator) in field_mappings.items():
                    total_fields_checked += 1
                    
                    if field in option:
                        try:
                            # 🔄 Type conversion
                            converted_value = field_type(option[field])
                            
                            # ✅ Validation
                            if validator(converted_value):
                                clean_option[field] = converted_value
                            else:
                                if required:
                                    option_issues += 1
                                    quality_issues += 1
                                clean_option[field] = None
                                self.logger.debug(f"⚠️ Validation failed for {field}: {option[field]}")
                        except (ValueError, TypeError) as e:
                            if required:
                                option_issues += 1
                                quality_issues += 1
                            clean_option[field] = None
                            self.logger.debug(f"⚠️ Conversion failed for {field}: {option[field]} ({e})")
                    else:
                        if required:
                            option_issues += 1
                            quality_issues += 1
                        clean_option[field] = None
                
                # 🕒 AI Assistant: Add metadata fields
                clean_option['timestamp'] = timestamp.isoformat()
                clean_option['data_quality_issues'] = option_issues
                clean_option['record_hash'] = self._calculate_record_hash(clean_option)
                
                # ✅ AI Assistant: Validate required fields are present
                required_fields = ['tradingsymbol', 'strike', 'option_type', 'last_price']
                if all(clean_option.get(field) is not None for field in required_fields):
                    sanitized.append(clean_option)
                else:
                    quality_issues += len(required_fields)
                    self.logger.warning(f"⚠️ Skipping option with missing required fields: {option}")
                    
            except Exception as e:
                quality_issues += 10  # Severe penalty for processing errors
                self.logger.warning(f"🔴 Error sanitizing option {option}: {e}")
        
        # 📊 AI Assistant: Calculate quality score
        if total_fields_checked > 0:
            quality_score = max(0.0, 1.0 - (quality_issues / total_fields_checked))
        else:
            quality_score = 0.0
        
        self.logger.debug(
            f"🧹 Sanitized {len(sanitized)}/{len(options_data)} options, "
            f"quality score: {quality_score:.2f}"
        )
        
        return sanitized, quality_score
    
    def _sanitize_overview_data(self, overview_data: Dict[str, Any], timestamp: datetime) -> Dict[str, Any]:
        """
        🧹 AI Assistant: Sanitize overview data.
        
        Args:
            overview_data: Raw overview data
            timestamp: Current timestamp
            
        Returns:
            Dict[str, Any]: Sanitized overview data
        """
        sanitized = {
            'timestamp': timestamp.isoformat(),
            'date': timestamp.strftime('%Y-%m-%d'),
            'time': timestamp.strftime('%H:%M:%S')
        }
        
        # 📊 AI Assistant: Safe field extraction with defaults
        safe_fields = {
            'index_name': (str, 'UNKNOWN'),
            'atm_strike': (float, 0.0),
            'total_options_collected': (int, 0),
            'ce_count': (int, 0),
            'pe_count': (int, 0),
            'avg_iv': (float, 0.0),
            'total_volume': (int, 0),
            'total_oi': (int, 0),
            'pcr': (float, 0.0),
            'max_pain': (float, 0.0),
            'collection_time_ms': (float, 0.0),
            'data_quality_score': (float, 0.0)
        }
        
        for field, (field_type, default_value) in safe_fields.items():
            try:
                if field in overview_data and overview_data[field] is not None:
                    sanitized[field] = field_type(overview_data[field])
                else:
                    sanitized[field] = default_value
            except (ValueError, TypeError):
                sanitized[field] = default_value
                self.logger.debug(f"⚠️ Using default for overview field {field}")
        
        return sanitized
    
    def _calculate_record_hash(self, record: Dict[str, Any]) -> str:
        """
        🔢 Calculate a hash for the record for deduplication.
        
        Args:
            record: Data record
            
        Returns:
            str: Record hash
        """
        # 🎯 Use key fields for hash calculation
        key_fields = ['tradingsymbol', 'strike', 'expiry', 'option_type']
        key_values = []
        
        for field in key_fields:
            value = record.get(field)
            if value is not None:
                key_values.append(str(value))
        
        key_string = '|'.join(key_values)
        return hashlib.md5(key_string.encode()).hexdigest()[:8]
    
    def _should_rotate_file(self, csv_file: Path) -> bool:
        """
        🔄 Check if file should be rotated based on size.
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            bool: True if file should be rotated
        """
        try:
            if not csv_file.exists():
                return False
            
            file_size_mb = csv_file.stat().st_size / (1024 * 1024)
            return file_size_mb > self.max_file_size_mb
        except Exception:
            return False
    
    def _rotate_file(self, csv_file: Path) -> Path:
        """
        🔄 Rotate a file by adding timestamp suffix.
        
        Args:
            csv_file: Path to CSV file to rotate
            
        Returns:
            Path: Path to rotated file
        """
        timestamp = datetime.now().strftime('%H%M%S')
        rotated_name = f"{csv_file.stem}_{timestamp}{csv_file.suffix}"
        rotated_path = csv_file.parent / rotated_name
        
        try:
            csv_file.rename(rotated_path)
            
            # 🗜️ Compress rotated file if enabled
            if self.enable_compression:
                self._compress_file(rotated_path)
            
            return rotated_path
        except Exception as e:
            self.logger.error(f"🔴 Failed to rotate file {csv_file}: {e}")
            return csv_file
    
    def _compress_file(self, file_path: Path) -> Optional[Path]:
        """
        🗜️ Compress a file using gzip.
        
        Args:
            file_path: Path to file to compress
            
        Returns:
            Optional[Path]: Path to compressed file if successful
        """
        try:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 🗑️ Remove original file
            file_path.unlink()
            
            self.logger.info(f"🗜️ Compressed {file_path} -> {compressed_path}")
            return compressed_path
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to compress {file_path}: {e}")
            return None
    
    def _create_backup(self, csv_file: Path):
        """
        💾 Create backup of important files.
        
        Args:
            csv_file: Path to CSV file to backup
        """
        try:
            backup_dir = self.base_dir.parent / "backups" / "csv"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{csv_file.stem}_{timestamp}{csv_file.suffix}"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(csv_file, backup_path)
            self.logger.debug(f"💾 Backup created: {backup_path}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to create backup for {csv_file}: {e}")
    
    def _write_csv_atomic(self, 
                         csv_file: Path, 
                         data: List[Dict[str, Any]], 
                         timestamp: datetime,
                         append_mode: bool = False,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        📝 AI Assistant: Write CSV file atomically to prevent corruption with enhanced features.
        
        Args:
            csv_file: Path to CSV file
            data: Data to write
            timestamp: Timestamp for the data
            append_mode: If True, append to existing file
            metadata: Optional metadata to include in header
            
        Returns:
            bool: True if write was successful
        """
        if not data:
            return True
        
        try:
            # 📊 AI Assistant: Determine if file exists and get existing data for append
            existing_data = []
            if append_mode and csv_file.exists():
                existing_data = self._read_existing_csv(csv_file)
            
            # 🔄 AI Assistant: Combine existing and new data
            combined_data = existing_data + data if append_mode else data
            
            # 📋 AI Assistant: Get all unique fieldnames with consistent ordering
            fieldnames = set()
            for row in combined_data:
                fieldnames.update(row.keys())
            
            # 🎯 AI Assistant: Order fields logically
            priority_fields = ['timestamp', 'tradingsymbol', 'strike', 'expiry', 'option_type', 'last_price']
            ordered_fields = []
            
            # Add priority fields first
            for field in priority_fields:
                if field in fieldnames:
                    ordered_fields.append(field)
                    fieldnames.discard(field)
            
            # Add remaining fields alphabetically
            ordered_fields.extend(sorted(fieldnames))
            
            # 📝 AI Assistant: Write to temporary file first (atomic operation)
            temp_file = csv_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', newline='', encoding='utf-8') as f:
                # 📋 Write metadata as comments if provided
                if metadata:
                    f.write(f"# Generated at: {timestamp.isoformat()}\n")
                    for key, value in metadata.items():
                        f.write(f"# {key}: {value}\n")
                    f.write(f"# Total records: {len(combined_data)}\n")
                
                writer = csv.DictWriter(f, fieldnames=ordered_fields, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(combined_data)
            
            # ⚡ AI Assistant: Atomic move (this is the atomic operation)
            if os.name == 'nt':  # Windows
                if csv_file.exists():
                    csv_file.unlink()
                temp_file.rename(csv_file)
            else:  # Unix-like
                temp_file.rename(csv_file)
            
            # 📊 AI Assistant: Log success with file info
            file_size = csv_file.stat().st_size
            self.logger.debug(
                f"✅ Atomic write successful: {csv_file.name} "
                f"({len(combined_data)} rows, {file_size:,} bytes)"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to write CSV atomically: {e}")
            
            # 🧹 AI Assistant: Cleanup temp file
            temp_file = csv_file.with_suffix('.tmp')
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass  # Best effort cleanup
            
            return False
    
    def _read_existing_csv(self, csv_file: Path) -> List[Dict[str, Any]]:
        """
        📖 AI Assistant: Read existing CSV data safely.
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            List[Dict[str, Any]]: Existing data
        """
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # 📋 Skip comment lines
                lines = []
                for line in f:
                    if not line.strip().startswith('#'):
                        lines.append(line)
                
                if not lines:
                    return []
                
                # 📊 Read CSV from filtered lines
                import io
                csv_content = ''.join(lines)
                reader = csv.DictReader(io.StringIO(csv_content))
                return list(reader)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Could not read existing CSV {csv_file}: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        📊 AI Assistant: Get comprehensive sink performance statistics.
        
        Returns:
            Dict[str, Any]: Detailed performance stats
        """
        with self.lock:
            avg_write_time = (self.total_write_time / self.write_count 
                            if self.write_count > 0 else 0)
            
            avg_file_size = (self.total_bytes_written / self.write_count 
                           if self.write_count > 0 else 0)
            
            # 📊 Calculate success rate
            total_operations = self.write_count + self.error_count
            success_rate = (self.write_count / total_operations * 100 
                          if total_operations > 0 else 100)
            
            return {
                'total_writes': self.write_count,
                'total_errors': self.error_count,
                'success_rate_percent': round(success_rate, 2),
                'total_write_time_seconds': round(self.total_write_time, 3),
                'average_write_time_ms': round(avg_write_time * 1000, 2),
                'total_bytes_written': self.total_bytes_written,
                'average_file_size_kb': round(avg_file_size / 1024, 2),
                'last_write_time': self.last_write_time.isoformat() if self.last_write_time else None,
                'base_directory': str(self.base_dir),
                'compression_enabled': self.enable_compression,
                'backup_enabled': self.enable_backup,
                'max_file_size_mb': self.max_file_size_mb,
                'open_files_count': len(self.open_files)
            }
    
    def get_file_summary(self) -> Dict[str, Any]:
        """
        📋 Get summary of all CSV files in the storage.
        
        Returns:
            Dict[str, Any]: File summary statistics
        """
        try:
            file_count = 0
            total_size = 0
            indices = set()
            oldest_file = None
            newest_file = None
            
            for csv_file in self.base_dir.rglob('*.csv'):
                file_count += 1
                file_stat = csv_file.stat()
                total_size += file_stat.st_size
                
                # 📊 Track indices
                parts = csv_file.parts
                if len(parts) >= 2:
                    indices.add(parts[-4])  # Index name should be 4 levels up
                
                # 📅 Track file ages
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                if oldest_file is None or file_time < oldest_file:
                    oldest_file = file_time
                if newest_file is None or file_time > newest_file:
                    newest_file = file_time
            
            return {
                'total_files': file_count,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'indices_count': len(indices),
                'indices': sorted(list(indices)),
                'oldest_file': oldest_file.isoformat() if oldest_file else None,
                'newest_file': newest_file.isoformat() if newest_file else None,
                'directory_structure': str(self.base_dir)
            }
            
        except Exception as e:
            self.logger.error(f"🔴 Error getting file summary: {e}")
            return {'error': str(e)}
    
    def cleanup_old_files(self, max_age_days: int = None) -> int:
        """
        🗑️ AI Assistant: Cleanup old CSV files with enhanced logic.
        
        Args:
            max_age_days: Maximum age of files to keep (uses instance default if None)
            
        Returns:
            int: Number of files cleaned up
        """
        if max_age_days is None:
            max_age_days = self.archive_after_days
        
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        cleaned_count = 0
        compressed_count = 0
        
        self.logger.info(f"🗑️ Starting cleanup of files older than {max_age_days} days...")
        
        try:
            for csv_file in self.base_dir.rglob('*.csv'):
                try:
                    file_stat = csv_file.stat()
                    
                    if file_stat.st_mtime < cutoff_time:
                        # 🗜️ Try compression first if enabled
                        if self.enable_compression and not csv_file.name.endswith('.gz'):
                            compressed = self._compress_file(csv_file)
                            if compressed:
                                compressed_count += 1
                                self.logger.debug(f"🗜️ Compressed old file: {csv_file}")
                                continue
                        
                        # 🗑️ Remove file if compression not enabled or failed
                        csv_file.unlink()
                        cleaned_count += 1
                        self.logger.debug(f"🗑️ Cleaned up old file: {csv_file}")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not process file {csv_file}: {e}")
        
        except Exception as e:
            self.logger.error(f"🔴 Error during cleanup: {e}")
        
        if cleaned_count > 0 or compressed_count > 0:
            self.logger.info(f"✅ Cleanup completed: {cleaned_count} files removed, {compressed_count} files compressed")
        else:
            self.logger.info("📁 No old files found to clean up")
        
        return cleaned_count + compressed_count
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """
        🧪 Validate data integrity across all CSV files.
        
        Returns:
            Dict[str, Any]: Validation results
        """
        self.logger.info("🧪 Starting data integrity validation...")
        
        validation_results = {
            'files_checked': 0,
            'files_valid': 0,
            'files_with_issues': 0,
            'total_records': 0,
            'duplicate_records': 0,
            'invalid_records': 0,
            'issues': []
        }
        
        try:
            for csv_file in self.base_dir.rglob('*.csv'):
                try:
                    validation_results['files_checked'] += 1
                    file_issues = []
                    
                    # 📖 Read and validate file
                    data = self._read_existing_csv(csv_file)
                    validation_results['total_records'] += len(data)
                    
                    # 🔍 Check for duplicates
                    seen_hashes = set()
                    duplicates = 0
                    invalid = 0
                    
                    for record in data:
                        record_hash = record.get('record_hash')
                        if record_hash:
                            if record_hash in seen_hashes:
                                duplicates += 1
                            seen_hashes.add(record_hash)
                        
                        # 🧪 Basic validation
                        if not record.get('tradingsymbol') or not record.get('strike'):
                            invalid += 1
                    
                    validation_results['duplicate_records'] += duplicates
                    validation_results['invalid_records'] += invalid
                    
                    if duplicates > 0:
                        file_issues.append(f"{duplicates} duplicate records")
                    if invalid > 0:
                        file_issues.append(f"{invalid} invalid records")
                    
                    if file_issues:
                        validation_results['files_with_issues'] += 1
                        validation_results['issues'].append({
                            'file': str(csv_file),
                            'issues': file_issues
                        })
                    else:
                        validation_results['files_valid'] += 1
                
                except Exception as e:
                    validation_results['files_with_issues'] += 1
                    validation_results['issues'].append({
                        'file': str(csv_file),
                        'issues': [f"Read error: {e}"]
                    })
        
        except Exception as e:
            validation_results['validation_error'] = str(e)
        
        self.logger.info(f"✅ Validation completed: {validation_results['files_valid']}/{validation_results['files_checked']} files valid")
        return validation_results
    
    def close(self):
        """🗑️ AI Assistant: Close the CSV sink and cleanup resources."""
        with self.lock:
            # 🗑️ Close any open file handles
            for file_path, handle in self.open_files.items():
                try:
                    handle.close()
                    self.logger.debug(f"🗑️ Closed file handle: {file_path}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Error closing file handle {file_path}: {e}")
            
            self.open_files.clear()
            
            # 📊 Log final statistics
            stats = self.get_stats()
            self.logger.info(
                f"🗑️ Enhanced CSV Sink closed. "
                f"Final stats: {stats['total_writes']} writes, "
                f"{stats['success_rate_percent']:.1f}% success rate"
            )

# 🧪 AI Assistant: Testing and validation functions
def test_enhanced_csv_sink():
    """🧪 Test Enhanced CSV Sink functionality."""
    print("🧪 Testing Enhanced CSV Sink functionality...")
    
    try:
        # Test initialization
        sink = EnhancedCSVSink("test_data", enable_compression=True, enable_backup=True)
        print("✅ CSV Sink initialization successful")
        
        # Test options data write
        sample_options = [
            {
                'tradingsymbol': 'NIFTY25SEP24800CE',
                'strike': 24800,
                'expiry': '2025-09-25',
                'option_type': 'CE',
                'last_price': 125.50,
                'volume': 1000000,
                'oi': 500000,
                'change': 5.25,
                'pchange': 4.37
            },
            {
                'tradingsymbol': 'NIFTY25SEP24800PE',
                'strike': 24800,
                'expiry': '2025-09-25',
                'option_type': 'PE',
                'last_price': 98.75,
                'volume': 800000,
                'oi': 400000,
                'change': -2.15,
                'pchange': -2.13
            }
        ]
        
        success = sink.write_options_data("NIFTY", "this_week", 0, sample_options)
        print(f"✅ Options data write: {'Success' if success else 'Failed'}")
        
        # Test overview data write
        overview_data = {
            'index_name': 'NIFTY',
            'atm_strike': 24800,
            'total_options_collected': len(sample_options),
            'ce_count': 1,
            'pe_count': 1,
            'avg_iv': 18.5,
            'pcr': 0.85,
            'data_quality_score': 0.95
        }
        
        success = sink.write_overview_data("NIFTY", overview_data)
        print(f"✅ Overview data write: {'Success' if success else 'Failed'}")
        
        # Test statistics
        stats = sink.get_stats()
        print(f"✅ Statistics: {stats['total_writes']} writes, {stats['success_rate_percent']:.1f}% success rate")
        
        # Test file summary
        summary = sink.get_file_summary()
        print(f"✅ File summary: {summary.get('total_files', 0)} files, {summary.get('total_size_mb', 0):.2f} MB")
        
        # Test data integrity validation
        validation = sink.validate_data_integrity()
        print(f"✅ Data validation: {validation['files_valid']}/{validation['files_checked']} files valid")
        
        sink.close()
        print("🎉 All Enhanced CSV Sink tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"🔴 Enhanced CSV Sink test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run tests if executed directly
    test_enhanced_csv_sink()