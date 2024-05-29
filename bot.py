import os
import logging
import re
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from pymongo import MongoClient

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    await update.message.reply_text("Welcome to the Leech Bot! Send me a direct download link to get started.")
    update_user_stats(user_id)

def find_first_link(text: str) -> str:
    url_regex = re.compile(r'(https?://[^\s]+)')
    match = url_regex.search(text)
    return match.group(0) if match else None

async def leech(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message:
        replied_message = update.message.reply_to_message.text
        link = find_first_link(replied_message)
        if not link:
            await update.message.reply_text("The replied message does not contain a link.")
            return
    else:
        if not context.args:
            await update.message.reply_text("Please provide a direct download link.")
            return
        link = context.args[0]

    try:
        file_name = link.split('/')[-1]
        message = await update.message.reply_text(f"Your file is downloading, please wait...")

        aria2c_command = [
            'aria2c', link,
            '--max-connection-per-server=16',
            '--split=16',
            '--out', file_name
        ]
        process = await asyncio.create_subprocess_exec(*aria2c_command)
        await process.communicate()

        await update.message.reply_document(open(file_name, 'rb'), filename=file_name)
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=message.message_id)
        os.remove(file_name)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Send me a direct download link and I'll download the file for you.")

def update_user_stats(user_id: int) -> None:
    user_stats_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"downloads": 1}},
        upsert=True
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message, file_id, file_type = None, None, None
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
            await update.message.reply_text("Unsupported message type.")
            return
    else:
        message = ' '.join(context.args)

    if not message and not file_id:
        await update.message.reply_text("Please provide a message to broadcast.")
        return

    total_users = user_stats_collection.count_documents({})
    success_count, failure_count = 0, 0

    users = user_stats_collection.find()
    for user in users:
        try:
            if message:
                await context.bot.send_message(chat_id=user['user_id'], text=message)
            else:
                if file_type == 'photo':
                    await context.bot.send_photo(chat_id=user['user_id'], photo=file_id)
                elif file_type == 'video':
                    await context.bot.send_video(chat_id=user['user_id'], video=file_id)
                elif file_type == 'document':
                    await context.bot.send_document(chat_id=user['user_id'], document=file_id)
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

    await update.message.reply_text(reply_message)

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
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

    await update.message.reply_text(reply_message)

async def main() -> None:
    try:
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("leech", leech))
        application.add_handler(CommandHandler("broadcast", broadcast))
        application.add_handler(CommandHandler("users", users))

        await application.initialize()
        await application.bot.delete_webhook(drop_pending_updates=True)
        await application.start()
        await application.run_polling()
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        if application:
            await application.stop()

if __name__ == '__main__':
    asyncio.run(main())
