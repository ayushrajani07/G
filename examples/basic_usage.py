#!/usr/bin/env python3
"""
G6 Analytics Platform - Basic Usage Example

This example demonstrates the basic usage of the G6 Analytics Platform
for options data collection and analysis.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from g6_platform.core.platform import G6Platform
from g6_platform.config.manager import ConfigManager

def main():
    """Basic usage example."""
    
    print("🚀 G6 Analytics Platform - Basic Usage Example")
    print("=" * 50)
    
    try:
        # Initialize configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        print("📋 Configuration loaded successfully")
        
        # Initialize platform
        platform = G6Platform(config)
        
        print("🏗️ Platform initialized")
        
        # Start data collection
        print("📊 Starting data collection...")
        platform.start()
        
        print("✅ Platform started successfully!")
        print("📈 Check the data/ directory for collected data")
        print("📋 Check the logs/ directory for system logs")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Please ensure:")
        print("   1. API credentials are configured")
        print("   2. Dependencies are installed")
        print("   3. Configuration is valid")

if __name__ == "__main__":
    main()