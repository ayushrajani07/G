#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔌 Enhanced Kite Login and Launch Script (FINAL VERSION)
Author: AI Assistant (Complete authentication and launch integration)

✅ FINAL FIXES INCLUDED:
- Clean terminal output without duplicates
- Proper error handling for checksum issues
- UTF-8 encoding support
- Enhanced subprocess management
- Token validation and storage
"""

import os
import sys
import time
import json
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
from flask import Flask, request, redirect
import threading
import signal

# UTF-8 support for Windows
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Environment setup
from dotenv import load_dotenv, set_key
load_dotenv()

# Configuration
API_KEY = os.getenv('KITE_API_KEY')
API_SECRET = os.getenv('KITE_API_SECRET')
APP_SCRIPT = 'g6_platform_main_fixed_FINAL.py'

class KiteAuthManager:
    """🔐 Enhanced Kite Connect Authentication Manager."""
    
    def __init__(self):
        self.request_token = None
        self.access_token = None
        self.flask_app = None
        self.server_thread = None
        self.auth_complete = threading.Event()
        
    def print_header(self, title: str):
        """📊 Print enhanced header."""
        print("\n" + "=" * 60)
        print(f"🚀 {title}")
        print("=" * 60)
    
    def print_info(self, message: str):
        """ℹ️ Print info message."""
        print(f"ℹ️  {message}")
    
    def print_success(self, message: str):
        """✅ Print success message."""
        print(f"✅ {message}")
    
    def print_warning(self, message: str):
        """⚠️ Print warning message."""
        print(f"⚠️  {message}")
    
    def print_error(self, message: str):
        """❌ Print error message."""
        print(f"❌ {message}")
    
    def validate_existing_token(self) -> bool:
        """🔍 Validate existing access token."""
        try:
            existing_token = os.getenv('KITE_ACCESS_TOKEN')
            if not existing_token:
                return False
            
            from kiteconnect import KiteConnect
            kite = KiteConnect(api_key=API_KEY)
            kite.set_access_token(existing_token)
            
            # Test the token
            profile = kite.profile()
            if profile:
                self.access_token = existing_token
                self.print_success(f"Existing token is valid - User: {profile.get('user_name', 'Unknown')}")
                return True
            
        except Exception as e:
            self.print_warning(f"Token validation failed: {str(e)[:50]}...")
        
        return False
    
    def setup_flask_callback_server(self):
        """🌐 Setup Flask callback server for OAuth flow."""
        self.flask_app = Flask(__name__)
        self.flask_app.config['SECRET_KEY'] = 'g6-kite-auth'
        
        @self.flask_app.route('/callback')
        def callback():
            self.request_token = request.args.get('request_token')
            status = request.args.get('status')
            
            if status == 'success' and self.request_token:
                self.print_success(f"Token captured: {self.request_token[:12]}...")
                self.auth_complete.set()
                return """
                <html><body style='font-family: Arial; text-align: center; padding: 50px;'>
                <h2>🎉 Authentication Successful!</h2>
                <p>You can close this window and return to the terminal.</p>
                </body></html>
                """
            else:
                self.print_error("Authentication failed or was cancelled")
                self.auth_complete.set()
                return """
                <html><body style='font-family: Arial; text-align: center; padding: 50px;'>
                <h2>❌ Authentication Failed</h2>
                <p>Please try again or use manual token entry.</p>
                </body></html>
                """
    
    def start_callback_server(self):
        """🚀 Start the callback server in a separate thread."""
        def run_server():
            self.flask_app.run(host='localhost', port=5000, debug=False, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        time.sleep(1)  # Give server time to start
    
    def browser_login_flow(self) -> bool:
        """🌐 Perform browser-based Kite Connect login flow."""
        try:
            self.print_info("Starting Kite Connect login flow...")
            
            # Setup callback server
            self.setup_flask_callback_server()
            self.start_callback_server()
            
            # Generate login URL
            login_url = f"https://kite.trade/connect/login?v=3&api_key={API_KEY}"
            
            self.print_info("Opening browser for Kite login...")
            webbrowser.open(login_url)
            
            self.print_info("Waiting for login completion...")
            
            # Wait for callback with timeout
            if self.auth_complete.wait(timeout=300):  # 5 minute timeout
                if self.request_token:
                    return self.generate_access_token()
                else:
                    self.print_error("No request token received")
                    return False
            else:
                self.print_error("Login timeout - please try manual token entry")
                return False
                
        except Exception as e:
            self.print_error(f"Browser login error: {e}")
            return False
    
    def generate_access_token(self) -> bool:
        """🔑 Generate access token from request token."""
        try:
            self.print_info("Generating access token...")
            
            from kiteconnect import KiteConnect
            kite = KiteConnect(api_key=API_KEY)
            
            session_data = kite.generate_session(self.request_token, api_secret=API_SECRET)
            self.access_token = session_data['access_token']
            
            # Save to environment
            env_file = Path('.env')
            set_key(str(env_file), 'KITE_ACCESS_TOKEN', self.access_token)
            
            self.print_success("Access token generated and saved")
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "Invalid checksum" in error_msg:
                self.print_error("Token generation failed: Invalid checksum - check API secret")
            else:
                self.print_error(f"Token generation failed: {error_msg}")
            return False
    
    def manual_token_entry(self) -> bool:
        """📝 Manual token entry method."""
        try:
            self.print_info("Manual token entry mode")
            
            token = input("🔑 Enter your Kite access token: ").strip()
            if not token:
                self.print_error("No token provided")
                return False
            
            # Validate the token
            from kiteconnect import KiteConnect
            kite = KiteConnect(api_key=API_KEY)
            kite.set_access_token(token)
            
            profile = kite.profile()
            if profile:
                self.access_token = token
                
                # Save to environment
                env_file = Path('.env')
                set_key(str(env_file), 'KITE_ACCESS_TOKEN', token)
                
                self.print_success("Manual token validated")
                self.print_success("Token saved to environment and .env file")
                return True
            else:
                self.print_error("Token validation failed")
                return False
                
        except Exception as e:
            self.print_error(f"Manual token validation failed: {e}")
            return False
    
    def authenticate(self) -> bool:
        """🔐 Main authentication flow."""
        self.print_header("G6.1 KITE CONNECT AUTHENTICATION")
        
        if not API_KEY:
            self.print_error("KITE_API_KEY not found in environment")
            return False
        
        self.print_info(f"API Key: {API_KEY[:12]}...")
        
        # Check platform configuration
        self.print_info("Checking platform configuration...")
        if os.getenv('G6_ENABLE_INFLUXDB', 'false').lower() == 'true':
            self.print_success("InfluxDB: Enabled")
        if os.getenv('G6_ENABLE_CSV', 'true').lower() == 'true':
            self.print_success("CSV Storage: Enabled")
        
        mode = "Mock (test data)" if os.getenv('G6_MOCK_MODE', 'false').lower() == 'true' else "Live (real market data)"
        self.print_info(f"Mode: {mode}")
        
        # Try to validate existing token first
        self.print_info("Validating existing access token...")
        if self.validate_existing_token():
            return True
        
        self.print_warning("No valid access token found")
        
        # Show authentication options
        print("\nℹ️  Choose authentication method:")
        print("  1️⃣  Kite Connect login (browser)")
        print("  2️⃣  Enter token manually")
        print("  3️⃣  Continue without token (may fail)")
        
        try:
            choice = input("Enter choice [1/2/3]: ").strip()
            
            if choice == '1':
                return self.browser_login_flow()
            elif choice == '2':
                return self.manual_token_entry()
            elif choice == '3':
                self.print_warning("Continuing without valid token")
                return True  # Allow platform to run in mock mode
            else:
                self.print_error("Invalid choice")
                return False
                
        except KeyboardInterrupt:
            self.print_info("\nAuthentication cancelled by user")
            return False

def launch_platform():
    """🚀 Launch the G6.1 platform with enhanced error handling."""
    print("\n" + "=" * 60)
    print("🚀 LAUNCHING G6.1 PLATFORM")
    print("=" * 60)
    
    try:
        # Set environment for UTF-8 support
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        
        process = subprocess.Popen(
            [sys.executable, APP_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            env=env
        )
        
        # Stream output in real-time
        for line in iter(process.stdout.readline, ''):
            print(line.rstrip())
        
        process.stdout.close()
        return_code = process.wait()
        
        if return_code == 0:
            print("✅ Platform exited successfully")
        else:
            print(f"⚠️  Platform exited with code: {return_code}")
        
    except KeyboardInterrupt:
        print("\n🛑 Platform interrupted by user")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    except Exception as e:
        print(f"❌ Failed to launch platform: {e}")

def main():
    """🚀 Main entry point."""
    try:
        # Initialize authentication manager
        auth_manager = KiteAuthManager()
        
        # Perform authentication
        if auth_manager.authenticate():
            # Launch the platform
            launch_platform()
        else:
            print("\n❌ Authentication failed - cannot launch platform")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        return 0
    except Exception as e:
        print(f"❌ Launcher error: {e}")
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)