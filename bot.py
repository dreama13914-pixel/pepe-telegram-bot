import os
from datetime import datetime
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, CallbackQueryHandler, filters
)

# ================= CONFIG =================

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

GET_ID, GET_SERVER, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(5)

KBZPAY = "09401878226"
WAVEPAY = "09788599697"
SG_EXTRA = 2900

SHOP_TZ = pytz.timezone("Asia/Yangon")

# ================= SHOP TIME =================

def shop_open():
    now = datetime.now(SHOP_TZ)
    minutes = now.hour * 60 + now.minute
    return 11 * 60 <= minutes <= 19 * 60 + 30


# ================= PRICE LIST =================

PRICE_TEXT = """💎 Diamond ဈေးနှုန်းများ

❗️Minimum order = 55 💎

💎55 = 4,850 MMK
💎86 = 5,350 MMK
💎165 = 14,350 MMK
💎172 = 15,050 MMK
💎257 = 22,350 MMK
💎275 = 23,850 MMK
💎343 = 30,050 MMK
💎565 = 48,850 MMK
💎706 = 61,050 MMK
💎2195 = 189,050 MMK
💎3688 = 317,350 MMK
💎5532 = 475,950 MMK
💎9288 = 799,050 MMK

🎟 Weekly Pass 1 = 6,550 MMK
🎟 Weekly Pass 2 = 13,100 MMK
🎟 Weekly Pass 3 = 19,650 MMK
🎟 Twilight Pass = 35,050 MMK
"""

BASE_PRICES = {
    55: 4850, 86: 5350, 165: 14350, 172: 15050,
    257: 22350, 275: 23850, 343: 30050,
    565: 48850, 706: 61050, 2195: 189050,
    3688: 317350, 5532: 475950, 9288: 799050
}

PASS_PRICES = {
    "weekly1": 6550,
    "weekly2": 13100,
    "weekly3": 19650,
    "twilight": 35050
}

# ================= MEMORY =================

user_data = {}

# ================= SAFE GET =================

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {}
    return user_data[uid]


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not shop_open():
        await update.message.reply_text("🔒 ဆိုင်ပိတ်ထားပါသည်\n🕒 ဖွင့်ချိန် (11:00 - 19:30)")
        return ConversationHandler.END

    uid = update.effective_chat.id
    get_user(uid).clear()

    await update.message.reply_text(
        "👋 မင်္ဂလာပါ!\n🎮 Pepe's Diamond Shop မှ ကြိုဆိုပါတယ်\n\n"
        "📌 လူကြီးမင်း၏ Game ID ကို ပို့ပေးပါရန်\n👉 ဥပမာ - Pepe 1600113465 (16740)"
    )

    return GET_ID


