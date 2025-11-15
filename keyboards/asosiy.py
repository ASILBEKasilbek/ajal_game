# keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_eng")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="start")]
    ])

def main_menu() -> InlineKeyboardMarkup:
    a="Healthy_Helper_robot"
    a1="ajal_oyini_alisa_bot"
    a2="Vision_care_robot"
    a3="mindx_uzbekistan_bot"
    # a3="ustoz_shogirt10_bot"
    buttons = [
        [
            InlineKeyboardButton(
                text="🤖 Botni guruhga qo'shish",
                url=f"https://t.me/{a3}?startgroup=true"
            )
        ],
        [
            InlineKeyboardButton(text="📜 Guruhlarni ko'rish", callback_data=f"profile"),
        ],[
            InlineKeyboardButton(text="Yangiliklar", url="https://t.me/Alisa_Borderland"),
        ],[
            InlineKeyboardButton(text="👤 Profile", callback_data=f"profile"),
            InlineKeyboardButton(text="💎 Olmoslar", callback_data=f"shop:diamonds")
        ],[
            InlineKeyboardButton(text="🌐 Tilni o'zgartirish", callback_data="lang"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Olmos sotib olish", callback_data=f"shop:diamonds")],
        [InlineKeyboardButton(text="Ballar", callback_data=f"balls_info")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="start")]
    ])
