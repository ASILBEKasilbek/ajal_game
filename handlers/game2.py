from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

router = Router()

# Konfiguratsiya
JOIN_TIME = 60
NOMINATE_TIME = 30
GROUP_VOTE_TIME = 30
NIGHT_DELAY = 60
MADARA_POISON_ROUNDS = 2
CARD_CHOICE_TIME = 25  # Karta tanlash vaqti

active_games: Dict[int, 'GameState'] = {}

# Kartalar
CARDS = [
    "🃏 ♣️ Chillik",
    "🃏 ♥️ Toppon",
    "🃏 ♦️ G'ishtin",
    "🃏 ♠️ Qirol Qarg'a"
]

@dataclass
class Player:
    user_id: int
    name: str
    alive: bool = True
    role: str = "Tinch o'yinchi"
    double_vote: bool = False
    saved_once: bool = False
    poisoned: bool = False
    can_save: bool = False
    card: Optional[str] = None  # Yangi: karta
    chosen_card: Optional[str] = None  # Tanlagan karta

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
    _nominee_counts: Dict[int, int] = field(default_factory=dict)
    _temp_vote: Optional[Dict] = None
    night_actions: Dict[str, Optional[int]] = field(default_factory=dict)
    qutqaruvchi_used: bool = False
    card_message_id: Optional[int] = None
    card_phase_active: bool = False

# --- Helpers ---
async def safe_delete(bot, chat_id: int, message_id: int):
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

async def broadcast(bot, chat_id: int, text: str, reply_markup=None):
    return await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode="HTML")

def assign_roles(gs: GameState):
    alive_players = list(gs.players.values())
    random.shuffle(alive_players)
    gs.najiro_id = alive_players[0].user_id
    alive_players[0].role = "Najiro"
    gs.orochimaru_id = alive_players[1].user_id
    alive_players[1].role = "Orochimaru"
    gs.qutqaruvchi_id = alive_players[2].user_id
    alive_players[2].role = "Qutqaruvchi"
    alive_players[2].can_save = True
    gs.obito_id = alive_players[3].user_id
    alive_players[3].role = "Obito"
    alive_players[3].double_vote = True
    gs.madara_id = alive_players[4].user_id
    alive_players[4].role = "Madara"
    for i in range(5, len(alive_players)):
        alive_players[i].role = "Tinch o'yinchi"

def assign_cards(gs: GameState):
    """Har o'yinchiga tasodifiy karta berish"""
    for player in gs.players.values():
        if player.alive:
            player.card = random.choice(CARDS)
            player.chosen_card = None

# --- Handlers ---
@router.message(Command("game"))
async def start_game(message: Message):
    chat_id = message.chat.id
    bot = message.bot
    if chat_id in active_games and active_games[chat_id].running:
        await message.answer("O'yin allaqachon boshlangan!")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'yinga qo'shilish", url=f"https://t.me/{(await bot.get_me()).username}?start=game")],
        [InlineKeyboardButton(text="Boshlash (admin)", callback_data="start_game_admin")]
    ])
    lobby_msg = await message.answer(
        f"<b>AJAL O'YINI</b>\n\n"
        f"Qo'shilish uchun tugmani bosing.\n"
        f"Lobby {JOIN_TIME} soniya ochiq.\n\n"
        f"<i>Ishtirokchilar: 0</i>",
        reply_markup=kb, parse_mode="HTML"
    )
    gs = GameState(chat_id=chat_id, lobby_message_id=lobby_msg.message_id)
    active_games[chat_id] = gs
    await asyncio.sleep(JOIN_TIME)

    gs = active_games.get(chat_id)
    if not gs or gs.running or len(gs.players) < 5:
        await broadcast(bot, chat_id, "Kamida 5 kishi kerak. Lobby yopildi.")
        await safe_delete(bot, chat_id, lobby_msg.message_id)
        active_games.pop(chat_id, None)
        return

    await safe_delete(bot, chat_id, lobby_msg.message_id)
    await begin_game(gs, bot)

from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.filters import CommandStart

