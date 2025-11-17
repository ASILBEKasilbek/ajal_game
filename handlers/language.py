from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.user_models import get_user, save_user_language_only
from locales import t
from keyboards.asosiy import lang_keyboard, main_menu
import asyncio 

router = Router()

@router.callback_query(F.data.startswith("lang_"))
async def change_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    save_user_language_only(user_id, lang)

    await callback.message.answer(t(lang, "language_changed"))
    await asyncio.sleep(1)  
    await callback.message.delete()
    await callback.message.answer(
        "Botni guruhga qo'shish uchun quyidagi tugmani bosing:",
        reply_markup=main_menu()
    )



@router.callback_query(F.data == "lang")
async def show_lang(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    lang = user.get("language", "uz")
    await callback.message.edit_text(t(lang, "choose_lang"), reply_markup=lang_keyboard())