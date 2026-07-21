from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import database

router = Router()

# ⚠️ ВСТАВЬ СЮДА СВОЙ TELEGRAM ID (чтобы только ты мог добавлять в списки)
ADMIN_IDS = [8310543040] 

class ReviewState(StatesGroup):
    waiting_for_comment = State()

def build_reputation_response(target_id: int, username: str = None, first_name: str = "", last_name: str = ""):
    card = database.get_card(target_id)
    
    user_ref = f"@{username}" if username else f"ID: {target_id}"
    full_name = f"{first_name} {last_name}".strip()
    
    if not card:
        status_text = "🟢 <b>В базе репутации не найден (Чисто)</b>"
        description = "Записи отсутствуют."
    else:
        status, description, _ = card
        if status == "blacklist":
            status_text = "🔴 <b>ЧЁРНЫЙ СПИСОК (Недобросовестный / Мошенник)</b>"
        else:
            status_text = "🟢 <b>БЕЛЫЙ СПИСОК (Проверенный / Надежный)</b>"

    comments = database.get_comments(target_id)

    text = (
        f"📋 <b>Карточка репутации</b>\n\n"
        f"👤 <b>Имя:</b> {full_name or 'Не указано'}\n"
        f"🆔 <b>ID:</b> <code>{target_id}</code>\n"
        f"🏷 <b>Username:</b> {user_ref}\n\n"
        f"<b>Статус:</b>\n{status_text}\n"
        f"<b>Причина / Примечание:</b> {description}\n\n"
        f"💬 <b>Отзывы участников:</b>\n"
    )
    
    if comments:
        for c_author, c_text, c_date in comments:
            date_short = c_date.split()[0]
            text += f"• <code>{date_short}</code> (от {c_author}): {c_text}\n"
    else:
        text += "<i>Комментариев пока нет.</i>\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Оставить комментарий", callback_data=f"add_comment:{target_id}")]
    ])

    return text, kb

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 <b>Бот репутации запущен!</b>\n\n"
        "• Перешли сообщение от пользователя, чтобы проверить его статус.\n"
        "• Или отправь команду: <code>/check ID_пользователя</code>"
    )

# --- АДМИН-КОМАНДА: Внести в Чёрный список ---
# Пример: /add_black 123456789 Занимался мошенничеством в личке
@router.message(Command("add_black"))
async def add_black_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав админа.")
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 3 or not args[1].isdigit():
        await message.answer("⚠️ Формат: <code>/add_black ID Причина</code>\nПример: <code>/add_black 123456789 Пишет в ЛС под видом админа</code>")
        return

    target_id = int(args[1])
    reason = args[2]

    database.add_or_update_card(
        target_id=target_id,
        username="",
        status="blacklist",
        description=reason,
        admin_id=message.from_user.id
    )
    await message.answer(f"🔴 Пользователь <code>{target_id}</code> внесён в **ЧЁРНЫЙ СПИСОК**!\nПричина: {reason}")

# --- АДМИН-КОМАНДА: Внести в Белый список ---
# Пример: /add_white 123456789 Реальный админ группы
@router.message(Command("add_white"))
async def add_white_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав админа.")
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 3 or not args[1].isdigit():
        await message.answer("⚠️ Формат: <code>/add_white ID Причина</code>\nПример: <code>/add_white 123456789 Проверенный админ</code>")
        return

    target_id = int(args[1])
    reason = args[2]

    database.add_or_update_card(
        target_id=target_id,
        username="",
        status="whitelist",
        description=reason,
        admin_id=message.from_user.id
    )
    await message.answer(f"🟢 Пользователь <code>{target_id}</code> внесён в **БЕЛЫЙ СПИСОК**!\nПримечание: {reason}")

# --- Проверка по /check ---
@router.message(Command("check"))
async def check_user_cmd(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Укажите Telegram ID цифрами.\nПример: <code>/check 123456789</code>")
        return
    
    target_id = int(args[1])
    text, kb = build_reputation_response(target_id)
    await message.answer(text, reply_markup=kb)

# --- Проверка по пересланному сообщению ---
@router.message(F.forward_origin)
async def handle_forwarded_message(message: types.Message):
    origin = message.forward_origin
    
    if origin.type == 'user':
        user = origin.sender_user
        text, kb = build_reputation_response(
            target_id=user.id,
            username=user.username,
            first_name=user.first_name or "",
            last_name=user.last_name or ""
        )
        await message.answer(text, reply_markup=kb)
    elif origin.type == 'hidden_user':
        await message.answer(
            f"⚠️ <b>Профиль скрыт настройками приватности!</b>\n"
            f"Имя: {origin.sender_user_name}\n"
            f"Узнать ID скрытого аккаунта напрямую невозможно."
        )
    else:
        await message.answer("Сообщение переслано из канала или бота.")

@router.callback_query(F.data.startswith("add_comment:"))
async def start_add_comment(callback: types.CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split(":")[1])
    await state.update_data(target_id=target_id)
    await state.set_state(ReviewState.waiting_for_comment)
    
    await callback.message.answer("Напишите ваш комментарий или отзыв о пользователе:")
    await callback.answer()

@router.message(ReviewState.waiting_for_comment)
async def save_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data["target_id"]
    comment_text = message.text.strip()

    database.add_comment(
        target_id=target_id,
        author_id=message.from_user.id,
        text=comment_text
    )

    await state.clear()
    await message.answer("✅ Ваш комментарий сохранен в карточке!")

@router.message(F.text)
async def fallback_handler(message: types.Message):
    await message.answer(
        "Перешли сообщение от пользователя или напиши команду <code>/check ID</code>"
    )