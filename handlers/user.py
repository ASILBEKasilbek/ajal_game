from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from database.db import get_all_guruhlar  # database.py dagi funksiya

router = Router()


@router.callback_query(F.data == "guruhlar")
async def back_to_start(callback: CallbackQuery):
    guruhlar = get_all_guruhlar()

    buttons = []
    for guruh in guruhlar:
        buttons.append([
            InlineKeyboardButton(text=guruh['group_name'], url=guruh.get('group_link', '#'))
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
