import datetime
import json
import logging
import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Updater, filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("TOKEN")
FORM_URL = os.getenv("FORM_URL")
FORM_FIELD_IDS = json.loads(os.getenv("FORM_FIELD_IDS"))
USER_NAME_MAPPING = json.loads(os.getenv("USER_NAME_MAPPING"))

# Initialize the Telegram bot
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

user_sessions = {}

# Command Handlers
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to RedhillAirconBot! Send /help to see available commands.")

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("List of commands:\n/help - Show available commands\n/on - Start timer\n/off - End timer")

def submit_google_form(user_name, start_time, end_time):
    start_date_str = start_time.strftime("%Y-%m-%d")
    start_time_str = start_time.strftime("%H:%M:%S")
    end_date_str = end_time.strftime("%Y-%m-%d")
    end_time_str = end_time.strftime("%H:%M:%S")

    form_data = {
        FORM_FIELD_IDS["name"]: user_name,
        FORM_FIELD_IDS["start_date"]: start_date_str,
        FORM_FIELD_IDS["start_time"]: start_time_str,
        FORM_FIELD_IDS["end_date"]: end_date_str,
        FORM_FIELD_IDS["end_time"]: end_time_str
    }

    response = requests.post(FORM_URL, data=form_data)

    return response.status_code == 200

def on_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in user_sessions:
        update.message.reply_text("You already have an active session.")
    else:
        user_sessions[user_id] = datetime.datetime.now()
        update.message.reply_text("Timer started. Use /off to stop the timer.")

def off_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in user_sessions:
        start_time = user_sessions[user_id]
        del user_sessions[user_id]
        end_time = datetime.datetime.now()
        user_name = USER_NAME_MAPPING.get(user_id, "Unknown")

        if user_name != "Unknown" and submit_google_form(user_name, start_time, end_time):
          update.message.reply_text('Form submitted successfully!')
        else:
          update.message.reply_text('Failed to submit the form. Please try again.')
    else:
        update.message.reply_text("You don't have an active session. Use /on to start the timer.")

# Message Handler
def handle_message(update: Update, context: CallbackContext):
    update.message.reply_text("I'm sorry, I don't understand that command. Send /help to see available commands.")

# Command Handlers registration
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("on", on_command))
dispatcher.add_handler(CommandHandler("off", off_command))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Start the Bot
def main() -> None:
    try:
        updater.start_polling()
        logger.info("Bot started polling...")
        updater.idle()
    except KeyboardInterrupt:
        logger.warning("Bot stopped by user.")
    finally:
        updater.stop()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    main()
