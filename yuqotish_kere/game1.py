from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

router = Router()

# Konfiguratsiya
JOIN_TIME = 60  # Lobby ochiq vaqt
NOMINATE_TIME = 30  # Nomzod tanlash vaqti
GROUP_VOTE_TIME = 30  # Guruh ovoz berish vaqti
NIGHT_DELAY = 60  # Kecha davomiyligi
MADARA_POISON_ROUNDS = 2  # Madara har necha raundda zahar beradi

active_games: Dict[int, 'GameState'] = {}

@dataclass
class Player:
    user_id: int
    name: str
    alive: bool = True
    role: str = "Tinch o'yinchi"
    double_vote: bool = False  # Obito uchun
    saved_once: bool = False  # Qutqaruvchi o'zini davolagan bo'lsa
    poisoned: bool = False  # Madara zaharlagan bo'lsa
    can_save: bool = False  # Qutqaruvchi uchun

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
    night_actions: Dict[str, Optional[int]] = field(default_factory=dict)  # role -> target_id
    qutqaruvchi_used: bool = False

# --- Helpers ---
async def safe_delete(bot, chat_id: int, message_id: int):
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

async def broadcast(bot, chat_id: int, text: str, reply_markup=None):
    return await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode="HTML")

def assign_roles(gs: GameState):
    """Rollarni tasodifiy tarzda tayinlash"""
    alive_players = list(gs.players.values())
    random.shuffle(alive_players)
    
    # Majburiy rollar
    gs.najiro_id = alive_players[0].user_id
    alive_players[0].role = "👑 Najiro"
    
    gs.orochimaru_id = alive_players[1].user_id
    alive_players[1].role = "🐍 Orochimaru"
    
    gs.qutqaruvchi_id = alive_players[2].user_id
    alive_players[2].role = "🕊 Qutqaruvchi"
    alive_players[2].can_save = True
    
    gs.obito_id = alive_players[3].user_id
    alive_players[3].role = "🌀 Obito"
    alive_players[3].double_vote = True
    
    gs.madara_id = alive_players[4].user_id
    alive_players[4].role = "☠️ Madara"
    
    # Qolganlar tinch o'yinchilar
    for i in range(5, len(alive_players)):
        alive_players[i].role = "Tinch o'yinchi"