@router.message(CommandStart(deep_link=True))
async def start_with_game(message: Message, deep_link: str):
    if deep_link == "game":
        user = message.from_user
        user_id = user.id
        bot = message.bot

        # Lobbyni topish (agar bir nechta chatda o'yin bo'lsa)
        # Masalan, faqat bitta chatda lobby ochilgan bo'lsa:
        gs = next((g for g in active_games.values() if not g.running), None)
        if not gs:
            await message.answer("⚠️ Hozir hech qanday o'yin lobbysi ochiq emas.")
            return

        # Agar foydalanuvchi allaqachon o'yindaysa
        if user_id in gs.players:
            await message.answer("Siz allaqachon o‘yindasiz!")
            return

        # O'yinga qo'shish
        gs.players[user_id] = Player(user_id=user_id, name=user.full_name)

        # Shaxsiy chatga xabar yuborish
        try:
            await bot.send_message(user_id, "🎮 Siz o‘yinga qo‘shildingiz!")
        except (TelegramForbiddenError, TelegramBadRequest):
            # Agar foydalanuvchi botni start bermagan bo'lsa, o'tkazib yuboramiz
            pass

        # Lobbydagi ishtirokchilar ro'yxatini yangilash
        players_list = '\n'.join([f"{i+1}. {p.name}" for i, p in enumerate(gs.players.values())])
        await bot.edit_message_text(
            chat_id=gs.chat_id,
            message_id=gs.lobby_message_id,
            text=(
                f"<b>AJAL O'YINI</b>\n\n"
                f"Lobby {JOIN_TIME} soniya ochiq.\n\n"
                f"<b>Ishtirokchilar ({len(gs.players)}):</b>\n{players_list}"
            ),
            reply_markup=None,  # Inline tugmalarni saqlash mumkin
            parse_mode="HTML"
        )


