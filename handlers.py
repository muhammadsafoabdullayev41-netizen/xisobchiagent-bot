import os
import io
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

async def safe_reply(message, text, **kwargs):
    """Tarmoq nosozliklarida xabarni xavfsiz qayta yuborish"""
    for attempt in range(4):
        try:
            return await message.reply_text(text, **kwargs)
        except Exception as e:
            if attempt == 3:
                print(f"Xabar yuborishda xatolik: {e}")
                raise e
            await asyncio.sleep(1.5)

from config import ADMIN_ID, RECEIPTS_DIR
from database import (
    get_or_create_user, log_activity, add_transaction,
    delete_transaction, get_current_stats, start_new_cycle
)
from parser import format_money
from ai_service import analyze_financial_text, analyze_receipt_image
from keyboards import (
    get_main_keyboard, get_cancel_transaction_keyboard,
    get_confirm_new_month_keyboard, get_receipt_confirm_keyboard
)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    log_activity(user.id, user.username, user.first_name, "command", "/start")
    
    welcome_text = (
        f"Assalomu alaykum, **{user.first_name}**! 👋\n\n"
        "Men sizning **Shaxsiy Aqlli Hisobchingizman** 🤖📊\n\n"
        "Men sizning barcha oylik daromadlaringiz va xarajatlaringizni aniq hisoblab boraman:\n"
        "🔹 **Daromadlar:** Oylik maosh, bonuslar, qo'shimcha tushumlar\n"
        "🔹 **Xarajatlar:** Do'kon, ro'zg'or, yo'lkira, cheklar va barcha sarflar\n"
        "🔹 **Cheklar tahlili:** Do'kon cheki rasmini yuborsangiz, sun'iy intellekt uni o'zi o'qib hisoblaydi!\n\n"
        "💡 **Misollar:**\n"
        "• _\"Do'kondan ikkita non oldim 10 000 so'm\"_\n"
        "• _\"5 ta suv 15k\"_\n"
        "• _\"Taxi 25 ming\"_\n"
        "• _\"Firma menga 2 million so'm bonus berdi\"_\n"
        "• _\"Oylik tushdi 4 mln\"_\n\n"
        "O'zingizga qulay shaklda yozishingiz yoki pastdagi menyudan foydalanishingiz mumkin 👇"
    )
    
    await safe_reply(
        update.message,
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user.id)
    )

