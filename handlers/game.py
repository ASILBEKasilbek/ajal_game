# handlers/game.py
import sqlite3
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, FSInputFile
)
import asyncio
import random
from dataclasses import dataclass, field
from typing import Dict, Optional
from database.db import (
    get_user, save_user, remove_olmos, add_balls,
    save_game_state, delete_game_state
)
from aiogram.filters import BaseFilter
from datetime import datetime
from config import *
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import time
router = Router()
active_games: Dict[int, 'GameState'] = {}
pending_anon = {}


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

class CardActions(StatesGroup):
    waiting_anon_target = State()
    waiting_anon_text = State()

class IsPendingAnon(BaseFilter):
    def __init__(self, pending_dict):
        self.pending = pending_dict

    async def __call__(self, msg):
        return msg.from_user.id in self.pending




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

def calculate_level(hp: int) -> int:
    cumulative = 0
    level = 1
    req = 20
    multiplier = 1.5 
    for l in range(2, 101):
        if hp < cumulative + req:
            return level
        cumulative += req
        level += 1
        if l <= 10:
            req = {2:40,3:60,4:90,5:130,6:180,7:250,8:350,9:500,10:800}[l]
        elif l <= 15:
            req = int(1000 + (l-10)*400) 
        else:
            req = int(req * 1.6)  
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
            print("Message deletion failed.")

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
            print("Lobby exists message failed.")
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
        print("Pin message failed.")

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
        print("Lobby tugadi, lekin o'yin boshlanmadi.")
        # await broadcast(bot, chat_id, f"Kamida 5 kishi kerak. Hozirda {len(gs.players)} kishi bor.")
        await safe_delete(bot, chat_id, gs.lobby_message_id if gs else None)
        active_games.pop(chat_id, None)
        return

    await safe_delete(bot, chat_id, gs.lobby_message_id)
    await begin_game(gs, bot)

@router.message(Command("play"))
async def start_game_play(message: Message):
    gs = active_games.get(message.chat.id)
    if not gs or gs.running or len(gs.players) < 5:
        return await message.answer("Kamida 5 kishi kerak!", show_alert=False)
    await message.answer("O'yin boshlanmoqda...")
    gs.running = True 
    await safe_delete(message.bot, message.chat.id, gs.lobby_message_id)
    await begin_game(gs, message.bot)




