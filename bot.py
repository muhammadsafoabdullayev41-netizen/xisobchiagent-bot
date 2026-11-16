import logging
import asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from telegram.request import HTTPXRequest
from config import BOT_TOKEN, ADMIN_ID, PROXY_URL
from database import init_db

from handlers import (
    start_handler, text_message_handler, photo_message_handler,
    callback_query_handler, report_handler, help_handler, new_month_request_handler
)
from admin import admin_command, admin_callbacks
from keep_alive import keep_alive

# Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # Render va 24/7 cron-job uchun veb-serverni ishga tushirish
    keep_alive()

    # 1. Ma'lumotlar bazasini initsializatsiya qilish
    logger.info("Ma'lumotlar bazasi initsializatsiya qilinmoqda...")
    init_db()
    
    # 2. Telegram Bot ilovasini qurish
    logger.info("Bot ishga tushirilmoqda...")
    if PROXY_URL:
        logger.info(f"Proksi ishlatilmoqda: {PROXY_URL}")
        request = HTTPXRequest(
            proxy=PROXY_URL,
            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0,
            pool_timeout=30.0,
            connection_pool_size=10,
            http_version="1.1"
        )
    else:
        request = HTTPXRequest(
            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0,
            pool_timeout=30.0,
            connection_pool_size=10,
            http_version="1.1"
        )
        
    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()
    
    # 3. Komandalar
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("report", report_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("new_month", new_month_request_handler))
    app.add_handler(CommandHandler("admin", admin_command))
    
    # 4. Callback Query Handlerlari (tugmalar)
    # Admin callbacklari
    app.add_handler(CallbackQueryHandler(admin_callbacks, pattern="^admin_"))
    # Oddiy callbacklar
    app.add_handler(CallbackQueryHandler(callback_query_handler))
    
    # 5. Rasm (Cheklar) va Matn xabarlari
    app.add_handler(MessageHandler(filters.PHOTO, photo_message_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    
    logger.info("Hisobchi bot muvaffaqiyatli tayyorlandi!")
    print("=" * 50)
    print("🤖 HISOBCHI BOT ISHGA TUSHMOQDA...")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print("=" * 50)
    
    # Doimiy qayta ulanish (Auto-reconnect) tsikli
    import time
    while True:
        try:
            logger.info("Telegram serveriga ulanilmoqda...")
            app.run_polling(drop_pending_updates=True, bootstrap_retries=10)
        except Exception as e:
            logger.warning(f"Tarmoq kutilmoqda (VPN/Internet): {e}. 5 soniyadan keyin qayta uriniladi...")
            time.sleep(5)

if __name__ == "__main__":
    main()
