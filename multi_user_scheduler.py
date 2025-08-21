"""
Multi-user scheduler module for handling automatic reminder functionality.
Manages reminders for all users with their private notes.
"""

import threading
import time
import random
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import telegram
from db_storage import DatabaseStorage

logger = logging.getLogger(__name__)

class MultiUserScheduler:
    """Handles scheduled reminder functionality for multiple users."""
    
    def __init__(self, bot_token: str, storage: DatabaseStorage, config):
        """
        Initialize the multi-user scheduler.
        
        Args:
            bot_token: Telegram bot token
            storage: Database storage instance
            config: Configuration instance
        """
        self.bot_token = bot_token
        self.storage = storage
        self.config = config
        self.bot = telegram.Bot(token=bot_token)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._user_reminder_times: Dict[str, datetime] = {}
    
    def start(self):
        """Start the reminder scheduler in a background thread."""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        logger.info("Multi-user reminder scheduler started")
    
    def stop(self):
        """Stop the reminder scheduler."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("Multi-user reminder scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop that runs in the background thread."""
        logger.info("Multi-user scheduler thread started")
        
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
        """Handle reminder logic for all users today."""
        # Get all users who have notes
        user_ids = self.storage.get_all_user_ids()
        
        if not user_ids:
            logger.info("No users with notes found for reminders")
            self._sleep_with_check(3600)
            return
        
        logger.info(f"Processing reminders for {len(user_ids)} users")
        
        # Schedule reminders for all users
        for user_id in user_ids:
            try:
                self._schedule_user_reminder(user_id)
            except Exception as e:
                logger.error(f"Failed to schedule reminder for user {user_id}: {e}")
        
        # Sleep until next day
        next_check = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        sleep_until_next_day = (next_check - datetime.now()).total_seconds()
        self._sleep_with_check(sleep_until_next_day)
    
    def _schedule_user_reminder(self, user_id: str):
        """Schedule a reminder for a specific user."""
        notes = self.storage.get_notes_with_metadata(user_id)
        
        if not notes:
            logger.debug(f"No notes found for user {user_id}, skipping reminder")
            return
        
        # Calculate random send time for this user
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
        
        # Store the reminder time for this user
        self._user_reminder_times[user_id] = send_time
        
        logger.info(f"Reminder scheduled for user {user_id} at {send_time}")
        
        # Start a thread to handle this user's reminder
        reminder_thread = threading.Thread(
            target=self._handle_user_reminder,
            args=(user_id, send_time, notes),
            daemon=True
        )
        reminder_thread.start()
    
    def _handle_user_reminder(self, user_id: str, send_time: datetime, notes: List[dict]):
        """Handle reminder for a specific user."""
        # Wait until send time
        wait_seconds = (send_time - datetime.now()).total_seconds()
        
        if wait_seconds > 0:
            if not self._sleep_with_check(wait_seconds):
                return  # Scheduler was stopped
        
        # Send the reminder
        try:
            self._send_reminder(user_id, notes)
        except Exception as e:
            logger.error(f"Failed to send reminder to user {user_id}: {e}")
    
    def _send_reminder(self, user_id: str, notes: List[dict]):
        """
        Send a random reminder message to a user.
        
        Args:
            user_id: Telegram user ID
            notes: List of user's notes with metadata
        """
        try:
            selected_note = random.choice(notes)
            note_type = selected_note.get('note_type', 'text')
            content = selected_note.get('content', '')
            metadata = selected_note.get('metadata', {})
            
            message = f"📚 Reminder:\n{content}"
            
            if note_type == 'text':
                # Send text message
                self.bot.send_message(chat_id=user_id, text=message)
                
            elif note_type == 'image':
                # Send image with caption
                file_path = metadata.get('file_path', '')
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as photo:
                            self.bot.send_photo(chat_id=user_id, photo=photo, caption=message)
                    except Exception as e:
                        logger.error(f"Failed to send image file: {e}")
                        # Fall back to text message
                        self.bot.send_message(chat_id=user_id, text=message)
                else:
                    # Fall back to text message if file not found
                    self.bot.send_message(chat_id=user_id, text=message)
                    
            elif note_type == 'voice':
                # Send voice message with caption
                file_path = metadata.get('file_path', '')
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as voice:
                            self.bot.send_voice(chat_id=user_id, voice=voice, caption=message)
                    except Exception as e:
                        logger.error(f"Failed to send voice file: {e}")
                        # Fall back to text message
                        self.bot.send_message(chat_id=user_id, text=message)
                else:
                    # Fall back to text message if file not found
                    self.bot.send_message(chat_id=user_id, text=message)
                    
            elif note_type == 'document':
                # Send document with caption
                file_path = metadata.get('file_path', '')
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as document:
                            self.bot.send_document(chat_id=user_id, document=document, caption=message)
                    except Exception as e:
                        logger.error(f"Failed to send document file: {e}")
                        # Fall back to text message
                        self.bot.send_message(chat_id=user_id, text=message)
                else:
                    # Fall back to text message if file not found
                    self.bot.send_message(chat_id=user_id, text=message)
                    
            elif note_type == 'video':
                # Send video with caption
                file_path = metadata.get('file_path', '')
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as video:
                            self.bot.send_video(chat_id=user_id, video=video, caption=message)
                    except Exception as e:
                        logger.error(f"Failed to send video file: {e}")
                        # Fall back to text message
                        self.bot.send_message(chat_id=user_id, text=message)
                else:
                    # Fall back to text message if file not found
                    self.bot.send_message(chat_id=user_id, text=message)
                    
            elif note_type == 'audio':
                # Send audio with caption
                file_path = metadata.get('file_path', '')
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as audio:
                            self.bot.send_audio(chat_id=user_id, audio=audio, caption=message)
                    except Exception as e:
                        logger.error(f"Failed to send audio file: {e}")
                        # Fall back to text message
                        self.bot.send_message(chat_id=user_id, text=message)
                else:
                    # Fall back to text message if file not found
                    self.bot.send_message(chat_id=user_id, text=message)
            else:
                # Default to text message for unknown types
                self.bot.send_message(chat_id=user_id, text=message)
            
            logger.info(f"Reminder sent to user {user_id}: {note_type} - {content[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to send reminder to user {user_id}: {e}")
    
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
    
    def send_test_reminder(self, user_id: str) -> bool:
        """
        Send a test reminder to a specific user immediately.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        notes = self.storage.get_notes_with_metadata(user_id)
        if not notes:
            return False
        
        try:
            self._send_reminder(user_id, notes)
            return True
        except Exception as e:
            logger.error(f"Failed to send test reminder to user {user_id}: {e}")
            return False
    
    def get_next_reminder_time(self, user_id: str) -> Optional[datetime]:
        """
        Get the next scheduled reminder time for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Optional[datetime]: Next reminder time if scheduled, None otherwise
        """
        return self._user_reminder_times.get(user_id)
    
    def get_scheduler_stats(self) -> Dict:
        """
        Get scheduler statistics.
        
        Returns:
            Dict: Statistics about the scheduler
        """
        total_users = self.storage.get_total_users()
        total_notes = self.storage.get_total_notes()
        active_users = len(self.storage.get_all_user_ids())
        scheduled_reminders = len(self._user_reminder_times)
        
        return {
            'total_users': total_users,
            'total_notes': total_notes,
            'active_users': active_users,
            'scheduled_reminders': scheduled_reminders,
            'running': self._running
        }