# ────────────────────── O'YIN BOSHLANISHI ──────────────────────
async def begin_game(gs: GameState, bot):
    gs.running = True
    assign_roles(gs)
    for p in gs.players.values():
        print(f"{p.name} roli: {p.role}")
        await bot.send_message(p.user_id,
            f"<b>Rolingiz:</b> {p.role}\n\n{get_role_description(p.role)}",
            parse_mode="HTML")
        
    await broadcast(bot, gs.chat_id,f"<b>O'yin boshlandi!</b>\nIshtirokchilar: {len(gs.players)}")

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
        if not player.alive:
            continue

        # Faqat boshqa tirik o'yinchilar
        others = [p for p in gs.players.values() if p.alive and p.user_id != user_id]
        
        keyboard = []
        row = []

        for o in others:
            name = o.name.split()[0]
            btn = InlineKeyboardButton(text=name, callback_data=f"anon_start:{o.user_id}")
            row.append(btn)
            if len(row) == 2:
                keyboard.append(row)
                row = []

        # O'z kartasini ko'rish tugmasi
        kartam_btn = InlineKeyboardButton(text="Kartamni ko'rish", callback_data=f"buy_card_reveal:{user_id}")
        if row:
            keyboard.append(row)
        keyboard.append([kartam_btn])

        kb = InlineKeyboardMarkup(inline_keyboard=keyboard)

        # Matn yaratish
        text = "<b>Boshqa o'yinchilar kartalari:</b>\n\n"
        if others:
            for o in others:
                text += f"<b>{o.name.split()[0]}</b> — {o.card}\n"
        else:
            text += "Boshqa tirik o'yinchi yo'q.\n"

        text += f"\n<b>Sizning kartangizni ko‘rish:</b> Tugmani bosing →"

        try:
            await bot.send_message(user_id, text, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            print(f"Xabar yuborilmadi {user_id}: {e}")

@router.callback_query(F.data.startswith("anon_start:"))
async def anon_start(cb: CallbackQuery, state: FSMContext):
    _, target_str = cb.data.split(":")
    target_id = int(target_str)

    # Kim kimga yubormoqchi
    pending_anon[cb.from_user.id] = target_id

    await cb.message.answer(
        "✉️ Anonim xabaringizni yuboring:",
    ) 

@router.message(F.text, IsPendingAnon(pending_anon))
async def send_anon_message(msg: Message):
    sender_id = msg.from_user.id
    target_id = pending_anon.pop(sender_id)

    await msg.bot.send_message(
        target_id,
        f"📨 Sizga anonim xabar keldi:\n\n{msg.text}"
    )

    await msg.answer("✅ Xabar anonim tarzda yuborildi!")

@router.callback_query(F.data.startswith("buy_card_reveal:"))
async def buy_card_reveal(cb: CallbackQuery, state: FSMContext):
    try:
        user_id = int(cb.data.split(":")[1])
    except:
        return await cb.answer("Xato!")

    if cb.from_user.id != user_id:
        return await cb.answer("Bu sizniki emas!", show_alert=True)
    
    user = get_user(user_id)
    buttons = []
    if user.get("olmos", 0) >= 1:
        buttons.append(InlineKeyboardButton(text="1 💎 bilan ochish", callback_data=f"reveal_with_olmos:{user_id}"))
    if user.get("balls", 0)  >= 150:
        buttons.append(InlineKeyboardButton(text="150 🟢 bilan ochish", callback_data=f"reveal_with_balls:{user_id}"))

    if not buttons:
        return await cb.answer("Yetarli olmos yoki ball yo‘q!\n1 olmos yoki 150 ball kerak.", show_alert=True)

    kb = InlineKeyboardMarkup(inline_keyboard=[[b] for b in buttons])
    await cb.message.answer("Kartangizni ochish uchun usulni tanlang:", reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data.startswith("reveal_with_olmos:"))
async def reveal_with_olmos(cb: CallbackQuery):
    user_id = int(cb.data.split(":")[1])
    remove_olmos(user_id, 1)
    gs = active_games.get(cb.message.chat.id)
    if not gs:
        for g in active_games.values():
            if user_id in g.players:
                gs = g
                break
    if not gs:
        return await cb.answer("O‘yin topilmadi yoki tugallangan!", show_alert=True)
    player = gs.players[user_id]
    await cb.message.edit_text(f"💳 Kartangiz ochildi!\nSizning kartangiz: <b>{player.card}</b>\nXarajat: 1 💎", parse_mode="HTML")

@router.callback_query(F.data.startswith("reveal_with_balls:"))
async def reveal_with_balls(cb: CallbackQuery):
    user_id = int(cb.data.split(":")[1])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET balls = balls - 150 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    gs = active_games.get(cb.message.chat.id)
    if not gs:
        for g in active_games.values():
            if user_id in g.players:
                gs = g
                break
    if not gs:
        return await cb.answer("O‘yin topilmadi yoki tugallangan!", show_alert=True)
    
    player = gs.players[user_id]
    await cb.message.edit_text(f"💳 Kartangiz ochildi!\nSizning kartangiz: <b>{player.card}</b>\nXarajat: 150 balls", parse_mode="HTML")



# ────────────────────── KARTA FAZASI ──────────────────────
async def card_phase(gs: GameState, bot):
    assign_cards(gs)
    gs.card_phase_active = True
    keyboard_rows = []
    row = []
    found = []
    await bot.send_animation(gs.chat_id, FSInputFile("card_choose.mp4"),caption=f"""🌑 1. Karta tanlash bosqichi boshlandi
🔮 “O'yinchilar, diqqatingizni jamlang.”
Har biringizga maxfiy rol kartalari tarqatildi.
Endi esa — o'zingizga tegishli kartani tanlang. Bu sizning taqdiringizni belgilaydi.""")

    for p in gs.players.values():
        print(p.name, "card:", p.card)

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
    await send_other_players_cards(gs, bot)
    msg = await broadcast(bot, gs.chat_id, "🃏 <b>Karta tanlang!</b>", reply_markup=kb)
    gs.card_message_id = msg.message_id

    try:
        await asyncio.wait_for(wait_for_all_choices(gs), timeout=CARD_CHOICE_TIME)
    except asyncio.TimeoutError:
        pass

    gs.card_phase_active = False
    killed = []

    for p in gs.players.values():
        if p.chosen_card == p.card:
            found.append("@"+p.name)  

        if p.alive and p.chosen_card != p.card:
            p.alive = False
            killed.append("@"+p.name)
            others = [f"{pl.name} — {pl.card}" for pl in gs.players.values()
                      if pl.alive and pl.user_id != p.user_id]

            try:
                await bot.send_message(
                    p.user_id,
                    f"Siz o'ldingiz!\n\nBoshqalar kartalari:\n",
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

    if found:
        await broadcast(bot, gs.chat_id, f"Kartani topa olganlar: {', '.join(found)}")
    else:
        await broadcast(bot, gs.chat_id, "Hech kim kartasini topa olmadi.")

    if killed:
        await broadcast(bot, gs.chat_id, f"Kartani topa olmaganlar: {', '.join(killed)}")

    await safe_delete(bot, gs.chat_id, gs.card_message_id)
    gs.card_message_id = None

async def wait_for_all_choices(gs: GameState):
    while any(p.alive and p.chosen_card is None for p in gs.players.values()):
        await asyncio.sleep(1)

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
    a = "Ajal_game_test_bot"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Botga o'tish", url=f"https://t.me/{a}")]]
    )

    # Tun fazasi xabari
    await bot.send_animation(
        gs.chat_id,
        FSInputFile("ajal_game_gif.mp4"),
        caption=(
            "🌘 2. Tun fazasi boshlandi\n"
            "🌙 O'rmonni sukunat qopladi…\n"
            "Soya orasida kimdir harakatga tushdi.\n"
            "Bu tunda kimningdir hayoti xavf ostida.\n"
            "“Hech kimga ishonmang, tun — aldamchi.”"
        )
    )
    await broadcast(bot, gs.chat_id, "Boshlang:", reply_markup=kb)
    gs.night_actions.clear()

    # Najiro harakati
    if gs.najiro_id and gs.players[gs.najiro_id].alive:
        targets = [p for p in gs.players.values() if p.alive and p.user_id != gs.najiro_id]
        if targets:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=p.name, callback_data=f"najiro_kill:{gs.chat_id}:{p.user_id}")]
                                 for p in targets[:10]]
            )
            await bot.send_message(gs.najiro_id, "Siz najirosiz kimni o'ldirishni tanlang?", reply_markup=kb)

    # Qutqaruvchi harakati
    if gs.qutqaruvchi_id and gs.players[gs.qutqaruvchi_id].alive and not gs.qutqaruvchi_used:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=p.name, callback_data=f"qutqaruvchi_save:{gs.chat_id}:{p.user_id}")]
                             for p in gs.players.values() if p.alive]
        )
        await bot.send_message(gs.qutqaruvchi_id, "Siz Qutqaruvchisiz kimni qutqarishni xohlaysiz? (1 marta)", reply_markup=kb)

    # Madara harakati
    if gs.madara_id and gs.players[gs.madara_id].alive:
        targets = [p for p in gs.players.values() if p.alive and p.user_id != gs.madara_id and not p.poisoned]
        if targets:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=p.name, callback_data=f"madara_poison:{gs.chat_id}:{p.user_id}")]
                                 for p in targets[:10]]
            )
            await bot.send_message(gs.madara_id, "Kimni zaharlamoqchisiz?", reply_markup=kb)

    # Tun tugashini kutish
    await asyncio.sleep(NIGHT_DELAY)

    # Harakatlarni qayta ishlash
    victim = gs.night_actions.get("najiro_kill")
    saved = gs.night_actions.get("qutqaruvchi_save")
    poison = gs.night_actions.get("madara_poison")

    print("Night actions:", gs.night_actions)

    if victim:
        p_victim = gs.players.get(victim)
        if not p_victim:
            print("Xatolik: Najiro ning maqsadi topilmadi!")
        else:
            if victim == saved:
                await broadcast(bot, gs.chat_id, "Qutqaruvchi kimnidir saqlab qoldi!")
            else:
                p_victim.alive = False
                await broadcast(bot, gs.chat_id, f"<b>{p_victim.name}</b> kecha o'ldirildi! Qutqaruvchi saqlay olmadi." if saved else f"<b>{p_victim.name}</b> kecha o'ldirildi!")

    if poison:
        p_poisoned = gs.players.get(poison)
        if p_poisoned:
            p_poisoned.poisoned = True
            await bot.send_message(poison, "Siz <b>zaharlandingiz</b>!", parse_mode="HTML")



