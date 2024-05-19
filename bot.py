import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient

# Get the bot token and owner ID from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))  # Owner's user ID
FORCE_SUBSCRIBE_MESSAGE = os.getenv("FORCE_SUBSCRIBE_MESSAGE", "Please subscribe to our channel to use this bot. Click here to subscribe: [Channel Name](https://t.me/your_channel)")
FORCE_SUBSCRIBE_CHANNEL_ID = int(os.getenv("FORCE_SUBSCRIBE_CHANNEL_ID"))  # Channel ID for force subscribe message

# Connect to MongoDB
MONGODB_URL = os.getenv("MONGODB_URL")
client = MongoClient(MONGODB_URL)
db = client.get_database()

# Initialize the bot
updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Variables to track user statistics
total_users = 0
blocked_users = 0

# Force subscribe handler
def force_subscribe(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE, parse_mode="Markdown")

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    global total_users
    total_users += 1
    update.message.reply_text("Welcome to the Leech Bot! Send me a direct download link or reply to a message containing a link with /leech command.")

# Leech command handler
def leech(update: Update, context: CallbackContext) -> None:
    # Get the message text
    message_text = update.message.text
    
    # Check if the message is a direct download link (http or https)
    if message_text.startswith("http://") or message_text.startswith("https://"):
        # Fetch the file from the link
        file_url = message_text
        response = requests.get(file_url)
        
        if response.status_code == 200:
            # Send the file to the user
            update.message.reply_document(document=response.content, filename="downloaded_file")
        else:
            update.message.reply_text("Failed to fetch file.")
    else:
        update.message.reply_text("Please provide a direct download link.")

# Broadcast command handler
def broadcast(update: Update, context: CallbackContext) -> None:
    # Check if the user is the owner
    if update.message.from_user.id == OWNER_ID:
        # Get the broadcast message from the command
        message = update.message.text.replace("/broadcast ", "")
        
        # Get all users from the database
        users = db.users.find()
        
        # Send the broadcast message to each user
        for user in users:
            context.bot.send_message(chat_id=user["user_id"], text=message)
    else:
        update.message.reply_text("You are not authorized to use this command.")

# Users command handler
def users(update: Update, context: CallbackContext) -> None:
    # Check if the user is the owner
    if update.message.from_user.id == OWNER_ID:
        # Get the total number of users
        total_users_count = db.users.count_documents({})
        
        # Get the total number of blocked users
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
