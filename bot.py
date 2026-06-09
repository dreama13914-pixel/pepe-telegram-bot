import os
from datetime import datetime
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)

# ================= CONFIG =================

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Explicit custom state definitions to replace ConversationHandler
STATE_IDLE = "IDLE"
STATE_GET_ID = "GET_ID"
STATE_GET_SERVER = "GET_SERVER"
STATE_GET_AMOUNT = "GET_AMOUNT"
STATE_CONFIRM = "CONFIRM"
STATE_WAIT_PAYMENT = "WAIT_PAYMENT"

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
        user_data[uid] = {"state": STATE_IDLE}
    return user_data[uid]


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not shop_open():
        await update.message.reply_text("🔒 ဆိုင်ပိတ်ထားပါတယ်။\n🕒 ဆိုင်ဖွင့်ချိန်ကတော့ (11:00 - 19:30) ဖြစ်ပါတယ်နော်။")
        return

    uid = update.effective_chat.id
    user_data[uid] = {"state": STATE_GET_ID}

    await update.message.reply_text(
        "👋 မင်္ဂလာပါ!\n🎮 Pepe's Diamond Shop မှ ကြိုဆိုပါတယ်နော်။\n\n"
        "📌 Diamond ထည့်ပေးရမယ့် Game ID ပို့ပေးပါ။\n👉 ဥပမာ - Pepe 1600113465 (16740)"
    )


# ================= INCOMING MESSAGES ROUTER =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_chat.id
    data = get_user(uid)
    current_state = data.get("state", STATE_IDLE)

    # 1. GET ID STATE
    if current_state == STATE_GET_ID:
        if not update.message.text:
            return
        data["id"] = update.message.text
        data["state"] = STATE_GET_SERVER

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

        await update.message.reply_text("⏳ Admin ဘက်က ID စစ်ပေးနေလို့ ခေတ္တစောင့်ဆိုင်းပေးပါနော်...")
        return

    # 2. GET AMOUNT STATE
    elif current_state == STATE_GET_AMOUNT:
        if not update.message.text:
            return
        text = update.message.text.lower().strip()

        if "server" not in data:
            await update.message.reply_text("❌ စနစ်ပိုင်းအဆင်မပြေဖြစ်သွားလို့ /start ကို ပြန်နှိပ်ပေးပါ။")
            data["state"] = STATE_IDLE
            return

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
            await update.message.reply_text("❌ ဝယ်ယူလိုတဲ့ ပမာဏ/အမျိုးအစား မှားယွင်းနေလို့ သေချာပြန်ရိုက်ပေးပါနော်။")
            return

        if data["server"] == "sg":
            price += SG_EXTRA

        data["amount"] = value
        data["price"] = price
        data["state"] = STATE_CONFIRM

        await update.message.reply_text(
            f"🔍 အော်ဒါအချက်အလက်ကို ပြန်စစ်ပေးပါ။\n\n"
            f"• ဝယ်ယူမည့်အမျိုးအစား: {value}\n"
            f"• ကျသင့်ငွေ: {price:,} MMK\n\n"
            f"👉 အတည်ပြုပြီး ဝယ်ယူမယ်ဆိုရင် YES ဟု ရိုက်ပို့ပေးပါနော်။"
        )
        return

    # 3. CONFIRM STATE
    elif current_state == STATE_CONFIRM:
        if not update.message.text:
            return
        if update.message.text.lower() != "yes":
            await update.message.reply_text("⚠️ အော်ဒါအတည်ပြုဖို့အတွက် YES ဟု စာလုံးအမှန်အတိုင်း ရိုက်ပို့ပေးပါ။")
            return

        data["state"] = STATE_WAIT_PAYMENT
        await update.message.reply_text(
            f"💳 ငွေပေးချေရမယ့် အကောင့်အချက်အလက်များ\n\n"
            f"• KBZPay: {KBZPAY}\n"
            f"• WavePay: {WAVEPAY}\n\n"
            f"📸 ငွေလွှဲပြီးသွားရင် ဖြတ်ပိုင်း (Screenshot) လေးကို ဒီမှာ ပို့ပေးခဲ့ပါနော်။"
        )
        return

    # 4. WAIT PAYMENT STATE
    elif current_state == STATE_WAIT_PAYMENT:
        if not update.message.photo:
            await update.message.reply_text("❌ ငွေလွှဲဖြတ်ပိုင်း Screenshot ပုံ ပို့ပေးရပါမယ်။ ပုံလေးပြန်ပို့ပေးပါ။")
            return

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
        await update.message.reply_text("✨ ငွေလွှဲဖြတ်ပိုင်း လက်ခံရရှိပါပြီ။\nAdmin က စစ်ဆေးပြီးတာနဲ့ Diamond ချက်ချင်းထည့်သွင်းပေးသွားမှာမို့ ခေတ္တစောင့်ပေးပါနော်။")
        
        data["state"] = STATE_IDLE
        return


