#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 Web-Based G6.1 Platform Launcher
Author: AI Assistant (Modern web UI alternative)

SOLUTION: Modern web interface for G6.1 platform management
Features: Beautiful UI, real-time status, token management, platform control
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import sys
import subprocess
import threading
import time
import json
from pathlib import Path
from datetime import datetime

# Setup
app = Flask(__name__)
app.secret_key = 'g6-platform-launcher-2024'

class WebLauncher:
    """🌐 Web-based launcher for G6.1 platform."""
    
    def __init__(self):
        """Initialize web launcher."""
        self.platform_process = None
        self.is_running = False
        self.platform_status = "stopped"
        self.platform_logs = []
        self.max_logs = 100
        
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = os.getenv('KITE_API_KEY')
        self.access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    def get_system_status(self):
        """Get comprehensive system status."""
        return {
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'api_key_set': bool(self.api_key),
            'access_token_set': bool(self.access_token),
            'platform_status': self.platform_status,
            'platform_running': self.is_running,
            'timestamp': datetime.now().isoformat(),
            'dependencies': self.check_dependencies()
        }
    
    def check_dependencies(self):
        """Check required dependencies."""
        deps = {}
        required = ['kiteconnect', 'rich', 'dotenv', 'flask', 'pathlib']
        
        for dep in required:
            try:
                __import__(dep)
                deps[dep] = {'status': 'available', 'error': None}
            except ImportError as e:
                deps[dep] = {'status': 'missing', 'error': str(e)}
        
        return deps
    
    def launch_platform(self):
        """Launch platform in background."""
        if self.is_running:
            return {'success': False, 'error': 'Platform already running'}
        
        # Find platform file
        platform_files = [
            'g6_platform_main_v2.py',
            'g6_platform_main_FINAL_WORKING.py',
            'enhanced_rich_launcher_fixed.py'
        ]
        
        platform_file = None
        for filename in platform_files:
            if Path(filename).exists():
                platform_file = Path(filename)
                break
        
        if not platform_file:
            return {'success': False, 'error': 'No platform file found'}
        
        try:
            # Setup environment
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            # Launch process
            self.platform_process = subprocess.Popen(
                [sys.executable, str(platform_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            
            self.is_running = True
            self.platform_status = "running"
            
            # Start log monitoring thread
            self.start_log_monitoring()
            
            return {'success': True, 'message': f'Platform launched: {platform_file}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_platform(self):
        """Stop platform gracefully."""
        if not self.is_running:
            return {'success': False, 'error': 'Platform not running'}
        
        try:
            if self.platform_process:
                self.platform_process.terminate()
                try:
                    self.platform_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.platform_process.kill()
                    self.platform_process.wait()
            
            self.is_running = False
            self.platform_status = "stopped"
            
            return {'success': True, 'message': 'Platform stopped'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def start_log_monitoring(self):
        """Start monitoring platform logs."""
        def monitor_logs():
            if self.platform_process:
                for line in iter(self.platform_process.stdout.readline, ''):
                    if line.strip():
                        self.add_log(line.strip())
                    
                    if self.platform_process.poll() is not None:
                        break
                
                # Process ended
                exit_code = self.platform_process.wait()
                self.add_log(f"Platform exited with code: {exit_code}")
                self.is_running = False
                self.platform_status = "stopped"
        
        log_thread = threading.Thread(target=monitor_logs, daemon=True)
        log_thread.start()
    
    def add_log(self, message):
        """Add log message."""
        log_entry = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'message': message
        }
        
        self.platform_logs.append(log_entry)
        
        # Keep only recent logs
        if len(self.platform_logs) > self.max_logs:
            self.platform_logs = self.platform_logs[-self.max_logs:]
    
    def save_credentials(self, api_key, access_token):
        """Save credentials to .env file."""
        try:
            from dotenv import set_key
            
            env_file = Path('.env')
            if not env_file.exists():
                env_file.touch()
            
            if api_key:
                set_key(str(env_file), 'KITE_API_KEY', api_key)
                os.environ['KITE_API_KEY'] = api_key
                self.api_key = api_key
            
            if access_token:
                set_key(str(env_file), 'KITE_ACCESS_TOKEN', access_token)
                os.environ['KITE_ACCESS_TOKEN'] = access_token
                self.access_token = access_token
            
            return {'success': True, 'message': 'Credentials saved successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global launcher instance
launcher = WebLauncher()

@app.route('/')
def index():
    """Main dashboard."""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """Get system status."""
    return jsonify(launcher.get_system_status())

@app.route('/api/launch', methods=['POST'])
def api_launch():
    """Launch platform."""
    result = launcher.launch_platform()
    return jsonify(result)

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop platform."""
    result = launcher.stop_platform()
    return jsonify(result)

@app.route('/api/logs')
def api_logs():
    """Get platform logs."""
    return jsonify({'logs': launcher.platform_logs})

@app.route('/api/credentials', methods=['POST'])
def api_credentials():
    """Save credentials."""
    data = request.get_json()
    api_key = data.get('api_key', '')
    access_token = data.get('access_token', '')
    
    result = launcher.save_credentials(api_key, access_token)
    return jsonify(result)

@app.route('/templates/dashboard.html')
def dashboard_template():
    """Dashboard HTML template."""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>G6.1 Platform Launcher</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            color: #5a67d8;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        
        .status-value {
            font-weight: bold;
        }
        
        .status-ok { color: #38a169; }
        .status-error { color: #e53e3e; }
        .status-warning { color: #d69e2e; }
        
        .controls {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .logs-container {
            background: #1a202c;
            color: #a0aec0;
            border-radius: 10px;
            padding: 20px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.4;
        }
        
        .log-entry {
            margin-bottom: 5px;
        }
        
        .log-timestamp {
            color: #4a5568;
            margin-right: 10px;
        }
        
        .credentials-form {
            display: grid;
            gap: 15px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        .form-group label {
            margin-bottom: 5px;
            font-weight: 600;
            color: #4a5568;
        }
        
        .form-group input {
            padding: 10px;
            border: 2px solid #e2e8f0;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .platform-status {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-running {
            background: #c6f6d5;
            color: #2f855a;
        }
        
        .status-stopped {
            background: #fed7d7;
            color: #c53030;
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .alert-success {
            background: #c6f6d5;
            color: #2f855a;
            border: 1px solid #9ae6b4;
        }
        
        .alert-error {
            background: #fed7d7;
            color: #c53030;
            border: 1px solid #fbb6ce;
        }
        
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            
            .controls {
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 G6.1 Platform Launcher</h1>
            <p>Enhanced Performance Edition v2.0</p>
        </div>
        
        <div id="alerts"></div>
        
        <div class="dashboard">
            <div class="card">
                <h3>📊 System Status</h3>
                <div class="status-grid" id="systemStatus">
                    <div class="status-item">
                        <span>Loading...</span>
                        <span class="status-value">Please wait</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🎛️ Platform Control</h3>
                <div class="status-item">
                    <span>Status:</span>
                    <span class="platform-status status-stopped" id="platformStatus">STOPPED</span>
                </div>
                <div class="controls" style="margin-top: 20px;">
                    <button class="btn btn-primary" id="launchBtn" onclick="launchPlatform()">Launch Platform</button>
                    <button class="btn btn-danger" id="stopBtn" onclick="stopPlatform()" disabled>Stop Platform</button>
                    <button class="btn btn-success" onclick="refreshStatus()">Refresh Status</button>
                </div>
            </div>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h3>🔐 API Credentials</h3>
                <div class="credentials-form">
                    <div class="form-group">
                        <label for="apiKey">Kite API Key:</label>
                        <input type="text" id="apiKey" placeholder="Enter your Kite API key">
                    </div>
                    <div class="form-group">
                        <label for="accessToken">Access Token:</label>
                        <input type="text" id="accessToken" placeholder="Enter your access token">
                    </div>
                    <button class="btn btn-primary" onclick="saveCredentials()">Save Credentials</button>
                </div>
            </div>
            
            <div class="card">
                <h3>📝 Platform Logs</h3>
                <div class="logs-container" id="logsContainer">
                    <div class="log-entry">
                        <span class="log-timestamp">[--:--:--]</span>
                        <span>Waiting for platform to start...</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let refreshInterval;
        
        function showAlert(message, type = 'success') {
            const alertsContainer = document.getElementById('alerts');
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.textContent = message;
            
            alertsContainer.innerHTML = '';
            alertsContainer.appendChild(alertDiv);
            
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
        
        function updateSystemStatus(status) {
            const container = document.getElementById('systemStatus');
            container.innerHTML = `
                <div class="status-item">
                    <span>Python:</span>
                    <span class="status-value status-ok">${status.python_version}</span>
                </div>
                <div class="status-item">
                    <span>API Key:</span>
                    <span class="status-value ${status.api_key_set ? 'status-ok' : 'status-error'}">
                        ${status.api_key_set ? 'SET' : 'MISSING'}
                    </span>
                </div>
                <div class="status-item">
                    <span>Access Token:</span>
                    <span class="status-value ${status.access_token_set ? 'status-ok' : 'status-error'}">
                        ${status.access_token_set ? 'SET' : 'MISSING'}
                    </span>
                </div>
                <div class="status-item">
                    <span>Platform:</span>
                    <span class="status-value ${status.platform_running ? 'status-ok' : 'status-warning'}">
                        ${status.platform_status.toUpperCase()}
                    </span>
                </div>
            `;
            
            // Update platform status
            const statusElement = document.getElementById('platformStatus');
            statusElement.textContent = status.platform_status.toUpperCase();
            statusElement.className = `platform-status ${status.platform_running ? 'status-running' : 'status-stopped'}`;
            
            // Update buttons
            document.getElementById('launchBtn').disabled = status.platform_running;
            document.getElementById('stopBtn').disabled = !status.platform_running;
        }
        
        function refreshStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateSystemStatus(data);
                })
                .catch(error => {
                    showAlert('Failed to refresh status: ' + error.message, 'error');
                });
        }
        
        function launchPlatform() {
            fetch('/api/launch', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showAlert(data.message, 'success');
                        startLogRefresh();
                    } else {
                        showAlert('Launch failed: ' + data.error, 'error');
                    }
                    refreshStatus();
                })
                .catch(error => {
                    showAlert('Launch request failed: ' + error.message, 'error');
                });
        }
        
        function stopPlatform() {
            fetch('/api/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showAlert(data.message, 'success');
                        stopLogRefresh();
                    } else {
                        showAlert('Stop failed: ' + data.error, 'error');
                    }
                    refreshStatus();
                })
                .catch(error => {
                    showAlert('Stop request failed: ' + error.message, 'error');
                });
        }
        
        function saveCredentials() {
            const apiKey = document.getElementById('apiKey').value;
            const accessToken = document.getElementById('accessToken').value;
            
            if (!apiKey && !accessToken) {
                showAlert('Please enter at least one credential', 'error');
                return;
            }
            
            fetch('/api/credentials', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey, access_token: accessToken })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showAlert(data.message, 'success');
                        document.getElementById('apiKey').value = '';
                        document.getElementById('accessToken').value = '';
                        refreshStatus();
                    } else {
                        showAlert('Save failed: ' + data.error, 'error');
                    }
                })
                .catch(error => {
                    showAlert('Save request failed: ' + error.message, 'error');
                });
        }
        
        function refreshLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('logsContainer');
                    container.innerHTML = '';
                    
                    if (data.logs && data.logs.length > 0) {
                        data.logs.forEach(log => {
                            const logDiv = document.createElement('div');
                            logDiv.className = 'log-entry';
                            logDiv.innerHTML = `
                                <span class="log-timestamp">[${log.timestamp}]</span>
                                <span>${log.message}</span>
                            `;
                            container.appendChild(logDiv);
                        });
                        
                        // Auto-scroll to bottom
                        container.scrollTop = container.scrollHeight;
                    } else {
                        container.innerHTML = '<div class="log-entry"><span class="log-timestamp">[--:--:--]</span><span>No logs available</span></div>';
                    }
                })
                .catch(error => {
                    console.error('Failed to refresh logs:', error);
                });
        }
        
        function startLogRefresh() {
            if (refreshInterval) clearInterval(refreshInterval);
            refreshInterval = setInterval(() => {
                refreshLogs();
                refreshStatus();
            }, 2000);
        }
        
        function stopLogRefresh() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            refreshStatus();
            refreshLogs();
        });
    </script>
</body>
</html>'''
    
    return html_content

def create_templates_dir():
    """Create templates directory and files."""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # Create dashboard template
    with open(templates_dir / 'dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_template())

def main():
    """Run web launcher."""
    print("🌐 G6.1 Platform Web Launcher")
    print("=" * 40)
    
    # Create templates
    create_templates_dir()
    
    print("Starting web server...")
    print("Open your browser to: http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nWeb launcher stopped")
        # Clean shutdown
        if launcher.is_running:
            launcher.stop_platform()

if __name__ == "__main__":
    main()