# Telegram Notes Reminder Bot

A multi-user Telegram bot that collects multimedia content (text, images, voice messages, documents, videos, audio) as private notes and sends random reminders on a scheduled basis. Each user has their own private note collection stored securely in a PostgreSQL database.

## Features

- 🔐 **Multi-User Support**: Each user has their own private note collection
- 📝 **Multimedia Note Collection**: Send various types of content:
  - Text messages (single sentences, paragraphs, lists, charts)
  - Images and photos with captions
  - Voice messages
  - Documents and files
  - Videos with captions
  - Audio files
- ⏰ **Smart Scheduling**: Automatic reminders every other day at random times (8 AM - 8 PM by default)
- 🎲 **Random Selection**: Bot picks random notes from your collection for reminders
- 📱 **Rich Reminders**: Receive reminders in original format (text, image, voice, etc.)
- 💾 **Database Storage**: Secure PostgreSQL database storage for all users
- 🔒 **Complete Privacy**: Users can only see their own notes
- 🧵 **Background Processing**: Multi-user reminder system runs in background thread
- 🔄 **Always Active**: Auto-restart on failures with exponential backoff and database retry logic

## Commands

- `/start` - Start using the bot and see welcome message
- `/help` - Show help information and usage instructions
- `/stats` - View your personal notes statistics
- `/test` - Send a test reminder immediately
- `/clear` - Select and delete individual notes
- `/clearall` - Delete all your notes

## Installation

1. **Create a Telegram Bot**:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Use `/newbot` command and follow instructions
   - Copy your bot token

2. **Set up PostgreSQL Database**:
   - Create a PostgreSQL database
   - Get your database connection string

3. **Set up Environment**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your credentials
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   DATABASE_URL=your_postgresql_connection_string
   ```

4. **Run the Bot**:
   ```bash
   python main.py
   ```

## Configuration

The bot can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Required | Your Telegram bot token |
| `DATABASE_URL` | Required | PostgreSQL database connection string |
| `REMINDER_START_HOUR` | `8` | Earliest hour for reminders (24h format) |
| `REMINDER_END_HOUR` | `20` | Latest hour for reminders (24h format) |
| `REMINDER_INTERVAL_DAYS` | `2` | Days between reminder checks |

## How It Works

1. **Note Collection**: When you send any content (text, image, voice, document, video, audio), the bot saves it to your private database collection
2. **User Management**: Each user is tracked separately with their own note collection
3. **File Storage**: Media files are stored in organized directories (`files/images/`, `files/voice/`, etc.)
4. **Scheduling**: A background thread manages reminders for all users individually
5. **Reminder Day Logic**: Reminders are sent every other day (when day number is even)
6. **Random Timing**: On reminder days, a random time between 8 AM - 8 PM is selected for each user
7. **Note Selection**: A random note from your personal collection is chosen and sent as reminder in original format

## Database Schema

The bot uses PostgreSQL with the following tables:
- `users` - User information (Telegram user ID, username, names, timestamps)
- `notes` - User notes with multimedia support (private to each user, with user_id foreign key)
  - `note_type` - Type of content (text, image, voice, document, video, audio)
  - `note_metadata` - JSON metadata for file information and captions

## File Structure

- `main.py` - Main entry point
- `bot.py` - Bot functionality and message handling
- `db_storage.py` - Database storage operations for multi-user support
- `multi_user_scheduler.py` - Multi-user reminder scheduling logic
- `config.py` - Configuration management

## Privacy & Security

- Each user has completely private note storage
- Notes are stored securely in PostgreSQL database
- Users cannot access other users' notes
- All data is encrypted in transit and at rest
- No data is sent to external services except Telegram

## Dependencies

- `python-telegram-bot==13.15` - Telegram Bot API wrapper
- `sqlalchemy` - Database ORM
- `psycopg2-binary` - PostgreSQL adapter

## Support

For issues or questions, please create an issue in the repository.