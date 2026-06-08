import os
from datetime import datetime
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, CallbackQueryHandler, filters
)

ADMIN_ID = 7488034821

GET_ORDER, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(4)

# =========================
# 💎 PRICE LIST
# =========================
MMK_PRICES = {
    55: 4800,
    86: 5300,
    165: 14300,
    172: 15000,
    257: 22300,
    275: 23800,
    343: 30000,
    565: 48800,
    706: 61000,
    2195: 189000,
    3688: 317300,
    5532: 475900,
    9288: 799000
}

PASS_PRICES = {
    "weekly": 6500,
    "twilight": 35000
}

SG_EXTRA = 2900

# =========================
# SHOP TIME
# =========================
SHOP_TZ = pytz.timezone("Asia/Yangon")

def shop_open():
    now = datetime.now(SHOP_TZ)
    minutes = now.hour * 60 + now.minute
    return (11 * 60) <= minutes <= (19 * 60 + 30)

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not shop_open():
        await update.message.reply_text(
            "🔒 ဆိုင်ပိတ်ထားပါသည်\n\n"
            "🕚 ဖွင့်ချိန် - 11:00 AM\n"
            "🕢 ပိတ်ချိန် - 7:30 PM\n\n"
            "ကျေးဇူးပြု၍ ဖွင့်ချိန်တွင် ပြန်လာပါ 🙏"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🎮 Pepe GameShop မှ ကြိုဆိုပါတယ်\n\n"
        "💎 Diamond / Pass ဝယ်ယူလိုပါက\n"
        "သင့် Game ID ပို့ပေးပါ\n\n"
        "📌 ဥပမာ - Pepe 123456 (7788)"
    )

    return GET_ORDER

# =========================
# USER ORDER → ADMIN BUTTONS
# =========================
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id
    text = update.message.text

    context.user_data["order"] = text

    keyboard = [
        [InlineKeyboardButton("🇲🇲 Myanmar", callback_data=f"myanmar_{user_id}")],
        [InlineKeyboardButton("🇸🇬 Singapore", callback_data=f"singapore_{user_id}")],
        [InlineKeyboardButton("🚫 Ban", callback_data=f"ban_{user_id}")]
    ]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔍 NEW ORDER\n👤 User: {user_id}\n📝 ID: {text}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("⏳ Admin စစ်ဆေးနေပါသည်...")
    return GET_AMOUNT

# =========================
# ADMIN BUTTON HANDLER
# =========================
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    action, user_id = query.data.split("_")
    user_id = int(user_id)

    if action == "ban":
        await context.bot.send_message(user_id, "❌ သင့် order ကို လက်မခံနိုင်ပါ")
        return

    context.user_data[user_id] = {"server": action}

    await context.bot.send_message(
        user_id,
        "🎯 Server Confirmed\n"
        f"🌍 Server: {action.upper()}\n\n"
        "💎 Amount ရိုက်ပါ\n"
        "ဥပမာ - 86 / weekly / twilight"
    )

# =========================
# AMOUNT HANDLER
# =========================
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id
    raw = update.message.text.lower().strip()

    try:
        amount = int(raw)
    except:
        amount = raw

    user_data = context.user_data.get(user_id, {})
    server = user_data.get("server", "myanmar")

    if amount in MMK_PRICES:
        price = MMK_PRICES[amount]
    elif amount in PASS_PRICES:
        price = PASS_PRICES[amount]
    else:
        await update.message.reply_text("❌ မရှိပါ")
        return

    if server == "singapore":
        price += SG_EXTRA

    user_data["amount"] = amount
    user_data["price"] = price
    context.user_data[user_id] = user_data

    await update.message.reply_text(
        "🔍 ပြန်စစ်ပါ\n"
        f"📦 Item: {amount}\n"
        f"🌍 Server: {server}\n"
        f"💰 Price: {price}\n\n"
        "YES ရိုက်ပါ"
    )

    return CONFIRM

# =========================
# CONFIRM
# =========================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text.lower() == "yes":
        await update.message.reply_text(
            "💳 Payment Info\n\n"
            "KBZPay / Wave Money\n\n"
            "ငွေလွှဲပြီး screenshot ပို့ပါ 📸"
        )
        return WAIT_PAYMENT

# =========================
# PAYMENT → ADMIN
# =========================
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id

    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=user_id,
        message_id=update.message.message_id
    )

    await update.message.reply_text("✅ Order received!\nကျေးဇူးတင်ပါတယ် 🙏")

    return ConversationHandler.END

# =========================
# MAIN (RENDER FIXED)
# =========================
def main():

    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

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
    app.add_handler(CallbackQueryHandler(handle_buttons))

    print("BOT RUNNING 🚀")

    # Render safe (prevents event loop crash)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
