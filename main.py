# main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.language import router as lang_router
from handlers.profile import router as profile_router
from aiogram import types
from handlers.shop import router as shop_router
from handlers.game import router as game_router
from handlers.admin import router as admin_router
from handlers.user import router as user_router
from handlers.clan import router as clan_router
from handlers.battle_1vs1 import router as battle_1vs1_router
from handlers.battle_1vs1 import battle_scheduler 
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()
async def set_default_commands(bot: Bot):
    await bot.set_my_commands(
        [
            types.BotCommand(command="start", description="⚪️Botni ishga tushirish | 🟡Botni yangilash"),
            types.BotCommand(command="help", description="📚Qo'llanma | Botdan qanday foydalanish"),
            types.BotCommand(command="rules", description="📜Qoidalar"),
            types.BotCommand(command="shop", description="🛒Do'kon"),
            types.BotCommand(command="game", description="🃏O'yinga ro'yxatga olish"),
        ]
    )

# Routerlarni qo'shamiz

dp.include_router(clan_router)
dp.include_router(admin_router)
dp.include_router(game_router)
dp.include_router(shop_router)
dp.include_router(lang_router)
dp.include_router(profile_router)
dp.include_router(user_router)
dp.include_router(start_router)
dp.include_router(battle_1vs1_router)


async def main():
    print("Bot ishga tushdi...")
    asyncio.create_task(battle_scheduler(bot))
    await set_default_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
