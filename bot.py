import os
from datetime import datetime
import pytz

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

# ==========================================
# ⚙️ CONFIG
# ==========================================
TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

KPAY_NUMBER = "09401878226"
KPAY_NAME = "Li Li Naing"

WAVE_NUMBER = "09401878226"
WAVE_NAME = "Li Li Naing"

TIMEZONE = pytz.timezone("Asia/Yangon")

# ==========================================
# 💎 PRICE LIST (+300 MMK UPDATED)
# ==========================================
PRICES = """
💎 Diamond ဈေးနှုန်းများ
❗️Minimum order = 55 💎

💎 55 = 5,100 MMK
💎 86 = 5,600 MMK
💎 165 = 14,600 MMK
💎 172 = 15,300 MMK
💎 257 = 22,600 MMK
💎 275 = 24,100 MMK
💎 343 = 30,300 MMK
💎 565 = 49,100 MMK
💎 706 = 61,300 MMK
💎 2195 = 189,300 MMK
💎 3688 = 317,600 MMK
💎 5532 = 476,200 MMK
💎 9288 = 799,300 MMK

🎟 Weekly Pass = 6,800 MMK
🎟 Twilight Pass = 35,300 MMK
"""

# ==========================================
# STATES
# ==========================================
GET_ORDER, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(4)

# ==========================================
# START
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE)

    if not (11 <= now.hour < 17):
        await update.message.reply_text(
            "🌙 Shop is CLOSED (11AM - 5PM)"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🎮 Pepe GameShop မှ ကြိုဆိုပါတယ်\n\n"
        "Name + ID ပို့ပါ\nExample: Pepe 123456789 (1234)"
    )
    return GET_ORDER


# ==========================================
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"] = update.message.text

    await update.message.reply_text(PRICES + "\n💎 Amount / Pass ရေးပါ")
    return GET_AMOUNT


# ==========================================
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["amount"] = update.message.text

    kb = [["Yes", "No"]]

    await update.message.reply_text(
        f"🔍 Confirm\n\n"
        f"{context.user_data['order']}\n"
        f"{context.user_data['amount']}\n\n"
        "မှန်ပါသလား?",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
    )
    return CONFIRM


# ==========================================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text != "Yes":
        await update.message.reply_text("Restart /start")
        return ConversationHandler.END

    await update.message.reply_text(
        "💳 Payment Info\n\n"
        f"KBZPay: {KPAY_NUMBER}\n{KPAY_NAME}\n\n"
        f"Wave: {WAVE_NUMBER}\n{WAVE_NAME}\n\n"
        "Screenshot ပို့ပါ"
    )
    return WAIT_PAYMENT


# ==========================================
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not update.message.photo:
        await update.message.reply_text("Screenshot ပို့ပါ")
        return WAIT_PAYMENT

    data = context.user_data

    caption = (
        "📦 NEW ORDER\n\n"
        f"ID: {data.get('order')}\n"
        f"Amount: {data.get('amount')}\n"
        f"User: @{user.username or user.first_name}"
    )

    buttons = [
        [InlineKeyboardButton("✅ ACCEPT", callback_data=f"acc|{user.id}")],
        [InlineKeyboardButton("❌ REJECT", callback_data=f"rej|{user.id}")]
    ]

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    await update.message.reply_text("Admin စစ်နေပါတယ်...")
    return ConversationHandler.END


# ==========================================
# ADMIN CALLBACK (FULL FLOW)
# ==========================================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        action, uid = query.data.split("|")
        uid = int(uid)
    except:
        return

    # =========================
    if action == "acc":
        await context.bot.send_message(
            uid,
            "⏳ Payment approved!\n"
            "Diamond ပို့နေပါပြီ..."
        )

        new_btn = [[
            InlineKeyboardButton("🚀 DIAMOND IN ACCOUNT (DONE)", callback_data=f"done|{uid}")
        ]]

        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(new_btn)
        )

    # =========================
    elif action == "rej":
        await context.bot.send_message(
            uid,
            "❌ Payment rejected\n"
            "ပြေစာကို ပြန်စစ်ပါ"
        )

        restart_btn = [[
            InlineKeyboardButton("🔄 Restart", callback_data="restart")
        ]]

        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ REJECTED",
            reply_markup=InlineKeyboardMarkup(restart_btn)
        )

    # =========================
    elif action == "done":
        await context.bot.send_message(
            uid,
            "💎 Diamonds are now in your account!\n"
            "Pepe GameShop ကို ကျေးဇူးတင်ပါတယ် 🙏"
        )

        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✅ DELIVERED",
            reply_markup=None
        )

    # =========================
    elif query.data == "restart":
        await query.message.reply_text("စတင်ရန် /start")


# ==========================================
# MAIN
# ==========================================
def main():
    if not TOKEN:
        print("BOT_TOKEN missing")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order)],
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO, payment)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(callback))

    print("Bot running 24/7 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()
