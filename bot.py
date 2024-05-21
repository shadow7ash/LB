import os
import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from pymongo import MongoClient
import re
import time

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
user_stats_collection = db['user_stats']

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    update.message.reply_text("Welcome to the Leech Bot! Send me a direct download link to get started.")
    update_user_stats(user_id)

def find_first_link(text: str) -> str:
    url_regex = re.compile(
        r'(https?://[^\s]+)')
    match = url_regex.search(text)
    if match:
        return match.group(0)
    return None

def leech(update: Update, context: CallbackContext) -> None:
    if update.message.reply_to_message:
        # Check if the replied message contains a link
        replied_message = update.message.reply_to_message.text
        link = find_first_link(replied_message)
        if not link:
            update.message.reply_text("The replied message does not contain a link.")
            return
    else:
        if len(context.args) == 0:
            update.message.reply_text("Please provide a direct download link.")
            return
        link = context.args[0]

    try:
        file_name = link.split('/')[-1]
        r = requests.get(link, stream=True)
        
        # Get the file size
        file_size = int(r.headers.get('Content-Length', 0))
        file_size_mb = file_size / (1024 * 1024)

        # Notify the user that the file is downloading
        message = update.message.reply_text(f"Your file is downloading, please wait...\nFile size: {file_size_mb:.2f} MB")

        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    # Update the message periodically
                    try:
                        context.bot.edit_message_text(
                            text=f"Your file is downloading, please wait...\nFile size: {file_size_mb:.2f} MB",
                            chat_id=update.message.chat_id,
                            message_id=message.message_id
                        )
                    except Exception as e:
                        logger.error(f"Error updating message: {str(e)}")

        context.bot.delete_message(chat_id=update.message.chat_id, message_id=message.message_id)
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

    message = None
    file_id = None
    file_type = None
    if update.message.reply_to_message:
        if update.message.reply_to_message.text:
            message = update.message.reply_to_message.text
        elif update.message.reply_to_message.photo:
            file_id = update.message.reply_to_message.photo[-1].file_id
            file_type = 'photo'
        elif update.message.reply_to_message.video:
            file_id = update.message.reply_to_message.video.file_id
            file_type = 'video'
        elif update.message.reply_to_message.document:
            file_id = update.message.reply_to_message.document.file_id
            file_type = 'document'
        else:
            update.message.reply_text("Unsupported message type.")
            return
    else:
        message = ' '.join(context.args)
    
    if not message and not file_id:
        update.message.reply_text("Please provide a message to broadcast.")
        return

    total_users = user_stats_collection.count_documents({})
    success_count = 0
    failure_count = 0

    users = user_stats_collection.find()
    for user in users:
        try:
            if message:
                context.bot.send_message(chat_id=user['user_id'], text=message)
            else:
                if file_type == 'photo':
                    context.bot.send_photo(chat_id=user['user_id'], photo=file_id)
                elif file_type == 'video':
                    context.bot.send_video(chat_id=user['user_id'], video=file_id)
                elif file_type == 'document':
                    context.bot.send_document(chat_id=user['user_id'], document=file_id)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send message to {user['user_id']}: {str(e)}")
            failure_count += 1

    active_users = total_users - failure_count
    blocked_users = user_stats_collection.count_documents({"is_blocked": True})
    deleted_users = user_stats_collection.count_documents({"is_deleted": True})

    reply_message = (
        f"Total users: {total_users}\n"
        f"Successfully broadcasted to: {success_count} users\n"
        f"Failed to broadcast to: {failure_count} users\n"
        f"Active users: {active_users}\n"
        f"Blocked users: {blocked_users}\n"
        f"Deleted users: {deleted_users}"
    )

    update.message.reply_text(reply_message)

def users(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != OWNER_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    total_users = user_stats_collection.count_documents({})
    blocked_users = user_stats_collection.count_documents({"is_blocked": True})
    deleted_users = user_stats_collection.count_documents({"is_deleted": True})
    active_users = total_users - blocked_users - deleted_users

    reply_message = (
        f"Total users: {total_users}\n"
        f"Active users: {active_users}\n"
        f"Blocked users: {blocked_users}\n"
        f"Deleted users: {deleted_users}"
    )

    update.message.reply_text(reply_message)

def main() -> None:
    try:
        updater = Updater(token=TOKEN)
        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("leech", leech))
        dispatcher.add_handler(CommandHandler("broadcast", broadcast))
        dispatcher.add_handler(CommandHandler("users", users))

        updater.start_polling()
        updater.idle()
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")

if __name__ == '__main__':
    main()
