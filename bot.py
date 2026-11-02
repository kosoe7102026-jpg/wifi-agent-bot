import telebot
from telebot import types
import sqlite3

BOT_TOKEN = "8858666249:AAFwB3KahSzk4HRyx3ez1Xh4anYmfYFyl8s"
ADMIN_ID = 8514199623
CREDIT_LIMIT = 50000

bot = telebot.TeleBot(BOT_TOKEN)

# --- Database Setup ---
conn = sqlite3.connect("wifi_system.db", check_same_thread=False)
cursor = conn.cursor()

# Reseller Agents Table
cursor.execute('''CREATE TABLE IF NOT EXISTS agents (
    agent_id INTEGER PRIMARY KEY,
    name TEXT,
    phone TEXT,
    balance INTEGER DEFAULT 0,
    credit_limit INTEGER DEFAULT 50000,
    status TEXT DEFAULT 'pending'
)''')

# Wi-Fi Packages Table
cursor.execute('''CREATE TABLE IF NOT EXISTS packages (
    package_name TEXT PRIMARY KEY,
    price INTEGER
)''')

# Initial Default Prices
default_packages = [
    ("1GB", 400),
    ("2GB", 800),
    ("3GB", 1200),
    ("4GB", 1600),
    ("5GB", 2000),
    ("6GB", 2000),
    ("7GB", 2800),
    ("8GB", 3200),
    ("9GB", 3600),
    ("10GB", 4000)
]
cursor.executemany("INSERT OR IGNORE INTO packages VALUES (?, ?)", default_packages)
conn.commit()


# --- Admin Commands ---

@bot.message_handler(commands=['prices'])
def view_prices(message):
    if message.chat.id != ADMIN_ID:
        return
    cursor.execute("SELECT package_name, price FROM packages")
    rows = cursor.fetchall()
    text = "📶 လက်ရှိ Wi-Fi ဈေးနှုန်းများ -\n\n"
    for row in rows:
        text += f"🔹 {row[0]} = {row[1]} MMK\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['setprice'])
def set_price(message):
    if message.chat.id != ADMIN_ID:
        return
    # ပုံစံ: /setprice 1GB 400
    try:
        parts = message.text.split()
        pkg_name = parts[1].upper()
        new_price = int(parts[2])
        cursor.execute("INSERT OR REPLACE INTO packages (package_name, price) VALUES (?, ?)", (pkg_name, new_price))
        conn.commit()
        bot.reply_to(message, f"✅ {pkg_name} ဈေးနှုန်းကို {new_price} MMK သို့ ပြောင်းလဲသတ်မှတ်ပြီးပါပြီ။")
    except Exception:
        bot.reply_to(message, "⚠️ ပုံစံမှားယွင်းနေပါသည်။\nဥပမာ - `/setprice 1GB 400` ဟု ရိုက်ပို့ပါ။")


# --- User & Agent Commands ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    cursor.execute("SELECT status FROM agents WHERE agent_id = ?", (user_id,))
    agent = cursor.fetchone()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if agent and agent[0] == 'approved':
        markup.add("🎟 Voucher ဝယ်ယူရန်", "💰 လက်ကျန်ငွေစစ်ရန်")
        markup.add("📋 ဈေးနှုန်းစာရင်းကြည့်ရန်")
        bot.send_message(user_id, "မင်္ဂလာပါ Reseller Agent ကြီးခင်ဗျာ။ စနစ်ကို အသုံးပြုနိုင်ပါပြီ။", reply_markup=markup)
    else:
        markup.add("📝 Agent လျှောက်ထားရန်", "📋 ဈေးနှုန်းစာရင်းကြည့်ရန်")
        bot.send_message(user_id, "Reyee Wi-Fi Agent System မှ ကြိုဆိုပါသည်။", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "📋 ဈေးနှုန်းစာရင်းကြည့်ရန်")
def show_pricing(message):
    cursor.execute("SELECT package_name, price FROM packages")
    rows = cursor.fetchall()
    text = "📶 Wi-Fi Package ဈေးနှုန်းများ -\n\n"
    for row in rows:
        text += f"🔹 {row[0]} - {row[1]} MMK\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda msg: msg.text == "📝 Agent လျှောက်ထားရန်")
def register_prompt(message):
    bot.send_message(message.chat.id, "Agent အဖြစ် လျှောက်ထားရန် သင်၏ အမည်နှင့် ဖုန်းနံပါတ်ကို အောက်ပါအတိုင်း ပေးပို့ပေးပါ -\n\nဥပမာ: `Agent Ko Soe - 09123456789`")

@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("Agent "))
def handle_agent_registration(message):
    user_id = message.chat.id
    details = message.text.replace("Agent ", "").strip()
    cursor.execute("INSERT OR REPLACE INTO agents (agent_id, name, phone, status) VALUES (?, ?, ?, 'pending')", 
                   (user_id, details, details))
    conn.commit()

    bot.reply_to(message, "✅ Agent လျှောက်ထားလွှာ ပေးပို့ပြီးပါပြီ။ Admin ဘက်မှ အတည်ပြုပြီးပါက အကြောင်းကြားပေးပါမည်။")

    # Admin ထံ အသိပေးချက်ပို့ခြင်း
    admin_markup = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton("အတည်ပြုမည်", callback_data=f"approve_{user_id}")
    admin_markup.add(approve_btn)
    bot.send_message(ADMIN_ID, f"🔔 Agent အသစ် လျှောက်ထားလာပါသည် -\nID: {user_id}\nအချက်အလက်: {details}", reply_markup=admin_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_agent(call):
    if call.message.chat.id != ADMIN_ID:
        return
    agent_id = int(call.data.split("_")[1])
    cursor.execute("UPDATE agents SET status = 'approved' WHERE agent_id = ?", (agent_id,))
    conn.commit()

    bot.send_message(agent_id, "🎉 သင်၏ Reseller Agent အကောင့်ကို Admin မှ အတည်ပြုလိုက်ပါပြီ။ /start ကို ပြန်နှိပ်၍ စတင်သုံးနိုင်ပါပြီ။")
    bot.edit_message_text(f"✅ Agent ID {agent_id} ကို အတည်ပြုပြီးပါပြီ။", call.message.chat.id, call.message.id)

print("Bot is starting...")
bot.infinity_polling()
