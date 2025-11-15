# locales.py
import json

LOCALES = {
    "uz": {
        "welcome": "Botni guruhga qo'shish uchun quyidagi tugmani bosing!\n",
        "choose_lang": "Tilni tanlang:",
        "game_start": "O'yin boshlanmoqda...",
        "language_changed": "✅ Til o'zgartirildi!",
        "profile": "👤 <b>Profil</b>\n\n👤 {name}\n🆔 {id}\n🏆 Level: {level}\n⭐ Rank: {rank}\n💎 Olmos: {olmos}",
        "shop_diamonds_intro": (
                "💎 OLMOSLAR\n\n"
                "🔹 Olmoslar - bu o'yin ichidagi premium valyuta\n"
                "🔹 Ulardan maxsus imkoniyatlar va afzalliklar uchun foydalanishingiz mumkin\n\n"
                "💰 Paketlar:\n"
                "• 10 💎 = 10,000 so'm\n"
                "• 20 💎 = 18,000 so'm\n"
                "• 40 💎 = 35,000 so'm\n"
                "• 100 💎 = 85,000 so'm\n\n"
                "📝 Qanday sotib olish mumkin:\n"
                "1️⃣ Paketni tanlang\n"
                "2️⃣ Karta raqamiga pul o'tkazing\n"
                "3️⃣ To'lov chekini screenshot qiling\n"
                "4️⃣ Screenshot yuborib tasdiqlang\n"
                "5️⃣ Admin tasdigidan keyin olmoslar hisobingizga tushadi"
        ),
        "screenshot_sent": "Screenshot adminlarga yuborildi. Tasdiqlashni kuting"
        
},
    "ru": {
        "welcome": "Bот для добавления в группу, нажмите кнопку ниже!\n",
        "choose_lang": "Выберите язык:",
        "game_start": "Игра начинается...",
        "language_changed": "✅ Язык изменен!",
        "shop_diamonds_intro": (
            "💎 АЛМАЗЫ\n\n"
            "🔹 Алмазы - это внутриигровая премиум валюта\n"
            "🔹 Их можно использовать для специальных возможностей и преимуществ\n\n"
            "💰 Пакеты:\n"
            "• 10 💎 = 10,000 сум\n"
            "• 20 💎 = 18,000 сум\n"
            "• 40 💎 = 35,000 сум\n"
            "• 100 💎 = 85,000 сум\n\n"
            "📝 Как купить:\n"
            "1️⃣ Выберите пакет\n"
            "2️⃣ Переведите деньги на карту\n"
            "3️⃣ Сделайте скриншот чека\n"
            "4️⃣ Отправьте скриншот для подтверждения\n"
            "5️⃣ После подтверждения админа алмазы поступят на ваш счет\n"),
        "screenshot_sent": "Скриншот отправлен администраторам. Ожидайте подтверждения",
        "profile": "👤 <b>Профиль</b>\n\n👤 {name}\n🆔 {id}\n🏆 Уровень: {level}\n⭐ Ранг: {rank}\n💎 Алмазы: {olmos}"
    },
    "eng": {
        "welcome": "To add the bot to a group, press the button below!\n",
        "choose_lang": "Choose language:",
        "game_start": "Game starting...",
        "language_changed": "✅ Language changed!",
        "shop_diamonds_intro": (
            "💎 DIAMONDS\n\n"
            "🔹 Diamonds - premium in-game currency\n"
            "🔹 Use them for special abilities and advantages\n\n"
            "💰 Packages:\n"
            "• 10 💎 = 10,000 som\n"
            "• 20 💎 = 18,000 som\n"
            "• 40 💎 = 35,000 som\n"
            "• 100 💎 = 85,000 som\n"
            "\n📝 How to buy:\n"
            "1️⃣ Choose a package\n"
            "2️⃣ Transfer money to the card\n"
            "3️⃣ Screenshot the receipt\n"
            "4️⃣ Send screenshot for confirmation\n"
            "5️⃣ After admin approval, diamonds will be added to your account"
        ),
        "screenshot_sent": "Screenshot sent to admins. Please wait for confirmation",
        "profile": "👤 <b>Profile</b>\n\n👤 {name}\n🆔 {id}\n🏆 Level: {level}\n⭐ Rank: {rank}\n💎 Diamonds: {olmos}"
    }
}

def t(lang, key, **kwargs):
    text = LOCALES.get(lang, LOCALES["uz"]).get(key, key)
    return text.format(**kwargs)