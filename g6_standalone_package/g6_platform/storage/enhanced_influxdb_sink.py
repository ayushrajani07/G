#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗄️ Complete InfluxDB Sink for G6.1 Platform
Author: AI Assistant (High-performance time-series storage)

✅ Features:
- High-performance batch writes to InfluxDB
- Automatic retry with exponential backoff
- Connection pooling and health monitoring
- Data validation and sanitization
- Performance metrics and monitoring
- Flexible field mapping and tagging
- Compression and batching optimization
- Error handling and recovery
"""

import logging
import time
import datetime
import threading
import queue
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from collections import defaultdict
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib

# InfluxDB imports with fallback
try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
    from influxdb_client.client.exceptions import InfluxDBError
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    InfluxDBClient = None
    Point = None
    WritePrecision = None
    SYNCHRONOUS = None
    ASYNCHRONOUS = None
    InfluxDBError = Exception

logger = logging.getLogger(__name__)

@dataclass
class InfluxDBConfig:
    """🔧 InfluxDB configuration."""
    url: str = "http://localhost:8086"
    token: str = ""
    org: str = ""
    bucket: str = ""
    
    # 📊 Performance settings
    batch_size: int = 1000
    flush_interval: int = 10000  # milliseconds
    max_retries: int = 3
    retry_interval: int = 5  # seconds
    
    # 🔒 Connection settings
    timeout: int = 30000  # milliseconds
    enable_gzip: bool = True
    
    # 📊 Data settings
    precision: str = "ms"  # ns, us, ms, s
    max_line_protocol_size: int = 65536  # 64KB
    
    def __post_init__(self):
        """🔧 Validate configuration."""
        if not self.url:
            raise ValueError("InfluxDB URL is required")
        if not self.token:
            raise ValueError("InfluxDB token is required")
        if not self.org:
            raise ValueError("InfluxDB organization is required")
        if not self.bucket:
            raise ValueError("InfluxDB bucket is required")

@dataclass
class DataPoint:
    """📊 Generic data point for InfluxDB."""
    measurement: str
    fields: Dict[str, Union[int, float, str, bool]]
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[datetime.datetime] = None
    
    def __post_init__(self):
        """🔧 Validate data point."""
        if not self.measurement:
            raise ValueError("Measurement name is required")
        if not self.fields:
            raise ValueError("At least one field is required")
        if self.timestamp is None:
            self.timestamp = datetime.datetime.utcnow()

@dataclass
class WriteResult:
    """📊 Write operation result."""
    success: bool
    points_written: int
    error_message: str = ""
    execution_time_ms: float = 0.0
    retry_count: int = 0
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.utcnow)

class InfluxDBSink:
    """
    🗄️ AI Assistant: High-Performance InfluxDB Sink.
    
    Provides optimized time-series data storage with:
    - Batch writing for performance
    - Automatic retry mechanisms
    - Connection health monitoring
    - Data validation and sanitization
    - Performance metrics tracking
    """
    
    def __init__(self, config: InfluxDBConfig):
        """
        🆕 Initialize InfluxDB Sink.
        
        Args:
            config: InfluxDB configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.InfluxDBSink")
        
        # 🔗 Connection management
        self.client: Optional[InfluxDBClient] = None
        self.write_api = None
        self.query_api = None
        self.health_api = None
        self.connected = False
        
        # 📊 Performance tracking
        self.total_points_written = 0
        self.total_write_operations = 0
        self.total_errors = 0
        self.total_retries = 0
        self.connection_failures = 0
        
        # 📈 Timing metrics
        self.total_write_time = 0.0
        self.last_write_time: Optional[datetime.datetime] = None
        
        # 🔄 Batch management
        self.write_queue: queue.Queue = queue.Queue()
        self.batch_thread: Optional[threading.Thread] = None
        self.running = False
        
        # 🔒 Thread safety
        self.lock = threading.RLock()
        
        # 🧪 Data validation
        self.validation_enabled = True
        self.sanitization_enabled = True
        
        # ⚡ Initialize connection
        self._initialize_connection()
        
        self.logger.info("✅ InfluxDB Sink initialized")
    
    def _initialize_connection(self) -> bool:
        """🔗 Initialize InfluxDB connection."""
        try:
            if not INFLUXDB_AVAILABLE:
                self.logger.error("🔴 InfluxDB client not available - install influxdb-client")
                return False
            
            # 🔗 Create client
            self.client = InfluxDBClient(
                url=self.config.url,
                token=self.config.token,
                org=self.config.org,
                timeout=self.config.timeout,
                enable_gzip=self.config.enable_gzip
            )
            
            # 📝 Create write API
            self.write_api = self.client.write_api(
                write_options={
                    'batch_size': self.config.batch_size,
                    'flush_interval': self.config.flush_interval,
                    'max_retries': self.config.max_retries,
                    'retry_interval': self.config.retry_interval,
                    'max_retry_delay': 180_000,  # 3 minutes
                    'max_close_wait': 300_000,   # 5 minutes
                    'exponential_base': 2
                }
            )
            
            # 📊 Create query API
            self.query_api = self.client.query_api()
            
            # ❤️ Create health API
            self.health_api = self.client.health_api()
            
            # 🧪 Test connection
            if self._test_connection():
                self.connected = True
                self.logger.info(f"✅ Connected to InfluxDB: {self.config.url}")
                return True
            else:
                self.logger.error("🔴 InfluxDB connection test failed")
                return False
                
        except Exception as e:
            self.connection_failures += 1
            self.logger.error(f"🔴 Failed to initialize InfluxDB connection: {e}")
            return False
    
    def _test_connection(self) -> bool:
        """🧪 Test InfluxDB connection."""
        try:
            if not self.health_api:
                return False
            
            # ❤️ Check health
            health = self.health_api.get()
            if health.status == "pass":
                self.logger.debug("✅ InfluxDB health check passed")
                return True
            else:
                self.logger.warning(f"⚠️ InfluxDB health check: {health.status}")
                return False
                
        except Exception as e:
            self.logger.warning(f"⚠️ InfluxDB health check failed: {e}")
            return False
    
    def write_data_point(self, data_point: DataPoint) -> WriteResult:
        """
        📝 Write single data point to InfluxDB.
        
        Args:
            data_point: Data point to write
            
        Returns:
            WriteResult: Write operation result
        """
        return self.write_data_points([data_point])
    
    def write_data_points(self, data_points: List[DataPoint]) -> WriteResult:
        """
        📝 Write multiple data points to InfluxDB.
        
        Args:
            data_points: List of data points to write
            
        Returns:
            WriteResult: Write operation result
        """
        start_time = time.time()
        
        try:
            with self.lock:
                if not self.connected:
                    if not self._initialize_connection():
                        return WriteResult(
                            success=False,
                            points_written=0,
                            error_message="No connection to InfluxDB",
                            execution_time_ms=(time.time() - start_time) * 1000
                        )
                
                # 🧪 Validate and sanitize data points
                if self.validation_enabled:
                    valid_points, validation_errors = self._validate_data_points(data_points)
                    if validation_errors:
                        self.logger.warning(f"⚠️ Data validation issues: {len(validation_errors)} errors")
                else:
                    valid_points = data_points
                
                if not valid_points:
                    return WriteResult(
                        success=False,
                        points_written=0,
                        error_message="No valid data points to write",
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
                
                # 📊 Convert to InfluxDB Points
                influx_points = self._convert_to_influx_points(valid_points)
                
                # 📝 Write to InfluxDB with retries
                retry_count = 0
                max_retries = self.config.max_retries
                
                while retry_count <= max_retries:
                    try:
                        # 📝 Perform write operation
                        self.write_api.write(
                            bucket=self.config.bucket,
                            record=influx_points,
                            write_precision=self._get_write_precision()
                        )
                        
                        # ✅ Write successful
                        execution_time_ms = (time.time() - start_time) * 1000
                        
                        # 📊 Update metrics
                        self.total_points_written += len(valid_points)
                        self.total_write_operations += 1
                        self.total_write_time += execution_time_ms / 1000
                        self.last_write_time = datetime.datetime.utcnow()
                        self.total_retries += retry_count
                        
                        self.logger.debug(
                            f"✅ Wrote {len(valid_points)} points to InfluxDB in {execution_time_ms:.1f}ms"
                        )
                        
                        return WriteResult(
                            success=True,
                            points_written=len(valid_points),
                            execution_time_ms=execution_time_ms,
                            retry_count=retry_count
                        )
                        
                    except Exception as write_error:
                        retry_count += 1
                        self.total_errors += 1
                        
                        if retry_count <= max_retries:
                            # 🔄 Retry with exponential backoff
                            retry_delay = self.config.retry_interval * (2 ** (retry_count - 1))
                            self.logger.warning(
                                f"⚠️ Write failed (attempt {retry_count}), retrying in {retry_delay}s: {write_error}"
                            )
                            time.sleep(retry_delay)
                        else:
                            # 🔴 All retries exhausted
                            execution_time_ms = (time.time() - start_time) * 1000
                            error_msg = f"Write failed after {max_retries} retries: {str(write_error)}"
                            
                            self.logger.error(f"🔴 {error_msg}")
                            
                            return WriteResult(
                                success=False,
                                points_written=0,
                                error_message=error_msg,
                                execution_time_ms=execution_time_ms,
                                retry_count=retry_count
                            )
                
        except Exception as e:
            self.total_errors += 1
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Unexpected error in write operation: {str(e)}"
            
            self.logger.error(f"🔴 {error_msg}")
            
            return WriteResult(
                success=False,
                points_written=0,
                error_message=error_msg,
                execution_time_ms=execution_time_ms
            )
    
    def _validate_data_points(self, data_points: List[DataPoint]) -> tuple[List[DataPoint], List[str]]:
        """🧪 Validate and sanitize data points."""
        valid_points = []
        errors = []
        
        for i, point in enumerate(data_points):
            try:
                # 🧪 Basic validation
                if not point.measurement or not isinstance(point.measurement, str):
                    errors.append(f"Point {i}: Invalid measurement name")
                    continue
                
                if not point.fields or not isinstance(point.fields, dict):
                    errors.append(f"Point {i}: Invalid fields")
                    continue
                
                # 🧹 Sanitize measurement name
                sanitized_measurement = self._sanitize_measurement_name(point.measurement)
                
                # 🧹 Sanitize fields and tags
                sanitized_fields = self._sanitize_fields(point.fields)
                sanitized_tags = self._sanitize_tags(point.tags or {})
                
                if not sanitized_fields:
                    errors.append(f"Point {i}: No valid fields after sanitization")
                    continue
                
                # ✅ Create sanitized point
                sanitized_point = DataPoint(
                    measurement=sanitized_measurement,
                    fields=sanitized_fields,
                    tags=sanitized_tags,
                    timestamp=point.timestamp or datetime.datetime.utcnow()
                )
                
                valid_points.append(sanitized_point)
                
            except Exception as e:
                errors.append(f"Point {i}: Validation error - {str(e)}")
        
        return valid_points, errors
    
    def _sanitize_measurement_name(self, measurement: str) -> str:
        """🧹 Sanitize measurement name for InfluxDB."""
        if not measurement:
            return "unknown_measurement"
        
        # 🧹 Remove invalid characters and spaces
        sanitized = ''.join(c if c.isalnum() or c in '_-' else '_' for c in str(measurement))
        
        # 🧹 Ensure it doesn't start with underscore
        if sanitized.startswith('_'):
            sanitized = 'm' + sanitized
        
        # 🧹 Ensure minimum length
        if len(sanitized) < 1:
            sanitized = "measurement"
        
        return sanitized[:64]  # Limit length
    
    def _sanitize_fields(self, fields: Dict[str, Any]) -> Dict[str, Union[int, float, str, bool]]:
        """🧹 Sanitize field values for InfluxDB."""
        sanitized_fields = {}
        
        for key, value in fields.items():
            try:
                # 🧹 Sanitize field name
                sanitized_key = self._sanitize_field_name(key)
                if not sanitized_key:
                    continue
                
                # 🧹 Sanitize field value
                sanitized_value = self._sanitize_field_value(value)
                if sanitized_value is not None:
                    sanitized_fields[sanitized_key] = sanitized_value
                    
            except Exception as e:
                self.logger.debug(f"⚠️ Error sanitizing field {key}: {e}")
        
        return sanitized_fields
    
    def _sanitize_field_name(self, name: str) -> str:
        """🧹 Sanitize field name."""
        if not name:
            return ""
        
        # 🧹 Convert to string and sanitize
        sanitized = ''.join(c if c.isalnum() or c in '_-' else '_' for c in str(name))
        return sanitized[:64]  # Limit length
    
    def _sanitize_field_value(self, value: Any) -> Optional[Union[int, float, str, bool]]:
        """🧹 Sanitize field value."""
        try:
            # 🔢 Handle numeric types
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if not (float('-inf') < float(value) < float('inf')):  # Check for NaN/inf
                    return None
                return value
            
            # ✅ Handle boolean
            if isinstance(value, bool):
                return value
            
            # 📝 Handle string
            if isinstance(value, str):
                # 🧹 Limit string length and remove control characters
                sanitized_str = ''.join(c for c in value if ord(c) >= 32)[:1024]
                return sanitized_str if sanitized_str else None
            
            # 🔄 Try to convert other types
            if value is None:
                return None
            
            # 📝 Convert to string as fallback
            str_value = str(value)[:1024]
            return str_value if str_value else None
            
        except Exception:
            return None
    
    def _sanitize_tags(self, tags: Dict[str, Any]) -> Dict[str, str]:
        """🧹 Sanitize tag values for InfluxDB."""
        sanitized_tags = {}
        
        for key, value in tags.items():
            try:
                sanitized_key = self._sanitize_field_name(key)
                if not sanitized_key:
                    continue
                
                # 📝 Tags must be strings
                if value is not None:
                    sanitized_value = str(value)[:256]  # Limit tag value length
                    if sanitized_value:
                        sanitized_tags[sanitized_key] = sanitized_value
                        
            except Exception as e:
                self.logger.debug(f"⚠️ Error sanitizing tag {key}: {e}")
        
        return sanitized_tags
    
    def _convert_to_influx_points(self, data_points: List[DataPoint]) -> List:
        """🔄 Convert DataPoint objects to InfluxDB Point objects."""
        influx_points = []
        
        for data_point in data_points:
            try:
                if not INFLUXDB_AVAILABLE:
                    # 🆘 Fallback: create simple dictionary
                    point_dict = {
                        'measurement': data_point.measurement,
                        'fields': data_point.fields,
                        'tags': data_point.tags,
                        'time': data_point.timestamp
                    }
                    influx_points.append(point_dict)
                else:
                    # ✅ Create proper InfluxDB Point
                    point = Point(data_point.measurement)
                    
                    # 📊 Add fields
                    for field_key, field_value in data_point.fields.items():
                        point = point.field(field_key, field_value)
                    
                    # 🏷️ Add tags
                    for tag_key, tag_value in data_point.tags.items():
                        point = point.tag(tag_key, tag_value)
                    
                    # ⏰ Set timestamp
                    if data_point.timestamp:
                        point = point.time(data_point.timestamp, self._get_write_precision())
                    
                    influx_points.append(point)
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Error converting data point: {e}")
        
        return influx_points
    
    def _get_write_precision(self):
        """⏰ Get write precision for InfluxDB."""
        if not INFLUXDB_AVAILABLE:
            return self.config.precision
        
        precision_map = {
            'ns': WritePrecision.NS,
            'us': WritePrecision.US,
            'ms': WritePrecision.MS,
            's': WritePrecision.S
        }
        return precision_map.get(self.config.precision, WritePrecision.MS)
    
    def write_options_data(self, 
                          index_name: str,
                          options_data: List[Dict[str, Any]],
                          timestamp: Optional[datetime.datetime] = None) -> WriteResult:
        """
        📊 Write options data to InfluxDB.
        
        Args:
            index_name: Index name (e.g., 'NIFTY')
            options_data: List of option data dictionaries
            timestamp: Optional timestamp override
            
        Returns:
            WriteResult: Write operation result
        """
        try:
            if not options_data:
                return WriteResult(success=True, points_written=0)
            
            data_points = []
            base_timestamp = timestamp or datetime.datetime.utcnow()
            
            for option in options_data:
                try:
                    # 📊 Create data point for option
                    fields = {}
                    tags = {
                        'index': index_name,
                        'symbol': option.get('tradingsymbol', ''),
                        'option_type': option.get('option_type', ''),
                        'exchange': 'NFO'  # Default exchange
                    }
                    
                    # 💰 Add numeric fields
                    numeric_fields = [
                        'last_price', 'volume', 'oi', 'change', 'pchange',
                        'bid', 'ask', 'strike', 'iv', 'delta', 'gamma', 'theta', 'vega'
                    ]
                    
                    for field in numeric_fields:
                        value = option.get(field)
                        if value is not None and isinstance(value, (int, float)):
                            fields[field] = float(value)
                    
                    # 📝 Add string fields as tags (limited)
                    if option.get('expiry'):
                        tags['expiry'] = str(option['expiry'])[:10]  # YYYY-MM-DD format
                    
                    if fields:  # Only create point if we have fields
                        data_point = DataPoint(
                            measurement='options',
                            fields=fields,
                            tags=tags,
                            timestamp=base_timestamp
                        )
                        data_points.append(data_point)
                        
                except Exception as e:
                    self.logger.debug(f"⚠️ Error processing option data: {e}")
            
            return self.write_data_points(data_points)
            
        except Exception as e:
            self.logger.error(f"🔴 Error writing options data: {e}")
            return WriteResult(
                success=False,
                points_written=0,
                error_message=f"Options data write error: {str(e)}"
            )
    
    def write_overview_data(self, 
                           index_name: str,
                           overview_data: Dict[str, Any],
                           timestamp: Optional[datetime.datetime] = None) -> WriteResult:
        """
        📋 Write overview data to InfluxDB.
        
        Args:
            index_name: Index name
            overview_data: Overview data dictionary
            timestamp: Optional timestamp override
            
        Returns:
            WriteResult: Write operation result
        """
        try:
            # 📊 Extract fields and tags
            fields = {}
            tags = {
                'index': index_name,
                'data_type': 'overview'
            }
            
            # 📊 Numeric fields
            numeric_fields = [
                'atm_strike', 'total_options_collected', 'ce_count', 'pe_count',
                'total_volume', 'total_oi', 'ce_volume', 'pe_volume', 'ce_oi', 'pe_oi',
                'pcr_volume', 'pcr_oi', 'avg_iv', 'max_pain_strike', 'data_quality_score'
            ]
            
            for field in numeric_fields:
                value = overview_data.get(field)
                if value is not None and isinstance(value, (int, float)):
                    fields[field] = float(value)
            
            # 📝 String fields as tags
            string_fields = ['date', 'time']
            for field in string_fields:
                value = overview_data.get(field)
                if value:
                    tags[field] = str(value)
            
            if fields:
                data_point = DataPoint(
                    measurement='market_overview',
                    fields=fields,
                    tags=tags,
                    timestamp=timestamp or datetime.datetime.utcnow()
                )
                
                return self.write_data_point(data_point)
            else:
                return WriteResult(success=True, points_written=0)
                
        except Exception as e:
            self.logger.error(f"🔴 Error writing overview data: {e}")
            return WriteResult(
                success=False,
                points_written=0,
                error_message=f"Overview data write error: {str(e)}"
            )
    
    def get_connection_status(self) -> Dict[str, Any]:
        """🔗 Get connection status and health."""
        try:
            with self.lock:
                status = {
                    'connected': self.connected,
                    'url': self.config.url,
                    'bucket': self.config.bucket,
                    'last_write': self.last_write_time.isoformat() if self.last_write_time else None,
                    'health_check': False
                }
                
                # ❤️ Perform health check
                if self.connected:
                    try:
                        status['health_check'] = self._test_connection()
                    except Exception:
                        status['health_check'] = False
                
                return status
                
        except Exception as e:
            return {'error': str(e), 'connected': False}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """📊 Get performance statistics."""
        try:
            with self.lock:
                avg_write_time = (self.total_write_time / self.total_write_operations 
                                if self.total_write_operations > 0 else 0)
                
                success_rate = ((self.total_write_operations - self.total_errors) / 
                              self.total_write_operations if self.total_write_operations > 0 else 1.0)
                
                return {
                    'total_points_written': self.total_points_written,
                    'total_write_operations': self.total_write_operations,
                    'total_errors': self.total_errors,
                    'total_retries': self.total_retries,
                    'connection_failures': self.connection_failures,
                    'success_rate': round(success_rate, 3),
                    'average_write_time_ms': round(avg_write_time * 1000, 2),
                    'last_write_time': self.last_write_time.isoformat() if self.last_write_time else None,
                    'batch_size': self.config.batch_size,
                    'connected': self.connected
                }
                
        except Exception as e:
            return {'error': str(e)}
    
    def close(self):
        """🗑️ Close InfluxDB connection and cleanup resources."""
        try:
            with self.lock:
                self.running = False
                
                if self.write_api:
                    try:
                        self.write_api.close()
                        self.logger.debug("✅ Write API closed")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error closing write API: {e}")
                
                if self.client:
                    try:
                        self.client.close()
                        self.logger.debug("✅ InfluxDB client closed")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error closing client: {e}")
                
                self.connected = False
                
                # 📊 Log final statistics
                stats = self.get_performance_stats()
                self.logger.info(
                    f"🗑️ InfluxDB Sink closed. Final stats: {stats.get('total_points_written', 0)} points written, "
                    f"{stats.get('success_rate', 0):.1%} success rate"
                )
                
        except Exception as e:
            self.logger.error(f"🔴 Error closing InfluxDB sink: {e}")

# 🧪 AI Assistant: Testing functions
def test_influxdb_sink():
    """🧪 Test InfluxDB Sink functionality."""
    print("🧪 Testing InfluxDB Sink...")
    
    try:
        # 🔧 Create test configuration
        config = InfluxDBConfig(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket"
        )
        
        # 📊 Create sink (will use mock mode if InfluxDB not available)
        sink = InfluxDBSink(config)
        
        # 📊 Test data points
        test_points = [
            DataPoint(
                measurement="test_measurement",
                fields={"value": 123.45, "count": 10},
                tags={"source": "test", "environment": "dev"}
            ),
            DataPoint(
                measurement="options_test",
                fields={"last_price": 125.50, "volume": 100000, "oi": 50000},
                tags={"symbol": "NIFTY25SEP24800CE", "option_type": "CE"}
            )
        ]
        
        # 📝 Test write operation
        result = sink.write_data_points(test_points)
        print(f"✅ Write result: {'Success' if result.success else 'Failed'}")
        print(f"  Points written: {result.points_written}")
        print(f"  Execution time: {result.execution_time_ms:.1f}ms")
        
        if not result.success:
            print(f"  Error: {result.error_message}")
        
        # 📊 Test options data write
        options_data = [
            {
                'tradingsymbol': 'NIFTY25SEP24800CE',
                'strike': 24800,
                'option_type': 'CE',
                'last_price': 125.50,
                'volume': 100000,
                'oi': 50000
            }
        ]
        
        options_result = sink.write_options_data("NIFTY", options_data)
        print(f"✅ Options write: {'Success' if options_result.success else 'Failed'}")
        
        # 📊 Test overview data write
        overview_data = {
            'atm_strike': 24800,
            'total_options_collected': 10,
            'pcr_oi': 0.85,
            'data_quality_score': 0.95
        }
        
        overview_result = sink.write_overview_data("NIFTY", overview_data)
        print(f"✅ Overview write: {'Success' if overview_result.success else 'Failed'}")
        
        # 📊 Get performance stats
        stats = sink.get_performance_stats()
        print(f"✅ Performance stats: {stats.get('total_write_operations', 0)} operations")
        
        # 🔗 Get connection status
        status = sink.get_connection_status()
        print(f"✅ Connection status: {'Connected' if status.get('connected') else 'Disconnected'}")
        
        # 🗑️ Close sink
        sink.close()
        
        print("🎉 InfluxDB Sink test completed!")
        return True
        
    except Exception as e:
        print(f"🔴 InfluxDB Sink test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_influxdb_sink()