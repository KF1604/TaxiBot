from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums.parse_mode import ParseMode
from app.database import async_session
from app.keyboards.driver_inline import (
    registered_driver_menu_kb,
    unregistered_driver_kb,
)
from app.database.queries import get_driver_by_id

driver_router = Router(name="driver_menu")

@driver_router.callback_query(F.data == "driver_menu")
async def show_driver_menu(cb: CallbackQuery):
    user_id = cb.from_user.id

    async with async_session() as session:
        driver = await get_driver_by_id(session, user_id)

    if driver:
        text = (
            "🚖 <b>Haydovchi bo‘limi</b>\n\n"
            "Kerakli bo‘limni tanlang:"
        )
        await cb.message.edit_text(
            text=text,
            reply_markup=registered_driver_menu_kb(),
            parse_mode=ParseMode.HTML
        )
    else:
        text = (
            "<b>🚗 Haydovchi sifatida ishlashni xohlaysizmi?</b>\n\n"
            "Bizning <b>yopiq haydovchilar guruhimizga</b> qo‘shilib:\n"
            "✅ <b>Kuniga 200+ real buyurtma</b> oling\n"
            "💬 <b>Faqat haqiqiy mijozlar — ortiqcha spam va reklamalarsiz</b>\n"
            "💸 <b>Daromadni oshiring, yo‘lovchilar bilan to‘g‘ridan-to‘g‘ri bog‘laning</b>\n\n"
            "Ro'yxatdan o'tish uchun quyidagi '📝 Ro'yxatdan o'tish' tugmasini bosing 👇"
        )

        await cb.message.edit_text(
            text=text,
            reply_markup=unregistered_driver_kb(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )