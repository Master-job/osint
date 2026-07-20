import os
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# Подгружаем переменные из файла .env (если работаем локально)
load_dotenv()

# Достаем токен из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ Ошибка: Переменная BOT_TOKEN не найдена в окружении (.env)!")

import database
import reputation

async def main():
    # Инициализируем БД
    database.init_db()
    print("База данных готова!")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем роутер списков
    dp.include_router(reputation.router)

    print("Бот успешно запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())