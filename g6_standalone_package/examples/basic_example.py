#!/usr/bin/env python3
"""
Simple example showing how to use the G6 Options Analytics Platform

This example demonstrates basic usage of the platform for collecting 
NIFTY options data and storing it to CSV files.
"""

import sys
import logging
from pathlib import Path

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """Run a simple example of the G6 platform."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Import the platform
        from g6_platform.core.platform import G6Platform
        
        logger.info("🚀 Starting G6 Platform Example...")
        
        # Create platform with default configuration
        platform = G6Platform(
            config_file='config_template.json',  # Use template config
            mock_mode=True,  # Use mock mode for this example
            debug=True
        )
        
        logger.info("✅ Platform initialized successfully")
        logger.info("This is a simple example. Check the logs for more details.")
        
        # Note: In a real scenario, you would call platform.run()
        # For this example, we just demonstrate initialization
        
    except Exception as e:
        logger.error(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    logger.info("🎉 Example completed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main())