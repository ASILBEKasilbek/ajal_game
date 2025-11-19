from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from database.user_models import get_guruhlar

router = Router()

@router.callback_query(F.data == "guruhlar")
async def back_to_start(callback: CallbackQuery):
    guruhlar = [
    ("Ajal o'yini chat", "https://t.me/Ajal_oyini_chat")
]
    buttons = []
    bot = callback.bot 
    for guruh in guruhlar:
        name = guruh[0]
        link = guruh[1]

        buttons.append([
            InlineKeyboardButton(text=name, url=link)
        ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Ortga", callback_data="start")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        "📜 Tasdiqlangan guruhlar:",
        reply_markup=keyboard
    )
    await callback.answer()
