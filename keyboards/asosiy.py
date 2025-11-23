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
    # a4="Ajal_game_test_bot"
    a5="ajal_oyini_alisa_bot"
    
    # a3="ustoz_shogirt10_bot"
    buttons = [
        [
            InlineKeyboardButton(
                text="➕ Botni guruhga qo'shish",
                url=f"https://t.me/{a5}?startgroup=true"
            )
        ],
        [
            InlineKeyboardButton(text="📜 Guruhlarni ko'rish", callback_data=f"guruhlar"),
        ],[
            InlineKeyboardButton(text="Yangiliklar", url="https://t.me/Alisa_Borderland"),
        ],[
            InlineKeyboardButton(text="👤 Profile", callback_data=f"profile"),
            InlineKeyboardButton(text="💎 Olmoslar", callback_data=f"shop:diamonds")
        ],[
            InlineKeyboardButton(text="🌐 Tilni o'zgartirish", callback_data="lang"),
        ],[
            InlineKeyboardButton(text=" 🏰 Clan", callback_data="asosiy_clan")
        ]
    ]
    # if False: 
    buttons.append([
            InlineKeyboardButton(text="🏆 Battle", callback_data="asosiy_battle")
        ])



    return InlineKeyboardMarkup(inline_keyboard=buttons)
