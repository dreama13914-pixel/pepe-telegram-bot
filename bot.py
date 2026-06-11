import os
import json
from datetime import datetime
import pytz
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)

# ================= CONFIG =================

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))  # Render automatically provides this port

STATE_GET_ID = "GET_ID"
STATE_GET_AMOUNT = "GET_AMOUNT"
STATE_CONFIRM = "CONFIRM"
STATE_WAIT_PAYMENT = "WAIT_PAYMENT"

KBZPAY = "09401878226"
WAVEPAY = "09788599697"

user_data = {}
STATUS_FILE = "server_status.txt"


# ================= FREE TIER WEB SERVER KEEP-ALIVE =================

class HealthCheckServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive and running safely on free tier!")

def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthCheckServer)
    print(f"Health check server listening on port {PORT}...")
    server.serve_forever()


# ================= SHOP OPENING HOURS CHECK =================

def is_shop_open():
    tz = pytz.timezone('Asia/Yangon')
    now = datetime.now(tz).time()
    
    start_time = datetime.strptime("11:00", "%H:%M").time()
    end_time = datetime.strptime("19:30", "%H:%M").time()
    
    return start_time <= now <= end_time


# ================= SERVER STATUS PERSISTENCE =================

def load_server_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "MYANMAR": True,
        "SINGAPORE": True,
        "MALAYSIA": True,
        "PHILIPPINES": True,
        "INDONESIA": True
    }

def save_server_status(status_dict):
    with open(STATUS_FILE, "w") as f:
        json.dump(status_dict, f)

server_status = load_server_status()

SERVER_FLAGS = {
    "MYANMAR": "🇲🇲",
    "SINGAPORE": "🇸🇬",
    "MALAYSIA": "🇲🇾",
    "PHILIPPINES": "🇵🇭",
    "INDONESIA": "🇮🇩"
}

# ================= BASE MYANMAR PRICES =================

MYANMAR_BASE = {
    55: 4850, 86: 5350, 165: 14350, 172: 15050, 257: 22350,
    275: 23850, 343: 30050, 565: 48850, 706: 61050,
    2195: 189050, 3688: 317350, 5532: 475950, 9288: 799050
}

# Key strings updated to handle short-codes (wp1, wp2, wp3, twi)
MYANMAR_PASS = {
    "wp1": 6550, "wp2": 13100, "wp3": 19650, "twi": 35050
}

# ================= SERVER RULES =================

def calc_price(server, item):
    base = MYANMAR_BASE.get(item) if isinstance(item, int) else MYANMAR_PASS.get(item)
    if base is None: return None

    if server == "MYANMAR": return base
    elif server in ["SINGAPORE", "MALAYSIA"]: return base - 300
    elif server == "PHILIPPINES": return base + 450
    elif server == "INDONESIA": return base + 270
    return None


# ================= RESTORED PRICE TEXTS =================

PRICE_MYANMAR = """🇲🇲 MYANMAR SERVER ဈေးနှုန်းများ

❗️Minimum order = 55 💎

💎 55 = 4,850 MMK
💎 86 = 5,350 MMK
💎 165 = 14,350 MMK
💎 172 = 15,050 MMK
💎 257 = 22,350 MMK
💎 275 = 23,850 MMK
💎 343 = 30,050 MMK
💎 565 = 48,850 MMK
💎 706 = 61,050 MMK
💎 2195 = 189,050 MMK
💎 3688 = 317,350 MMK
💎 5532 = 475,950 MMK
💎 9288 = 799,050 MMK

🎟 Weekly Pass 1 = 6,550 MMK (ရိုက်ရန်ပုံစံ - wp1)
🎟 Weekly Pass 2 = 13,100 MMK (ရိုက်ရန်ပုံစံ - wp2)
🎟 Weekly Pass 3 = 19,650 MMK (ရိုက်ရန်ပုံစံ - wp3)
🎟 Twilight Pass = 35,050 MMK (ရိုက်ရန်ပုံစံ - twi)"""

PRICE_SG = """🇸🇬 🇲🇾 SINGAPORE / MALAYSIA SERVER ဈေးနှုန်းများ

❗️Minimum order = 55 💎

💎 55 = 4,550 MMK
💎 86 = 5,050 MMK
💎 165 = 14,050 MMK
💎 172 = 14,750 MMK
💎 257 = 22,050 MMK
💎 275 = 23,550 MMK
💎 343 = 29,750 MMK
💎 565 = 48,550 MMK
💎 706 = 60,750 MMK
💎 2195 = 188,750 MMK
💎 3688 = 316,950 MMK
💎 5532 = 475,650 MMK
💎 9288 = 798,750 MMK"""

