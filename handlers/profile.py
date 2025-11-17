# handlers/profile.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
# from database.user_models import get_user
from database.db import update_user_field,get_user
from locales import t
from datetime import datetime
import sqlite3
from config import DB_FILE

router = Router()

# ────────────────────── FSM States ──────────────────────
class ProfileEditStates(StatesGroup):
    waiting_for_value = State()

# ────────────────────── FORMAT PROFILE ──────────────────────
def format_user_profile(user: dict, lang: str) -> str:
    if lang == "uz":
        profile_text = f"""
────────────────────────────
👤 <b>Sizning profilingiz</b>
────────────────────────────
📝 <b>Ism:</b> {user.get('first_name', 'Nomalum')} (@{user.get('username', 'Nomalum')})
🆔 <b>ID:</b> {user.get('user_id', 'Nomalum')}
────────────────────────────
⚔️ <b>LVL:</b> {user.get('level', 0)} 💀 ({user.get('xp', 0)} HP)
🏆 <b>RANK:</b> {user.get('rank', 'Nomalum')}
────────────────────────────
💎 <b>Olmoslar:</b> {user.get('olmos', 0)}
🎁 <b>Ballar:</b> {user.get('balls', 0)}
💖 <b>PP (Mashhurlik):</b> {user.get('popularity', 0)} 🔺(+{user.get('popularity_today', 0)} bugun)
────────────────────────────
🎮 <b>Jami o'yinlar:</b> {user.get('total_games', 0)}
🏆 <b>G'alabalar:</b> {user.get('wins', 0)}
📊 <b>Reyting:</b> #{user.get('rating', 0)}
────────────────────────────
⚔️ <b>So'nggi o'yin:</b> {"✅ G'alaba" if user.get('last_game_result') == 'win' else "❌ Mag'lubiyat"} ({user.get('last_game_date', 'Nomalum')})
────────────────────────────
🧬 <b>Bio:</b> "{user.get('bio', 'Bio yozilmagan')}"  
────────────────────────────
🔗 <b>Kanal:</b> {user.get('channel', 'Nomalum')}
💬 <b>Guruh:</b> {user.get('user_group', 'Nomalum')}
────────────────────────────
👥 <b>Clan:</b> {user.get('clan_name', 'Yoq')}
🎖 <b>Clan roli:</b> {user.get('clan_role', 'Azo')}
🏅 <b>Clan LVL:</b> {user.get('clan_level', 0)} ({user.get('clan_xp', 0)} / {user.get('clan_xp_next', 800)} XP)
📊 <b>Clan reytingi:</b> #{user.get('clan_rank', 0)} / {user.get('total_clans', 0)} klan
🔗 <b>Clan Kanal:</b> {user.get('clan_channel', 'Nomalum')}
💬 <b>Clan Guruh:</b> {user.get('clan_group', 'Nomalum')}
────────────────────────────
🕒 <b>Oxirgi kirish:</b> {user.get('last_active', 'Nomalum')}
⏳ <b>Davringiz:</b> {(datetime.now()-datetime.strptime(user.get('created_at', 'Nomalum'), "%Y-%m-%d %H:%M:%S")).days} kun
🌐 <b>Til:</b> {user.get('language', '🇺🇿 UZ')}
────────────────────────────
        """.strip()

    elif lang == "eng":
        profile_text = f"""
────────────────────────────
👤 <b>Your Profile</b>
────────────────────────────
📝 <b>Name:</b> {user.get('first_name', 'Unknown')} (@{user.get('username', 'Unknown')})
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
⚔️ <b>Last Game:</b> {'✅ Win' if user.get('last_game_result') == 'win' else '❌ Defeat'} ({user.get('last_game_date', 'Unknown')})
────────────────────────────
🧬 <b>Bio:</b> "{user.get('bio', 'No bio written')}"
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
🌐 <b>Language:</b> {user.get('language', '🇬🇧 EN')}
────────────────────────────
        """.strip()

    elif lang == "ru":
        profile_text = f"""
────────────────────────────
👤 <b>Ваш профиль</b>
────────────────────────────
📝 <b>Имя:</b> {user.get('first_name', 'Неизвестно')} (@{user.get('username', 'Неизвестно')})
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
🧬 <b>Био:</b> "{user.get('bio', 'Био не указано')}"
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
🌐 <b>Язык:</b> {user.get('language', '🇷🇺 RU')}
────────────────────────────
        """.strip()

    else:
        profile_text = "❌ Unknown language selected."

    return profile_text

# ────────────────────── SHOW PROFILE ──────────────────────
@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user:
        return await callback.answer("❌ Foydalanuvchi topilmadi!", show_alert=True)
    
    lang = user.get("language", "uz")
    text = format_user_profile(user, lang)
    
    try:
        photo = FSInputFile("ajal_image.jpg")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Profilni tahrirlash", callback_data="profile_edit")],
            [InlineKeyboardButton(text="🔙 Ortga", callback_data="rasm_start")]
        ])
        
        await callback.message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=keyboard
        )
        await callback.answer()
    except Exception as e:
        print(f"Profile show error: {e}")
        await callback.message.answer(text, reply_markup=keyboard)

# ────────────────────── EDIT PROFILE MENU ──────────────────────
@router.callback_query(F.data == "profile_edit")
async def edit_profile(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Username", callback_data="edit_username"),
            InlineKeyboardButton(text="🧬 Bio", callback_data="edit_bio")
        ],
        [
            InlineKeyboardButton(text="📢 Kanal", callback_data="edit_channel"),
            InlineKeyboardButton(text="💬 Guruh", callback_data="edit_user_group")
        ],
        [
            InlineKeyboardButton(text="👥 Clan", callback_data="edit_clan_name"),
            InlineKeyboardButton(text="🔙 Ortga", callback_data="profile")
        ]
    ])
    
    await callback.message.edit_caption(
        caption="✏️ <b>Tahrirlash uchun bo'limni tanlang:</b>",
        reply_markup=keyboard
    )
    await callback.answer()

# ────────────────────── EDIT FIELD START ──────────────────────
@router.callback_query(F.data.startswith("edit_"))
async def handle_profile_edit(callback: CallbackQuery, state: FSMContext):
    field = callback.data.replace("edit_", "")
    
    field_names = {
        "username": "Username",
        "bio": "Bio",
        "channel": "Kanal",
        "user_group": "Guruh",
        "clan_name": "Clan"
    }
    
    field_display = field_names.get(field, field.capitalize())
    
    await callback.message.answer(
        f"✏️ Yangi <b>{field_display}</b> kiriting:\n\n"
        f"<i>Bekor qilish uchun /cancel yuboring</i>",
        parse_mode="HTML"
    )
    
    await state.set_state(ProfileEditStates.waiting_for_value)
    await state.update_data(field=field)
    await callback.answer()

# ────────────────────── SAVE EDIT (FSM) ──────────────────────
@router.message(ProfileEditStates.waiting_for_value)
async def save_profile_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("field")
    
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("❌ Tahrirlash bekor qilindi.")
    
    value = message.text.strip()
    
    # Validation (optional)
    if len(value) > 200:
        return await message.answer("❌ Qiymat juda uzun! (max 200 belgi)")
    
    try:
        update_user_field(message.from_user.id, field, value)
        await message.answer(
            f"✅ <b>{field.replace('_', ' ').title()}</b> muvaffaqiyatli yangilandi!\n\n"
            f"📝 Yangi qiymat: <code>{value}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")
    finally:
        await state.clear()
