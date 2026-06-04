import os
from datetime import datetime
import pytz

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN is missing in Render environment variables")

ADMIN_ID = 7488034821
KPAY_NUMBER = "09401878226"
KPAY_NAME = "Li Li Naing"
WAVE_NUMBER = "09401878226"
WAVE_NAME = "Li Li Naing"

TIMEZONE = pytz.timezone('Asia/Yangon')

PRICES = """
💎 Diamond ဈေးနှုန်းများ
❗️Minimum order = 55 💎

💎 55 = 4,800 MMK
💎 86 = 5,300 MMK
💎 165 = 14,300 MMK
💎 172 = 15,000 MMK
💎 257 = 22,300 MMK
💎 275 = 23,800 MMK
💎 343 = 30,000 MMK
💎 565 = 48,800 MMK
💎 706 = 61,000 MMK
💎 2195 = 189,000 MMK
💎 3688 = 317,300 MMK
💎 5532 = 475,900 MMK
💎 9288 = 799,000 MMK

🎟 Weekly Pass = 6,500 MMK
🎟 Twilight Pass = 35,000 MMK
"""

GET_ORDER_INFO, GET_AMOUNT, CONFIRM_ALL, WAIT_PAYMENT = range(4)

# ==========================================
# 🤖 HANDLERS
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE)

    if not (11 <= now.hour < 17):
        await update.message.reply_text(
            "🌙 **Pepe GameShop is currently CLOSED.**\n"
            "Open time: 11AM - 5PM"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Welcome 🎮\nSend Name + ID (Zone)\nExample: Pepe 123456789 (1234)"
    )
    return GET_ORDER_INFO


async def handle_order_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_details'] = update.message.text
    await update.message.reply_text(f"{PRICES}\nEnter amount / pass type:")
    return GET_AMOUNT


async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['amount'] = update.message.text

    kb = [["Yes", "No"]]

    await update.message.reply_text(
        f"Check info:\n\n"
        f"ID: {context.user_data['order_details']}\n"
        f"Amount: {context.user_data['amount']}\n\nConfirm?",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRM_ALL


async def confirm_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Yes":
        await update.message.reply_text(
            f"💳 Payment Info\n\n"
            f"KBZPay: {KPAY_NUMBER}\n"
            f"Name: {KPAY_NAME}\n\n"
            f"Wave: {WAVE_NUMBER}\n"
            f"Name: {WAVE_NAME}\n\n"
            "Send screenshot after payment."
        )
        return WAIT_PAYMENT
    else:
        await update.message.reply_text("Restart with /start")
        return ConversationHandler.END


async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not update.message.photo:
        await update.message.reply_text("Please send screenshot.")
        return WAIT_PAYMENT

    photo = update.message.photo[-1].file_id
    data = context.user_data

    caption = (
        "📦 New Order\n"
        f"Info: {data.get('order_details')}\n"
        f"Amount: {data.get('amount')}\n"
        f"User: @{user.username or user.first_name}"
    )

    buttons = [
        [InlineKeyboardButton("✅ Accept", callback_data=f"acc|{user.id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"rej|{user.id}")]
    ]

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    await update.message.reply_text("Waiting admin approval...")
    return ConversationHandler.END


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("|")
    action = parts[0]
    uid = int(parts[1]) if len(parts) > 1 else None

    if not uid:
        return

    if action == "acc":
        await context.bot.send_message(uid, "Processing your diamonds ⏳")

        await query.edit_message_caption(
            caption=query.message.caption + "\n\nAPPROVED ✅"
        )

    elif action == "rej":
        await context.bot.send_message(uid, "Payment rejected ❌")

        await query.edit_message_caption(
            caption=query.message.caption + "\n\nREJECTED ❌"
        )


# ==========================================
# 🚀 MAIN
# ==========================================

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GET_ORDER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order_info)],
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
            CONFIRM_ALL: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_all)],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO, handle_payment)],
        },
        fallbacks=[CommandHandler('start', start)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_callback))

    print("Bot running...")
    app.run_polling()
