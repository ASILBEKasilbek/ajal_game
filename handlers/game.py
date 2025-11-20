# handlers/game.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, FSInputFile
)
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
import asyncio
import random
from dataclasses import dataclass, field
from typing import Dict, Optional
from database.db import (
    get_user, save_user, remove_olmos, add_balls,
    save_game_state, delete_game_state
)
from datetime import datetime
from config import CARD_CHOICE_TIME, NIGHT_DELAY, NOMINATE_TIME, GROUP_VOTE_TIME, MADARA_POISON_ROUNDS, CARDS,JOIN_TIME

router = Router()
active_games: Dict[int, 'GameState'] = {}

RANKS = [
    {"name": "ACE", "emoji": "🔥", "min_hp": 0, "next_hp": 2500},
    {"name": "ACE MASTER", "emoji": "⚡️", "min_hp": 2500, "next_hp": 6000},
    {"name": "ACE DOMINATOR", "emoji": "💀", "min_hp": 6000, "next_hp": 10000},
    {"name": "ZAVA", "emoji": "👑", "min_hp": 10000, "next_hp": None},
]
RANK_UP_MESSAGES = {
    "ACE": """
🎉 RANK UP!
✨ Siz endi ACE bo‘ldingiz!
🔥 O‘yin maydonida sizni endi hech kim to‘xtata olmaydi!
🕹 Har bir g‘alaba — kuch, har bir mag‘lubiyat — saboq.
    """,
    "ACE MASTER": """
⚡ Yangi daraja!
🔥 Siz ACE MASTER maqomiga yetdingiz!
💀 Sizdan qo‘rqishadi, chunki siz o‘yin maydonining ustasisiz!
🌪 Har bir raqib endi siz uchun oddiy sinov xolos.
    """,
    "ACE DOMINATOR": """
💥 E’tibor! E’tibor!
🏆 Siz ACE DOMINATOR bo‘ldingiz!
🚀 Sizning nomingiz endi reyting tepasida porlaydi!
⚔️ Bu darajaga faqat eng kuchlilar chiqadi.
    """,
    "ZAVA": """
🔥🔥🔥 IMKONSIZ! 🔥🔥🔥
👑 Siz endi ZAVA — afsonaga aylangansiz!
💫 Sizni endi na vaqt, na raqib to‘xtata oladi.
🌍 O‘yin sizni eslab qoladi… abadiy.
    """,
}
HP_BONUS = {"ACE": 8, "ACE MASTER": 10, "ACE DOMINATOR": 12, "ZAVA": 15}
HP_PENALTY = {"ACE": -5, "ACE MASTER": -8, "ACE DOMINATOR": -10, "ZAVA": -12}

# Level progression (hp_required_for_next, cumulative)
LEVEL_PROGRESSION = [
    (0, 0),  # lvl 1
    (20, 20), (40, 60), (60, 120), (90, 210), (130, 340), (180, 520), (250, 770), (350, 1120), (500, 1620),  # 2-10
]
STREAK_WIN_BONUS = 25  # 3 ketma-ket win
STREAK_LOSE_PENALTY = -20  # 3 ketma-ket lose

GAME_RESULT_HP = {"win": 10, "lose": 3, "draw": 5}
@dataclass
class Player:
    user_id: int
    name: str
    alive: bool = True
    role: str = "Tinch o'yinchi"
    double_vote: bool = False
    poisoned: bool = False
    can_save: bool = False
    card: Optional[str] = None
    chosen_card: Optional[str] = None

@dataclass
class GameState:
    chat_id: int
    lobby_message_id: Optional[int] = None
    players: Dict[int, Player] = field(default_factory=dict)
    round_number: int = 0
    najiro_id: Optional[int] = None
    orochimaru_id: Optional[int] = None
    qutqaruvchi_id: Optional[int] = None
    obito_id: Optional[int] = None
    madara_id: Optional[int] = None
    running: bool = False
    night_actions: Dict[str, Optional[int]] = field(default_factory=dict)
    qutqaruvchi_used: bool = False
    card_phase_active: bool = False
    card_message_id: Optional[int] = None
    _nominee_counts: Dict[int, int] = field(default_factory=dict)
    _temp_vote: Optional[Dict] = None
    game_winners: list = field(default_factory=list)
    group_invite_link: str = ""

