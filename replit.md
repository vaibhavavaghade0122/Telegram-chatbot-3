# Telegram Notes Reminder Bot

## Overview

This is a multi-user Telegram bot that collects multimedia content (text, images, voice messages, documents, videos, audio) and sends random reminders on a scheduled basis. The bot stores all types of content as private notes in a PostgreSQL database and automatically sends random reminders every other day at random times between 8 AM and 8 PM. Each user has their own private note collection that is completely isolated from other users. The system has evolved from a single-user file-based application to a robust multi-user database-backed solution with full multimedia support.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

### Core Components
- **Main Entry Point** (`main.py`): Handles application startup and configuration validation
- **Bot Handler** (`bot.py`): Manages Telegram interactions and coordinates all components
- **Configuration** (`config.py`): Handles environment variables and application settings
- **Database Storage** (`db_storage.py`): Provides PostgreSQL-based multi-user note storage
- **Multi-User Scheduler** (`multi_user_scheduler.py`): Manages background reminder functionality for all users
- **Legacy Storage** (`storage.py`): Deprecated file-based storage system
- **Legacy Scheduler** (`scheduler.py`): Deprecated single-user scheduler

### Architecture Pattern
The system uses a **layered architecture** with:
- **Presentation Layer**: Telegram bot interface
- **Business Logic Layer**: Note management and scheduling logic
- **Data Layer**: PostgreSQL database with multi-user support

## Key Components

### 1. Telegram Bot Interface
- **Technology**: Python Telegram Bot library
- **Purpose**: Handles user interactions, commands, and message processing
- **Commands**: `/start`, `/help`, `/stats`, `/test`, `/clear`, `/clearall`
- **Features**: Inline keyboards, callback handling, command menu setup

### 2. Database Storage System
- **Implementation**: PostgreSQL with SQLAlchemy ORM
- **Database Tables**: 
  - `users`: Stores user information (Telegram user ID, username, names, timestamps)
  - `notes`: Stores private notes for each user (with user_id foreign key)
- **Rationale**: Scalable multi-user solution with proper data isolation and security

### 3. Multi-User Background Scheduler
- **Implementation**: Background thread with daemon mode for multi-user support
- **Functionality**: Sends random note reminders every other day at random times for all users
- **Time Range**: 8 AM - 8 PM (configurable)
- **Selection**: Random note selection from each user's private collection
- **Isolation**: Each user receives reminders independently

### 4. Configuration Management
- **Method**: Environment variables with sensible defaults
- **Validation**: Built-in configuration validation
- **Data Organization**: Automatic data directory creation

## Data Flow

1. **User Registration**: User sends `/start` → Bot saves user info to `users` table
2. **Note Collection**: User sends text message → Bot saves to `notes` table with user_id
3. **Multi-User Scheduling**: Background thread → Queries all users → Sends individual reminders
4. **Command Processing**: User commands → Bot processes with user context → Responds with appropriate action
5. **Privacy Isolation**: Each user only sees their own notes and statistics

## External Dependencies

### Required Libraries
- `python-telegram-bot==13.15`: Telegram Bot API wrapper (specific version for stability)
- `sqlalchemy`: Database ORM for PostgreSQL operations
- `psycopg2-binary`: PostgreSQL database adapter
- `threading`: Background task management
- `datetime`: Time and date operations
- `random`: Random selection functionality
- `os`: Environment variable access
- `logging`: Application logging

### Telegram Integration
- **Bot Token**: Required from @BotFather
- **API**: Telegram Bot API for message sending and receiving
- **Webhooks**: Not used - polling-based approach

## Deployment Strategy

### Environment Setup
- **Configuration**: Environment variables (`.env` file support)
- **Data Directory**: Automatic creation of `data/` directory
- **File Permissions**: Standard file system permissions

### Runtime Requirements
- **Python**: Python 3.x environment
- **Bot Token**: Valid Telegram bot token
- **File System**: Write access for note storage
- **Network**: Internet connection for Telegram API

### Operational Considerations
- **Background Processing**: Daemon thread for scheduling
- **Error Handling**: Comprehensive logging and error recovery
- **Resource Usage**: Minimal memory footprint with file-based storage
- **Scalability**: Single-user design, files stored locally

### Security Features
- **Token Management**: Environment variable storage
- **File Access**: Local file system only
- **Thread Safety**: Proper locking mechanisms
- **Input Validation**: Configuration validation on startup

## Recent Changes (July 2025)

### Multi-User Architecture Migration
- **From**: Single-user file-based storage (`storage.py`, `scheduler.py`)
- **To**: Multi-user PostgreSQL database system (`db_storage.py`, `multi_user_scheduler.py`)
- **Key Changes**:
  - Added `users` and `notes` tables with proper foreign key relationships
  - Implemented user isolation - each user has private note collection
  - Updated all bot commands to work with user context
  - Multi-user scheduler handles reminders for all users independently
  - Enhanced privacy and security with database-backed storage

### Always Active Bot Enhancement
- **Auto-restart capability**: Bot automatically restarts on crashes with exponential backoff
- **Database resilience**: Retry logic for database operations with connection pooling
- **Enhanced polling**: Optimized Telegram API polling with proper error handling
- **Connection management**: Pool pre-ping, connection recycling, and timeout handling
- **Graceful shutdown**: Proper cleanup of resources on shutdown

### Database Schema
- `users` table: Stores user information (user_id, username, names, timestamps)
- `notes` table: Stores private notes with multimedia support and user_id foreign key
  - `note_type` field: Supports text, image, voice, document, video, audio
  - `note_metadata` field: JSON metadata for file information, captions, and media attributes
- Proper indexing on user_id for efficient queries

### Multimedia Support (July 2025)
- **File Storage**: Organized directory structure in `files/` with subdirectories for each media type
- **Supported Content Types**:
  - Text messages (single sentences, paragraphs, lists, charts)
  - Images and photos with captions
  - Voice messages
  - Documents and files
  - Videos with captions
  - Audio files
- **Rich Reminders**: Reminders are sent in original format (text, image, voice, etc.)
- **File Management**: Automatic file download, storage, and retrieval for reminders
- **Fallback Handling**: Graceful degradation to text messages if media files are unavailable

The system now supports unlimited users with complete multimedia capabilities while maintaining privacy and data isolation, with robust reliability features making it suitable for production deployment with high availability.