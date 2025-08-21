#!/usr/bin/env python3
"""
Main entry point for the Telegram Notes Reminder Bot.
This bot collects user notes and sends random reminders on a scheduled basis.
"""

import logging
import sys
import time
from bot import NotesBot
from config import Config

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to start the bot with auto-restart capability."""
    max_retries = 10
    retry_delay = 30  # seconds
    
    for attempt in range(max_retries):
        try:
            # Load configuration
            config = Config()
            
            # Validate configuration
            if not config.validate():
                logger.error("Configuration validation failed. Please check your environment variables.")
                sys.exit(1)
            
            # Create and start the bot
            bot = NotesBot(config)
            logger.info(f"Starting Telegram Notes Reminder Bot (attempt {attempt + 1}/{max_retries})...")
            bot.start()
            
            # If we reach here, the bot stopped normally
            logger.info("Bot stopped normally")
            break
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Bot crashed with error: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Restarting in {retry_delay} seconds... (attempt {attempt + 2}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)  # Exponential backoff, max 5 minutes
            else:
                logger.error("Max retry attempts reached. Bot will not restart.")
                sys.exit(1)

if __name__ == '__main__':
    main()