@router.callback_query(F.data == "join_game")
async def join_game(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    gs = active_games.get(chat_id)
    if not gs or gs.running:
        await callback.answer("Lobby yopilgan.", show_alert=True)
        return

    user = callback.from_user
    user_id = user.id
    bot = callback.bot

    # ✅ Foydalanuvchi start bosganini tekshirish
    try:
        await bot.send_chat_action(user_id, "typing")
    except (TelegramForbiddenError, TelegramBadRequest):
        # Start bermagan bo‘lsa → faqat alert va bot linki
        bot_username = (await bot.get_me()).username
        start_url = f"https://t.me/{bot_username}"
        await callback.answer(
            f"❌ Siz hali botni ishga tushirmagansiz! Avval botga kiring: {start_url}",
            show_alert=True
        )
        return

    # ✅ Foydalanuvchi allaqachon o‘yinda bo‘lsa
    if user_id in gs.players:
        await callback.answer("Siz allaqachon o‘yindasiz.")
        return

    # ✅ O‘yinga yangi o‘yinchini qo‘shish
    gs.players[user_id] = Player(user_id=user_id, name=user.full_name)

    # ✅ Foydalanuvchiga alert bilan xabar yuborish
    await callback.answer("🎮 Siz o‘yinga qo‘shildingiz!", show_alert=True)

    # ✅ Lobbydagi ishtirokchilar ro‘yxatini yangilash
    players_list = '\n'.join([f"{i+1}. {p.name}" for i, p in enumerate(gs.players.values())])
    await callback.message.edit_text(
        f"<b>AJAL O'YINI</b>\n\n"
        f"Lobby {JOIN_TIME} soniya ochiq.\n\n"
        f"<b>Ishtirokchilar ({len(gs.players)}):</b>\n{players_list}",
        reply_markup=callback.message.reply_markup,  # Inline tugmalar o'zgarmaydi
        parse_mode="HTML"
    )

@router.callback_query(F.data == "start_game_admin")
async def start_game_admin(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    bot = callback.bot
    gs = active_games.get(chat_id)
    if not gs or gs.running or len(gs.players) < 5:
        await callback.answer("Kamida 5 kishi kerak!", show_alert=True)
        return
    await callback.answer("O'yin boshlanmoqda...")
    await safe_delete(bot, chat_id, gs.lobby_message_id)
    await begin_game(gs, bot)

async def begin_game(gs: GameState, bot):
    gs.running = True
    assign_roles(gs)
    try:
        from aiogram.types import FSInputFile
        file = FSInputFile("ajal_game_gif.mp4")
        await bot.send_animation(gs.chat_id, animation=file, caption="O'yin boshlanmoqda!")
    except Exception:
        pass

    for player in gs.players.values():
        role_info = get_role_description(player.role)
        await bot.send_message(player.user_id, f"<b>Rolingiz:</b> {player.role}\n\n{role_info}", parse_mode="HTML")

    await broadcast(bot, gs.chat_id, f"<b>O'yin boshlandi!</b>\nIshtirokchilar: {len(gs.players)}")
    await asyncio.sleep(3)

    while gs.running:
        alive = [p for p in gs.players.values() if p.alive]
        if len(alive) <= 2:
            winners = ", ".join(p.name for p in alive)
            await end_game(gs, bot, f"O'yin tugadi! Qolganlar: {winners}")
            return

        najiro_alive = gs.players[gs.najiro_id].alive if gs.najiro_id in gs.players else False
        orochimaru_alive = gs.players[gs.orochimaru_id].alive if gs.orochimaru_id in gs.players else False
        if not najiro_alive and not orochimaru_alive:
            await end_game(gs, bot, "<b>Tinch o'yinchilar g'alaba qozondi!</b>\nNajiro va Orochimaru yo'q qilindi!")
            return

        all_poisoned = all(p.poisoned for p in alive)
        if all_poisoned and len(alive) > 0:
            await end_game(gs, bot, "<b>Madara g'alaba qozondi!</b>\nHamma zaharlandi!")
            return

        gs.round_number += 1
        await broadcast(bot, gs.chat_id, f"\n━━━ <b>Raund {gs.round_number}</b> ━━━")

        # Karta tanlash
        await card_phase(gs, bot)
        # Kecha
        await night_phase(gs, bot)
        # Kun
        await day_phase(gs, bot)
        await asyncio.sleep(2)

async def card_phase(gs: GameState, bot):
    """Karta tanlash fazasi"""
    assign_cards(gs)
    gs.card_phase_active = True

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=card, callback_data=f"choose_card:{gs.chat_id}:{i}")]
        for i, card in enumerate(CARDS)
    ])
    msg = await broadcast(bot, gs.chat_id,
        "Karta tanlang!\n\n"
        "Quyidagi kartalardan birini tanlang:",
        reply_markup=kb
    )
    gs.card_message_id = msg.message_id

    await asyncio.sleep(CARD_CHOICE_TIME)
    gs.card_phase_active = False

    # Notug'ri tanlaganlarni o'ldirish
    killed = []
    for player in gs.players.values():
        if player.alive and player.chosen_card != player.card:
            player.alive = False
            killed.append(player.name)
            # Maxfiy xabar: boshqalar kartalari
            others = [f"{p.name} {p.card}" for p in gs.players.values() if p.alive and p.user_id != player.user_id]
            try:
                await bot.send_message(player.user_id,
                    "Siz noto'g'ri karta tanladingiz va o'ldingiz!\n\n"
                    "Boshqa o'yinchilar kartalari:\n" + "\n".join(others),
                    parse_mode="HTML"
                )
                # Tirilish taklifi
                revive_kb = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="1 olmosga tirilish", callback_data=f"revive:{gs.chat_id}:{player.user_id}")
                ]])
                await bot.send_message(player.user_id, "1 olmosga qayta tirilishni xohlaysizmi?", reply_markup=revive_kb)
            except:
                pass

    if killed:
        await broadcast(bot, gs.chat_id, f"O'ldirildi: {', '.join(killed)}")

    await safe_delete(bot, gs.chat_id, gs.card_message_id)

@router.callback_query(F.data.startswith("choose_card:"))
async def choose_card(callback: CallbackQuery):
    if not active_games.get(callback.message.chat.id):
        return
    gs = active_games[callback.message.chat.id]
    if not gs.card_phase_active:
        await callback.answer("Vaqt tugadi.")
        return
    try:
        _, chat_id_str, idx_str = callback.data.split(":")
        idx = int(idx_str)
        chosen = CARDS[idx]
    except:
        await callback.answer("Xato.")
        return

    player = gs.players.get(callback.from_user.id)
    if not player or not player.alive:
        await callback.answer("Siz o'yinda emassiz.")
        return

    player.chosen_card = chosen
    await callback.answer(f"{chosen} tanlandi!")

