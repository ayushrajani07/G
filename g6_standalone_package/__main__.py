#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 G6 Options Analytics Platform - Standalone Package Main Entry Point

This is the main entry point for the G6 Options Analytics Platform standalone package.
It provides a clean, production-ready interface for options data collection and analytics.

Features:
- Real-time options data collection from NSE/BSE
- Advanced analytics: Greeks, volatility, PCR analysis  
- Multiple storage backends: CSV and InfluxDB
- Health monitoring and performance metrics
- Production-ready error handling and recovery
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the g6_platform package to the path
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging(level=logging.INFO):
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('g6_platform.log')
        ]
    )

def main():
    """Main entry point for the G6 Platform."""
    parser = argparse.ArgumentParser(
        description='G6 Options Analytics Platform - Standalone Package',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m g6_platform                    # Run with default settings
  python -m g6_platform --debug           # Run with debug logging
  python -m g6_platform --config custom.json  # Use custom config
  
For more information, visit: https://github.com/ayushrajani07/G
        """
    )
    
    parser.add_argument(
        '--config', 
        type=str, 
        default='config.json',
        help='Configuration file path (default: config.json)'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--mock', 
        action='store_true',
        help='Run in mock mode (for testing without real API)'
    )
    
    parser.add_argument(
        '--version', 
        action='version',
        version='G6 Options Analytics Platform v3.0 (Standalone)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Import the platform core
        from g6_platform.core.platform import G6Platform
        
        # Create and configure platform
        platform = G6Platform(
            config_file=args.config,
            mock_mode=args.mock,
            debug=args.debug
        )
        
        logger.info("🚀 Starting G6 Options Analytics Platform...")
        logger.info(f"Configuration: {args.config}")
        logger.info(f"Debug mode: {args.debug}")
        logger.info(f"Mock mode: {args.mock}")
        
        # Run the platform
        platform.run()
        
    except KeyboardInterrupt:
        logger.info("⏹️  Platform stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Platform failed to start: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())