# --- Handlers ---
@router.message(Command("game"))
async def start_game(message: Message):
    chat_id = message.chat.id
    bot = message.bot
    
    if chat_id in active_games and active_games[chat_id].running:
        await message.answer("❌ O'yin allaqachon boshlangan!")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'yinga qo'shilish ✅", callback_data="join_game")],
        [InlineKeyboardButton(text="Boshlash (admin) ▶️", callback_data="start_game_admin")]
    ])
    
    lobby_msg = await message.answer(
        f"🃏 <b>AJAL O'YINI</b>\n\n"
        f"Qo'shilish uchun tugmani bosing.\n"
        f"Lobby {JOIN_TIME} soniya ochiq qoladi.\n\n"
        f"<i>Ishtirokchilar: 0</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    
    gs = GameState(chat_id=chat_id, lobby_message_id=lobby_msg.message_id)
    active_games[chat_id] = gs
    
    await asyncio.sleep(JOIN_TIME)
    
    gs = active_games.get(chat_id)
    if not gs or gs.running:
        return
    
    if len(gs.players) < 5:
        await broadcast(bot, chat_id, "⚠️ Kamida 5 ishtirokchi kerak. Lobby bekor qilindi.")
        await safe_delete(bot, chat_id, lobby_msg.message_id)
        active_games.pop(chat_id, None)
        return
    
    await safe_delete(bot, chat_id, lobby_msg.message_id)
    await begin_game(gs, bot)

@router.callback_query(F.data == "join_game")
async def join_game(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    gs = active_games.get(chat_id)
    
    if not gs or gs.running:
        await callback.answer("Lobby yopilgan yoki o'yin boshlangan.", show_alert=True)
        return
    
    user_id = callback.from_user.id
    if user_id in gs.players:
        await callback.answer("Siz allaqachon qo'shildingiz.")
        return
    
    gs.players[user_id] = Player(user_id=user_id, name=callback.from_user.full_name)
    await callback.answer("✅ O'yinga qo'shildingiz!")
    
    players_list = '\n'.join([f"{i+1}. {p.name}" for i, p in enumerate(gs.players.values())])
    await callback.message.edit_text(
        f"🃏 <b>AJAL O'YINI</b>\n\n"
        f"Qo'shilish uchun tugmani bosing.\n"
        f"Lobby {JOIN_TIME} soniya ochiq qoladi.\n\n"
        f"<b>Ishtirokchilar ({len(gs.players)}):</b>\n{players_list}",
        reply_markup=callback.message.reply_markup,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "start_game_admin")
async def start_game_admin(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    bot = callback.bot
    gs = active_games.get(chat_id)
    
    if not gs or gs.running:
        await callback.answer("Lobby topilmadi yoki o'yin boshlangan.")
        return
    
    if len(gs.players) < 5:
        await callback.answer("⚠️ Kamida 5 kishi kerak!", show_alert=True)
        return
    
    await callback.answer("O'yin boshlanmoqda...")
    await safe_delete(bot, chat_id, gs.lobby_message_id)
    await begin_game(gs, bot)

async def begin_game(gs: GameState, bot):
    gs.running = True
    gs._nominee_counts = {}
    gs._temp_vote = None
    gs.night_actions = {}
    
    # Rollarni tayinlash
    assign_roles(gs)
    
    # Animatsiya yuborish (agar fayl mavjud bo'lsa)
    try:
        from aiogram.types import FSInputFile
        file = FSInputFile("ajal_game_gif.mp4")
        await bot.send_animation(chat_id=gs.chat_id, animation=file, caption="🎮 O'yin boshlanmoqda!")
    except Exception:
        pass
    
    # Har bir o'yinchiga rolini yuborish
    for player in gs.players.values():
        try:
            role_info = get_role_description(player.role)
            await bot.send_message(
                player.user_id,
                f"<b>Sizning rolingiz:</b> {player.role}\n\n{role_info}",
                parse_mode="HTML"
            )
        except Exception:
            pass
    
    await broadcast(bot, gs.chat_id, 
        f"🔴 <b>O'yin boshlandi!</b>\n\n"
        f"Ishtirokchilar: {len(gs.players)}\n"
        f"Rollar tayinlandi. Raundlar boshlanmoqda..."
    )
    
    await asyncio.sleep(3)
    
    # O'yin sikli
    while gs.running:
        alive = [p for p in gs.players.values() if p.alive]
        
        # G'alaba shartini tekshirish
        najiro_alive = gs.players[gs.najiro_id].alive if gs.najiro_id in gs.players else False
        orochimaru_alive = gs.players[gs.orochimaru_id].alive if gs.orochimaru_id in gs.players else False
        
        if not najiro_alive and not orochimaru_alive:
            await broadcast(bot, gs.chat_id, 
                "🎉 <b>Tinch o'yinchilar g'alaba qozondi!</b>\n"
                "Najiro va Orochimaru ikkalasi ham yo'q qilindi!"
            )
            active_games.pop(gs.chat_id, None)
            return
        
        # Madara zahri tekshiruvi
        all_poisoned = all(p.poisoned for p in gs.players.values() if p.alive)
        if all_poisoned and len(alive) > 0:
            await broadcast(bot, gs.chat_id, 
                "☠️ <b>Madara g'alaba qozondi!</b>\n"
                "Barcha o'yinchilar zaharlangan!"
            )
            active_games.pop(gs.chat_id, None)
            return
        
        if len(alive) <= 2:
            winners = ", ".join(p.name for p in alive)
            await broadcast(bot, gs.chat_id, f"🎉 <b>O'yin tugadi!</b>\n\nQolganlar: {winners}")
            active_games.pop(gs.chat_id, None)
            return
        
        gs.round_number += 1
        await broadcast(bot, gs.chat_id, f"\n━━━ <b>Raund {gs.round_number}</b> ━━━")
        
        # === KECHA ===
        await night_phase(gs, bot)
        
        # === KUN: Nomzod tanlash ===
        await day_phase(gs, bot)
        
        await asyncio.sleep(2)

async def night_phase(gs: GameState, bot):
    """Kecha fazasi - rollar harakat qiladi"""
    await broadcast(bot, gs.chat_id, f"🌙 <b>Kecha tushdi...</b> ({NIGHT_DELAY} soniya)")
    
    gs.night_actions = {}
    
    # Najiro harakati
    najiro = gs.players.get(gs.najiro_id)
    if najiro and najiro.alive:
        targets = [p for p in gs.players.values() if p.alive and p.user_id != gs.najiro_id]
        if targets:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"{p.name}", callback_data=f"najiro_kill:{gs.chat_id}:{p.user_id}")]
                for p in targets[:10]  # Maksimal 10 ta tugma
            ])
            try:
                await bot.send_message(
                    najiro.user_id,
                    "👑 <b>Kimni o'ldirmoqchisiz?</b>",
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            except Exception:
                pass
    
    # Qutqaruvchi harakati
    qutqaruvchi = gs.players.get(gs.qutqaruvchi_id)
    if qutqaruvchi and qutqaruvchi.alive and not gs.qutqaruvchi_used:
        targets = [p for p in gs.players.values() if p.alive]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{p.name}", callback_data=f"qutqaruvchi_save:{gs.chat_id}:{p.user_id}")]
            for p in targets[:10]
        ])
        try:
            await bot.send_message(
                qutqaruvchi.user_id,
                "🕊 <b>Kimni qutqarmoqchisiz?</b> (Faqat bir marta)",
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception:
            pass
    
    # Madara harakati (har 2 raundda)
    if gs.round_number % MADARA_POISON_ROUNDS == 0:
        madara = gs.players.get(gs.madara_id)
        if madara and madara.alive:
            targets = [p for p in gs.players.values() if p.alive and p.user_id != gs.madara_id and not p.poisoned]
            if targets:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"{p.name}", callback_data=f"madara_poison:{gs.chat_id}:{p.user_id}")]
                    for p in targets[:10]
                ])
                try:
                    await bot.send_message(
                        madara.user_id,
                        "☠️ <b>Kimni zaharlamoqchisiz?</b>",
                        reply_markup=kb,
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
    
    await asyncio.sleep(NIGHT_DELAY)
    
    # Kecha natijalarini e'lon qilish
    victim_id = gs.night_actions.get("najiro_kill")
    saved_id = gs.night_actions.get("qutqaruvchi_save")
    poison_id = gs.night_actions.get("madara_poison")
    
    if victim_id and victim_id == saved_id:
        await broadcast(bot, gs.chat_id, "🕊 Qutqaruvchi kimnidir saqlab qoldi!")
    elif victim_id:
        victim = gs.players[victim_id]
        victim.alive = False
        await broadcast(bot, gs.chat_id, f"💀 <b>{victim.name}</b> kechasi o'ldirildi!")
    else:
        await broadcast(bot, gs.chat_id, "🌙 Kecha tinch o'tdi.")
    
    if poison_id:
        poisoned = gs.players[poison_id]
        poisoned.poisoned = True
        try:
            await bot.send_message(
                poison_id,
                "☠️ <b>Siz zaharlandingiz!</b>",
                parse_mode="HTML"
            )
        except Exception:
            pass

async def day_phase(gs: GameState, bot):
    """Kun fazasi - nomzod tanlash va ovoz berish"""
    gs._nominee_counts = {}
    
    await broadcast(bot, gs.chat_id, 
        f"☀️ <b>Kun boshlanadi!</b>\n\n"
        f"Gumon qilingan shaxsni shaxsiy xabarda tanlang! ({NOMINATE_TIME}s)"
    )
    
    # Har bir tirik o'yinchiga nomzod tanlash imkoniyati
    for player in gs.players.values():
        if player.alive:
            candidates = [p for p in gs.players.values() if p.alive and p.user_id != player.user_id]
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=p.name, callback_data=f"nominate:{gs.chat_id}:{player.user_id}:{p.user_id}")]
                for p in candidates[:10]
            ] + [[InlineKeyboardButton(text="🎲 Tasodifiy", callback_data=f"nominate_auto:{gs.chat_id}:{player.user_id}")]])
            
            try:
                await bot.send_message(
                    player.user_id,
                    "🔎 <b>Kimni gumon qilasiz?</b>",
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            except Exception:
                pass
    
    await asyncio.sleep(NOMINATE_TIME)
    
    # Eng ko'p ovoz olgan nomzodni aniqlash
    if not gs._nominee_counts:
        candidates = [p for p in gs.players.values() if p.alive]
        nominee = random.choice(candidates) if candidates else None
        await broadcast(bot, gs.chat_id, "⚠️ Hech kim nomzod qilinmadi. Tasodifiy tanlanadi.")
    else:
        top_id = max(gs._nominee_counts.items(), key=lambda x: x[1])[0]
        nominee = gs.players.get(top_id)
    
    if not nominee or not nominee.alive:
        await broadcast(bot, gs.chat_id, "⚠️ Nomzod topilmadi. Raund o'tkazib yuboriladi.")
        return
    
    await broadcast(bot, gs.chat_id, 
        f"🔎 <b>Nomzod:</b> {nominee.name}\n\n"
        f"Guruh ovoz beradi: Osish yoki Qutqarish? ({GROUP_VOTE_TIME}s)"
    )
    
    # Guruh ovozi
    vote_state = {"hang": 0, "spare": 0}
    voters = set()
    vote_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="👎 Osish", callback_data=f"vote_hang:{gs.chat_id}:{nominee.user_id}"),
        InlineKeyboardButton(text="👍 Qutqarish", callback_data=f"vote_spare:{gs.chat_id}:{nominee.user_id}")
    ]])
    
    vote_msg = await broadcast(bot, gs.chat_id, f"📊 Ovoz bering!", reply_markup=vote_kb)
    
    gs._temp_vote = {
        "vote_state": vote_state,
        "voters": voters,
        "nominee_id": nominee.user_id,
        "vote_msg_id": vote_msg.message_id
    }
    
    await asyncio.sleep(GROUP_VOTE_TIME)
    
    # Natijani hisoblash
    if gs._temp_vote:
        hang = gs._temp_vote["vote_state"]["hang"]
        spare = gs._temp_vote["vote_state"]["spare"]
        
        try:
            await bot.edit_message_reply_markup(gs.chat_id, vote_msg.message_id, reply_markup=None)
        except Exception:
            pass
        
        if hang > spare:
            nominee.alive = False
            await broadcast(bot, gs.chat_id, 
                f"⚖️ <b>Qaror:</b> {nominee.name} <b>osildi!</b>\n"
                f"Ovozlar: 👎 {hang} - 👍 {spare}"
            )
            
            # Najiro tekshiruvi
            if nominee.user_id == gs.najiro_id:
                orochimaru_alive = gs.players[gs.orochimaru_id].alive if gs.orochimaru_id in gs.players else False
                if not orochimaru_alive:
                    await broadcast(bot, gs.chat_id, "🔴 <b>Najiro o'ldirildi! Tinch o'yinchilar g'alaba qozondi!</b> 🎉")
                    active_games.pop(gs.chat_id, None)
                    gs.running = False
                else:
                    await broadcast(bot, gs.chat_id, "🔴 <b>Najiro o'ldirildi, lekin Orochimaru tirik!</b> O'yin davom etadi...")
        elif spare > hang:
            await broadcast(bot, gs.chat_id, 
                f"✅ <b>Qaror:</b> {nominee.name} <b>qutqarildi!</b>\n"
                f"Ovozlar: 👎 {hang} - 👍 {spare}"
            )
        else:
            await broadcast(bot, gs.chat_id, 
                f"⚖️ <b>Qaror:</b> Ovozlar teng! {nominee.name} qutqarildi.\n"
                f"Ovozlar: 👎 {hang} - 👍 {spare}"
            )
    
    gs._temp_vote = None

