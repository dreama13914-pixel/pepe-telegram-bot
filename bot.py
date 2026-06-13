import os
import re
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

STATE_GET_ID = "GET_ID"
STATE_SELECT_SERVER = "SELECT_SERVER"
STATE_GET_AMOUNT = "GET_AMOUNT"
STATE_CONFIRM_AMOUNT = "CONFIRM_AMOUNT"
STATE_WAIT_PAYMENT = "WAIT_PAYMENT"

KBZPAY = "09401878226"
WAVEPAY = "09788599697"

user_data = {}

# ================= SHOP TIME =================

def is_shop_open():
    tz = pytz.timezone('Asia/Yangon')
    now = datetime.now(tz).time()
    start = datetime.strptime("11:00", "%H:%M").time()
    end = datetime.strptime("19:30", "%H:%M").time()
    return start <= now <= end

# ================= EXACT VERTICAL PRICE TEXT SHEETS =================

PRICE_SHEETS = {
    "MYANMAR": """💎 MYANMAR SERVER ဈေးနှုန်းများ
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
🎟 Starlight Card = 25,700 MMK""",

    "SG_MY": """💎 SINGAPORE & MALAYSIA SERVER ဈေးနှုန်းများ
❗️Minimum order = 55 💎
💎55 = 7,450 MMK
💎86 = 7,950 MMK
💎165 = 16,950 MMK
💎172 = 17,650 MMK
💎257 = 24,950 MMK
💎275 = 26,450 MMK
💎343 = 32,650 MMK
💎565 = 51,450 MMK
💎706 = 63,650 MMK
💎2195 = 191,650 MMK
💎3688 = 319,950 MMK
💎5532 = 478,550 MMK
💎9288 = 801,650 MMK
🎟 Weekly Pass 1 = 9,150 MMK
🎟 Weekly Pass 2 = 15,700 MMK
🎟 Weekly Pass 3 = 22,250 MMK
🎟 Twilight Pass = 37,650 MMK
🎟 Starlight Card = 28,300 MMK""",

    "PH": """💎 PHILIPPINES SERVER ဈေးနှုန်းများ
❗️Minimum order = 55 💎
💎55 = 5,300 MMK
💎86 = 5,800 MMK
💎165 = 14,800 MMK
💎172 = 15,500 MMK
💎227 = 22,800 MMK
💎275 = 24,300 MMK
💎343 = 30,500 MMK
💎565 = 49,300 MMK
💎706 = 61,500 MMK
💎2195 = 189,500 MMK
💎3688 = 317,800 MMK
💎5532 = 476,400 MMK
💎9288 = 799,500 MMK
🎟 Weekly Pass 1 = 7,000 MMK
🎟 Weekly Pass 2 = 13,550 MMK
🎟 Weekly Pass 3 = 20,100 MMK
🎟 Twilight Pass = 35,500 MMK
🎟 Starlight Card = 26,150 MMK""",

    "ID": """💎 INDONESIA SERVER ဈေးနှုန်းများ
❗️Minimum order = 55 💎
💎55 = 5,320 MMK
💎86 = 5,820 MMK
💎165 = 14,820 MMK
💎172 = 15,520 MMK
💎257 = 22,820 MMK
💎275 = 24,320 MMK
💎343 = 30,520 MMK
💎565 = 49,320 MMK
💎706 = 61,520 MMK
💎2195 = 189,520 MMK
💎3688 = 317,820 MMK
💎5532 = 476,420 MMK
💎9288 = 799,520 MMK
🎟 Weekly Pass 1 = 7,020 MMK
🎟 Weekly Pass 2 = 13,570 MMK
🎟 Weekly Pass 3 = 20,120 MMK
🎟 Twilight Pass = 35,520 MMK
🎟 Starlight Card = 26,170 MMK"""
}

# ================= BACKEND PRICE DATA =================

