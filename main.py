#!/usr/bin/env python3
"""
Twicket Bot - Automated ticket monitoring and purchasing system.

This application monitors Twickets for available tickets and automatically
attempts to purchase them when found.
"""

import argparse
import logging
import sys
from typing import Optional

from twicket_bot.core.config import TwicketConfig
from twicket_bot.core.bot import TwicketBot


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application."""
    format_string = "%(levelname)s %(asctime)s: %(message)s"
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        format=format_string,
        level=log_level,
        datefmt="%H:%M:%S",
        stream=sys.stdout
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Twicket Bot - Automated ticket monitoring and purchasing system"
    )
    
    parser.add_argument(
        "--config-file",
        type=str,
        help="Path to configuration file (optional, uses environment variables by default)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--event-id",
        type=str,
        help="Override event ID from configuration"
    )
    
    parser.add_argument(
        "--time-delay",
        type=float,
        help="Override time delay between checks (seconds)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (default: True)"
    )
    
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with GUI (overrides --headless)"
    )
    
    return parser.parse_args()


def create_config(args: argparse.Namespace) -> TwicketConfig:
    """Create configuration from arguments and environment."""
    # Start with JSON-based config
    config = TwicketConfig.from_json()
    
    # Override with command line arguments if provided
    if args.event_id:
        config.event_id = args.event_id
    
    if args.time_delay:
        config.time_delay = args.time_delay
    
    if args.no_headless:
        config.headless = False
    elif args.headless:
        config.headless = True
    
    return config


def main() -> int:
    """Main entry point."""
    args = parse_arguments()
    setup_logging(args.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Main       : Initializing Twicket Bot")
    
    try:
        # Create configuration
        config = create_config(args)
        
        # Log basic configuration (without sensitive data)
        logger.info(f"Main       : Event ID: {config.event_id}")
        logger.info(f"Main       : Time delay: {config.time_delay}s")
        logger.info(f"Main       : Headless browser: {config.headless}")
        logger.info(f"Main       : Max seats: {config.max_seats}")
        
        if config.discord_webhook_url:
            logger.info("Main       : Discord webhook notifications enabled")
        
        # Create and run bot
        with TwicketBot(config) as bot:
            bot.run_monitoring_loop()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Main       : Received interrupt signal, shutting down...")
        return 0
    except Exception as e:
        logger.error(f"Main       : Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())