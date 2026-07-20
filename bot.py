import asyncio
from aiogram import Bot, Dispatcher

# Импортируем наш роутер и функцию инициализации БД из соседних файлов
import database
import reputation

# ⚠️ ВСТАВЬТЕ СЮДА ВАШ ТОКЕН БОТА ИЗ @BotFather
BOT_TOKEN = "ВАШ_ТОКЕН_БОТА"

async def main():
    # 1. При старте бота сразу создаем таблицы в базе данных (если их нет)
    database.init_db()
    print("База данных успешно подключена!")

    # 2. Инициализируем бота и диспетчер
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # 3. Подключаем наш модуль репутации
    dp.include_router(reputation.router)

    print("Бот запущен и готов к работе!")
    
    # Удаляем старые необработанные сообщения и запускаем бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())