PRICE_PH = """🇵🇭 PHILIPPINES SERVER ဈေးနှုန်းများ

💎 55 = 5,300 MMK
💎 86 = 5,800 MMK
💎 165 = 14,800 MMK
💎 172 = 15,500 MMK
💎 257 = 22,800 MMK
💎 275 = 24,300 MMK
💎 343 = 30,500 MMK
💎 565 = 49,300 MMK
💎 706 = 61,500 MMK
💎 2195 = 189,500 MMK
💎 3688 = 317,800 MMK
💎 5532 = 476,400 MMK
💎 9288 = 799,500 MMK"""

PRICE_ID = """🇮🇩 INDONESIA SERVER ဈေးနှုန်းများ

💎 55 = 5,120 MMK
💎 86 = 5,620 MMK
💎 165 = 14,620 MMK
💎 172 = 15,320 MMK
💎 257 = 22,620 MMK
💎 275 = 24,120 MMK
💎 343 = 30,320 MMK
💎 565 = 49,120 MMK
💎 706 = 61,320 MMK
💎 2195 = 189,320 MMK
💎 3688 = 317,620 MMK
💎 5532 = 476,220 MMK
💎 9288 = 799,320 MMK"""


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    if not is_shop_open():
        await update.message.reply_text("အခုက ဆိုင်ပိတ်ချိန်ဖြစ်လို့ ဆိုင်ဖွင့်ချိန် (11:00 AM - 7:30 PM) ထဲမှာပဲ ပြန်အော်ဒါတင်ပေးပါ။")
        return

    user_data[uid] = {"state": STATE_GET_ID}
    
    welcome_text = (
        "🐸 Welcome to Pepe's MLBB Diamond Shop!\n\n"
        "ဝယ်ယူဖို့အတွက် Game ID နဲ့ Zone ID ကို ရိုက်ထည့်ပေးပါ။\n"
        "ဥပမာ - 123456789 (1234)"
    )
    await update.message.reply_text(welcome_text)

# ================= MESSAGE =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    text = update.message.text.strip()

    if not is_shop_open():
        await update.message.reply_text("အခုက ဆိုင်ပိတ်ချိန်ဖြစ်လို့ ဆိုင်ဖွင့်ချိန် (11:00 AM - 7:30 PM) ထဲမှာပဲ ပြန်အော်ဒါတင်ပေးပါ။")
        return

    if uid not in user_data: user_data[uid] = {}
    state = user_data[uid].get("state")

    if state == STATE_GET_ID:
        user_data[uid]["id"] = text
        user_data[uid]["state"] = STATE_GET_AMOUNT
        
        full_price_sheet = (
            f"{PRICE_MYANMAR}\n\n"
            f"{PRICE_SG}\n\n"
            f"{PRICE_PH}\n\n"
            f"{PRICE_ID}\n\n"
            "အထက်ပါဈေးနှုန်းတွေကို ကြည့်ပြီး လိုချင်တဲ့ ပမာဏ (Amount) ဒါမှမဟုတ် Pass အတိုကောက် ကုဒ်တွေကို ရိုက်ထည့်ပေးပါ။\n"
            "ဥပမာ - 55 သို့မဟုတ် wp1"
        )
        await update.message.reply_text(full_price_sheet)
        return

    if state == STATE_GET_AMOUNT:
        try: item = int(text)
        except: item = text.lower()  # Converts 'WP1' or 'TWI' cleanly to lowercase maps

        chosen_server = None
        for srv in ["MYANMAR", "SINGAPORE", "MALAYSIA", "PHILIPPINES", "INDONESIA"]:
            if server_status.get(srv, True):
                chosen_server = srv
                break
        
        if not chosen_server:
            await update.message.reply_text("လက်ရှိမှာ Server အားလုံး Ban ဖြစ်နေလို့ Diamond ဝယ်လို့မရသေးပါ။")
            return

        price = calc_price(chosen_server, item)
        if price is None:
            await update.message.reply_text("ရိုက်ထည့်ထားတဲ့ ပမာဏ မမှန်ပါ။ သေချာပြန်စစ်ပြီး ရိုက်ပေးပါ။")
            return

        # Human presentation naming logic for receipts
        display_item = item
        if item == "wp1": display_item = "Weekly Pass 1"
        elif item == "wp2": display_item = "Weekly Pass 2"
        elif item == "wp3": display_item = "Weekly Pass 3"
        elif item == "twi": display_item = "Twilight Pass"

        user_data[uid]["server"] = chosen_server
        user_data[uid]["item"] = display_item
        user_data[uid]["raw_item"] = item
        user_data[uid]["price"] = price
        user_data[uid]["state"] = STATE_CONFIRM
        await update.message.reply_text(f"🛒 အော်ဒါအချက်အလက်တွေကို အတည်ပြုပေးပါ\n\nID: {user_data[uid]['id']}\nItem: {display_item}\nPrice: {price:,} MMK\n\nဝယ်ယူမှုကို အတည်ပြုရင် 'YES' လို့ ရိုက်ထည့်ပေးပါ။")
        return

    if state == STATE_CONFIRM:
        if text.lower() != "yes":
            await update.message.reply_text("'YES' တစ်မျိုးတည်းပဲ ရိုက်ထည့်ပေးဖို့ လိုအပ်ပါတယ်။")
            return

        server = user_data[uid].get("server")
        if not server_status.get(server, True):
            await update.message.reply_text("လက်ရှိမှာ Server Ban ဖြစ်သွားလို့ Diamond ဝယ်လို့မရတော့ပါ။ အော်ဒါကို ခေတ္တပယ်ဖျက်လိုက်ပါတယ်။")
            return

        user_data[uid]["state"] = STATE_WAIT_PAYMENT
        await update.message.reply_text(f"💳 အောက်ပါအကောင့်တွေထဲကို Ngwe လွှဲပေးပါ\n\nKBZPay: {KBZPAY}\nWavePay: {WAVEPAY}\n\nငွေလွှဲပြီးရင် ငွေလွှဲပြေစာ (Screenshot) ကို ပို့ပေးပါ။")

