# handlers/clan.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.db import (
    all_clans, show_clan, create_clan, join_clan, get_user, remove_olmos, DB_FILE,
    get_clan_members, update_user_clan_role, leave_clan, kick_member,
    get_pending_requests, add_join_request, approve_request, reject_request,
    transfer_leadership, set_clan_join_type, get_clan_join_type
)
from locales import t
import sqlite3

router = Router()

# --- EMOJI ---
EMOJI = {
    "clan": "🏰", "create": "➕", "join": "➡️", "leave": "🚪",
    "leader": "👑", "co_leader": "🛡️", "member": "👤",
    "request": "📩", "open": "🔓", "settings": "⚙️",
    "kick": "👞", "promote": "⬆️", "transfer": "🔄",
    "check": "✅", "cross": "❌", "back": "⬅️", "info": "ℹ️"
}

# --- FSM ---
class ClanCreateState(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    waiting_group = State()
    waiting_channel = State()

# --- DB MIGRATSIYA ---
def migrate_clan_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA table_info(clans)")
    columns = [col[1] for col in c.fetchall()]
    if 'join_type' not in columns:
        c.execute("ALTER TABLE clans ADD COLUMN join_type TEXT DEFAULT 'open'")
    c.execute('''
        CREATE TABLE IF NOT EXISTS join_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clan_name TEXT,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    c.execute("UPDATE users SET clan_role = 'Lider' WHERE clan_role = 'Lider'")
    c.execute("UPDATE users SET clan_role = 'Azo' WHERE clan_role IN ('Azo', '', NULL)")
    conn.commit()
    conn.close()

migrate_clan_db()

# --- LINK NORMALIZATSIYA ---
def normalize_link(link: str) -> str:
    link = link.strip()
    if link.startswith("@"):
        return f"https://t.me/{link[1:]}"
    if "t.me/" in link:
        return link if link.startswith("http") else f"https://{link}"
    return f"https://t.me/{link.split('/')[-1]}"

# --- YORDAMCHI ---
def get_user_lang(callback: CallbackQuery | Message) -> str:
    user = get_user(callback.from_user.id)
    return user.get("lang", "uz")

def get_clan_keyboard(clan_name: str, user_id: int, lang: str, is_leader: bool = False, is_co: bool = False):
    join_type = get_clan_join_type(clan_name)
    join_text = t(lang, "clan_join_request") if join_type == "request" else t(lang, "clan_join_open")
    keyboard = [
        [InlineKeyboardButton(text=f"{EMOJI['join']} {join_text}", callback_data=f"clan:join:{clan_name}")],
        [InlineKeyboardButton(text=f"📋 {t(lang, 'clan_all_clans')}", callback_data="clan:all")]
    ]
    if is_leader or is_co:
        keyboard.append([InlineKeyboardButton(text=f"{EMOJI['settings']} {t(lang, 'clan_management')}", callback_data=f"clan:manage:{clan_name}")])
    keyboard.append([InlineKeyboardButton(text=f"{EMOJI['back']} {t(lang, 'back')}", callback_data="asosiy_clan")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# --- ASOSIY MENYU ---
@router.callback_query(F.data == "asosiy_clan")
async def clan_menu(callback: CallbackQuery):
    lang = get_user_lang(callback)
    user = get_user(callback.from_user.id)
    keyboard = []
    
    if user.get("clan_name"):
        keyboard.append([InlineKeyboardButton(text=f"{EMOJI['clan']} {t(lang, 'clan_my_clan')}", callback_data=f"clan:show:{user['clan_name']}")])
    
    keyboard += [
        [InlineKeyboardButton(text=f"📋 {t(lang, 'clan_all_clans')}", callback_data="clan:all")],
        [InlineKeyboardButton(text=f"{EMOJI['create']} {t(lang, 'clan_create')}", callback_data="create_clan")],
        [InlineKeyboardButton(text=f"{EMOJI['back']} {t(lang, 'main_menu')}", callback_data="start")]
    ]
    
    await callback.message.edit_text(
        f"*{EMOJI['clan']} {t(lang, 'clan_menu_title')}*\n\n{t(lang, 'clan_all_clans')} {t(lang, 'back')}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

# --- BARCHA KLANLAR ---
@router.callback_query(F.data == "clan:all")
async def show_all_clans(callback: CallbackQuery):
    lang = get_user_lang(callback)
    clans = all_clans()
    if not clans:
        await callback.message.edit_text(
            f"*{EMOJI['clan']} {t(lang, 'clan_no_clans')}*\n\n{EMOJI['create']} {t(lang, 'clan_create_first')}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"{EMOJI['back']} {t(lang, 'back')}", callback_data="asosiy_clan")]
            ])
        )
        return

    clans = clans[:8]
    keyboard = []
    for clan in clans:
        join_emoji = EMOJI['request'] if get_clan_join_type(clan['clan_name']) == "request" else EMOJI['open']
        join_text = t(lang, 'clan_join_request_type') if get_clan_join_type(clan['clan_name']) == "request" else t(lang, 'clan_join_open_type')
        button_text = f"{clan['clan_name']}\n   LVL {clan['clan_level']} | 👥 {clan['members_count']}/10 | {join_emoji} {join_text}"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"clan:show:{clan['clan_name']}")])
    
    keyboard.append([InlineKeyboardButton(text=f"{EMOJI['back']} {t(lang, 'back')}", callback_data="asosiy_clan")])
    
    await callback.message.edit_text(
        f"*{EMOJI['clan']} {t(lang, 'clan_all_clans')}:*\n\n{t(lang, 'back')}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )

# --- KLAN HAQIDA ---
@router.callback_query(F.data.startswith("clan:show:"))
async def show_specific_clan(callback: CallbackQuery):
    _, _, clan_name = callback.data.split(":", 2)
    lang = get_user_lang(callback)
    clan = show_clan(clan_name)
    if not clan:
        await callback.answer(t(lang, "clan_no_clans"), show_alert=True)
        return

    user = get_user(callback.from_user.id)
    is_member = user.get("clan_name") == clan_name
    is_leader = is_member and user.get("clan_role") == "Lider"
    is_co = is_member and user.get("clan_role") == "Zam Lider"
    creator = get_user(clan['creator_id'])
    creator_name = creator["first_name"] if creator else "Unknown"

    join_type = get_clan_join_type(clan_name)
    join_emoji = EMOJI['request'] if join_type == "request" else EMOJI['open']
    join_text = t(lang, 'clan_join_request_type') if join_type == "request" else t(lang, 'clan_join_open_type')

    text = (
        f"*{EMOJI['clan']} {t(lang, 'clan_info_title', name=clan['clan_name'])}*\n\n"
        f"   📊 {t(lang, 'clan_level')}: {clan['clan_level']} | 👥 {t(lang, 'clan_members')}: {clan['members_count']}/10\n"
        f"   👑 {t(lang, 'clan_leader')}: [{creator_name}](tg://user?id={clan['creator_id']})\n"
        f"   {join_emoji} {t(lang, 'clan_join_type')}: {join_text}\n\n"
        f"*{EMOJI['info']} {t(lang, 'clan_description')}:*\n{clan['clan_description'] or '_No description_'}\n\n"
        f"💬 {t(lang, 'clan_group')}: {clan['clan_group'] or '_Not set_'}\n"
        f"📢 {t(lang, 'clan_channel')}: {clan['clan_channel'] or '_Not set_'}"
    )

    keyboard = get_clan_keyboard(clan_name, callback.from_user.id, lang, is_leader, is_co)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
    await callback.answer()

# --- QO‘SHILISH ---
@router.callback_query(F.data.startswith("clan:join:"))
async def join_clan_handler(callback: CallbackQuery):
    _, _, clan_name = callback.data.split(":", 2)
    lang = get_user_lang(callback)
    user = get_user(callback.from_user.id)
    clan = show_clan(clan_name)
    join_type = get_clan_join_type(clan_name)

    if user.get("clan_name"):
        await callback.answer(t(lang, "clan_already_member"), show_alert=True)
        return
    if clan['members_count'] >= 10:
        await callback.answer(t(lang, "clan_full"), show_alert=True)
        return

    if join_type == "open":
        if join_clan(callback.from_user.id, clan_name):
            await callback.answer(t(lang, "clan_join_success"), show_alert=True)
            await show_specific_clan(callback)
        else:
            await callback.answer(t(lang, "cross") + " Error!", show_alert=True)
    else:
        add_join_request(clan_name, callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
        await callback.answer(t(lang, "clan_request_sent"), show_alert=True)

# --- BOSHQARUV ---
@router.callback_query(F.data.startswith("clan:manage:"))
async def clan_management(callback: CallbackQuery):
    _, _, clan_name = callback.data.split(":", 2)
    lang = get_user_lang(callback)
    user = get_user(callback.from_user.id)
    if user.get("clan_name") != clan_name or user.get("clan_role") not in ["Lider", "Zam Lider"]:
        await callback.answer(t(lang, "clan_no_permission"), show_alert=True)
        return

    is_leader = user.get("clan_role") == "Lider"
    keyboard = [
        [InlineKeyboardButton(text=f"👥 {t(lang, 'clan_members_list')}", callback_data=f"clan:members:{clan_name}")],
        [InlineKeyboardButton(text=f"{EMOJI['request']} {t(lang, 'clan_requests')}", callback_data=f"clan:requests:{clan_name}")],
        [InlineKeyboardButton(text=f"🔓 {t(lang, 'clan_join_type_settings')}", callback_data=f"clan:join_type:{clan_name}")]
    ]
    if is_leader:
        keyboard.append([InlineKeyboardButton(text=f"{EMOJI['transfer']} {t(lang, 'clan_transfer_leadership')}", callback_data=f"clan:transfer:{clan_name}")])
    keyboard.append([InlineKeyboardButton(text=f"{EMOJI['back']} {t(lang, 'back')}", callback_data=f"clan:show:{clan_name}")])

    await callback.message.edit_text(
        f"*{EMOJI['settings']} {t(lang, 'clan_management')} — {clan_name}*\n\n{t(lang, 'back')}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

# --- A'ZOLAR ---
@router.callback_query(F.data.startswith("clan:members:"))
async def clan_members(callback: CallbackQuery):
    _, _, clan_name = callback.data.split(":", 2)
    lang = get_user_lang(callback)
    members = get_clan_members(clan_name)
    user = get_user(callback.from_user.id)
    is_leader = user.get("clan_role") == "Lider"
    is_co = user.get("clan_role") == "Zam Lider"

    text = f"*{EMOJI['clan']} {t(lang, 'clan_members_list')} — {clan_name}*\n\n"
    keyboard = []
    co_count = sum(1 for m in members if m['clan_role'] == "Zam Lider")

    for member in members:
        role_emoji = EMOJI['leader'] if member['clan_role'] == "Lider" else EMOJI['co_leader'] if member['clan_role'] == "Zam Lider" else EMOJI['member']
        name = f"[{member['first_name']}](tg://user?id={member['user_id']})"
        text += f"{role_emoji} {name}\n"

        if (is_leader or is_co) and member['clan_role'] == "Azo":
            keyboard.append([InlineKeyboardButton(text=f"{EMOJI['kick']} {t(lang, 'clan_kick')} — {member['first_name'][:12]}", callback_data=f"clan:kick:{clan_name}:{member['user_id']}")])
        if is_leader and member['clan_role'] == "Azo" and co_count < 3:
            keyboard.append([InlineKeyboardButton(text=f"{EMOJI['promote']} {t(lang, 'clan_promote')} — {member['first_name'][:12]}", callback_data=f"clan:promote:{clan_name}:{member['user_id']}")])

    keyboard.append([InlineKeyboardButton(text=f"{EMOJI['back']} {t(lang, 'back')}", callback_data=f"clan:manage:{clan_name}")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

# --- QO‘SHILISH TURINI O‘ZGARTIRISH ---
@router.callback_query(F.data.startswith("clan:join_type:"))
async def change_join_type(callback: CallbackQuery):
    _, _, clan_name = callback.data.split(":", 2)
    lang = get_user_lang(callback)
    if get_user(callback.from_user.id).get("clan_role") != "Lider":
        await callback.answer(t(lang, "clan_only_leader"), show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton(text=f"{EMOJI['open']} {t(lang, 'clan_set_join_open')}", callback_data=f"clan:set_join:open:{clan_name}")],
        [InlineKeyboardButton(text=f"{EMOJI['request']} {t(lang, 'clan_set_join_request')}", callback_data=f"clan:set_join:request:{clan_name}")],
        [InlineKeyboardButton(text=f"{EMOJI['back']} {t(lang, 'back')}", callback_data=f"clan:manage:{clan_name}")]
    ]
    await callback.message.edit_text(f"*{EMOJI['settings']} {t(lang, 'clan_join_type_settings')}:*", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data.startswith("clan:set_join:"))
async def set_join_type(callback: CallbackQuery):
    _, _, jtype, clan_name = callback.data.split(":", 3)
    lang = get_user_lang(callback)
    if get_user(callback.from_user.id).get("clan_role") != "Lider":
        await callback.answer(t(lang, "clan_no_permission"), show_alert=True)
        return
    set_clan_join_type(clan_name, jtype)
    await callback.answer(f"{EMOJI['check']} {t(lang, 'clan_join_type')}: {t(lang, 'clan_set_join_open') if jtype == 'open' else t(lang, 'clan_set_join_request')}", show_alert=True)
    await clan_management(callback)

# --- LIDERLIK O‘TKAZISH ---
@router.callback_query(F.data.startswith("clan:transfer:"))
async def start_transfer_leadership(callback: CallbackQuery):
    _, _, clan_name = callback.data.split(":", 2)
    lang = get_user_lang(callback)
    if get_user(callback.from_user.id).get("clan_role") != "Lider":
        await callback.answer(t(lang, "clan_only_leader"), show_alert=True)
        return

    members = get_clan_members(clan_name)
    keyboard = []
    for m in members:
        if m['user_id'] != callback.from_user.id and m['clan_role'] != "Lider":
            keyboard.append([InlineKeyboardButton(text=f"{EMOJI['member']} {m['first_name']}", callback_data=f"clan:transfer_to:{clan_name}:{m['user_id']}")])
    keyboard.append([InlineKeyboardButton(text=f"{EMOJI['back']} {t(lang, 'back')}", callback_data=f"clan:manage:{clan_name}")])
    await callback.message.edit_text(f"*{EMOJI['transfer']} {t(lang, 'clan_transfer_prompt')}*", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data.startswith("clan:transfer_to:"))
async def confirm_transfer(callback: CallbackQuery):
    _, _, clan_name, target_id = callback.data.split(":", 3)
    lang = get_user_lang(callback)
    transfer_leadership(clan_name, callback.from_user.id, int(target_id))
    await callback.answer(t(lang, "clan_transferred"), show_alert=True)
    await show_specific_clan(callback)

# --- PROMOTE / KICK / REQUESTS ---
@router.callback_query(F.data.startswith("clan:promote:"))
async def promote_to_co_leader(callback: CallbackQuery):
    _, _, clan_name, target_id = callback.data.split(":", 3)
    lang = get_user_lang(callback)
    members = get_clan_members(clan_name)
    if sum(1 for m in members if m['clan_role'] == "Zam Lider") >= 3:
        await callback.answer(t(lang, "cross") + " Max 3 co-leaders!", show_alert=True)
        return
    update_user_clan_role(int(target_id), "Zam Lider")
    await callback.answer(t(lang, "clan_promoted"), show_alert=True)
    await clan_members(callback)

@router.callback_query(F.data.startswith("clan:kick:"))
async def kick_member_handler(callback: CallbackQuery):
    _, _, clan_name, target_id = callback.data.split(":", 3)
    lang = get_user_lang(callback)
    kick_member(int(target_id))
    await callback.answer(t(lang, "clan_kicked"), show_alert=True)
    await clan_members(callback)

@router.callback_query(F.data.startswith("clan:requests:"))
async def show_requests(callback: CallbackQuery):
    _, _, clan_name = callback.data.split(":", 2)
    lang = get_user_lang(callback)
    requests = get_pending_requests(clan_name)
    if not requests:
        await callback.message.edit_text(t(lang, "clan_no_requests"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(t(lang, "back"), f"clan:manage:{clan_name}")]]))
        return

    keyboard = []
    for req in requests:
        name = req['first_name'][:15]
        keyboard += [
            [InlineKeyboardButton(f"{EMOJI['check']} {t(lang, 'clan_request_approve')}: {name}", f"clan:approve:{clan_name}:{req['user_id']}")],
            [InlineKeyboardButton(f"{EMOJI['cross']} {t(lang, 'clan_request_reject')}: {name}", f"clan:reject:{clan_name}:{req['user_id']}")]
        ]
    keyboard.append([InlineKeyboardButton(f"{EMOJI['back']} {t(lang, 'back')}", f"clan:manage:{clan_name}")])
    await callback.message.edit_text(f"*{EMOJI['request']} {t(lang, 'clan_requests')}:*", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data.startswith("clan:approve:"))
async def approve_join(callback: CallbackQuery):
    _, _, clan_name, user_id = callback.data.split(":", 3)
    lang = get_user_lang(callback)
    approve_request(clan_name, int(user_id))
    await callback.answer(t(lang, "clan_request_approved"), show_alert=True)
    await show_requests(callback)

@router.callback_query(F.data.startswith("clan:reject:"))
async def reject_join(callback: CallbackQuery):
    _, _, clan_name, user_id = callback.data.split(":", 3)
    lang = get_user_lang(callback)
    reject_request(clan_name, int(user_id))
    await callback.answer(t(lang, "clan_request_rejected"), show_alert=True)
    await show_requests(callback)

# --- CHIQISH ---
@router.callback_query(F.data == "clan:leave")
async def leave_clan_handler(callback: CallbackQuery):
    lang = get_user_lang(callback)
    user = get_user(callback.from_user.id)
    if user.get("clan_role") == "Lider":
        await callback.answer(t(lang, "clan_leader_cant_leave"), show_alert=True)
        return
    leave_clan(callback.from_user.id)
    await callback.answer(t(lang, "clan_left"), show_alert=True)
    await clan_menu(callback)

# --- KLAN YARATISH ---
@router.callback_query(F.data == "create_clan")
async def start_create_clan(callback: CallbackQuery, state: FSMContext):
    lang = get_user_lang(callback)
    user = get_user(callback.from_user.id)
    if user["olmos"] < 1:
        await callback.answer(f"{EMOJI['cross']} 1 {t(lang, 'clan_create').split('(')[1][:-1]} {t(lang, 'back')}", show_alert=True)
        return
    await callback.message.answer(f"{EMOJI['clan']} {t(lang, 'clan_create_name')}")
    await state.set_state(ClanCreateState.waiting_name)
    await callback.answer()

@router.message(ClanCreateState.waiting_name)
async def receive_clan_name(message: Message, state: FSMContext):
    lang = get_user_lang(message)
    name = message.text.strip()
    if not (3 <= len(name) <= 20):
        await message.answer(f"{EMOJI['cross']} 3-20 {t(lang, 'back')}")
        return
    await state.update_data(clan_name=name)
    await message.answer(f"{EMOJI['check']} {name} qabul qilindi!\n\n {t(lang, 'clan_create_desc')}")
    await state.set_state(ClanCreateState.waiting_description)

@router.message(ClanCreateState.waiting_description)
async def receive_clan_description(message: Message, state: FSMContext):
    lang = get_user_lang(message)
    if len(message.text) > 200:
        await message.answer(f"{EMOJI['cross']} Max 200 {t(lang, 'back')}")
        return
    await state.update_data(clan_description=message.text)
    await message.answer(t(lang, 'clan_create_group'))
    await state.set_state(ClanCreateState.waiting_group)

@router.message(ClanCreateState.waiting_group)
async def receive_clan_group(message: Message, state: FSMContext):
    lang = get_user_lang(message)
    group = message.text.strip()
    if not (group.startswith("@") or "t.me/" in group):
        await message.answer(f"{EMOJI['cross']} @username or t.me/link")
        return
    await state.update_data(clan_group=group)
    await message.answer(t(lang, 'clan_create_channel'))
    await state.set_state(ClanCreateState.waiting_channel)

@router.message(ClanCreateState.waiting_channel)
async def receive_clan_channel(message: Message, state: FSMContext):
    lang = get_user_lang(message)
    channel = message.text.strip()
    if not (channel.startswith("@") or "t.me/" in channel or "https://" in channel):
        await message.answer(f"{EMOJI['cross']} @kanal or https://t.me/kanal")
        return

    channel_url = normalize_link(channel)
    data = await state.get_data()
    clan_group_url = normalize_link(data["clan_group"])

    if create_clan(data["clan_name"], message.from_user.id, data["clan_description"], data["clan_group"], channel):
        remove_olmos(message.from_user.id, 1)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE users SET clan_name = ?, clan_role = 'Lider' WHERE user_id = ?", (data["clan_name"], message.from_user.id))
        conn.commit()
        conn.close()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📢 {t(lang, 'clan_channel_btn')}", url=channel_url)],
            [InlineKeyboardButton(text=f"💬 {t(lang, 'clan_group_btn')}", url=clan_group_url)],
            [InlineKeyboardButton(text=f"{EMOJI['clan']} {t(lang, 'clan_menu_btn')}", callback_data="asosiy_clan")]
        ])
        await message.answer(
            f"*{EMOJI['check']} {t(lang, 'clan_created')}* `{data['clan_name']}`\n\n"
            f"{EMOJI['leader']} {t(lang, 'clan_leader')}: {message.from_user.first_name}\n"
            f"1 olmos olindi",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await message.answer(t(lang, "clan_name_taken"))
    await state.clear()