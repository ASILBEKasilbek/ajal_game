# handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.user_models import get_user, save_user
from database.db import init_db
from locales import t
from keyboards.asosiy import lang_keyboard, main_menu
import random
import re
from config import CLANS,JOIN_TIME
from handlers.game import active_games, GameState, Player
from aiogram.types import CallbackQuery

router = Router()
init_db()

@router.message(CommandStart(deep_link=True))
async def handle_game_join(message: Message):
    args = message.text.split()
    if len(args) < 2:
        return

    command = args[1]
    match = re.match(r"game_(-?\d+)", command)
    if not match:
        return

    chat_id = int(match.group(1))
    user = message.from_user

    gs = active_games.get(chat_id)
    if not gs or gs.running:
        return await message.answer("Lobby yopilgan yoki o'yin boshlangan.")

    if user.id in gs.players:
        return await message.answer("Siz allaqachon qo'shilgansiz!")

    # Qo'shish
    gs.players[user.id] = Player(user_id=user.id, name=user.full_name)

    # Lobby yangilash
    try:
        bot_info = await message.bot.get_me()
        join_url = f"https://t.me/{bot_info.username}?start=game_{chat_id}"
        players_list = '\n'.join(f"{i+1}. {p.name}" for i, p in enumerate(gs.players.values()))
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="O'yinga qo'shilish", url=join_url)],
            [InlineKeyboardButton(text="Boshlash", callback_data="start_game_admin")]
        ])

        await message.bot.edit_message_text(
            chat_id=chat_id,
            message_id=gs.lobby_message_id,
            text=f"<b>AJAL O'YINI</b>\n\n"
                 f"Lobby {JOIN_TIME}s ochiq.\n\n"
                 f"<b>Ishtirokchilar ({len(gs.players)}):</b>\n{players_list}",
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Lobby update error: {e}")

    # Foydalanuvchiga tasdiq
    return await message.answer(
        "<b>Siz o'yinga muvaffaqiyatli qo'shildingiz!</b>\n\n"
        "O'yin boshlanishini kuting...\n"
        "Guruhga qaytish uchun pastdagi tugmani bosing.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Guruhga qaytish", url=f"t.me/c/{str(chat_id)[4:]}")
        ]]),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "start")
async def back_to_start(callback: CallbackQuery):
    await callback.message.edit_text(
        "Botni guruhga qo'shish uchun quyidagi tugmani bosing:",
        reply_markup=main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "rasm_start")
async def back_to_start(callback: CallbackQuery):
    await callback.message.answer(
        "Botni guruhga qo'shish uchun quyidagi tugmani bosing:",
        reply_markup=main_menu()
    )
    await callback.answer()

@router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        clan = random.choice(CLANS)
        user = {
            "user_id": user_id,
            "username": message.from_user.username or "",
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name or "",
            "clan": clan,
            "language": "uz",
            "level": 1,
        }
        save_user(user)

    lang = user.get("language", "uz")
    if message.chat.type in ["group", "supergroup"]:
        await message.answer(t(lang, "choose_lang"), reply_markup=lang_keyboard())
    else:
        await message.answer(
            t(lang, "welcome", name=user["first_name"], level=user["level"]),
            reply_markup=main_menu()
        )