# ────────────────────── CALLBACKLAR ──────────────────────
@router.callback_query(F.data.startswith("najiro_kill:"))
async def najiro_kill(cb: CallbackQuery):
    print("Najiro kill:", cb.data)

    try:
        _, chat_id_str, target_id_str = cb.data.split(":")
        chat_id = int(chat_id_str)
        target_id = int(target_id_str)
    except:
        await cb.answer("Xatolik!", show_alert=True)
        return

    gs = active_games.get(chat_id)
    if not gs:
        await cb.answer("O'yin topilmadi!", show_alert=True)
        return

    if cb.from_user.id != gs.najiro_id:
        await cb.answer("Bu tugma sizga emas!", show_alert=True)
        return

    gs.night_actions["najiro_kill"] = target_id
    await cb.answer("Tanlandi!")

@router.callback_query(F.data.startswith("qutqaruvchi_save:"))
async def qutqaruvchi_save(cb: CallbackQuery):
    try:
        _, chat_id_str, target_id_str = cb.data.split(":")
        chat_id = int(chat_id_str)
        target_id = int(target_id_str)
    except:
        return await cb.answer("Xato!", show_alert=True)

    gs = active_games.get(chat_id)
    if not gs:
        return await cb.answer("O'yin topilmadi!")

    if cb.from_user.id != gs.qutqaruvchi_id:
        return await cb.answer("Bu sizga emas!", show_alert=True)

    gs.night_actions["qutqaruvchi_save"] = target_id
    gs.qutqaruvchi_used = True
    await cb.answer("Saqlab qoldi!")