@router.callback_query(F.data=="rank_level_info")
async def rank_level_info(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user:
        await callback.message.answer("❌ Foydalanuvchi topilmadi.")
        await callback.answer()
        return

    # Foydalanuvchining tilini aniqlash
    lang = user.get("language", "uz")

    # Hozirgi HP va Rank
    current_hp = user.get("hp", 0)
    current_rank = user.get("current_rank", "ACE")

    # Levelni hisoblash
    def calculate_level(hp: int) -> int:
        level = 1
        cumulative = 0
        for hp_required, cum_hp in LEVEL_PROGRESSION:
            if hp >= cum_hp:
                level += 1
            else:
                break
        return level

    user_level = calculate_level(current_hp)

    # Keyingi rank va zarur HP
    next_rank_info = None
    for i, rank in enumerate(RANKS):
        if rank["name"] == current_rank:
            if i + 1 < len(RANKS):
                next_rank_info = RANKS[i + 1]
            break

    # Rank up uchun xabar
    rank_message = RANK_UP_MESSAGES.get(current_rank, "")

    # Keyingi rank va qolgan HPni aniqlash
    if next_rank_info:
        hp_needed = next_rank_info["min_hp"] - current_hp
        next_rank_text = f"\n⏳ Keyingi rank: <b>{next_rank_info['name']}</b> ({hp_needed} HP kerak)"
    else:
        next_rank_text = "\n🏆 Siz eng yuqori rankdasiz!"

    # Chiroyli xabar
    text = f"""
🏅 <b>Rank va Level haqida ma'lumot</b> 🏅

👤 Foydalanuvchi: <b>{user.get('username','Foydalanuvchi')}</b>
💖 Hozirgi HP: <b>{current_hp}</b>
🎯 Hozirgi Level: <b>{user_level}</b>
🔥 Hozirgi Rank: <b>{current_rank}</b>
{next_rank_text}

📜 Rank haqida izoh:
{rank_message}
    """

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()



# ────────────────────── YORDAMCHILAR ──────────────────────
def migrate_db():
    import sqlite3
    from database.db import DB_FILE
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    if 'hp' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN hp INTEGER DEFAULT 0")
    if 'current_rank' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN current_rank TEXT DEFAULT 'ACE'")
    if 'streak' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0")
    if 'streak_type' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN streak_type TEXT DEFAULT NULL")
    conn.commit()
    conn.close()

migrate_db()

def calculate_level(hp: int) -> int:
    cumulative = 0
    level = 1
    req = 20
    multiplier = 1.5  # taxminiy exponential
    for l in range(2, 101):
        if hp < cumulative + req:
            return level
        cumulative += req
        level += 1
        if l <= 10:
            req = {2:40,3:60,4:90,5:130,6:180,7:250,8:350,9:500,10:800}[l]
        elif l <= 15:
            req = int(1000 + (l-10)*400)  # 800-2000
        else:
            req = int(req * 1.6)  # exponential o'sish
    return 100

def get_rank_by_name(name: str):
    return next((r for r in RANKS if r["name"] == name), RANKS[0])

def get_current_rank(hp: int) -> dict:
    for rank in reversed(RANKS):
        if hp >= rank["min_hp"]:
            return rank
    return RANKS[0]

def update_rank_and_level(user: dict, old_hp: int):
    old_rank = get_rank_by_name(user.get('current_rank', 'ACE'))
    new_rank_obj = get_current_rank(user['hp'])
    user['current_rank'] = new_rank_obj["name"]

    # Rank up message
    if user['hp'] >= old_rank["next_hp"] and old_rank["next_hp"] is not None and old_hp < old_rank["next_hp"]:
        return RANK_UP_MESSAGES.get(user['current_rank'], "")

    # ZAVA downgrade
    if old_rank["name"] == "ZAVA" and user['hp'] < 10000:
        user['current_rank'] = "ACE DOMINATOR"
        return "⚠️ ZAVA rankidan tushdingiz! HP 10,000 dan pastga tushdi."

    return None

async def safe_delete(bot, chat_id: int, message_id: Optional[int]):
    if message_id:
        try:
            await bot.delete_message(chat_id, message_id)
        except:
            pass

async def broadcast(bot, chat_id: int, text: str, reply_markup=None):
    return await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode="HTML")

