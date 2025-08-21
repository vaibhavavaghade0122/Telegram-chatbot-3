#!/usr/bin/env python3
"""
Test script to verify multimedia support in the Telegram Notes Reminder Bot.
This script tests the database operations for different note types.
"""

import json
import sys
import os
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_storage import DatabaseStorage
from config import Config

def test_multimedia_storage():
    """Test storing and retrieving multimedia notes."""
    print("🧪 Testing multimedia note storage...")
    
    # Initialize components
    config = Config()
    if not config.validate():
        print("❌ Configuration validation failed")
        return False
    
    storage = DatabaseStorage(config.database_url)
    test_user_id = "test_user_123"
    
    # Test user creation
    print("👤 Testing user creation...")
    success = storage.save_user(
        user_id=test_user_id,
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    if success:
        print("✅ User created successfully")
    else:
        print("❌ User creation failed")
        return False
    
    # Test different note types
    test_cases = [
        {
            "type": "text",
            "content": "This is a test text note with multiple sentences. It can contain lists, charts, and longer content.",
            "metadata": {}
        },
        {
            "type": "image",
            "content": "📷 Image: Beautiful sunset photo",
            "metadata": {
                "file_id": "test_image_123",
                "file_path": "files/images/test_image.jpg",
                "file_size": 1024000,
                "width": 1920,
                "height": 1080,
                "caption": "Beautiful sunset photo"
            }
        },
        {
            "type": "voice",
            "content": "🎤 Voice message (30s)",
            "metadata": {
                "file_id": "test_voice_123",
                "file_path": "files/voice/test_voice.ogg",
                "file_size": 256000,
                "duration": 30,
                "mime_type": "audio/ogg"
            }
        },
        {
            "type": "document",
            "content": "📄 Document: project_report.pdf (Important quarterly report)",
            "metadata": {
                "file_id": "test_doc_123",
                "file_path": "files/documents/project_report.pdf",
                "file_size": 2048000,
                "file_name": "project_report.pdf",
                "mime_type": "application/pdf",
                "caption": "Important quarterly report"
            }
        },
        {
            "type": "video",
            "content": "🎥 Video (60s): Tutorial video",
            "metadata": {
                "file_id": "test_video_123",
                "file_path": "files/videos/tutorial.mp4",
                "file_size": 5120000,
                "duration": 60,
                "width": 1280,
                "height": 720,
                "mime_type": "video/mp4",
                "caption": "Tutorial video"
            }
        },
        {
            "type": "audio",
            "content": "🎵 Audio: Amazing Song by Great Artist (No caption)",
            "metadata": {
                "file_id": "test_audio_123",
                "file_path": "files/audio/amazing_song.mp3",
                "file_size": 3072000,
                "duration": 180,
                "performer": "Great Artist",
                "title": "Amazing Song",
                "mime_type": "audio/mpeg",
                "caption": ""
            }
        }
    ]
    
    print(f"📝 Testing {len(test_cases)} different note types...")
    
    for i, case in enumerate(test_cases):
        print(f"  {i+1}. Testing {case['type']} note...")
        success = storage.save_note(
            user_id=test_user_id,
            content=case['content'],
            note_type=case['type'],
            note_metadata=case['metadata']
        )
        if success:
            print(f"    ✅ {case['type']} note saved successfully")
        else:
            print(f"    ❌ {case['type']} note save failed")
            return False
    
    # Test retrieval
    print("📚 Testing note retrieval...")
    notes = storage.get_notes_with_metadata(test_user_id)
    
    if len(notes) == len(test_cases):
        print(f"✅ Retrieved {len(notes)} notes successfully")
        
        # Check each note type
        for note in notes:
            note_type = note.get('note_type', 'unknown')
            content = note.get('content', '')
            metadata = note.get('metadata', {})
            
            print(f"  📋 {note_type}: {content[:50]}...")
            
            if note_type != 'text' and metadata:
                file_path = metadata.get('file_path', '')
                print(f"    📂 File: {file_path}")
    else:
        print(f"❌ Expected {len(test_cases)} notes, got {len(notes)}")
        return False
    
    # Test statistics
    print("📊 Testing statistics...")
    count = storage.get_notes_count(test_user_id)
    if count == len(test_cases):
        print(f"✅ Note count correct: {count}")
    else:
        print(f"❌ Expected count {len(test_cases)}, got {count}")
        return False
    
    # Test cleanup
    print("🧹 Testing cleanup...")
    if storage.clear_notes(test_user_id):
        print("✅ Notes cleared successfully")
        
        # Verify cleanup
        remaining_notes = storage.get_notes_count(test_user_id)
        if remaining_notes == 0:
            print("✅ All notes removed")
        else:
            print(f"❌ Expected 0 notes after cleanup, got {remaining_notes}")
            return False
    else:
        print("❌ Failed to clear notes")
        return False
    
    print("\n🎉 All multimedia storage tests passed!")
    return True

def main():
    """Run all tests."""
    print("🚀 Starting multimedia support tests...\n")
    
    if test_multimedia_storage():
        print("\n✅ All tests passed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())