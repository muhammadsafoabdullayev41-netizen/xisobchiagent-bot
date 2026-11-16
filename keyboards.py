from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID

def get_main_keyboard(user_id: int):
    buttons = [
        [KeyboardButton("📊 Oylik Hisobot & Balans")],
        [KeyboardButton("➕ Daromad (Kirim)"), KeyboardButton("➖ Xarajat (Chiqim)")],
        [KeyboardButton("🔄 Yangi oy boshlash"), KeyboardButton("🧾 Chek tashlash")],
        [KeyboardButton("❓ Yordam va Qo'llanma")]
    ]
    
    # Faqat adminga maxsus tugma ko'rinadi
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton("👑 Admin Panel")])
        
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_cancel_transaction_keyboard(trans_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 O'chirish (Bekor qilish)", callback_data=f"del_trans_{trans_id}")]
    ])

def get_confirm_new_month_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Ha, yangi oy boshlansin", callback_data="confirm_new_month"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_new_month")
        ]
    ])

def get_admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Umumiy Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Foydalanuvchilar Ro'yxati", callback_data="admin_users")],
        [InlineKeyboardButton("📜 Foydalanuvchilar Yozgan Xabarlar", callback_data="admin_logs")],
        [InlineKeyboardButton("🔙 Yopish", callback_data="admin_close")]
    ])

def get_receipt_confirm_keyboard(trans_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ To'g'ri", callback_data="receipt_ok"),
            InlineKeyboardButton("🗑 Bekor qilish", callback_data=f"del_trans_{trans_id}")
        ]
    ])