@router.callback_query(F.data.startswith("madara_poison:"))
async def madara_poison(cb: CallbackQuery):
    try:
        _, chat_id_str, target_id_str = cb.data.split(":")
        chat_id = int(chat_id_str)
        target_id = int(target_id_str)
    except:
        return await cb.answer("Xatolik!", show_alert=True)

    gs = active_games.get(chat_id)
    if not gs:
        return await cb.answer("O'yin topilmadi!")

    if cb.from_user.id != gs.madara_id:
        return await cb.answer("Bu sizga emas!", show_alert=True)

    gs.night_actions["madara_poison"] = target_id
    await cb.answer("Zaharlandi!")















# ────────────────────── KUN ──────────────────────
async def day_phase(gs: GameState, bot):
    if not any(p.alive for p in gs.players.values()):
        await broadcast(bot, gs.chat_id, "Hech kim tirik qolmadi. O'yin tugadi.")
        return end_game(gs, bot)

    gs._nominee_counts.clear()
    gs._temp_vote = None

    # Kunduz boshlanishi animatsiyasi
    await bot.send_animation(
        gs.chat_id,
        FSInputFile("kun.mp4"),
        caption="""🌕 **KUNDUZ FAZASI BOSHLANDI** ☀️

Qorong‘u tun ortda qoldi... Endi haqiqat vaqti!
Kim yolg‘on gapiryapti? Kim qotil?
Gumon qiling, bahslash, ovoz bering!

⏱ Gumon qilish uchun 60 soniya vaqtingiz bor."""
    )

    alive_players = [p for p in gs.players.values() if p.alive]

    for player in alive_players:
        candidates = [p for p in alive_players if p.user_id != player.user_id]
        if not candidates:
            continue

        buttons = []
        for cand in candidates:
            buttons.append([InlineKeyboardButton(
                text=cand.name,
                callback_data=f"nominate:{gs.chat_id}:{cand.user_id}"
            )])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        try:
            await bot.send_message(player.user_id, "Kimni gumon qilasiz?", reply_markup=kb)
        except Exception as e:
            print(f"Xabar yuborilmadi {player.user_id}: {e}")

    await asyncio.sleep(NOMINATE_TIME)


    # Eng ko‘p gumon qilingan
    if not gs._nominee_counts:
        nominee = random.choice(alive_players)
        await broadcast(bot, gs.chat_id, f"Hech kim gumon qilinmadi!\nTasodifiy: <b>{nominee.name}</b>")
    else:
        nominee_id = max(gs._nominee_counts.items(), key=lambda x: x[1])[0]
        nominee = gs.players[nominee_id]
        count = gs._nominee_counts[nominee_id]
        await broadcast(bot, gs.chat_id, f"Eng ko‘p gumon qilingan: <b>{nominee.name}</b> ({count} ovoz)")

    # Ovoz berish
    vote_state = {"hang": 0, "spare": 0}
    voters = set()

    kb = get_vote_keyboard(gs, nominee.user_id)
    vote_msg = await broadcast(
        bot, gs.chat_id,
        f"<b>{nominee.name}</b> uchun ovoz bering!\n\nOsish: 0 | Qutqarish: 0",
        reply_markup=kb
    )

    gs._temp_vote = {
        "vote_state": vote_state,
        "voters": voters,
        "nominee_id": nominee.user_id,
        "vote_msg_id": vote_msg.message_id,
        "start_time": time.time(),
    }

    await asyncio.sleep(GROUP_VOTE_TIME)

    # Ovoz tugadi
    gs._temp_vote = None
    h, s = vote_state["hang"], vote_state["spare"]

    if h > s:
        nominee.alive = False
        emoji = "Obito kuchi" if nominee.user_id == gs.obito_id else "O‘ldirildi"
        await broadcast(bot, gs.chat_id, f"{emoji} <b>{nominee.name}</b> osildi!\n{h} — {s}")
    elif h == s:
        await broadcast(bot, gs.chat_id, f"Teng! {nominee.name} qutqarildi!")
    else:
        await broadcast(bot, gs.chat_id, f"<b>{nominee.name}</b> qutqarildi!\n{h} — {s}")



