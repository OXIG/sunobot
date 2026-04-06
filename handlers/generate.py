from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.crud import get_user_balance, deduct_balance, save_generation, get_or_create_user
from database.session import async_session_maker
from services.deepseek import get_lyrics
from services.suno import SunoClient
from services.global_counter import can_generate, use_generation
from config import SUNO_API_URL
import logging

logger = logging.getLogger(__name__)

router = Router()
suno = SunoClient(SUNO_API_URL)

class SongCreation(StatesGroup):
    waiting_for_theme = State()
    waiting_for_style = State()
    waiting_for_vocal = State()
    waiting_for_approval = State()

def style_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Рок", callback_data="style_rock")],
        [InlineKeyboardButton(text="Поп", callback_data="style_pop")],
        [InlineKeyboardButton(text="Рэп", callback_data="style_rap")],
        [InlineKeyboardButton(text="Джаз", callback_data="style_jazz")],
        [InlineKeyboardButton(text="✏️ Свой вариант", callback_data="style_other")]
    ])

def vocal_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Мужской", callback_data="vocal_male")],
        [InlineKeyboardButton(text="👩 Женский", callback_data="vocal_female")],
        [InlineKeyboardButton(text="🎤 Другое", callback_data="vocal_other")]
    ])

@router.message(Command("generate"))
async def start_generation(message: types.Message, state: FSMContext):
    async with async_session_maker() as session:
        balance = await get_user_balance(session, message.from_user.id)
    if balance <= 0:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 ПОПОЛНИТЬ", callback_data="pay")]
        ])
        await message.answer(
            "❌ У вас недостаточно средств. Пополните баланс, чтобы создавать песни.",
            reply_markup=keyboard
        )
        return
    if not await can_generate():
        await message.answer("❌ Месячный лимит генераций для бота исчерпан. Попробуйте позже.")
        return
    await message.answer("✍️ О чём будет ваша песня? Напишите тему, идею, настроение.")
    await state.set_state(SongCreation.waiting_for_theme)

@router.message(SongCreation.waiting_for_theme)
async def theme_received(message: types.Message, state: FSMContext):
    await state.update_data(theme=message.text)
    await message.answer("🎸 Выберите жанр:", reply_markup=style_keyboard())
    await state.set_state(SongCreation.waiting_for_style)

@router.callback_query(SongCreation.waiting_for_style, lambda c: c.data.startswith("style_"))
async def style_callback(callback: types.CallbackQuery, state: FSMContext):
    style = callback.data.split("_")[1]
    if style == "other":
        await callback.message.answer("Напишите ваш жанр вручную:")
        await state.set_state(SongCreation.waiting_for_style)
    else:
        await state.update_data(style=style)
        await callback.message.answer(f"🎸 Выбрано: {style}")
        await callback.message.answer("🎤 Выберите тип вокала:", reply_markup=vocal_keyboard())
        await state.set_state(SongCreation.waiting_for_vocal)
    await callback.answer()

@router.message(SongCreation.waiting_for_style)
async def style_manual(message: types.Message, state: FSMContext):
    await state.update_data(style=message.text)
    await message.answer("🎤 Выберите тип вокала:", reply_markup=vocal_keyboard())
    await state.set_state(SongCreation.waiting_for_vocal)

@router.callback_query(SongCreation.waiting_for_vocal, lambda c: c.data.startswith("vocal_"))
async def vocal_callback(callback: types.CallbackQuery, state: FSMContext):
    vocal = callback.data.split("_")[1]
    if vocal == "other":
        await callback.message.answer("Напишите тип вокала вручную:")
        await state.set_state(SongCreation.waiting_for_vocal)
    else:
        await state.update_data(vocal=vocal)
        await callback.message.answer(f"🎤 Выбрано: {vocal}")
        # Генерация текста
        await callback.message.answer("🤖 Генерирую текст песни... Подождите немного.")
        messages = []
        data = await state.get_data()
        theme = data.get("theme", "")
        style = data.get("style", "поп")
        vocal = data.get("vocal", "мужской")
        messages.append({"role": "user", "content": f"Тема: {theme}"})
        messages.append({"role": "user", "content": f"Жанр: {style}"})
        messages.append({"role": "user", "content": f"Вокал: {vocal}"})
        messages.append({"role": "user", "content": "Напиши текст песни на русском языке, 2-3 куплета и припев."})
        try:
            lyrics = await get_lyrics(messages)
            await state.update_data(lyrics=lyrics)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Сгенерировать песню", callback_data="confirm_generate")]
            ])
            await callback.message.answer(f"📝 Вот текст песни:\n\n{lyrics}\n\nНажмите кнопку, чтобы начать генерацию музыки.", reply_markup=keyboard)
            await state.set_state(SongCreation.waiting_for_approval)
        except Exception as e:
            logger.exception("Ошибка генерации текста")
            await callback.message.answer("❌ Не удалось сгенерировать текст песни. Попробуйте позже.")
            await state.clear()
    await callback.answer()

@router.message(SongCreation.waiting_for_vocal)
async def vocal_manual(message: types.Message, state: FSMContext):
    await state.update_data(vocal=message.text)
    await message.answer("🤖 Генерирую текст песни... Подождите немного.")
    messages = []
    data = await state.get_data()
    theme = data.get("theme", "")
    style = data.get("style", "поп")
    vocal = data.get("vocal", "мужской")
    messages.append({"role": "user", "content": f"Тема: {theme}"})
    messages.append({"role": "user", "content": f"Жанр: {style}"})
    messages.append({"role": "user", "content": f"Вокал: {vocal}"})
    messages.append({"role": "user", "content": "Напиши текст песни на русском языке, 2-3 куплета и припев."})
    try:
        lyrics = await get_lyrics(messages)
        await state.update_data(lyrics=lyrics)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Сгенерировать песню", callback_data="confirm_generate")]
        ])
        await message.answer(f"📝 Вот текст песни:\n\n{lyrics}\n\nНажмите кнопку, чтобы начать генерацию музыки.", reply_markup=keyboard)
        await state.set_state(SongCreation.waiting_for_approval)
    except Exception as e:
        logger.exception("Ошибка генерации текста")
        await message.answer("❌ Не удалось сгенерировать текст песни. Попробуйте позже.")
        await state.clear()

@router.callback_query(SongCreation.waiting_for_approval, F.data == "confirm_generate")
async def confirm_generation(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session_maker() as session:
        balance = await get_user_balance(session, user_id)
    if balance <= 0:
        await callback.message.answer("❌ Недостаточно средств.")
        await callback.answer()
        return
    if not await can_generate():
        await callback.message.answer("❌ Месячный лимит генераций исчерпан.")
        await callback.answer()
        return

    await callback.message.answer("🎵 Генерация началась, обычно это занимает не более 5 минут...")

    data = await state.get_data()
    lyrics = data.get("lyrics")
    style = data.get("style", "pop")
    vocal = data.get("vocal", "male")

    if not lyrics:
        await callback.message.answer("❌ Текст песни не найден. Начните сначала /generate")
        await callback.answer()
        return

    audio1, audio2 = await suno.generate(lyrics, style, vocal)
    if not audio1 or not audio2:
        await callback.message.answer("❌ Ошибка генерации. Попробуйте позже.")
        await callback.answer()
        return

    async with async_session_maker() as session:
        success = await deduct_balance(session, user_id, 1)
        if success:
            user = await get_or_create_user(session, user_id)
            await save_generation(session, user.id, lyrics, style, vocal, audio1, audio2)
            await use_generation()
            new_balance = await get_user_balance(session, user_id)
        else:
            await callback.message.answer("❌ Не удалось списать средства.")
            await callback.answer()
            return

    await callback.message.answer_audio(audio1, caption="🎵 Вариант 1")
    await callback.message.answer_audio(audio2, caption="🎵 Вариант 2")
    await callback.message.answer(f"✅ Песня готова! Осталось генераций: {new_balance}")

    await state.clear()
    await callback.answer()
