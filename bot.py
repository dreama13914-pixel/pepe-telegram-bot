import os
import json
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
STATE_CONFIRM_ID = "CONFIRM_ID"
STATE_WAIT_IGN_CHECK = "WAIT_IGN_CHECK"
STATE_WAIT_ADMIN_SERVER = "WAIT_ADMIN_SERVER"
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

# ================= PRICING SYSTEM =================

BASE_ADJUST = {
    "MYANMAR": 0,
    "SINGAPORE": 2600,
    "MALAYSIA": 2600,
    "PHILIPPINES": 450,
    "INDONESIA": 470
}

MYANMAR_BASE = {
    55: 4850, 86: 5350, 165: 14350, 172: 15050, 257: 22350,
    275: 23850, 343: 30050, 565: 48850, 706: 61050,
    2195: 189050, 3688: 317350, 5532: 475950, 9288: 799050
}

MYANMAR_PASS = {
    "wp1": 6550,
    "wp2": 13100,
    "wp3": 19650,
    "twi": 35050,
    "starlight": 25700,
    "starlightcard": 25700,
    "star": 25700
}

def calc_price(server, item):
    adj = BASE_ADJUST.get(server, 0)

    if isinstance(item, int):
        base = MYANMAR_BASE.get(item)
    else:
        item = str(item).replace(" ", "").lower()
        base = MYANMAR_PASS.get(item)

    if base is None:
        return None

    return base + adj

# ================= PRICE SHEETS =================

PRICE_MYANMAR = """💎 MYANMAR SERVER ဈေးနှုန်းများ

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
🎟 Starlight Card = 25,700 MMK"""

PRICE_SG_MY = """💎 SINGAPORE & MALAYSIA SERVER ဈေးနှုန်းများ

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
🎟 Starlight Card = 28,300 MMK"""

PRICE_PH = """💎 PHILIPPINES SERVER ဈေးနှုန်းများ

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
🎟 Starlight Card = 26,150 MMK"""

