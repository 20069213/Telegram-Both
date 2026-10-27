import telebot
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask
import threading

# ==========================================
# 1. البيانات الأساسية
# ==========================================
TOKEN = '9075617365:AAGKaqQmvyqqBqzMyqDi2J6MX-PKOrLy0Bg'
OWNER_ID = 7626253167
MY_USERNAME = "YourUsernameHere" # <--- غير دي ليوزرنيمك الحقيقي (من غير @)

CHANNELS = [
    "https://t.me/ddd_488",
    "https://t.me/shawmingii",
    "https://t.me/jfjfhfjrhexxs"
]

bot = telebot.TeleBot(TOKEN)
FILES_DB = "files_data.json"
POSTS_DB = "posts_data.json"

# ==========================================
# 2. إدارة قواعد البيانات
# ==========================================
def load_data(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==========================================
# 3. التحقق من الاشتراك
# ==========================================
def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            channel_username = channel.split('/')[-1]
            member = bot.get_chat_member(f"@{channel_username}", user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return False
    return True

def get_subscribe_keyboard():
    markup = InlineKeyboardMarkup()
    for i, channel in enumerate(CHANNELS, 1):
        markup.add(InlineKeyboardButton(f"📢 اشترك في القناة {i}", url=channel))
    markup.add(InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="check"))
    return markup

def main_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("📂 البرامج المتاحة"))
    markup.add(KeyboardButton("🖼️ تصفح المحتوى العام"))
    markup.add(KeyboardButton("📞 تواصل مع صاحب البوت"))
    
    if user_id == OWNER_ID:
        markup.add(KeyboardButton("➕ إضافة برنامج جديد"))
        
    return markup

# ==========================================
# 4. أوامر البوت
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = message.from_user.username
    
    if user_id != OWNER_ID:
        try:
            user_link = f"@{username}" if username else "لا يوجد يوزرنيم"
            bot.send_message(OWNER_ID, f"🔔 **شخص جديد دخل البوت!**\n\n👤 الاسم: {user_name}\n🔗 اليوزر: {user_link}\n🆔 الـ ID: `{user_id}`", parse_mode='Markdown')
        except: pass

    if user_id == OWNER_ID or check_subscription(user_id):
        bot.reply_to(message, "أهلاً بيك! 👋\nاختار من الأزرار اللي تحت:", reply_markup=main_keyboard(user_id))
    else:
        bot.reply_to(message, "⚠️ عشان تستخدم البوت، لازم تشترك في القنوات دي الأول:", reply_markup=get_subscribe_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "check")
