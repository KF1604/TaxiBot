import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from app.keyboards.depart_inline import to_main_menu_inline, contact_client_button
from app.keyboards.depart_reply import comment_keyboard
from app.states.depart_states import OrderState
from app.database.queries import save_order, get_user_phone
from app.utils import normalize_phone
from app.utils.rate_limiter import is_allowed_to_order

depart_router = Router(name="depart")

GROUP_ID = int(os.getenv("TARGET_CHAT_IDS"))

# --- 1. Buyurtma boshlash ---
@depart_router.callback_query(F.data == "order_depart")
async def start_depart_callback(call: CallbackQuery, state: FSMContext):
    allowed, next_time = await is_allowed_to_order(user_id=call.from_user.id)
    if not allowed:
        await call.answer(
            f"⏳ Siz yaqinda buyurtma bergansiz\n\n"
            f"Har 5 daqiqada faqat bitta buyurtma berish mumkin\n\n"
            f"{next_time} dan keyin qayta urinib ko‘ring\n\n"
            f"Tushunganingiz uchun rahmat!",
            show_alert=True
        )
        return
    await state.clear()
    await state.set_state(OrderState.choose_comment)
    await call.message.answer(
        "<b>🚖 Jo'nab ketish bo'limi</b>\n\n"
        "Haydovchiga izoh qoldiring, bu sizga mos haydovchi topilishiga yordam beradi\n\n"
        "<b>Misollar:</b>\n"
        "• <code>Oldi o‘rindiqda o‘tiraman</code>\n"
        "• <code>Ayolman, ayol yo‘lovchi bo‘lishi kerak</code>\n"
        "• <code>2 kishi, 3 ta sumka</code>\n"
        "• <code>1 kishi, nogironlik aravachasi bor</code>\n"
        "• <code>1 kishi, 1 ta velosiped, 'rack' kerak</code>\n"
        "• <code>Ona va 2 bola, 2 ta sumka</code>\n\n"
        "Iltimos, faqat kerakli ma’lumotlarni yozing 👇",
        reply_markup=comment_keyboard(),
        parse_mode="HTML"
    )
    await call.message.delete()

# --- 2. Izoh va tasdiqlash ---
@depart_router.message(OrderState.choose_comment, F.text)
async def input_comment(message: Message, state: FSMContext):
    comment = None if message.text == "⏭️ O‘tkazib yuborish" else message.text.strip()

    # Mijoz telefon raqamini olish
    phone = await get_user_phone(message.from_user.id)
    phone_text = normalize_phone(phone) if phone else "kiritilmagan"

    # Buyurtmani bazaga saqlash
    await save_order(
        user_fullname=message.from_user.full_name,
        user_id=message.from_user.id,
        order_type="jo'nab ketish",
        phone=phone_text,
        comment_to_driver=comment,
    )

    # Guruhga yuborish
    group_text = (
        "<b>💥 Yangi buyurtma!</b>\n\n"
        "<b>Buyurtma turi:</b> 🚖 Jo'nab ketish\n"
        f"<b>👤 Mijoz:</b> {message.from_user.full_name}\n"
        f"<b>🆔 ID:</b> <code>{message.from_user.id}</code>\n"
        f"<b>📞 Telefon raqami:</b> {phone_text}\n\n"
        f"<b>💬 Izoh:</b> <i>{comment or 'yo‘q'}</i>"
    )
    reply_markup = contact_client_button(
        user_id=message.from_user.id,
        username=message.from_user.username,
    )

    await message.bot.send_message(
        GROUP_ID,
        text=group_text,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

    await message.answer("✅ Ma'lumotlar qabul qilindi!", reply_markup=ReplyKeyboardRemove())
    # Foydalanuvchiga xabar
    await message.answer(
        "<b>✅ Buyurtmangiz qabul qilindi!</b>\n\n"
        "Haydovchilarimiz tez orada siz bilan bog‘lanishadi!\n\n"
        "Bizning xizmatimizdan foydalanganingiz uchun tashakkur!",
        reply_markup=to_main_menu_inline()
    )

    await state.clear()