def assign_roles(gs: GameState):
    alive = [p for p in gs.players.values() if p.alive]
    random.shuffle(alive)
    if len(alive) < 5: return
    gs.najiro_id = alive[0].user_id; alive[0].role = "Najiro"
    gs.orochimaru_id = alive[1].user_id; alive[1].role = "Orochimaru"
    gs.qutqaruvchi_id = alive[2].user_id; alive[2].role = "Qutqaruvchi"; alive[2].can_save = True
    gs.obito_id = alive[3].user_id; alive[3].role = "Obito"; alive[3].double_vote = True
    gs.madara_id = alive[4].user_id; alive[4].role = "Madara"

def assign_cards(gs: GameState):
    for p in gs.players.values():
        if p.alive:
            p.card = random.choice(CARDS)
            p.chosen_card = None

def get_role_description(role: str) -> str:
    d = {
        "Najiro": """Najiro — o‘yinning asosiy dushmani va markaziy qahramoni.
🌙 Har kechada Najiro bitta o‘yinchini o‘ldiradi.
Uning maqsadi — barcha o‘yinchilarni yo‘q qilish va oxirigacha tirik qolish.

⚠️ Agar Najiro o‘ldirilsa, odatda o‘yin tugaydi, lekin Orochimaru tirik bo‘lsa, o‘yin davom etadi.
Najiro va Orochimaru ikkalasi o‘lgandagina o‘yin tugaydi.

Najiro o‘yinda eng kuchli va xavfli kuch. U yashirincha harakat qilib, o‘yin taqdirini o‘zgartiradi.""",
        "Orochimaru": """
Orochimaru — Najironing sodiq sherigi.
Agar Najiro o‘ldirilsa, o‘yin darhol tugamaydi, chunki Orochimaru tirik bo‘lsa, o‘yin davom etadi.
Shu sababli, o‘yinni yakunlash uchun Najiro va Orochimaru ikkisi ham o‘lishi kerak.

🕰 Orochimaru odam o‘ldira olmaydi, u o‘yinni uzaytirish va Najironi himoya qilish uchun xizmat qiladi.
U yashirincha ma’lumot to‘playdi, odamlarni chalg‘itadi va Najironing harakatlarini qo‘llab-quvvatlaydi.""",
        "Qutqaruvchi": """Qutqaruvchi — o‘yindagi yagona najotkor.
🌙 O‘yin davomida faqat bitta marta istalgan o‘yinchini o‘limdan saqlab qolishi mumkin.
Uning vazifasi — Najiro yoki tinch o‘yinchilarni himoya qilish va o‘yinni davom ettirish.

⚕️ Qutqaruvchi o‘zini ham bir marta davolay oladi, ammo undan keyin bu kuchni yo‘qotadi.""",
        "Obito": """Obito — o‘ziga xos kuchga ega o‘yinchi.
🗳 Ovoz berish (dorga osish) jarayonida uning ovozi ikki o‘yinchining ovoziga teng.
Ya’ni, Obito kimga ovoz bersa, o‘sha nomzodga 2 ta ovoz yoziladi.

Uning maqsadi — o‘z tomonining g‘alabasini ta’minlash uchun strategik ovoz berish orqali o‘yinni boshqarish.
Obitoning ovozi hal qiluvchi kuchga ega, shuning uchun u jim bo‘lsa ham o‘yinda katta rol o‘ynaydi.""",
        "Madara": """Madara — zahar kuchiga ega yovuz strateg.
🌙 Har kechada Madara bitta o‘yinchini zaharlaydi.

💀 Zaharlangan o‘yinchiga maxfiy xabar boradi:
“Siz zaharlandingiz.”

Ammo kim uni zaharlaganini hech kim bilmaydi.
Agar hamma o‘yinchilar zaharlansa, o‘yin Madaraning g‘alabasi bilan tugaydi.

⚠️ Madara Najironi ham zaharlashi mumkin — uning zahri hammaga o‘tadi va vaqt o‘tishi bilan butun o‘yinni yo‘q qiladi.
U o‘yin davomida sekin, ammo muqarrar tarzda halokat tarqatadi.""",
        "Tinch o'yinchi": """Tinch o'yinchi — o‘yinning asosiy ishtirokchisi.
Ularning maqsadi — Najiro va uning yordamchilarini topib, o‘ldirish va o‘yinni tinch yo‘l bilan yakunlash.
Tinch o‘yinchilar bir-birlari bilan hamkorlik qilib, Najiro va uning jamoasini aniqlashlari va yo‘q qilishlari kerak.""",   
    }
    return d.get(role, "Tinch o'yinchi")

