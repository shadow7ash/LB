import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from pymongo import MongoClient

# MongoDB connection URI
MONGODB_URI = 'YOUR_MONGODB_URI'

# Telegram bot token
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# Owner's Telegram user ID
OWNER_ID = 'YOUR_OWNER_TELEGRAM_USER_ID'

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    update.message.reply_text("Welcome to the Leech Bot! Send me a direct download link to get started.")
    # Update user statistics in MongoDB
    update_user_stats(user_id)

def leech(update: Update, context: CallbackContext) -> None:
    # Check if a link is provided
    if len(context.args) == 0:
        update.message.reply_text("Please provide a direct download link.")
        return
    
    link = context.args[0]

    # Download the file
    try:
        # Get the filename from the URL
        file_name = link.split('/')[-1]
        r = requests.get(link, stream=True)
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        # Send the file to the user with the original filename
        update.message.reply_document(open(file_name, 'rb'), filename=file_name)
        # Remove the downloaded file
        os.remove(file_name)
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send me a direct download link and I'll download the file for you.")

def update_user_stats(user_id: int) -> None:
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client.get_database()
    user_stats_collection = db.user_stats

    # Update or insert user statistics
    user_stats_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"downloads": 1}},
        upsert=True
    )

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Define handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("leech", leech))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
