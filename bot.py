
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from config import TOKEN

# Включаем логирование, чтобы видеть ошибки в терминале
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    await message.answer(
        "👋 Привет! Я OSINT-бот.\n\n"
        "Перешли мне **любое сообщение мошенника**, и я попробую вытащить всю информацию о его аккаунте."
    )

@dp.message()
async def analyze_forwarded_message(message: Message):
    # Проверяем, является ли сообщение пересланным
    if not message.forward_origin:
        await message.answer("⚠️ Пожалуйста, именно **перешли** мне сообщение мошенника, а не скопируй его текст.")
        return

    origin = message.forward_origin
    user_id = None
    name = "Скрыто"
    username = "Отсутствует"

    # Обработка разных типов пересылки (от пользователя, скрытого аккаунта, канала, чата)
    if origin.type == "user":
        user = origin.sender_user
        user_id = user.id
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "Отсутствует"
    
    elif origin.type == "hidden_user":
        name = origin.sender_user_name
        await message.answer(
            f"❌ **Аккаунт скрыт настройками приватности!**\n"
            f"Имя в профиле: `{name}`\n\n"
            f"Прямой Telegram ID извлечь невозможно. Попробуй отправить мне его `@username` текстовым сообщением."
        )
        return
        
    elif origin.type == "channel":
        await message.answer("📢 Это сообщение переслано из канала, а не от пользователя.")
        return
    elif origin.type == "chat":
        await message.answer("👥 Это сообщение переслано из супергруппы/чата.")
        return

    # Если ID успешно найден, выводим первичный отчет
    if user_id:
        report = (
            f"🔍 **РЕЗУЛЬТАТ ПЕРВИЧНОГО АНАЛИЗА:**\n\n"
            f"🆔 **Telegram ID:** `{user_id}`\n"
            f"👤 **Имя:** {name}\n"
            f"🔗 **Никнейм:** {username}\n"
            f" Ссылка: tg://user?id={user_id}\n\n"
            f"⏳ *Запускаю поиск по базам данных и чатам...*"
        )
        
        # Проверяем наличие фото профиля
        photos = await bot.get_user_profile_photos(user_id=user_id, limit=1)
        if photos.total_count > 0:
            # Отправляем отчет вместе с последней аватаркой
            photo_id = photos.photos[0][-1].file_id
            await message.reply_photo(photo=photo_id, caption=report, parse_mode="Markdown")
        else:
            await message.reply(text=report, parse_mode="Markdown")

async def main():
    print("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
