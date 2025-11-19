# handlers/admin.py
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton as IB,
    Message
)
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import sqlite3
import asyncio
from config import ADMIN_IDS, DB_FILE
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from aiogram.utils.keyboard import InlineKeyboardBuilder
import math
import json
router = Router()

# ==================== YORDAMCHI FUNKSIYALAR ====================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def get_rows(table: str, columns: str = "*"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"SELECT {columns} FROM {table}")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_row(table: str, column: str, value):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"DELETE FROM {table} WHERE {column} = ?", (value,))
    conn.commit()
    conn.close()

def add_row(table: str, data: dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    values = tuple(data.values())
    c.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", values)
    conn.commit()
    conn.close()

# ==================== INLINE KEYBOARD YARATISH ====================

def create_list_keyboard(rows, table, id_col, name_col=None, del_prefix="del"):
    buttons = []
    for row in rows:
        item_id = row[0]
        display_text = str(row[1]) if name_col and len(row) > 1 else str(item_id)
        buttons.append([IB(text=f"🗑 {display_text}", callback_data=f"{del_prefix}_{table}_{id_col}_{item_id}")])
    buttons.append([IB(text="➕ Yangi qo'shish", callback_data=f"add_{table}")])
    buttons.append([IB(text="🔙 Ortga", callback_data="admin_group_management")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def show_list(callback: CallbackQuery, table: str, title: str, id_col: str, name_col=None, del_prefix="del"):
    rows = get_rows(table, f"{id_col}, {name_col}" if name_col else id_col)
    if not rows:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [IB(text="➕ Yangi qo'shish", callback_data=f"add_{table}")],
            [IB(text="🔙 Ortga", callback_data="admin_group_management")]
        ])
        await callback.message.edit_text(f"📋 <b>{title}</b>\n\n❌ Hali hech nima qo'shilmagan.", reply_markup=keyboard, parse_mode="HTML")
        return

    keyboard = create_list_keyboard(rows, table, id_col, name_col, del_prefix)
    await callback.message.answer(f"📋 <b>{title}:</b>", reply_markup=keyboard, parse_mode="HTML")

# ==================== FSM STATE ====================

class AddChannelState(StatesGroup):
    waiting_for_id = State()
    waiting_for_name = State()

# ==================== ADMIN PANEL ====================

async def show_admin_panel(target):
    user_id = target.from_user.id
    if not is_admin(user_id):
        await target.answer("🚫 Sizda admin huquqi yo'q!", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [IB(text="👥 Foydalanuvchilar", callback_data="user_list")],
        [IB(text="📊 Statistika", callback_data="admin_stats")],
        [IB(text="📢 Reklama", callback_data="admin_ads")],
        [IB(text="⚙️ Guruhlar boshqaruvi", callback_data="admin_group_management")],
        [IB(text="1 vs 1",callback_data="manage_1vs1")]
    ])

    text = "🔐 <b>Admin Paneli</b>\n\nKerakli bo'limni tanlang:"

    if isinstance(target, Message):
        await target.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await target.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await target.answer()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    await show_admin_panel(message)

@router.callback_query(F.data == "admin")
async def cb_admin(callback: CallbackQuery):
    await show_admin_panel(callback)

@router.callback_query(F.data == "admin_exit")
async def admin_exit(callback: CallbackQuery):
    await callback.message.edit_text("✅ Admin panel yopildi.")
    await callback.answer()


class Battle1v1State(StatesGroup):
    date = State()
    time = State()


BATTLES_PER_PAGE = 5

