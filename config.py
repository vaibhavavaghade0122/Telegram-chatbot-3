"""
Configuration module for the Telegram Notes Reminder Bot.
Handles environment variables and application settings.
"""

import os
from typing import Optional

class Config:
    """Configuration class for bot settings."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")
        self.database_url: str = os.getenv("DATABASE_URL", "")
        
        # Reminder settings
        self.reminder_start_hour: int = int(os.getenv("REMINDER_START_HOUR", "8"))
        self.reminder_end_hour: int = int(os.getenv("REMINDER_END_HOUR", "20"))
        self.reminder_interval_days: int = int(os.getenv("REMINDER_INTERVAL_DAYS", "2"))
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        if not self.bot_token or self.bot_token == "PASTE_YOUR_TOKEN_HERE":
            return False
        
        if not self.database_url:
            return False
        
        if self.reminder_start_hour < 0 or self.reminder_start_hour > 23:
            return False
        
        if self.reminder_end_hour < 0 or self.reminder_end_hour > 23:
            return False
        
        if self.reminder_start_hour >= self.reminder_end_hour:
            return False
        
        return True