# ────────────────────── LOBBY ──────────────────────


@router.message(Command("game"))
async def start_game(message: Message):
    chat_id = message.chat.id
    bot = message.bot
    if message.chat.type not in ["group", "supergroup"]:
        return await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi.")

    if chat_id in active_games:
        gs = active_games[chat_id]
        try:
            await bot.delete_message(chat_id, message.message_id)
            await message.answer("⚠️ Lobby allaqachon mavjud.")
        except:
            pass

        return  
    
    bot_info = await bot.get_me()
    join_url = f"https://t.me/{bot_info.username}?start=game_{chat_id}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'yinga qo'shilish", url=join_url)]
    ])

    msg = await message.answer(
        f"<b>AJAL O'YINI</b>\n\n"
        f"Lobby {JOIN_TIME}s ochiq.\n\n"
        f"<i>Ishtirokchilar: 0</i>",
        reply_markup=kb, parse_mode="HTML"
    )

    try:
        await bot.pin_chat_message(chat_id, msg.message_id, disable_notification=True)
    except:
        pass

    username = message.chat.username or ""
    gs = GameState( 
        chat_id=chat_id,
        lobby_message_id=msg.message_id,
        group_invite_link=f"https://t.me/{username}"
    )
    active_games[chat_id] = gs

    await asyncio.sleep(JOIN_TIME)
    gs = active_games.get(chat_id)

    if not gs or gs.running or len(gs.players) < 5:
        await broadcast(bot, chat_id, "Kamida 5 kishi kerak.")
        await safe_delete(bot, chat_id, gs.lobby_message_id if gs else None)
        active_games.pop(chat_id, None)
        return

    await safe_delete(bot, chat_id, gs.lobby_message_id)
    await begin_game(gs, bot)

@router.callback_query(F.data == "start_game_admin")
async def start_game_admin(callback: CallbackQuery):
    gs = active_games.get(callback.message.chat.id)
    if not gs or gs.running or len(gs.players) < 5:
        return await callback.answer("Kamida 5 kishi kerak!", show_alert=True)
    await callback.answer("O'yin boshlanmoqda...")
    await safe_delete(callback.bot, callback.message.chat.id, gs.lobby_message_id)
    await begin_game(gs, callback.bot)
    

@router.message(Command("play"))
async def start_game_play(message: Message):
    gs = active_games.get(message.chat.id)
    
    if not gs or gs.running or len(gs.players) < 5:
        return await message.answer("Kamida 5 kishi kerak!", show_alert=False)
    
    await message.answer("O'yin boshlanmoqda...")
    await safe_delete(message.bot, message.chat.id, gs.lobby_message_id)
    await begin_game(gs, message.bot)

