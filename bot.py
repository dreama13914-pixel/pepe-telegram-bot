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
STATE_GET_SERVER = "GET_SERVER"
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

# ================= BASE MYANMAR PRICES =================

MYANMAR_BASE = {
    55: 4850, 86: 5350, 165: 14350, 172: 15050, 257: 22350,
    275: 23850, 343: 30050, 565: 48850, 706: 61050,
    2195: 189050, 3688: 317350, 5532: 475950, 9288: 799050
}

MYANMAR_PASS = {
    "weekly1": 6550, "weekly2": 13100, "weekly3": 19650, "twilight": 35050
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


# ================= PRICE TEXT =================

PRICE_MYANMAR = """💎 MYANMAR SERVER ဈေးနှုန်းများ

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

🎟 Weekly Pass 1 = 6,550 MMK
🎟 Weekly Pass 2 = 13,100 MMK
🎟 Weekly Pass 3 = 19,650 MMK
🎟 Twilight Pass = 35,050 MMK"""

PRICE_SG = """💎 SINGAPORE / MALAYSIA SERVER ဈေးနှုန်းများ

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

PRICE_PH = """💎 PHILIPPINES SERVER ဈေးနှုန်းများ

💎 (Myanmar + 450 MMK)

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

PRICE_ID = """💎 INDONESIA SERVER ဈေးနှုန်းများ

💎 (Myanmar + 270 MMK)

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
        await update.message.reply_text("ယခုအချိန်သည် ဆိုင်ပိတ်ချိန် ဖြစ်ပါသည်။ ဆိုင်ဖွင့်ချိန် (11:00 AM - 7:30 PM) အတွင်း ပြန်လည်အော်ဒါတင်ပေးပါ။")
        return

    user_data[uid] = {"state": STATE_GET_ID}
    keyboard = [
        [InlineKeyboardButton("MYANMAR", callback_data="server|MYANMAR")],
        [InlineKeyboardButton("SINGAPORE", callback_data="server|SINGAPORE")],
        [InlineKeyboardButton("MALAYSIA", callback_data="server|MALAYSIA")],
        [InlineKeyboardButton("PHILIPPINES", callback_data="server|PHILIPPINES")],
        [InlineKeyboardButton("INDONESIA", callback_data="server|INDONESIA")]
    ]
    await update.message.reply_text("ကျေးဇူးပြု၍ Game ID ရိုက်ထည့်ပေးပါ။", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= MESSAGE =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    text = update.message.text.strip()

    if not is_shop_open():
        await update.message.reply_text("ယခုအချိန်သည် ဆိုင်ပိတ်ချိန် ဖြစ်ပါသည်။ ဆိုင်ဖွင့်ချိန် (11:00 AM - 7:30 PM) အတွင်း ပြလည်အော်ဒါတင်ပေးပါ။")
        return

    if uid not in user_data: user_data[uid] = {}
    state = user_data[uid].get("state")

    if state == STATE_GET_ID:
        user_data[uid]["id"] = text
        user_data[uid]["state"] = STATE_GET_SERVER
        await update.message.reply_text("ကျေးဇူးပြု၍ Server ကို ရွေးချယ်ပေးပါ။")
        return

    if state == STATE_GET_AMOUNT:
        try: item = int(text)
        except: item = text.lower()

        server = user_data[uid]["server"]
        if not server_status.get(server, True):
            await update.message.reply_text("Ban Server ဖြစ်နေသဖြင့် Diamond ဝယ်လို့မရပါ။")
            return

        price = calc_price(server, item)
        if price is None:
            await update.message.reply_text("ရိုက်ထည့်ထားသော ပမာဏ မမှန်ကန်ပါ။ ပြန်လည်စစ်ဆေးပေးပါ။")
            return

        user_data[uid]["item"] = item
        user_data[uid]["price"] = price
        user_data[uid]["state"] = STATE_CONFIRM
        await update.message.reply_text(f"🛒 အော်ဒါအချက်အလက်များကို အတည်ပြုပေးပါ\n\nItem: {item}\nPrice: {price:,} MMK\n\nဝယ်ယူမှုကို အတည်ပြုရန် 'YES' ဟု ရိုက်ထည့်ပေးပါ။")
        return

    if state == STATE_CONFIRM:
        if text.lower() != "yes":
            await update.message.reply_text("'YES' တစ်မျိုးတည်းသာ ရိုက်ထည့်ပေးရန် လိုအပ်ပါသည်။")
            return

        server = user_data[uid].get("server")
        if not server_status.get(server, True):
            await update.message.reply_text("Ban Server ဖြစ်နေသဖြင့် Diamond ဝယ်လို့မရပါ။")
            return

        user_data[uid]["state"] = STATE_WAIT_PAYMENT
        await update.message.reply_text(f"💳 ကျေးဇူးပြု၍ အောက်ပါအကောင့်များသို့ ငွေပေးချေမှု ပြုလုပ်ပေးပါ\n\nKBZPay: {KBZPAY}\nWavePay: {WAVEPAY}\n\nငွေလွှဲပြီးပါက Ngwe Lwe Sar (Screenshot) ကို ပို့ပေးပါ။")

# ================= SERVER SELECTION =================

async def server_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_shop_open():
        await query.message.reply_text("ယခုအချိန်သည် ဆိုင်ပိတ်ချိန် ဖြစ်ပါသည်။ ဆိုင်ဖွင့်ချိန် (11:00 AM - 7:30 PM) အတွင်း ပြန်လည်အော်ဒါတင်ပေးပါ။")
        return

    _, server = query.data.split("|")
    uid = query.from_user.id

    if not server_status.get(server, True):
        await query.message.reply_text("Ban Server ဖြစ်နေသဖြင့် Diamond ဝယ်လို့မရပါ။")
        return

    user_data[uid]["server"] = server
    user_data[uid]["state"] = STATE_GET_AMOUNT
    txt = PRICE_MYANMAR if server == "MYANMAR" else (PRICE_SG if server in ["SINGAPORE", "MALAYSIA"] else (PRICE_PH if server == "PHILIPPINES" else PRICE_ID))
    await query.message.reply_text(txt + "\n\nကျေးဇူးပြု၍ လိုချင်သော ပမာဏ (Amount) ကို ရိုက်ထည့်ပေးပါ။")

# ================= PAYMENT PROCESSING =================

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    if not is_shop_open():
        await update.message.reply_text("ယခုအချိန်သည် ဆိုင်ပိတ်ချိန် ဖြစ်ပါသည်။ ဆိုင်ဖွင့်ချိန် (11:00 AM - 7:30 PM) အတွင်း ပြန်လည်အော်ဒါတင်ပေးပါ။")
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
    await update.message.reply_text("ငွေလွှဲပြေစာ လက်ခံရရှိပါသည်။ Admin မှ စစ်ဆေးနေပါသဖြင့် ခေတ္တစောင့်ဆိုင်းပေးပါ။")

# ================= ADMIN ACTIONS =================

async def admin_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("|")
    uid = int(uid)

    if action == "rej":
        await context.bot.send_message(uid, "ငွေလွှဲပြေစာ စစ်ဆေးရတာ အဆင်မပြေလို့ အော်ဒါကို ခေတ္တပယ်ဖျက်ထားပါတယ်။ အချက်အလက်တွေ ပြန်စစ်ပြီး Admin ဆီ တိုက်ရိုက် ဆက်သွယ်ပေးပါ။")
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ [REJECTED BY ADMIN]")
        return

    await context.bot.send_message(uid, "ငွေလွှဲတာ လက်ခံရရှိပါပြီ။ Diamond တွေကို အကောင့်ထဲ အမြန်ဆုံး ထည့်သွင်းပေးနေပါပြီ။ ခေတ္တမျှ စောင့်ဆိုင်းပေးပါ။")
    await query.edit_message_caption(caption=query.message.caption + "\n\n✅ [ACCEPTED BY ADMIN]")

# ================= ADMIN SERVER BAN CONTROL =================

async def server_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID: return
    keyboard = [[InlineKeyboardButton(f"{srv}: {'🟢 Live' if act else '🔴 BANNED'}", callback_data=f"toggle|{srv}")] for srv, act in server_status.items()]
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
    keyboard = [[InlineKeyboardButton(f"{srv}: {'🟢 Live' if act else '🔴 BANNED'}", callback_data=f"toggle|{srv}")] for srv, act in server_status.items()]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


# ================= MAIN =================

def main():
    # 1. Start the free background dummy web server first
    threading.Thread(target=run_health_server, daemon=True).start()

    # 2. Start the normal Telegram Bot polling process
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("server_status", server_status_cmd))
    app.add_handler(CallbackQueryHandler(server_cb, pattern="server\\|"))
    app.add_handler(CallbackQueryHandler(admin_cb, pattern="^(acc|rej)\\|"))
    app.add_handler(CallbackQueryHandler(toggle_server_cb, pattern="toggle\\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, payment))

    print("BOT RUNNING 🚀")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
