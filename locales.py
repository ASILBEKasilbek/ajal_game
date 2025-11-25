# locales.py
import json

LOCALES = {
    "uz": {
        "welcome": """🎮  Ajal O'yini — Asosiy menyu

Quyidagi bo'limlardan birini tanlab, o'yinni davom ettiring.
Har bir bo'lim sizning kuchingiz, darajangiz va imkoniyatlaringizni oshiradi.\n""",
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
        "screenshot_sent": "Screenshot adminlarga yuborildi. Tasdiqlashni kuting",
        "clan_menu_title": "Klanlar bo‘limi",
        "clan_my_clan": "Mening klanim",
        "clan_all_clans": "Barcha klanlar",
        "clan_create": "Klan yaratish (100 olmos)",
        "clan_no_clans": "Hozircha klan yo‘q.",
        "clan_create_first": "Birinchilardan bo‘lib yarating!",
        "clan_info_title": """Klan: {name}""",
        "clan_level": "Daraja",
        "clan_members": "A'zolar",
        "clan_leader": "Lider",
        "clan_join_type": "Qo‘shilish",
        "clan_description": "Ta'rif",
        "clan_group": "Guruh",
        "clan_channel": "Kanal",
        "clan_join_request": "So‘rov yuborish",
        "clan_join_open": "Qo‘shilish",
        "clan_management": "Boshqaruv",
        "clan_members_list": "A'zolar ro‘yxati",
        "clan_requests": "So‘rovlar",
        "clan_join_type_settings": "Qo‘shilish turi",
        "clan_transfer_leadership": "Liderlik o‘tkazish",
        "clan_kick": "Chiqar",
        "clan_promote": "Zam lider",
        "clan_leave": "Chiqish",
        "clan_create_name": """✨ Yangi klan yaratish jarayoni boshlandi!

🔹 1-qadam: Klan nomini yozing (3-20 belgi)
Masalan: Qora Qalpoq, Ajdarlar""",
        "clan_create_desc": """ 
🔹 2-qadam: Klan haqida qisqacha ta'rif yozing (maks 200 belgi)
Masalan: Biz eng kuchli jamoamiz!""",
        "clan_create_group": """✅ Ta'rif qabul qilindi!

🔹 3-qadam: Klan guruhini yuboring
Masalan: @MyClanChat yoki https://t.me/MyClanChat""",
        "clan_create_channel": """✅ Guruh qabul qilindi!

🔹 4-qadam: Klan kanalini yuboring
Masalan: @MyClanNews yoki https://t.me/MyClanNews""",
        "clan_created": "Klan yaratildi!",
        "clan_name_taken": "Bu nom band!",
        "clan_join_success": "Muvaffaqiyatli qo‘shildingiz!",
        "clan_request_sent": "So‘rovingiz yuborildi!",
        "clan_full": "Klan to‘lgan!",
        "clan_already_member": "Siz allaqachon klanga a'zosiz!",
        "clan_no_permission": "Ruxsat yo‘q!",
        "clan_only_leader": "Faqat lider!",
        "clan_request_approve": "Qabul",
        "clan_request_reject": "Rad",
        "clan_request_approved": "Qabul qilindi!",
        "clan_request_rejected": "Rad etildi!",
        "clan_kicked": "Chiqarildi!",
        "clan_promoted": "Zam lider qilindi!",
        "clan_transferred": "Liderlik o‘tkazildi!",
        "clan_leader_cant_leave": "Lider chiqa olmaydi!",
        "clan_left": "Chiqdingiz.",
        "clan_join_open_type": "Ochiq",
        "clan_join_request_type": "So‘rov orqali",
        "clan_set_join_open": "Ochiq",
        "clan_set_join_request": "So‘rov orqali",
        "clan_no_requests": "So‘rov yo‘q.",
        "clan_no_members": "Hozircha a'zolar yo‘q.",
        "clan_transfer_prompt": "Liderlikni kimga o‘tkazmoqchisiz?",
        "clan_channel_btn": "Kanal",
        "clan_group_btn": "Guruh",
        "clan_menu_btn": "Menyu",
        "back": "Ortga",
        "main_menu": "Asosiy menyuga"
        
},
    "ru": {
        "welcome": """🎮  Ajal O'yini — Asosiy menyu

Quyidagi bo'limlardan birini tanlab, o'yinni davom ettiring.
Har bir bo'lim sizning kuchingiz, darajangiz va imkoniyatlaringizni oshiradi.\n""",
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
        "profile": "👤 <b>Профиль</b>\n\n👤 {name}\n🆔 {id}\n🏆 Уровень: {level}\n⭐ Ранг: {rank}\n💎 Алмазы: {olmos}",
        "clan_menu_title": "Раздел кланов",
        "clan_my_clan": "Мой клан",
        "clan_all_clans": "Все кланы",
        "clan_create": "Создать клан (1 алмаз)",
        "clan_no_clans": "Пока нет кланов.",
        "clan_create_first": "Будьте первым!",
        "clan_info_title": "Клан: {name}",
        "clan_level": "Уровень",
        "clan_members": "Участники",
        "clan_leader": "Лидер",
        "clan_join_type": "Присоединение",
        "clan_description": "Описание",
        "clan_group": "Группа",
        "clan_channel": "Канал",
        "clan_join_request": "Отправить заявку",
        "clan_join_open": "Присоединиться",
        "clan_management": "Управление",
        "clan_members_list": "Список участников",
        "clan_requests": "Заявки",
        "clan_join_type_settings": "Тип присоединения",
        "clan_transfer_leadership": "Передать лидерство",
        "clan_kick": "Исключить",
        "clan_promote": "Зам. лидера",
        "clan_leave": "Выйти",
        "clan_create_name": "Введите название клана (3-20):",
        "clan_create_desc": "Введите описание (макс. 200):",
        "clan_create_group": "Отправьте ссылку на группу (@ или t.me):",
        "clan_create_channel": "Отправьте ссылку на канал:",
        "clan_created": "Клан создан!",
        "clan_name_taken": "Это название занято!",
        "clan_join_success": "Вы успешно присоединились!",
        "clan_request_sent": "Заявка отправлена!",
        "clan_full": "Клан полон!",
        "clan_already_member": "Вы уже в клане!",
        "clan_no_permission": "Нет доступа!",
        "clan_only_leader": "Только лидер!",
        "clan_request_approve": "Принять",
        "clan_request_reject": "Отклонить",
        "clan_request_approved": "Принято!",
        "clan_request_rejected": "Отклонено!",
        "clan_kicked": "Исключён!",
        "clan_promoted": "Назначен зам. лидером!",
        "clan_transferred": "Лидерство передано!",
        "clan_leader_cant_leave": "Лидер не может выйти!",
        "clan_left": "Вы вышли.",
        "clan_join_open_type": "Открытый",
        "clan_join_request_type": "По заявке",
        "clan_set_join_open": "Открытый",
        "clan_set_join_request": "По заявке",
        "clan_no_requests": "Заявок нет.",
        "clan_no_members": "Участников пока нет.",
        "clan_transfer_prompt": "Кому передать лидерство?",
        "clan_channel_btn": "Канал",
        "clan_group_btn": "Группа",
        "clan_menu_btn": "Меню",
        "back": "Назад",
        "main_menu": "В главное меню"
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
        "profile": "👤 <b>Profile</b>\n\n👤 {name}\n🆔 {id}\n🏆 Level: {level}\n⭐ Rank: {rank}\n💎 Diamonds: {olmos}",
        "clan_menu_title": "Clans Section",
        "clan_my_clan": "My Clan",
        "clan_all_clans": "All Clans",
        "clan_create": "Create Clan (1 diamond)",
        "clan_no_clans": "No clans yet.",
        "clan_create_first": "Be the first to create!",
        "clan_info_title": "Clan: {name}",
        "clan_level": "Level",
        "clan_members": "Members",
        "clan_leader": "Leader",
        "clan_join_type": "Join Type",
        "clan_description": "Description",
        "clan_group": "Group",
        "clan_channel": "Channel",
        "clan_join_request": "Send Request",
        "clan_join_open": "Join",
        "clan_management": "Management",
        "clan_members_list": "Member List",
        "clan_requests": "Requests",
        "clan_join_type_settings": "Join Type",
        "clan_transfer_leadership": "Transfer Leadership",
        "clan_kick": "Kick",
        "clan_promote": "Promote to Co-Leader",
        "clan_leave": "Leave",
        "clan_create_name": "Enter clan name (3-20):",
        "clan_create_desc": "Enter description (max 200):",
        "clan_create_group": "Send group link (@ or t.me):",
        "clan_create_channel": "Send channel link:",
        "clan_created": "Clan created!",
        "clan_name_taken": "This name is taken!",
        "clan_join_success": "Successfully joined!",
        "clan_request_sent": "Request sent!",
        "clan_full": "Clan is full!",
        "clan_already_member": "You're already in a clan!",
        "clan_no_permission": "No permission!",
        "clan_only_leader": "Only leader!",
        "clan_request_approve": "Approve",
        "clan_request_reject": "Reject",
        "clan_request_approved": "Approved!",
        "clan_request_rejected": "Rejected!",
        "clan_kicked": "Kicked!",
        "clan_promoted": "Promoted to co-leader!",
        "clan_transferred": "Leadership transferred!",
        "clan_leader_cant_leave": "Leader cannot leave!",
        "clan_left": "You left.",
        "clan_join_open_type": "Open",
        "clan_join_request_type": "By Request",
        "clan_set_join_open": "Open",
        "clan_set_join_request": "By Request",
        "clan_no_requests": "No requests.",
        "clan_no_members": "No members yet.",
        "clan_transfer_prompt": "Who to transfer leadership to?",
        "clan_channel_btn": "Channel",
        "clan_group_btn": "Group",
        "clan_menu_btn": "Menu",
        "back": "Back",
        "main_menu": "Main Menu"
    }
}

def t(lang, key, **kwargs):
    text = LOCALES.get(lang, LOCALES["uz"]).get(key, key)
    return text.format(**kwargs)