# ────────────────────── CALLBACKLAR ──────────────────────
@router.callback_query(F.data.startswith("vh:"))
async def vote_hang(cb: CallbackQuery):
    await handle_vote(cb, "hang")

@router.callback_query(F.data.startswith("vs:"))
async def vote_spare(cb: CallbackQuery):
    await handle_vote(cb, "spare")

def get_vote_keyboard(gs, nominee_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔥 Osish",
                callback_data=f"vh:{nominee_id}"  # vh = vote hang
            ),
            InlineKeyboardButton(
                text="🛡 Qutqarish",
                callback_data=f"vs:{nominee_id}"  # vs = vote spare
            )
        ]
    ])

async def handle_vote(cb: CallbackQuery, action: str):
    try:
        nominee_id = int(cb.data.split(":")[1])
        gs = active_games.get(cb.message.chat.id)
        if not gs or not gs._temp_vote:
            return await cb.answer("Ovoz berish tugagan!")

        if gs._temp_vote["nominee_id"] != nominee_id:
            return await cb.answer("Bu odam uchun ovoz berish tugagan!")

        voter_id = cb.from_user.id
        player = gs.players.get(voter_id)
        if not player or not player.alive:
            return await cb.answer("Siz o'ldingiz yoki o'yinda yo'qsiz!")

        if voter_id in gs._temp_vote["voters"]:
            return await cb.answer("Siz allaqachon ovoz berdingiz!")

        # Obito — 2 ovoz
        count = 2 if player.user_id == gs.obito_id else 1

        gs._temp_vote["voters"].add(voter_id)
        gs._temp_vote["vote_state"][action] += count

        await cb.answer(f"{count}x ovoz qabul qilindi!", show_alert=False)

        # Tugmalarni yangilash (hozirgi natija bilan)
        h = gs._temp_vote["vote_state"]["hang"]
        s = gs._temp_vote["vote_state"]["spare"]

        new_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🔥 Osish ({h})",
                    callback_data=f"vh:{nominee_id}"
                ),
                InlineKeyboardButton(
                    text=f"🛡 Qutqarish ({s})",
                    callback_data=f"vs:{nominee_id}"
                )
            ]
        ])

        await cb.message.edit_reply_markup(reply_markup=new_kb)

        # Matnni ham yangilab qo‘yamiz (chiroyli bo‘lsin)
        text = f"<b>{gs.players[nominee_id].name}</b> uchun ovoz berish...\n\nOsish: {h} | Qutqarish: {s}"
        await cb.message.edit_text(text, reply_markup=new_kb, parse_mode="HTML")

    except Exception as e:
        print("Vote error:", e)
        await cb.answer("Xatolik yuz berdi!")


