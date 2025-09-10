#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 ENCODING FIX for Windows - G6.1 Platform Launcher
Author: AI Assistant (Fixed charmap codec error)

SOLUTION: Proper UTF-8 handling for Windows systems
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
import io

# 🔧 CRITICAL FIX: Force UTF-8 encoding on Windows
if os.name == 'nt':
    # Method 1: Reconfigure stdout/stderr
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    
    # Method 2: Set environment variables
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # Method 3: Wrap stdout/stderr with UTF-8
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')
    except Exception:
        pass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import enhanced components with error handling
try:
    from config_manager import get_config, ConfigurationManager
    from enhanced_terminal_ui import TerminalUI
    from enhanced_kite_provider import EnhancedKiteDataProvider
    ENHANCED_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Enhanced components not available: {e}")
    ENHANCED_COMPONENTS_AVAILABLE = False
except UnicodeDecodeError as e:
    print(f"Encoding error importing components: {e}")
    ENHANCED_COMPONENTS_AVAILABLE = False

# Fallback imports
from dotenv import load_dotenv, set_key
load_dotenv()

class EnhancedLauncher:
    """🚀 Enhanced platform launcher with Windows encoding fixes."""
    
    def __init__(self):
        """Initialize enhanced launcher with encoding fixes."""
        # Load configuration with encoding safety
        if ENHANCED_COMPONENTS_AVAILABLE:
            try:
                self.config = get_config()
                self.ui = TerminalUI()
            except UnicodeDecodeError:
                print("Encoding error in configuration - using fallback")
                self.config = None
                self.ui = None
        else:
            self.config = None
            self.ui = None
        
        # Platform state
        self.platform_process = None
        self.is_running = False
        
        # Environment variables
        self.api_key = os.getenv('KITE_API_KEY')
        self.api_secret = os.getenv('KITE_API_SECRET')
        self.access_token = os.getenv('KITE_ACCESS_TOKEN')
        
        print("Enhanced Launcher initialized (encoding-safe)")
    
    def safe_print(self, message: str):
        """🛡️ Safe printing with encoding handling."""
        try:
            print(message)
        except UnicodeEncodeError:
            # Fallback: ASCII-only version
            ascii_message = message.encode('ascii', errors='replace').decode('ascii')
            print(ascii_message)
        except Exception:
            # Ultimate fallback
            try:
                print(message.encode('utf-8', errors='replace').decode('utf-8'))
            except Exception:
                print("Message encoding error")
    
    def launch_platform_safe(self):
        """🚀 Launch platform with encoding fixes."""
        try:
            # Check if main platform file exists
            platform_files = [
                'g6_platform_main_v2.py',
                'g6_platform_main_FINAL_WORKING.py',
                'kite_login_and_launch_FINAL_WORKING.py'
            ]
            
            platform_file = None
            for file_name in platform_files:
                if Path(file_name).exists():
                    platform_file = Path(file_name)
                    break
            
            if not platform_file:
                self.safe_print("No platform file found")
                return False
            
            # Setup environment with encoding fixes
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            env['LANG'] = 'en_US.UTF-8'
            env['LC_ALL'] = 'en_US.UTF-8'
            
            # Create startup info for Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Launch with encoding fixes
            self.platform_process = subprocess.Popen(
                [sys.executable, str(platform_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',  # 🔧 KEY FIX: Replace invalid characters
                bufsize=1,
                env=env,
                startupinfo=startupinfo
            )
            
            self.is_running = True
            self.safe_print(f"Platform launched: {platform_file}")
            
            # Stream output safely
            try:
                for line in iter(self.platform_process.stdout.readline, ''):
                    if line.strip():
                        # Clean line of problematic characters
                        clean_line = line.encode('utf-8', errors='replace').decode('utf-8').strip()
                        self.safe_print(clean_line)
                    
                    # Check if process ended
                    if self.platform_process.poll() is not None:
                        break
                
                # Get exit code
                exit_code = self.platform_process.wait()
                
                if exit_code == 0:
                    self.safe_print("Platform exited successfully")
                else:
                    self.safe_print(f"Platform exited with code: {exit_code}")
                
                return exit_code == 0
                
            except UnicodeDecodeError as e:
                self.safe_print(f"Encoding error in output: {e}")
                return False
            except KeyboardInterrupt:
                self.safe_print("Platform interrupted by user")
                self.stop_platform()
                return True
                
        except Exception as e:
            self.safe_print(f"Platform launch failed: {e}")
            return False
    
    def stop_platform(self):
        """🛑 Stop the running platform safely."""
        if self.platform_process and self.is_running:
            try:
                self.platform_process.terminate()
                try:
                    self.platform_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.platform_process.kill()
                    self.platform_process.wait()
                
                self.is_running = False
                # Don't print here to avoid encoding errors in cleanup
                
            except Exception:
                pass  # Ignore cleanup errors
    
    def run_safe_launcher(self):
        """🖥️ Run the safe launcher interface."""
        try:
            self.safe_print("")
            self.safe_print("=" * 50)
            self.safe_print("G6.1 PLATFORM LAUNCHER v2.0 (Safe Mode)")
            self.safe_print("=" * 50)
            
            while True:
                self.safe_print("")
                self.safe_print("OPTIONS:")
                self.safe_print("1. Launch Platform")
                self.safe_print("2. Test Credentials")
                self.safe_print("3. Setup Configuration")
                self.safe_print("4. Exit")
                
                try:
                    choice = input("Select option [1-4]: ").strip()
                except KeyboardInterrupt:
                    self.safe_print("Interrupted by user")
                    break
                
                if choice == "1":
                    launched = self.launch_platform_safe()
                    if not launched:
                        input("Launch failed. Press Enter to continue...")
                elif choice == "2":
                    self.safe_print(f"API Key: {'Set' if self.api_key else 'Missing'}")
                    self.safe_print(f"Access Token: {'Set' if self.access_token else 'Missing'}")
                    input("Press Enter to continue...")
                elif choice == "3":
                    self.safe_print("Configuration setup:")
                    self.safe_print("1. Edit .env file with your credentials")
                    self.safe_print("2. Copy config_template.json to config.json")
                    input("Press Enter to continue...")
                elif choice == "4":
                    self.safe_print("Goodbye!")
                    break
                else:
                    self.safe_print("Invalid choice")
                    input("Press Enter to continue...")
                    
        except Exception as e:
            self.safe_print(f"Launcher error: {e}")
        finally:
            if self.is_running:
                self.stop_platform()

def main():
    """🚀 Main launcher entry point with encoding fixes."""
    try:
        # Initialize launcher
        launcher = EnhancedLauncher()
        
        # Try enhanced UI first, fallback to safe mode
        if ENHANCED_COMPONENTS_AVAILABLE and launcher.ui:
            try:
                launcher.ui.run_interactive_mode()
            except UnicodeDecodeError:
                print("Encoding error in enhanced UI - switching to safe mode")
                launcher.run_safe_launcher()
            except Exception as e:
                print(f"Enhanced UI error: {e} - switching to safe mode")
                launcher.run_safe_launcher()
        else:
            launcher.run_safe_launcher()
        
        return 0
        
    except Exception as e:
        try:
            print(f"Launcher error: {e}")
        except UnicodeEncodeError:
            print("Critical encoding error")
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)