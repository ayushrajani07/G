#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultimate Fixed Launcher - G6.1 Platform (FIXED VERSION)
Advanced launcher with proper Kite authentication and stable monitoring display

FIXES APPLIED:
- Fixed Rich Live display to prevent panels moving down
- Added missing random import 
- Fixed Flask server URL consistency
- Optimized refresh rates and display stability
- Added proper error handling for display updates
"""

import os
import sys
import json
import time
import threading
import webbrowser
import requests
import random  # FIXED: Added missing import
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import hashlib
import uuid

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

@dataclass
class AuthenticationStatus:
    """Authentication status container."""
    is_valid: bool
    token: Optional[str]
    expiry_date: Optional[datetime]
    user_name: Optional[str]
    error_message: Optional[str] = None

@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    active_threads: int
    open_files: int

@dataclass
class DataCollectionMetrics:
    """Data collection performance metrics."""
    timestamp: datetime
    total_legs_collected: Dict[str, int] = field(default_factory=dict)
    symmetric_offsets: Dict[str, int] = field(default_factory=dict)
    asymmetric_offsets: Dict[str, int] = field(default_factory=dict)
    data_drops: Dict[str, int] = field(default_factory=dict)
    success_rates: Dict[str, float] = field(default_factory=dict)
    timing_metrics: Dict[str, float] = field(default_factory=dict)
    throughput_metrics: Dict[str, float] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)

@dataclass
class WarningEntry:
    """Warning log entry."""
    timestamp: datetime
    level: str  # INFO, WARNING, ERROR, CRITICAL
    category: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

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
        
        return "http://localhost:5555"  # FIXED: Consistent port
    
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

class MetricsCollector:
    """Collects and tracks comprehensive system and application metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.system_metrics: deque = deque(maxlen=300)  # 5 minutes at 1-second intervals
        self.data_metrics: deque = deque(maxlen=100)    # Recent data collection metrics
        self.warnings: deque = deque(maxlen=1000)       # Warning log entries
        
        self.running = False
        self.collector_thread = None
        
        # Metric baselines for anomaly detection
        self.baselines = {
            'cpu_percent': {'mean': 0, 'std': 0, 'samples': []},
            'memory_percent': {'mean': 0, 'std': 0, 'samples': []},
            'collection_time': {'mean': 0, 'std': 0, 'samples': []},
            'throughput': {'mean': 0, 'std': 0, 'samples': []},
        }
        
        # Current collection statistics
        self.current_stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'total_options_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls': 0,
            'errors': defaultdict(int)
        }
    
    def start_collection(self, interval: int = 2):  # FIXED: Less frequent updates
        """Start metrics collection."""
        if self.running:
            return
        
        self.running = True
        
        def collect_loop():
            while self.running:
                try:
                    # Collect system metrics
                    sys_metrics = self._collect_system_metrics()
                    self.system_metrics.append(sys_metrics)
                    
                    # Update baselines
                    self._update_baselines(sys_metrics)
                    
                    # Check for anomalies
                    self._check_anomalies(sys_metrics)
                    
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
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            import psutil
            
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Process info
            process = psutil.Process()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=disk_usage_percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                },
                active_threads=process.num_threads(),
                open_files=len(process.open_files()) if hasattr(process, 'open_files') else 0
            )
            
        except ImportError:
            # Fallback without psutil
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_usage_percent=0.0,
                network_io={'bytes_sent': 0, 'bytes_recv': 0},
                active_threads=threading.active_count(),
                open_files=0
            )
        except Exception as e:
            # Return safe defaults on any error
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_usage_percent=0.0,
                network_io={'bytes_sent': 0, 'bytes_recv': 0},
                active_threads=0,
                open_files=0
            )
    
    def _update_baselines(self, metrics: SystemMetrics):
        """Update baseline metrics for anomaly detection."""
        for metric_name in ['cpu_percent', 'memory_percent']:
            try:
                value = getattr(metrics, metric_name)
                baseline = self.baselines[metric_name]
                
                # Add sample
                baseline['samples'].append(value)
                
                # Keep only recent samples (last 100)
                if len(baseline['samples']) > 100:
                    baseline['samples'] = baseline['samples'][-100:]
                
                # Update mean and std
                if len(baseline['samples']) >= 10:
                    import statistics
                    baseline['mean'] = statistics.mean(baseline['samples'])
                    baseline['std'] = statistics.stdev(baseline['samples']) if len(baseline['samples']) > 1 else 0
            except Exception:
                pass  # Ignore errors in baseline calculation
    
    def _check_anomalies(self, metrics: SystemMetrics):
        """Check for metric anomalies and generate warnings."""
        try:
            # Check CPU usage
            if metrics.cpu_percent > 90:
                self.add_warning(
                    level="CRITICAL",
                    category="SYSTEM",
                    message=f"High CPU usage: {metrics.cpu_percent:.1f}%"
                )
            
            # Check memory usage
            if metrics.memory_percent > 90:
                self.add_warning(
                    level="CRITICAL",
                    category="SYSTEM",
                    message=f"High memory usage: {metrics.memory_percent:.1f}%"
                )
            
            # Check deviation from baseline
            for metric_name in ['cpu_percent', 'memory_percent']:
                baseline = self.baselines[metric_name]
                if baseline['std'] > 0:
                    value = getattr(metrics, metric_name)
                    deviation = abs(value - baseline['mean']) / baseline['std']
                    
                    if deviation > 3:  # 3 standard deviations
                        self.add_warning(
                            level="WARNING",
                            category="ANOMALY",
                            message=f"{metric_name} deviates significantly: {value:.1f} (baseline: {baseline['mean']:.1f})"
                        )
        except Exception:
            pass  # Ignore errors in anomaly detection
    
    def add_warning(self, level: str, category: str, message: str, details: Dict[str, Any] = None):
        """Add warning to log."""
        try:
            warning = WarningEntry(
                timestamp=datetime.now(),
                level=level,
                category=category,
                message=message,
                details=details or {}
            )
            
            self.warnings.append(warning)
        except Exception:
            pass  # Ignore errors in warning creation
    
    def update_data_metrics(self, metrics: DataCollectionMetrics):
        """Update data collection metrics."""
        try:
            self.data_metrics.append(metrics)
            
            # Update statistics
            self.current_stats['total_collections'] += 1
            
            # Check success rates
            for index, rate in metrics.success_rates.items():
                if rate < 0.90:  # Below 90%
                    self.add_warning(
                        level="WARNING",
                        category="DATA_QUALITY",
                        message=f"{index} success rate below 90%: {rate:.1%}",
                        details={'index': index, 'success_rate': rate}
                    )
        except Exception:
            pass  # Ignore errors in metrics update
    
    def get_current_system_metrics(self) -> Optional[SystemMetrics]:
        """Get most recent system metrics."""
        try:
            return self.system_metrics[-1] if self.system_metrics else None
        except Exception:
            return None
    
    def get_current_data_metrics(self) -> Optional[DataCollectionMetrics]:
        """Get most recent data metrics."""
        try:
            return self.data_metrics[-1] if self.data_metrics else None
        except Exception:
            return None
    
    def get_recent_warnings(self, count: int = 10) -> List[WarningEntry]:
        """Get recent warning entries."""
        try:
            return list(self.warnings)[-count:] if self.warnings else []
        except Exception:
            return []

