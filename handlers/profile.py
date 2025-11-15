# handlers/profile.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.user_models import get_user
from locales import t
from keyboards.asosiy import profile_keyboard
from aiogram.types import FSInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from aiogram.types import Message
import sqlite3
from datetime import datetime
from config import DB_FILE

router = Router()

def format_user_profile(user: dict, lang: str) -> str:
    if lang == "uz":
        profile_text = f"""
────────────────────────────
👤 <b>Sizning profilingiz</b>
────────────────────────────
📝 <b>Ism:</b> {user.get('first_name', 'Nomalum')} ({user.get('username', 'Nomalum')})
🆔 <b>ID:</b> {user.get('user_id', 'Nomalum')}
────────────────────────────
⚔️ <b>LVL:</b> {user.get('level', 0)} 💀 ({user.get('xp', 0)} HP)
🏆 <b>RANK:</b> {user.get('rank', 'Nomalum')}
────────────────────────────
💎 <b>Olmoslar:</b> {user.get('olmos', 0)}
🎁 <b>Ballar:</b> {user.get('balls', 0)}
💖 <b>PP (Mashhurlik):</b> {user.get('popularity', 0)} 🔺(+{user.get('popularity_today', 0)} bugun)
────────────────────────────
🎮 <b>Jami o‘yinlar:</b> {user.get('total_games', 0)}
🏆 <b>G‘alabalar:</b> {user.get('wins', 0)}
📊 <b>Reyting:</b> #{user.get('rating', 0)}
────────────────────────────
⚔️ <b>So‘nggi o‘yin natijasi:</b> {'✅ G‘alaba' if user.get('last_game_result') == 'win' else '❌ Mag‘lubiyat'} ({user.get('last_game_date', 'Nomalum')})
────────────────────────────
🧬 <b>Bio:</b> “{user.get('bio', 'Bio yozilmagan')}”  
────────────────────────────
🔗 <b>Kanal:</b> {user.get('channel', 'Nomalum')}
💬 <b>Guruh:</b> {user.get('user_group', 'Nomalum')}
────────────────────────────
👥 <b>Clan:</b> {user.get('clan_name', 'Yo‘q')}
🎖 <b>Clan roli:</b> {user.get('clan_role', 'Azo')}
🏅 <b>Clan LVL:</b> {user.get('clan_level', 0)} ({user.get('clan_xp', 0)} / {user.get('clan_xp_next', 800)} XP)
📊 <b>Clan reytingi:</b> #{user.get('clan_rank', 0)} / {user.get('total_clans', 0)} klan
🔗 <b>Clan Kanal:</b> {user.get('clan_channel', 'Nomalum')}
💬 <b>Clan Guruh:</b> {user.get('clan_group', 'Nomalum')}
────────────────────────────
🕒 <b>Oxirgi kirish:</b> {user.get('last_active', 'Nomalum')}
⏳ <b>Davringiz:</b> {(datetime.now()-datetime.strptime(user.get('created_at', 'Nomalum'), "%Y-%m-%d %H:%M:%S")).days} kun
🌐 <b>Til:</b> {user.get('language_code', '🇺🇿 UZ')}
────────────────────────────
    """.strip()

    elif lang == "eng":
        profile_text = f"""
────────────────────────────
👤 <b>Your Profile</b>
────────────────────────────
📝 <b>Name:</b> {user.get('first_name', 'Unknown')} ({user.get('username', 'Unknown')})
🆔 <b>ID:</b> {user.get('user_id', 'Unknown')}
────────────────────────────
⚔️ <b>LVL:</b> {user.get('level', 0)} 💀 ({user.get('xp', 0)} HP)
🏆 <b>RANK:</b> {user.get('rank', 'Unknown')}
────────────────────────────
💎 <b>Diamonds:</b> {user.get('olmos', 0)}
🎁 <b>Points:</b> {user.get('balls', 0)}
💖 <b>PP (Popularity):</b> {user.get('popularity', 0)} 🔺(+{user.get('popularity_today', 0)} today)
────────────────────────────
🎮 <b>Total Games:</b> {user.get('total_games', 0)}
🏆 <b>Wins:</b> {user.get('wins', 0)}
📊 <b>Rating:</b> #{user.get('rating', 0)}
────────────────────────────
⚔️ <b>Last Game Result:</b> {'✅ Win' if user.get('last_game_result') == 'win' else '❌ Defeat'} ({user.get('last_game_date', 'Unknown')})
────────────────────────────
🧬 <b>Bio:</b> “{user.get('bio', 'No bio written')}”
────────────────────────────
🔗 <b>Channel:</b> {user.get('channel', 'Unknown')}
💬 <b>Group:</b> {user.get('user_group', 'Unknown')}
────────────────────────────
👥 <b>Clan:</b> {user.get('clan_name', 'None')}
🎖 <b>Clan Role:</b> {user.get('clan_role', 'Member')}
🏅 <b>Clan LVL:</b> {user.get('clan_level', 0)} ({user.get('clan_xp', 0)} / {user.get('clan_xp_next', 800)} XP)
📊 <b>Clan Rank:</b> #{user.get('clan_rank', 0)} / {user.get('total_clans', 0)} clans
🔗 <b>Clan Channel:</b> {user.get('clan_channel', 'Unknown')}
💬 <b>Clan Group:</b> {user.get('clan_group', 'Unknown')}
────────────────────────────
🕒 <b>Last Active:</b> {user.get('last_active', 'Unknown')}
⏳ <b>Days in Game:</b> {(datetime.now()-datetime.strptime(user.get('created_at', 'Nomalum'), "%Y-%m-%d %H:%M:%S")).days} days
🌐 <b>Language:</b> {user.get('language_code', '🇬🇧 EN')}
────────────────────────────
    """.strip()

    elif lang == "ru":
        profile_text = f"""
────────────────────────────
👤 <b>Ваш профиль</b>
────────────────────────────
📝 <b>Имя:</b> {user.get('first_name', 'Неизвестно')} ({user.get('username', 'Неизвестно')})
🆔 <b>ID:</b> {user.get('user_id', 'Неизвестно')}
────────────────────────────
⚔️ <b>Уровень:</b> {user.get('level', 0)} 💀 ({user.get('xp', 0)} HP)
🏆 <b>Ранг:</b> {user.get('rank', 'Неизвестно')}
────────────────────────────
💎 <b>Алмазы:</b> {user.get('olmos', 0)}
🎁 <b>Очки:</b> {user.get('balls', 0)}
💖 <b>PP (Популярность):</b> {user.get('popularity', 0)} 🔺(+{user.get('popularity_today', 0)} сегодня)
────────────────────────────
🎮 <b>Всего игр:</b> {user.get('total_games', 0)}
🏆 <b>Победы:</b> {user.get('wins', 0)}
📊 <b>Рейтинг:</b> #{user.get('rating', 0)}
────────────────────────────
⚔️ <b>Последний результат:</b> {'✅ Победа' if user.get('last_game_result') == 'win' else '❌ Поражение'} ({user.get('last_game_date', 'Неизвестно')})
────────────────────────────
🧬 <b>Био:</b> “{user.get('bio', 'Био не указано')}”
────────────────────────────
🔗 <b>Канал:</b> {user.get('channel', 'Неизвестно')}
💬 <b>Группа:</b> {user.get('user_group', 'Неизвестно')}
────────────────────────────
👥 <b>Клан:</b> {user.get('clan_name', 'Нет')}
🎖 <b>Роль в клане:</b> {user.get('clan_role', 'Участник')}
🏅 <b>Уровень клана:</b> {user.get('clan_level', 0)} ({user.get('clan_xp', 0)} / {user.get('clan_xp_next', 800)} XP)
📊 <b>Рейтинг клана:</b> #{user.get('clan_rank', 0)} / {user.get('total_clans', 0)} кланов
🔗 <b>Канал клана:</b> {user.get('clan_channel', 'Неизвестно')}
💬 <b>Группа клана:</b> {user.get('clan_group', 'Неизвестно')}
────────────────────────────
🕒 <b>Последний вход:</b> {user.get('last_active', 'Неизвестно')}
⏳ <b>Дни в игре:</b> {(datetime.now()-datetime.strptime(user.get('created_at', 'Nomalum'), "%Y-%m-%d %H:%M:%S")).days} дней
🌐 <b>Язык:</b> {user.get('language_code', '🇷🇺 RU')}
────────────────────────────
    """.strip()

    else:
        profile_text = "❌ Unknown language selected."

    return profile_text


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    lang = user["language"]
    text1=format_user_profile(user,lang)
    photo = FSInputFile("ajal_image.jpg") 
    keyboard=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Profilini o'zgartirish", callback_data=f"profile_edit")]
        # [InlineKeyboardButton(text="🔙 Ortga", callback_data="start")]
    ])

    await callback.message.answer_photo(
            photo=photo,
            caption=text1,
            reply_markup=keyboard
        )
    

