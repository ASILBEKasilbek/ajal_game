from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID")
MIN_PLAYERS = 4

DB_FILE = "ajal_bot.db"

BOT_NAME = "Asilbek_yangi_test_bot"
CLANS = ["Fire", "Water", "Wind", "Earth"]

ROUND_DURATION = 300
XP_PER_KILL = 25

GAME_RESULT_HP = {"win": 10, "lose": 3, "draw": 5}
PACKAGES = {
    "10": {"amount": 10, "price": 10000},
    "20": {"amount": 20, "price": 18000},
    "40": {"amount": 40, "price": 35000},
    "100": {"amount": 100, "price": 85000},
}


CARDS = [
    "♣️ Chillik",
    "♥️ Toppon",
    "♦️ G'ishtin",
    "♠️ Qirol Qarg'a"
]

CARD_CHOICE_TIME = 60
JOIN_TIME = 180 

NIGHT_DELAY = 40
NOMINATE_TIME = 40
GROUP_VOTE_TIME = 120
MADARA_POISON_ROUNDS = 1


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

RANKS = [
    {"name": "ACE", "emoji": "🔥", "min_hp": 0, "next_hp": 2500},
    {"name": "ACE MASTER", "emoji": "⚡️", "min_hp": 2500, "next_hp": 6000},
    {"name": "ACE DOMINATOR", "emoji": "💀", "min_hp": 6000, "next_hp": 10000},
    {"name": "ZAVA", "emoji": "👑", "min_hp": 10000, "next_hp": None},
]

LEVEL_PROGRESSION = [
    (0, 0),  # lvl 1
    (20, 20), (40, 60), (60, 120), (90, 210), (130, 340), (180, 520), (250, 770), (350, 1120), (500, 1620),  # 2-10
]
STREAK_WIN_BONUS = 25 
STREAK_LOSE_PENALTY = -20  # 3 ketma-ket lose