@router.callback_query(F.data.startswith("revive:"))
async def revive_player(callback: CallbackQuery):
    try:
        _, chat_id_str, user_id_str = callback.data.split(":")
        chat_id = int(chat_id_str)
        user_id = int(user_id_str)
    except:
        return
    gs = active_games.get(chat_id)
    if not gs:
        return
    player = gs.players.get(user_id)
    if not player or player.alive:
        await callback.answer("Siz tiriksiniz.")
        return
    player.alive = True
    await callback.answer("1 olmos evaziga tirildingiz!")
    await broadcast(callback.bot, chat_id, f"{player.name} 1 olmosga tirildi!")

async def night_phase(gs: GameState, bot):
    await broadcast(bot, gs.chat_id, f"Kecha tushdi... ({NIGHT_DELAY}s)")
    gs.night_actions = {}

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
        targets = [p for p in gs.players.values() if p.alive]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=p.name, callback_data=f"qutqaruvchi_save:{gs.chat_id}:{p.user_id}")]
            for p in targets[:10]
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

    victim_id = gs.night_actions.get("najiro_kill")
    saved_id = gs.night_actions.get("qutqaruvchi_save")
    poison_id = gs.night_actions.get("madara_poison")

    if victim_id and victim_id == saved_id:
        await broadcast(bot, gs.chat_id, "Qutqaruvchi kimnidir saqlab qoldi!")
    elif victim_id:
        victim = gs.players[victim_id]
        victim.alive = False
        await broadcast(bot, gs.chat_id, f"<b>{victim.name}</b> kecha o'ldirildi!")
    else:
        await broadcast(bot, gs.chat_id, "Kecha tinch o'tdi.")

    if poison_id:
        p = gs.players[poison_id]
        p.poisoned = True
        await bot.send_message(poison_id, "Siz <b>zaharlandingiz</b>!", parse_mode="HTML")

async def day_phase(gs: GameState, bot):
    gs._nominee_counts = {}
    await broadcast(bot, gs.chat_id, f"Kun boshlandi! Gumonli shaxsni tanlang ({NOMINATE_TIME}s)")

    for player in gs.players.values():
        if player.alive:
            candidates = [p for p in gs.players.values() if p.alive and p.user_id != player.user_id]
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=p.name, callback_data=f"nominate:{gs.chat_id}:{player.user_id}:{p.user_id}")]
                for p in candidates[:10]
            ] + [[InlineKeyboardButton(text="Tasodifiy", callback_data=f"nominate_auto:{gs.chat_id}:{player.user_id}")]])
            await bot.send_message(player.user_id, "Kimni gumon qilasiz?", reply_markup=kb)

    await asyncio.sleep(NOMINATE_TIME)

    if not gs._nominee_counts:
        nominee = random.choice([p for p in gs.players.values() if p.alive])
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
        "vote_state": vote_state, "voters": voters, "nominee_id": nominee.user_id,
        "vote_msg_id": vote_msg.message_id, "bot": bot
    }

    # Real-time ovoz yangilash
    for _ in range(GROUP_VOTE_TIME):
        await asyncio.sleep(1)
        if gs._temp_vote:
            h, s = vote_state["hang"], vote_state["spare"]
            try:
                await bot.edit_message_text(
                    chat_id=gs.chat_id, message_id=vote_msg.message_id,
                    text=f"Ovozlar: {h} - {s}", reply_markup=kb
                )
            except:
                pass

    # Yakuniy
    if gs._temp_vote:
        h, s = vote_state["hang"], vote_state["spare"]
        await bot.edit_message_reply_markup(gs.chat_id, vote_msg.message_id, reply_markup=None)
        if h > s:
            nominee.alive = False
            await broadcast(bot, gs.chat_id, f"<b>{nominee.name} osildi!</b>\nOvozlar: {h} - {s}")
        else:
            await broadcast(bot, gs.chat_id, f"<b>{nominee.name} qutqarildi!</b>\nOvozlar: {h} - {s}")
        gs._temp_vote = None

# Faqat o'yinchilar ovoz bera oladi + auto-delete
@router.message()
async def check_group_message(message: Message):
    chat_id = message.chat.id
    gs = active_games.get(chat_id)
    if not gs or not gs.running or not gs._temp_vote:
        return
    if message.from_user.id not in gs.players:
        return
    if message.text in ["", "Osish", "Qutqarish"]:
        await message.delete()