# ────────────────────── O'YIN BOSHLANISHI ──────────────────────
async def begin_game(gs: GameState, bot):
    gs.running = True
    assign_roles(gs)
    try:
        await bot.send_animation(gs.chat_id, FSInputFile("ajal_game_gif.mp4"),
                                 caption="O'yin boshlanmoqda!")
    except:
        pass

    for p in gs.players.values():
        await bot.send_message(p.user_id,
            f"<b>Rolingiz:</b> {p.role}\n\n{get_role_description(p.role)}",
            parse_mode="HTML")
    
    await send_other_players_cards(gs, bot)

    await broadcast(bot, gs.chat_id,
        f"<b>O'yin boshlandi!</b>\nIshtirokchilar: {len(gs.players)}")

    while gs.running:
        alive = [p for p in gs.players.values() if p.alive]
        if len(alive) <= 2:
            await end_game(gs, bot, f"O'yin tugadi! Qolganlar: {', '.join(p.name for p in alive)}")
            return

        najiro_alive = gs.najiro_id in gs.players and gs.players[gs.najiro_id].alive
        orochimaru_alive = gs.orochimaru_id in gs.players and gs.players[gs.orochimaru_id].alive
        if not najiro_alive and not orochimaru_alive:
            await end_game(gs, bot, "<b>Tinch o'yinchilar g'alaba qozondi!</b>")
            return

        if all(p.poisoned for p in alive) and alive:
            await end_game(gs, bot, "<b>Madara g'alaba qozondi!</b>\nHamma zaharlandi!")
            return

        gs.round_number += 1
        await card_phase(gs, bot)
        await night_phase(gs, bot)
        await day_phase(gs, bot)
        await asyncio.sleep(2)

# ────────────────────── HAR BIR PLAYERGA QOLGANLARNING KARTASI ──────────────────────
async def send_other_players_cards(gs: GameState, bot):
    for user_id, player in gs.players.items():
        print(gs)
        others = [p for p in gs.players.values() if p.user_id != user_id]

        text = "🃏 <b>Boshqa o'yinchilar kartalari:</b>\n\n"
        print(others)

        for o in others:
            text += f"<b>{o.name}</b> — {o.card}\n"

        await bot.send_message(user_id, text, parse_mode="HTML")

# ────────────────────── KARTA FAZASI ──────────────────────
async def card_phase(gs: GameState, bot):
    assign_cards(gs)
    gs.card_phase_active = True
    keyboard_rows = []
    row = []

    for i, card in enumerate(CARDS):
        row.append(
            InlineKeyboardButton(
                text=card,
                callback_data=f"choose_card:{gs.chat_id}:{i}"
            )
        )
        if len(row) == 2:
            keyboard_rows.append(row)
            row = []
    if row:
        keyboard_rows.append(row)
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    msg = await broadcast(bot, gs.chat_id, "🃏 <b>Karta tanlang!</b>", reply_markup=kb)
    gs.card_message_id = msg.message_id
    await asyncio.sleep(CARD_CHOICE_TIME)
    gs.card_phase_active = False
    killed = []

    for p in gs.players.values():
        if p.alive and p.chosen_card != p.card:
            p.alive = False
            killed.append(p.name)

            others = [f"{pl.name} — {pl.card}" for pl in gs.players.values()
                      if pl.alive and pl.user_id != p.user_id]

            try:
                await bot.send_message(
                    p.user_id,
                    f"Siz o'ldingiz!\n\nBoshqalar kartalari:\n" + "\n".join(others),
                    parse_mode="HTML"
                )
                revive_kb = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="1 olmosga tirilish",
                        callback_data=f"revive:{gs.chat_id}:{p.user_id}"
                    )
                ]])
                await bot.send_message(p.user_id, "1 olmosga tirilish?", reply_markup=revive_kb)
            except:
                pass

    if killed:
        await broadcast(bot, gs.chat_id, f"O'ldirildi: {', '.join(killed)}")

    await safe_delete(bot, gs.chat_id, gs.card_message_id)
    gs.card_message_id = None

@router.callback_query(F.data.startswith("choose_card:"))
async def choose_card(callback: CallbackQuery):
    gs = active_games.get(callback.message.chat.id)
    if not gs or not gs.card_phase_active:
        return await callback.answer("Vaqt tugadi.")
    try:
        _, _, idx = callback.data.split(":")
        chosen = CARDS[int(idx)]
    except:
        return await callback.answer("Xato.")
    p = gs.players.get(callback.from_user.id)
    if p and p.alive:
        p.chosen_card = chosen
    await callback.answer(f"{chosen} tanlandi!")

@router.callback_query(F.data.startswith("revive:"))
async def revive_player(callback: CallbackQuery):
    try:
        _, chat_id_str, user_id_str = callback.data.split(":")
        chat_id, user_id = int(chat_id_str), int(user_id_str)
    except:
        return
    gs = active_games.get(chat_id)
    if not gs: return
    p = gs.players.get(user_id)
    if not p or p.alive:
        return await callback.answer("Siz tirik emassiz.")
    if not remove_olmos(user_id, 1):
        return await callback.answer("Olmos yetarli emas! /profile")
    p.alive = True
    await callback.answer("TIRILDINGIZ!")
    await broadcast(callback.bot, chat_id, f"{p.name} 1 olmosga tirildi!")

