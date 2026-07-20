import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

import database
import reputation

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("ОШИБКА: Задайте переменную окружения BOT_TOKEN!")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle_ping(request):
    return web.Response(text="Bot is active!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Веб-сервер запущен на порту {port}")

# --- ГЛАВНАЯ ТОЧКА ВХОДА ---
async def main():
    logging.basicConfig(level=logging.INFO)
    
    # 1. Запуск базы данных
    database.init_db()
    
    # 2. Подключение роутера с хэндлерами
    dp.include_router(reputation.router)
    
    # 3. Очистка старых сообщений
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 4. Одновременный запуск веб-сервера и бота
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())