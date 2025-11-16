from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from database.user_models import get_guruhlar

router = Router()

@router.callback_query(F.data == "guruhlar")
async def back_to_start(callback: CallbackQuery):
    # guruhlar = get_guruhlar()   # ["https://t.me/Ajal_oyini_chat"]
    guruhlar = [
    ("Ajal o‘yini chat", "https://t.me/Ajal_oyini_chat")
]


    buttons = []
    bot = callback.bot   # Bot obyektini olish

    for guruh in guruhlar:
        # link = guruh.strip()

        # # linkdan username olish
        # username = link.replace("https://t.me/", "").replace("@", "").strip()

        # # Telegramdan guruh nomini olish
        # chat = await bot.get_chat(username)
        name = guruh[0]
        link = guruh[1]

        buttons.append([
            InlineKeyboardButton(text=name, url=link)
        ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Ortga", callback_data="start")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(
        "📜 Tasdiqlangan guruhlar:",
        reply_markup=keyboard
    )
    await callback.answer()
