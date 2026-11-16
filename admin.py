from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from database import get_admin_system_stats, get_users_list, get_recent_activity_logs
from parser import format_money
from keyboards import get_admin_keyboard

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return
        
    stats = get_admin_system_stats()
    text = (
        "👑 **ADMIN BOSHQARUV PANELI**\n\n"
        f"👥 Jami foydalanuvchilar: **{stats['users_count']} ta**\n"
        f"📝 Jami tranzaksiyalar: **{stats['total_transactions']} ta**\n"
        f"💳 Jami pul aylanmasi: **{format_money(stats['total_volume'])}**\n"
        f"📜 Jami tizim loglari: **{stats['total_logs']} ta**\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await query.answer("Siz admin emassiz!", show_alert=True)
        return
        
    await query.answer()
    data = query.data
    
    if data == "admin_stats":
        stats = get_admin_system_stats()
        text = (
            "📊 **TIZIM STATISTIKASI**\n\n"
            f"👤 Foydalanuvchilar soni: **{stats['users_count']} ta**\n"
            f"🔄 Tranzaksiyalar soni: **{stats['total_transactions']} ta**\n"
            f"💰 Jami aylanma summa: **{format_money(stats['total_volume'])}**\n"
            f"📑 Qayd etilgan harakatlar: **{stats['total_logs']} ta**"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_admin_keyboard())
        
    elif data == "admin_users":
        users = get_users_list(limit=25)
        if not users:
            text = "👥 Hozircha foydalanuvchilar mavjud emas."
        else:
            text = "👥 **OXIRGI FOYDALANUVCHILAR RO'YXATI:**\n\n"
            for i, u in enumerate(users, 1):
                username = f"@{u['username']}" if u['username'] else "mavjud emas"
                name = f"{u['first_name'] or ''} {u['last_name'] or ''}".strip() or "Noma'lum"
                text += (
                    f"{i}. **{name}** ({username})\n"
                    f"   🆔 ID: `{u['user_id']}`\n"
                    f"   🧾 Tranzaksiyalar: {u['trans_count']} ta\n"
                    f"   📅 Qo'shilgan: {u['created_at'][:16]}\n\n"
                )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_admin_keyboard())
        
    elif data == "admin_logs":
        logs = get_recent_activity_logs(limit=20)
        if not logs:
            text = "📜 Hozircha faollik yozuvlari yo'q."
        else:
            text = "📜 **FOYDALANUVCHILARNING SO'NGGI XABARLARI:**\n\n"
            for l in logs:
                name = l['first_name'] or str(l['user_id'])
                username = f"(@{l['username']})" if l['username'] else ""
                content = (l['content'][:60] + "...") if len(l['content']) > 60 else l['content']
                text += f"🕒 {l['created_at'][11:16]} | **{name}** {username}:\n💬 _{content}_\n\n"
                
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_admin_keyboard())
        
    elif data == "admin_close":
        await query.delete_message()