# ────────────────────── KECHA ──────────────────────
async def night_phase(gs: GameState, bot):

    await bot.send_animation(gs.chat_id, FSInputFile("ajal_game_gif.mp4"),caption="Kecha tushdi! Gumondorni tanlang (30s)")
    
    # await broadcast(bot, gs.chat_id, f"Kecha tushdi... ({NIGHT_DELAY}s)")
    gs.night_actions.clear()

    # Najiro
    if gs.najiro_id and gs.players[gs.najiro_id].alive:
        targets = [p for p in gs.players.values() if p.alive and p.user_id != gs.najiro_id]
        if targets:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=p.name, callback_data=f"najiro_kill:{gs.chat_id}:{p.user_id}")]
                for p in targets[:10]
            ])
            await bot.send_message(gs.najiro_id, "Kimni o'ldirmoqchisiz?", reply_markup=kb)

    # Qutqaruvchi
    if gs.qutqaruvchi_id and gs.players[gs.qutqaruvchi_id].alive and not gs.qutqaruvchi_used:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=p.name, callback_data=f"qutqaruvchi_save:{gs.chat_id}:{p.user_id}")]
            for p in gs.players.values() if p.alive
        ])
        await bot.send_message(gs.qutqaruvchi_id, "Kimni qutqarishni xohlaysiz? (1 marta)", reply_markup=kb)

    # Madara
    if gs.round_number % MADARA_POISON_ROUNDS == 0 and gs.madara_id and gs.players[gs.madara_id].alive:
        targets = [p for p in gs.players.values() if p.alive and p.user_id != gs.madara_id and not p.poisoned]
        if targets:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=p.name, callback_data=f"madara_poison:{gs.chat_id}:{p.user_id}")]
                for p in targets[:10]
            ])
            await bot.send_message(gs.madara_id, "Kimni zaharlamoqchisiz?", reply_markup=kb)

    await asyncio.sleep(NIGHT_DELAY)
    victim = gs.night_actions.get("najiro_kill")
    saved = gs.night_actions.get("qutqaruvchi_save")
    poison = gs.night_actions.get("madara_poison")

    if victim and victim == saved:
        await broadcast(bot, gs.chat_id, "Qutqaruvchi kimnidir saqlab qoldi!")
    elif victim:
        p = gs.players[victim]
        p.alive = False
        await broadcast(bot, gs.chat_id, f"<b>{p.name}</b> kecha o'ldirildi!")

    if poison:
        p = gs.players[poison]
        p.poisoned = True
        await bot.send_message(poison, "Siz <b>zaharlandingiz</b>!", parse_mode="HTML")

