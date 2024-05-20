from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext
import pymongo
import os
import requests
from urllib.parse import urlparse
import asyncio

# MongoDB setup
MONGODB_URL = os.getenv("MONGODB_URL")
client = pymongo.MongoClient(MONGODB_URL)
db = client["your_database_name"]  # Replace "your_database_name" with your actual database name

# Force subscribe message
FORCE_SUB_MESSAGE = os.getenv("FORCE_SUBSCRIBE_MESSAGE", "Please join our channel to access the bot's features.")
CHANNEL_INVITE_LINK = "https://t.me/your_channel_invite_link"  # Replace with your channel invite link

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    # Check if user is in a group chat
    if update.effective_chat.type == "private":
        keyboard = [[InlineKeyboardButton("Join Channel", url=CHANNEL_INVITE_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Join this force sub channel then send commands to the bot from here.", reply_markup=reply_markup)
        return
    
    # Check if user is a member of the force subscription channel
    if await user_in_channel(user_id, context):
        await update.message.reply_text("Welcome to the bot!")
    else:
        # User is not in the channel, send force subscribe message with button
        keyboard = [[InlineKeyboardButton("Join Channel", url=CHANNEL_INVITE_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(FORCE_SUB_MESSAGE, reply_markup=reply_markup)

async def leech(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    # Check if user is in a group chat
    if update.effective_chat.type == "private":
        keyboard = [[InlineKeyboardButton("Join Channel", url=CHANNEL_INVITE_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Join this force sub channel then send commands to the bot from here.", reply_markup=reply_markup)
        return
    
    # Check if the message contains a valid link
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a valid downloadable link.")
        return
    
    download_link = context.args[0]
    
    # Download the file from the provided link
    file_path = await download_file(download_link)
    if file_path:
        # Send the downloaded file to the user's personal chat
        await context.bot.send_document(chat_id=user_id, document=open(file_path, 'rb'))
        os.remove(file_path)  # Remove the downloaded file after sending
    else:
        await update.message.reply_text("Failed to download the file.")

async def user_in_channel(user_id, context: CallbackContext):
    # Check if the user is a member of the force subscription channel
    try:
        # Get channel information
        channel_id = os.getenv("FORCE_SUBSCRIBE_CHANNEL_ID")  # Replace with your channel ID
        chat_member = await context.bot.get_chat_member(channel_id, user_id)
        
        # If user is a member, return True
        return chat_member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print("Error checking channel membership:", e)
        return False

async def download_file(download_link):
    try:
        response = requests.get(download_link)
        if response.status_code == 200:
            # Get the filename from the Content-Disposition header
            content_disposition = response.headers.get("Content-Disposition")
            if content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')
            else:
                # If Content-Disposition header is not present, extract filename from the URL
                filename = os.path.basename(urlparse(download_link).path)
            
            file_path = os.path.join("downloads", filename)  # Save the file in a "downloads" directory
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as file:
                file.write(response.content)
            return file_path
        else:
            return None
    except Exception as e:
        print("Error downloading file:", e)
        return None

async def broadcast(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != int(os.getenv("OWNER_ID")):
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
        if update.effective_user.id != int(os.getenv("OWNER_ID")):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    total_users = db.users.count_documents({})
    blocked_users = db.users.count_documents({"blocked": True})
    active_users = total_users - blocked_users
    
    await update.message.reply_text(f"Total users: {total_users}\nActive users: {active_users}\nBlocked users: {blocked_users}")

def error(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

async def start_application() -> None:
    updater = Updater(os.getenv("TELEGRAM_BOT_TOKEN"))
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("leech", leech))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    dispatcher.add_handler(CommandHandler("users", users))

    # Error handler
    dispatcher.add_error_handler(error)

    # Run the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    asyncio.run(start_application())
