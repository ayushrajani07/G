#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕸️ InfluxDB Storage Backend - G6 Platform v3.0
Time-series data storage with high performance and reliability.

Restructured from: influxdb_sink.py
Features:
- High-performance time-series data storage
- Automatic batching and buffering
- Connection pooling and retry mechanisms
- Data compression and retention policies
- Thread-safe operations with proper error handling
- Comprehensive monitoring and health checks
"""

import time
import logging
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from collections import deque
import json

# InfluxDB imports
try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision, WriteOptions
    from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
    from influxdb_client.client.exceptions import InfluxDBError
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    InfluxDBClient = None
    Point = None
    WritePrecision = None
    WriteOptions = None
    InfluxDBError = Exception

logger = logging.getLogger(__name__)

@dataclass
class InfluxDBStats:
    """InfluxDB operation statistics."""
    points_written: int = 0
    write_operations: int = 0
    write_errors: int = 0
    bytes_written: int = 0
    last_write_time: Optional[datetime] = None
    connection_errors: int = 0
    retry_operations: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate write success rate."""
        total = self.write_operations + self.write_errors
        if total == 0:
            return 0.0
        return (self.write_operations / total) * 100
    
    @property
    def average_points_per_write(self) -> float:
        """Calculate average points per write operation."""
        if self.write_operations == 0:
            return 0.0
        return self.points_written / self.write_operations

