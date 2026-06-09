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

STATE_IDLE = "IDLE"
STATE_GET_ID = "GET_ID"
STATE_GET_SERVER = "GET_SERVER"
STATE_GET_AMOUNT = "GET_AMOUNT"
STATE_CONFIRM = "CONFIRM"
STATE_WAIT_PAYMENT = "WAIT_PAYMENT"

KBZPAY = "09401878226"
WAVEPAY = "09788599697"

SHOP_TZ = pytz.timezone("Asia/Yangon")

# ================= SHOP TIME =================

def shop_open():
    now_mm = datetime.now(SHOP_TZ)
    minutes = now_mm.hour * 60 + now_mm.minute
    return 11 * 60 <= minutes <= 19 * 60 + 30


# ================= PRICE LISTS =================

PRICE_TEXT_MYANMAR = """💎 MYANMAR SERVER ဈေးနှုန်းများ

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

PRICE_TEXT_SINGAPORE = """💎 SINGAPORE SERVER ဈေးနှုန်းများ

❗️Minimum order = 55 💎

💎55 = 7,750 MMK
💎86 = 8,250 MMK
💎165 = 17,250 MMK
💎172 = 17,950 MMK
💎257 = 25,250 MMK
💎275 = 26,750 MMK
💎343 = 32,950 MMK
💎565 = 51,750 MMK
💎706 = 63,950 MMK
💎2195 = 191,950 MMK
💎3688 = 320,250 MMK
💎5532 = 478,850 MMK
💎9288 = 801,950 MMK