def callback_check(call):
    user_id = call.from_user.id
    if user_id == OWNER_ID or check_subscription(user_id):
        bot.edit_message_text("✅ تمام! انت مشترك.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id, "اختار من الأزرار:", reply_markup=main_keyboard(user_id))
    else:
        bot.answer_callback_query(call.id, "❌ لسه مش مشترك.", show_alert=True)

# ==========================================
# 5. إضافة برنامج (لصاحب البوت فقط)
# ==========================================
@bot.message_handler(func=lambda message: message.text == "➕ إضافة برنامج جديد" and message.from_user.id == OWNER_ID)
def ask_for_file(message):
    msg = bot.reply_to(message, "📥 ابعتلي الملف (البرنامج) اللي عايز ترفعه دلوقتي.")
    bot.register_next_step_handler(msg, receive_file)

def receive_file(message):
    if not message.document:
        bot.reply_to(message, "❌ انت مكتبعتش ملف. ابعت الملف تاني.")
        return
    msg = bot.reply_to(message, "✍️ تمام، الملف وصل. اكتب اسم البرنامج اللي هيظهر للناس:")
    bot.register_next_step_handler(msg, save_program_name, message.document.file_id)

def save_program_name(message, file_id):
    files = load_data(FILES_DB)
    new_id = str(len(files) + 1)
    files[new_id] = {"name": message.text, "file_id": file_id}
    save_data(FILES_DB, files)
    bot.reply_to(message, f"✅ **تم الرفع بنجاح!**\nالبرنامج: {message.text}", parse_mode='Markdown', reply_markup=main_keyboard(message.from_user.id))

# ==========================================
# 6. عرض البرامج (الملفات)
# ==========================================
@bot.message_handler(func=lambda message: message.text == "📂 البرامج المتاحة")
def show_programs(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and not check_subscription(user_id):
        bot.reply_to(message, "⚠️ لازم تشترك الأول.", reply_markup=get_subscribe_keyboard())
        return
    
    files = load_data(FILES_DB)
    if not files:
        bot.reply_to(message, "📂 مفيش برامج مرفوعة لحد الآن.")
        return

    markup = InlineKeyboardMarkup()
    for file_id, file_data in files.items():
        markup.add(InlineKeyboardButton(f"📥 {file_data['name']}", callback_data=f"getfile_{file_id}"))
    bot.reply_to(message, "📂 **البرامج المتاحة:**", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("getfile_"))
def send_file_to_user(call):
    file_id = call.data.split("_")[1]
    files = load_data(FILES_DB)
    if file_id in files:
        bot.answer_callback_query(call.id, "⏳ جاري تحميل الملف...")
        bot.send_document(call.message.chat.id, files[file_id]['file_id'])
    else:
        bot.answer_callback_query(call.id, "❌ الملف غير موجود.", show_alert=True)

# ==========================================
# 7. تصفح المحتوى العام
# ==========================================
@bot.message_handler(func=lambda message: message.text == "🖼️ تصفح المحتوى العام")
def show_posts(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and not check_subscription(user_id):
        bot.reply_to(message, "⚠️ لازم تشترك الأول.", reply_markup=get_subscribe_keyboard())
        return

    posts = load_data(POSTS_DB)
    if not posts:
        bot.reply_to(message, "📭 مفيش محتوى منشور لحد الآن.")
        return

    markup = InlineKeyboardMarkup()
    for post_id, post_data in reversed(list(posts.items())):
        btn_text = post_data.get('text', 'محتوى')[:20] 
        markup.add(InlineKeyboardButton(f"📄 {btn_text}...", callback_data=f"getpost_{post_id}"))
    
    bot.reply_to(message, "🖼️ **كل المحتوى المنشور:**\nاختار عشان تشوفه:", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("getpost_"))
def send_post_to_user(call):
    post_id = call.data.split("_")[1]
    posts = load_data(POSTS_DB)
    
    if post_id in posts:
        post = posts[post_id]
        bot.answer_callback_query(call.id, "⏳ جاري التحميل...")
        if post['type'] == 'text':
            bot.send_message(call.message.chat.id, post['content'])
        else:
            try:
                bot.copy_message(call.message.chat.id, from_chat_id=OWNER_ID, message_id=post['content'])
            except Exception:
                bot.send_message(call.message.chat.id, "❌ حدث خطأ في إرسال المحتوى.")
    else:
        bot.answer_callback_query(call.id, "❌ المحتوى غير موجود.", show_alert=True)

# ==========================================
# 8. استقبال أي حاجة منك (صاحب البوت) وحفظها
# ==========================================
@bot.message_handler(func=lambda message: message.from_user.id == OWNER_ID, content_types=['text', 'photo', 'video', 'document', 'audio'])
def receive_owner_posts(message):
    if message.text in ["📂 البرامج المتاحة", "🖼️ تصفح المحتوى العام", "📞 تواصل مع صاحب البوت", "➕ إضافة برنامج جديد", "/start"]:
        return

    posts = load_data(POSTS_DB)
    new_id = str(len(posts) + 1)
    
    if message.text:
        posts[new_id] = {"type": "text", "content": message.text, "text": message.text}
        bot.reply_to(message, "✅ تم حفظ النص ونشره للمستخدمين.")
    else:
        posts[new_id] = {"type": "media", "content": message.message_id, "text": "محتوى جديد"}
        bot.reply_to(message, "✅ تم حفظ المحتوى ونشره للمستخدمين.")
        
    save_data(POSTS_DB, posts)

# ==========================================
# 9. زرار التواصل
# ==========================================
@bot.message_handler(func=lambda message: message.text == "📞 تواصل مع صاحب البوت")
def contact_owner(message):
    text = f"👤 **للتواصل:**\n\n🔗 اليوزرنيم: @{MY_USERNAME}"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"💬 ابعت رسالة", url=f"https://t.me/{MY_USERNAME}"))
    bot.reply_to(message, text, parse_mode='Markdown', reply_markup=markup)

# ==========================================
# 10. سيرفر الويب (عشان Render)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running successfully!"

def run_bot():
    print("البوت شغال...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    # تشغيل البوت في Thread منفصل
    t = threading.Thread(target=run_bot)
    t.start()
    
    # تشغيل سيرفر Flask عشان Render ميقفلوش
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