class UltimateFixedLauncher:
    """Ultimate launcher with proper authentication and stable monitoring display."""
    
    def __init__(self):
        """Initialize the ultimate launcher."""
        self.console = Console() if RICH_AVAILABLE else None
        self.authenticator = KiteAuthenticator()
        self.metrics_collector = MetricsCollector()
        
        # Runtime state
        self.running = False
        self.data_collection_active = False
        self.authenticated = False
        
        # Mock indices for demonstration
        self.indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
        
        # Layout components
        self.layout = None
        self.live_display = None
        
        # Display update control - FIXED
        self.update_counter = 0
        self.last_update = time.time()
    
    def print_system_status(self):
        """Print concise system status summary."""
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
                self.console.print(f"🔗 [cyan]Opening browser to: {auth_url}[/cyan]")  # FIXED: Consistent URL
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
        """Setup the main monitoring layout."""
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
            
            # Header
            self.layout["header"].update(self._create_header())
            
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
            
            # Right panel: Warnings log
            self.layout["right_panel"].update(Panel("", title="⚠️  Warnings Log", border_style="yellow"))
            
            # Footer
            self.layout["footer"].update(self._create_footer())
            
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
            footer_text = "[dim]Press Ctrl+C to exit | Data updates every 5 seconds[/dim]"  # FIXED: Updated interval
            return Panel(Align.center(footer_text), box=box.HEAVY)
        except Exception:
            return Panel(Align.center("[dim]Press Ctrl+C to exit[/dim]"), box=box.HEAVY)
    
    def _update_data_collection_panel(self):
        """Update data collection streaming panel."""
        try:
            if not self.data_collection_active:
                # Show initialization message
                self.layout["data_collection"].update(
                    Panel(
                        Align.center("📊 Starting data collection...\n\n[dim]Initializing connections and collectors[/dim]"),
                        title="📈 Live Data Collection",
                        border_style="blue"
                    )
                )
                return
            
            # Create data collection table
            data_table = Table(title="Data Collection Status", box=box.ROUNDED, show_lines=True)
            data_table.add_column("Index", style="cyan", width=12)
            data_table.add_column("Legs", style="green", width=8)
            data_table.add_column("Sym Off", style="yellow", width=8)
            data_table.add_column("Asym Off", style="yellow", width=8)
            data_table.add_column("Drops", style="red", width=8)
            data_table.add_column("Success", style="green", width=10)
            data_table.add_column("Status", style="bold", width=8)
            
            # Get current metrics (mock data for demonstration)
            current_metrics = self._generate_mock_data_metrics()
            
            for index in self.indices:
                legs = current_metrics.total_legs_collected.get(index, 0)
                sym_off = current_metrics.symmetric_offsets.get(index, 0)
                asym_off = current_metrics.asymmetric_offsets.get(index, 0)
                drops = current_metrics.data_drops.get(index, 0)
                success_rate = current_metrics.success_rates.get(index, 0.95)
                
                status = "✅" if success_rate >= 0.90 else "❌"
                
                data_table.add_row(
                    index,
                    str(legs),
                    str(sym_off),
                    str(asym_off),
                    str(drops),
                    f"{success_rate:.1%}",
                    status
                )
            
            # Summary stats
            total_legs = sum(current_metrics.total_legs_collected.values())
            avg_success = sum(current_metrics.success_rates.values()) / len(current_metrics.success_rates) if current_metrics.success_rates else 0
            
            summary_text = f"Total Legs: [bold green]{total_legs}[/bold green] | Avg Success: [bold green]{avg_success:.1%}[/bold green] | Collection Time: [bold yellow]{current_metrics.timing_metrics.get('collection_time', 0):.1f}s[/bold yellow]"
            
            # Create full panel content as string
            collection_content = f"{data_table}\n\n{summary_text}"
            
            collection_panel = Panel(
                collection_content,
                title="📈 Live Data Collection",
                border_style="blue"
            )
            
            self.layout["data_collection"].update(collection_panel)
        
        except Exception as e:
            # Fallback panel on error
            error_panel = Panel(
                f"⚠️ Display update error\n\n[dim]{str(e)[:100]}...[/dim]",
                title="📈 Live Data Collection",
                border_style="red"
            )
            self.layout["data_collection"].update(error_panel)
    
    def _update_live_metrics_panel(self):
        """Update live metrics panel."""
        try:
            metrics_table = Table(title="System & Performance Metrics", box=box.MINIMAL, show_lines=True)
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="green")
            metrics_table.add_column("Status", style="yellow")
            
            # System metrics
            sys_metrics = self.metrics_collector.get_current_system_metrics()
            if sys_metrics:
                metrics_table.add_row("CPU Usage", f"{sys_metrics.cpu_percent:.1f}%", 
                                    "🟢" if sys_metrics.cpu_percent < 80 else "🟡" if sys_metrics.cpu_percent < 90 else "🔴")
                metrics_table.add_row("Memory Usage", f"{sys_metrics.memory_percent:.1f}%",
                                    "🟢" if sys_metrics.memory_percent < 80 else "🟡" if sys_metrics.memory_percent < 90 else "🔴")
                metrics_table.add_row("Active Threads", str(sys_metrics.active_threads), "🟢")
            
            # Application metrics
            stats = self.metrics_collector.current_stats
            metrics_table.add_row("API Calls", str(stats['api_calls']), "🟢")
            metrics_table.add_row("Cache Hits", str(stats['cache_hits']), "🟢")
            metrics_table.add_row("Cache Misses", str(stats['cache_misses']), "🟡" if stats['cache_misses'] > stats['cache_hits'] else "🟢")
            metrics_table.add_row("Total Errors", str(sum(stats['errors'].values())), "🟢" if sum(stats['errors'].values()) == 0 else "🟡")
            
            self.layout["live_metrics"].update(
                Panel(metrics_table, title="⚡ Live Metrics", border_style="green")
            )
        
        except Exception as e:
            # Fallback panel on error
            error_panel = Panel(
                f"⚠️ Metrics update error\n\n[dim]{str(e)[:100]}...[/dim]",
                title="⚡ Live Metrics",
                border_style="red"
            )
            self.layout["live_metrics"].update(error_panel)
    
    def _update_warnings_panel(self):
        """Update warnings log panel."""
        try:
            warnings = self.metrics_collector.get_recent_warnings(15)
            
            if not warnings:
                warning_content = "[dim]No warnings or anomalies detected[/dim]"
            else:
                warning_lines = []
                for warning in warnings:
                    level_color = {
                        "INFO": "blue",
                        "WARNING": "yellow", 
                        "ERROR": "red",
                        "CRITICAL": "bold red"
                    }.get(warning.level, "white")
                    
                    time_str = warning.timestamp.strftime("%H:%M:%S")
                    warning_lines.append(f"[{level_color}]{warning.level}[/{level_color}] [{warning.category}] {time_str}: {warning.message}")
                
                warning_content = "\n".join(warning_lines[-15:])  # Last 15 warnings
            
            self.layout["right_panel"].update(
                Panel(warning_content, title="⚠️  Warnings Log", border_style="yellow")
            )
        
        except Exception as e:
            # Fallback panel on error
            error_panel = Panel(
                f"⚠️ Warning log error\n\n[dim]{str(e)[:100]}...[/dim]",
                title="⚠️  Warnings Log",
                border_style="red"
            )
            self.layout["right_panel"].update(error_panel)
    
    def _generate_mock_data_metrics(self) -> DataCollectionMetrics:
        """Generate mock data metrics for demonstration."""
        try:
            metrics = DataCollectionMetrics(timestamp=datetime.now())
            
            for index in self.indices:
                # Simulate realistic metrics
                base_legs = 50 if index == 'NIFTY' else 30
                legs = base_legs + random.randint(-5, 10)
                
                metrics.total_legs_collected[index] = legs
                metrics.symmetric_offsets[index] = random.randint(8, 12)
                metrics.asymmetric_offsets[index] = random.randint(4, 8)
                metrics.data_drops[index] = random.randint(0, 3)
                metrics.success_rates[index] = random.uniform(0.88, 0.98)
            
            metrics.timing_metrics['collection_time'] = random.uniform(25, 45)
            metrics.throughput_metrics['options_per_second'] = random.uniform(15, 25)
            
            return metrics
        except Exception:
            # Return empty metrics on error
            return DataCollectionMetrics(timestamp=datetime.now())
    
    def run_monitoring_loop(self):
        """Run the main monitoring loop with stable display."""
        if not RICH_AVAILABLE:
            self._run_basic_monitoring()
            return
        
        # Setup layout
        layout = self.setup_layout()
        if not layout:
            print("❌ Failed to setup layout")
            return
        
        # Start metrics collection
        self.metrics_collector.start_collection(interval=2)  # FIXED: Less frequent collection
        self.data_collection_active = True
        
        try:
            # FIXED: Use proper Live display with controlled refresh
            with Live(layout, refresh_per_second=0.5, screen=True) as live:  # FIXED: Slower refresh
                self.live_display = live
                
                while self.running:
                    try:
                        current_time = time.time()
                        
                        # FIXED: Only update display every 5 seconds
                        if current_time - self.last_update >= 5.0:
                            # Update all panels
                            self._update_data_collection_panel()
                            self._update_live_metrics_panel()
                            self._update_warnings_panel()
                            
                            # Update header and footer
                            self.layout["header"].update(self._create_header())
                            self.layout["footer"].update(self._create_footer())
                            
                            # Simulate occasional warnings (reduced frequency)
                            if random.random() < 0.05:  # FIXED: 5% chance instead of 10%
                                self.metrics_collector.add_warning(
                                    level=random.choice(["INFO", "WARNING", "ERROR"]),
                                    category=random.choice(["DATA", "SYSTEM", "API"]),
                                    message=f"Sample warning at {datetime.now().strftime('%H:%M:%S')}"
                                )
                            
                            self.last_update = current_time
                            self.update_counter += 1
                        
                        time.sleep(1.0)  # FIXED: Sleep for 1 second between checks
                        
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        # Log error but don't crash
                        self.metrics_collector.add_warning("ERROR", "DISPLAY", f"Display error: {e}")
                        time.sleep(2)  # Wait longer on error
                        
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
        finally:
            self.running = False
            self.metrics_collector.stop_collection()
            
            if RICH_AVAILABLE:
                self.console.print("\n✅ [green]Platform shutdown complete[/green]")
            else:
                print("\n✅ Platform shutdown complete")
    
    def _run_basic_monitoring(self):
        """Run basic monitoring without Rich UI."""
        print("\n" + "="*60)
        print("📊 G6.1 PLATFORM MONITORING (Basic Mode)")
        print("="*60)
        print("Press Ctrl+C to exit\n")
        
        # Start metrics collection
        self.metrics_collector.start_collection(interval=5)  # Less frequent in basic mode
        self.data_collection_active = True
        
        try:
            cycle = 0
            while self.running:
                cycle += 1
                print(f"\n--- Update {cycle} at {datetime.now().strftime('%H:%M:%S')} ---")
                
                # System metrics
                sys_metrics = self.metrics_collector.get_current_system_metrics()
                if sys_metrics:
                    print(f"System: CPU {sys_metrics.cpu_percent:.1f}% | Memory {sys_metrics.memory_percent:.1f}% | Threads {sys_metrics.active_threads}")
                
                # Data collection metrics (mock)
                current_metrics = self._generate_mock_data_metrics()
                total_legs = sum(current_metrics.total_legs_collected.values())
                avg_success = sum(current_metrics.success_rates.values()) / len(current_metrics.success_rates)
                
                print(f"Data Collection: {total_legs} legs | {avg_success:.1%} success rate | {current_metrics.timing_metrics.get('collection_time', 0):.1f}s")
                
                # Recent warnings
                warnings = self.metrics_collector.get_recent_warnings(3)
                if warnings:
                    print("Recent warnings:")
                    for warning in warnings:
                        print(f"  {warning.level}: {warning.message}")
                
                time.sleep(10)  # FIXED: Update every 10 seconds in basic mode
                
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self.metrics_collector.stop_collection()
            print("\n✅ Platform shutdown complete")
    
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
                self.console.print("\n🚀 [bold green]Starting G6.1 Ultimate Platform...[/bold green]")
                self.console.print("💭 [dim]Press Ctrl+C to exit[/dim]\n")
            else:
                print("\n🚀 Starting G6.1 Ultimate Platform...")
                print("💭 Press Ctrl+C to exit\n")
            
            self.running = True
            
            # Launch monitoring interface
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
        launcher = UltimateFixedLauncher()
        success = launcher.launch()
        
        if success:
            print("\n👋 Thanks for using G6.1 Platform!")
        else:
            print("\n❌ Platform failed to start properly")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()