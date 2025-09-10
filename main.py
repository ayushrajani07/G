#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 G6.1 Options Analytics Platform - Main Entry Point
Organized modular structure for production use.

Usage:
    python main.py              # Launch with UI
    python main.py --config     # Configure settings  
    python main.py --test       # Run tests
    python main.py --help       # Show help
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main entry point for G6.1 Platform."""
    import argparse
    
    parser = argparse.ArgumentParser(description='G6.1 Options Analytics Platform')
    parser.add_argument('--config', action='store_true', help='Configure platform settings')
    parser.add_argument('--test', action='store_true', help='Run platform tests')
    parser.add_argument('--diagnostic', action='store_true', help='Run platform diagnostics')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode (no API)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    try:
        if args.config:
            from ui.launcher import configure_platform
            configure_platform()
        elif args.test:
            from tests.quick_test import run_all_tests
            run_all_tests()
        elif args.diagnostic:
            from utils.diagnostics import run_platform_diagnostic
            run_platform_diagnostic()
        else:
            # Default: Launch main platform
            from ui.launcher import launch_platform
            launch_platform(mock_mode=args.mock, debug_mode=args.debug)
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please ensure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Platform shutdown requested. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()