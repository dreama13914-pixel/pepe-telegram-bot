import os
from datetime import datetime
import pytz

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

ADMIN_ID = 7488034821
ADMIN_ROUTING = {}

GET_ORDER, WAIT_ADMIN, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(5)

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
# SHOP TIME (MYANMAR)
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
        "📌 ဥပမာ - Pepe 123456 (7788)\n\n"
        "⏳ Server စစ်ဆေးပြီး စျေးနှုန်းပို့ပေးပါမည်"
    )
    return GET_ORDER

# =========================
# USER ORDER
# =========================
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id
    text = update.message.text

    context.user_data["order"] = text

    msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🔍 NEW ORDER REQUEST\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"👤 User: {user_id}\n"
            f"📝 ID: {text}\n\n"
            "📌 Reply:\n"
            "server: myanmar / singapore / ban"
        )
    )

    ADMIN_ROUTING[msg.message_id] = {
        "user_id": user_id,
        "context": context
    }

    await update.message.reply_text(
        "⏳ Admin မှ server စစ်ဆေးနေပါသည်...\n"
        "ခဏစောင့်ပါ"
    )

    return WAIT_ADMIN

# =========================
# ADMIN CONTROL (FIXED)
# =========================
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    msg_id = update.message.reply_to_message.message_id

    if msg_id not in ADMIN_ROUTING:
        return await update.message.reply_text("❌ Session expired")

    session = ADMIN_ROUTING[msg_id]
    user_id = session["user_id"]
    user_ctx = session["context"]

    text = update.message.text.lower().strip()

    # FIX: accept both formats
    if "server:" in text:
        server = text.split("server:")[1].strip()
    else:
        server = text

    if server not in ["myanmar", "singapore", "ban"]:
        return await update.message.reply_text("❌ myanmar / singapore / ban only")

    if server == "ban":
        await context.bot.send_message(user_id, "❌ သင့် order ကို လက်မခံနိုင်ပါ")
        del ADMIN_ROUTING[msg_id]
        return

    user_ctx.user_data["server"] = server

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "🎯 Server Confirmed\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 Server: {server.upper()}\n\n"
            "💎 Amount ရိုက်ပါ\n"
            "ဥပမာ - 86 / weekly / twilight"
        )
    )

    del ADMIN_ROUTING[msg_id]
    user_ctx.user_data["flow"] = GET_AMOUNT

# =========================
# AMOUNT HANDLER (FIXED)
# =========================
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get("flow") != GET_AMOUNT:
        return

    raw = update.message.text.lower().strip()

    try:
        amount = int(raw)
    except:
        amount = raw

    server = context.user_data.get("server", "myanmar")

    if amount in MMK_PRICES:
        price = MMK_PRICES[amount]
    elif amount in PASS_PRICES:
        price = PASS_PRICES[amount]
    else:
        await update.message.reply_text("❌ မရှိပါ")
        return

    if server == "singapore":
        price += SG_EXTRA

    context.user_data["amount"] = amount
    context.user_data["price"] = price

    await update.message.reply_text(
        "🔍 ပြန်စစ်ပါ\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Order: {context.user_data['order']}\n"
        f"💎 Item: {amount}\n"
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

    return ConversationHandler.END

# =========================
# MAIN (RENDER SAFE - NO LOOP ERROR)
# =========================
def main():

    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order)],
            WAIT_ADMIN: [MessageHandler(filters.TEXT, lambda u, c: None)],
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO, lambda u, c: None)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Chat(ADMIN_ID) & filters.TEXT, handle_admin))

    print("BOT RUNNING 🚀")

    # FIX: prevents Render crash
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
