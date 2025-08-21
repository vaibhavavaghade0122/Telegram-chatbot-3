"""
Database storage module for multi-user note storage.
Provides private note storage for each user using PostgreSQL.
"""

import os
import logging
import time
from datetime import datetime
from typing import List, Optional
from functools import wraps
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError

logger = logging.getLogger(__name__)

Base = declarative_base()

def retry_db_operation(max_retries=3, delay=1):
    """Decorator to retry database operations on connection failures."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DisconnectionError) as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}")
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                        raise
                except SQLAlchemyError as e:
                    logger.error(f"Database error in {func.__name__}: {e}")
                    raise
        return wrapper
    return decorator

class User(Base):
    """User table to store basic user information."""
    __tablename__ = 'users'
    
    user_id = Column(String, primary_key=True)  # Telegram user ID
    username = Column(String, nullable=True)    # Telegram username
    first_name = Column(String, nullable=True)  # User's first name
    last_name = Column(String, nullable=True)   # User's last name
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Note(Base):
    """Note table to store user notes privately."""
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)  # Links to User.user_id
    content = Column(Text, nullable=False)    # Note content (text, file paths, etc.)
    note_type = Column(String, nullable=False, default='text')  # text, image, voice, document
    note_metadata = Column(JSON, nullable=True)    # Additional metadata (file info, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Index for faster queries by user_id
    __table_args__ = (Index('idx_user_id', 'user_id'),)

class DatabaseStorage:
    """Database storage for multi-user note management."""
    
    def __init__(self, database_url: str):
        """Initialize database connection with resilient settings."""
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,        # Test connections before using
            pool_recycle=300,          # Recycle connections every 5 minutes
            pool_size=10,              # Connection pool size
            max_overflow=20,           # Additional connections allowed
            connect_args={
                "connect_timeout": 10,  # Connection timeout
                "application_name": "telegram_notes_bot"
            }
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database initialized successfully")
    
    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    @retry_db_operation(max_retries=3, delay=1)
    def save_user(self, user_id: str, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """
        Save or update user information.
        
        Args:
            user_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            session = self.get_session()
            
            # Check if user exists
            user = session.query(User).filter(User.user_id == user_id).first()
            
            if user:
                # Update existing user
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.updated_at = datetime.utcnow()
            else:
                # Create new user
                user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
            
            session.commit()
            logger.info(f"User saved: {user_id}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to save user {user_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    @retry_db_operation(max_retries=3, delay=1)
    def save_note(self, user_id: str, content: str, note_type: str = 'text', note_metadata: dict = None) -> bool:
        """
        Save a note for a specific user.
        
        Args:
            user_id: Telegram user ID
            content: Note content
            note_type: Type of note (text, image, voice, document)
            note_metadata: Additional metadata about the note
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            session = self.get_session()
            
            note = Note(
                user_id=user_id, 
                content=content.strip() if note_type == 'text' else content,
                note_type=note_type,
                note_metadata=note_metadata or {}
            )
            session.add(note)
            session.commit()
            
            logger.info(f"Note saved for user {user_id} (type: {note_type}): {content[:50]}...")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to save note for user {user_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    @retry_db_operation(max_retries=3, delay=1)
    def get_notes(self, user_id: str) -> List[str]:
        """
        Get all notes for a specific user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List[str]: List of user's notes
        """
        try:
            session = self.get_session()
            
            notes = session.query(Note).filter(Note.user_id == user_id).order_by(Note.created_at.desc()).all()
            
            return [note.content for note in notes]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get notes for user {user_id}: {e}")
            return []
        finally:
            session.close()
    
    @retry_db_operation(max_retries=3, delay=1)
    def get_notes_with_metadata(self, user_id: str) -> List[dict]:
        """
        Get all notes for a specific user with metadata.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List[dict]: List of notes with metadata
        """
        try:
            session = self.get_session()
            
            notes = session.query(Note).filter(Note.user_id == user_id).order_by(Note.created_at.desc()).all()
            return [
                {
                    'id': note.id,
                    'content': note.content,
                    'note_type': note.note_type,
                    'metadata': note.note_metadata or {},
                    'created_at': note.created_at
                }
                for note in notes
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get notes with metadata for user {user_id}: {e}")
            return []
        finally:
            session.close()
    
    @retry_db_operation(max_retries=3, delay=1)
    def get_notes_count(self, user_id: str) -> int:
        """
        Get the total number of notes for a specific user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            int: Number of notes
        """
        try:
            session = self.get_session()
            
            count = session.query(Note).filter(Note.user_id == user_id).count()
            return count
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get notes count for user {user_id}: {e}")
            return 0
        finally:
            session.close()
    
    @retry_db_operation(max_retries=3, delay=1)
    def delete_note_by_index(self, user_id: str, index: int) -> bool:
        """
        Delete a specific note by its index for a user.
        
        Args:
            user_id: Telegram user ID
            index: Index of the note to delete (0-based)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            session = self.get_session()
            
            # Get notes ordered by creation date (newest first)
            notes = session.query(Note).filter(Note.user_id == user_id).order_by(Note.created_at.desc()).all()
            
            if not notes or index < 0 or index >= len(notes):
                logger.error(f"Invalid note index {index} for user {user_id}, total notes: {len(notes)}")
                return False
            
            # Delete the note at the specified index
            note_to_delete = notes[index]
            session.delete(note_to_delete)
            session.commit()
            
            logger.info(f"Note deleted for user {user_id} at index {index}: {note_to_delete.content[:50]}...")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete note for user {user_id} at index {index}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    @retry_db_operation(max_retries=3, delay=1)
    def clear_notes(self, user_id: str) -> bool:
        """
        Clear all notes for a specific user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            session = self.get_session()
            
            # Delete all notes for this user
            deleted_count = session.query(Note).filter(Note.user_id == user_id).delete()
            session.commit()
            
            logger.info(f"All notes cleared for user {user_id} ({deleted_count} notes deleted)")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to clear notes for user {user_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_all_user_ids(self) -> List[str]:
        """
        Get all user IDs who have notes (for reminder system).
        
        Returns:
            List[str]: List of user IDs
        """
        try:
            session = self.get_session()
            
            # Get distinct user IDs who have notes
            user_ids = session.query(Note.user_id).distinct().all()
            
            return [user_id[0] for user_id in user_ids]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get user IDs: {e}")
            return []
        finally:
            session.close()
    
    def get_total_users(self) -> int:
        """
        Get total number of users.
        
        Returns:
            int: Number of users
        """
        try:
            session = self.get_session()
            
            count = session.query(User).count()
            return count
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get total users: {e}")
            return 0
        finally:
            session.close()
    
    def get_total_notes(self) -> int:
        """
        Get total number of notes across all users.
        
        Returns:
            int: Number of notes
        """
        try:
            session = self.get_session()
            
            count = session.query(Note).count()
            return count
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get total notes: {e}")
            return 0
        finally:
            session.close()