# ================= PAYMENT PROCESSING =================

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    if not is_shop_open():
        await update.message.reply_text("အခုက ဆိုင်ပိတ်ချိန်ဖြစ်လို့ ဆိုင်ဖွင့်ချိန် (11:00 AM - 7:30 PM) ထဲမှာပဲ ပြန်အော်ဒါတင်ပေးပါ။")
        return

    u_info = user_data.get(uid, {})
    g_id = u_info.get("id", "Unknown")
    server = u_info.get("server", "Unknown")
    item = u_info.get("item", "Unknown")
    price = u_info.get("price", 0)

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"📩 **NEW PAYMENT RECEIVED**\n\n👤 User Chat ID: `{uid}`\n🎮 Game ID: `{g_id}`\n🌐 Server: {server}\n💎 Item: {item}\n💰 Price: {price:,} MMK",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ACCEPT", callback_data=f"acc|{uid}")], [InlineKeyboardButton("❌ REJECT", callback_data=f"rej|{uid}")]])
    )
    await update.message.reply_text("ငွေလွှဲပြေစာ ရပါပြီ။ Admin ဘက်က စစ်ဆေးနေလို့ ခဏတော့ စောင့်ပေးပါ။")

# ================= ADMIN ACTIONS =================

async def admin_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("|")
    uid = int(uid)

    if action == "rej":
        await context.bot.send_message(uid, "ငွေဝင်မလာသေးလို့ Admin ဘက်က Diamond ထည့်ပေးလို့မရပါ။ Ngwe လွှဲတာ ပြန်စစ်ပြီး Admin ဆီ တိုက်ရိုက် ဆက်သွယ်ပေးပါ။")
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ [REJECTED BY ADMIN]")
        return

    await context.bot.send_message(uid, "ငွေလွှဲတာ လက်ခံရရှိပါပြီ။ Diamond တွေကို အကောင့်ထဲ ချက်ချင်း ထည့်ပေးနေပြီမို့ ခဏပဲ စောင့်ပေးပါ။")
    await query.edit_message_caption(caption=query.message.caption + "\n\n✅ [ACCEPTED BY ADMIN]")

# ================= ADMIN SERVER BAN CONTROL =================

async def server_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID: return
    keyboard = [[InlineKeyboardButton(f"{SERVER_FLAGS.get(srv, '🌐')} {srv}: {'🟢 Live' if act else '🔴 BANNED'}", callback_data=f"toggle|{srv}")] for srv, act in server_status.items()]
    await update.message.reply_text("🛠 **Server Status & Ban Manager**", reply_markup=InlineKeyboardMarkup(keyboard))

async def toggle_server_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("ခွင့်ပြုချက်မရှိပါ။", show_alert=True)
        return

    await query.answer()
    _, server = query.data.split("|")
    server_status[server] = not server_status.get(server, True)
    save_server_status(server_status)
    keyboard = [[InlineKeyboardButton(f"{SERVER_FLAGS.get(srv, '🌐')} {srv}: {'🟢 Live' if act else '🔴 BANNED'}", callback_data=f"toggle|{srv}")] for srv, act in server_status.items()]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


# ================= MAIN =================

def main():
    threading.Thread(target=run_health_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("server_status", server_status_cmd))
    app.add_handler(CallbackQueryHandler(admin_cb, pattern="^(acc|rej)\\|"))
    app.add_handler(CallbackQueryHandler(toggle_server_cb, pattern="toggle\\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, payment))

    print("BOT RUNNING 🚀")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
