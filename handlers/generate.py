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

# Хранилище для последнего сгенерированного текста (для регенерации)
last_lyrics_cache = {}

# Системный промпт для DeepSeek (строгий, под Suno)
SYSTEM_PROMPT = """Ты — ассистент для написания текстов песен для нейросети Suno.

ПРАВИЛА:
1. Отвечай ТОЛЬКО по делу. Без воды, без лишних объяснений, без "конечно, вот что я могу предложить".
2. Твои ответы должны быть краткими (максимум 2-3 предложения, если не просят иное).
3. Если пользователь просит текст песни — сразу пиши текст в формате:
   [КУПЛЕТ 1]
   [ПРИПЕВ]
   [КУПЛЕТ 2]
   [ПРИПЕВ]
   [БРИДЖ]
   [КУПЛЕТ 3]
   [ПРИПЕВ]
4. По умолчанию текст = 3 куплета + бридж + припев (повторяется).
5. Если пользователь просит изменить текст — меняй ТОЛЬКО то, что просят, остальное оставляй.
6. Не задавай лишних вопросов. Если темы недостаточно — запроси ТОЛЬКО недостающее одним коротким вопросом.
7. В конце каждого готового текста ОБЯЗАТЕЛЬНО добавь строку: [ТЕКСТ_ГОТОВ]
8. Если пользователь просит указать стиль музыки — подбирай 1-2 слова (pop, rock, hip-hop, electronic, lo-fi, orchestral, ambient и т.д.)

Пример хорошего ответа:
"Тема: любовь и расставание. Жанр: pop.
[КУПЛЕТ 1]
Текст...
[ПРИПЕВ]
Текст...
[ТЕКСТ_ГОТОВ]"

Запомни: ты помощник для Suno, а не поэт-философ. Быстро, чётко, по делу."""

def get_generate_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎵 Сгенерировать песню", callback_data="confirm_generate")]
    ])

def get_regenerate_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Попробовать ещё раз", callback_data="regenerate_song")]
    ])

def get_manual_lyrics_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Ввести текст вручную", callback_data="manual_lyrics")]
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
        await message.answer("❌ У вас недостаточно средств. Пополните баланс, чтобы создавать песни.", reply_markup=keyboard)
        return
    if not await can_generate():
        await message.answer("❌ Месячный лимит генераций для бота исчерпан. Попробуйте позже.")
        return
    
    await message.answer(
        "✍️ **О чем будет ваша песня?**\n\n"
        "Напишите тему, настроение, жанр.\n"
        "Примеры:\n"
        "- «Грустная песня про любовь, поп»\n"
        "- «Энергичный трек про успех, рэп»\n"
        "- «Осенний дождь и одиночество, инди»\n\n"
        "Или сразу отправьте свой текст — я передам его в Suno.",
        parse_mode="Markdown"
    )
    await state.set_state(SongCreation.waiting_for_theme)

@router.message(SongCreation.waiting_for_theme)
async def theme_received(message: types.Message, state: FSMContext):
    user_input = message.text
    await state.update_data(original_theme=user_input)
    
    # Формируем историю с системным промптом
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Напиши текст песни на тему: {user_input}. По умолчанию: 3 куплета, бридж, припев. Жанр подбери сам."}
    ]
    
    await message.answer("🎤 **Генерирую текст...**")
    
    response = await get_lyrics(messages)
    await state.update_data(deepseek_messages=messages + [{"role": "assistant", "content": response}])
    
    if "[ТЕКСТ_ГОТОВ]" in response:
        clean_text = response.replace("[ТЕКСТ_ГОТОВ]", "").strip()
        await state.update_data(generated_lyrics=clean_text)
        await message.answer(
            f"📝 **Текст готов:**\n\n{clean_text}\n\nЕсли хотите изменить — напишите, что именно. Если всё устраивает — нажмите кнопку.",
            reply_markup=get_generate_keyboard()
        )
        await state.set_state(SongCreation.chatting_with_deepseek)
    else:
        await message.answer(response)
        await state.set_state(SongCreation.chatting_with_deepseek)
        await state.update_data(deepseek_messages=messages + [{"role": "assistant", "content": response}])

@router.message(SongCreation.chatting_with_deepseek)
async def chat_with_deepseek(message: types.Message, state: FSMContext):
    user_input = message.text
    data = await state.get_data()
    deepseek_messages = data.get("deepseek_messages", [])
    
    deepseek_messages.append({"role": "user", "content": user_input})
    response = await get_lyrics(deepseek_messages)
    deepseek_messages.append({"role": "assistant", "content": response})
    await state.update_data(deepseek_messages=deepseek_messages)
    
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
    """Общая функция для генерации музыки и отправки аудио"""
    data = await state.get_data()
    lyrics = data.get("generated_lyrics")
    
    if not lyrics:
        await callback.message.answer("❌ Текст песни не найден. Попробуйте начать заново: /generate")
        return False
    
    async with async_session_maker() as session:
        balance = await get_user_balance(session, user_id)
    if balance <= 0:
        await callback.message.answer("❌ Недостаточно средств.")
        return False
    if not await can_generate():
        await callback.message.answer("❌ Месячный лимит генераций исчерпан.")
        return False
    
    msg = await callback.message.answer("🎵 **Генерирую музыку через Suno...**\n\n_Это может занять до 5 минут_", parse_mode="Markdown")
    
    # Генерация через Suno
    style = data.get("style", "pop")
    vocal = data.get("vocal", "male")
    
    audio1, audio2 = await suno.generate(lyrics, style, vocal)
    await msg.delete()
    
    if not audio1 or not audio2:
        await callback.message.answer("❌ Ошибка генерации. Попробуйте позже.")
        return False
    
    async with async_session_maker() as session:
        success = await deduct_balance(session, user_id, 1)
        if success:
            user = await get_or_create_user(session, user_id)
            await save_generation(session, user.id, lyrics, style, vocal, audio1, audio2)
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
        f"Не понравились варианты? Нажмите кнопку, чтобы попробовать ещё раз (будет списана ещё одна генерация).",
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
        await callback.message.answer("❌ Нет сохранённого текста для регенерации. Попробуйте создать новую песню через /generate")
        await callback.answer()
        return
    
    await state.update_data(generated_lyrics=lyrics, style="pop", vocal="male")
    
    success = await generate_and_send_audio(callback, state, user_id)
    if success:
        await state.clear()
    await callback.answer()

@router.callback_query(F.data == "manual_lyrics")
async def manual_lyrics_input(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✍️ **Введите текст песни вручную.**\n\n"
        "Напишите текст целиком. Suno сам подберёт музыку.\n"
        "Формат не важен, но чем структурированнее текст — тем лучше результат."
    )
    await state.set_state(SongCreation.waiting_for_manual_lyrics)
    await callback.answer()

@router.message(SongCreation.waiting_for_manual_lyrics)
async def manual_lyrics_received(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lyrics = message.text
    
    if len(lyrics) < 20:
        await message.answer("❌ Текст слишком короткий. Напишите хотя бы 2-3 строки.")
        return
    
    await state.update_data(generated_lyrics=lyrics)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎵 Сгенерировать песню", callback_data="confirm_generate")]
    ])
    await message.answer(
        f"📝 **Текст сохранён:**\n\n{lyrics[:500]}{'...' if len(lyrics) > 500 else ''}\n\nТеперь можно сгенерировать музыку.",
        reply_markup=keyboard
    )
    await state.set_state(SongCreation.chatting_with_deepseek)
