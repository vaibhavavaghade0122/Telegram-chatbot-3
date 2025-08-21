"""
Scheduler module for handling automatic reminder functionality.
Manages the background thread that sends random note reminders.
"""

import threading
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Optional
import telegram
from storage import FileStorage

logger = logging.getLogger(__name__)

class ReminderScheduler:
    """Handles scheduled reminder functionality."""
    
    def __init__(self, bot_token: str, storage: FileStorage, config):
        """
        Initialize the reminder scheduler.
        
        Args:
            bot_token: Telegram bot token
            storage: File storage instance
            config: Configuration instance
        """
        self.bot_token = bot_token
        self.storage = storage
        self.config = config
        self.bot = telegram.Bot(token=bot_token)
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the reminder scheduler in a background thread."""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        logger.info("Reminder scheduler started")
    
    def stop(self):
        """Stop the reminder scheduler."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("Reminder scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop that runs in the background thread."""
        logger.info("Scheduler thread started")
        
        while self._running:
            try:
                today = datetime.now().date()
                
                # Check if today is a reminder day (every other day)
                if today.day % self.config.reminder_interval_days == 0:
                    self._handle_reminder_day()
                else:
                    logger.debug(f"Not a reminder day (day {today.day})")
                    # Sleep for 1 hour and check again
                    self._sleep_with_check(3600)
            
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                # Sleep for 5 minutes before retrying
                self._sleep_with_check(300)
    
    def _handle_reminder_day(self):
        """Handle reminder logic for today."""
        chat_id = self.storage.get_chat_id()
        notes = self.storage.get_notes()
        
        if not chat_id:
            logger.warning("No chat ID found, skipping reminder")
            self._sleep_with_check(3600)
            return
        
        if not notes:
            logger.warning("No notes found, skipping reminder")
            self._sleep_with_check(3600)
            return
        
        # Calculate random send time
        random_hour = random.randint(
            self.config.reminder_start_hour, 
            self.config.reminder_end_hour
        )
        random_minute = random.randint(0, 59)
        
        now = datetime.now()
        send_time = now.replace(
            hour=random_hour, 
            minute=random_minute, 
            second=0, 
            microsecond=0
        )
        
        # If the time has already passed today, schedule for tomorrow
        if now >= send_time:
            send_time += timedelta(days=1)
        
        # Wait until send time
        wait_seconds = (send_time - datetime.now()).total_seconds()
        logger.info(f"Next reminder scheduled for {send_time} (in {wait_seconds:.0f} seconds)")
        
        if self._sleep_with_check(wait_seconds):
            # Send the reminder
            self._send_reminder(chat_id, notes)
            
            # Sleep until next day
            next_check = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)
            sleep_until_next_day = (next_check - datetime.now()).total_seconds()
            self._sleep_with_check(sleep_until_next_day)
    
    def _send_reminder(self, chat_id: str, notes: list):
        """
        Send a random reminder message.
        
        Args:
            chat_id: Telegram chat ID
            notes: List of available notes
        """
        try:
            selected_note = random.choice(notes)
            message = f"📚 Reminder:\n{selected_note}"
            
            self.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Reminder sent: {selected_note[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")
    
    def _sleep_with_check(self, seconds: float) -> bool:
        """
        Sleep for specified seconds while checking if scheduler should stop.
        
        Args:
            seconds: Number of seconds to sleep
            
        Returns:
            bool: True if completed normally, False if interrupted
        """
        end_time = time.time() + seconds
        
        while time.time() < end_time and self._running:
            # Sleep in small chunks to allow for responsive shutdown
            remaining = min(1.0, end_time - time.time())
            if remaining > 0:
                time.sleep(remaining)
        
        return self._running
    
    def send_test_reminder(self, chat_id: str) -> bool:
        """
        Send a test reminder immediately.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        notes = self.storage.get_notes()
        if not notes:
            return False
        
        try:
            self._send_reminder(chat_id, notes)
            return True
        except Exception as e:
            logger.error(f"Failed to send test reminder: {e}")
            return False
