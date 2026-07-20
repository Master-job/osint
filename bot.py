import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

# Загружаем переменные из .env файла (не забудь создать его и добавить BOT_TOKEN=твой_токен)
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я антифрод-бот. Перешли мне сообщение от пользователя, "
        "и я попробую достать его данные для проверки."
    )

# Хэндлер, который ловит только пересланные сообщения
@dp.message(F.forward_origin)
async def handle_forwarded_message(message: types.Message):
    origin = message.forward_origin
    
    # Проверяем, от кого переслано (если это обычный пользователь)
    if origin.type == 'user':
        user_id = origin.sender_user.id
        first_name = origin.sender_user.first_name
        last_name = origin.sender_user.last_name or ""
        username = f"@{origin.sender_user.username}" if origin.sender_user.username else "Нет юзернейма"
        
        response = (
            f"🔍 <b>Данные из пересланного сообщения:</b>\n"
            f"ID: <code>{user_id}</code>\n"
            f"Имя: {first_name} {last_name}\n"
            f"Username: {username}"
        )
    # Если профиль скрыт настройками приватности
    elif origin.type == 'hidden_user':
        response = (
            "⚠️ <b>Профиль скрыт</b>\n"
            f"Имя: {origin.sender_user_name}\n"
            "Пользователь запретил ссылаться на свой аккаунт при пересылке. "
            "Извлечь ID невозможно."
        )
    else:
        response = "Это сообщение переслано не от обычного пользователя (возможно, от канала или бота)."

    await message.reply(response)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен...")
    # Пропускаем старые апдейты и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())