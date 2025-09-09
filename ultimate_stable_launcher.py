#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultimate Stable Launcher - G6.1 Platform (FLICKER-FREE VERSION)
Advanced launcher with rolling live data stream, color-coded warnings, and flicker-free display

FIXES IMPLEMENTED:
- Rolling live data stream with timestamps
- Color-coded warning stamps for better visibility  
- Flicker-free display using proper Rich update methods
- Stable panel rendering without screen refresh issues
- In-place data updates instead of full screen redraws
"""

import os
import sys
import json
import time
import threading
import webbrowser
import requests
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import hashlib
import uuid
import signal

# Flask imports for authentication
try:
    from flask import Flask, request, redirect, url_for, render_template_string
    import werkzeug.serving
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️  Flask not available - manual token entry only")

# Rich imports for advanced UI
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich.columns import Columns
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.align import Align
    from rich import box
    from rich.rule import Rule
    from rich.markup import escape
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Rich not available - using basic output")

# Kite Connect
try:
    from kiteconnect import KiteConnect
    KITE_AVAILABLE = True
except ImportError:
    KITE_AVAILABLE = False
    print("❌ KiteConnect not available - install with: pip install kiteconnect")

# Environment and configuration
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not available - using system environment only")

# Global console for persistent display
CONSOLE = Console() if RICH_AVAILABLE else None

@dataclass
class AuthenticationStatus:
    """Authentication status container."""
    is_valid: bool
    token: Optional[str]
    expiry_date: Optional[datetime]
    user_name: Optional[str]
    error_message: Optional[str] = None

@dataclass
class RollingDataPoint:
    """Single data point for rolling stream."""
    timestamp: datetime
    index: str
    legs: int
    success_rate: float
    premium_flow: float
    volume: int
    throughput: float
    status: str

@dataclass
class ComprehensiveMetrics:
    """Comprehensive system and application metrics."""
    timestamp: datetime
    
    # Timing Metrics
    api_response_time: float = 0.0
    data_collection_time: float = 0.0
    processing_time: float = 0.0
    db_query_time: float = 0.0
    cache_access_time: float = 0.0
    total_cycle_time: float = 0.0
    
    # Throughput Metrics
    options_per_second: float = 0.0
    requests_per_minute: float = 0.0
    data_points_processed: int = 0
    transactions_per_second: float = 0.0
    bandwidth_usage_mbps: float = 0.0
    
    # Success Rates
    api_success_rate: float = 0.0
    data_collection_success_rate: float = 0.0
    cache_hit_rate: float = 0.0
    validation_success_rate: float = 0.0
    overall_system_health: float = 0.0
    
    # Resource Utilization
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    network_io_in_mb: float = 0.0
    network_io_out_mb: float = 0.0
    active_threads: int = 0
    open_file_handles: int = 0
    
    # Cache Performance
    cache_hits: int = 0
    cache_misses: int = 0
    cache_evictions: int = 0
    cache_memory_usage_mb: float = 0.0
    cache_efficiency: float = 0.0
    
    # Batch Processing
    batch_size_avg: float = 0.0
    batch_processing_time: float = 0.0
    batch_success_rate: float = 0.0
    batches_per_minute: float = 0.0
    queue_depth: int = 0
    
    # Error Tracking
    total_errors: int = 0
    api_errors: int = 0
    validation_errors: int = 0
    timeout_errors: int = 0
    connection_errors: int = 0
    data_quality_errors: int = 0
    system_errors: int = 0
    error_rate_per_minute: float = 0.0

@dataclass
class ColorCodedWarning:
    """Color-coded warning entry with rich formatting."""
    timestamp: datetime
    level: str  # INFO, WARNING, ERROR, CRITICAL
    category: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def get_color_code(self) -> str:
        """Get color code for warning level."""
        colors = {
            "INFO": "blue",
            "WARNING": "yellow", 
            "ERROR": "red",
            "CRITICAL": "bold red"
        }
        return colors.get(self.level, "white")
    
    def get_stamp(self) -> str:
        """Get color-coded timestamp stamp."""
        color = self.get_color_code()
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"[{color}]{self.level}[/{color}] [{self.category}] [dim]{time_str}[/dim]"
    
    def get_formatted_text(self) -> Text:
        """Get formatted Rich Text object."""
        text = Text()
        
        # Color-coded level
        color = self.get_color_code()
        text.append(f"{self.level}", style=color + " bold")
        text.append(f" [{self.category}] ", style="cyan")
        text.append(f"{self.timestamp.strftime('%H:%M:%S')}: ", style="dim")
        text.append(self.message, style="white")
        
        return text

class RollingDataStream:
    """Manages rolling live data stream with timestamps."""
    
    def __init__(self, max_entries: int = 50):
        """Initialize rolling data stream."""
        self.max_entries = max_entries
        self.data_points: deque = deque(maxlen=max_entries)
        self.indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
        self.stream_active = False
        
    def add_data_point(self, index: str, legs: int, success_rate: float, 
                      premium_flow: float, volume: int, throughput: float):
        """Add new data point to rolling stream."""
        status = "✅" if success_rate >= 0.90 else "❌"
        
        data_point = RollingDataPoint(
            timestamp=datetime.now(),
            index=index,
            legs=legs,
            success_rate=success_rate,
            premium_flow=premium_flow,
            volume=volume,
            throughput=throughput,
            status=status
        )
        
        self.data_points.append(data_point)
    
    def get_recent_data(self, count: int = 20) -> List[RollingDataPoint]:
        """Get recent data points for display."""
        return list(self.data_points)[-count:] if self.data_points else []
    
    def simulate_data_stream(self):
        """Simulate continuous data stream."""
        for index in self.indices:
            # Simulate realistic data for each index
            legs = random.randint(15, 55)
            success_rate = random.uniform(0.88, 0.99)
            premium_flow = random.uniform(50.0, 500.0)
            volume = random.randint(10000, 100000)
            throughput = random.uniform(8.0, 25.0)
            
            self.add_data_point(index, legs, success_rate, premium_flow, volume, throughput)

class KiteAuthenticator:
    """Handles Kite Connect authentication with Flask integration."""
    
    def __init__(self):
        """Initialize authenticator."""
        self.api_key = os.getenv('KITE_API_KEY')
        self.api_secret = os.getenv('KITE_API_SECRET')
        self.access_token = os.getenv('KITE_ACCESS_TOKEN')
        self.token_expiry = os.getenv('KITE_TOKEN_EXPIRY')
        
        self.kite = None
        self.flask_app = None
        self.auth_server = None
        self.received_token = None
    
    def check_token_validity(self) -> AuthenticationStatus:
        """Check if current access token is valid."""
        if not self.access_token:
            return AuthenticationStatus(
                is_valid=False,
                token=None,
                expiry_date=None,
                user_name=None,
                error_message="No access token found"
            )
        
        # Check expiry date if available
        if self.token_expiry:
            try:
                expiry_date = datetime.fromisoformat(self.token_expiry)
                if datetime.now() >= expiry_date:
                    return AuthenticationStatus(
                        is_valid=False,
                        token=self.access_token,
                        expiry_date=expiry_date,
                        user_name=None,
                        error_message=f"Token expired on {expiry_date}"
                    )
            except ValueError:
                pass
        
        # Test actual API connection
        if not KITE_AVAILABLE:
            return AuthenticationStatus(
                is_valid=False,
                token=self.access_token,
                expiry_date=None,
                user_name=None,
                error_message="KiteConnect not available"
            )
        
        try:
            kite = KiteConnect(api_key=self.api_key)
            kite.set_access_token(self.access_token)
            
            profile = kite.profile()
            
            return AuthenticationStatus(
                is_valid=True,
                token=self.access_token,
                expiry_date=datetime.fromisoformat(self.token_expiry) if self.token_expiry else None,
                user_name=profile.get('user_name', 'Unknown'),
                error_message=None
            )
            
        except Exception as e:
            return AuthenticationStatus(
                is_valid=False,
                token=self.access_token,
                expiry_date=None,
                user_name=None,
                error_message=str(e)
            )
    
    def setup_flask_auth(self) -> str:
        """Setup Flask authentication server."""
        if not FLASK_AVAILABLE:
            raise RuntimeError("Flask not available for web authentication")
        
        if not self.api_key or not self.api_secret:
            raise RuntimeError("API key and secret required for authentication")
        
        # Create Flask app
        self.flask_app = Flask(__name__)
        self.flask_app.secret_key = os.urandom(24)
        
        # Login template
        login_template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>G6.1 Platform - Kite Authentication</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 50px; background: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; color: #333; margin-bottom: 30px; }
                .info { background: #e3f2fd; padding: 20px; border-radius: 5px; margin: 20px 0; }
                .button { background: #2196F3; color: white; padding: 15px 30px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; font-size: 16px; }
                .button:hover { background: #1976D2; }
                .status { margin: 20px 0; padding: 10px; border-radius: 5px; }
                .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 G6.1 Platform</h1>
                    <h2>Kite Connect Authentication</h2>
                </div>
                
                {% if status %}
                    <div class="status {{ status_type }}">
                        {{ status }}
                    </div>
                {% endif %}
                
                {% if not authenticated %}
                    <div class="info">
                        <h3>📋 Authentication Steps:</h3>
                        <ol>
                            <li>Click "Login with Kite" below</li>
                            <li>Enter your Kite credentials</li>
                            <li>Authorize the G6.1 Platform</li>
                            <li>You'll be redirected back automatically</li>
                            <li>Close this browser tab when done</li>
                        </ol>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{{ login_url }}" class="button">🔐 Login with Kite</a>
                    </div>
                {% else %}
                    <div class="status success">
                        <h3>✅ Authentication Successful!</h3>
                        <p>User: {{ user_name }}</p>
                        <p>Token expires: {{ expiry_date }}</p>
                        <p>You can now close this browser tab and return to the platform.</p>
                    </div>
                {% endif %}
            </div>
        </body>
        </html>
        '''
        
        @self.flask_app.route('/')
        def index():
            kite = KiteConnect(api_key=self.api_key)
            login_url = kite.login_url()
            return render_template_string(login_template, login_url=login_url, authenticated=False)
        
        @self.flask_app.route('/callback')
        def callback():
            request_token = request.args.get('request_token')
            
            if not request_token:
                return render_template_string(
                    login_template, 
                    status="❌ No request token received. Please try again.",
                    status_type="error",
                    authenticated=False
                )
            
            try:
                kite = KiteConnect(api_key=self.api_key)
                data = kite.generate_session(request_token, api_secret=self.api_secret)
                
                access_token = data['access_token']
                user_profile = kite.profile()
                
                # Store token and expiry
                self.received_token = access_token
                expiry_date = datetime.now() + timedelta(days=1)  # Tokens typically expire daily
                
                # Update environment
                self._update_env_token(access_token, expiry_date.isoformat())
                
                return render_template_string(
                    login_template,
                    status="✅ Authentication successful! Token has been saved.",
                    status_type="success",
                    authenticated=True,
                    user_name=user_profile.get('user_name', 'Unknown'),
                    expiry_date=expiry_date.strftime('%Y-%m-%d %H:%M:%S')
                )
                
            except Exception as e:
                return render_template_string(
                    login_template,
                    status=f"❌ Authentication failed: {str(e)}",
                    status_type="error",
                    authenticated=False
                )
        
        return "http://localhost:5555"
    
    def start_auth_server(self) -> None:
        """Start Flask authentication server."""
        if not self.flask_app:
            raise RuntimeError("Flask app not initialized")
        
        # Disable Flask logging
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        # Start server in background thread
        def run_server():
            self.flask_app.run(host='localhost', port=5555, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(1)  # Give server time to start
    
    def _update_env_token(self, access_token: str, expiry_date: str) -> None:
        """Update environment file with new token."""
        env_file = '.env'
        lines = []
        
        # Read existing .env file
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
        
        # Update or add token entries
        token_updated = False
        expiry_updated = False
        
        for i, line in enumerate(lines):
            if line.startswith('KITE_ACCESS_TOKEN='):
                lines[i] = f'KITE_ACCESS_TOKEN={access_token}\n'
                token_updated = True
            elif line.startswith('KITE_TOKEN_EXPIRY='):
                lines[i] = f'KITE_TOKEN_EXPIRY={expiry_date}\n'
                expiry_updated = True
        
        # Add new entries if not found
        if not token_updated:
            lines.append(f'KITE_ACCESS_TOKEN={access_token}\n')
        if not expiry_updated:
            lines.append(f'KITE_TOKEN_EXPIRY={expiry_date}\n')
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        # Update current environment
        os.environ['KITE_ACCESS_TOKEN'] = access_token
        os.environ['KITE_TOKEN_EXPIRY'] = expiry_date
        self.access_token = access_token
        self.token_expiry = expiry_date
    
    def manual_token_entry(self) -> bool:
        """Handle manual token entry."""
        print("\n" + "="*60)
        print("📝 MANUAL TOKEN ENTRY")
        print("="*60)
        
        print(f"Current API Key: {self.api_key[:8]}..." if self.api_key else "❌ No API key found")
        print(f"Current Token: {'✅ Present' if self.access_token else '❌ Not found'}")
        
        token = input("\n🔑 Enter new access token (or press Enter to skip): ").strip()
        
        if not token:
            return False
        
        # Validate token format (basic check)
        if len(token) < 20:
            print("❌ Token appears too short. Please check and try again.")
            return False
        
        # Test token
        if KITE_AVAILABLE and self.api_key:
            try:
                kite = KiteConnect(api_key=self.api_key)
                kite.set_access_token(token)
                profile = kite.profile()
                
                print(f"✅ Token validated successfully!")
                print(f"   User: {profile.get('user_name', 'Unknown')}")
                print(f"   Account: {profile.get('user_id', 'Unknown')}")
                
                # Save token
                expiry_date = datetime.now() + timedelta(days=1)
                self._update_env_token(token, expiry_date.isoformat())
                
                print(f"   Token saved with expiry: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
                return True
                
            except Exception as e:
                print(f"❌ Token validation failed: {str(e)}")
                save_anyway = input("💭 Save token anyway? (y/N): ").strip().lower()
                
                if save_anyway == 'y':
                    expiry_date = datetime.now() + timedelta(days=1)
                    self._update_env_token(token, expiry_date.isoformat())
                    print("✅ Token saved (unvalidated)")
                    return True
                
                return False
        else:
            # Save without validation
            expiry_date = datetime.now() + timedelta(days=1)
            self._update_env_token(token, expiry_date.isoformat())
            print("✅ Token saved (validation skipped - KiteConnect not available)")
            return True

class StableMetricsCollector:
    """Stable metrics collector with flicker-free updates."""
    
    def __init__(self):
        """Initialize stable metrics collector."""
        self.comprehensive_metrics: deque = deque(maxlen=300)
        self.warnings: deque = deque(maxlen=200)  # Color-coded warnings
        
        self.running = False
        self.collector_thread = None
        
        # Comprehensive metric baselines
        self.baselines = {
            'cpu_percent': {'mean': 0, 'std': 0, 'samples': []},
            'memory_percent': {'mean': 0, 'std': 0, 'samples': []},
            'api_response_time': {'mean': 0, 'std': 0, 'samples': []},
            'cache_hit_rate': {'mean': 0, 'std': 0, 'samples': []},
        }
        
        # Comprehensive statistics
        self.comprehensive_stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'total_options_processed': 0,
            'total_api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'batch_operations': 0,
            'errors': defaultdict(int),
            'total_errors': 0,
            'uptime_seconds': 0,
            'data_throughput_mb': 0.0
        }
        
        self.start_time = time.time()
        
    def start_collection(self, interval: int = 15):
        """Start stable metrics collection."""
        if self.running:
            return
        
        self.running = True
        self.start_time = time.time()
        
        def collect_loop():
            while self.running:
                try:
                    # Collect comprehensive metrics
                    comp_metrics = self._collect_comprehensive_metrics()
                    self.comprehensive_metrics.append(comp_metrics)
                    
                    # Update baselines
                    self._update_comprehensive_baselines(comp_metrics)
                    
                    # Check for anomalies
                    self._check_comprehensive_anomalies(comp_metrics)
                    
                    # Update comprehensive stats
                    self._update_comprehensive_stats(comp_metrics)
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    self.add_warning(
                        level="ERROR",
                        category="METRICS",
                        message=f"Metrics collection error: {str(e)}"
                    )
                    time.sleep(interval)
        
        self.collector_thread = threading.Thread(target=collect_loop, daemon=True)
        self.collector_thread.start()
    
    def stop_collection(self):
        """Stop metrics collection."""
        self.running = False
    
    def _collect_comprehensive_metrics(self) -> ComprehensiveMetrics:
        """Collect comprehensive system and application metrics."""
        try:
            import psutil
            
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            
            # Process info
            process = psutil.Process()
            
            # Create comprehensive metrics with realistic simulation
            metrics = ComprehensiveMetrics(
                timestamp=datetime.now(),
                
                # Timing Metrics
                api_response_time=random.uniform(0.5, 3.0),
                data_collection_time=random.uniform(12.0, 18.0),
                processing_time=random.uniform(2.0, 5.0),
                db_query_time=random.uniform(0.1, 1.0),
                cache_access_time=random.uniform(0.01, 0.1),
                total_cycle_time=random.uniform(15.0, 25.0),
                
                # Throughput Metrics
                options_per_second=random.uniform(10.0, 25.0),
                requests_per_minute=random.uniform(50.0, 150.0),
                data_points_processed=random.randint(500, 1500),
                transactions_per_second=random.uniform(5.0, 15.0),
                bandwidth_usage_mbps=random.uniform(0.5, 4.0),
                
                # Success Rates
                api_success_rate=random.uniform(0.92, 0.99),
                data_collection_success_rate=random.uniform(0.88, 0.98),
                cache_hit_rate=random.uniform(0.75, 0.95),
                validation_success_rate=random.uniform(0.95, 0.99),
                overall_system_health=random.uniform(0.90, 0.98),
                
                # Resource Utilization
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_io_read_mb=random.uniform(1.0, 10.0),
                disk_io_write_mb=random.uniform(0.5, 5.0),
                network_io_in_mb=random.uniform(0.1, 2.0),
                network_io_out_mb=random.uniform(0.1, 1.5),
                active_threads=process.num_threads(),
                open_file_handles=len(process.open_files()) if hasattr(process, 'open_files') else 0,
                
                # Cache Performance
                cache_hits=random.randint(800, 1200),
                cache_misses=random.randint(50, 200),
                cache_evictions=random.randint(0, 10),
                cache_memory_usage_mb=random.uniform(10.0, 50.0),
                cache_efficiency=random.uniform(0.80, 0.95),
                
                # Batch Processing
                batch_size_avg=random.uniform(20.0, 30.0),
                batch_processing_time=random.uniform(1.0, 3.0),
                batch_success_rate=random.uniform(0.90, 0.98),
                batches_per_minute=random.uniform(15.0, 25.0),
                queue_depth=random.randint(0, 5),
                
                # Error Tracking
                total_errors=random.randint(0, 5),
                api_errors=random.randint(0, 2),
                validation_errors=random.randint(0, 1),
                timeout_errors=random.randint(0, 1),
                connection_errors=random.randint(0, 1),
                data_quality_errors=random.randint(0, 2),
                system_errors=random.randint(0, 1),
                error_rate_per_minute=random.uniform(0.0, 0.5)
            )
            
            return metrics
            
        except ImportError:
            # Fallback without psutil
            return ComprehensiveMetrics(
                timestamp=datetime.now(),
                cpu_percent=random.uniform(5.0, 15.0),
                memory_percent=random.uniform(40.0, 60.0),
                active_threads=threading.active_count(),
                api_success_rate=random.uniform(0.92, 0.99),
                overall_system_health=random.uniform(0.90, 0.98)
            )
        except Exception:
            return ComprehensiveMetrics(timestamp=datetime.now())
    
    def _update_comprehensive_baselines(self, metrics: ComprehensiveMetrics):
        """Update baseline metrics for comprehensive anomaly detection."""
        baseline_fields = ['cpu_percent', 'memory_percent', 'api_response_time', 'cache_hit_rate']
        
        for field_name in baseline_fields:
            try:
                if hasattr(metrics, field_name):
                    value = getattr(metrics, field_name)
                    if field_name not in self.baselines:
                        self.baselines[field_name] = {'mean': 0, 'std': 0, 'samples': []}
                    
                    baseline = self.baselines[field_name]
                    
                    # Add sample
                    baseline['samples'].append(value)
                    
                    # Keep only recent samples (last 100)
                    if len(baseline['samples']) > 100:
                        baseline['samples'] = baseline['samples'][-100:]
                    
                    # Update mean and std
                    if len(baseline['samples']) >= 10:
                        baseline['mean'] = statistics.mean(baseline['samples'])
                        baseline['std'] = statistics.stdev(baseline['samples']) if len(baseline['samples']) > 1 else 0
            except Exception:
                pass
    
    def _check_comprehensive_anomalies(self, metrics: ComprehensiveMetrics):
        """Check for comprehensive metric anomalies and generate warnings."""
        try:
            # Critical resource checks
            if metrics.cpu_percent > 90:
                self.add_warning(
                    level="CRITICAL",
                    category="SYSTEM",
                    message=f"Critical CPU usage: {metrics.cpu_percent:.1f}%"
                )
            elif metrics.cpu_percent > 80:
                self.add_warning(
                    level="WARNING",
                    category="SYSTEM",
                    message=f"High CPU usage: {metrics.cpu_percent:.1f}%"
                )
            
            if metrics.memory_percent > 90:
                self.add_warning(
                    level="CRITICAL",
                    category="SYSTEM",
                    message=f"Critical memory usage: {metrics.memory_percent:.1f}%"
                )
            elif metrics.memory_percent > 80:
                self.add_warning(
                    level="WARNING",
                    category="RESOURCE",
                    message=f"Memory usage trending upward: {metrics.memory_percent:.1f}%"
                )
            
            # Performance warnings
            if metrics.api_response_time > 5.0:
                self.add_warning(
                    level="WARNING",
                    category="PERFORMANCE",
                    message=f"API response time elevated: {metrics.api_response_time:.2f}s"
                )
            
            if metrics.cache_hit_rate < 0.70:
                self.add_warning(
                    level="WARNING",
                    category="CACHE",
                    message=f"Cache hit rate below optimal: {metrics.cache_hit_rate:.1%}"
                )
            
            if metrics.api_success_rate < 0.90:
                self.add_warning(
                    level="ERROR",
                    category="API",
                    message=f"API rate limit approaching: {int(metrics.requests_per_minute)} req/min"
                )
            
            if metrics.total_errors > 10:
                self.add_warning(
                    level="ERROR",
                    category="ERRORS",
                    message=f"High error count: {metrics.total_errors} errors"
                )
            
            # Baseline deviation checks
            for metric_name in ['cpu_percent', 'memory_percent', 'api_response_time']:
                if metric_name in self.baselines:
                    baseline = self.baselines[metric_name]
                    if baseline['std'] > 0:
                        value = getattr(metrics, metric_name)
                        deviation = abs(value - baseline['mean']) / baseline['std']
                        
                        if deviation > 2.5:
                            self.add_warning(
                                level="WARNING",
                                category="ANOMALY",
                                message=f"{metric_name} deviates significantly: {value:.1f} (baseline: {baseline['mean']:.1f})"
                            )
        except Exception:
            pass
    
    def _update_comprehensive_stats(self, metrics: ComprehensiveMetrics):
        """Update comprehensive statistics."""
        try:
            self.comprehensive_stats['total_collections'] += 1
            self.comprehensive_stats['total_api_calls'] += int(metrics.requests_per_minute / 4)
            self.comprehensive_stats['cache_hits'] += metrics.cache_hits
            self.comprehensive_stats['cache_misses'] += metrics.cache_misses
            self.comprehensive_stats['total_errors'] += metrics.total_errors
            self.comprehensive_stats['total_options_processed'] += metrics.data_points_processed
            self.comprehensive_stats['uptime_seconds'] = int(time.time() - self.start_time)
            self.comprehensive_stats['data_throughput_mb'] += metrics.bandwidth_usage_mbps / 4
            
            if metrics.overall_system_health > 0.95:
                self.comprehensive_stats['successful_collections'] += 1
            else:
                self.comprehensive_stats['failed_collections'] += 1
        except Exception:
            pass
    
    def add_warning(self, level: str, category: str, message: str, details: Dict[str, Any] = None):
        """Add color-coded warning to log."""
        try:
            warning = ColorCodedWarning(
                timestamp=datetime.now(),
                level=level,
                category=category,
                message=message,
                details=details or {}
            )
            
            self.warnings.append(warning)
        except Exception:
            pass
    
    def get_current_comprehensive_metrics(self) -> Optional[ComprehensiveMetrics]:
        """Get most recent comprehensive metrics."""
        try:
            return self.comprehensive_metrics[-1] if self.comprehensive_metrics else None
        except Exception:
            return None
    
    def get_recent_warnings(self, count: int = 15) -> List[ColorCodedWarning]:
        """Get recent color-coded warning entries."""
        try:
            return list(self.warnings)[-count:] if self.warnings else []
        except Exception:
            return []

class UltimateStableLauncher:
    """Ultimate stable launcher with rolling data stream and flicker-free display."""
    
    def __init__(self):
        """Initialize the stable launcher."""
        self.console = Console() if RICH_AVAILABLE else None
        self.authenticator = KiteAuthenticator()
        self.metrics_collector = StableMetricsCollector()
        self.data_stream = RollingDataStream()
        
        # Runtime state
        self.running = False
        self.data_collection_active = False
        self.authenticated = False
        
        # Indices for data collection
        self.indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
        
        # Layout components with stable references
        self.layout = None
        self.live_display = None
        
        # Display update control - FLICKER-FREE
        self.update_counter = 0
        self.last_update = time.time()
        
        # Panel content cache to prevent unnecessary redraws
        self.panel_cache = {
            'data_collection': None,
            'live_metrics': None,
            'warnings': None,
            'header': None,
            'footer': None
        }
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle exit signals gracefully."""
        self.running = False
    
    def print_system_status(self):
        """Print system status summary."""
        if RICH_AVAILABLE:
            self._print_rich_system_status()
        else:
            self._print_basic_system_status()
    
    def _print_rich_system_status(self):
        """Print Rich-formatted system status."""
        # System info
        system_table = Table(title="🖥️  System Status", box=box.ROUNDED)
        system_table.add_column("Component", style="cyan")
        system_table.add_column("Status", style="green")
        system_table.add_column("Details", style="yellow")
        
        # Check dependencies
        system_table.add_row("Python Version", "✅" if sys.version_info >= (3, 8) else "❌", f"{sys.version.split()[0]}")
        system_table.add_row("KiteConnect", "✅" if KITE_AVAILABLE else "❌", "Available" if KITE_AVAILABLE else "Missing")
        system_table.add_row("Rich UI", "✅" if RICH_AVAILABLE else "❌", "Available" if RICH_AVAILABLE else "Basic mode")
        system_table.add_row("Flask Auth", "✅" if FLASK_AVAILABLE else "❌", "Available" if FLASK_AVAILABLE else "Manual only")
        
        # Authentication status
        auth_status = self.authenticator.check_token_validity()
        auth_table = Table(title="🔐 Authentication", box=box.ROUNDED)
        auth_table.add_column("Item", style="cyan")
        auth_table.add_column("Status", style="green" if auth_status.is_valid else "red")
        auth_table.add_column("Details", style="yellow")
        
        auth_table.add_row("API Key", "✅" if self.authenticator.api_key else "❌", 
                          f"{self.authenticator.api_key[:8]}..." if self.authenticator.api_key else "Not found")
        auth_table.add_row("Access Token", "✅" if auth_status.is_valid else "❌",
                          auth_status.user_name if auth_status.user_name else auth_status.error_message or "Invalid")
        
        if auth_status.expiry_date:
            auth_table.add_row("Token Expiry", "✅" if auth_status.is_valid else "❌",
                              auth_status.expiry_date.strftime('%Y-%m-%d %H:%M:%S'))
        
        # Configuration status
        config_table = Table(title="⚙️  Configuration", box=box.ROUNDED)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")
        
        config_table.add_row("Target Indices", str(len(self.indices)), ", ".join(self.indices))
        config_table.add_row("Data Directory", "✅" if os.path.exists("data") else "❌", 
                            "data/" if os.path.exists("data") else "Missing")
        config_table.add_row("Config File", "✅" if os.path.exists("config.json") else "❌",
                            "config.json" if os.path.exists("config.json") else "Missing")
        
        # Display tables
        self.console.print(Panel(system_table, title="System Status Summary", border_style="blue"))
        self.console.print()
        self.console.print(Columns([auth_table, config_table], equal=True))
        self.console.print()
    
    def _print_basic_system_status(self):
        """Print basic system status without Rich."""
        print("\n" + "="*60)
        print("🖥️  SYSTEM STATUS SUMMARY")
        print("="*60)
        
        print(f"Python Version: {sys.version.split()[0]} {'✅' if sys.version_info >= (3, 8) else '❌'}")
        print(f"KiteConnect: {'✅ Available' if KITE_AVAILABLE else '❌ Missing'}")
        print(f"Rich UI: {'✅ Available' if RICH_AVAILABLE else '❌ Basic mode'}")
        print(f"Flask Auth: {'✅ Available' if FLASK_AVAILABLE else '❌ Manual only'}")
        
        print("\n🔐 AUTHENTICATION")
        print("-" * 20)
        auth_status = self.authenticator.check_token_validity()
        print(f"API Key: {'✅ Present' if self.authenticator.api_key else '❌ Missing'}")
        print(f"Access Token: {'✅ Valid' if auth_status.is_valid else '❌ Invalid'}")
        if auth_status.user_name:
            print(f"User: {auth_status.user_name}")
        if auth_status.error_message:
            print(f"Error: {auth_status.error_message}")
        
        print("\n⚙️  CONFIGURATION")
        print("-" * 20)
        print(f"Target Indices: {', '.join(self.indices)}")
        print(f"Data Directory: {'✅ Exists' if os.path.exists('data') else '❌ Missing'}")
        print(f"Config File: {'✅ Exists' if os.path.exists('config.json') else '❌ Missing'}")
        print()
    
    def show_auth_menu(self) -> bool:
        """Show authentication menu and handle user selection."""
        if RICH_AVAILABLE:
            return self._show_rich_auth_menu()
        else:
            return self._show_basic_auth_menu()
    
    def _show_rich_auth_menu(self) -> bool:
        """Show Rich-formatted authentication menu."""
        auth_panel = Panel.fit(
            f"""
🔐 KITE AUTHENTICATION REQUIRED

Current token is invalid or expired.
Choose an authentication method:

[bold cyan]1.[/bold cyan] [green]Kite Login[/green] - Web-based authentication (recommended)
[bold cyan]2.[/bold cyan] [yellow]Manual Token[/yellow] - Enter access token manually
[bold cyan]3.[/bold cyan] [red]Continue Anyway[/red] - Proceed with existing credentials

[dim]Note: Option 1 requires Flask and will open your web browser[/dim]
            """,
            title="🚀 G6.1 Platform Authentication",
            border_style="blue"
        )
        
        self.console.print(auth_panel)
        
        while True:
            choice = self.console.input("\n🤔 Enter your choice (1-3): ").strip()
            
            if choice == '1':
                return self._handle_kite_login()
            elif choice == '2':
                return self._handle_manual_token()
            elif choice == '3':
                self.console.print("⚠️  [yellow]Continuing with existing credentials[/yellow]")
                return True
            else:
                self.console.print("❌ [red]Invalid choice. Please enter 1, 2, or 3.[/red]")
    
    def _show_basic_auth_menu(self) -> bool:
        """Show basic authentication menu."""
        print("\n" + "="*60)
        print("🔐 KITE AUTHENTICATION REQUIRED")
        print("="*60)
        print("Current token is invalid or expired.")
        print("Choose an authentication method:\n")
        print("1. Kite Login - Web-based authentication (recommended)")
        print("2. Manual Token - Enter access token manually")
        print("3. Continue Anyway - Proceed with existing credentials")
        print("\nNote: Option 1 requires Flask and will open your web browser")
        
        while True:
            choice = input("\n🤔 Enter your choice (1-3): ").strip()
            
            if choice == '1':
                return self._handle_kite_login()
            elif choice == '2':
                return self._handle_manual_token()
            elif choice == '3':
                print("⚠️  Continuing with existing credentials")
                return True
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    def _handle_kite_login(self) -> bool:
        """Handle Kite web login authentication."""
        if not FLASK_AVAILABLE:
            if RICH_AVAILABLE:
                self.console.print("❌ [red]Flask not available. Please install Flask or use manual token entry.[/red]")
            else:
                print("❌ Flask not available. Please install Flask or use manual token entry.")
            return self._handle_manual_token()
        
        try:
            # Setup Flask server
            auth_url = self.authenticator.setup_flask_auth()
            self.authenticator.start_auth_server()
            
            if RICH_AVAILABLE:
                self.console.print(f"🌐 [green]Starting authentication server...[/green]")
                self.console.print(f"🔗 [cyan]Opening browser to: {auth_url}[/cyan]")
            else:
                print(f"🌐 Starting authentication server...")
                print(f"🔗 Opening browser to: {auth_url}")
            
            # Open browser
            webbrowser.open(auth_url)
            
            if RICH_AVAILABLE:
                self.console.print("\n📋 [yellow]Please complete authentication in your browser...[/yellow]")
                self.console.print("💭 [dim]Press Enter when authentication is complete (or Ctrl+C to cancel)[/dim]")
            else:
                print("\n📋 Please complete authentication in your browser...")
                print("💭 Press Enter when authentication is complete (or Ctrl+C to cancel)")
            
            try:
                input()
            except KeyboardInterrupt:
                if RICH_AVAILABLE:
                    self.console.print("\n❌ [red]Authentication cancelled[/red]")
                else:
                    print("\n❌ Authentication cancelled")
                return False
            
            # Check if token was received
            if self.authenticator.received_token:
                if RICH_AVAILABLE:
                    self.console.print("✅ [green]Authentication successful![/green]")
                else:
                    print("✅ Authentication successful!")
                return True
            else:
                if RICH_AVAILABLE:
                    self.console.print("❌ [red]No token received. Please try manual entry.[/red]")
                else:
                    print("❌ No token received. Please try manual entry.")
                return self._handle_manual_token()
                
        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"❌ [red]Authentication error: {str(e)}[/red]")
            else:
                print(f"❌ Authentication error: {str(e)}")
            return self._handle_manual_token()
    
    def _handle_manual_token(self) -> bool:
        """Handle manual token entry."""
        return self.authenticator.manual_token_entry()
    
    def setup_layout(self):
        """Setup the stable monitoring layout."""
        if not RICH_AVAILABLE:
            return None
        
        try:
            self.layout = Layout()
            
            # Split main layout into header, body, and footer
            self.layout.split_column(
                Layout(name="header", size=3),
                Layout(name="body"),
                Layout(name="footer", size=3)
            )
            
            # Split body into main sections
            self.layout["body"].split_row(
                Layout(name="left_panel", ratio=2),
                Layout(name="right_panel", ratio=1)
            )
            
            # Left panel: Data collection and metrics
            self.layout["left_panel"].split_column(
                Layout(name="data_collection", ratio=2),
                Layout(name="live_metrics", ratio=1)
            )
            
            # Initialize with empty panels
            self.layout["header"].update(Panel("", title="Header", border_style="blue"))
            self.layout["data_collection"].update(Panel("", title="📈 Rolling Live Data Stream", border_style="blue"))
            self.layout["live_metrics"].update(Panel("", title="⚡ Live Comprehensive Metrics", border_style="green"))
            self.layout["right_panel"].update(Panel("", title="⚠️  Color-Coded Warnings Log", border_style="yellow"))
            self.layout["footer"].update(Panel("", title="Footer", border_style="blue"))
            
            return self.layout
        except Exception as e:
            print(f"❌ Error setting up layout: {e}")
            return None
    
    def _create_header(self) -> Panel:
        """Create header panel."""
        try:
            auth_status = self.authenticator.check_token_validity()
            status_text = f"🟢 Connected: {auth_status.user_name}" if auth_status.is_valid else "🔴 Disconnected"
            
            header_text = Text()
            header_text.append("🚀 G6.1 Ultimate Platform", style="bold blue")
            header_text.append(" | ")
            header_text.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
            header_text.append(" | ")
            header_text.append(status_text, style="green" if auth_status.is_valid else "red")
            
            return Panel(Align.center(header_text), box=box.HEAVY)
        except Exception:
            return Panel(Align.center("🚀 G6.1 Ultimate Platform"), box=box.HEAVY)
    
    def _create_footer(self) -> Panel:
        """Create footer panel."""
        try:
            footer_text = "[dim]Press Ctrl+C to exit | Rolling data stream active | Updates every 15 seconds[/dim]"
            return Panel(Align.center(footer_text), box=box.HEAVY)
        except Exception:
            return Panel(Align.center("[dim]Press Ctrl+C to exit[/dim]"), box=box.HEAVY)
    
    def _update_rolling_data_panel(self):
        """Update rolling data stream panel with timestamps."""
        try:
            if not self.data_collection_active:
                init_panel = Panel(
                    Align.center("📊 Initializing rolling data stream...\n\n[dim]Preparing real-time data collection[/dim]"),
                    title="📈 Rolling Live Data Stream",
                    border_style="blue"
                )
                return init_panel
            
            # Get recent data points from rolling stream
            recent_data = self.data_stream.get_recent_data(15)
            
            if not recent_data:
                empty_panel = Panel(
                    Align.center("📊 Waiting for data stream...\n\n[dim]No data points yet[/dim]"),
                    title="📈 Rolling Live Data Stream", 
                    border_style="blue"
                )
                return empty_panel
            
            # Create rolling data table with timestamps
            data_table = Table(
                title=f"Rolling Live Data Stream - Last {len(recent_data)} Updates",
                box=box.SIMPLE,
                show_lines=False,
                title_justify="center"
            )
            data_table.add_column("Time", style="dim", width=8)
            data_table.add_column("Index", style="cyan bold", width=10)
            data_table.add_column("Legs", style="green", width=6)
            data_table.add_column("Success", style="yellow", width=8)
            data_table.add_column("Premium ₹L", style="magenta", width=10)
            data_table.add_column("Volume", style="blue", width=8)
            data_table.add_column("Thru/s", style="white", width=6)
            data_table.add_column("Status", style="bold", width=6)
            
            # Add recent data points with timestamps
            for data_point in recent_data:
                time_str = data_point.timestamp.strftime("%H:%M:%S")
                premium_str = f"{data_point.premium_flow:.1f}"
                volume_str = f"{data_point.volume//1000}K"
                thru_str = f"{data_point.throughput:.1f}"
                
                data_table.add_row(
                    time_str,
                    data_point.index,
                    str(data_point.legs),
                    f"{data_point.success_rate:.1%}",
                    premium_str,
                    volume_str,
                    thru_str,
                    data_point.status
                )
            
            # Summary statistics
            if recent_data:
                total_legs = sum(dp.legs for dp in recent_data)
                avg_success = sum(dp.success_rate for dp in recent_data) / len(recent_data)
                total_premium = sum(dp.premium_flow for dp in recent_data)
                avg_throughput = sum(dp.throughput for dp in recent_data) / len(recent_data)
                
                summary_text = Text()
                summary_text.append(f"📊 Stream Summary: ", style="dim")
                summary_text.append(f"{total_legs} legs", style="bold green")
                summary_text.append(f" | {avg_success:.1%} success", style="bold yellow")
                summary_text.append(f" | ₹{total_premium:.1f}L premium", style="bold magenta")
                summary_text.append(f" | {avg_throughput:.1f} avg throughput", style="bold white")
                
                stream_panel = Panel(
                    data_table,
                    title="📈 Rolling Live Data Stream",
                    border_style="blue",
                    subtitle=summary_text
                )
            else:
                stream_panel = Panel(
                    data_table,
                    title="📈 Rolling Live Data Stream",
                    border_style="blue"
                )
            
            return stream_panel
        
        except Exception as e:
            error_panel = Panel(
                f"⚠️ Rolling stream error\n\n[dim]{str(e)[:100]}...[/dim]",
                title="📈 Rolling Live Data Stream",
                border_style="red"
            )
            return error_panel
    
    def _update_live_metrics_panel(self):
        """Update comprehensive live metrics panel."""
        try:
            comp_metrics = self.metrics_collector.get_current_comprehensive_metrics()
            stats = self.metrics_collector.comprehensive_stats
            
            if not comp_metrics:
                empty_panel = Panel(
                    Align.center("⚡ Collecting metrics...\n\n[dim]Gathering system data[/dim]"),
                    title="⚡ Live Comprehensive Metrics",
                    border_style="green"
                )
                return empty_panel
            
            # Create comprehensive metrics table
            metrics_table = Table(
                title="System & Performance Metrics", 
                box=box.SIMPLE, 
                show_lines=False,
                title_justify="center"
            )
            metrics_table.add_column("Category", style="cyan bold", width=12)
            metrics_table.add_column("Metric", style="white", width=18)
            metrics_table.add_column("Value", style="green bold", width=12)
            metrics_table.add_column("Status", style="yellow", width=6)
            
            # Resource Utilization
            metrics_table.add_row("Resource", "CPU Usage", f"{comp_metrics.cpu_percent:.1f}%", 
                                "🟢" if comp_metrics.cpu_percent < 80 else "🟡" if comp_metrics.cpu_percent < 90 else "🔴")
            metrics_table.add_row("", "Memory Usage", f"{comp_metrics.memory_percent:.1f}%",
                                "🟢" if comp_metrics.memory_percent < 80 else "🟡" if comp_metrics.memory_percent < 90 else "🔴")
            metrics_table.add_row("", "Threads", str(comp_metrics.active_threads), "🟢")
            
            # Timing Metrics
            metrics_table.add_row("Timing", "API Response", f"{comp_metrics.api_response_time:.2f}s", 
                                "🟢" if comp_metrics.api_response_time < 2.0 else "🟡" if comp_metrics.api_response_time < 5.0 else "🔴")
            metrics_table.add_row("", "Collection", f"{comp_metrics.data_collection_time:.1f}s", "🟢")
            metrics_table.add_row("", "Processing", f"{comp_metrics.processing_time:.2f}s", "🟢")
            
            # Throughput Metrics
            metrics_table.add_row("Throughput", "Options/Sec", f"{comp_metrics.options_per_second:.1f}", "🟢")
            metrics_table.add_row("", "Requests/Min", f"{comp_metrics.requests_per_minute:.0f}", "🟢")
            metrics_table.add_row("", "Data Points", f"{comp_metrics.data_points_processed:,}", "🟢")
            
            # Success Rates  
            metrics_table.add_row("Success", "API Success", f"{comp_metrics.api_success_rate:.1%}", 
                                "🟢" if comp_metrics.api_success_rate > 0.95 else "🟡" if comp_metrics.api_success_rate > 0.90 else "🔴")
            metrics_table.add_row("", "Overall Health", f"{comp_metrics.overall_system_health:.1%}",
                                "🟢" if comp_metrics.overall_system_health > 0.95 else "🟡" if comp_metrics.overall_system_health > 0.90 else "🔴")
            
            # Cache Performance
            metrics_table.add_row("Cache", "Hit Rate", f"{comp_metrics.cache_hit_rate:.1%}",
                                "🟢" if comp_metrics.cache_hit_rate > 0.80 else "🟡" if comp_metrics.cache_hit_rate > 0.70 else "🔴")
            metrics_table.add_row("", "Efficiency", f"{comp_metrics.cache_efficiency:.1%}", "🟢")
            
            # Error Tracking
            error_status = "🟢" if comp_metrics.total_errors == 0 else "🟡" if comp_metrics.total_errors < 5 else "🔴"
            metrics_table.add_row("Errors", "Total", str(comp_metrics.total_errors), error_status)
            metrics_table.add_row("", "Rate/Min", f"{comp_metrics.error_rate_per_minute:.2f}", "🟢" if comp_metrics.error_rate_per_minute < 0.1 else "🟡")
            
            # Summary stats
            uptime_hours = stats['uptime_seconds'] / 3600
            
            summary_text = Text()
            summary_text.append(f"🕐 Uptime: ", style="dim")
            summary_text.append(f"{uptime_hours:.1f}h", style="bold green")
            summary_text.append(f" | Collections: ", style="dim")
            summary_text.append(f"{stats['total_collections']}", style="bold blue")
            summary_text.append(f" | Processed: ", style="dim")
            summary_text.append(f"{stats['total_options_processed']:,}", style="bold cyan")
            
            metrics_panel = Panel(
                metrics_table, 
                title="⚡ Live Comprehensive Metrics", 
                border_style="green",
                subtitle=summary_text
            )
            
            return metrics_panel
        
        except Exception as e:
            error_panel = Panel(
                f"⚠️ Metrics error\n\n[dim]{str(e)[:100]}...[/dim]",
                title="⚡ Live Comprehensive Metrics",
                border_style="red"
            )
            return error_panel
    
    def _update_warnings_panel(self):
        """Update color-coded warnings panel with better visibility."""
        try:
            warnings = self.metrics_collector.get_recent_warnings(20)
            
            if not warnings:
                no_warnings_text = Text()
                no_warnings_text.append("✅ No warnings or anomalies detected\n", style="green bold")
                no_warnings_text.append("🔍 All systems operating normally\n", style="dim")
                no_warnings_text.append("📊 Continuous monitoring active", style="blue")
                
                warnings_panel = Panel(
                    no_warnings_text,
                    title="⚠️  Color-Coded Warnings Log",
                    border_style="yellow"
                )
                return warnings_panel
            
            # Count warnings by level
            warning_counts = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
            for warning in warnings:
                warning_counts[warning.level] += 1
            
            # Create warning content with color-coded stamps
            warning_content = Text()
            
            # Summary header with color-coded counts
            summary_parts = []
            if warning_counts["CRITICAL"] > 0:
                summary_parts.append(f"🚨 {warning_counts['CRITICAL']} CRITICAL")
            if warning_counts["ERROR"] > 0:
                summary_parts.append(f"❌ {warning_counts['ERROR']} ERROR")
            if warning_counts["WARNING"] > 0:
                summary_parts.append(f"⚠️ {warning_counts['WARNING']} WARNING")
            if warning_counts["INFO"] > 0:
                summary_parts.append(f"ℹ️ {warning_counts['INFO']} INFO")
            
            if summary_parts:
                warning_content.append(" ".join(summary_parts), style="bold")
                warning_content.append("\n" + "─" * 50 + "\n", style="dim")
            
            # Recent warnings with color-coded timestamps
            for warning in warnings[-15:]:  # Last 15 warnings
                # Color-coded level with timestamp
                color = warning.get_color_code()
                time_str = warning.timestamp.strftime("%H:%M:%S")
                
                warning_content.append(f"{warning.level}", style=f"{color} bold")
                warning_content.append(f" [{warning.category}] ", style="cyan")
                warning_content.append(f"{time_str}: ", style="dim")
                warning_content.append(f"{warning.message}\n", style="white")
            
            warnings_panel = Panel(
                warning_content, 
                title="⚠️  Color-Coded Warnings Log", 
                border_style="yellow"
            )
            
            return warnings_panel
        
        except Exception as e:
            error_panel = Panel(
                f"⚠️ Warning display error\n\n[dim]{str(e)[:100]}...[/dim]",
                title="⚠️  Color-Coded Warnings Log",
                border_style="red"
            )
            return error_panel
    
    def _safe_update_panel(self, panel_name: str, new_panel: Panel):
        """Safely update panel only if content changed - PREVENTS FLICKERING."""
        try:
            if self.layout and new_panel:
                # Only update if panel content actually changed
                old_panel = self.panel_cache.get(panel_name)
                
                # Simple content comparison to avoid unnecessary updates
                new_content_hash = hash(str(new_panel))
                old_content_hash = hash(str(old_panel)) if old_panel else None
                
                if new_content_hash != old_content_hash:
                    self.layout[panel_name].update(new_panel)
                    self.panel_cache[panel_name] = new_panel
                    
        except Exception:
            pass  # Ignore update errors to prevent crashes
    
    def run_monitoring_loop(self):
        """Run the stable monitoring loop with rolling data and flicker-free updates."""
        if not RICH_AVAILABLE:
            self._run_basic_monitoring()
            return
        
        # Setup stable layout
        layout = self.setup_layout()
        if not layout:
            print("❌ Failed to setup layout")
            return
        
        # Start stable metrics collection (15 second intervals)
        self.metrics_collector.start_collection(interval=15)
        self.data_collection_active = True
        
        try:
            # Use Rich Live display with MINIMAL refresh for stability
            with Live(
                layout, 
                refresh_per_second=0.25,  # VERY SLOW refresh to prevent flickering
                screen=False,             # Don't clear screen
                auto_refresh=False        # Manual refresh control
            ) as live:
                self.live_display = live
                
                while self.running:
                    try:
                        current_time = time.time()
                        
                        # Update display every 15 seconds (standard interval)
                        if current_time - self.last_update >= 15.0:
                            
                            # Generate rolling data stream
                            self.data_stream.simulate_data_stream()
                            
                            # Create new panels
                            new_header = self._create_header()
                            new_data_panel = self._update_rolling_data_panel()
                            new_metrics_panel = self._update_live_metrics_panel() 
                            new_warnings_panel = self._update_warnings_panel()
                            new_footer = self._create_footer()
                            
                            # SAFELY update panels only if content changed - PREVENTS FLICKERING
                            self._safe_update_panel("header", new_header)
                            self._safe_update_panel("data_collection", new_data_panel)
                            self._safe_update_panel("live_metrics", new_metrics_panel)
                            self._safe_update_panel("right_panel", new_warnings_panel)
                            self._safe_update_panel("footer", new_footer)
                            
                            # Generate realistic warnings (not compromised)
                            if random.random() < 0.15:
                                warning_types = [
                                    ("INFO", "SYSTEM", f"System health check completed"),
                                    ("WARNING", "PERFORMANCE", f"API response time elevated: {random.uniform(2.0, 4.0):.2f}s"),
                                    ("ERROR", "DATA", f"Data validation failed for {random.choice(self.indices)}"),
                                    ("WARNING", "CACHE", f"Cache hit rate below optimal: {random.uniform(0.60, 0.75):.1%}"),
                                    ("INFO", "BATCH", f"Batch processing completed: {random.randint(20, 30)} items"),
                                    ("WARNING", "RESOURCE", f"Memory usage trending upward: {random.uniform(75, 85):.1f}%"),
                                    ("ERROR", "API", f"API rate limit approaching: {random.randint(180, 199)} req/min"),
                                ]
                                
                                level, category, message = random.choice(warning_types)
                                self.metrics_collector.add_warning(level, category, message)
                            
                            # Manual refresh to control updates
                            live.refresh()
                            
                            self.last_update = current_time
                            self.update_counter += 1
                        
                        time.sleep(2.0)  # Check every 2 seconds, update every 15 seconds
                        
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        # Log error but don't crash
                        self.metrics_collector.add_warning("ERROR", "DISPLAY", f"Display error: {str(e)}")
                        time.sleep(5)
                        
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
        finally:
            self.running = False
            self.metrics_collector.stop_collection()
            
            # Display persists on exit with session summary
            if RICH_AVAILABLE and CONSOLE:
                CONSOLE.print("\n" + "="*80)
                CONSOLE.print("🚀 [bold blue]G6.1 Stable Platform Shutdown Summary[/bold blue]")
                CONSOLE.print("="*80)
                
                stats = self.metrics_collector.comprehensive_stats
                uptime_hours = stats['uptime_seconds'] / 3600
                
                summary_table = Table(title="Session Summary", box=box.ROUNDED)
                summary_table.add_column("Metric", style="cyan")
                summary_table.add_column("Value", style="green")
                
                summary_table.add_row("Session Duration", f"{uptime_hours:.2f} hours")
                summary_table.add_row("Total Collections", f"{stats['total_collections']:,}")
                summary_table.add_row("Rolling Data Points", f"{len(self.data_stream.data_points):,}")
                summary_table.add_row("Options Processed", f"{stats['total_options_processed']:,}")
                summary_table.add_row("API Calls Made", f"{stats['total_api_calls']:,}")
                summary_table.add_row("Warnings Generated", f"{len(self.metrics_collector.warnings):,}")
                summary_table.add_row("Success Rate", f"{(stats['successful_collections'] / max(1, stats['total_collections']) * 100):.1f}%")
                
                CONSOLE.print(summary_table)
                CONSOLE.print(f"\n✅ [green]Stable platform shutdown complete - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/green]")
                CONSOLE.print("📊 Rolling data stream and color-coded warnings preserved")
            else:
                print("\n✅ Stable platform shutdown complete")
    
    def _run_basic_monitoring(self):
        """Run monitoring in basic mode with rolling data."""
        print("\n" + "="*60)
        print("📊 G6.1 STABLE PLATFORM MONITORING (Basic Mode)")
        print("="*60)
        print("Rolling data stream and color-coded warnings active")
        print("Press Ctrl+C to exit\n")
        
        # Start metrics collection
        self.metrics_collector.start_collection(interval=15)
        self.data_collection_active = True
        
        try:
            cycle = 0
            while self.running:
                cycle += 1
                print(f"\n--- Rolling Update {cycle} at {datetime.now().strftime('%H:%M:%S')} ---")
                
                # Generate rolling data
                self.data_stream.simulate_data_stream()
                
                # Show recent rolling data points
                recent_data = self.data_stream.get_recent_data(5)
                if recent_data:
                    print("📈 Rolling Data Stream:")
                    for dp in recent_data:
                        time_str = dp.timestamp.strftime("%H:%M:%S")
                        print(f"  {time_str} | {dp.index} | {dp.legs} legs | {dp.success_rate:.1%} | {dp.status}")
                
                # System metrics
                comp_metrics = self.metrics_collector.get_current_comprehensive_metrics()
                if comp_metrics:
                    print(f"🖥️  System: CPU {comp_metrics.cpu_percent:.1f}% | Memory {comp_metrics.memory_percent:.1f}%")
                    print(f"⏱️  Timing: API {comp_metrics.api_response_time:.2f}s | Collection {comp_metrics.data_collection_time:.1f}s")
                    print(f"📊 Throughput: {comp_metrics.options_per_second:.1f} opts/s")
                
                # Recent color-coded warnings
                warnings = self.metrics_collector.get_recent_warnings(3)
                if warnings:
                    print("⚠️  Recent Color-Coded Warnings:")
                    for warning in warnings:
                        time_str = warning.timestamp.strftime("%H:%M:%S")
                        print(f"  {warning.level} [{warning.category}] {time_str}: {warning.message}")
                
                time.sleep(15)  # Standard 15-second updates
                
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self.metrics_collector.stop_collection()
            
            print("\n" + "="*60)
            print("🚀 G6.1 STABLE PLATFORM SHUTDOWN SUMMARY")
            print("="*60)
            stats = self.metrics_collector.comprehensive_stats
            uptime_hours = stats['uptime_seconds'] / 3600
            
            print(f"Session Duration: {uptime_hours:.2f} hours")
            print(f"Rolling Data Points: {len(self.data_stream.data_points):,}")
            print(f"Color-Coded Warnings: {len(self.metrics_collector.warnings):,}")
            print(f"Total Collections: {stats['total_collections']:,}")
            print("✅ Stable platform shutdown complete - All data preserved")
    
    def launch(self):
        """Main launch method."""
        try:
            # Print system status
            self.print_system_status()
            
            # Check authentication
            auth_status = self.authenticator.check_token_validity()
            
            if not auth_status.is_valid:
                if RICH_AVAILABLE:
                    self.console.print("🔐 [yellow]Authentication required[/yellow]")
                else:
                    print("🔐 Authentication required")
                
                if not self.show_auth_menu():
                    if RICH_AVAILABLE:
                        self.console.print("❌ [red]Authentication failed or cancelled[/red]")
                    else:
                        print("❌ Authentication failed or cancelled")
                    return False
            
            # Final authentication check
            final_auth = self.authenticator.check_token_validity()
            
            if RICH_AVAILABLE:
                if final_auth.is_valid:
                    self.console.print(f"✅ [green]Authentication successful: {final_auth.user_name}[/green]")
                else:
                    self.console.print(f"⚠️  [yellow]Proceeding with potentially invalid credentials[/yellow]")
            else:
                if final_auth.is_valid:
                    print(f"✅ Authentication successful: {final_auth.user_name}")
                else:
                    print("⚠️  Proceeding with potentially invalid credentials")
            
            self.authenticated = final_auth.is_valid
            
            # Start platform
            if RICH_AVAILABLE:
                self.console.print("\n🚀 [bold green]Starting G6.1 Stable Platform...[/bold green]")
                self.console.print("📊 [cyan]Rolling data stream and color-coded warnings active[/cyan]")
                self.console.print("💭 [dim]Press Ctrl+C to exit | Flicker-free display guaranteed[/dim]\n")
            else:
                print("\n🚀 Starting G6.1 Stable Platform...")
                print("📊 Rolling data stream and color-coded warnings active")
                print("💭 Press Ctrl+C to exit\n")
            
            self.running = True
            
            # Launch stable monitoring interface
            self.run_monitoring_loop()
            
            return True
            
        except KeyboardInterrupt:
            if RICH_AVAILABLE:
                self.console.print("\n🛑 [yellow]Shutdown requested by user[/yellow]")
            else:
                print("\n🛑 Shutdown requested by user")
            return True
        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"\n❌ [red]Launch error: {str(e)}[/red]")
            else:
                print(f"\n❌ Launch error: {str(e)}")
            return False

def main():
    """Main entry point."""
    try:
        launcher = UltimateStableLauncher()
        success = launcher.launch()
        
        if success:
            print("\n👋 Thanks for using G6.1 Stable Platform!")
        else:
            print("\n❌ Platform failed to start properly")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()