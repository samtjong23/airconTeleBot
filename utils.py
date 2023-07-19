import aiohttp
from data import FORM_FIELD_IDS, FORM_URL
from telegram import Update
from telegram.ext import ContextTypes

# Util functions

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I'm sorry, I don't understand that command. Type /help to see available commands.")
    
async def submit_google_form(user_name, start_time, end_time):
    start_date_str, start_time_str = str(start_time).split(" ")
    start_hour, start_minute =start_time_str.split(":")[:2]
    start_year, start_month, start_day =start_date_str.split("-")
    end_date_str, end_time_str = str(end_time).split(" ")
    end_hour, end_minute =end_time_str.split(":")[:2]
    end_year, end_month, end_day =end_date_str.split("-")

    form_data = {
        FORM_FIELD_IDS["name"]: user_name,
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

