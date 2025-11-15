# handlers/admin.py
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    Message, InlineKeyboardButton as IB
)
from aiogram.filters import Command, CommandStart
import sqlite3
import asyncio
from config import ADMIN_IDS, DB_FILE

router = Router()

# ------------------- Yordamchi funksiyalar -------------------
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

def add_row(table: str, column_values: dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    columns = ", ".join(column_values.keys())
    placeholders = ", ".join("?" for _ in column_values)
    values = tuple(column_values.values())
    c.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
    conn.commit()
    conn.close()

def create_keyboard(rows: list[tuple], table: str, column: str) -> InlineKeyboardMarkup:
    buttons = [
        [IB(text=str(row[0]), callback_data=f"del_{table}_{column}_{row[0]}")]
        for row in rows
    ]
    buttons.append([IB(text="Ortga", callback_data="admin_group_management")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_channel_list(callback: CallbackQuery, table: str, column: str, title: str):
    rows = get_rows(table, column)
    if not rows:
        await callback.message.answer(f"{title} mavjud emas.")
        return
    keyboard = create_keyboard(rows, table, column)
    await callback.message.answer(f"{title} ro'yxati:", reply_markup=keyboard)

# ------------------- Admin panel (umumiy) -------------------
async def show_admin_panel(target):
    user_id = target.from_user.id
    if not is_admin(user_id):
        if isinstance(target, Message):
            await target.answer("Sizda admin huquqi yo'q.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [IB(text="Foydalanuvchilar ro'yxati", callback_data="user_list")],
        [IB(text="Statistika", callback_data="admin_stats")],
        [IB(text="Reklama", callback_data="admin_ads")],
        [IB(text="Guruhlar boshqaruvi", callback_data="admin_group_management")],
        [IB(text="Ortga", callback_data="start")]
    ])

    text = "Admin paneliga xush kelibsiz!"
    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=keyboard)
        await target.answer()
    else:
        await target.answer(text, reply_markup=keyboard)

# ------------------- 1. /admin KOMANDASI (TUG'IRLANDI) -------------------
@router.message(Command(commands=["admin"], ignore_case=True, ignore_mention=True))
async def cmd_admin(message: Message):
    await show_admin_panel(message)

# Callback orqali
@router.callback_query(F.data == "admin")
async def cb_admin(callback: CallbackQuery):
    await show_admin_panel(callback)

# ------------------- 2. KANAL QO‘ShISH KOMANDALARI (TUG'IRLANDI) -------------------
@router.message(Command(commands=["add_payment"], ignore_case=True, ignore_mention=True))
async def add_payment_channel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Ruxsat yo'q.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Masalan: `/add_payment 123456789`", parse_mode="Markdown")
        return

    try:
        kanal_id = int(args[1].strip())
        add_row("tulov_kanallar", {"kanal_id": kanal_id})
        await message.answer(f"To'lov kanali qo'shildi: `{kanal_id}`", parse_mode="Markdown")
    except ValueError:
        await message.answer("Kanal ID faqat raqam bo'lishi kerak!")

@router.message(Command(commands=["add_mandatory"], ignore_case=True, ignore_mention=True))
async def add_mandatory_channel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Ruxsat yo'q.")
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.answer("Masalan: `/add_mandatory 123456789 https://t.me/example`", parse_mode="Markdown")
        return

    try:
        kanal_id = int(args[1].strip())
        kanal_link = args[2].strip() if len(args) > 2 else "Nomalum"
        add_row("majburiy_kanallar", {"kanal_id": kanal_id, "kanal_link": kanal_link})
        await message.answer(f"Majburiy kanal qo'shildi:\nID: `{kanal_id}`\nLink: {kanal_link}", parse_mode="Markdown")
    except ValueError:
        await message.answer("Kanal ID faqat raqam bo'lishi kerak!")

# ------------------- 3. Foydalanuvchilar ro'yxati -------------------
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
        buttons.append(IB(text="Oldingi", callback_data=f"users_page_{page-1}"))
    if (page + 1) * PAGE_SIZE < total:
        buttons.append(IB(text="Keyingi", callback_data=f"users_page_{page+1}"))
    buttons.append(IB(text="Ortga", callback_data="admin"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

@router.callback_query(F.data == "user_list")
async def user_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    rows, total = get_users_page(0)
    if not rows:
        await callback.message.answer("Foydalanuvchilar hali yo'q.")
        await callback.answer()
        return

    text = f"Foydalanuvchilar ro'yxati (1–{min(PAGE_SIZE, total)} / {total})\n\n"
    for row in rows:
        uid, uname, fname, lvl, xp, olmos, balls = row
        uname = f"@{uname}" if uname else ""
        text += f"• <a href='tg://user?id={uid}'>{fname or 'NoName'}</a> {uname}\n"
        text += f"   ID: <code>{uid}</code> | Lvl: {lvl} | XP: {xp} | {olmos} | {balls}\n\n"

    keyboard = users_keyboard(0, total)
    await callback.message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)
    await callback.answer()

@router.callback_query(F.data.startswith("users_page_"))
async def users_page(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    page = int(callback.data.split("_")[-1])
    rows, total = get_users_page(page)
    if not rows:
        await callback.answer("Bu sahifa bo'sh.", show_alert=True)
        return

    text = f"Foydalanuvchilar ro'yxati ({page*PAGE_SIZE + 1}–{min((page+1)*PAGE_SIZE, total)} / {total})\n\n"
    for row in rows:
        uid, uname, fname, lvl, xp, olmos, balls = row
        uname = f"@{uname}" if uname else ""
        text += f"• <a href='tg://user?id={uid}'>{fname or 'NoName'}</a> {uname}\n"
        text += f"   ID: <code>{uid}</code> | Lvl: {lvl} | XP: {xp} | {olmos} | {balls}\n\n"

    keyboard = users_keyboard(page, total)
    await callback.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    await callback.answer()

# ------------------- 4. Statistika -------------------
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users"); total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE last_active >= date('now', '-1 day')"); active_today = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM clans"); total_clans = c.fetchone()[0]
    c.execute("SELECT SUM(wins) FROM users"); total_wins = c.fetchone()[0] or 0
    c.execute("SELECT SUM(total_games) FROM users"); total_games = c.fetchone()[0] or 0
    conn.close()

    text = f"""**Bot Statistika**

Jami foydalanuvchilar: `{total_users}`
Bugun faol: `{active_today}`
Jami o‘yinlar: `{total_games}`
Jami g‘alabalar: `{total_wins}`
Klanning soni: `{total_clans}`
"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[IB(text="Ortga", callback_data="admin")]])
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

# ------------------- 5. Reklama (Broadcast) -------------------
ads_state = {}

@router.callback_query(F.data == "admin_ads")
async def admin_ads(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [IB(text="Xabar yuborish", callback_data="ads_send")],
        [IB(text="Ortga", callback_data="admin")]
    ])
    await callback.message.answer("Reklama yuborish bo‘limi.\nXabar yuborish uchun tugmani bosing.", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "ads_send")
async def ads_send(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    ads_state[callback.from_user.id] = True
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[IB(text="Bekor qilish", callback_data="ads_cancel")]])
    await callback.message.answer(
        "Reklama xabarini yuboring (matn, rasm, video va h.k.).\n"
        "Yuborilgandan keyin barcha foydalanuvchilarga yuboriladi.",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "ads_cancel")
async def ads_cancel(callback: CallbackQuery):
    ads_state.pop(callback.from_user.id, None)
    await callback.message.edit_text("Reklama bekor qilindi.")
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
        except Exception:
            failed += 1
        await asyncio.sleep(0.04)

    result = f"Yuborildi: {success}\nXato: {failed}"
    await message.answer(result)
    ads_state.pop(user_id, None)
    await message.answer("Reklama yuborildi!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[IB(text="Ortga", callback_data="admin")]]))

# ------------------- 6. Guruhlar boshqaruvi -------------------
@router.callback_query(F.data == "admin_group_management")
async def group_management(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [IB(text="Majburiy kanal", callback_data="mandatory_channel_list")],
        [IB(text="To'lov kanal", callback_data="payment_channel_list")],
        [IB(text="O'yin kanal", callback_data="game_channel_list")],
        [IB(text="Ortga", callback_data="admin")]
    ])
    await callback.message.answer("Guruhlar boshqaruvi bo'limi:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "payment_channel_list")
async def payment_channel_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    await send_channel_list(callback, "tulov_kanallar", "kanal_id", "To'lov kanallari")
    await callback.answer()

@router.callback_query(F.data == "mandatory_channel_list")
async def mandatory_channel_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    await send_channel_list(callback, "majburiy_kanallar", "kanal_id", "Majburiy kanallar")
    await callback.answer()

@router.callback_query(F.data == "game_channel_list")
async def game_channel_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    await send_channel_list(callback, "games", "chat_id", "O'yin kanallari")
    await callback.answer()

@router.callback_query(F.data.startswith("del_"))
async def delete_channel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    try:
        _, table, column, value = callback.data.split("_", 3)
        delete_row(table, column, value)
        await callback.message.edit_text(f"'{value}' o'chirildi!")
        await send_channel_list(callback, table, column, f"{table} yangilandi")
    except Exception:
        await callback.message.edit_text("Xatolik yuz berdi.")
    await callback.answer()