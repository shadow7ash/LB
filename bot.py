import os
import warnings
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient

# Suppress specific warning
warnings.filterwarnings('ignore', message='python-telegram-bot is using upstream urllib3')

# Get the bot token and owner ID from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))  # Owner's user ID
FORCE_SUBSCRIBE_MESSAGE = os.getenv("FORCE_SUBSCRIBE_MESSAGE", "Please subscribe to our channel to use this bot. Click here to subscribe: [Channel Name](https://t.me/your_channel)")
FORCE_SUBSCRIBE_CHANNEL_ID = int(os.getenv("FORCE_SUBSCRIBE_CHANNEL_ID"))  # Channel ID for force subscribe message

# Connect to MongoDB
MONGODB_URL = os.getenv("MONGODB_URL")
client = MongoClient(MONGODB_URL)
db_name = MONGODB_URL.split('/')[-1]
db = client[db_name]

# Initialize the bot
updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Force subscribe handler
def force_subscribe(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE, parse_mode="Markdown")

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    db.users.update_one({"user_id": user_id}, {"$set": {"blocked": False}}, upsert=True)
    update.message.reply_text("Welcome to the Leech Bot! Send me a direct download link or reply to a message containing a link with /leech command.")

# Leech command handler
def leech(update: Update, context: CallbackContext) -> None:
    message = update.message
    file_url = message.text.split(" ")[1] if len(message.text.split(" ")) > 1 else None

    if not file_url and message.reply_to_message:
        file_url = message.reply_to_message.text

    if file_url and (file_url.startswith("http://") or file_url.startswith("https://")):
        response = requests.get(file_url)
        if response.status_code == 200:
            update.message.reply_document(document=response.content, filename="downloaded_file")
        else:
            update.message.reply_text("Failed to fetch file.")
    else:
        update.message.reply_text("Please provide a direct download link.")

# Broadcast command handler
def broadcast(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == OWNER_ID:
        message = update.message.text.replace("/broadcast ", "")
        users = db.users.find()

        for user in users:
            try:
                context.bot.send_message(chat_id=user["user_id"], text=message)
            except Exception:
                db.users.update_one({"user_id": user["user_id"]}, {"$set": {"blocked": True}})
    else:
        update.message.reply_text("You are not authorized to use this command.")

# Users command handler
def users(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == OWNER_ID:
        total_users_count = db.users.count_documents({})
        blocked_users_count = db.users.count_documents({"blocked": True})
        update.message.reply_text(f"Total users: {total_users_count}\nBlocked users: {blocked_users_count}")
    else:
        update.message.reply_text("You are not authorized to use this command.")

# Add handlers for commands and messages
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("leech", leech))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, leech))
dispatcher.add_handler(CommandHandler("broadcast", broadcast))
dispatcher.add_handler(CommandHandler("users", users))

# Start the bot
updater.start_polling()
updater.idle()