PRICE_DATA = {
    "MYANMAR": {
        "55": 4850, "86": 5350, "165": 14350, "172": 15050, "257": 22350, "275": 23850,
        "343": 30050, "565": 48850, "706": 61050, "2195": 189050, "3688": 317350,
        "5532": 475950, "9288": 799050, "wp1": 6550, "wp2": 13100, "wp3": 19650,
        "twi": 35050, "starlight": 25700, "star": 25700, "starlightcard": 25700
    },
    "SG_MY": {
        "55": 7450, "86": 7950, "165": 16950, "172": 17650, "257": 24950, "275": 26450,
        "343": 32650, "565": 51450, "706": 63650, "2195": 191650, "3688": 319950,
        "5532": 478550, "9288": 801650, "wp1": 9150, "wp2": 15700, "wp3": 22250,
        "twi": 37650, "starlight": 28300, "star": 28300, "starlightcard": 28300
    },
    "PH": {
        "55": 5300, "86": 5800, "165": 14800, "172": 15500, "227": 22800, "275": 24300,
        "343": 30500, "565": 49300, "706": 61500, "2195": 189500, "3688": 317800,
        "5532": 476400, "9288": 799500, "wp1": 7000, "wp2": 13550, "wp3": 20100,
        "twi": 35500, "starlight": 26150, "star": 26150, "starlightcard": 26150
    },
    "ID": {
        "55": 5320, "86": 5820, "165": 14820, "172": 15520, "257": 22820, "275": 24320,
        "343": 30520, "565": 49320, "706": 61520, "2195": 189520, "3688": 317820,
        "5532": 476420, "9288": 799520, "wp1": 7020, "wp2": 13570, "wp3": 20120,
        "twi": 35520, "starlight": 26170, "star": 26170, "starlightcard": 26170
    }
}

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    if not is_shop_open():
        await update.message.reply_text("⛔ ဆိုင်ပိတ်နေပါပြီ။ ဆိုင်ဖွင့်ချိန်မှာ မနက် ၁၁ နာရီမှ ည ၇ခွဲ ထိဖြစ်ပါသည်။")
        return

    user_data[uid] = {"state": STATE_GET_ID}
    await update.message.reply_text("🐸 Pepe's Shop မှ ကြိုဆိုပါတယ်။\nGame ID နဲ့ Server ID ကို ရိုက်ပို့ပေးပါ။\n💡 ဥပမာ - Pepe 1600113465 (16740)")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    text = update.message.text.strip()
    if uid not in user_data: return

    state = user_data[uid].get("state")

    if state == STATE_GET_ID:
        user_data[uid]["id"] = text
        user_data[uid]["state"] = STATE_SELECT_SERVER
        kb = [
            [InlineKeyboardButton("Myanmar 🇲🇲", callback_data="srv|MYANMAR")],
            [InlineKeyboardButton("Singapore/Malaysia 🇸🇬🇲🇾", callback_data="srv|SG_MY")],
            [InlineKeyboardButton("Philippines 🇵🇭", callback_data="srv|PH")],
            [InlineKeyboardButton("Indonesia 🇮🇩", callback_data="srv|ID")],
            [InlineKeyboardButton("Others (Banned) 🚫", callback_data="srv|BANNED")]
        ]
        await update.message.reply_text("Server ကို ရွေးချယ်ပေးပါ 🌍", reply_markup=InlineKeyboardMarkup(kb))

    elif state == STATE_GET_AMOUNT:
        server = user_data[uid]["server"]
        clean_key = text.lower().replace(" ", "")
        
        price = PRICE_DATA.get(server, {}).get(clean_key)
        
        if not price:
            await update.message.reply_text("❌ မှားယွင်းနေပါသည်။ Amount ကို အမှန်အတိုင်း ပြန်ရိုက်ပေးပါ။")
            return

        user_data[uid]["tmp_item"] = text.upper()
        user_data[uid]["tmp_price"] = price
        user_data[uid]["state"] = STATE_CONFIRM_AMOUNT
        
        kb = [
            [InlineKeyboardButton("YES ✅", callback_data="conf|yes"),
             InlineKeyboardButton("NO ❌", callback_data="conf|no")]
        ]
        await update.message.reply_text(
            f"🛒 {text.upper()} = {price:,} MMK\n\nအချက်အလက်များ မှန်ကန်ပါသလား?", 
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.message.chat_id
    data = q.data.split("|")
    await q.answer()

    if data[0] == "srv":
        server = data[1]
        if server == "BANNED":
            await q.edit_message_text("⚠️ စိတ်မကောင်းပါဘူး။ ဒီ Server က Banned ဖြစ်နေတဲ့အတွက် Diamond တင်လို့မရပါဘူး။")
            return
        
        user_data[uid]["server"] = server
        user_data[uid]["state"] = STATE_GET_AMOUNT
        
        # Pulling up your exact vertical layout view string block
        sheet = PRICE_SHEETS.get(server, "")
        await q.edit_message_text(
            f"{sheet}\n\nဝယ်ယူမည့် Amount ကို ရိုက်ထည့်ပါ\n(Normal Diamond အတွက် ပမာဏတစ်ခုတည်း၊ Weekly Pass အတွက် wp 1၊ Twilight Pass အတွက် twi)"
        )

    elif data[0] == "conf":
        if data[1] == "yes":
            user_data[uid]["item"] = user_data[uid]["tmp_item"]
            user_data[uid]["price"] = user_data[uid]["tmp_price"]
            user_data[uid]["state"] = STATE_WAIT_PAYMENT
            
            pay_txt = f"💰 ကျသင့်ငွေ: {user_data[uid]['price']:,} MMK\n\n"
            pay_txt += f"KBZPay - {KBZPAY}\nWavePay - {WAVEPAY}\n\n"
            pay_txt += "ငွေလွှဲပြီးလျှင် Screenshot ပို့ပေးပါ။"
            await q.edit_message_text(pay_txt)
        else:
            user_data[uid]["state"] = STATE_GET_ID
            await q.edit_message_text("အစမှပြန်စပါမည်။ Game ID ကို ပြန်ပို့ပေးပါ။")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    if uid not in user_data or user_data[uid].get("state") != STATE_WAIT_PAYMENT: return

    # Forward payload down to Admin Chat endpoint
    await context.bot.forward_message(ADMIN_ID, uid, update.message.message_id)
    info = f"📦 Order New!\nID: {user_data[uid]['id']}\nServer: {user_data[uid]['server']}\nItem: {user_data[uid]['item']}\nPrice: {user_data[uid]['price']:,} MMK"
    await context.bot.send_message(ADMIN_ID, info)
    
    await update.message.reply_text("✨ ပြီးပါပြီ! Admin မှ စစ်ဆေးပြီးပါက Diamond များ ချက်ချင်း ထည့်သွင်းပေးသွားမည် ဖြစ်ပါသည်။")

# ================= RUN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(callback_query))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    PORT = int(os.getenv("PORT", "8000"))
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

    if RENDER_URL:
        app.run_webhook(
            listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN,
            webhook_url=f"{RENDER_URL}/{BOT_TOKEN}"
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
