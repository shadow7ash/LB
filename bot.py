import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("FORCE_SUBSCRIBE_CHANNEL_ID")

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
    
    if chat_member.status in ['member', 'administrator', 'creator']:
        await update.message.reply_text(
            "Welcome! You are already a member of the channel. Send commands in the force sub channel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Force Sub Channel", url=f"https://t.me/{CHANNEL_ID[1:]}")]
            ])
        )
    else:
        invite_link = await generate_channel_invite_link(context)
        await update.message.reply_text(
            "You must join the channel to use the bot. Please click the button below to join.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url=invite_link)]
            ])
        )

async def generate_channel_invite_link(context: CallbackContext) -> str:
    invite_link = await context.bot.create_chat_invite_link(chat_id=CHANNEL_ID)
    return invite_link.invite_link

async def leech(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Leech command executed!")

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("leech", leech))

    application.run_polling()

if __name__ == "__main__":
    main()
