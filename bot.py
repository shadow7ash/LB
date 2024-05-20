import os
import logging
import requests
from telegram import Update, Bot, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from pymongo import MongoClient
from bson.objectid import ObjectId

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
FORCE_SUBSCRIBE_CHANNEL_ID = int(os.getenv("FORCE_SUBSCRIBE_CHANNEL_ID"))
FORCE_SUBSCRIBE_MESSAGE = os.getenv("FORCE_SUBSCRIBE_MESSAGE")
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# MongoDB client
client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]
users_collection = db['users']

# Define command handlers
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id
    chat_id = update.message.chat_id

    # Check if user is subscribed
    try:
        chat_member = context.bot.get_chat_member(FORCE_SUBSCRIBE_CHANNEL_ID, user_id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE)
            return
    except Exception as e:
        update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE)
        return

    # Add user to database
    users_collection.update_one({'_id': user_id}, {'$set': {'chat_id': chat_id}}, upsert=True)
    update.message.reply_text('Welcome! Send me a direct download link to leech.')

def leech(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id

    # Check if user is subscribed
    try:
        chat_member = context.bot.get_chat_member(FORCE_SUBSCRIBE_CHANNEL_ID, user_id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE)
            return
    except Exception as e:
        update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE)
        return

    message = update.message.text
    if message.startswith('http://') or message.startswith('https://'):
        update.message.reply_text('Please wait, your file is downloading...')
        file_url = message
        file_name = file_url.split('/')[-1]

        try:
            response = requests.get(file_url)
            if response.status_code == 200:
                with open(file_name, 'wb') as file:
                    file.write(response.content)
                update.message.reply_document(document=open(file_name, 'rb'))
            else:
                update.message.reply_text('Failed to download the file.')
        except Exception as e:
            update.message.reply_text(f'Error: {str(e)}')

def broadcast(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        update.message.reply_text("You're not authorized to use this command.")
        return

    message = ' '.join(context.args)
    if not message:
        update.message.reply_text('Please provide a message to broadcast.')
        return

    for user in users_collection.find():
        try:
            context.bot.send_message(chat_id=user['chat_id'], text=message)
        except Exception as e:
            logger.warning(f"Could not send message to {user['chat_id']}: {str(e)}")

def users(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        update.message.reply_text("You're not authorized to use this command.")
        return

    total_users = users_collection.count_documents({})
    update.message.reply_text(f'Total users: {total_users}')

def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_BOT_TOKEN)

    dispatcher = updater.dispatcher

    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("leech", leech))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast, filters.User(OWNER_ID)))
    dispatcher.add_handler(CommandHandler("users", users, filters.User(OWNER_ID)))
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, leech))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
