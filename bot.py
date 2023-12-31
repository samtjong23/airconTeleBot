import boto3
import datetime
import json
import logging
import os
import pytz
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_REGION_NAME = os.getenv("AWS_REGION_NAME")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
FORM_URL = os.getenv("FORM_URL")
FORM_FIELD_IDS = json.loads(os.getenv("FORM_FIELD_IDS"))
HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME")
PORT = int(os.environ.get("PORT", 5000))
TOKEN = os.getenv("TOKEN")
USER_NAME_MAPPING = json.loads(os.getenv("USER_NAME_MAPPING"))

# AWS setup
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION_NAME
)
dynamodb = session.resource("dynamodb")
table = dynamodb.Table("airconTeleBot")

# Set the Singapore time zone
sgt = pytz.timezone("Asia/Singapore")

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to RedhillAirconBot!\n\nIf you're new, please contact @samtjong to register before you can use this bot.\n\nOtherwise, type /help to see available commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("List of commands:\n\n/help - Show available commands\n/on - Start timer\n/off - End timer \n/abort - Cancel ongoing timer\n/hour <h> - Record usage in hours (e.g. '/hour 6.5')")

def is_item_exists(user_name):
    response = table.get_item(
        Key={
            "User": user_name
        }
    )
    return "Item" in response

def submit_google_form(user_name, start_time: datetime.datetime, end_time: datetime.datetime):
    start_date_str, start_time_str = str(start_time).split(" ")
    start_hour, start_minute = start_time_str.split(":")[:2]
    start_year, start_month, start_day = start_date_str.split("-")
    end_date_str, end_time_str = str(end_time).split(" ")
    end_hour, end_minute = end_time_str.split(":")[:2]
    end_year, end_month, end_day = end_date_str.split("-")

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

    response = requests.post(FORM_URL, data=form_data)
    return response.status_code == 200

async def on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    if user_name not in USER_NAME_MAPPING:
        await update.message.reply_text("You are not registered yet. Contact @samtjong to register before you can use this bot.")
    elif is_item_exists(user_name):
        await update.message.reply_text("You already have an active session.")
    else:
        table.put_item(
            Item={
                "User": user_name,
                "startTime": str(datetime.datetime.now(sgt))
            }
        )
        await update.message.reply_text("Timer started. Use /off to stop the timer or /abort to cancel the timer.")

async def off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    if is_item_exists(user_name):
        user_item_dict = {
            "User": user_name
        }
        
        response = table.get_item(Key=user_item_dict)
        start_time_string = response["Item"]["startTime"]
        start_time = datetime.datetime.strptime(start_time_string, "%Y-%m-%d %H:%M:%S.%f%z")
        
        table.delete_item(Key=user_item_dict)
        end_time = datetime.datetime.now(sgt)
        
        if submit_google_form(user_name, start_time, end_time):
            await update.message.reply_text(f"Form submitted successfully! You used the AC from {start_time.strftime('%d/%m/%Y, %H:%M')} to {end_time.strftime('%d/%m/%Y, %H:%M')}.")
        else:
            await update.message.reply_text("Failed to submit the form. Please try again.")
    else:
        await update.message.reply_text("You don't have an active session. Use /on to start a new timer.")

async def abort_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    if is_item_exists(user_name):
        table.delete_item(
            Key={
                "User": user_name
            }
        )
        await update.message.reply_text("Your session has been cancelled. Use /on to start a new timer.")
    else:
        await update.message.reply_text("You don't have an active session. Use /on to start a new timer.")

async def hour_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    if user_name not in USER_NAME_MAPPING:
        await update.message.reply_text("You are not registered yet. Contact @samtjong to register before you can use this bot.")
    elif len(context.args) != 1 or not context.args[0].replace('.','',1).isdigit():
        # Check if too many arguments or argument is not a number (int or float)
        await update.message.reply_text("I'm sorry, I can't tell how long you've used the AC.\n\nPlease input only one number after /hour (e.g. '/hour 8' or '/hour 6.5').")
    else:
        current_time = datetime.datetime.now(sgt)
        hours = context.args[0]
        hours_delta = datetime.timedelta(hours=float(hours))
        if submit_google_form(user_name, current_time-hours_delta, current_time):
            await update.message.reply_text(f"Form submitted successfully! You used the AC for {hours} hours.")
        else:
            await update.message.reply_text("Failed to submit the form. Please try again.")


# Message Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I'm sorry, I don't understand that command. Type /help to see available commands.")

# Error Handler
async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f"Update '{update}' caused error '{context.error}'")

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

    # On error: Log warning message
    application.add_error_handler(handle_error)

    # Run the bot until the user presses Ctrl-C
    application.run_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url="https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
    # For dev
    # application.run_polling(allowed_updates=Update.ALL_TYPES) 


if __name__ == "__main__":
    main()
