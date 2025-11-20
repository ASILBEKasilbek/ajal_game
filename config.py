from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID")
MIN_PLAYERS = 4

DB_FILE = "ajal_bot.db"

JOIN_TIME = 60
CARD_CHOICE_TIME = 25
NIGHT_DELAY = 60
NOMINATE_TIME = 30
GROUP_VOTE_TIME = 30
MADARA_POISON_ROUNDS = 2
BOT_NAME = "Asilbek_yangi_test_bot"
CLANS = ["Fire", "Water", "Wind", "Earth"]

ROUND_DURATION = 300
XP_PER_KILL = 25

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
CARD_CHOICE_TIME = 25

JOIN_TIME = 180 