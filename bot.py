from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)
import mysql.connector

# Bosqichlar
ASK_NAME, ASK_PHONE, WAIT_FOR_CONFIRM = range(3)

# MySQL ulanish
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",           # o'zgartiring agar boshqa user bo'lsa
        password="1111",       # parolingiz
        database="telegram_bot"
    )

# Foydalanuvchini saqlash (agar mavjud bo'lmasa) va ID olish
def save_user(full_name, phone):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Tekshiramiz — bu yerda fetchone()dan so'ng nextset() bilan tozalaymiz
        cursor.execute("SELECT id FROM users WHERE phone = %s", (phone,))
        result = cursor.fetchone()
        cursor.nextset()  # 👈 Bu muammoni hal qiladi

        if result:
            user_id = result[0]
        else:
            cursor.execute("INSERT INTO users (full_name, phone) VALUES (%s, %s)", (full_name, phone))
            conn.commit()
            user_id = cursor.lastrowid
    except mysql.connector.Error as err:
        print(f"MySQL xatosi: {err}")
        user_id = None
    finally:
        cursor.close()
        conn.close()

    return user_id


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👤 Iltimos, ismingiz va familyangizni kiriting:")
    return ASK_NAME

# 1-qadam: ism familiya
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text("📱 Telefon raqamingizni kiriting: +998 xx xxx xx xx")
    return ASK_PHONE

# 2-qadam: telefon → ro‘yxat → shartlar
async def show_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    context.user_data['phone'] = phone
    full_name = context.user_data['full_name']

    user_id = save_user(full_name, phone)
    if user_id is None:
        await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")
        return ConversationHandler.END

    await update.message.reply_text("✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!")

    message = (
        "🕌 Assalomu alaykum!\n"
        "✈️ Bilum Travel botga xush kelibsiz!\n\n"
        "🎉 *KONKURSIMIZGA XUSH KELIBSIZ!* 🎁\n"
        "Quyidagi oddiy 3 ta shartni bajaring va sovrinli o‘yinda ishtirok eting:\n\n"
        f"1️⃣ [Instagram sahifamizga obuna bo‘ling 📸](https://www.instagram.com/bilum_travel?igsh=enIyNHNjNXNqenR3)\n"
        f"2️⃣ [Telegram kanalimizga a'zo bo‘ling 📢](https://t.me/bilum_travel)\n"
        f"3️⃣ [Telegram guruhimizga qo‘shiling 👥](https://t.me/bilumgr)\n\n"
        "✅ Ushbu 3 shartni bajarganingizdan so‘ng *Bajardim* tugmasini bosing va bot sizga ishtirok raqamingizni yuboradi! 🎫\n\n"
        "👀 Bizni faol kuzatishda davom eting — qiziqarli yangiliklar va sovrinlar sizni kutmoqda!\n\n"
        "🍀 Konkursda omad tilaymiz!"
    )

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

    keyboard = [['Bajardim']]
    await update.message.reply_text(
        "🔘 Tugatganingizdan so'ng quyidagi tugmani bosing:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

    return WAIT_FOR_CONFIRM

# 3-qadam: "Bajardim" tugmasi bosiladi
async def confirm_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = context.user_data.get('full_name')
    phone = context.user_data.get('phone')

    user_id = save_user(full_name, phone)

    await update.message.reply_text(
        f"🎉 Rahmat, {full_name}!\n"
        f"✅ Siz muvaffaqiyatli ro'yxatdan o'tdingiz.\n"
        f"🎫 Sizning ishtirok raqamingiz: {user_id:06d}"
    )
    return ConversationHandler.END

# Botni ishga tushirish
def main():
    app = Application.builder().token("8346687594:AAFcK_zjRXvpsWGA40HrnVVQEpF9XJK056c").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_conditions)],
            WAIT_FOR_CONFIRM: [MessageHandler(filters.Regex("^Bajardim$"), confirm_done)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)

    print("✅ Bot ishga tushdi...")
    app.run_polling()

if __name__ == '__main__':
    main()
