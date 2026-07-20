from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импортируем готовые функции из нашего файла database.py
import database

router = Router()

# Состояние ожидания текста комментария
class ReviewState(StatesGroup):
    waiting_for_comment = State()

# --- 1. Проверка пользователя по команде /check ---
@router.message(Command("check"))
async def check_user_cmd(message: types.Message):
    # Разбиваем команду: из "/check 123456" получаем "123456"
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Укажите Telegram ID цифрами.\nПример: `/check 123456789`", parse_mode="Markdown")
        return
    
    target_id = int(args[1])
    
    # Спрашиваем базу данных
    card = database.get_card(target_id)
    
    if not card:
        await message.answer(f"ℹ️ Пользователь с ID `{target_id}` в списках не числится.", parse_mode="Markdown")
        return

    status, description, username = card
    user_ref = f"@{username}" if username else f"ID: {target_id}"
    
    # Красивая плашка статуса без обидных слов
    if status == "blacklist":
        badge = "🔴 **ЧЁРНЫЙ СПИСОК (Недобросовестный)**"
    else:
        badge = "🟢 **БЕЛЫЙ СПИСОК (Проверенный / Надежный)**"
        
    # Достаем комментарии
    comments = database.get_comments(target_id)

    # Собираем красивый текст
    text = (
        f"📋 **Карточка репутации**\n\n"
        f"Пользователь: {user_ref}\n"
        f"Статус: {badge}\n"
        f"Примечание: {description}\n\n"
        f"💬 **Отзывы и комментарии:**\n"
    )
    
    if comments:
        for c_author, c_text, c_date in comments:
            date_short = c_date.split()[0] # Берем только дату без времени
            text += f"• `{date_short}` (от {c_author}): {c_text}\n"
    else:
        text += "_Комментариев пока нет._\n"

    # Кнопка для добавления своего отзыва
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Оставить комментарий", callback_data=f"add_comment:{target_id}")]
    ])

    await message.answer(text, parse_mode="Markdown", reply_markup=kb)


# --- 2. Нажали кнопку "Оставить комментарий" ---
@router.callback_query(F.data.startswith("add_comment:"))
async def start_add_comment(callback: types.CallbackQuery, state: FSMContext):
    # Достаем ID того, про кого пишем отзыв
    target_id = int(callback.data.split(":")[1])
    
    # Запоминаем этот ID в памяти бота
    await state.update_data(target_id=target_id)
    
    # Переводим пользователя в режим «ожидания текста»
    await state.set_state(ReviewState.waiting_for_comment)
    
    await callback.message.answer("Напишите ваш отзыв или комментарий об этом пользователе:")
    await callback.answer()


# --- 3. Пользователь прислал текст комментария ---
@router.message(ReviewState.waiting_for_comment)
async def save_comment(message: types.Message, state: FSMContext):
    # Вспоминаем, кому писали комментарий
    data = await state.get_data()
    target_id = data["target_id"]
    comment_text = message.text.strip()

    # Сохраняем комментарий в БД через наш файл database.py
    database.add_comment(
        target_id=target_id,
        author_id=message.from_user.id,
        text=comment_text
    )

    # Сбрасываем состояние
    await state.clear()
    await message.answer("✅ Ваш комментарий сохранен в карточке пользователя!")