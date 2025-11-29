from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from database.user_models import get_guruhlar
from config import DB_FILE
import random
import sqlite3, json
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.battle_models import save_vote, get_cost,get_name, get_balance, update_balance
from datetime import datetime
import asyncio
from datetime import datetime, timezone, timedelta
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup


router = Router()
LOCAL_TZ = timezone(timedelta(hours=5))  


def parse_scheduled_time(raw: str) -> datetime:
    """Return timezone-aware datetime for stored battle timestamps."""
    if not raw:
        raise ValueError("empty scheduled_time")
    candidates = ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"]
    for fmt in candidates:
        try:
            dt = datetime.strptime(raw, fmt)
            break
        except ValueError:
            continue
    else:
        dt = datetime.fromisoformat(raw)
    return dt if dt.tzinfo else dt.replace(tzinfo=LOCAL_TZ)

def generate_pairs(players):
    random.shuffle(players)
    pairs = []

    while len(players) >= 2:
        p1 = players.pop()
        p2 = players.pop()
        pairs.append((p1, p2))

    if players:
        pairs.append((players[0], None))

    return pairs

@router.callback_query(F.data.startswith("join_1vs1"))
async def join_battle(call: CallbackQuery):
    battle_id = int(call.data.split(":")[1])
    user_id = call.from_user.id

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT players FROM battle_1vs1 WHERE id = ?", (battle_id,))
    players_json = c.fetchone()[0]
    players = json.loads(players_json)

    if user_id not in players:
        players.append(user_id)

    c.execute("UPDATE battle_1vs1 SET players = ? WHERE id = ?",
              (json.dumps(players), battle_id))
    
    scheduled_time = c.execute("SELECT scheduled_time FROM battle_1vs1 WHERE id = ?", (battle_id,)).fetchone()[0]
    conn.commit()
    conn.close()

    dt = parse_scheduled_time(scheduled_time).astimezone(LOCAL_TZ)
    time_str = dt.strftime("%d %B %Y, %H:%M %p") 

    await call.message.edit_text(
        f"""
    <b>🎮 1 vs 1 Battle!</b>

    🏆 <i>Siz qo'shildingiz!</i>

    ⏱ <u>Boshlanish vaqti:</u> <b>{time_str}</b>
    """,
        parse_mode="HTML"
    )
    await call.answer("✅ Battle ga qo'shildingiz!", show_alert=True)

async def battle_scheduler(bot: Bot):
    while True:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        c.execute("SELECT id, players, scheduled_time, status FROM battle_1vs1")
        battles = c.fetchall()

        now = datetime.now(LOCAL_TZ)

        for battle_id, players_json, time_str, status in battles:
            try:
                battle_time = parse_scheduled_time(time_str).astimezone(LOCAL_TZ)
            except Exception as exc:
                print(f"[battle_scheduler] Invalid scheduled_time for battle {battle_id}: {time_str} ({exc})")
                continue

            # 1 kun o‘tgach tugagan battle’larni yakunlash
            if now >= battle_time + timedelta(days=1):
                if status != 'finished':
                    # Battle holatini tugadi deb belgilaymiz
                    c.execute("UPDATE battle_1vs1 SET status='finished' WHERE id=?", (battle_id,))
                    conn.commit()

                    # Har bir pair uchun natijani aniqlash
                    c.execute("SELECT id, player1, player2, votes1, votes2 FROM battle_pairs WHERE battle_id=?", (battle_id,))
                    pairs = c.fetchall()

                    for pair_id, p1, p2, votes1, votes2 in pairs:
                        if votes1 > votes2:
                            winner = p1
                        elif votes2 > votes1:
                            winner = p2
                        else:
                            winner = 0 

                        # battle_pairs jadvalini yangilash
                        c.execute("UPDATE battle_pairs SET winner=? WHERE id=?", (winner, pair_id))
                        conn.commit()

                        if winner and winner != 0:
                            c.execute("UPDATE users SET balls = balls + 100, wins = wins + 1 WHERE user_id=?", (winner,))
                            conn.commit()

                    try:
                        for uid in json.loads(players_json):
                            await bot.send_message(uid, f"🎮 1vs1 battle (ID: {battle_id}) tugadi! Natijalar hisoblandi.")
                    except:
                        print("Battle end notification failed.")

                continue

            # Battle’ni boshlash qismi (oldingi kod)
            if status == 'pending' and now >= battle_time:
                players = json.loads(players_json)
                random.shuffle(players)
                pairs = []
                while len(players) >= 2:
                    p1 = players.pop()
                    p2 = players.pop()
                    pairs.append((p1, p2))
                if players:
                    pairs.append((players[0], "bot"))

                # DBga saqlash
                for p1, p2 in pairs:
                    c.execute("""
                        INSERT INTO battle_pairs(battle_id, player1, player2)
                        VALUES (?, ?, ?)
                    """, (battle_id, p1, p2))

                c.execute("UPDATE battle_1vs1 SET status='started' WHERE id=?", (battle_id,))
                conn.commit()
                await notify_pairs(bot, battle_id)

        conn.close()
        await asyncio.sleep(60)