async def end_game(gs: GameState, bot, result_text: str):
    roles = "\n".join([f"{p.name} — {p.role}" for p in gs.players.values()])
    await broadcast(bot, gs.chat_id, f"{result_text}\n\n<b>Rollari:</b>\n{roles}")
    active_games.pop(gs.chat_id, None)
    gs.running = False

def get_role_description(role: str) -> str:
    d = {
        "Najiro": "Har kecha o'ldiradi.",
        "Orochimaru": "Najiro sherigi.",
        "Qutqaruvchi": "1 marta qutqaradi.",
        "Obito": "Ovozi 2 barobar.",
        "Madara": "Har 2 raundda zaharlaydi.",
        "Tinch o'yinchi": "Oddiy o'yinchi."
    }
    return d.get(role, "Tinch o'yinchi")

# Callback handlers (qisqartirilgan)
@router.callback_query(F.data.startswith("najiro_kill:"))
async def najiro_kill(callback: CallbackQuery):
    gs = active_games.get(callback.message.chat.id)
    if gs and callback.from_user.id == gs.najiro_id:
        _, _, tid = callback.data.split(":")
        gs.night_actions["najiro_kill"] = int(tid)
        await callback.answer("Tanlandi!")

@router.callback_query(F.data.startswith("qutqaruvchi_save:"))
async def qutqaruvchi_save(callback: CallbackQuery):
    gs = active_games.get(callback.message.chat.id)
    if gs and callback.from_user.id == gs.qutqaruvchi_id:
        _, _, tid = callback.data.split(":")
        gs.night_actions["qutqaruvchi_save"] = int(tid)
        gs.qutqaruvchi_used = True
        await callback.answer("Qutqarildi!")

@router.callback_query(F.data.startswith("madara_poison:"))
async def madara_poison(callback: CallbackQuery):
    gs = active_games.get(callback.message.chat.id)
    if gs and callback.from_user.id == gs.madara_id:
        _, _, tid = callback.data.split(":")
        gs.night_actions["madara_poison"] = int(tid)
        await callback.answer("Zaharlandi!")

@router.callback_query(F.data.startswith("nominate:"))
async def nominate_player(callback: CallbackQuery):
    try:
        _, cid, vid, nid = callback.data.split(":")
        gs = active_games.get(int(cid))
        if gs and callback.from_user.id == int(vid):
            gs._nominee_counts[int(nid)] = gs._nominee_counts.get(int(nid), 0) + 1
            await callback.answer("Nomzod qilindi!")
    except:
        pass

@router.callback_query(F.data.startswith("nominate_auto:"))
async def nominate_auto(callback: CallbackQuery):
    try:
        _, cid, pid = callback.data.split(":")
        gs = active_games.get(int(cid))
        if gs and callback.from_user.id == int(pid):
            candidates = [p for p in gs.players.values() if p.alive and p.user_id != int(pid)]
            suspect = random.choice(candidates)
            gs._nominee_counts[suspect.user_id] = gs._nominee_counts.get(suspect.user_id, 0) + 1
            await callback.answer(f"{suspect.name} tanlandi!")
    except:
        pass

@router.callback_query(F.data.startswith("vote_hang:"))
async def vote_hang(callback: CallbackQuery):
    await handle_vote(callback, "hang")

@router.callback_query(F.data.startswith("vote_spare:"))
async def vote_spare(callback: CallbackQuery):
    await handle_vote(callback, "spare")

async def handle_vote(callback: CallbackQuery, action: str):
    try:
        _, cid, nid = callback.data.split(":")
        gs = active_games.get(int(cid))
        if not gs or not gs._temp_vote or gs._temp_vote["nominee_id"] != int(nid):
            await callback.answer("Ovoz tugagan.")
            return
        voter_id = callback.from_user.id
        if voter_id not in gs.players or not gs.players[voter_id].alive or voter_id in gs._temp_vote["voters"]:
            await callback.answer("Ovoz bera olmaysiz.")
            return
        vote_count = 2 if gs.players[voter_id].double_vote else 1
        gs._temp_vote["voters"].add(voter_id)
        gs._temp_vote["vote_state"][action] += vote_count
        await callback.answer(f"{vote_count}x ovoz!")
    except:
        pass