# ================= GET ID =================

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_chat.id
    data = get_user(uid)

    data["id"] = update.message.text

    keyboard = [
        [InlineKeyboardButton("🇲🇲 Myanmar", callback_data=f"mm_{uid}")],
        [InlineKeyboardButton("🇸🇬 Singapore", callback_data=f"sg_{uid}")],
        [InlineKeyboardButton("🚫 Ban", callback_data=f"ban_{uid}")]
    ]

    await context.bot.send_message(
        ADMIN_ID,
        f"🔍 NEW ID CHECK\n{update.message.text}\nUSER: {uid}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("⏳ Admin မှ စစ်ဆေးပေးနေပါသဖြင့် ခေတ္တစောင့်ဆိုင်းပေးပါရန်...")
    return GET_SERVER


# ================= SERVER =================

async def server_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("_")
    uid = int(uid)

    data = get_user(uid)

    # Find the main ConversationHandler in the application to update customer state
    conv_handler = None
    for handler in context.application.handlers[0]:
        if isinstance(handler, ConversationHandler):
            conv_handler = handler
            break

    if action == "ban":
        await context.bot.send_message(uid, "❌ Ban server ဖြစ်သဖြင့် လူကြီးမင်း၏ Order ကို ငြင်းပယ်ထားပါသည်")
        if conv_handler:
            context.application.conversation_tracker.update_state(conv_handler, (uid, uid), ConversationHandler.END)
        return

    data["server"] = action

    await context.bot.send_message(
        uid,
        f"🎯 Server: {action.upper()}\n\n{PRICE_TEXT}\n\n💎 ဝယ်ယူလိုသည့် ပမာဏကို ရိုက်ထည့်ပေးပါရန်"
    )

    # Manually move the user from GET_SERVER state over to GET_AMOUNT state
    if conv_handler:
        context.application.conversation_tracker.update_state(conv_handler, (uid, uid), GET_AMOUNT)


# ================= AMOUNT =================

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_chat.id
    data = get_user(uid)

    text = update.message.text.lower().strip()

    if "server" not in data:
        await update.message.reply_text("❌ အဆင်မပြေမှုရှိပါသဖြင့် /start ကို ပြန်နှိပ်ပေးပါရန်")
        return ConversationHandler.END

    try:
        value = int(text)
    except:
        value = text

    price = None

    if isinstance(value, int) and value in BASE_PRICES:
        price = BASE_PRICES[value]
    elif isinstance(value, str) and value in PASS_PRICES:
        price = PASS_PRICES[value]

    if price is None:
        await update.message.reply_text("❌ ဝယ်ယူလိုသည့်အမျိုးအစား ရှာမတွေ့ပါသဖြင့် ပြန်လည်ရိုက်ထည့်ပေးပါရန်")
        return GET_AMOUNT

    if data["server"] == "sg":
        price += SG_EXTRA

    data["amount"] = value
    data["price"] = price

    await update.message.reply_text(
        f"🔍 အော်ဒါအတည်ပြုရန်\nအမျိုးအစား: {value}\nကျသင့်ငွေ: {price} MMK\n\nအတည်ပြုရန် YES ဟု ရိုက်ပို့ပေးပါရန်"
    )

    return CONFIRM


# ================= CONFIRM =================

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text.lower() != "yes":
        await update.message.reply_text("အတည်ပြုရန် YES ဟု ရိုက်ပို့ပေးရပါမည်")
        return CONFIRM

    await update.message.reply_text(
        f"💳 Ngwe pay ryan a chat a lak\n\nKBZPay: {KBZPAY}\nWavePay: {WAVEPAY}\n\n📸 ငွေလွှဲပြေစာ (Screenshot) ကို ပို့ပေးပါရန်"
    )

    return WAIT_PAYMENT


# ================= PAYMENT =================

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_chat.id

    keyboard = [
        [InlineKeyboardButton("✅ ACCEPT", callback_data=f"acc_{uid}")],
        [InlineKeyboardButton("❌ REJECT", callback_data=f"rej_{uid}")]
    ]

    await context.bot.send_message(
        ADMIN_ID,
        "💰 NEW PAYMENT RECEIVED",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await context.bot.forward_message(ADMIN_ID, uid, update.message.message_id)
    
    await update.message.reply_text("✨ ငွေလွှဲပြေစာ လက်ခံရရှိပါပြီ။ Admin မှ စစ်ဆေးပြီးပါက Diamond ထည့်သွင်းပေးသွားမည်ဖြစ်ပါသည်။")

    return ConversationHandler.END


# ================= ADMIN =================

async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("_")
    uid = int(uid)

    if action == "rej":
        await context.bot.send_message(uid, "❌ လူကြီးမင်း ပေးပို့ထားသော ငွေလွှဲပြေစာ အဆင်မပြေပါသဖြင့် အော်ဒါကို ငြင်းပယ်ထားပါသည်")
        return

    await context.bot.send_message(uid, "⏳ Diamond များ ထည့်သွင်းပေးနေပါသဖြင့် ခေတ္တစောင့်ဆိုင်းပေးပါရန်...")

    await context.bot.send_message(
        ADMIN_ID,
        f"User {uid} accepted",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏁 FINISH", callback_data=f"fin_{uid}")]
        ])
    )


# ================= FINISH =================

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    _, uid = query.data.split("_")
    uid = int(uid)

    await context.bot.send_message(uid, "🎉 Diamond များ ထည့်သွင်းမှု အောင်မြင်ပါပြီ။ အားပေးမှုကို ကျေးဇူးတင်ရှိပါသည်။")


# ================= MAIN =================

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_id)],
            GET_SERVER: [], # Kept as placeholder state while user waits for Admin interaction
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO, payment)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv)
    
    # Registering interactive callback handlers globally so Admin commands clear correctly
    app.add_handler(CallbackQueryHandler(server_buttons, pattern="^(mm|sg|ban)_"))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^(acc|rej)_"))
    app.add_handler(CallbackQueryHandler(finish, pattern="^fin_"))

    print("BOT RUNNING 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