def get_role_description(role: str) -> str:
    """Rol haqida ma'lumot"""
    descriptions = {
        "👑 Najiro": "Siz asosiy yovuzsiz! Har kecha bitta o'yinchini o'ldiring. Maqsad: hamma tinch o'yinchilarni yo'q qilish.",
        "🐍 Orochimaru": "Siz Najironing sherigi. Agar Najiro o'lsa, siz tirik bo'lsangiz o'yin davom etadi.",
        "🕊 Qutqaruvchi": "Siz har kecha bitta kishini qutqara olasiz. Bu kuchni faqat bir marta ishlata olasiz!",
        "🌀 Obito": "Sizning ovozingiz 2 kishining ovoziga teng!",
        "☠️ Madara": "Har 2 raundda bitta kishini zaharlaysiz. Agar hamma zaharlansa, siz g'alaba qolasiz!",
        "Tinch o'yinchi": "Siz oddiy o'yinchisiz. Yovuzlarni topishga harakat qiling!"
    }
    return descriptions.get(role, "Tinch o'yinchi")

# === Callback Handlers ===

@router.callback_query(F.data.startswith("najiro_kill:"))
async def najiro_kill(callback: CallbackQuery):
    try:
        _, chat_id_str, target_id_str = callback.data.split(":")
        chat_id = int(chat_id_str)
        target_id = int(target_id_str)
    except Exception:
        await callback.answer("Xato.")
        return
    
    gs = active_games.get(chat_id)
    if not gs or callback.from_user.id != gs.najiro_id:
        await callback.answer("Xato.")
        return
    
    gs.night_actions["najiro_kill"] = target_id
    await callback.answer(f"✅ Nishon tanlandi!")
    try:
        await callback.message.edit_text("✅ Tanlov amalga oshirildi.")
    except Exception:
        pass