@router.callback_query(F.data.startswith("manage_1vs1"))
async def admin_manage(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫 Ruxsat yo'q!", show_alert=True)

    page = int(callback.data.split(":")[1]) if ":" in callback.data else 1

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, scheduled_time, status FROM battle_1vs1 ORDER BY status='started' DESC, scheduled_time ASC")
    battles = c.fetchall()
    conn.close()

    # Pagination
    total_pages = math.ceil(len(battles) / BATTLES_PER_PAGE)
    start_idx = (page - 1) * BATTLES_PER_PAGE
    end_idx = start_idx + BATTLES_PER_PAGE
    battles_page = battles[start_idx:end_idx]

    keyboard = []

    for battle_id, scheduled_time, status in battles_page:
        time_str = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M").strftime("%d %B %Y, %H:%M")
        status_emoji = "🟢" if status=="started" else "✅" if status=="finished" else "⏳"
        keyboard.append([IB(text=f"{status_emoji} Battle {battle_id} | {time_str}", callback_data=f"admin_1vs1_detail:{battle_id}")])

    # Paginate buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(IB(text="⬅️ Oldingi", callback_data=f"manage_1vs1:{page-1}"))
    if page < total_pages:
        nav_buttons.append(IB(text="Keyingi ➡️", callback_data=f"manage_1vs1:{page+1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Qo‘shimcha admin tugmalari
    keyboard.append([IB(text="📅 Yangi 1vs1 battle yaratish", callback_data="admin_1vs1")])
    keyboard.append([IB(text="🔙 Ortga", callback_data="admin")])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await callback.message.edit_text(
        "🎮 <b>1 vs 1 Battle boshqaruvi</b>\n\nBo'limni tanlang:",
        reply_markup=reply_markup, parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_1vs1_detail:"))
async def battle_detail(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫 Ruxsat yo'q!", show_alert=True)

    battle_id = int(callback.data.split(":")[1])

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Battle info
    c.execute("SELECT scheduled_time, status, players FROM battle_1vs1 WHERE id=?", (battle_id,))
    row = c.fetchone()
    if not row:
        await callback.answer("Battle topilmadi ❌", show_alert=True)
        conn.close()
        return

    scheduled_time, status, players_json = row
    players = json.loads(players_json)
    time_str = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M").strftime("%d %B %Y, %H:%M")
    
    # Pairs va ovozlar
    c.execute("SELECT player1, player2, votes1, votes2 FROM battle_pairs WHERE battle_id=?", (battle_id,))
    pairs = c.fetchall()
    conn.close()
    votes_dict = {}

    for p1, p2, v1, v2 in pairs:
        votes_dict[p1] = votes_dict.get(p1, 0) + v1
        if p2 != "bot":
            votes_dict[p2] = votes_dict.get(p2, 0) + v2

    top5_users = sorted(votes_dict.items(), key=lambda x: x[1], reverse=True)[:5]
    top5_ids = [user_id for user_id, _ in top5_users]

    text = f"<b>🎮 Battle {battle_id}</b>\n"
    text += f"⏱ Scheduled: {time_str}\n"
    text += f"📌 Status: {status}\n"
    text += f"👥 Qatnashchilar: {', '.join(str(p) for p in players)}\n\n"
    text += "<b>Top 5 eng ko'p ovoz olganlar:</b>\n"

    from database.battle_models import get_name_battle

    for p1, p2, v1, v2 in pairs:
        if (p1 in top5_ids) or (p2 in top5_ids):
            name1 = "Bot" if p1=="bot" else get_name_battle(p1)
            name2 = "Bot" if p2=="bot" else get_name_battle(p2)
            text += f"{name1}({v1})  🆚 {name2}({v2}) ovoz\n"

    # Admin action buttons
    # kb = InlineKeyboardMarkup(inline_keyboard=[
    #     [IB(text="✅ Start", callback_data=f"admin_1vs1_start:{battle_id}")],
    #     [IB(text="⏹ Finish", callback_data=f"admin_1vs1_finish:{battle_id}")],
    #     [IB(text="✏️ Edit", callback_data=f"admin_1vs1_edit:{battle_id}")],
    #     [IB(text="🗑 Delete", callback_data=f"admin_1vs1_delete:{battle_id}")],
    #     [IB(text="🔙 Ortga", callback_data="manage_1vs1")]
    # ])

    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

# --- BATTLE BOSHLASH ---
@router.callback_query(F.data == "admin_1vs1")
async def admin_1vs1_start(call: CallbackQuery, state: FSMContext):

    await state.set_state(Battle1v1State.date)

    calendar = await SimpleCalendar().start_calendar()
    await call.message.edit_text("📅 1vs1 sanasini tanlang:", reply_markup=calendar)

# --- SANA TANLANGANDA ---
@router.callback_query(SimpleCalendarCallback.filter(), Battle1v1State.date)
async def date_chosen(call: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(call, callback_data)

    if selected:
        await state.update_data(date=date)
        kb = InlineKeyboardBuilder()
        for h in range(0, 24):
            kb.button(text=f"{h:02d}:00", callback_data=f"hour:{h}")
        kb.adjust(4)
        await call.message.answer(f"📌 Sana: {date.strftime('%Y-%m-%d')}\n⏰ Endi soatni tanlang:", reply_markup=kb.as_markup())
        await state.set_state(Battle1v1State.time)


# --- SOAT TANLANGANDA ---
@router.callback_query(Battle1v1State.time, F.data.startswith("hour:"))
async def hour_selected(call: CallbackQuery, state: FSMContext):

    hour = int(call.data.split(":")[1])
    data = await state.get_data()
    date = data["date"]
    final = date.replace(hour=hour, minute=0)
    final_text = final.strftime("%Y-%m-%d %H:%M")

    await state.update_data(final_time=final_text)

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, tasdiqlayman", callback_data="confirm_1vs1")
    kb.button(text="❌ Yo‘q, bekor qilish", callback_data="cancel_1vs1")
    kb.adjust(1)

    await call.message.edit_text(
        f"📌 Tanlangan vaqt:\n<b>{final_text}</b>\n\nTasdiqlaysizmi?",
        reply_markup=kb.as_markup()
    )
@router.callback_query(F.data == "confirm_1vs1")
async def confirm_battle(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    final_time = data["final_time"]

    # DBga battle yaratamiz
    import sqlite3, json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO battle_1vs1 (scheduled_time, players) VALUES (?, ?)",
              (final_time, json.dumps([])))
    conn.commit()
    conn.close()

    await call.message.answer(
        f"🔥 1 vs 1 battle tasdiqlandi!\n⏰ Vaqt: <b>{final_time}</b>\n\n"
        "Endi foydalanuvchilarga yuboraymi?"
    )

    # Hamma userlarga yuboriladi — lekin admin tasdiqlasin
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Hamma userlarga yubor", callback_data="send_to_all_1vs1")
    kb.button(text="❌ Bekor qilish", callback_data="cancel_1vs1")
    kb.adjust(1)

    await call.message.answer("Davom etamizmi?", reply_markup=kb.as_markup())
    await state.clear()


@router.callback_query(F.data == "send_to_all_1vs1")
async def send_to_all(call: CallbackQuery, bot: Bot):
    import sqlite3

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Oxirgi battle-id
    c.execute("SELECT id, scheduled_time FROM battle_1vs1 ORDER BY id DESC LIMIT 1")
    battle_id, final_time = c.fetchone()
    conn.close()

    # Hamma userlar
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    users = c.execute("SELECT user_id FROM users").fetchall()
    conn.close()

    total = len(users)       # jami
    sent = 0                 # yuborilganlar
    failed = 0               # yuborilmaganlar

    for (user_id,) in users:
        kb = InlineKeyboardBuilder()
        kb.button(text="🏆 Ha, qatnashaman", callback_data=f"join_1vs1:{battle_id}")
        kb.button(text="❌ Yo‘q", callback_data="nojoin_1vs1")
        kb.adjust(1)

        try:
            await bot.send_message(
                user_id,
                f"🔥 1vs1 BATTLE e'lon qilindi!\n\n⏰ Vaqt: <b>{final_time}</b>\n"
                "Qatnashasizmi?",
                reply_markup=kb.as_markup()
            )
            sent += 1
        except:
            failed += 1
            continue

    # Admin uchun hisobot
    await call.message.answer(
        f"📢 Xabar yuborish yakunlandi.\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total}</b>\n"
        f"📨 Yuborildi: <b>{sent}</b>\n"
        f"❌ Yuborilmadi: <b>{failed}</b>"
    )

# ==================== GURUHLAR & KANALLAR BOSHQARUVI ====================

@router.callback_query(F.data == "admin_group_management")
async def group_management(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫 Ruxsat yo'q!", show_alert=True)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [IB(text="💳 To'lov kanallari", callback_data="list_tulov_kanallar")],
        [IB(text="🔗 Majburiy kanallar", callback_data="list_majburiy_kanallar")],
        [IB(text="📢 Umumiy kanallar", callback_data="list_kanallar")],
        [IB(text="👥 Guruhlar", callback_data="list_guruhlar")],
        [IB(text="🔙 Ortga", callback_data="admin")]
    ])

    await callback.message.edit_text(
        "⚙️ <b>Guruh va kanallar boshqaruvi</b>\n\nBo'limni tanlang:",
        reply_markup=keyboard, parse_mode="HTML"
    )
    await callback.answer()

# ==================== TO'LOV KANALLARI ====================

@router.callback_query(F.data == "list_tulov_kanallar")
async def list_tulov(callback: CallbackQuery):
    await show_list(callback, "tulov_kanallar", "To'lov kanallari", "kanal_id")

@router.callback_query(F.data == "add_tulov_kanallar")
async def add_tulov_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🔢 To'lov kanali <b>ID</b>sini yuboring:\n(masalan: <code>-1001234567890</code>)", parse_mode="HTML")
    await state.set_state(AddChannelState.waiting_for_id)
    await state.update_data(table="tulov_kanallar", id_col="kanal_id", title="To'lov kanali")
    await callback.answer()

# ==================== MAJBURIY KANALLAR ====================

@router.callback_query(F.data == "list_majburiy_kanallar")
async def list_majburiy(callback: CallbackQuery):
    await show_list(callback, "majburiy_kanallar", "Majburiy kanallar", "kanal_id", "kanal_link")

@router.callback_query(F.data == "add_majburiy_kanallar")
async def add_majburiy_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🔢 Majburiy kanal <b>ID</b>sini yuboring:", parse_mode="HTML")
    await state.set_state(AddChannelState.waiting_for_id)
    await state.update_data(table="majburiy_kanallar", id_col="kanal_id", name_col="kanal_link", title="Majburiy kanal")
    await callback.answer()

# ==================== UMUMIY KANALLAR ====================

@router.callback_query(F.data == "list_kanallar")
async def list_kanallar(callback: CallbackQuery):
    await show_list(callback, "kanallar", "Umumiy kanallar", "kanal_link", "kanal_name")

@router.callback_query(F.data == "add_kanallar")
async def add_kanallar_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📢 Kanal <b>linki</b>ni yuboring:\n(masalan: <code>https://t.me/mychannel</code>)", parse_mode="HTML")
    await state.set_state(AddChannelState.waiting_for_id)
    await state.update_data(table="kanallar", id_col="kanal_link", name_col="kanal_name", title="Umumiy kanal", is_link=True)
    await callback.answer()

# ==================== GURUHLAR ====================

@router.callback_query(F.data == "list_guruhlar")
async def list_guruhlar(callback: CallbackQuery):
    await show_list(callback, "guruhlar", "Guruhlar", "group_id", "group_name")

@router.callback_query(F.data == "add_guruhlar")
async def add_guruh_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🔢 Guruh <b>ID</b>sini yuboring:", parse_mode="HTML")
    await state.set_state(AddChannelState.waiting_for_id)
    await state.update_data(table="guruhlar", id_col="group_id", name_col="group_name", title="Guruh")
    await callback.answer()

# ==================== QO'SHISH LOGIKASI ====================

@router.message(AddChannelState.waiting_for_id)
async def get_id(message: Message, state: FSMContext):
    data = await state.get_data()
    text = message.text.strip()

    if data.get("is_link"):
        if not text.startswith("http"):
            return await message.answer("❌ Iltimos, to'g'ri link yuboring![](https://t.me/...)")
        await state.update_data(temp_id=text)
        await message.answer("📛 Endi kanal <b>nomini</b> yuboring:", parse_mode="HTML")
        await state.set_state(AddChannelState.waiting_for_name)
        return

    if not text.lstrip("-").isdigit():
        return await message.answer("❌ Faqat raqam kiriting! (masalan: -1001234567890)")

    await state.update_data(temp_id=int(text))
    name_col = data.get("name_col")
    if name_col:
        await message.answer(f"📛 Endi <b>{data['title']} nomini</b> yuboring:", parse_mode="HTML")
        await state.set_state(AddChannelState.waiting_for_name)
    else:
        await finish_add(message, state)

@router.message(AddChannelState.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await finish_add(message, state)

async def finish_add(message: Message, state: FSMContext):
    data = await state.get_data()
    temp_id = data["temp_id"]
    table = data["table"]
    id_col = data["id_col"]
    name_col = data.get("name_col")
    title = data["title"]

    row_data = {id_col: temp_id}
    if name_col:
        row_data[name_col] = message.text.strip()

    try:
        add_row(table, row_data)
        await message.answer(f"✅ <b>{title}</b> muvaffaqiyatli qo'shildi!", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")
    finally:
        await state.clear()

    # Yangilash
    dummy = type('obj', (), {'message': message, 'answer': lambda: None})()
    await show_list(dummy, table, f"{title}lar", id_col, name_col)

# ==================== O'CHIRISH ====================

@router.callback_query(F.data.startswith("del_"))
async def delete_item(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫 Ruxsat yo'q!", show_alert=True)

    try:
        _, table, id_col, value = callback.data.split("_", 3)
        delete_row(table, id_col, value)
        await callback.answer("🗑 O'chirildi!")
        await show_list(callback, table, table.replace("_", " ").title(), id_col)
    except Exception as e:
        await callback.answer("❌ Xatolik!")

# ==================== FOYDALANUVCHILAR RO'YXATI ====================

PAGE_SIZE = 10

def get_users_page(page: int = 0):
    offset = page * PAGE_SIZE
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT user_id, username, first_name, level, xp, olmos, balls
        FROM users ORDER BY user_id LIMIT ? OFFSET ?
    """, (PAGE_SIZE, offset))
    rows = c.fetchall()
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    conn.close()
    return rows, total

def users_keyboard(page: int, total: int):
    buttons = []
    if page > 0:
        buttons.append(IB(text="⬅️ Oldingi", callback_data=f"users_page_{page-1}"))
    if (page + 1) * PAGE_SIZE < total:
        buttons.append(IB(text="Keyingi ➡️", callback_data=f"users_page_{page+1}"))
    buttons.append(IB(text="🔙 Ortga", callback_data="admin"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

@router.callback_query(F.data == "user_list")
async def user_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫 Ruxsat yo'q!", show_alert=True)

    rows, total = get_users_page(0)
    if not rows:
        await callback.message.edit_text("👥 Foydalanuvchilar hali yo'q.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[IB("🔙 Ortga", callback_data="admin")]]))
        return

    text = f"👥 <b>Foydalanuvchilar (1–{min(PAGE_SIZE, total)} / {total})</b>\n\n"
    for row in rows:
        uid, uname, fname, lvl, xp, olmos, balls = row
        uname = f"@{uname}" if uname else ""
        text += f"• <a href='tg://user?id={uid}'>{fname or 'NoName'}</a> {uname}\n"
        text += f"   ID: <code>{uid}</code> | Lvl: {lvl} | XP: {xp} | 💎 {olmos} | 🎾 {balls}\n\n"

    keyboard = users_keyboard(0, total)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

@router.callback_query(F.data.startswith("users_page_"))
async def users_page(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫 Ruxsat yo'q!", show_alert=True)

    page = int(callback.data.split("_")[-1])
    rows, total = get_users_page(page)
    if not rows:
        return await callback.answer("Bu sahifa bo'sh.", show_alert=True)

    text = f"👥 <b>Foydalanuvchilar ({page*PAGE_SIZE + 1}–{min((page+1)*PAGE_SIZE, total)} / {total})</b>\n\n"
    for row in rows:
        uid, uname, fname, lvl, xp, olmos, balls = row
        uname = f"@{uname}" if uname else ""
        text += f"• <a href='tg://user?id={uid}'>{fname or 'NoName'}</a> {uname}\n"
        text += f"   ID: <code>{uid}</code> | Lvl: {lvl} | XP: {xp} | 💎 {olmos} | 🎾 {balls}\n\n"

    keyboard = users_keyboard(page, total)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

# ==================== STATISTIKA ====================

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫 Ruxsat yo'q!", show_alert=True)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users"); total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE last_active >= date('now', '-1 day')"); active_today = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM clans"); total_clans = c.fetchone()[0]
    c.execute("SELECT SUM(wins) FROM users"); total_wins = c.fetchone()[0] or 0
    c.execute("SELECT SUM(total_games) FROM users"); total_games = c.fetchone()[0] or 0
    conn.close()

    text = f"""📊 <b>Bot Statistika</b>

👥 Jami foydalanuvchilar: <code>{total_users}</code>
🟢 Bugun faol: <code>{active_today}</code>
🎮 Jami o‘yinlar: <code>{total_games}</code>
🏆 Jami g‘alabalar: <code>{total_wins}</code>
🏰 Klanning soni: <code>{total_clans}</code>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[IB(text="🔙 Ortga", callback_data="admin")]])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# ==================== REKLAMA ====================

ads_state = {}

@router.callback_query(F.data == "admin_ads")
async def admin_ads(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫 Ruxsat yo'q!", show_alert=True)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [IB(text="📩 Xabar yuborish", callback_data="ads_send")],
        [IB(text="🔙 Ortga", callback_data="admin")]
    ])
    await callback.message.edit_text("📢 <b>Reklama yuborish</b>\n\nXabar yuborish uchun tugmani bosing.", reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "ads_send")
async def ads_send(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    ads_state[callback.from_user.id] = True
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[IB(text="❌ Bekor qilish", callback_data="ads_cancel")]])
    await callback.message.edit_text(
        "📩 <b>Reklama xabarini yuboring</b>\n\n(matn, rasm, video, h.k.)\n\nYuborilgandan keyin barcha foydalanuvchilarga yuboriladi.",
        reply_markup=keyboard, parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "ads_cancel")
async def ads_cancel(callback: CallbackQuery):
    ads_state.pop(callback.from_user.id, None)
    await callback.message.edit_text("❌ Reklama bekor qilindi.")
    await callback.answer()

@router.message(lambda m: m.from_user.id in ads_state)
async def catch_ads_message(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in c.fetchall()]
    conn.close()

    success = 0
    failed = 0
    for uid in user_ids:
        try:
            await message.copy_to(uid)
            success += 1
        except:
            failed += 1
        await asyncio.sleep(0.04)

    result = f"✅ Yuborildi: <code>{success}</code>\n❌ Xato: <code>{failed}</code>"
    await message.answer(result, parse_mode="HTML")
    ads_state.pop(user_id, None)
    await message.answer("📢 Reklama yuborildi!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[IB(text="🔙 Ortga", callback_data="admin")]]))