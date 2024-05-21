from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import pymongo
import os

# MongoDB setup
MONGODB_URL = os.getenv("MONGODB_URL")
client = pymongo.MongoClient(MONGODB_URL)
db = client[os.getenv("DATABASE_NAME")]

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
        update.message.reply_text("Welcome to the bot! Send commands in the channel to use the bot.")
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
    
    # Your leech logic here
    # After downloading the file, send it to the user's personal chat

def user_in_channel(user_id):
    # Check if the user is a member of the force subscription channel
    try:
        # Get channel information
        channel_id = os.getenv("FORCE_SUBSCRIBE_CHANNEL_ID")  # Replace with your channel ID
        chat_member = context.bot.get_chat_member(channel_id, user_id)
        
        # If user is a member, return True
        return chat_member.status == "member"
    except Exception as e:
        print("Error checking channel membership:", e)
        return False

def generate_channel_invite_link(context):
    try:
        channel_id = os.getenv("FORCE_SUBSCRIBE_CHANNEL_ID")  # Replace with your channel ID
        invite_link = context.bot.export_chat_invite_link(channel_id)
        return invite_link
    except Exception as e:
        print("Error generating channel invite link:", e)
        return None

def main() -> None:
    updater = Updater(token=os.getenv("TELEGRAM_BOT_TOKEN"), use_context=True)
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("leech", leech))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
