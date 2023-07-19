import datetime
import pytz
from data import USER_NAME_MAPPING, user_sessions
from telegram import Update
from telegram.ext import ContextTypes
from utils import submit_google_form

sgt = pytz.timezone("Asia/Singapore")

# Command functions

async def abort_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    if user_name in user_sessions:
        del user_sessions[user_name]
        await update.message.reply_text("Your session has been cancelled. Use /on to start a new timer.")
    else:
        await update.message.reply_text("You don't have an active session. Use /on to start a new timer.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("List of commands:\n\n/help - Show available commands\n/on - Start timer\n/off - End timer \n/abort - Cancel ongoing timer")

async def off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    if user_name in user_sessions:
        start_time = user_sessions[user_name]
        del user_sessions[user_name]
        end_time = datetime.datetime.now(sgt)

        if await submit_google_form(user_name, start_time, end_time):
            await update.message.reply_text("Form submitted successfully!")
        else:
            await update.message.reply_text("Failed to submit the form. Please try again.")
    else:
        await update.message.reply_text("You don't have an active session. Use /on to start a new timer.")

async def on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    if USER_NAME_MAPPING.get(user_name, "Unknown") == "Unknown":
        await update.message.reply_text("You are not registered yet. Contact @samtjong to register before you can use this bot.")
    elif user_name in user_sessions:
        await update.message.reply_text("You already have an active session.")
    else:
        user_sessions[user_name] = datetime.datetime.now(sgt)
        await update.message.reply_text("Timer started. Use /off to stop the timer or /abort to cancel the timer.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to RedhillAirconBot!\n\nIf you're new, please contact @samtjong to register before you can use this bot.\n\nOtherwise, type /help to see available commands.")