@router.callback_query(F.data.startswith("nominate:"))
async def nominate_player(cb: CallbackQuery):
    try:
        _, cid, target_id = cb.data.split(":")
        cid = int(cid)
        target_id = int(target_id)

        gs = active_games.get(cid)

        if not gs:
            return await cb.answer("O'yin mavjud emas.", show_alert=True)

        voter_id = cb.from_user.id
        player = gs.players.get(voter_id)

        if not player or not player.alive:
            return await cb.answer("Siz gumon qila olmaysiz!")

        if target_id not in gs.players:
            return await cb.answer("Bunday o‘yinchi yo‘q!")

        count = 2 if voter_id == gs.obito_id else 1
        gs._nominee_counts[target_id] = gs._nominee_counts.get(target_id, 0) + count

        await cb.answer(f"Gumon qilindi! (+{count})")
    except Exception as e:
        print("Nominate ERR:", e)
        await cb.answer("Xatolik!")


@router.callback_query(F.data.startswith("nominate_auto:"))
async def nominate_auto(cb: CallbackQuery):
    try:
        _, cid, pid = cb.data.split(":")
        gs = active_games.get(int(cid))
        if not gs:
            return
        player = gs.players.get(int(cb.from_user.id))
        if not player or not player.alive:
            return await cb.answer("Siz ovoz bera olmaysiz!")
        candidates = [p for p in gs.players.values() if p.alive and p.user_id != player.user_id]
        suspect = random.choice(candidates)

        count = 2 if player.user_id == gs.obito_id else 1
        
        gs._nominee_counts[suspect.user_id] = gs._nominee_counts.get(suspect.user_id, 0) + count

        await cb.answer(f"🎲 Tasodifiy: {suspect.name} (+{count} ovoz)" +
                        (" | Obito kuchi!" if count == 2 else ""))
    except Exception as e:
        print("Nominate auto error:", e)














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



