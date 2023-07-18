import datetime
import json
import logging
import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("TOKEN")
FORM_URL = os.getenv("FORM_URL")
FORM_FIELD_IDS = json.loads(os.getenv("FORM_FIELD_IDS"))
USER_NAME_MAPPING = json.loads(os.getenv("USER_NAME_MAPPING"))

user_sessions = {}

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to RedhillAirconBot! Send /help to see available commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("List of commands:\n/help - Show available commands\n/on - Start timer\n/off - End timer")

async def submit_google_form(user_name, start_time, end_time):
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

    response = await requests.post(FORM_URL, data=form_data)

    return response.status_code == 200

async def on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        await update.message.reply_text("You already have an active session.")
    else:
        user_sessions[user_id] = datetime.datetime.now()
        await update.message.reply_text("Timer started. Use /off to stop the timer.")

async def off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        start_time = user_sessions[user_id]
        del user_sessions[user_id]
        end_time = datetime.datetime.now()
        user_name = USER_NAME_MAPPING.get(user_id, "Unknown")

        is_google_form_submitted = await submit_google_form(user_name, start_time, end_time)
        if user_name != "Unknown" and is_google_form_submitted:
          await update.message.reply_text('Form submitted successfully!')
        else:
          await update.message.reply_text('Failed to submit the form. Please try again.')
    else:
        await update.message.reply_text("You don't have an active session. Use /on to start the timer.")

# Message Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I'm sorry, I don't understand that command. Send /help to see available commands.")

# Start the Bot
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # On command: Answer
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("on", on_command))
    application.add_handler(CommandHandler("off", off_command))

    # On non command: Return error messsage
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