@router.callback_query(F.data.startswith("qutqaruvchi_save:"))
async def qutqaruvchi_save(callback: CallbackQuery):
    try:
        _, chat_id_str, target_id_str = callback.data.split(":")
        chat_id = int(chat_id_str)
        target_id = int(target_id_str)
    except Exception:
        await callback.answer("Xato.")
        return
    
    gs = active_games.get(chat_id)
    if not gs or callback.from_user.id != gs.qutqaruvchi_id:
        await callback.answer("Xato.")
        return
    
    gs.night_actions["qutqaruvchi_save"] = target_id
    gs.qutqaruvchi_used = True
    await callback.answer(f"✅ Qutqarildi!")
    try:
        await callback.message.edit_text("✅ Qutqaruv amalga oshirildi.")
    except Exception:
        pass

@router.callback_query(F.data.startswith("madara_poison:"))
async def madara_poison(callback: CallbackQuery):
    try:
        _, chat_id_str, target_id_str = callback.data.split(":")
        chat_id = int(chat_id_str)
        target_id = int(target_id_str)
    except Exception:
        await callback.answer("Xato.")
        return
    
    gs = active_games.get(chat_id)
    if not gs or callback.from_user.id != gs.madara_id:
        await callback.answer("Xato.")
        return
    
    gs.night_actions["madara_poison"] = target_id
    await callback.answer(f"✅ Zaharlandi!")
    try:
        await callback.message.edit_text("✅ Zahar qo'llandi.")
    except Exception:
        pass

