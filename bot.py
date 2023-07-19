import asyncio
import logging
from commands import abort_command, help_command, on_command, off_command, start_command
from data import TOKEN
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from utils import handle_message

# Logging: set higher logging level for httpx 
# to avoid all GET and POST requests being logged
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Start the Bot
def main():
    application = Application.builder().token(TOKEN).build()

    # On command: Answer
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("on", on_command))
    application.add_handler(CommandHandler("off", off_command))
    application.add_handler(CommandHandler("abort", abort_command))

    # On non command: Return error messsage
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    asyncio.run(application.run_polling(allowed_updates=Update.ALL_TYPES))

if __name__ == "__main__":
    main()
