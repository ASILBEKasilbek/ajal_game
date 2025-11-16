from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.db import all_clans, show_clan, create_clan, join_clan, get_user, remove_olmos, DB_FILE
from locales import t
import sqlite3

router = Router()

# --- FSM for creating clan ---
class ClanCreateState(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    waiting_group = State()
    waiting_channel = State()


# --- Barcha klanlar ro‘yxati ---
@router.callback_query(F.data == "clan:all")
async def show_all_clans(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    clans = all_clans()

    if not clans:
        await callback.message.edit_text(
            "🏰 *Hozircha hech qanday klan yaratilmagan.*\n\n"
            "Siz birinchilardan bo‘lib o‘z klanningizni yarating!",
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for clan in clans:
        button_text = (
            f"🏰 {clan['clan_name']}\n"
            f"   ├ 📊 LVL {clan['clan_level']} | 👥 {clan['members_count']} azo\n"
            f"   └ 👑 {clan['creator_id']}"  # Lider ID (keyin username qo‘shsa bo‘ladi)
        )
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"clan:show:{clan['clan_name']}"
            )
        ])

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Ortga", callback_data="asosiy_clan")
    ])

    await callback.message.edit_text(
        "📜 *Barcha klanlar ro‘yxati:*\n\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


# --- Bitta klan ko‘rsatish ---
@router.callback_query(F.data.startswith("clan:show:"))
async def show_specific_clan(callback: CallbackQuery):
    _, _, clan_name = callback.data.split(":", 2)
    clan = show_clan(clan_name)
    user = get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"

    if not clan:
        await callback.answer("❌ Klan topilmadi!", show_alert=True)
        return

    # Lider ismini olish (agar kerak bo‘lsa)
    creator = get_user(clan['creator_id'])
    creator_name = creator["first_name"] if creator else "Noma'lum"

    text = (
        f"🏰 *Klan: {clan['clan_name']}*\n\n"
        f"📊 *Daraja:* {clan['clan_level']} | 👥 *A'zolar:* {clan['members_count']}\n"
        f"👑 *Lider:* [{creator_name}](tg://user?id={clan['creator_id']})\n\n"
        f"📜 *Ta'rif:*\n{clan['clan_description']}\n\n"
        f"👥 *Guruh:* {clan['clan_group']}\n"
        f"📢 *Kanal:* {clan['clan_channel']}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 Qo‘shilish", callback_data=f"clan:join:{clan['clan_name']}")],
        [InlineKeyboardButton(text="📜 Barcha klanlar", callback_data="clan:all")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="asosiy_clan")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
    await callback.answer()


# --- Qo‘shilish ---
@router.callback_query(F.data.startswith("clan:join:"))
async def join_clan_handler(callback: CallbackQuery):
    _, _, clan_name = callback.data.split(":", 2)
    user = get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"

    success = join_clan(callback.from_user.id, clan_name)
    if success:
        await callback.answer("✅ Klanga muvaffaqiyatli qo‘shildingiz!", show_alert=True)
        # Yangi ma'lumot bilan yangilash
        await show_specific_clan(callback)
    else:
        await callback.answer("❌ Siz allaqachon klanga a'zosiz yoki klan to‘lgan!", show_alert=True)


