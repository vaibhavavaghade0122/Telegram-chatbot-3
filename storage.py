"""
Storage module for handling file operations for notes and chat IDs.
Provides thread-safe file operations with proper error handling.
"""

import os
import threading
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class FileStorage:
    """Thread-safe file storage for notes and chat IDs."""
    
    def __init__(self, notes_file: str, chat_id_file: str):
        """Initialize file storage with file paths."""
        self.notes_file = notes_file
        self.chat_id_file = chat_id_file
        self._lock = threading.Lock()
    
    def save_note(self, note: str) -> bool:
        """
        Save a note to the notes file.
        
        Args:
            note: The note text to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._lock:
                with open(self.notes_file, "a", encoding="utf-8") as f:
                    f.write(note.strip() + "\n")
                logger.info(f"Note saved: {note[:50]}...")
                return True
        except Exception as e:
            logger.error(f"Failed to save note: {e}")
            return False
    
    def get_notes(self) -> List[str]:
        """
        Get all notes from the notes file.
        
        Returns:
            List[str]: List of all notes
        """
        try:
            with self._lock:
                if not os.path.exists(self.notes_file):
                    return []
                
                with open(self.notes_file, "r", encoding="utf-8") as f:
                    notes = [line.strip() for line in f if line.strip()]
                return notes
        except Exception as e:
            logger.error(f"Failed to read notes: {e}")
            return []
    
    def save_chat_id(self, chat_id: str) -> bool:
        """
        Save chat ID to file.
        
        Args:
            chat_id: The chat ID to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._lock:
                with open(self.chat_id_file, "w", encoding="utf-8") as f:
                    f.write(str(chat_id))
                logger.info(f"Chat ID saved: {chat_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to save chat ID: {e}")
            return False
    
    def get_chat_id(self) -> Optional[str]:
        """
        Get chat ID from file.
        
        Returns:
            Optional[str]: Chat ID if exists, None otherwise
        """
        try:
            with self._lock:
                if not os.path.exists(self.chat_id_file):
                    return None
                
                with open(self.chat_id_file, "r", encoding="utf-8") as f:
                    chat_id = f.read().strip()
                return chat_id if chat_id else None
        except Exception as e:
            logger.error(f"Failed to read chat ID: {e}")
            return None
    
    def get_notes_count(self) -> int:
        """
        Get the total number of notes stored.
        
        Returns:
            int: Number of notes
        """
        return len(self.get_notes())
    
    def clear_notes(self) -> bool:
        """
        Clear all notes from storage.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._lock:
                if os.path.exists(self.notes_file):
                    os.remove(self.notes_file)
                logger.info("All notes cleared")
                return True
        except Exception as e:
            logger.error(f"Failed to clear notes: {e}")
            return False
    
    def delete_note_by_index(self, index: int) -> bool:
        """
        Delete a specific note by its index.
        
        Args:
            index: Index of the note to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._lock:
                # Read notes fresh from file
                if not os.path.exists(self.notes_file):
                    logger.error("Notes file does not exist")
                    return False
                
                with open(self.notes_file, "r", encoding="utf-8") as f:
                    notes = [line.strip() for line in f if line.strip()]
                
                if not notes or index < 0 or index >= len(notes):
                    logger.error(f"Invalid note index: {index}, total notes: {len(notes)}")
                    return False
                
                # Remove the note at the specified index
                deleted_note = notes.pop(index)
                
                # Write the remaining notes back to file
                with open(self.notes_file, "w", encoding="utf-8") as f:
                    for note in notes:
                        f.write(note + "\n")
                
                logger.info(f"Note deleted successfully at index {index}: {deleted_note[:50]}...")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete note at index {index}: {e}")
            return False