@router.callback_query(F.data == "profile_edit")
async def edit_profile(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    text = "Edit uchun profile bo'limini tanlang."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Username", callback_data="edit_username"), InlineKeyboardButton(text="Bio", callback_data="edit_bio")],
        [InlineKeyboardButton(text="Kanal", callback_data="edit_channel"), InlineKeyboardButton(text="Guruh", callback_data="edit_user_group")],
        [InlineKeyboardButton(text="Clan", callback_data="edit_clan_name"), InlineKeyboardButton(text="🔙 Ortga", callback_data="profile")]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard)

edit_states = {}

@router.callback_query(F.data.startswith("edit_"))
async def handle_profile_edit(callback: CallbackQuery):
    field = callback.data.replace("edit_", "")  
    if field == "user_group":
        field1 = "Guruh"
    elif field == "channel":
        field1 = "Kanal"
    elif field == "clan_name":
        field1 = "Clan"
    else:
        field1 = field.capitalize()
    await callback.message.answer(f"Yangi {field1} ni kiriting:")

    edit_states[callback.from_user.id] = field

@router.message()
async def save_profile_edit(message: Message):
    user_id = message.from_user.id
    if user_id in edit_states:
        field = edit_states.pop(user_id)
        value = message.text.strip()
        update_user_field(user_id, field, value)
        await message.answer(f"{field} muvaffaqiyatli yangilandi: {value}")

def get_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        columns = [col[0] for col in c.description]
        return dict(zip(columns, row))
    return None

def update_user_field(user_id: int, field: str, value):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, user_id))
    conn.commit()
    conn.close()