import os
import logging  # Import the logging module
import requests
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from pymongo import MongoClient
from bson.objectid import ObjectId

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.getenv('TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID'))
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# MongoDB client
client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]
users_collection = db['users']

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    update.message.reply_text("Welcome to the Leech Bot! Send me a direct download link to get started.")
    update_user_stats(user_id)

def leech(update: Update, context: CallbackContext) -> None:
    if len(context.args) == 0:
        update.message.reply_text("Please provide a direct download link.")
        return

    link = context.args[0]

    try:
        file_name = link.split('/')[-1]
        r = requests.get(link, stream=True)
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        update.message.reply_document(open(file_name, 'rb'), filename=file_name)
        os.remove(file_name)
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send me a direct download link and I'll download the file for you.")

def update_user_stats(user_id: int) -> None:
    user_stats_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"downloads": 1}},
        upsert=True
    )

def broadcast(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != OWNER_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    message = ' '.join(context.args)
    users = user_stats_collection.find()
    for user in users:
        try:
            context.bot.send_message(chat_id=user['user_id'], text=message)
        except Exception as e:
            print(f"Failed to send message to {user['user_id']}: {str(e)}")

def users(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != OWNER_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    total_users = user_stats_collection.count_documents({})
    update.message.reply_text(f"Total users: {total_users}")

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("leech", leech))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    dispatcher.add_handler(CommandHandler("users", users))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
