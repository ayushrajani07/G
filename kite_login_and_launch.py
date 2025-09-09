#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Enhanced Kite Login & Launch Script for G6.1 Platform
Author: AI Assistant (Streamlined with rich terminal output)

✅ Features:
- Rich, concise terminal output with colored text
- Integration with existing TokenManager
- Graceful error handling without tracebacks
- Automatic InfluxDB status detection
- Clean subprocess management
"""

import os
import sys
import threading
import webbrowser
import subprocess
import signal
from urllib.parse import parse_qs
from flask import Flask, request

import os, sys
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# Rich terminal output
class TerminalColors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_rich(message: str, color: str = TerminalColors.END):
    """Print with rich terminal colors."""
    print(f"{color}{message}{TerminalColors.END}")

def print_header(title: str):
    """Print styled header."""
    print_rich("=" * 60, TerminalColors.CYAN)
    print_rich(f"🚀 {title}", TerminalColors.BOLD + TerminalColors.GREEN)
    print_rich("=" * 60, TerminalColors.CYAN)

def print_success(message: str):
    """Print success message."""
    print_rich(f"✅ {message}", TerminalColors.GREEN)

def print_warning(message: str):
    """Print warning message."""
    print_rich(f"⚠️  {message}", TerminalColors.YELLOW)

def print_error(message: str):
    """Print error message."""
    print_rich(f"❌ {message}", TerminalColors.RED)

def print_info(message: str):
    """Print info message."""
    print_rich(f"ℹ️  {message}", TerminalColors.BLUE)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

try:
    from kiteconnect import KiteConnect
    from kiteconnect.exceptions import KiteException
    KITE_AVAILABLE = True
except ImportError:
    KITE_AVAILABLE = False
    print_error("KiteConnect not available. Install with: pip install kiteconnect")

# Configuration
APP_SCRIPT = "g6_platform_main_fixed.py"
API_KEY = os.getenv("KITE_API_KEY")
API_SECRET = os.getenv("KITE_API_SECRET")
REDIRECT_URI = "http://127.0.0.1:5000/success"

# Flask app for token capture
app = Flask(__name__)
_req_token = None
_server_shutdown = False

@app.route("/success")
def login_callback():
    """Handle Kite Connect redirect and capture request token."""
    global _req_token, _server_shutdown
    
    req = request.args.get("request_token")
    status = request.args.get("status")
    
    if status == "success" and req:
        _req_token = req
        print_success(f"Token captured: {req[:12]}...")
        
        # Schedule server shutdown
        func = request.environ.get('werkzeug.server.shutdown')
        if func:
            func()
        _server_shutdown = True
        
        return """
        <html><body style='font-family: Arial; text-align: center; margin-top: 50px;'>
        <h2 style='color: green;'>✅ Login Successful!</h2>
        <p>Token captured successfully. You can close this window.</p>
        <p style='color: #666;'>The platform will launch automatically...</p>
        </body></html>
        """
    else:
        return """
        <html><body style='font-family: Arial; text-align: center; margin-top: 50px;'>
        <h2 style='color: red;'>❌ Login Failed</h2>
        <p>Authentication was unsuccessful. Please try again.</p>
        </body></html>
        """

def run_flask_server():
    """Run Flask server with suppressed output."""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    try:
        app.run(port=5000, debug=False, use_reloader=False)
    except Exception:
        pass  # Suppress Flask shutdown messages

def validate_existing_token() -> bool:
    """Check if existing access token is valid."""
    access_token = os.getenv("KITE_ACCESS_TOKEN")
    
    if not access_token:
        return False
    
    if not KITE_AVAILABLE:
        print_warning("Cannot validate token - KiteConnect not available")
        return False
    
    try:
        print_info("Validating existing access token...")
        kite = KiteConnect(api_key=API_KEY)
        kite.set_access_token(access_token)
        profile = kite.profile()
        
        if profile and profile.get("user_id"):
            print_success(f"Token valid for user: {profile.get('user_name', 'Unknown')}")
            return True
        
    except Exception as e:
        print_warning(f"Token validation failed: {str(e)[:50]}...")
        return False
    
    return False

def get_new_token_via_kite() -> str:
    """Get new access token via Kite Connect login flow."""
    global _req_token
    
    print_info("Starting Kite Connect login flow...")
    
    # Start Flask server in background
    server_thread = threading.Thread(target=run_flask_server, daemon=True)
    server_thread.start()
    
    # Build login URL and open browser
    kite = KiteConnect(api_key=API_KEY)
    login_url = kite.login_url() + f"&redirect_uri={REDIRECT_URI}"
    
    print_info("Opening browser for Kite login...")
    webbrowser.open(login_url)
    
    print_info("Waiting for login completion...")
    
    # Wait for token capture with timeout
    import time
    timeout = 120  # 2 minutes
    start_time = time.time()
    
    while not _req_token and not _server_shutdown:
        if time.time() - start_time > timeout:
            print_error("Login timeout - no response received")
            return None
        time.sleep(0.5)
    
    if not _req_token:
        print_error("Failed to capture request token")
        return None
    
    # Generate access token
    try:
        print_info("Generating access token...")
        session_data = kite.generate_session(_req_token, api_secret=API_SECRET)
        access_token = session_data["access_token"]
        print_success("Access token generated successfully")
        return access_token
        
    except KiteException as e:
        print_error(f"Token generation failed: {e}")
        return None

def get_manual_token() -> str:
    """Get access token via manual entry."""
    print_info("Manual token entry mode")
    token = input("🔑 Enter your Kite access token: ").strip()
    
    if not token:
        print_error("No token provided")
        return None
    
    # Optional: validate manually entered token
    if validate_manual_token(token):
        print_success("Manual token validated")
        return token
    else:
        print_warning("Token validation failed, but proceeding anyway")
        return token

def validate_manual_token(token: str) -> bool:
    """Validate manually entered token."""
    try:
        kite = KiteConnect(api_key=API_KEY)
        kite.set_access_token(token)
        profile = kite.profile()
        return bool(profile and profile.get("user_id"))
    except:
        return False

def update_env_token(access_token: str):
    """Update access token in environment and .env file."""
    if not access_token:
        return
    
    # Update current session
    os.environ["KITE_ACCESS_TOKEN"] = access_token
    
    # Update .env file
    env_file = ".env"
    key = "KITE_ACCESS_TOKEN"
    
    lines = []
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            lines = f.readlines()
    
    updated = False
    with open(env_file, "w") as f:
        for line in lines:
            if line.startswith(f"{key}="):
                f.write(f"{key}={access_token}\n")
                updated = True
            else:
                f.write(line)
        if not updated:
            f.write(f"{key}={access_token}\n")
    
    print_success("Token saved to environment and .env file")

def check_platform_config():
    """Check and display platform configuration status."""
    print_info("Checking platform configuration...")
    
    # Check InfluxDB
    influx_enabled = os.getenv("G6_ENABLE_INFLUXDB", "false").lower() == "true"
    if influx_enabled:
        print_success("InfluxDB: Enabled")
    else:
        print_info("InfluxDB: Disabled")
    
    # Check CSV
    csv_enabled = os.getenv("G6_ENABLE_CSV", "true").lower() == "true"
    if csv_enabled:
        print_success("CSV Storage: Enabled")
    else:
        print_info("CSV Storage: Disabled")
    
    # Check Mock Mode
    mock_mode = os.getenv("G6_MOCK_MODE", "false").lower() == "true"
    if mock_mode:
        print_info("Mode: Mock (simulated data)")
    else:
        print_info("Mode: Live (real market data)")

def launch_platform():
    """Launch the G6.1 platform with proper error handling and robust output decoding."""
    print_header("LAUNCHING G6.1 PLATFORM")
    try:
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")  # prefer UTF-8 mode on Windows
        process = subprocess.Popen(
            [sys.executable, APP_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,                 # text mode (no binary warning)
            encoding="utf-8",          # explicit decoding
            errors="replace",          # never crash on bad bytes
            bufsize=1,                 # line-buffered in text mode
            env=env
        )
        for line in iter(process.stdout.readline, ""):
            print(line.rstrip())
        process.stdout.close()
        return_code = process.wait()
        if return_code == 0:
            print_success("Platform exited successfully")
        else:
            print_warning(f"Platform exited with code: {return_code}")
    except KeyboardInterrupt:
        print_info("Platform interrupted by user")
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            process.kill()
    except Exception as e:
        print_error(f"Failed to launch platform: {e}")


def main():
    """Main application flow."""
    print_header("G6.1 KITE CONNECT AUTHENTICATION")
    
    # Check prerequisites
    if not API_KEY or not API_SECRET:
        print_error("KITE_API_KEY and KITE_API_SECRET must be set in .env file")
        return 1
    
    if not KITE_AVAILABLE:
        print_error("KiteConnect library not available")
        return 1
    
    print_info(f"API Key: {API_KEY[:12]}...")
    
    # Check platform configuration
    check_platform_config()
    
    # Step 1: Validate existing token
    if validate_existing_token():
        print_success("Existing token is valid - launching platform")
        launch_platform()
        return 0
    
    # Step 2: Get new token
    print_warning("No valid access token found")
    print_info("Choose authentication method:")
    print("  1️⃣  Kite Connect login (browser)")
    print("  2️⃣  Enter token manually")
    print("  3️⃣  Continue without token (may fail)")
    
    choice = input("\nEnter choice [1/2/3]: ").strip()
    
    new_token = None
    
    if choice == "1":
        new_token = get_new_token_via_kite()
    elif choice == "2":
        new_token = get_manual_token()
    elif choice == "3":
        print_warning("Continuing without valid token")
        launch_platform()
        return 0
    else:
        print_error("Invalid choice")
        return 1
    
    # Step 3: Save and launch
    if new_token:
        update_env_token(new_token)
        launch_platform()
        return 0
    else:
        print_error("Failed to obtain valid access token")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_info("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)