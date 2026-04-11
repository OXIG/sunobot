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
        "✍️ **О чём будет ваша песня?**\n\n"
        "Напишите тему, идею, настроение — я помогу создать текст.\n"
        "Вы также можете сразу написать свой текст, и я подберу к нему музыку.",
        parse_mode="Markdown"
    )
    await state.set_state(SongCreation.waiting_for_theme)

@router.message(SongCreation.waiting_for_theme)
async def theme_received(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_input = message.text
    
    await state.update_data(original_theme=user_input)
    
    messages = [
        {"role": "system", "content": "Ты — голосовой помощник для написания песен. Твоя задача — помочь пользователю написать текст песни. Общайся дружелюбно, предлагай варианты, уточняй жанр и настроение. Когда текст будет готов, напиши его в сообщении и добавь в конце строку: [ТЕКСТ_ГОТОВ]. Не пиши эту строку, пока текст не согласован полностью."},
        {"role": "user", "content": f"Вот идея для песни: {user_input}. Помоги написать текст. Спрашивай уточняющие вопросы, предлагай варианты."}
    ]
    
    await message.answer("🎤 **Работаю над текстом...**\n\nЯ задам несколько вопросов, чтобы текст получился именно таким, как вы хотите.")
    
    response = await get_lyrics(messages)
    await state.update_data(deepseek_messages=messages + [{"role": "assistant", "content": response}])
    
    if "[ТЕКСТ_ГОТОВ]" in response:
        clean_text = response.replace("[ТЕКСТ_ГОТОВ]", "").strip()
        await state.update_data(generated_lyrics=clean_text)
        await message.answer(
            f"📝 **Вот что получилось:**\n\n{clean_text}\n\nЕсли хотите изменить текст, просто напишите свои пожелания. Если всё устраивает — нажмите кнопку.",
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
    
    # Анимированное уведомление
    msg = await callback.message.answer("🐱 **Печатающий кот трудится...**\n\n_Генерация началась_", parse_mode="Markdown")
    
    frames = [
        "🐱‍💻 **Генерация началась...**",
        "🐱‍👤 **Создаю мелодию...**",
        "🐱‍🎤 **Добавляю вокал...**",
        "🐱‍🏍 **Почти готово!**",
        "🐱‍🚀 **Завершаю...**"
    ]
    for frame in frames:
        await asyncio.sleep(2)
        await msg.edit_text(f"{frame}\n\n_Пожалуйста, подождите..._", parse_mode="Markdown")
    
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
            last_lyrics_cache[user_id] = lyrics  # сохраняем для регенерации
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
    
    # Восстанавливаем текст в состояние
    await state.update_data(generated_lyrics=lyrics, style="pop", vocal="male")
    
    success = await generate_and_send_audio(callback, state, user_id)
    if success:
        await state.clear()
    await callback.answer()

@router.callback_query(F.data == "manual_lyrics")
async def manual_lyrics_input(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✍️ **Введите текст песни вручную.**\n\n"
        "Напишите текст целиком, а я передам его в Suno для создания музыки.\n"
        "Не забудьте указать жанр и тип вокала в тексте (например, «поп, женский вокал»)."
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
        f"📝 **Текст сохранён:**\n\n{lyrics}\n\nТеперь можно сгенерировать музыку.",
        reply_markup=keyboard
    )
    await state.set_state(SongCreation.chatting_with_deepseek)
