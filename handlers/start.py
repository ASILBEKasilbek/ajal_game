# handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from database.user_models import get_user, save_user
from database.db import init_db
from locales import t
from keyboards.asosiy import lang_keyboard, main_menu
import random
from config import CLANS

router = Router()

init_db()
# @router.message(CommandStart(deep_link=True))
# async def start_with_game(message: Message, deep_link: str):
#     if deep_link == "game":
#         user_id = message.from_user.id
#         await message.answer("🎮 Siz o‘yinga qo‘shildingiz!")

@router.callback_query(F.data == "start")
async def back_to_start(callback: CallbackQuery):
    user_id=callback.from_user.id
    await callback.message.answer(
        "Botni guruhga qo'shish uchun quyidagi tugmani bosing:",
        reply_markup=main_menu()
    )
    await callback.answer()
from aiogram.filters import Command

from .admin import show_admin_panel

@router.message(Command(commands=["admin"], ignore_case=True, ignore_mention=True))
async def cmd_admin(message: Message):
    await show_admin_panel(message)
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