# --- Klan yaratish boshlash ---
@router.callback_query(F.data == "create_clan")
async def start_create_clan(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"

    if user["olmos"] < 1:
        await callback.answer("❌ Yetarli olmos yo‘q! 1 olmos kerak.", show_alert=True)
        return

    await callback.message.answer(
        "✨ *Yangi klan yaratish jarayoni boshlandi!*\n\n"
        "🔹 *1-qadam:* Klan nomini yozing (3-20 belgi)\n"
        "Masalan: `Qora Qalpoq`, `Ajdarlar`",
        parse_mode="Markdown"
    )
    await state.set_state(ClanCreateState.waiting_name)
    await callback.answer()


# --- 1. Nom olish ---
@router.message(ClanCreateState.waiting_name)
async def receive_clan_name(message: Message, state: FSMContext):
    clan_name = message.text.strip()
    if len(clan_name) < 3 or len(clan_name) > 20:
        await message.answer("❌ Nomi 3-20 belgi oralig‘ida bo‘lishi kerak!\nQayta yozing:")
        return
    if not clan_name.replace(" ", "").isalnum() and " " not in clan_name:
        await message.answer("❌ Nom faqat harf va raqamlardan iborat bo‘lishi kerak!")
        return

    await state.update_data(clan_name=clan_name)
    await message.answer(
        "✅ Nom qabul qilindi!\n\n"
        "🔹 *2-qadam:* Klan haqida qisqacha ta'rif yozing (maks 200 belgi)\n"
        "Masalan: `Biz eng kuchli jamoamiz!`",
        parse_mode="Markdown"
    )
    await state.set_state(ClanCreateState.waiting_description)


# --- 2. Ta'rif ---
@router.message(ClanCreateState.waiting_description)
async def receive_clan_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if len(description) > 200:
        await message.answer("❌ Ta'rif 200 belgidan oshmasin!")
        return

    await state.update_data(clan_description=description)
    await message.answer(
        "✅ Ta'rif qabul qilindi!\n\n"
        "🔹 *3-qadam:* Klan **guruhini** yuboring\n"
        "Masalan: `@MyClanChat` yoki `https://t.me/MyClanChat`",
        parse_mode="Markdown"
    )
    await state.set_state(ClanCreateState.waiting_group)


# --- 3. Guruh ---
@router.message(ClanCreateState.waiting_group)
async def receive_clan_group(message: Message, state: FSMContext):
    group = message.text.strip()
    if not (group.startswith("@") or "t.me/" in group):
        await message.answer("❌ Noto‘g‘ri format!\n"
                             "Masalan: `@MyClanGroup` yoki `https://t.me/joinchat/...`")
        return

    await state.update_data(clan_group=group)
    await message.answer(
        "✅ Guruh qabul qilindi!\n\n"
        "🔹 *4-qadam:* Klan **kanalini** yuboring\n"
        "Masalan: `@MyClanNews` yoki `https://t.me/MyClanNews`",
        parse_mode="Markdown"
    )
    await state.set_state(ClanCreateState.waiting_channel)


# --- 4. Kanal + Yaratish ---
@router.message(ClanCreateState.waiting_channel)
async def receive_clan_channel(message: Message, state: FSMContext):
    channel = message.text.strip()
    if not (channel.startswith("@") or "t.me/" in channel):
        await message.answer("❌ Noto‘g‘ri format!\n"
                             "Masalan: `@MyClanChannel` yoki `https://t.me/MyClan`")
        return

    data = await state.get_data()
    clan_name = data["clan_name"]
    clan_description = data["clan_description"]
    clan_group = data["clan_group"]

    if create_clan(clan_name, message.from_user.id, clan_description, clan_group, channel):
        remove_olmos(message.from_user.id, 1)

        # Lider ma'lumotlarini yangilash
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE users SET clan_name = ?, clan_role = 'Lider' WHERE user_id = ?",
                  (clan_name, message.from_user.id))
        conn.commit()
        conn.close()

        result_text = (
            f"🎉 *Klan muvaffaqiyatli yaratildi!*\n\n"
            f"🏰 *Nomi:* `{clan_name}`\n"
            f"📜 *Ta'rif:* {clan_description}\n"
            f"👥 *Guruh:* {clan_group}\n"
            f"📢 *Kanal:* {channel}\n\n"
            f"💎 *1 olmos hisobdan yechildi.*\n"
            f"👑 *Siz — klan liderisiz!*"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga o‘tish", url=channel if "t.me" in channel else f"t.me/{channel[1:]}")],
            [InlineKeyboardButton(text="👥 Guruhga o‘tish", url=clan_group if "t.me" in clan_group else f"t.me/{clan_group[1:]}")],
            [InlineKeyboardButton(text="🔙 Klan menyusiga", callback_data="asosiy_clan")]
        ])

        await message.answer(result_text, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await message.answer("❌ *Bu nomdagi klan allaqachon mavjud!*\nBoshqa nom tanlang.", parse_mode="Markdown")

    await state.clear()


# --- Asosiy Klan Menyusi ---
@router.callback_query(F.data == "asosiy_clan")
async def clan_menu(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Barcha klanlar", callback_data="clan:all")],
        [InlineKeyboardButton(text="➕ Klan yaratish (1 olmos)", callback_data="create_clan")],
        [InlineKeyboardButton(text="🔙 Asosiy menyuga", callback_data="start")]
    ])

    await callback.message.edit_text(
        "🏰 *Klanlar bo‘limi*\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()