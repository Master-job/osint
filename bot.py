import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- ВЕБ-СЕРВЕР ДЛЯ РЕНДЕРА (чтобы не отключал) ---
async def handle_ping(request):
    return web.Response(text="Bot is active and running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render передает PORT автоматически, если нет - берем 10000
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Веб-сервер запущен на порту {port}")

# --- ЛОГИКА БОТА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **Бот-аналитик запущен!**\n\n"
        "Перешли мне любое сообщение от пользователя, чтобы проверить его профиль."
    )

@dp.message(F.forward_origin)
async def handle_forwarded_message(message: types.Message):
    origin = message.forward_origin
    
    if origin.type == 'user':
        user = origin.sender_user
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        username = f"@{user.username}" if user.username else "Отсутствует"
        
        text = (
            f"🔍 <b>Информация из пересланного сообщения:</b>\n\n"
            f"👤 <b>Имя:</b> {first_name} {last_name}\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"🏷 <b>Username:</b> {username}"
        )
    elif origin.type == 'hidden_user':
        text = (
            f"⚠️ <b>Профиль скрыт настройками приватности!</b>\n\n"
            f"👤 <b>Имя в профиле:</b> {origin.sender_user_name}\n"
            f"❌ Узнать ID прямо через пересылку невозможно."
        )
    else:
        text = "Сообщение переслано из канала или бота."

    await message.reply(text)

# --- ГЛАВНАЯ ТОЧКА ВХОДА ---
async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Очищаем очередь старых сообщений
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем одновременно бота и веб-сервер
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())