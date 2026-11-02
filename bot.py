import telebot
from telebot import types
import sqlite3

BOT_TOKEN = "8858666249:AAFwB3KahSzk4HRy"
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
    balance INTEGER DEFAULT 0,
    credit_limit INTEGER DEFAULT 50000
)''')

# Wi-Fi Packages Table (Dynamic Pricing)
cursor.execute('''CREATE TABLE IF NOT EXISTS packages (
    gb INTEGER PRIMARY KEY,
    price INTEGER
)''')

# Initial Default Packages Setup
default_packages = [
    (1, 400), (2, 800), (3, 1200), (4, 1600), (5, 2000),
    (6, 2400), (7, 2800), (8, 3200), (9, 3600), (10, 4000)
]
cursor.executemany('''INSERT OR IGNORE INTO packages (gb, price) VALUES (?, ?)''', default_packages)
conn.commit()

# --- Helper Functions ---
def get_packages():
    """Database ထဲမှ လက်ရှိ Package ဈေးနှုန်းများကို ဆွဲထုတ်ခြင်း"""
    cursor.execute("SELECT gb, price FROM packages ORDER BY gb ASC")
    return cursor.fetchall()

def update_package_price(gb, price):
    """ဈေးနှုန်း ပြင်ဆင်ခြင်း သို့မဟုတ် Package အသစ် ထည့်သွင်းခြင်း"""
    cursor.execute("INSERT OR REPLACE INTO packages (gb, price) VALUES (?, ?)", (gb, price))
    conn.commit()

# --- Admin Commands for Pricing ---

@bot.message_handler(commands=['setprice'])
def set_price_command(message):
    """Admin သီးသန့် ဈေးနှုန်းပြင်ဆင်သည့် Command: /setprice 1 500"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ ဤ Command အား အသုံးပြုခွင့် မရှိပါ။")
        return

    try:
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message, "⚠️ အသုံးပြုပုံ မှားယွင်းနေပါသည်။\nဥပမာ - `/setprice 1 500` (1GB ကို 500 ကျပ် သတ်မှတ်ခြင်း)", parse_mode="Markdown")
            return

        gb = int(args[1])
        price = int(args[2])

        update_package_price(gb, price)
        bot.reply_to(message, f"✅ *အောင်မြင်ပါသည်*\n\n{gb} GB ဈေးနှုန်းအား *{price:,} MMK* သို့ ပြောင်းလဲ သတ်မှတ်လိုက်ပါပြီ။", parse_mode="Markdown")

    except ValueError:
        bot.reply_to(message, "❌ ဂဏန်းအချက်အလက်များကိုသာ ရိုက်ထည့်ပေးပါ။ (ဥပမာ: /setprice 2 900)")

@bot.message_handler(commands=['prices'])
def show_prices_command(message):
    """လက်ရှိ Wi-Fi ဈေးနှုန်းအားလုံးကို ကြည့်ရှုခြင်း"""
    packages = get_packages()
    text = "📶 *လက်ရှိ သတ်မှတ်ထားသော Wi-Fi ဈေးနှုန်းများ*\n\n"
    for gb, price in packages:
        text += f"• {gb} GB — *{price:,} MMK*\n"
    
    if message.from_user.id == ADMIN_ID:
        text += "\n💡 _Admin အနေဖြင့် ဈေးနှုန်းပြင်လိုပါက `/setprice <GB> <ဈေးနှုန်း>` ဟု ရိုက်ပို့နိုင်ပါသည်။_"

    bot.reply_to(message, text, parse_mode="Markdown")

# --- Agent & User Interactions ---

@bot.message_handler(commands=['start', 'menu'])
def start_menu(message):
    packages = get_packages()
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = []
    for gb, price in packages:
        btn = types.InlineKeyboardButton(f"{gb}GB ({price:,} Ks)", callback_data=f"buy_{gb}_{price}")
        buttons.append(btn)
    
    markup.add(*buttons)
    bot.send_message(
        message.chat.id,
        "👋 မင်္ဂလာပါ၊ ဝယ်ယူလိုသော Wi-Fi Package အား ရွေးချယ်ပေးပါ-",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_buy_package(call):
    _, gb, price = call.data.split('_')
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        f"✅ ရွေးချယ်ထားသော ပက်ကေ့ဂျ် - *{gb} GB*\nကျသင့်ငွေ - *{int(price):,} MMK*\n\nVoucher Code ထုတ်ယူရန် လုပ်ဆောင်နေပါသည်...",
        parse_mode="Markdown"
    )

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
            