async def report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_activity(user.id, user.username, user.first_name, "menu", "Oylik Hisobot")
    
    stats = get_current_stats(user.id)
    
    # Kategoriya matni
    exp_cats_text = ""
    if stats['expense_categories']:
        for cat in stats['expense_categories']:
            exp_cats_text += f"   • {cat['category']}: **{format_money(cat['total'])}** ({cat['count']} ta)\n"
    else:
        exp_cats_text = "   _Xarajatlar kiritilmagan_\n"
        
    inc_cats_text = ""
    if stats['income_categories']:
        for cat in stats['income_categories']:
            inc_cats_text += f"   • {cat['category']}: **{format_money(cat['total'])}**\n"
    else:
        inc_cats_text = "   _Daromadlar kiritilmagan_\n"

    # Oxirgi tranzaksiyalar
    recent_text = ""
    if stats['recent_transactions']:
        for t in stats['recent_transactions'][:5]:
            icon = "🟢 +" if t['type'] == 'kirim' else "🔴 -"
            desc = t['description'] or t['category']
            recent_text += f"{icon} {format_money(t['amount'])} — _{desc}_\n"
    else:
        recent_text = "_Tranzaksiyalar yo'q_\n"

    balance_icon = "🟢" if stats['balance'] >= 0 else "🔴"

    report_text = (
        f"📊 **{stats['cycle_title'].upper()}**\n"
        f"📅 Boshlangan sana: `{stats['cycle_start'][:10]}`\n\n"
        f"💰 **Jami Daromad (Kirim):** {format_money(stats['total_income'])}\n"
        f"{inc_cats_text}\n"
        f"💸 **Jami Xarajat (Chiqim):** {format_money(stats['total_expense'])}\n"
        f"{exp_cats_text}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"{balance_icon} **Qoldiq Balans:** **{format_money(stats['balance'])}**\n"
        f"➖➖➖➖➖➖➖➖➖➖\n\n"
        f"🕒 **So'nggi yozuvlar:**\n{recent_text}"
    )
    
    await safe_reply(
        update.message,
        report_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user.id)
    )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_activity(user.id, user.username, user.first_name, "menu", "Yordam")
    
    help_text = (
        "❓ **QANDAY ISHLATILADI?**\n\n"
        "Botga xabarni odatiy o'zbek tilida yozishingiz kifoya. Bot miqdor (donasi) bilan pul summasini adashtirmaydi!\n\n"
        "🔹 **Xarajat kiritish usullari:**\n"
        "• `Do'kondan 2 ta non oldim 10 000 so'm`\n"
        "• `Besh dona muzqaymoq 35 ming`\n"
        "• `Taksi 20k` yoki `taksi 20 000`\n"
        "• `10 va uchta nol non` (10 000 so'm deb hisoblaydi)\n"
        "• `Benzin 150000`\n\n"
        "🔹 **Daromad (Bonus / Oylik / Pul tushumi) kiritish:**\n"
        "• `Oylik oldim 4 mln` yoki `Oylik 4 million`\n"
        "• `Firma 2 million so'm bonus berdi`\n"
        "• `Qo'shimcha ishdan 500k tushdi`\n"
        "• `Kirim: 1 500 000`\n\n"
        "🔹 **Do'kon cheki rasmini yuborish:**\n"
        "• Shunchaki telefoningizda chekni rasmga olib tashlang. Botdagi sun'iy intellekt chekni tahlil qilib, summasini chiqaradi!\n\n"
        "🔹 **Yangi oy boshlash:**\n"
        "• Oyingiz tugagach '🔄 Yangi oy boshlash' tugmasini bosing. Eski oylik hisobot yopiladi va yangi oy hisobi ochiladi."
    )
    await safe_reply(update.message, help_text, parse_mode="Markdown")