# ================= SERVER CALLBACK (ADMIN ACTION) =================

async def server_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("_")
    uid = int(uid)

    data = get_user(uid)

    if action == "ban":
        await context.bot.send_message(uid, "❌ စည်းကမ်းချက်များနှင့် မကိုက်ညီလို့ အော်ဒါကို ငြင်းပယ်ထားပါတယ်။")
        data["state"] = STATE_IDLE
        return

    # Assign server selection to the unique customer's dataset
    data["server"] = action
    # Explicitly set the customer's state to accept an amount next
    data["state"] = STATE_GET_AMOUNT

    await context.bot.send_message(
        uid,
        f"🎯 ရွေးချယ်ထားသော Server: {action.upper()}\n\n"
        f"{PRICE_TEXT}\n"
        f"👉 အထက်ပါဈေးနှုန်းများအတိုင်း ဝယ်ယူလိုတဲ့ ပမာဏ (သို့) အမျိုးအစားကို ရိုက်ထည့်ပေးပါနော်။"
    )


# ================= ADMIN ACTIONS CALLBACK =================

async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("_")
    uid = int(uid)

    if action == "rej":
        await context.bot.send_message(uid, "❌ ပေးပို့ထားတဲ့ ငွေလွှဲဖြတ်ပိုင်း အဆင်မပြေလို့ အော်ဒါကို ငြင်းပယ်ထားပါတယ်။ အချက်အလက်များ ပြန်လည်စစ်ဆေးပေးပါ။")
        return

    await context.bot.send_message(uid, "⏳ ငွေလွှဲပြေစာ စစ်ဆေးပြီးပါပြီ။ Diamond များ ထည့်သွင်းပေးနေပြီမို့ ခေတ္တစောင့်ဆိုင်းပေးပါနော်...")

    await context.bot.send_message(
        ADMIN_ID,
        f"User {uid} accepted",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏁 FINISH", callback_data=f"fin_{uid}")]
        ])
    )


# ================= FINISH CALLBACK =================

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, uid = query.data.split("_")
    uid = int(uid)

    await context.bot.send_message(uid, "🎉 အကောင့်ထဲကို Diamond များ ထည့်သွင်းမှု အောင်မြင်စွာ ပြီးဆုံးပါပြီ!\nPepe's Diamond Shop ကို အားပေးတဲ့အတွက် အထူးပင် ကျေးဇူးတင်ရှိပါတယ်နော်။ 🥰")


# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Base operational routes
    app.add_handler(CommandHandler("start", start))
    
    # Callback query handlers for internal operations
    app.add_handler(CallbackQueryHandler(server_buttons, pattern="^(mm|sg|ban)_"))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^(acc|rej)_"))
    app.add_handler(CallbackQueryHandler(finish, pattern="^fin_"))
    
    # Unified custom message router handling all incoming states
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    print("BOT RUNNING 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