@router.callback_query(F.data.startswith("nominate:"))
async def nominate_player(callback: CallbackQuery):
    try:
        _, chat_id_str, voter_id_str, nominee_id_str = callback.data.split(":")
        chat_id = int(chat_id_str)
        voter_id = int(voter_id_str)
        nominee_id = int(nominee_id_str)
    except Exception:
        await callback.answer("Xato.")
        return
    
    gs = active_games.get(chat_id)
    if not gs or callback.from_user.id != voter_id:
        await callback.answer("Xato.")
        return
    
    gs._nominee_counts[nominee_id] = gs._nominee_counts.get(nominee_id, 0) + 1
    nominee_name = gs.players[nominee_id].name
    await callback.answer(f"✅ {nominee_name} nomzod qilindi!")
    try:
        await callback.message.edit_text(f"✅ Siz {nominee_name}ni nomzod qildingiz.")
    except Exception:
        pass

@router.callback_query(F.data.startswith("nominate_auto:"))
async def nominate_auto(callback: CallbackQuery):
    try:
        _, chat_id_str, player_id_str = callback.data.split(":")
        chat_id = int(chat_id_str)
        player_id = int(player_id_str)
    except Exception:
        await callback.answer("Xato.")
        return
    
    gs = active_games.get(chat_id)
    if not gs or callback.from_user.id != player_id:
        await callback.answer("Xato.")
        return
    
    candidates = [p for p in gs.players.values() if p.alive and p.user_id != player_id]
    if not candidates:
        await callback.answer("Nomzod yo'q.")
        return
    
    suspect = random.choice(candidates)
    gs._nominee_counts[suspect.user_id] = gs._nominee_counts.get(suspect.user_id, 0) + 1
    await callback.answer(f"✅ {suspect.name} nomzod qilindi!")
    try:
        await callback.message.edit_text(f"✅ Tasodifiy: {suspect.name} nomzod qilindi.")
    except Exception:
        pass

@router.callback_query(F.data.startswith("vote_hang:"))
async def vote_hang(callback: CallbackQuery):
    await handle_vote(callback, "hang")

@router.callback_query(F.data.startswith("vote_spare:"))
async def vote_spare(callback: CallbackQuery):
    await handle_vote(callback, "spare")

async def handle_vote(callback: CallbackQuery, action: str):
    try:
        _, chat_id_str, nominee_id_str = callback.data.split(":")
        chat_id = int(chat_id_str)
        nominee_id = int(nominee_id_str)
    except Exception:
        await callback.answer("Xato.")
        return
    
    gs = active_games.get(chat_id)
    if not gs or not gs._temp_vote or gs._temp_vote.get("nominee_id") != nominee_id:
        await callback.answer("Ovoz yig'ish tugagan.")
        return
    
    voter_id = callback.from_user.id
    if voter_id in gs._temp_vote["voters"]:
        await callback.answer("Siz allaqachon ovoz berdingiz.")
        return
    
    voter = gs.players.get(voter_id)
    vote_count = 2 if voter and voter.double_vote else 1  # Obito uchun 2 ovoz
    
    gs._temp_vote["voters"].add(voter_id)
    gs._temp_vote["vote_state"][action] += vote_count
    
    action_text = "osish" if action == "hang" else "qutqarish"
    await callback.answer(f"✅ Siz {action_text}ga ovoz berdingiz!" + (" (2x)" if vote_count == 2 else ""))