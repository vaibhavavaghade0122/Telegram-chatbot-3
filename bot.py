"""
Main bot module that handles Telegram interactions and coordinates all components.
"""

import logging
import os
import json
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import CallbackContext
from db_storage import DatabaseStorage
from multi_user_scheduler import MultiUserScheduler
from config import Config

logger = logging.getLogger(__name__)

class NotesBot:
    """Main bot class that handles all Telegram interactions."""
    
    def __init__(self, config: Config):
        """
        Initialize the notes bot.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.storage = DatabaseStorage(config.database_url)
        self.scheduler = MultiUserScheduler(config.bot_token, self.storage, config)
        self.updater = Updater(config.bot_token, use_context=True)
        
        # Set up handlers
        self._setup_handlers()
        
        # Set up command menu
        self._setup_command_menu()
    
    def _setup_handlers(self):
        """Set up message and command handlers."""
        dp = self.updater.dispatcher
        
        # Command handlers
        dp.add_handler(CommandHandler("start", self.start_command))
        dp.add_handler(CommandHandler("help", self.help_command))
        dp.add_handler(CommandHandler("stats", self.stats_command))
        dp.add_handler(CommandHandler("test", self.test_command))
        dp.add_handler(CommandHandler("clear", self.clear_command))
        dp.add_handler(CommandHandler("clearall", self.clear_all_command))
        
        # Callback query handler for inline buttons
        dp.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handlers for different content types
        dp.add_handler(MessageHandler(
            Filters.text & ~Filters.command, 
            self.handle_text_message
        ))
        dp.add_handler(MessageHandler(
            Filters.photo, 
            self.handle_photo_message
        ))
        dp.add_handler(MessageHandler(
            Filters.voice, 
            self.handle_voice_message
        ))
        dp.add_handler(MessageHandler(
            Filters.document, 
            self.handle_document_message
        ))
        dp.add_handler(MessageHandler(
            Filters.video, 
            self.handle_video_message
        ))
        dp.add_handler(MessageHandler(
            Filters.audio, 
            self.handle_audio_message
        ))
    
    def start_command(self, update: Update, context: CallbackContext):
        """Handle /start command."""
        user = update.message.from_user
        user_id = str(user.id)
        
        # Save user information
        self.storage.save_user(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        welcome_message = (
            "🗒️ Welcome to Notes Reminder Bot!\n\n"
            "📝 Send me any content and I'll save it as your private note:\n"
            "• Text messages (multiple sentences, lists, charts)\n"
            "• Images and photos\n"
            "• Voice messages\n"
            "• Documents and files\n"
            "• Videos and audio\n\n"
            "⏰ I'll send you random reminders every other day.\n"
            "🔒 Your notes are completely private and secure.\n\n"
            "Commands:\n"
            "/help - Show this help message\n"
            "/stats - Show your notes statistics\n"
            "/test - Send a test reminder now\n"
            "/clear - Select and delete individual notes\n"
            "/clearall - Delete all your notes"
        )
        update.message.reply_text(welcome_message)
        
        logger.info(f"New user started: {user_id} (@{user.username})")
    
    def help_command(self, update: Update, context: CallbackContext):
        """Handle /help command."""
        help_message = (
            "🤖 Notes Reminder Bot Help\n\n"
            "📝 How to use:\n"
            "• Send any content to save it as a note:\n"
            "  - Text messages (long text, lists, charts)\n"
            "  - Images and photos\n"
            "  - Voice messages\n"
            "  - Documents and files\n"
            "  - Videos and audio\n"
            "• I'll automatically send you random reminders\n\n"
            "⏰ Reminder schedule:\n"
            f"• Every {self.config.reminder_interval_days} days\n"
            f"• Between {self.config.reminder_start_hour}:00 and {self.config.reminder_end_hour}:00\n"
            "• Random time within the window\n\n"
            "🔧 Commands:\n"
            "/start - Start using the bot\n"
            "/stats - View your notes statistics\n"
            "/test - Get a random reminder now\n"
            "/clear - Select and delete individual notes\n"
            "/clearall - Delete all your notes\n"
            "/help - Show this message"
        )
        update.message.reply_text(help_message)
    
    def stats_command(self, update: Update, context: CallbackContext):
        """Handle /stats command."""
        user_id = str(update.message.from_user.id)
        notes_count = self.storage.get_notes_count(user_id)
        
        stats_message = (
            f"📊 Your Notes Statistics\n\n"
            f"📝 Your notes: {notes_count}\n"
            f"⏰ Reminder interval: Every {self.config.reminder_interval_days} days\n"
            f"🕐 Reminder window: {self.config.reminder_start_hour}:00 - {self.config.reminder_end_hour}:00"
        )
        
        if notes_count == 0:
            stats_message += "\n\n💡 Send me a message to create your first note!"
        
        update.message.reply_text(stats_message)
    
    def test_command(self, update: Update, context: CallbackContext):
        """Handle /test command - send a test reminder."""
        user_id = str(update.message.from_user.id)
        
        if self.scheduler.send_test_reminder(user_id):
            update.message.reply_text("✅ Test reminder sent!")
        else:
            update.message.reply_text(
                "❌ No notes available for reminder. "
                "Send me some messages first!"
            )
    
    def clear_command(self, update: Update, context: CallbackContext):
        """Handle /clear command - show notes for selective deletion."""
        user_id = str(update.message.from_user.id)
        notes = self.storage.get_notes(user_id)
        
        if not notes:
            update.message.reply_text(
                "📝 You don't have any notes to delete.\n"
                "Send me some messages first!"
            )
            return
        
        # Create inline keyboard with notes (max 10 per page)
        keyboard = []
        for i, note in enumerate(notes[:10]):  # Limit to first 10 notes
            # Truncate long notes for display
            display_text = note[:50] + "..." if len(note) > 50 else note
            keyboard.append([InlineKeyboardButton(
                f"🗑️ {display_text}", 
                callback_data=f"delete_{i}"
            )])
        
        # Add cancel button
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = (
            "🗑️ Select a note to delete:\n\n"
            f"Showing {min(10, len(notes))} of {len(notes)} notes"
        )
        
        update.message.reply_text(message_text, reply_markup=reply_markup)

    def clear_all_command(self, update: Update, context: CallbackContext):
        """Handle /clearall command - clear all notes."""
        user_id = str(update.message.from_user.id)
        
        if self.storage.clear_notes(user_id):
            update.message.reply_text(
                "🗑️ All your notes have been cleared!\n"
                "Send me new messages to start collecting notes again."
            )
        else:
            update.message.reply_text("❌ Failed to clear notes. Please try again.")
    
    def button_callback(self, update: Update, context: CallbackContext):
        """Handle button callbacks for note deletion."""
        try:
            query = update.callback_query
            query.answer()  # Acknowledge the callback immediately
            
            logger.info(f"Button callback received: {query.data}")
            
            if query.data == "cancel":
                query.edit_message_text("❌ Deletion cancelled.")
                return
            
            if query.data.startswith("delete_"):
                try:
                    note_index = int(query.data.split("_")[1])
                    user_id = str(query.from_user.id)
                    notes = self.storage.get_notes(user_id)
                    
                    logger.info(f"Attempting to delete note at index {note_index} for user {user_id}, total notes: {len(notes)}")
                    
                    if 0 <= note_index < len(notes):
                        deleted_note = notes[note_index]
                        logger.info(f"Deleting note: {deleted_note[:30]}...")
                        
                        if self.storage.delete_note_by_index(user_id, note_index):
                            # Truncate for display
                            display_note = deleted_note[:50] + "..." if len(deleted_note) > 50 else deleted_note
                            query.edit_message_text(
                                f"✅ Note deleted successfully!\n\n"
                                f"Deleted: {display_note}"
                            )
                            logger.info(f"Note deleted successfully: {deleted_note[:50]}...")
                        else:
                            query.edit_message_text("❌ Failed to delete note. Please try again.")
                            logger.error("Failed to delete note from storage")
                    else:
                        query.edit_message_text("❌ Invalid note selection.")
                        logger.error(f"Invalid note index: {note_index}")
                        
                except ValueError as e:
                    logger.error(f"Invalid note index format: {e}")
                    query.edit_message_text("❌ Invalid selection format.")
                except Exception as e:
                    logger.error(f"Error processing note deletion: {e}")
                    query.edit_message_text("❌ Error deleting note. Please try again.")
            
        except Exception as e:
            logger.error(f"Error in button callback: {e}")
            try:
                update.callback_query.edit_message_text("❌ Something went wrong. Please try again.")
            except:
                pass
    
    def _setup_command_menu(self):
        """Set up the command menu that appears when typing /"""
        try:
            commands = [
                BotCommand("start", "Start using the bot"),
                BotCommand("help", "Show help information"),
                BotCommand("stats", "View your notes statistics"),
                BotCommand("test", "Send a test reminder now"),
                BotCommand("clear", "Select and delete individual notes"),
                BotCommand("clearall", "Delete all your notes")
            ]
            
            # Set the command menu
            self.updater.bot.set_my_commands(commands)
            logger.info("Command menu set successfully")
            
        except Exception as e:
            logger.error(f"Failed to set command menu: {e}")
    
    def handle_text_message(self, update: Update, context: CallbackContext):
        """
        Handle incoming text messages and save them as notes.
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        text = update.message.text.strip()
        user = update.message.from_user
        user_id = str(user.id)
        
        if not text:
            update.message.reply_text("❌ Empty message. Please send some text!")
            return
        
        # Save/update user information
        self.storage.save_user(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Save the note
        if self.storage.save_note(user_id, text):
            notes_count = self.storage.get_notes_count(user_id)
            response = f"📝 Note saved! (Total: {notes_count})"
            
            # Add encouragement for first note
            if notes_count == 1:
                response += "\n🎉 Your first note! I'll start sending you reminders."
        else:
            response = "❌ Failed to save note. Please try again."
        
        update.message.reply_text(response)
        logger.info(f"Note saved from {user_id} (@{user.username}): {text[:50]}...")
    
    def handle_photo_message(self, update: Update, context: CallbackContext):
        """Handle incoming photo messages and save them as notes."""
        try:
            user = update.message.from_user
            user_id = str(user.id)
            
            # Save/update user information
            self.storage.save_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Get the largest photo
            photo = update.message.photo[-1]
            file_id = photo.file_id
            
            # Download the file
            file_obj = context.bot.get_file(file_id)
            file_extension = file_obj.file_path.split('.')[-1] if '.' in file_obj.file_path else 'jpg'
            filename = f"{user_id}_{file_id}.{file_extension}"
            file_path = f"files/images/{filename}"
            
            # Download and save the file
            file_obj.download(file_path)
            
            # Prepare metadata
            metadata = {
                'file_id': file_id,
                'file_path': file_path,
                'file_size': photo.file_size,
                'width': photo.width,
                'height': photo.height,
                'caption': update.message.caption or ''
            }
            
            # Save the note with caption and file path
            content = f"📷 Image: {update.message.caption or 'No caption'}"
            
            if self.storage.save_note(user_id, content, 'image', metadata):
                notes_count = self.storage.get_notes_count(user_id)
                response = f"📷 Image saved! (Total: {notes_count})"
                if notes_count == 1:
                    response += "\n🎉 Your first note! I'll start sending you reminders."
            else:
                response = "❌ Failed to save image. Please try again."
            
            update.message.reply_text(response)
            logger.info(f"Image saved from {user_id} (@{user.username}): {filename}")
            
        except Exception as e:
            logger.error(f"Error handling photo message: {e}")
            update.message.reply_text("❌ Failed to save image. Please try again.")
    
    def handle_voice_message(self, update: Update, context: CallbackContext):
        """Handle incoming voice messages and save them as notes."""
        try:
            user = update.message.from_user
            user_id = str(user.id)
            
            # Save/update user information
            self.storage.save_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Get voice message
            voice = update.message.voice
            file_id = voice.file_id
            
            # Download the file
            file_obj = context.bot.get_file(file_id)
            filename = f"{user_id}_{file_id}.ogg"
            file_path = f"files/voice/{filename}"
            
            # Download and save the file
            file_obj.download(file_path)
            
            # Prepare metadata
            metadata = {
                'file_id': file_id,
                'file_path': file_path,
                'file_size': voice.file_size,
                'duration': voice.duration,
                'mime_type': voice.mime_type
            }
            
            # Save the note
            content = f"🎤 Voice message ({voice.duration}s)"
            
            if self.storage.save_note(user_id, content, 'voice', metadata):
                notes_count = self.storage.get_notes_count(user_id)
                response = f"🎤 Voice message saved! (Total: {notes_count})"
                if notes_count == 1:
                    response += "\n🎉 Your first note! I'll start sending you reminders."
            else:
                response = "❌ Failed to save voice message. Please try again."
            
            update.message.reply_text(response)
            logger.info(f"Voice message saved from {user_id} (@{user.username}): {filename}")
            
        except Exception as e:
            logger.error(f"Error handling voice message: {e}")
            update.message.reply_text("❌ Failed to save voice message. Please try again.")
    
    def handle_document_message(self, update: Update, context: CallbackContext):
        """Handle incoming document messages and save them as notes."""
        try:
            user = update.message.from_user
            user_id = str(user.id)
            
            # Save/update user information
            self.storage.save_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Get document
            document = update.message.document
            file_id = document.file_id
            
            # Download the file
            file_obj = context.bot.get_file(file_id)
            filename = f"{user_id}_{file_id}_{document.file_name}"
            file_path = f"files/documents/{filename}"
            
            # Download and save the file
            file_obj.download(file_path)
            
            # Prepare metadata
            metadata = {
                'file_id': file_id,
                'file_path': file_path,
                'file_size': document.file_size,
                'file_name': document.file_name,
                'mime_type': document.mime_type,
                'caption': update.message.caption or ''
            }
            
            # Save the note
            content = f"📄 Document: {document.file_name} ({update.message.caption or 'No caption'})"
            
            if self.storage.save_note(user_id, content, 'document', metadata):
                notes_count = self.storage.get_notes_count(user_id)
                response = f"📄 Document saved! (Total: {notes_count})"
                if notes_count == 1:
                    response += "\n🎉 Your first note! I'll start sending you reminders."
            else:
                response = "❌ Failed to save document. Please try again."
            
            update.message.reply_text(response)
            logger.info(f"Document saved from {user_id} (@{user.username}): {document.file_name}")
            
        except Exception as e:
            logger.error(f"Error handling document message: {e}")
            update.message.reply_text("❌ Failed to save document. Please try again.")
    
    def handle_video_message(self, update: Update, context: CallbackContext):
        """Handle incoming video messages and save them as notes."""
        try:
            user = update.message.from_user
            user_id = str(user.id)
            
            # Save/update user information
            self.storage.save_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Get video
            video = update.message.video
            file_id = video.file_id
            
            # Download the file
            file_obj = context.bot.get_file(file_id)
            file_extension = file_obj.file_path.split('.')[-1] if '.' in file_obj.file_path else 'mp4'
            filename = f"{user_id}_{file_id}.{file_extension}"
            file_path = f"files/videos/{filename}"
            
            # Download and save the file
            file_obj.download(file_path)
            
            # Prepare metadata
            metadata = {
                'file_id': file_id,
                'file_path': file_path,
                'file_size': video.file_size,
                'duration': video.duration,
                'width': video.width,
                'height': video.height,
                'mime_type': video.mime_type,
                'caption': update.message.caption or ''
            }
            
            # Save the note
            content = f"🎥 Video ({video.duration}s): {update.message.caption or 'No caption'}"
            
            if self.storage.save_note(user_id, content, 'video', metadata):
                notes_count = self.storage.get_notes_count(user_id)
                response = f"🎥 Video saved! (Total: {notes_count})"
                if notes_count == 1:
                    response += "\n🎉 Your first note! I'll start sending you reminders."
            else:
                response = "❌ Failed to save video. Please try again."
            
            update.message.reply_text(response)
            logger.info(f"Video saved from {user_id} (@{user.username}): {filename}")
            
        except Exception as e:
            logger.error(f"Error handling video message: {e}")
            update.message.reply_text("❌ Failed to save video. Please try again.")
    
    def handle_audio_message(self, update: Update, context: CallbackContext):
        """Handle incoming audio messages and save them as notes."""
        try:
            user = update.message.from_user
            user_id = str(user.id)
            
            # Save/update user information
            self.storage.save_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Get audio
            audio = update.message.audio
            file_id = audio.file_id
            
            # Download the file
            file_obj = context.bot.get_file(file_id)
            file_extension = file_obj.file_path.split('.')[-1] if '.' in file_obj.file_path else 'mp3'
            filename = f"{user_id}_{file_id}.{file_extension}"
            file_path = f"files/audio/{filename}"
            
            # Download and save the file
            file_obj.download(file_path)
            
            # Prepare metadata
            metadata = {
                'file_id': file_id,
                'file_path': file_path,
                'file_size': audio.file_size,
                'duration': audio.duration,
                'performer': audio.performer,
                'title': audio.title,
                'mime_type': audio.mime_type,
                'caption': update.message.caption or ''
            }
            
            # Save the note
            content = f"🎵 Audio: {audio.title or 'Untitled'} by {audio.performer or 'Unknown'} ({update.message.caption or 'No caption'})"
            
            if self.storage.save_note(user_id, content, 'audio', metadata):
                notes_count = self.storage.get_notes_count(user_id)
                response = f"🎵 Audio saved! (Total: {notes_count})"
                if notes_count == 1:
                    response += "\n🎉 Your first note! I'll start sending you reminders."
            else:
                response = "❌ Failed to save audio. Please try again."
            
            update.message.reply_text(response)
            logger.info(f"Audio saved from {user_id} (@{user.username}): {audio.title or 'Untitled'}")
            
        except Exception as e:
            logger.error(f"Error handling audio message: {e}")
            update.message.reply_text("❌ Failed to save audio. Please try again.")
    
    def start(self):
        """Start the bot and scheduler with enhanced error handling."""
        try:
            # Start the reminder scheduler
            self.scheduler.start()
            
            # Start the bot with enhanced polling settings
            logger.info("Starting Telegram bot polling...")
            self.updater.start_polling(
                poll_interval=1.0,  # Check for updates every second
                timeout=30,         # Request timeout
                drop_pending_updates=True  # Drop pending updates on start
            )
            
            # Keep the bot running indefinitely
            logger.info("Bot is now running. Press Ctrl+C to stop.")
            self.updater.idle()
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            # Clean shutdown
            try:
                self.scheduler.stop()
                self.updater.stop()
                logger.info("Bot stopped gracefully")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
