import asyncio
import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# Импортируем ваши модули
import database
import reputation

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 1. Функция для "обмана" Render (слушает веб-порт)
async def handle_ping(request):
    return web.Response(text="Bot is live!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render сам передает переменную PORT (по умолчанию 10000)
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Веб-сервер запущен на порту {port}")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Инициализация базы данных
    database.init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем роутер
    dp.include_router(reputation.router)

    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем БОТА и ВЕБ-СЕРВЕР одновременно
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())