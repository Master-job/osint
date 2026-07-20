import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

# Импортируем нашу работу с БД
from database import init_db, add_to_blacklist, check_blacklist

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Впиши сюда свой Telegram ID (или список ID админов)
ADMIN_IDS = [8852003217] # <-- ЗАМЕНИ НА СВОЙ ID!

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- ВЕБ-СЕРВЕР ДЛЯ РЕНДЕРА ---
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

# --- ЛОГИКА БОТА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 <b>Антифрод-бот запущен!</b>\n\n"
        "• Перешли сообщение от юзера, чтобы проверить его.\n"
        "• Админ-команда добавления в ЧС:\n"
        "<code>/ban ID_юзера Причина</code>"
    )

# Команда для бана (только для админов)
@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply("❌ У вас нет прав админа.")
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        return await message.reply("⚠️ Неверный формат!\nИспользуй: <code>/ban ID_пользователя Причина</code>\nПример: <code>/ban 6832166859 Кидала / не оплатил</code>")
    
    try:
        target_id = int(args[1])
        reason = args[2]
        
        success = add_to_blacklist(target_id, "Неизвестно", reason, message.from_user.id)
        if success:
            await message.reply(f"✅ Пользователь <code>{target_id}</code> внесен в черный список!\n<b>Причина:</b> {reason}")
        else:
            await message.reply("❌ Ошибка при записи в базу данных.")
    except ValueError:
        await message.reply("❌ ID должен состоять только из цифр.")

# Проверка пересланных сообщений
@dp.message(F.forward_origin)
async def handle_forwarded_message(message: types.Message):
    origin = message.forward_origin
    
    if origin.type == 'user':
        user = origin.sender_user
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        username = f"@{user.username}" if user.username else "Отсутствует"
        
        # ЧЕКАЕМ ПО БАЗЕ
        ban_info = check_blacklist(user.id)
        
        if ban_info:
            reason, created_at = ban_info
            status = f"🔴 <b>ВНИМАНИЕ! ПОЛЬЗОВАТЕЛЬ В ЧЕРНОМ СПИСКЕ!</b>\n<b>Причина:</b> {reason}\n<b>Дата внесения:</b> {created_at}"
        else:
            status = "🟢 <b>В локальной базе ЧС не найден.</b>"

        text = (
            f"🔍 <b>Информация о пользователе:</b>\n\n"
            f"👤 <b>Имя:</b> {first_name} {last_name}\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"🏷 <b>Username:</b> {username}\n\n"
            f"Статус проверки: {status}"
        )
    elif origin.type == 'hidden_user':
        text = (
            f"⚠️ <b>Профиль скрыт!</b>\n"
            f"Имя: {origin.sender_user_name}\n"
            f"Узнать ID невозможно."
        )
    else:
        text = "Сообщение переслано из канала или бота."

    await message.reply(text)

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Инициализируем БД
    init_db()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())