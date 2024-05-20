import os
import logging
import requests
from telegram import Update, Bot, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, Application, ContextTypes
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

# Ensure DATABASE_NAME is provided
if not DATABASE_NAME:
    raise ValueError("No DATABASE_NAME provided. Set the DATABASE_NAME environment variable.")

# MongoDB client
client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]
users_collection = db['users']

# Define command handlers
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id
    chat_id = update.message.chat_id

    # Check if user is subscribed
    try:
        chat_member = await context.bot.get_chat_member(FORCE_SUBSCRIBE_CHANNEL_ID, user_id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            await update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE)
            return
    except Exception as e:
        await update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE)
        return

    # Add user to database
    users_collection.update_one({'_id': user_id}, {'$set': {'chat_id': chat_id}}, upsert=True)
    await update.message.reply_text('Welcome! Send me a direct download link to leech.')

async def leech(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id

    # Check if user is subscribed
    try:
        chat_member = await context.bot.get_chat_member(FORCE_SUBSCRIBE_CHANNEL_ID, user_id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            await update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE)
            return
    except Exception as e:
        await update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE)
        return

    message = update.message.text
    if message.startswith('http://') or message.startswith('https://'):
        await update.message.reply_text('Please wait, your file is downloading...')
        file_url = message
        file_name = file_url.split('/')[-1]

        try:
            response = requests.get(file_url)
            if response.status_code == 200:
                with open(file_name, 'wb') as file:
                    file.write(response.content)
                await context.bot.send_document(chat_id=user_id, document=open(file_name, 'rb'))
            else:
                await update.message.reply_text('Failed to download the file.')
        except Exception as e:
            await update.message.reply_text(f'Error: {str(e)}')

async def broadcast(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You're not authorized to use this command.")
        return

    message = ' '.join(context.args)
    if not message:
        await update.message.reply_text('Please provide a message to broadcast.')
        return

    for user in users_collection.find():
        try:
            await context.bot.send_message(chat_id=user['chat_id'], text=message)
        except Exception as e:
            logger.warning(f"Could not send message to {user['chat_id']}: {str(e)}")

async def users(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You're not authorized to use this command.")
        return

    total_users = users_collection.count_documents({})
    await update.message.reply_text(f'Total users: {total_users}')

def main() -> None:
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("leech", leech))
    application.add_handler(CommandHandler("broadcast", broadcast, filters.User(OWNER_ID)))
    application.add_handler(CommandHandler("users", users, filters.User(OWNER_ID)))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, leech))

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    application.run_polling()

if __name__ == '__main__':
    main()