PRICE_ID = """💎 INDONESIA SERVER ဈေးနှုန်းများ

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


# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id

    if not is_shop_open():
        await update.message.reply_text("ဆိုင်ပိတ်နေပါပြီ ဆိုင်ဖွင့်ချိန်မှာ မနက် ၁၁ နာရီမှ ည ၇ ခွဲဖြစ်ပါသည် ထိုအချိန်မှာ ဝယ်ယူအားပေးနိုင်ပါသည်")
        return

    user_data[uid] = {"state": STATE_GET_ID}
    await update.message.reply_text("🐸 မင်္ဂလာပါ Pepe's MLBB Diamond Shop မှကြိုဆိုပါသည်။ ဝယ်ယူဖို့အတွက် Game ID နဲ့ Zone ID ကို ရိုက်ထည့်ပေးပါ။\nဥပမာ - 123456789 (1234)")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    text = update.message.text.strip()

    if uid not in user_data:
        user_data[uid] = {}

    state = user_data[uid].get("state")

    if state == STATE_GET_ID:
        user_data[uid]["id"] = text
        user_data[uid]["state"] = STATE_CONFIRM_ID

        kb = [[
            InlineKeyboardButton("YES", callback_data=f"idconf|yes|{uid}"),
            InlineKeyboardButton("NO", callback_data=f"idconf|no|{uid}")
        ]]
        await update.message.reply_text(f"ရိုက်ထည့်လိုက်သော ID မှာ {text} မှန်ပါသလား।", reply_markup=InlineKeyboardMarkup(kb))

    elif state == STATE_GET_AMOUNT:
        quantity = 1
        clean_text = text.lower().replace(" ", "")
        
        try:
            item = int(clean_text)
        except ValueError:
            # Smart Regex: Separate letters from trailing numbers (handles both "star 2" and "star2")
            match = re.match(r"([a-z]+)(\d+)$", clean_text)
            if match:
                item = match.group(1)
                quantity = int(match.group(2))
            else:
                item = clean_text

        server = user_data[uid].get("server", "MYANMAR")
        single_price = calc_price(server, item)

        if single_price is None:
            await update.message.reply_text("မှားယွင်းနေပါသည်။ ပြန်လည်ရိုက်ထည့်ပါ။")
            return

        price = single_price * quantity
        display_item = f"{item.upper()} x{quantity}" if quantity > 1 else item.upper()

        user_data[uid]["temp_item"] = display_item
        user_data[uid]["temp_price"] = price
        user_data[uid]["state"] = STATE_CONFIRM_AMOUNT

        kb = [[
            InlineKeyboardButton("YES", callback_data=f"amtconf|yes|{uid}"),
            InlineKeyboardButton("NO", callback_data=f"amtconf|no|{uid}")
        ]]
        await update.message.reply_text(f"{display_item} = {price:,} MMK မှန်ပါသလား।", reply_markup=InlineKeyboardMarkup(kb))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    
    if uid not in user_data or user_data[uid].get("state") != STATE_WAIT_PAYMENT:
        return

    photo_id = update.message.photo[-1].file_id
    game_id = user_data[uid].get("id")
    item = user_data[uid].get("item")
    price = user_data[uid].get("price")
    server = user_data[uid].get("server")

    admin_msg = f"📩 **ငွေလွှဲဖြတ်ပိုင်း ရောက်ရှိလာပါသည်**\n\nUser ID: `{uid}`\nGame ID: `{game_id}`\nServer: {server}\nဝယ်ယူသည့်အမောင့်: {item}\nကျသင့်ငွေ: {price:,} MMK"
    
    kb = [
        [InlineKeyboardButton("✅ Accept Payment", callback_data=f"pay|accept|{uid}")],
        [InlineKeyboardButton("❌ Reject Payment", callback_data=f"pay|reject|{uid}")]
    ]

    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=admin_msg, reply_markup=InlineKeyboardMarkup(kb))
    await update.message.reply_text("ဖြတ်ပိုင်းကို ပို့လိုက်ပါပြီ။ Admin ဘက်မှ စစ်ဆေးအတည်ပြုသည်အထိ ခေတ္တစောင့်ဆိုင်းပေးပါ။")

# ================= CALLBACKS =================

async def id_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, choice, uid = q.data.split("|")
    uid = int(uid)

    if choice == "no":
        user_data[uid]["state"] = STATE_GET_ID
        await q.edit_message_text("ပြန်လည်စတင်ရန်အတွက် /start ကို နှိပ်ပေးပါ။")
        return

    user_data[uid]["state"] = STATE_WAIT_IGN_CHECK
    game_id = user_data[uid]["id"]

    await q.edit_message_text("Admin မှ Game Server စစ်ဆေးနေပါသည်။ ခေတ္တစောင့်ဆိုင်းပေးပါ။")
    
    kb = [
        [InlineKeyboardButton("IGN မှန်ကန်သည်", callback_data=f"ign|yes|{uid}")],
        [InlineKeyboardButton("IGN မမှန်ပါ/မတွေ့ပါ", callback_data=f"ign|no|{uid}")]
    ]
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📥 **IGN စစ်ဆေးရန်**\n\nGame ID: `{game_id}`\n\nဤ ID ၏ In-game Name ကို စစ်ဆေးပြီး အောက်ပါအတိုင်း အတည်ပြုပေးပါ။", reply_markup=InlineKeyboardMarkup(kb))

async def ign_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, choice, uid = q.data.split("|")
    uid = int(uid)

    if choice == "no":
        user_data[uid]["state"] = STATE_GET_ID
        await context.bot.send_message(chat_id=uid, text=f"ရိုက်ထည့်လိုက်သော ID မှာ In-game Name ရှာမတွေ့ပါ သို့မဟုတ် မှားယွင်းနေပါသည်။ /start ကိုနှိပ်ပြီး အစမှ ပြန်လုပ်ပေးပါ။")
        await q.edit_message_text("IGN မမှန်ကန်ကြောင်း ပို့လိုက်ပါပြီ။")
        return

    user_data[uid]["state"] = STATE_WAIT_ADMIN_SERVER
    
    kb = [
        [InlineKeyboardButton("🇲🇲 MYANMAR", callback_data=f"admsrv|MYANMAR|{uid}")],
        [InlineKeyboardButton("🇸🇬 SINGAPORE", callback_data=f"admsrv|SINGAPORE|{uid}")],
        [InlineKeyboardButton("🇲🇾 MALAYSIA", callback_data=f"admsrv|MALAYSIA|{uid}")],
        [InlineKeyboardButton("🇵🇭 PHILIPPINES", callback_data=f"admsrv|PHILIPPINES|{uid}")],
        [InlineKeyboardButton("🇮🇩 INDONESIA", callback_data=f"admsrv|INDONESIA|{uid}")],
        [InlineKeyboardButton("🚫 BAN SERVER", callback_data=f"admsrv|BAN|{uid}")]
    ]
    await q.edit_message_text(f"IGN အတည်ပြုပြီး။ ဆက်လက်ပြီး Server ရွေးချယ်ပေးပါ။", reply_markup=InlineKeyboardMarkup(kb))

async def admin_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, server, uid = q.data.split("|")
    uid = int(uid)

    if server == "BAN":
        user_data[uid]["state"] = STATE_GET_ID
        await context.bot.send_message(chat_id=uid, text="လူကြီးမင်း၏ Server မှာ Ban ခံထားရသော Server ဖြစ်သောကြောင့် Diamond ဝယ်ယူ၍ မရနိုင်ပါ။")
        await q.edit_message_text("Ban Server ဖြစ်ကြောင်း အကြောင်းကြားလိုက်ပါပြီ။")
        return

    user_data[uid]["server"] = server
    user_data[uid]["state"] = STATE_GET_AMOUNT

    sheet = (
        PRICE_MYANMAR if server == "MYANMAR"
        else PRICE_SG_MY if server in ["SINGAPORE", "MALAYSIA"]
        else PRICE_PH if server == "PHILIPPINES"
        else PRICE_ID
    )

    await context.bot.send_message(chat_id=uid, text=sheet)
    await context.bot.send_message(chat_id=uid, text="ဈေးနှုန်းဇယားကို ကြည့်ရှုပြီး ဝယ်ယူလိုသော Diamond အမောင့် သို့မဟုတ် ပက်ကေ့ဂျ်အမည် (ဥပမာ- 55 သို့မဟုတ် wp1) ကို ရိုက်ထည့်ပေးပါ။")
    await q.edit_message_text(f"ရွေးချယ်လိုက်သော Server: {server}")

async def amount_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, choice, uid = q.data.split("|")
    uid = int(uid)

    if choice == "no":
        user_data[uid]["state"] = STATE_GET_AMOUNT
        await q.edit_message_text("ဝယ်ယူလိုသော အမောင့်ကို ပြန်လည်ရိုက်ထည့်ပေးပါ။")
        return

    user_data[uid]["item"] = user_data[uid]["temp_item"]
    user_data[uid]["price"] = user_data[uid]["temp_price"]
    user_data[uid]["state"] = STATE_WAIT_PAYMENT

    pay_text = f"💰 **ငွေပေးချေရန် အချက်အလက်**\n\n" \
               f"ကျသင့်ငွေ: {user_data[uid]['price']:,} MMK\n\n" \
               f"📱 KBZPay: `{KBZPAY}`\n" \
               f"📱 WavePay: `{WAVEPAY}`\n\n" \
               f"ငွေလွှဲပြီးပါက ပြေစာ (Screenshot) ကို ဤနေရာတွင် ပို့ပေးပါ။"
               
    await q.edit_message_text("အမောင့်ကို အတည်ပြုပြီးပါပြီ။")
    await context.bot.send_message(chat_id=uid, text=pay_text, parse_mode="Markdown")

async def payment_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, action, uid = q.data.split("|")
    uid = int(uid)

    if action == "reject":
        user_data[uid]["state"] = STATE_GET_ID
        await context.bot.send_message(chat_id=uid, text="ငွေလွှဲဝင်လာခြင်း မရှိသေးပါ။ /start ကို နှိပ်ပြီး လုပ်ငန်းစဉ်ကို အစမှ ပြန်လည်စတင်ပေးပါ။")
        await q.edit_message_text("Payment ကို ပယ်ဖျက်လိုက်ပါသည်။")
        return

    kb = [[InlineKeyboardButton("🏁 Finish Topping", callback_data=f"finish|{uid}")]]
    await q.edit_message_text("ငွေလွှဲမှုကို အတည်ပြုလိုက်ပါပြီ။ Diamond ထည့်သွင်းပြီးပါက အောက်ပါခလုတ်ကို နှိပ်ပါ။", reply_markup=InlineKeyboardMarkup(kb))

async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("|")[1])

    user_data[uid] = {}
    await context.bot.send_message(chat_id=uid, text="Diamond ထည့်သွင်းခြင်း လုပ်ငန်းစဉ် အောင်မြင်စွာ ပြီးဆုံးပါပြီ။ အားပေးမှုကို ကျေးဇူးတင်ပါသည်။ နောက်တစ်ကြိမ် ပြန်လည်ဝယ်ယူလိုပါက /start ကို နှိပ်ပေးပါ။")
    await q.edit_message_text("အော်ဒါ ပြီးမြောက်ကြောင်း အောင်မြင်စွာ ပို့လိုက်ပါပြီ။")

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    app.add_handler(CallbackQueryHandler(id_confirm, pattern="^idconf\\|"))
    app.add_handler(CallbackQueryHandler(ign_callback, pattern="^ign\\|"))
    app.add_handler(CallbackQueryHandler(admin_server, pattern="^admsrv\\|"))
    app.add_handler(CallbackQueryHandler(amount_confirm, pattern="^amtconf\\|"))
    app.add_handler(CallbackQueryHandler(payment_action, pattern="^pay\\|"))
    app.add_handler(CallbackQueryHandler(finish_order, pattern="^finish\\|"))

    PORT = int(os.getenv("PORT", "8000"))
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

    if RENDER_URL:
        print(f"RUNNING BOT VIA WEBHOOK ON PORT {PORT}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{RENDER_URL}/{BOT_TOKEN}"
        )
    else:
        print("RUNNING BOT VIA POLLING (LOCAL SETUP)")
        app.run_polling()

if __name__ == "__main__":
    main()
