import telebot
from telebot import types
import sqlite3
import datetime
import random
import string

BOT_TOKEN = "8858666249:AAFwB3KahSzk4HRyx3ez1Xh4anYmfYFyl8s"
ADMIN_ID = 8514199623
CREDIT_LIMIT = 50000

bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect("wifi_system.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS agents (telegram_id INTEGER PRIMARY KEY, name TEXT, debt INTEGER DEFAULT 0, status TEXT DEFAULT 'active')''')
cursor.execute('''CREATE TABLE IF NOT EXISTS vouchers (id INTEGER PRIMARY KEY AUTOINCREMENT, package_type TEXT, code TEXT UNIQUE, status TEXT DEFAULT 'available')''')
cursor.execute('''CREATE TABLE IF NOT EXISTS sales_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id INTEGER, agent_name TEXT, package_type TEXT, price INTEGER, code TEXT, issue_time TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS unlock_codes (code TEXT PRIMARY KEY, agent_id INTEGER, is_used INTEGER DEFAULT 0)''')
conn.commit()

NORMAL_PACKAGES = {"1GB": 400, "2GB": 800, "3GB": 1200, "4GB": 1600, "5GB": 2000, "6GB": 2400, "7GB": 2800, "8GB": 3200, "9GB": 3600, "10GB": 4000}
VIP_PACKAGES = {"VIP 2GB": 2000, "VIP 4GB": 4000, "VIP 8GB": 8000, "VIP 10GB": 10000, "VIP 12GB": 12000, "VIP 15GB": 15000}

def generate_random_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if user_id == ADMIN_ID:
        markup.add("📦 စတော့ထည့်မည်", "👥 Agent များစာရင်း")
        markup.add("🔓 Agent Unlock ပေးမည်", "📊 ၁ လစာ စာရင်းစစ်ရန်")
        markup.add("🧹 ၁ လကျော် ကုဒ်ဟောင်းရှင်းမည်", "❌ Agent ထုတ်မည်")
    markup.add("📶 Normal Package", "⭐ VIP Package")
    markup.add("💰 လက်ကျန် အကြွေးစာရင်း", "🔑 Unlock Code ထည့်မည်")
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    cursor.execute("SELECT name, debt, status FROM agents WHERE telegram_id = ?", (uid,))
    row = cursor.fetchone()
    if uid == ADMIN_ID:
        bot.send_message(uid, "👑 မင်္ဂလာပါ Admin! စနစ်အား စီမံခန့်ခွဲနိုင်ပါပြီ။", reply_markup=get_main_keyboard(uid))
        return
    if not row:
        bot.send_message(uid, f"❌ သင်သည် စနစ်တွင် မှတ်ပုံမတင်ရသေးပါ။\nသင့် Telegram ID: `{uid}` ကို Admin ထံ ပေးပို့၍ ခွင့်ပြုချက်တောင်းပါ။", parse_mode="Markdown")
        return
    name, debt, status = row
    if status == 'blocked':
        bot.send_message(uid, "🚫 သင့်အကောင့်အား ရပ်ဆိုင်းထားပါသည်။ Admin ထံ ဆက်သွယ်ပါ။")
        return
    bot.send_message(uid, f"👋 မင်္ဂလာပါ {name}!\nလက်ရှိ အကြွေး

 