async def new_month_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_activity(user.id, user.username, user.first_name, "menu", "Yangi oy so'rovi")
    
    stats = get_current_stats(user.id)
    text = (
        "🔄 **YANGI OY BOSHLASH**\n\n"
        f"Hozirgi davr: **{stats['cycle_title']}**\n"
        f"💰 Jami kirim: {format_money(stats['total_income'])}\n"
        f"💸 Jami chiqim: {format_money(stats['total_expense'])}\n"
        f"💳 Qoldiq: **{format_money(stats['balance'])}**\n\n"
        "Haqiqatan ham yangi oy hisob-kitobini boshlamoqchimisiz?\n"
        "_(Joriy hisobotingiz yopiladi va yangi oydan noldan hisoblanadi)_"
    )
    await safe_reply(update.message, text, parse_mode="Markdown", reply_markup=get_confirm_new_month_keyboard())

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()
    
    # Activity log
    log_activity(user.id, user.username, user.first_name, "text", text)
    
    # Tugmalar bosilganda
    if text == "📊 Oylik Hisobot & Balans":
        await report_handler(update, context)
        return
    elif text == "➕ Daromad (Kirim)":
        await safe_reply(
            update.message,
            "➕ **Kirim / Daromad kiritish**\n\n"
            "Mablag' summasini yozib yuboring, masalan:\n"
            "• `Oylik oldim 5 mln`\n"
            "• `Firma 2 000 000 so'm bonus berdi`\n"
            "• `Qo'shimcha daromad 500k`\n\n"
            "Bu summa umumiy balansingizga qo'shiladi!"
        )
        return
    elif text == "➖ Xarajat (Chiqim)":
        await safe_reply(
            update.message,
            "➖ **Xarajat kiritish**\n\n"
            "Qilgan xarajatingizni yozing yoki chek rasmini tashlang:\n"
            "• `Do'kondan ikkita non oldim 10 000 so'm`\n"
            "• `5 ta suv 15k`\n"
            "• `Tushlik 45 ming`\n"
            "• `Benzin 150000`"
        )
        return
    elif text == "🔄 Yangi oy boshlash":
        await new_month_request_handler(update, context)
        return
    elif text == "🧾 Chek tashlash":
        await safe_reply(
            update.message,
            "🧾 **Chek tahlili (AI)**\n\n"
            "Supermarket, do'kon, dorixona yoki to'lov cheki fotosuratini to'g'ridan-to'g'ri shu yerga yuboring.\n"
            "Sun'iy intellekt chekni skanerlab, xaridlar va summani avtomatik hisoblab beradi!"
        )
        return
    elif text == "❓ Yordam va Qo'llanma":
        await help_handler(update, context)
        return
    elif text == "👑 Admin Panel" and user.id == ADMIN_ID:
        from admin import admin_command
        await admin_command(update, context)
        return

    # Moliyaviy tahlil qilish (AI + Local Parser)
    result = analyze_financial_text(text)
    
    if result and result.get("amount"):
        trans_type = result["type"]
        amount = result["amount"]
        category = result["category"]
        description = result["description"]
        
        # Bazaga qo'shamiz
        trans_id = add_transaction(
            user_id=user.id,
            trans_type=trans_type,
            amount=amount,
            category=category,
            description=description,
            raw_text=text
        )
        
        # Yangilangan balans
        stats = get_current_stats(user.id)
        
        if trans_type == "kirim":
            resp_text = (
                f"✅ **KIRIM QABUL QILINDI!** 🟢\n\n"
                f"💰 **Summa:** +{format_money(amount)}\n"
                f"📂 **Toifa:** {category}\n"
                f"📝 **Tavsif:** {description}\n\n"
                f"💳 **Yangi Balans:** **{format_money(stats['balance'])}**"
            )
        else:
            resp_text = (
                f"✅ **XARAJAT YOZILDI!** 🔴\n\n"
                f"💸 **Summa:** -{format_money(amount)}\n"
                f"📂 **Toifa:** {category}\n"
                f"📝 **Tavsif:** {description}\n\n"
                f"💳 **Qoldiq Balans:** **{format_money(stats['balance'])}**"
            )
            
        await safe_reply(
            update.message,
            resp_text,
            parse_mode="Markdown",
            reply_markup=get_cancel_transaction_keyboard(trans_id)
        )
    else:
        # Moliyaviy bo'lmagan matn
        await safe_reply(
            update.message,
            "🤔 Uzr, bu xabaringizda pul summasi topilmadi.\n\n"
            "Misol uchun quyidagicha yozishingiz mumkin:\n"
            "• `Do'kondan 2 ta non oldim 10 000 so'm`\n"
            "• `Taksi 25k`\n"
            "• `Oylik tushdi 3 mln`"
        )

