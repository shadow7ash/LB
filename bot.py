from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters  # Corrected import statement
import pymongo
import os
import requests
from urllib.parse import urlparse

# MongoDB setup
MONGODB_URL = os.getenv("MONGODB_URL")
client = pymongo.MongoClient(MONGODB_URL)
db = client["your_database_name"]  # Replace "your_database_name" with your actual database name

# Force subscribe message
FORCE_SUB_MESSAGE = "Please join our channel to access the bot's features."
CHANNEL_INVITE_LINK = "https://t.me/your_channel_invite_link"  # Replace with your channel invite link

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    # Check if user is in a group chat
    if update.effective_chat.type == "private":
        update.message.reply_text("Please use the bot only through the group.")
        return
    
    # Check if user is a member of the force subscription channel
    if user_in_channel(user_id):
        update.message.reply_text("Welcome to the bot!")
    else:
        # User is not in the channel, send force subscribe message with button
        keyboard = [[InlineKeyboardButton("Join Channel", url=CHANNEL_INVITE_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(FORCE_SUB_MESSAGE, reply_markup=reply_markup)

def leech(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    # Check if user is in a group chat
    if update.effective_chat.type == "private":
        update.message.reply_text("Please use the bot only through the group.")
        return
    
    # Check if the message contains a valid link
    if len(context.args) == 0:
        update.message.reply_text("Please provide a valid downloadable link.")
        return
    
    download_link = context.args[0]
    
    # Download the file from the provided link
    file_path = download_file(download_link)
    if file_path:
        # Send the downloaded file to the user's personal chat
        update.message.reply_document(open(file_path, 'rb'))
        os.remove(file_path)  # Remove the downloaded file after sending
    else:
        update.message.reply_text("Failed to download the file.")
        

def user_in_channel(user_id):
    # Check if the user is a member of the force subscription channel
    try:
        # Get channel information
        channel_id = "your_channel_id"  # Replace with your channel ID
        chat_member = context.bot.get_chat_member(channel_id, user_id)
        
        # If user is a member, return True
        return chat_member.status == "member"
    except Exception as e:
        print("Error checking channel membership:", e)
        return False

def download_file(download_link):
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
            with open(file_path, 'wb') as file:
                file.write(response.content)
            return file_path
        else:
            return None
    except Exception as e:
        print("Error downloading file:", e)
        return None

def main() -> None:
    updater = Updater("your_bot_token")  # Replace "your_bot_token" with your actual bot token
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("leech", leech))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
