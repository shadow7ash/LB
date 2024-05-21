from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext
import pymongo
import os
import requests
from urllib.parse import urlparse
import asyncio
import logging

# Environment Variable Configuration (Replace placeholders)
MONGODB_URL = os.getenv("MONGODB_URL")
FORCE_SUBSCRIBE_MESSAGE = os.getenv("FORCE_SUBSCRIBE_MESSAGE", "Please join our channel to access the bot's features.")
CHANNEL_INVITE_LINK = os.getenv("CHANNEL_INVITE_LINK", "https://t.me/your_channel_invite_link")
FORCE_SUBSCRIBE_CHANNEL_ID = os.getenv("FORCE_SUBSCRIBE_CHANNEL_ID")
OWNER_ID = int(os.getenv("OWNER_ID"))  # Ensure OWNER_ID is an integer

# MongoDB Setup
client = pymongo.MongoClient(MONGODB_URL)
db = client["your_database_name"]  # Replace "your_database_name" with your actual database name

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Commands

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Force Subscribe Check
    if update.effective_chat.type == "private":
        keyboard = [[InlineKeyboardButton("Join Channel", url=CHANNEL_INVITE_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE, reply_markup=reply_markup)
        return

    if await user_in_channel(user_id, context):
        await update.message.reply_text("Welcome to the bot!")
    else:
        keyboard = [[InlineKeyboardButton("Join Channel", url=CHANNEL_INVITE_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE, reply_markup=reply_markup)

async def leech(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Force Subscribe Check
    if update.effective_chat.type == "private":
        keyboard = [[InlineKeyboardButton("Join Channel", url=CHANNEL_INVITE_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE, reply_markup=reply_markup)
        return

    # Check for Valid Link
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a valid downloadable link.")
        return

    download_link = context.args[0]

    # Download and Send File
    file_path = await download_file(download_link)
    if file_path:
        try:
            await context.bot.send_document(chat_id=user_id, document=open(file_path, 'rb'))
            os.remove(file_path)  # Remove downloaded file after sending
        except Exception as e:
            await update.message.reply_text(f"Error sending file: {e}")
            logger.error(f"Error sending file to {user_id}: {e}")
    else:
        await update.message.reply_text("Failed to download the file.")

async def user_in_channel(user_id, context: CallbackContext):
    # Check Force Subscribe Channel Membership
    try:
        chat_member = await context.bot.get_chat_member(FORCE_SUBSCRIBE_CHANNEL_ID, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error checking channel membership for {user_id}: {e}")
        return False

async def download_file(download_link):
    try:
        response = requests.get(download_link)
        if response.status_code == 200:
            # Extract Filename
            content_disposition = response.headers.get("Content-Disposition")
            if content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')
            else:
                # If no Content-Disposition header, extract from URL
                filename = os.path.basename(urlparse(download_link).path)
            # Create directory and save file
            file_path = os.path.join("downloads", filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as file:
                file.write(response.content)
            return file_path
        else:
            logger.error(f"Failed to download file: {download_link} (status code: {response.status_code})")
            return None
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return None

# Optional: Additional Commands (Uncomment and customize)

async def broadcast(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message = " ".join(context.args)
    users = db.users.find({"blocked": False})
    for user in users:
        try:
            await context.bot.send_message(chat_id=user["user_id"], text=message)
        except Exception as e:
            print(f"Failed to send message to {user['user_id']}: {e}")

async def users(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    total_users = db.users.count_documents({})
    blocked_users = db.users.count_documents({"blocked": True})
    active_users = total_users - blocked_users

    await update.message.reply_text(f"Total users: {total_users}\nActive users: {active_users}\nBlocked users: {blocked_users}")

# Error Handler

def error(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

# Main Function

async def start_application() -> None:
    # Fix 1: Provide both arguments to Updater
    updater = Updater(os.getenv("TELEGRAM_BOT_TOKEN"), use_context=True)
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("leech", leech))
    # Uncomment these lines to add broadcast and user commands
    # dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    # dispatcher.add_handler(CommandHandler("users", users))

    # Error handler
    dispatcher.add_error_handler(error)

    # Start the webhook
    await updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT")),
        url_path=os.getenv("TELEGRAM_BOT_TOKEN"),
        webhook_url=os.getenv("WEBHOOK_URL") + os.getenv("TELEGRAM_BOT_TOKEN")
    )

    # Fix 2: Await the start_coroutine
    await updater.idle()

if __name__ == "__main__":
    asyncio.run(start_application())
