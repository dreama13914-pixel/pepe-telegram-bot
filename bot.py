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
# This reads your token safely from the host settings. No colons are used here!
TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 7488034821 
KPAY_NUMBER = "09401878226"
WAVEPAY_NUMBER = "09788599697"
PAYMENT_NAME = "Li Li Naing"

PRICES = """
💎 **Diamond Prices**
❗️Minimum order = 55 💎

💎 55 = 5,100 MMK
💎 86 = 5,300 MMK
💎 165 = 14,600 MMK
💎 172 = 15,300 MMK
💎 257 = 22,600 MMK
💎 275 = 24,100 MMK
💎 343 = 30,300 MMK
💎 565 = 49,100 MMK
💎 706 = 61,300 MMK
💎 2195 = 189,300 MMK
💎 3688 = 317,600 MMK
💎 5532 = 476,500 MMK
💎 9288 = 799,300 MMK

🎟 Weekly Pass = 6,800 MMK
🎟 Twilight Pass = 35,300 MMK
"""

GET_ORDER_INFO, GET_AMOUNT, CONFIRM_ALL, WAIT_PAYMENT = range(4)

# ==========================================
# 🤖 BOT HANDLERS
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Pepe GameShop! 🎮\n\n"
        "To purchase Diamonds, please send your **Name** and **ID (Zone)**.\n"
        "Example: Pepe 123456789 (1234)"
    )
    return GET_ORDER_INFO

async def handle_order_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_details'] = update.message.text
    await update.message.reply_text(f"{PRICES}\nPlease type the Amount or Pass type you want to buy.")
    return GET_AMOUNT

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['amount'] = update.message.text
    
    recheck_text = (
        "🔍 **Please verify your information**\n\n"
        f"📝 ID/Name: {context.user_data['order_details']}\n"
        f"💎 Amount: {context.user_data['amount']}\n\n"
        "Is the above information correct?"
    )
    
    kb = [["Yes", "No"]]
    await update.message.reply_text(
        recheck_text,
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRM_ALL

async def confirm_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Yes":
        await update.message.reply_text(
            f"💳 **Payment Info**\n\n"
            f"🔹 Kpay - {KPAY_NUMBER}\n"
            f"🔹 WavePay - {WAVEPAY_NUMBER}\n"
            f"👤 Name - {PAYMENT_NAME}\n\n"
            f"Please send the transaction receipt (Screenshot) once paid."
        )
        return WAIT_PAYMENT
    else:
        await update.message.reply_text("Information incorrect. Click /start to try again.")
        return ConversationHandler.END

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = context.user_data
    
    if not update.message.photo:
        await update.message.reply_text("Please send your payment screenshot photo.")
        return WAIT_PAYMENT

    photo = update.message.photo[-1].file_id
    caption = (
        f"📦 **New Order Received!**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 Info: {data.get('order_details')}\n"
        f"💎 Amount: {data.get('amount')}\n"
        f"👤 From: @{user.username if user.username else user.first_name}\n"
        f"━━━━━━━━━━━━━━━"
    )
    
    buttons = [
        [InlineKeyboardButton("✅ Accept Payment", callback_data=f"acc|{user.id}")],
        [InlineKeyboardButton("❌ Reject Payment", callback_data=f"rej|{user.id}")]
    ]
    
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
    await update.message.reply_text("Admin is verifying your receipt. Please hold on a moment.")
    return ConversationHandler.END

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, uid = query.data.split("|")
    if action == "acc":
        await context.bot.send_message(uid, "Payment verified successfully! Your Diamonds are being processed. Please wait around 3 minutes. ⏳")
        new_buttons = [[InlineKeyboardButton("🚀 Mark as Success", callback_data=f"done|{uid}")]]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(new_buttons))
    elif action == "rej":
        restart_btn = [[InlineKeyboardButton("🔄 Restart Process", callback_data="user_restart")]]
        await context.bot.send_message(uid, "Payment verification failed. Please check your receipt and try again. ❌", reply_markup=InlineKeyboardMarkup(restart_btn))
        await query.edit_message_caption(query.message.caption + "\n\nStatus: [REJECTED ❌]")
    elif action == "done":
        await context.bot.send_message(uid, "Your purchased Diamonds have been sent. Thank you! ✅")
        await query.edit_message_caption(query.message.caption + "\n\nStatus: [SUCCESS ✅]")

async def user_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Press /start to begin.")

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
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(acc|rej|done)"))
    app.add_handler(CallbackQueryHandler(user_restart, pattern="^user_restart$"))
    
    print("Pepe Shop is LIVE 24/7!")
    app.run_polling()