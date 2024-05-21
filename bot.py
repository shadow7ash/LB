from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, filters
import pymongo
import os

# MongoDB setup
MONGODB_URL = os.getenv("MONGODB_URL")
client = pymongo.MongoClient(MONGODB_URL)
db = client["your_database_name"]  # Replace "your_database_name" with your actual database name

# Force subscribe message
FORCE_SUB_MESSAGE = "Please join our channel to access the bot's features."
CHANNEL_INVITE_LINK = "https://t.me/your_channel_invite_link"  # Replace with your channel invite link
FORCE_SUB_CHANNEL_ID = "your_force_sub_channel_id"  # Replace with your force sub channel ID

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if user is in a group chat
    if update.effective_chat.type == "private":
        update.message.reply_text("Please use the bot only through the group.")
        return

    # Check if user is a member of the force subscription channel
    if user_in_channel(context, user_id):
        # User is in the channel, send welcome message
        keyboard = [[InlineKeyboardButton("Join Force Sub Channel", url=CHANNEL_INVITE_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Welcome to the bot! If you want to use me, please send commands in the force subscription channel.", reply_markup=reply_markup)
    else:
        # User is not in the channel, send force subscribe message with button to join force sub channel
        force_sub_channel_invite_link = context.bot.export_chat_invite_link(FORCE_SUB_CHANNEL_ID)
        keyboard = [[InlineKeyboardButton("Join Force Sub Channel", url=force_sub_channel_invite_link)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(FORCE_SUB_MESSAGE, reply_markup=reply_markup)

def user_in_channel(context, user_id):
    # Check if the user is a member of the force subscription channel
    try:
        # Get channel information
        chat_member = context.bot.get_chat_member(FORCE_SUB_CHANNEL_ID, user_id)
        
        # If user is a member, return True
        return chat_member.status == "member"
    except Exception as e:
        print("Error checking channel membership:", e)
        return False

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