async def notify_pairs(bot: Bot, battle_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT id, player1, player2, votes1, votes2 FROM battle_pairs WHERE battle_id=?", (battle_id,))
    pairs = c.fetchall()

    for pair_id, p1, p2, votes1, votes2 in pairs:
        name1 = get_name(p1)
        name2 = "Bot" if p2 == "bot" else get_name(p2)

        kb = InlineKeyboardBuilder()
        kb.button(text=f"{name1} 🔥", callback_data=f"vote:{battle_id}:{pair_id}:{p1}")

        if p2 != "bot":
            kb.button(text=f"{name2} 🔥", callback_data=f"vote:{battle_id}:{pair_id}:{p2}")

        kb.adjust(2) 


        text = f"""{battle_id} - Battle juftligi:
<b>{name1}</b> 🆚 <b>{name2}</b>

{votes1} ta ovoz | {votes2} ta ovoz
        """

        for uid in [p1, p2]:
            if uid != "bot":
                try:
                    await bot.send_message(uid, text, reply_markup=kb.as_markup())
                except:
                    print(f"Notification to {uid} failed.")

    conn.close()

@router.callback_query(F.data.startswith("vote:"))
async def vote_menu(call: CallbackQuery, bot: Bot):
    _, battle_id, pair_id, target_player = call.data.split(":")
    kb = InlineKeyboardBuilder()

    kb.button(text="1 ta ovoz (bepul)", callback_data=f"vote_do:{battle_id}:{pair_id}:{target_player}:1")

    packages = [
        (10, 10),
        (50, 35),
        (100, 70),
        (500, 450),
        (1000, 900),
        (5000, 4200),
        (10000, 7500),
    ]

    for amount, cost in packages:
        kb.button(text=f"{amount}X — {cost} almaz", 
                  callback_data=f"vote_do:{battle_id}:{pair_id}:{target_player}:{amount}")

    kb.adjust(1)
    from database.battle_models import get_name_battle
    await call.message.edit_text(f"{get_name_battle(int(target_player))} uchun nechta ovoz berasiz?", reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("vote_do:"))
async def vote_do(call: CallbackQuery, bot: Bot):
    _, battle_id, pair_id, target_player, amount = call.data.split(":")
    amount = int(amount)
    user_id = call.from_user.id

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        SELECT 1 FROM votes 
        WHERE battle_id=? AND pair_id=? AND voter_id=?
    """, (battle_id, pair_id, user_id))
    already_voted = c.fetchone()

    if already_voted:
        await call.message.edit_text("Siz bu juftlikka allaqachon ovoz berdingiz! ❌", show_alert=True)
        conn.close()
        return

    cost = get_cost(amount)
    balance = get_balance(user_id)
    if balance < cost:
        await call.message.edit_text(f"Sizda yetarli almaz yo'q! ❌\n\n Balansingiz: {balance}", show_alert=True)
        conn.close()
        return


    update_balance(user_id, balance - cost)
    save_vote(battle_id, pair_id, user_id, amount, int(target_player)) 

    c.execute("""
        INSERT INTO votes(battle_id, pair_id, voter_id) 
        VALUES (?, ?, ?)
    """, (battle_id, pair_id, user_id))
    conn.commit()
    conn.close()

    await call.message.edit_text("Ovoz berildi! 🔥", show_alert=True)


@router.callback_query(F.data == "asosiy_battle")
async def show_battle_menu(call: CallbackQuery):
    await call.answer()  # callback alert ko‘rsatmasdan ishlaydi

    kb = InlineKeyboardBuilder()
    kb.button(text="🎮 Mening Battles", callback_data="my_battles")
    kb.button(text="🔍 Battle Qidiruv", callback_data="battle_search")
    kb.button(text="⬅️ Ortga", callback_data="start")
    kb.adjust(1)  # har qatorda 1 ta button

    from aiogram.exceptions import TelegramBadRequest
    try:
        await call.message.edit_text(
            "1vs1 Battle menyusiga xush kelibsiz! Tanlang:",
            reply_markup=kb.as_markup()
        )
    except TelegramBadRequest:
        pass 


# FSM state
class BattleSearchStates(StatesGroup):
    waiting_for_id = State()

# Battle search callback
@router.callback_query(F.data == "battle_search")
async def battle_search_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Iltimos, qidiriladigan Battle ID ni kiriting:")
    await state.set_state(BattleSearchStates.waiting_for_id)
    await call.answer()

@router.callback_query(F.data == "my_battles")
async def battle_search_start(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Foydalanuvchi qatnashgan juftliklarni olish
    c.execute("""
        SELECT id, battle_id, player1, player2, votes1, votes2, winner 
        FROM battle_pairs 
        WHERE player1=? OR player2=?
    """, (user_id, user_id))
    
    battles = c.fetchall()
    conn.close()

    if not battles:
        await call.message.answer("Sizda hech qanday Battle yo'q!")
        await call.answer()
        return
    
    text = "Sizning Battles:\n\n"
    for pair_id, battle_id, p1, p2, votes1, votes2, winner in battles:
        opponent = p2 if p1 == user_id else p1
        user_votes = votes1 if p1 == user_id else votes2
        opp_votes = votes2 if p1 == user_id else votes1
        
        if winner == user_id:
            result = "🏆 Yutdingiz"
        elif winner == 0 or winner is None:
            result = "Nomalum natija"
        else:
            result = "❌ Yutqazdingiz"

        text += f"Battle ID: {battle_id} | Juftlik ID: {pair_id}\n"
        text += f"{get_name(user_id)} ({user_votes}) 🆚 {get_name(opponent)} ({opp_votes}) → {result}\n\n"

    await call.message.answer(text)
    await call.answer()


# Foydalanuvchi ID kiritganda
@router.message(BattleSearchStates.waiting_for_id)
async def battle_search_id(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting!")
        return

    pair_id = int(text)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT battle_id, player1, player2, votes1 ,votes2 FROM battle_pairs WHERE id=?", (pair_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        await message.answer("Bunday Battle topilmadi!")
        await state.clear()
        return

    battle_id, p1, p2, votes1, votes2 = row
    user_id = message.from_user.id

    kb = InlineKeyboardBuilder()
    kb.button(text=f"{get_name(p1)} 🔥", callback_data=f"vote:{battle_id}:{pair_id}:{p1}")

    if p2 != "bot":
        kb.button(text=f"{get_name(p2)} 🔥", callback_data=f"vote:{battle_id}:{pair_id}:{p2}")

    kb.adjust(2) 


    await message.answer(
        f"Battle topildi:\n\n {get_name(p1)}({votes1}) 🆚 {get_name(p2)}({votes2})\n\nKimga ovoz berasiz?",
        reply_markup=kb.as_markup()
    )
    await state.clear()