# ────────────────────── KUN ──────────────────────
async def day_phase(gs: GameState, bot):
    gs._nominee_counts.clear()
    # await broadcast(bot, gs.chat_id, f"Kun boshlandi! Gumonli tanlang ({NOMINATE_TIME}s)")
    await bot.send_animation(gs.chat_id, FSInputFile("kun.mp4"),caption="Tong otdi! Gumondorni tanlang (30s)")
    

    for p in gs.players.values():
        if p.alive:
            candidates = [pl for pl in gs.players.values() if pl.alive and pl.user_id != p.user_id]
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=pl.name, callback_data=f"nominate:{gs.chat_id}:{p.user_id}:{pl.user_id}")]
                for pl in candidates[:10]
            ] + [[InlineKeyboardButton(text="Tasodifiy", callback_data=f"nominate_auto:{gs.chat_id}:{p.user_id}")]])
            await bot.send_message(p.user_id, "Kimni gumon qilasiz?", reply_markup=kb)

    await asyncio.sleep(NOMINATE_TIME)

    if not gs._nominee_counts:
        alive_players = [p for p in gs.players.values() if p.alive]
        if not alive_players:
            print("Hech kim tirik emas, o'yin tugadi!")
            return
        nominee = random.choice(alive_players)
    else:
        nominee_id = max(gs._nominee_counts.items(), key=lambda x: x[1])[0]
        nominee = gs.players[nominee_id]

    await broadcast(bot, gs.chat_id, f"<b>Nomzod:</b> {nominee.name}\nOvoz bering:")
    vote_state = {"hang": 0, "spare": 0}
    voters = set()
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Osish", callback_data=f"vote_hang:{gs.chat_id}:{nominee.user_id}"),
        InlineKeyboardButton(text="Qutqarish", callback_data=f"vote_spare:{gs.chat_id}:{nominee.user_id}")
    ]])
    vote_msg = await broadcast(bot, gs.chat_id, "Ovozlar: 0 - 0", reply_markup=kb)
    gs._temp_vote = {
        "vote_state": vote_state,
        "voters": voters,
        "nominee_id": nominee.user_id,
        "vote_msg_id": vote_msg.message_id,
        "bot": bot
    }

    for _ in range(GROUP_VOTE_TIME):
        await asyncio.sleep(1)
        if gs._temp_vote:
            h, s = vote_state["hang"], vote_state["spare"]
            try:
                await bot.edit_message_text(
                    chat_id=gs.chat_id,
                    message_id=vote_msg.message_id,
                    text=f"Ovozlar: {h} - {s}",
                    reply_markup=kb
                )
            except:
                pass

    if gs._temp_vote:
        h, s = vote_state["hang"], vote_state["spare"]
        await bot.edit_message_reply_markup(gs.chat_id, vote_msg.message_id, reply_markup=None)
        if h > s:
            nominee.alive = False
            await broadcast(bot, gs.chat_id, f"<b>{nominee.name} osildi!</b>\n{h}-{s}")
        else:
            await broadcast(bot, gs.chat_id, f"<b>{nominee.name} qutqarildi!</b>\n{h}-{s}")
        gs._temp_vote = None

# ────────────────────── CALLBACKLAR ──────────────────────
@router.callback_query(F.data.startswith("najiro_kill:"))
async def najiro_kill(cb: CallbackQuery):
    gs = active_games.get(cb.message.chat.id)
    if gs and cb.from_user.id == gs.najiro_id:
        _, _, tid = cb.data.split(":")
        gs.night_actions["najiro_kill"] = int(tid)
    await cb.answer("Tanlandi!")

@router.callback_query(F.data.startswith("qutqaruvchi_save:"))
async def qutqaruvchi_save(cb: CallbackQuery):
    gs = active_games.get(cb.message.chat.id)
    if gs and cb.from_user.id == gs.qutqaruvchi_id:
        _, _, tid = cb.data.split(":")
        gs.night_actions["qutqaruvchi_save"] = int(tid)
        gs.qutqaruvchi_used = True
    await cb.answer("Saqlab qoldi!")

@router.callback_query(F.data.startswith("madara_poison:"))
async def madara_poison(cb: CallbackQuery):
    gs = active_games.get(cb.message.chat.id)
    if gs and cb.from_user.id == gs.madara_id:
        _, _, tid = cb.data.split(":")
        gs.night_actions["madara_poison"] = int(tid)
    await cb.answer("Zaharlandi!")

@router.callback_query(F.data.startswith("nominate:"))
async def nominate_player(cb: CallbackQuery):
    try:
        _, cid, vid, nid = cb.data.split(":")
        gs = active_games.get(int(cid))
        if gs and cb.from_user.id == int(vid):
            gs._nominee_counts[int(nid)] = gs._nominee_counts.get(int(nid), 0) + 1
        await cb.answer("Nomzod qilindi!")
    except: pass

@router.callback_query(F.data.startswith("nominate_auto:"))
async def nominate_auto(cb: CallbackQuery):
    try:
        _, cid, pid = cb.data.split(":")
        gs = active_games.get(int(cid))
        if gs and cb.from_user.id == int(pid):
            candidates = [p for p in gs.players.values() if p.alive and p.user_id != int(pid)]
            suspect = random.choice(candidates)
            gs._nominee_counts[suspect.user_id] = gs._nominee_counts.get(suspect.user_id, 0) + 1
        await cb.answer(f"{suspect.name} tanlandi!")
    except: pass