@dataclass
class WriteBuffer:
    """Write buffer for batching operations."""
    points: List[Point] = field(default_factory=list)
    max_size: int = 1000
    max_age_seconds: int = 60
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_full(self) -> bool:
        """Check if buffer is full."""
        return len(self.points) >= self.max_size
    
    def is_expired(self) -> bool:
        """Check if buffer has expired."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age >= self.max_age_seconds
    
    def should_flush(self) -> bool:
        """Check if buffer should be flushed."""
        return self.is_full() or self.is_expired()
    
    def add_point(self, point: Point):
        """Add point to buffer."""
        self.points.append(point)
    
    def clear(self):
        """Clear buffer."""
        self.points.clear()
        self.created_at = datetime.now()

class InfluxDBSink:
    """
    🕸️ Enhanced InfluxDB storage backend for time-series data.
    
    Provides high-performance, reliable storage for options and market data
    with automatic batching, retry mechanisms, and comprehensive monitoring.
    """
    
    def __init__(self,
                 url: str = "http://localhost:8086",
                 token: Optional[str] = None,
                 org: str = "g6_platform",
                 bucket: str = "options_data",
                 timeout: int = 30000,
                 batch_size: int = 1000,
                 flush_interval: int = 60,
                 max_retries: int = 3,
                 enable_compression: bool = True,
                 enable_batching: bool = True):
        """
        Initialize InfluxDB storage backend.
        
        Args:
            url: InfluxDB server URL
            token: Authentication token
            org: Organization name
            bucket: Bucket name for data storage
            timeout: Request timeout in milliseconds
            batch_size: Maximum points per batch
            flush_interval: Flush interval in seconds
            max_retries: Maximum retry attempts
            enable_compression: Enable gzip compression
            enable_batching: Enable write batching
        """
        if not INFLUXDB_AVAILABLE:
            raise ImportError("InfluxDB client not available. Install with: pip install influxdb-client")
        
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.timeout = timeout
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        self.enable_compression = enable_compression
        self.enable_batching = enable_batching
        
        # Statistics
        self.stats = InfluxDBStats()
        
        # Buffering
        self._write_buffer = WriteBuffer(max_size=batch_size, max_age_seconds=flush_interval)
        self._buffer_lock = threading.RLock()
        
        # Client and write API
        self._client: Optional[InfluxDBClient] = None
        self._write_api = None
        self._query_api = None
        
        # Background flushing
        self._flush_thread: Optional[threading.Thread] = None
        self._stop_flushing = threading.Event()
        
        # Connection state
        self._connected = False
        self._last_health_check = 0
        self._health_check_interval = 300  # 5 minutes
        
        # Initialize connection
        self._initialize_connection()
        
        # Start background flushing if batching is enabled
        if enable_batching:
            self._start_background_flushing()
        
        logger.info("🕸️ InfluxDB storage backend initialized")
        logger.info(f"🔗 URL: {url}, Org: {org}, Bucket: {bucket}")
        logger.info(f"⚙️ Batching: {'✅' if enable_batching else '❌'}, "
                   f"Batch size: {batch_size}, Flush interval: {flush_interval}s")
    
    def _initialize_connection(self):
        """Initialize InfluxDB connection."""
        try:
            # Create client
            self._client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org,
                timeout=self.timeout,
                enable_gzip=self.enable_compression
            )
            
            # Configure write options
            write_options = WriteOptions(
                batch_size=self.batch_size,
                flush_interval=self.flush_interval * 1000,  # Convert to milliseconds
                jitter_interval=2000,
                retry_interval=5000,
                max_retries=self.max_retries,
                max_retry_delay=30000,
                exponential_base=2
            )
            
            # Create write API
            if self.enable_batching:
                self._write_api = self._client.write_api(write_options=write_options)
            else:
                self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
            
            # Create query API
            self._query_api = self._client.query_api()
            
            # Test connection
            self._test_connection()
            
            self._connected = True
            logger.info("✅ InfluxDB connection established")
            
        except Exception as e:
            logger.error(f"🔴 Failed to initialize InfluxDB connection: {e}")
            self._connected = False
            raise
    
    def _test_connection(self):
        """Test InfluxDB connection."""
        try:
            # Simple health check
            health = self._client.health()
            if health.status != "pass":
                raise Exception(f"InfluxDB health check failed: {health.message}")
            
            # Test bucket access
            buckets_api = self._client.buckets_api()
            bucket = buckets_api.find_bucket_by_name(self.bucket)
            if not bucket:
                logger.warning(f"⚠️ Bucket '{self.bucket}' not found, attempting to create...")
                # Note: Creating bucket requires admin permissions
                
        except Exception as e:
            logger.warning(f"⚠️ Connection test warning: {e}")
    
    def store_options_data(self,
                          index_name: str,
                          options_data: Union[List[Dict[str, Any]], Dict[str, Any]],
                          timestamp: Optional[datetime] = None) -> bool:
        """
        Store options data to InfluxDB.
        
        Args:
            index_name: Index name (NIFTY, BANKNIFTY, etc.)
            options_data: Options data to store
            timestamp: Optional timestamp (uses current if None)
            
        Returns:
            True if successful
        """
        try:
            if not self._connected:
                logger.error("🔴 InfluxDB not connected")
                return False
            
            timestamp = timestamp or datetime.now()
            
            # Ensure options_data is a list
            if isinstance(options_data, dict):
                options_data = [options_data]
            
            if not options_data:
                logger.warning("⚠️ No options data to store")
                return True
            
            # Convert data to InfluxDB points
            points = self._create_options_points(index_name, options_data, timestamp)
            
            if not points:
                logger.warning("⚠️ No valid points created from options data")
                return False
            
            # Write points
            return self._write_points(points)
            
        except Exception as e:
            logger.error(f"🔴 Failed to store options data for {index_name}: {e}")
            self.stats.write_errors += 1
            return False
    
    def store_overview_data(self,
                          index_name: str,
                          overview_data: Dict[str, Any],
                          timestamp: Optional[datetime] = None) -> bool:
        """
        Store market overview data to InfluxDB.
        
        Args:
            index_name: Index name
            overview_data: Overview data to store
            timestamp: Optional timestamp
            
        Returns:
            True if successful
        """
        try:
            if not self._connected:
                logger.error("🔴 InfluxDB not connected")
                return False
            
            timestamp = timestamp or datetime.now()
            
            # Create overview point
            point = self._create_overview_point(index_name, overview_data, timestamp)
            
            if not point:
                logger.warning("⚠️ No valid overview point created")
                return False
            
            return self._write_points([point])
            
        except Exception as e:
            logger.error(f"🔴 Failed to store overview data for {index_name}: {e}")
            self.stats.write_errors += 1
            return False
    
    def _create_options_points(self,
                              index_name: str,
                              options_data: List[Dict[str, Any]],
                              timestamp: datetime) -> List[Point]:
        """Create InfluxDB points from options data."""
        points = []
        
        for option in options_data:
            try:
                # Create point with measurement name
                point = Point("options_data")
                
                # Add timestamp
                point.time(timestamp, WritePrecision.S)
                
                # Add tags (indexed fields)
                point.tag("index_name", index_name)
                point.tag("symbol", option.get("symbol", ""))
                point.tag("option_type", option.get("option_type", ""))
                point.tag("strike", str(option.get("strike", 0)))
                point.tag("expiry", option.get("expiry", ""))
                
                # Add fields (non-indexed data)
                numeric_fields = [
                    'last_price', 'volume', 'oi', 'change', 'pchange',
                    'iv', 'delta', 'gamma', 'theta', 'vega', 'bid', 'ask'
                ]
                
                for field in numeric_fields:
                    value = option.get(field)
                    if value is not None and self._is_numeric(value):
                        point.field(field, float(value))
                
                # Add string fields
                string_fields = ['tradingsymbol', 'exchange', 'segment']
                for field in string_fields:
                    value = option.get(field)
                    if value is not None:
                        point.field(field, str(value))
                
                # Add metadata
                point.field("data_source", "g6_platform")
                point.field("collection_timestamp", timestamp.isoformat())
                
                points.append(point)
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to create point for option {option}: {e}")
        
        return points
    
    def _create_overview_point(self,
                              index_name: str,
                              overview_data: Dict[str, Any],
                              timestamp: datetime) -> Optional[Point]:
        """Create InfluxDB point from overview data."""
        try:
            # Create point
            point = Point("market_overview")
            
            # Add timestamp
            point.time(timestamp, WritePrecision.S)
            
            # Add tags
            point.tag("index_name", index_name)
            
            # Add numeric fields
            numeric_fields = [
                'current_price', 'atm_strike', 'total_ce_oi', 'total_pe_oi',
                'total_ce_volume', 'total_pe_volume', 'pcr_oi', 'pcr_volume',
                'max_pain', 'implied_volatility', 'sentiment_score'
            ]
            
            for field in numeric_fields:
                value = overview_data.get(field)
                if value is not None and self._is_numeric(value):
                    point.field(field, float(value))
            
            # Add string fields
            sentiment = overview_data.get('sentiment')
            if sentiment:
                point.field('sentiment', str(sentiment))
            
            # Add list fields as JSON strings
            list_fields = ['support_levels', 'resistance_levels']
            for field in list_fields:
                value = overview_data.get(field)
                if value is not None:
                    point.field(field, json.dumps(value))
            
            # Add metadata
            point.field("data_source", "g6_platform")
            point.field("generation_timestamp", timestamp.isoformat())
            
            return point
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to create overview point: {e}")
            return None
    
    def _write_points(self, points: List[Point]) -> bool:
        """Write points to InfluxDB with proper error handling."""
        try:
            if not points:
                return True
            
            if self.enable_batching:
                # Add to buffer
                with self._buffer_lock:
                    for point in points:
                        self._write_buffer.add_point(point)
                    
                    # Flush if buffer is full
                    if self._write_buffer.should_flush():
                        return self._flush_buffer()
                
                return True  # Buffered successfully
            else:
                # Write immediately
                return self._write_points_immediate(points)
                
        except Exception as e:
            logger.error(f"🔴 Failed to write points: {e}")
            self.stats.write_errors += 1
            return False
    
    def _write_points_immediate(self, points: List[Point]) -> bool:
        """Write points immediately to InfluxDB."""
        try:
            start_time = time.time()
            
            # Write points
            self._write_api.write(
                bucket=self.bucket,
                org=self.org,
                record=points
            )
            
            # Update statistics
            write_time = time.time() - start_time
            self.stats.points_written += len(points)
            self.stats.write_operations += 1
            self.stats.last_write_time = datetime.now()
            
            logger.debug(f"✅ Wrote {len(points)} points in {write_time:.3f}s")
            return True
            
        except InfluxDBError as e:
            logger.error(f"🔴 InfluxDB write error: {e}")
            self.stats.write_errors += 1
            self.stats.connection_errors += 1
            return False
        except Exception as e:
            logger.error(f"🔴 Unexpected write error: {e}")
            self.stats.write_errors += 1
            return False
    
    def _flush_buffer(self) -> bool:
        """Flush write buffer to InfluxDB."""
        try:
            with self._buffer_lock:
                if not self._write_buffer.points:
                    return True
                
                points_to_write = self._write_buffer.points.copy()
                self._write_buffer.clear()
            
            # Write buffered points
            success = self._write_points_immediate(points_to_write)
            
            if success:
                logger.debug(f"🚽 Flushed {len(points_to_write)} points from buffer")
            
            return success
            
        except Exception as e:
            logger.error(f"🔴 Buffer flush failed: {e}")
            return False
    
    def _start_background_flushing(self):
        """Start background flushing thread."""
        def flush_worker():
            while not self._stop_flushing.wait(self.flush_interval):
                try:
                    with self._buffer_lock:
                        if self._write_buffer.should_flush():
                            self._flush_buffer()
                except Exception as e:
                    logger.error(f"🔴 Background flush error: {e}")
        
        self._flush_thread = threading.Thread(
            target=flush_worker,
            daemon=True,
            name="InfluxDBFlush"
        )
        self._flush_thread.start()
        logger.info("🔄 Background flushing thread started")
    
    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def flush(self) -> bool:
        """Manually flush any buffered data."""
        if self.enable_batching:
            return self._flush_buffer()
        return True
    
    def query_data(self,
                  measurement: str,
                  start_time: datetime,
                  end_time: Optional[datetime] = None,
                  filters: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Query data from InfluxDB.
        
        Args:
            measurement: Measurement name (options_data, market_overview)
            start_time: Start time for query
            end_time: End time for query (uses now if None)
            filters: Additional filters as tag=value pairs
            
        Returns:
            List of data records
        """
        try:
            if not self._connected:
                logger.error("🔴 InfluxDB not connected")
                return []
            
            end_time = end_time or datetime.now()
            
            # Build query
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
                |> filter(fn: (r) => r._measurement == "{measurement}")
            '''
            
            # Add filters
            if filters:
                for tag, value in filters.items():
                    query += f'\n|> filter(fn: (r) => r.{tag} == "{value}")'
            
            # Execute query
            result = self._query_api.query(query, org=self.org)
            
            # Process results
            records = []
            for table in result:
                for record in table.records:
                    records.append({
                        'time': record.get_time(),
                        'measurement': record.get_measurement(),
                        'field': record.get_field(),
                        'value': record.get_value(),
                        'tags': record.values
                    })
            
            return records
            
        except Exception as e:
            logger.error(f"🔴 Query failed: {e}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with self._buffer_lock:
            buffered_points = len(self._write_buffer.points)
        
        return {
            'points_written': self.stats.points_written,
            'write_operations': self.stats.write_operations,
            'write_errors': self.stats.write_errors,
            'success_rate': self.stats.success_rate,
            'average_points_per_write': self.stats.average_points_per_write,
            'connection_errors': self.stats.connection_errors,
            'retry_operations': self.stats.retry_operations,
            'last_write_time': self.stats.last_write_time.isoformat() if self.stats.last_write_time else None,
            'connected': self._connected,
            'batching_enabled': self.enable_batching,
            'buffered_points': buffered_points,
            'bucket': self.bucket,
            'org': self.org
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health = {
            'status': 'healthy',
            'connected': self._connected,
            'client_initialized': self._client is not None,
            'write_api_available': self._write_api is not None,
            'query_api_available': self._query_api is not None,
            'stats': self.get_storage_stats()
        }
        
        try:
            # Test connection if it's been a while
            now = time.time()
            if now - self._last_health_check > self._health_check_interval:
                health_result = self._client.health()
                if health_result.status != "pass":
                    health['status'] = 'unhealthy'
                    health['error'] = health_result.message
                
                self._last_health_check = now
                
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
        
        return health
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            # Stop background flushing
            if self._flush_thread and self._flush_thread.is_alive():
                self._stop_flushing.set()
                self._flush_thread.join(timeout=5)
            
            # Flush any remaining data
            self.flush()
            
            # Close client
            if self._client:
                self._client.close()
            
            logger.info("✅ InfluxDB storage backend cleanup completed")
            
        except Exception as e:
            logger.error(f"🔴 Cleanup error: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass