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

router = Router()
suno = SunoClient(SUNO_API_URL)

class SongCreation(StatesGroup):
    waiting_for_theme = State()
    waiting_for_style = State()
    waiting_for_vocal = State()
    waiting_for_approval = State()

async def get_deepseek_messages(state: FSMContext):
    data = await state.get_data()
    return data.get("messages", [{"role": "system", "content": "Ты — ассистент, помогающий написать текст песни. Задавай уточняющие вопросы о теме, жанре, настроении. После того как текст согласован, предложи нажать кнопку 'Сгенерировать песню'."}])

async def add_to_history(state: FSMContext, role: str, content: str):
    messages = await get_deepseek_messages(state)
    messages.append({"role": role, "content": content})
    await state.update_data(messages=messages)

async def call_deepseek(state: FSMContext) -> str:
    messages = await get_deepseek_messages(state)
    return await get_lyrics(messages)

@router.message(Command("generate"))
async def start_generation(message: types.Message, state: FSMContext):
    async with async_session_maker() as session:
        balance = await get_user_balance(session, message.from_user.id)
    if balance <= 0:
        await message.answer("❌ У вас недостаточно средств. Пополните баланс командой /pay")
        return
    if not await can_generate():
        await message.answer("❌ Месячный лимит генераций для бота исчерпан. Попробуйте позже.")
        return
    await message.answer("✍️ О чём будет ваша песня? Напишите тему, идею, настроение.")
    await state.set_state(SongCreation.waiting_for_theme)
    await add_to_history(state, "user", f"Пользователь хочет песню. Тема: {message.text}")

@router.message(SongCreation.waiting_for_theme)
async def theme_received(message: types.Message, state: FSMContext):
    await add_to_history(state, "user", f"Тема: {message.text}")
    response = await call_deepseek(state)
    await add_to_history(state, "assistant", response)
    await message.answer(response)
    await message.answer("🎸 В каком жанре вы хотите песню?")
    await state.set_state(SongCreation.waiting_for_style)

@router.message(SongCreation.waiting_for_style)
async def style_received(message: types.Message, state: FSMContext):
    await add_to_history(state, "user", f"Жанр: {message.text}")
    await state.update_data(style=message.text)
    response = await call_deepseek(state)
    await add_to_history(state, "assistant", response)
    await message.answer(response)
    await message.answer("🎤 Какой вокал: мужской или женский?")
    await state.set_state(SongCreation.waiting_for_vocal)

@router.message(SongCreation.waiting_for_vocal)
async def vocal_received(message: types.Message, state: FSMContext):
    await add_to_history(state, "user", f"Вокал: {message.text}")
    await state.update_data(vocal=message.text)
    response = await call_deepseek(state)
    await add_to_history(state, "assistant", response)
    await message.answer(response)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Сгенерировать песню", callback_data="confirm_generate")]
    ])
    await message.answer("Если всё устраивает, нажмите кнопку для генерации.", reply_markup=keyboard)
    await state.set_state(SongCreation.waiting_for_approval)

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

    messages = await get_deepseek_messages(state)
    lyrics = None
    for msg in reversed(messages):
        if msg["role"] == "assistant":
            lyrics = msg["content"]
            break

    if not lyrics:
        await callback.message.answer("❌ Не удалось получить текст песни. Попробуйте начать заново /generate")
        await callback.answer()
        return

    data = await state.get_data()
    style = data.get("style", "pop")
    vocal = data.get("vocal", "male")

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
