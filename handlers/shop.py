from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.user_models import get_user
from database.db import add_olmos
from locales import t
from config import PACKAGES,DB_FILE


router = Router()


user_selected_package = {}


@router.callback_query(F.data.startswith("shop:diamonds"))
async def show_diamonds_shop(callback: CallbackQuery):
    lang = get_user(callback.from_user.id).get("language", "uz")

    text = t(lang, "shop_diamonds_intro")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{info['amount']}💎 ({info['price']} so'm)",
            callback_data=f"buy_olmos:{key}:{callback.from_user.id}"
        )]
        for key, info in PACKAGES.items()
    ] + [[InlineKeyboardButton(text="🔙 Ortga", callback_data="start")]])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# 💳 To'lov ma'lumotini ko‘rsatish
@router.callback_query(F.data.startswith("buy_olmos:"))
async def process_buy_olmos(callback: CallbackQuery):
    _, package, user_id = callback.data.split(":")
    user_id = int(user_id)
    info = PACKAGES[package]
    user_selected_package[user_id] = info

    lang = get_user(user_id).get("language", "uz")
    olmos = info['amount']
    narx_price = info['price']

    if lang == "uz":
        text = f"""
💳 To'lov ma'lumotlari

💎 Paket: {olmos} Olmos
💰 Narx: {narx_price} so'm

📌 Karta raqami:
9860 6067 4288 9219 
(Ism: Abdullayev Umarbek)

📝 Ko'rsatma:
1. Yuqoridagi karta raqamiga {narx_price} so'm o'tkazing
2. To'lov chekini screenshot qiling
3. Screenshot'ni botga yuboring

⏰ 10 daqiqa ichida screenshot yuboring!
📸 Endi to'lov chekingizni screenshot qilib yuboring:
"""
    elif lang == "ru":
        text = f"""
💳 Платежная информация

💎 Пакет: {olmos} Алмазов
💰 Цена: {narx_price} сум

📌 Номер карты:
9860 6067 4288 9219
(Имя: Abdullayev Umarбек)

📝 Инструкция:
1. Переведите {narx_price} сум на указанную карту
2. Сделайте скриншот чека
3. Отправьте скриншот боту

⏰ Отправьте скриншот в течение 10 минут!

📸 Теперь отправьте скриншот вашего чека оплаты:
"""
    else:  # English
        text = f"""
💳 Payment Information

💎 Package: {olmos} Diamonds
💰 Price: {narx_price} som

📌 Card number:
9860 6067 4288 9219
(Name: Abdullayev Umarbek)

📝 Instructions:
1. Transfer {narx_price} som to the card above
2. Screenshot the receipt
3. Send the screenshot to the bot

⏰ Send the screenshot within 10 minutes!
📸 Now send a screenshot of your payment receipt:
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="shop:diamonds")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# 📸 Screenshot qabul qilish
@router.message(F.photo | F.document)
async def receive_payment_screenshot(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        return
    if message.from_user.id not in user_selected_package:
        return  

    info = user_selected_package.get(message.from_user.id)
    if not info:
        await message.answer("Avval paket tanlang.")
        return

    lang = user["language"]

    # Admin panelga yuborish
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_olmos:{message.from_user.id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"deny_olmos:{message.from_user.id}")
        ]
    ])

    caption = (
        f"🧾 To'lov screenshot\n"
        f"💎 Paket: {info['amount']}💎 ({info['price']} so'm)\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} (@{message.from_user.username or 'yo‘q'})\n"
        f"🆔 ID: `{message.from_user.id}`"
    )
    import sqlite3

    # DB faylingni ochamiz
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT kanal_id FROM tulov_kanallar ORDER BY id DESC LIMIT 1")
    result = c.fetchone()

    if result:
        ADMIN_GROUP_ID = result[0]
        print(ADMIN_GROUP_ID)
    else:
        ADMIN_GROUP_ID = -1002938796047 

    if message.photo:
        await message.bot.send_photo(
            chat_id=ADMIN_GROUP_ID,
            photo=message.photo[-1].file_id,
            caption=caption,
            reply_markup=keyboard
        )
    else:
        await message.bot.send_document(
            chat_id=ADMIN_GROUP_ID,
            document=message.document.file_id,
            caption=caption,
            reply_markup=keyboard
        )

    await message.answer(t(lang, "screenshot_sent"))


# ✅ Tasdiqlash
@router.callback_query(F.data.startswith("confirm_olmos:"))
async def confirm_olmos(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    info = user_selected_package.get(user_id)

    if not info:
        await callback.answer("Xatolik: foydalanuvchi paketi topilmadi.", show_alert=True)
        return

    add_olmos(user_id, info['amount'])

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"✅ Tasdiqlandi: {user_id}")

    try:
        await callback.bot.send_message(
            user_id,
            f"✅ To‘lovingiz tasdiqlandi! {info['amount']} olmos hisobingizga tushdi 💎"
        )
    except:
        pass

    await callback.answer()


# ❌ Rad etish
@router.callback_query(F.data.startswith("deny_olmos:"))
async def deny_olmos(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"❌ Rad etildi: {user_id}")

    try:
        await callback.bot.send_message(
            user_id,
            "❌ To‘lovingiz rad etildi. Iltimos, qayta urinib ko‘ring."
        )
    except:
        pass

    await callback.answer()
