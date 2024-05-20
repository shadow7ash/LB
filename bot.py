import os
import logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from pymongo import MongoClient
from telegram.error import TelegramError
import requests

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
FORCE_SUBSCRIBE_MESSAGE = os.getenv("FORCE_SUBSCRIBE_MESSAGE")
FORCE_SUBSCRIBE_CHANNEL_ID = os.getenv("FORCE_SUBSCRIBE_CHANNEL_ID")
MONGODB_URL = os.getenv("MONGODB_URL")

# Initialize bot and database client
bot = Bot(token=TELEGRAM_BOT_TOKEN)
client = MongoClient(MONGODB_URL)
db = client.get_database()
users_collection = db.get_collection("users")

# Check if user is a member of the channel
def is_user_subscribed(user_id):
    try:
        member_status = bot.get_chat_member(FORCE_SUBSCRIBE_CHANNEL_ID, user_id).status
        return member_status in ["member", "administrator", "creator"]
    except TelegramError as e:
        logger.error(f"Error checking subscription status: {e}")
        return False

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not is_user_subscribed(user.id):
        update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE)
        return

    # Save user to database
    if users_collection.find_one({"user_id": user.id}) is None:
        users_collection.insert_one({"user_id": user.id, "blocked": False, "deleted": False})

    update.message.reply_text('Hello! Send me a link to leech.')

def leech(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not is_user_subscribed(user.id):
        update.message.reply_text(FORCE_SUBSCRIBE_MESSAGE)
        return

    message = update.message
    link = message.text.strip()

    if link.startswith(("http://", "https://")):
        update.message.reply_text("Please wait, your file is downloading...")

        try:
            # Get file name from the URL
            file_name = link.split("/")[-1]
            response = requests.get(link, stream=True)

            # Check if the URL is valid and can be accessed
            if response.status_code == 200:
                file_size = int(response.headers.get('content-length', 0)) / (1024 * 1024)  # Convert size to MB
                update.message.reply_text(f"File size: {file_size:.2f} MB")

                # Save the file
                with open(file_name, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)

                # Send the file to the user's personal chat
                bot.send_document(chat_id=user.id, document=open(file_name, 'rb'))
                update.message.reply_text("The file has been sent to your personal chat.")
            else:
                update.message.reply_text("Failed to download the file. Please check the link.")
        except Exception as e:
            logger.error(f"Error processing the link: {e}")
            update.message.reply_text("An error occurred while processing your request.")
    else:
        update.message.reply_text("Please send a valid download link.")

def broadcast(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        return

    message = ' '.join(context.args)
    if not message:
        update.message.reply_text("Please provide a message to broadcast.")
        return

    for user in users_collection.find({"blocked": False, "deleted": False}):
        try:
            bot.send_message(chat_id=user["user_id"], text=message)
        except TelegramError as e:
            logger.error(f"Error sending message to {user['user_id']}: {e}")

def users(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        return

    total_users = users_collection.count_documents({})
    blocked_users = users_collection.count_documents({"blocked": True})
    deleted_users = users_collection.count_documents({"deleted": True})

    update.message.reply_text(
        f"Total users: {total_users}\nBlocked users: {blocked_users}\nDeleted users: {deleted_users}"
    )

def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("leech", leech))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast, pass_args=True))
    dispatcher.add_handler(CommandHandler("users", users))
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, leech))

    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
