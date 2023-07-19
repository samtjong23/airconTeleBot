import aiohttp
import asyncio
import datetime
import json
import logging
import os
import pytz
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("TOKEN")
FORM_URL = os.getenv("FORM_URL")
FORM_FIELD_IDS = json.loads(os.getenv("FORM_FIELD_IDS"))
USER_NAME_MAPPING = json.loads(os.getenv("USER_NAME_MAPPING"))

user_sessions = {}

# Set the Singapore time zone
sgt = pytz.timezone("Asia/Singapore")

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to RedhillAirconBot!\n\nIf you're new, please contact @samtjong to register before you can use this bot.\n\nOtherwise, type /help to see available commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("List of commands:\n\n/help - Show available commands\n/on - Start timer\n/off - End timer \n/abort - Cancel ongoing timer\n/hour <h> - Record usage in hours (e.g. '/hour 6.5')")

async def submit_google_form(user_name, start_time: datetime.datetime, end_time: datetime.datetime):
    start_date_str, start_time_str = str(start_time).split(" ")
    start_hour, start_minute =start_time_str.split(":")[:2]
    start_year, start_month, start_day =start_date_str.split("-")
    end_date_str, end_time_str = str(end_time).split(" ")
    end_hour, end_minute =end_time_str.split(":")[:2]
    end_year, end_month, end_day =end_date_str.split("-")

    form_data = {
        FORM_FIELD_IDS["name"]: USER_NAME_MAPPING[user_name],
        FORM_FIELD_IDS["usage_duration"]: (end_time - start_time)/datetime.timedelta(hours=1),
        FORM_FIELD_IDS["start_time_hour"]: start_hour,
        FORM_FIELD_IDS["start_time_minute"]: start_minute,
        FORM_FIELD_IDS["start_date_year"]: start_year,
        FORM_FIELD_IDS["start_date_month"]: start_month,
        FORM_FIELD_IDS["start_date_day"]: start_day,
        FORM_FIELD_IDS["end_time_hour"]: end_hour,
        FORM_FIELD_IDS["end_time_minute"]: end_minute,
        FORM_FIELD_IDS["end_date_year"]: end_year,
        FORM_FIELD_IDS["end_date_month"]: end_month,
        FORM_FIELD_IDS["end_date_day"]: end_day,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(FORM_URL, data=form_data) as response:
            return response.status == 200

async def on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    if user_name not in USER_NAME_MAPPING:
        await update.message.reply_text("You are not registered yet. Contact @samtjong to register before you can use this bot.")
    elif user_name in user_sessions:
        await update.message.reply_text("You already have an active session.")
    else:
        user_sessions[user_name] = datetime.datetime.now(sgt)
        await update.message.reply_text("Timer started. Use /off to stop the timer or /abort to cancel the timer.")

async def off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    if user_name in user_sessions:
        start_time = user_sessions[user_name]
        del user_sessions[user_name]
        end_time = datetime.datetime.now(sgt)

        if await submit_google_form(user_name, start_time, end_time):
            await update.message.reply_text(f"Form submitted successfully! You used the AC from {start_time.strftime('%d/%m/%Y, %H:%M')} to {end_time.strftime('%d/%m/%Y, %H:%M')}.")
        else:
            await update.message.reply_text("Failed to submit the form. Please try again.")
    else:
        await update.message.reply_text("You don't have an active session. Use /on to start a new timer.")

async def abort_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    if user_name in user_sessions:
        del user_sessions[user_name]
        await update.message.reply_text("Your session has been cancelled. Use /on to start a new timer.")
    else:
        await update.message.reply_text("You don't have an active session. Use /on to start a new timer.")

async def hour_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    if USER_NAME_MAPPING.get(user_name, "Unknown") == "Unknown":
        await update.message.reply_text("You are not registered yet. Contact @samtjong to register before you can use this bot.")
    elif len(context.args) != 1 or not context.args[0].replace('.','',1).isdigit():
        # Check if too many arguments or argument is not a number (int or float)
        await update.message.reply_text("I'm sorry, I can't tell how long you've used the AC.\n\nPlease input only one number after /hour (e.g. '/hour 8' or '/hour 6.5').")
    else:
        current_time = datetime.datetime.now(sgt)
        hours = context.args[0]
        hours_delta = datetime.timedelta(hours=float(hours))
        if await submit_google_form(user_name, current_time-hours_delta, current_time):
            await update.message.reply_text(f"Form submitted successfully! You used the AC for {hours} hours.") 
        else:
            await update.message.reply_text("Failed to submit the form. Please try again.")


# Message Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I'm sorry, I don't understand that command. Type /help to see available commands.")

# Start the Bot
def main():
    application = Application.builder().token(TOKEN).build()

    # On command: Answer
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("on", on_command))
    application.add_handler(CommandHandler("off", off_command))
    application.add_handler(CommandHandler("abort", abort_command))
    application.add_handler(CommandHandler("hour", hour_command))

    # On non command: Return error messsage
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    asyncio.run(application.run_polling(allowed_updates=Update.ALL_TYPES))


if __name__ == "__main__":
    main()
