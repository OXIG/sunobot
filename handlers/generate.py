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
import asyncio

logger = logging.getLogger(__name__)

router = Router()
suno = SunoClient(SUNO_API_URL)

class SongCreation(StatesGroup):
    waiting_for_theme = State()
    chatting_with_deepseek = State()
    waiting_for_manual_lyrics = State()

last_lyrics_cache = {}

SYSTEM_PROMPT = """Ты — ассистент для написания текстов песен для нейросети Suno.

ПРАВИЛА:
1. Отвечай ТОЛЬКО по делу. Без воды, без лишних объяснений.
2. Твои ответы должны быть краткими (максимум 2-3 предложения).
3. Если пользователь просит текст песни — сразу пиши текст в формате:
   [КУПЛЕТ 1]
   [ПРИПЕВ]
   [КУПЛЕТ 2]
   [ПРИПЕВ]
   [БРИДЖ]
   [КУПЛЕТ 3]
   [ПРИПЕВ]
4. По умолчанию текст = 3 куплета + бридж + припев.
5. Если пользователь просит изменить текст — меняй ТОЛЬКО то, что просят.
6. Не задавай лишних вопросов.
7. В конце каждого готового текста добавь строку: [ТЕКСТ_ГОТОВ]
8. Жанр подбирай сам (pop, rock, hip-hop, electronic, lo-fi, orchestral, ambient)."""

def get_generate_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎵 Сгенерировать песню", callback_data="confirm_generate")]
    ])

def get_regenerate_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Попробовать ещё раз", callback_data="regenerate_song")]
    ])

@router.message(Command("generate"))
async def start_generation(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with async_session_maker() as session:
        balance = await get_user_balance(session, user_id)
    if balance <= 0:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 ПОПОЛНИТЬ", callback_data="pay")]
        ])
        await message.answer("❌ У вас недостаточно средств.", reply_markup=keyboard)
        return
    if not await can_generate():
        await message.answer("❌ Месячный лимит генераций исчерпан.")
        return
    
    await message.answer(
        "✍️ **О чем будет ваша песня?**\n\n"
        "Напишите тему, настроение, жанр.\n"
        "Пример: «Грустная песня про любовь, поп»",
        parse_mode="Markdown"
    )
    await state.set_state(SongCreation.waiting_for_theme)

@router.message(SongCreation.waiting_for_theme)
async def theme_received(message: types.Message, state: FSMContext):
    user_input = message.text
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Напиши текст песни на тему: {user_input}. 3 куплета, бридж, припев."}
    ]
    
    await message.answer("🎤 **Генерирую текст...**")
    
    response = await get_lyrics(messages)
    await state.update_data(deepseek_messages=messages)
    await state.update_data(deepseek_messages_history=messages + [{"role": "assistant", "content": response}])
    
    if "[ТЕКСТ_ГОТОВ]" in response:
        clean_text = response.replace("[ТЕКСТ_ГОТОВ]", "").strip()
        await state.update_data(generated_lyrics=clean_text)
        await message.answer(
            f"📝 **Текст готов:**\n\n{clean_text}\n\nЕсли хотите изменить — напишите. Если всё устраивает — нажмите кнопку.",
            reply_markup=get_generate_keyboard()
        )
        await state.set_state(SongCreation.chatting_with_deepseek)
    else:
        await message.answer(response)
        await state.set_state(SongCreation.chatting_with_deepseek)

@router.message(SongCreation.chatting_with_deepseek)
async def chat_with_deepseek(message: types.Message, state: FSMContext):
    user_input = message.text
    data = await state.get_data()
    deepseek_messages = data.get("deepseek_messages_history", [])
    
    if not deepseek_messages:
        deepseek_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    deepseek_messages.append({"role": "user", "content": user_input})
    response = await get_lyrics(deepseek_messages)
    deepseek_messages.append({"role": "assistant", "content": response})
    await state.update_data(deepseek_messages_history=deepseek_messages)
    
    if "[ТЕКСТ_ГОТОВ]" in response:
        clean_text = response.replace("[ТЕКСТ_ГОТОВ]", "").strip()
        await state.update_data(generated_lyrics=clean_text)
        await message.answer(
            f"📝 **Обновлённый текст:**\n\n{clean_text}\n\nЕсли всё устраивает — нажмите кнопку.",
            reply_markup=get_generate_keyboard()
        )
    else:
        await message.answer(response)

async def generate_and_send_audio(callback: types.CallbackQuery, state: FSMContext, user_id: int):
    data = await state.get_data()
    lyrics = data.get("generated_lyrics")
    
    if not lyrics:
        await callback.message.answer("❌ Текст не найден. Начните заново: /generate")
        return False
    
    async with async_session_maker() as session:
        balance = await get_user_balance(session, user_id)
    if balance <= 0:
        await callback.message.answer("❌ Недостаточно средств.")
        return False
    if not await can_generate():
        await callback.message.answer("❌ Месячный лимит исчерпан.")
        return False
    
    msg = await callback.message.answer("🎵 **Генерирую музыку через Suno...**\n\n_Это может занять до 5 минут_", parse_mode="Markdown")
    
    audio1, audio2 = await suno.generate(lyrics, "pop", "male")
    await msg.delete()
    
    if not audio1 or not audio2:
        await callback.message.answer("❌ Ошибка генерации. Попробуйте позже.")
        return False
    
    async with async_session_maker() as session:
        success = await deduct_balance(session, user_id, 1)
        if success:
            user = await get_or_create_user(session, user_id)
            await save_generation(session, user.id, lyrics, "pop", "male", audio1, audio2)
            await use_generation()
            new_balance = await get_user_balance(session, user_id)
            last_lyrics_cache[user_id] = lyrics
        else:
            await callback.message.answer("❌ Не удалось списать средства.")
            return False
    
    await callback.message.answer_audio(audio1, caption="🎵 Вариант 1")
    await callback.message.answer_audio(audio2, caption="🎵 Вариант 2")
    await callback.message.answer(
        f"✅ **Песня готова!** Осталось генераций: {new_balance}\n\n"
        f"Не понравились варианты? Нажмите кнопку для регенерации (спишется ещё одна генерация).",
        reply_markup=get_regenerate_keyboard()
    )
    return True

@router.callback_query(SongCreation.chatting_with_deepseek, F.data == "confirm_generate")
async def confirm_generation(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    success = await generate_and_send_audio(callback, state, user_id)
    if success:
        await state.clear()
    await callback.answer()

@router.callback_query(F.data == "regenerate_song")
async def regenerate_song(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lyrics = last_lyrics_cache.get(user_id)
    
    if not lyrics:
        await callback.message.answer("❌ Нет сохранённого текста. Начните заново: /generate")
        await callback.answer()
        return
    
    await state.update_data(generated_lyrics=lyrics)
    
    success = await generate_and_send_audio(callback, state, user_id)
    if success:
        await state.clear()
    await callback.answer()
