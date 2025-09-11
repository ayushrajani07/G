#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__main__.py - G6 Analytics Platform Package Entry Point

This module allows the G6 Analytics Platform to be executed as a Python package:
    python -m g6_platform

It provides a clean entry point for the entire platform while maintaining
compatibility with the direct main.py execution method.
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for package execution."""
    try:
        # Import and run the main application
        from main import main as app_main
        app_main()
    except ImportError as e:
        print(f"🔴 Failed to import main application: {e}")
        print("🔧 Please ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"🔴 Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()