@router.callback_query(F.data.startswith("vote_hang:"))
async def vote_hang(cb: CallbackQuery):
    await handle_vote(cb, "hang")

@router.callback_query(F.data.startswith("vote_spare:"))
async def vote_spare(cb: CallbackQuery):
    await handle_vote(cb, "spare")

async def handle_vote(cb: CallbackQuery, action: str):
    try:
        _, cid, nid = cb.data.split(":")
        gs = active_games.get(int(cid))
        if not gs or not gs._temp_vote or gs._temp_vote["nominee_id"] != int(nid):
            return await cb.answer("Ovoz tugagan.")
        voter_id = cb.from_user.id
        if voter_id not in gs.players or not gs.players[voter_id].alive or voter_id in gs._temp_vote["voters"]:
            return await cb.answer("Ovoz bera olmaysiz.")
        count = 2 if gs.players[voter_id].double_vote else 1
        gs._temp_vote["voters"].add(voter_id)
        gs._temp_vote["vote_state"][action] += count
        await cb.answer(f"{count}x ovoz!")
    except: pass

# ────────────────────── O'YIN TUGASHI ──────────────────────
async def end_game(gs: GameState, bot, result_text: str):
    roles = "\n".join(f"{p.name} — {p.role}" for p in gs.players.values())
    await broadcast(bot, gs.chat_id, f"{result_text}\n\n<b>Rollari:</b>\n{roles}")

    # G'olib faction aniqlash
    najiro_team_win = any("najiro" in result_text.lower() or "orochimaru" in result_text.lower() for _ in [0])
    madara_win = "madara" in result_text.lower()
    peace_win = "tinch" in result_text.lower()

    for p in gs.players.values():
        user = get_user(p.user_id)
        if not user:
            continue

        user['total_games'] += 1
        add_balls(p.user_id, 50)  # bazaviy balls

        is_winner = p.alive
        result_key = "win" if is_winner else "lose"
        if "durang" in result_text.lower():
            result_key = "draw"

        # Streak update
        old_streak = user.get('streak', 0)
        old_type = user.get('streak_type')
        if old_type == result_key:
            user['streak'] = old_streak + 1
        else:
            user['streak'] = 1
            user['streak_type'] = result_key

        # Base HP from result
        base_hp = GAME_RESULT_HP[result_key]
        vip_multiplier = 1.5 if user.get('olmos', 0) > 0 else 1.0  # misol VIP
        hp_gain = int(base_hp * vip_multiplier)

        # Rank-based bonus/penalty
        rank = get_rank_by_name(user.get('current_rank', 'ACE'))
        if is_winner:
            hp_gain += HP_BONUS[rank["name"]]
            if user['wins'] > 0:
                user['wins'] += 1
        else:
            hp_gain += HP_PENALTY[rank["name"]]

        # Streak bonus
        if user['streak'] == 3 and user['streak_type'] == "win":
            hp_gain += STREAK_WIN_BONUS
        elif user['streak'] == 3 and user['streak_type'] == "lose":
            hp_gain += STREAK_LOSE_PENALTY

        old_hp = user.get('hp', 0)
        user['hp'] = max(0, old_hp + hp_gain)  # salbiy bo'lmasin

        # Level update (hp orqali)
        user['level'] = calculate_level(user['hp'])

        # Rank update va xabar
        rank_message = update_rank_and_level(user, old_hp)
        if rank_message:
            await bot.send_message(p.user_id, rank_message.strip())

        user['last_game_result'] = "G'olib" if is_winner else "Mag'lub"
        user['last_game_date'] = datetime.now().strftime("%Y-%m-%d")
        save_user(user)

    delete_game_state(gs.chat_id)
    active_games.pop(gs.chat_id, None)
    gs.running = False

# ────────────────────── GURUH XABARLARI TOZALASH ──────────────────────
@router.message(F.chat.type.in_(["group", "supergroup"]))
async def delete_vote_messages(message: Message):
    gs = active_games.get(message.chat.id)
    if not gs or not gs.running or not gs._temp_vote:
        return
    if message.from_user.id not in gs.players:
        return
    if message.text in ("Osish", "Qutqarish"):
        await message.delete()