🎟 Weekly Pass 1 = 9,450 MMK
🎟 Weekly Pass 2 = 16,000 MMK
🎟 Weekly Pass 3 = 22,550 MMK
🎟 Twilight Pass = 37,950 MMK
"""

# --- MYANMAR SERVER PRICING ---
MYANMAR_BASE_PRICES = {
    55: 4850, 86: 5350, 165: 14350, 172: 15050,
    257: 22350, 275: 23850, 343: 30050,
    565: 48850, 706: 61050, 2195: 189050,
    3688: 317350, 5532: 475950, 9288: 799050
}
MYANMAR_PASS_PRICES = {
    "weekly1": 6550, "weekly2": 13100, "weekly3": 19650, "twilight": 35050
}

# --- SINGAPORE SERVER PRICING ---
SINGAPORE_BASE_PRICES = {
    55: 7750, 86: 8250, 165: 17250, 172: 17950,
    257: 25250, 275: 26750, 343: 32950,
    565: 51750, 706: 63950, 2195: 191950,
    3688: 320250, 5532: 478850, 9288: 801950
}
SINGAPORE_PASS_PRICES = {
    "weekly1": 9450, "weekly2": 16000, "weekly3": 22550, "twilight": 37950
}

user_data = {}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {"state": STATE_IDLE}
    return user_data[uid]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not shop_open():
        await update.message.reply_text("🔒 ဆိုင်ပိတ်နေပါပြီ။\n🕒 ဆိုင်ဖွင့်ချိန်ကတော့ မနက် ၁၁ နာရီကနေ ည ၇ခွဲ ဖြစ်ပါတယ်။")
        return

    uid = update.effective_chat.id
    user_data[uid] = {"state": STATE_GET_ID}

    await update.message.reply_text(
        "👋 မင်္ဂလာပါ!\n🎮 Pepe's Diamond Shop မှ ကြိုဆိုပါတယ်နော်။\n\n"
        "📌 Diamond ထည့်ပေးရမယ့် Game ID ပို့ပေးပါ။\n👉 ဥပမာ - Pepe 1600113465 (16740)"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_chat.id
    data = get_user(uid)
    current_state = data.get("state", STATE_IDLE)

    # 1. ID လက်ခံခြင်း အဆင့်
    if current_state == STATE_GET_ID:
        if not update.message.text:
            return
        data["id"] = update.message.text
        data["state"] = STATE_GET_SERVER

        keyboard = [
            [InlineKeyboardButton("🇲🇲 MYANMAR", callback_data=f"MYANMAR_{uid}")],
            [InlineKeyboardButton("🇸🇬 SINGAPORE", callback_data=f"SINGAPORE_{uid}")],
            [InlineKeyboardButton("🚫 BAN", callback_data=f"BAN_{uid}")]
        ]

        await context.bot.send_message(
            ADMIN_ID,
            f"🔍 ID အသစ် စစ်ဆေးရန်\n{update.message.text}\nUSER ID: {uid}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text("⏳ Admin ဘက်က ID စစ်ပေးနေလို့ ခေတ္တစောင့်ဆိုင်းပေးပါနော်...")
        return

    # 2. ပမာဏ လက်ခံခြင်း အဆင့် (STATE_GET_AMOUNT)
    elif current_state == STATE_GET_AMOUNT:
        if not update.message.text:
            return
        text = update.message.text.lower().strip().replace(" ", "")

        if "server" not in data:
            await update.message.reply_text("❌ သင့် server ကိုရှာမတွေ့ပါ /start ကို ပြန်နှိပ်ပေးပါ။")
            data["state"] = STATE_IDLE
            return

        # Pass အမျိုးအစားများကို သတ်မှတ်ချက်အတိုင်း စစ်ဆေးခြင်း
        if text in ["wp1", "weeklypass1", "weekly1", "wp 1", "wp_1"]:
            value = "weekly1"
        elif text in ["wp2", "weeklypass2", "weekly2", "wp 2", "wp_2"]:
            value = "weekly2"
        elif text in ["wp3", "weeklypass3", "weekly3", "wp 3", "wp_3"]:
            value = "weekly3"
        elif text in ["twi", "twilight", "twilightpass"]:
            value = "twilight"
        else:
            try:
                value = int(text)
            except:
                value = text

        price = None
        server_choice = data["server"]

        # ဆာဗာအလိုက် သီးသန့်ခွဲထုတ်ထားသော ဈေးနှုန်း List ထဲကနေ တိုက်ရိုက်ဆွဲယူခြင်း
        if server_choice == "SINGAPORE":
            if isinstance(value, int) and value in SINGAPORE_BASE_PRICES:
                price = SINGAPORE_BASE_PRICES[value]
            elif isinstance(value, str) and value in SINGAPORE_PASS_PRICES:
                price = SINGAPORE_PASS_PRICES[value]
        else: # MYANMAR
            if isinstance(value, int) and value in MYANMAR_BASE_PRICES:
                price = MYANMAR_BASE_PRICES[value]
            elif isinstance(value, str) and value in MYANMAR_PASS_PRICES:
                price = MYANMAR_PASS_PRICES[value]

        if price is None:
            await update.message.reply_text("❌ ဝယ်ယူလိုတဲ့ ပမာဏ သို့မဟုတ် အမျိုးအစား မှားယွင်းနေလို့ သေချာပြန်ရိုက်ပေးပါနော်။")
            return

        display_item = value
        if value == "weekly1":
            display_item = "Weekly Pass 1"
        elif value == "weekly2":
            display_item = "Weekly Pass 2"
        elif value == "weekly3":
            display_item = "Weekly Pass 3"
        elif value == "twilight":
            display_item = "Twilight Pass"
        else:
            display_item = f"{value} Diamond"

        data["amount"] = value
        data["price"] = price
        data["state"] = STATE_CONFIRM

        await update.message.reply_text(
            f"🔍 အော်ဒါအချက်အလက်ကို ပြန်စစ်ပေးပါ။\n\n"
            f"• ရွေးချယ်ထားသော ဆာဗာ: {server_choice}\n"
            f"• ဝယ်ယူမည့်အမျိုးအစား: {display_item}\n"
            f"• ကျသင့်ငွေ: {price:,} MMK\n\n"
            f"👉 အတည်ပြုပြီး ဝယ်ယူမယ်ဆိုရင် YES ဟု စာလုံးကြီးဖြင့် ရိုက်ပို့ပေးပါနော်။"
        )
        return

    # 3. အော်ဒါ အတည်ပြုခြင်း အဆင့် (STATE_CONFIRM)
    elif current_state == STATE_CONFIRM:
        if not update.message.text:
            return
        
        if update.message.text.upper() != "YES":
            data["state"] = STATE_GET_AMOUNT
            await update.message.reply_text(
                "❌ အော်ဒါကို အတည်မပြုခဲ့ပါဘူး။\n"
                "ဝယ်ယူလိုတဲ့ Diamond ပမာဏ သို့မဟုတ် အမျိုးအစားကို ပြန်လည်ရိုက်ထည့်ပေးပါနော်။\n\n"
                "💡 [သတိပြုရန်]\n"
                "Weekly Pass အတွက် wp 1, wp 2, wp 3 ဟု ရိုက်ပေးပါ။\n"
                "Twilight Pass အတွက် twi ဟု ရိုက်ပေးပါ။"
            )
            return

        data["state"] = STATE_WAIT_PAYMENT
        await update.message.reply_text(
            f"💳 Ngwe pay jya r m_al a-kaut a-chat a-lak myar\n\n"
            f"• KBZPay: {KBZPAY}\n"
            f"• WavePay: {WAVEPAY}\n\n"
            f"📸 Ngwe hlwel pee thwar yin phat pine (Screenshot) lay ko de ma pot pay khat par naw."
        )
        return

    # 4. Ngwe lhwl sawnt hsaing jin
    elif current_state == STATE_WAIT_PAYMENT:
        if not update.message.photo:
            await update.message.reply_text("❌ Ngwe hlwel phat pine Screenshot pone pot pay ya mal. Pone lay pyan pot pay par.")
            return

        keyboard = [
            [InlineKeyboardButton("✅ ACCEPT", callback_data=f"acc_{uid}")],
            [InlineKeyboardButton("❌ REJECT", callback_data=f"rej_{uid}")]
        ]

        await context.bot.send_message(
            ADMIN_ID,
            f"💰 Ngwe hlwel phat pine a thit\nUSER ID: {uid}\nID: {data.get('id')}\nServer: {data.get('server')}\nပမာဏ: {data.get('amount')}\nကျသင့်ငွေ: {data.get('price'):,} MMK",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await context.bot.forward_message(ADMIN_ID, uid, update.message.message_id)
        await update.message.reply_text("✨ Ngwe hlwel phat pine lak khan ya she par pre.\nAdmin ka sit say pee tar nae Diamond chat chin htal thwin pay thwar mar mo khatt saung pay par naw.")
        
        data["state"] = STATE_IDLE
        return


# ================= SERVER CALLBACK (ADMIN ACTION) =================

async def server_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("_")
    uid = int(uid)

    data = get_user(uid)

    if action == "BAN":
        await context.bot.send_message(uid, "❌ Ban server ဖြစ်လို့ အော်ဒါကို ငြင်းပယ်ထားပါတယ်။")
        data["state"] = STATE_IDLE
        return

    data["server"] = action
    data["state"] = STATE_GET_AMOUNT

    # ဆာဗာအလိုက် သီးသန့်ခွဲထားတဲ့ ဈေးနှုန်း Text ကို ထုတ်ပြပေးခြင်း
    price_text_to_show = PRICE_TEXT_SINGAPORE if action == "SINGAPORE" else PRICE_TEXT_MYANMAR

    await context.bot.send_message(
        uid,
        f"🎯 ရွေးချယ်ထားသော ဆာဗာ: {action}\n\n"
        f"{price_text_to_show}\n"
        f"👉 ဝယ်ယူလိုသည့် ပမာဏကို ရိုက်ထည့်ပေးပါ။\n\n"
        f"💡 [သတိပြုရန်]\n"
        f"Weekly Pass ဝယ်ယူလိုပါက wp 1, wp 2, wp 3 ဟု ရိုက်ထည့်ပေးပါ။\n"
        f"Twilight Pass ဝယ်ယူလိုပါက twi ဟု ရိုက်ထည့်ပေးပါ။"
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
        f"User {uid} အော်ဒါကို လက်ခံလိုက်ပါပြီ။",
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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(server_buttons, pattern="^(MYANMAR|SINGAPORE|BAN)_"))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^(acc|rej)_"))
    app.add_handler(CallbackQueryHandler(finish, pattern="^fin_"))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    print("BOT RUNNING 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