async def photo_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    
    log_activity(user.id, user.username, user.first_name, "photo", f"Photo file_id: {photo.file_id}")
    
    msg_wait = await update.message.reply_text("🧾 Chek rasmi qabul qilindi. Sun'iy intellekt (AI) orqali tahlil qilinmoqda... ⏳")
    
    try:
        # Rasmni yuklab olish
        file = await photo.get_file()
        file_bytes = io.BytesIO()
        await file.download_to_memory(file_bytes)
        image_data = file_bytes.getvalue()
        
        # Chekni saqlash
        receipt_filename = f"receipt_{user.id}_{update.message.id}.jpg"
        receipt_path = os.path.join(RECEIPTS_DIR, receipt_filename)
        with open(receipt_path, "wb") as f:
            f.write(image_data)
            
        # Gemini AI orqali tahlil qilish
        receipt_result = analyze_receipt_image(image_data)
        
        if receipt_result and receipt_result.get("amount"):
            amount = receipt_result["amount"]
            category = receipt_result.get("category", "Oziq-ovqat")
            description = receipt_result.get("description", "Do'kon cheki")
            merchant = receipt_result.get("merchant", "")
            items = receipt_result.get("items", "")
            
            trans_id = add_transaction(
                user_id=user.id,
                trans_type="chiqim",
                amount=amount,
                category=category,
                description=description,
                raw_text="Chek fotosurati",
                receipt_path=receipt_path
            )
            
            stats = get_current_stats(user.id)
            
            detail_info = ""
            if merchant:
                detail_info += f"🏪 **Do'kon:** {merchant}\n"
            if items:
                detail_info += f"🛒 **Xaridlar:** {items}\n"
                
            reply_text = (
                "🧾 **CHEK TAHLIL QILINDI VA YOZILDI!** 🔴\n\n"
                f"{detail_info}"
                f"💸 **To'langan Summa:** -{format_money(amount)}\n"
                f"📂 **Toifa:** {category}\n\n"
                f"💳 **Qoldiq Balans:** **{format_money(stats['balance'])}**"
            )
            
            await msg_wait.edit_text(
                reply_text,
                parse_mode="Markdown",
                reply_markup=get_receipt_confirm_keyboard(trans_id)
            )
        else:
            await msg_wait.edit_text(
                "🧾 Chek rasmi saqlandi, ammo undagi umumiy summa aniqlanmadi.\n\n"
                "Iltimos, ushbu chekdagi summani xabar qilib yozib yuboring:\n"
                "Masalan: `Do'kon cheki 65 000 so'm` yoki `65k`"
            )
    except Exception as e:
        print(f"Rasm xatosi: {e}")
        await msg_wait.edit_text(
            "🧾 Chek rasmi qabul qilindi va saqlandi.\n"
            "Iltimos, xarajat summasini matn sifatida yuboring (masalan: `Korzinka 85 000 so'm`):"
        )

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    data = query.data
    
    # Tranzaksiyani bekor qilish
    if data.startswith("del_trans_"):
        trans_id = int(data.split("_")[2])
        success = delete_transaction(trans_id, user.id)
        if success:
            await query.answer("Tranzaksiya muvaffaqiyatli o'chirildi!", show_alert=True)
            stats = get_current_stats(user.id)
            await query.edit_message_text(
                f"🗑 **Ushbu tranzaksiya bekor qilindi.**\n\n"
                f"💳 Hozirgi qoldiq balansingiz: **{format_money(stats['balance'])}**",
                parse_mode="Markdown"
            )
        else:
            await query.answer("Tranzaksiya topilmadi yoki allaqachon o'chirilgan.", show_alert=True)
            
    elif data == "receipt_ok":
        await query.answer("Chek tasdiqlandi!")
        
    elif data == "confirm_new_month":
        await query.answer()
        stats = get_current_stats(user.id)
        
        # Yangi cycle ochamiz
        new_cycle_id = start_new_cycle(user.id)
        
        text = (
            "🎉 **Yangi oy muvaffaqiyatli boshlandi!**\n\n"
            f"O'tgan oy hisoboti yopildi (Qoldiq: {format_money(stats['balance'])}).\n\n"
            "Yangi oy uchun boshlang'ich maoshingiz yoki byudjetingizni kiritishingiz mumkin:\n"
            "Masalan: `Oylik 4.5 mln` yoki `Daromad 5 000 000 so'm`"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
        
    elif data == "cancel_new_month":
        await query.answer("Bekor qilindi.")
        await query.edit_message_text("❌ Yangi oy boshlash bekor qilindi. Joriy hisobingiz davom etmoqda.")
