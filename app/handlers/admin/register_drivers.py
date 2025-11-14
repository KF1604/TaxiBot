import asyncio
import os
from datetime import datetime, timedelta
from urllib.parse import quote_plus, unquote_plus

from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, ContentType, KeyboardButton,
    ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext

from app.database.session import async_session
from app.database.models import Driver, User
from app.database.queries import get_admin_users, get_driver_by_id
from app.handlers.admin.forwarder import unrestrict_driver
from app.keyboards.driver_inline import retry_register_kb
from app.lib.time import now_tashkent
from app.states import AdminManageState
from app.states.driver_states import DriverRegState
from dispatcher import bot

router = Router(name="register_drivers")

GROUP_ID = int(os.getenv("SOURCE_CHAT_IDS"))

# ─── 1️⃣ Ro‘yxatni boshlash ─────────────────────────────
@router.callback_query(F.data == "register_driver")
async def start_driver_registration(cb: CallbackQuery, state: FSMContext):
    user_id = cb.from_user.id

    try:
        await cb.message.delete()
    except Exception:
        pass

    async with async_session() as session:
        user = await session.get(User, user_id)

    if not user or not user.phone_number:
        return await cb.message.answer(
            "❌ Telefon raqamingiz tizimda topilmadi. Iltimos, /start buyrug‘ini bosib qayta kirib ko‘ring."
        )

    await state.update_data(phone_number=user.phone_number)

    # To‘lov haqida xabar
    text = (
        f"👋 Hurmatli <b>{cb.from_user.full_name}</b>!\n\n"
        "Siz hozir <b>haydovchilar ro‘yxatiga</b> qo‘shilmoqdasiz.\n"
        "Iltimos, quyidagi ma’lumotlarni diqqat bilan o‘qing va to‘lovni amalga oshiring 👇\n\n"
        "💼 <b>Guruh afzalliklari:</b>\n"
        "🚗 Har kuni 200+ real buyurtmalar\n"
        "💬 Faqat haqiqiy mijozlar — reklamasiz, spamsiz\n"
        "📈 Barqaror daromad va qulay tizim\n"
        "🔒 Faqat faol haydovchilar uchun yopiq guruh\n\n"
        "💰 <b>Obuna narxi:</b> 50.000(ellik ming) so‘m/oy\n"
        "• To‘lov qilinmagan holatda guruhdan foydalanish vaqtincha cheklanadi\n\n"
        "🏦 <b>To‘lovni amalga oshiring:</b>\n"
        "💳 <b>Karta:</b> 9860160602412274\n"
        "👤 <b>Karta egasi:</b> SHOHRUH MIRZAYEV\n\n"
        "🧾 To‘lovni amalga oshirgach, chekni shu yerga yuboring\n\n"
        "✅ Tekshirilgach, sizga darhol haydovchilar yopiq guruhi havolasi taqdim etiladi!\n\n"
    )

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Faqat to‘lov chekini yuboring..."
    )

    await state.set_state(DriverRegState.waiting_for_check)

    sent_msg = await cb.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await state.update_data(info_message_id=sent_msg.message_id)

    await cb.answer()


# ─── 2️⃣ Chekni yuborish ────────────────────────────────
@router.message(DriverRegState.waiting_for_check, F.content_type.in_({"photo", "document"}))
async def handle_driver_check(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != DriverRegState.waiting_for_check:
        return

    data = await state.get_data()
    phone_number = data.get("phone_number")
    info_message_id = data.get("info_message_id")

    if not phone_number:
        return await msg.answer("❌ Telefon raqamingiz topilmadi. Iltimos, qaytadan boshlang.")

    allowed_extensions = (".pdf", ".png", ".jpg", ".jpeg")

    if msg.content_type == ContentType.DOCUMENT:
        doc = msg.document
        if not doc.file_name.lower().endswith(allowed_extensions):
            return await msg.answer("❌ Faqat PDF, PNG yoki JPG fayl yuboring")
        file_ref = doc.file_id
        is_document = True
    elif msg.content_type == ContentType.PHOTO:
        file_ref = msg.photo[-1].file_id
        is_document = False
    else:
        return await msg.answer("❌ Faqat rasm (PNG/JPG) yoki PDF fayl yuboring")

    username = f"@{msg.from_user.username}" if msg.from_user.username else "—"
    caption = (
        f"🧾 <b>Yangi to‘lov cheki</b>\n\n"
        f"👤 Ismi: <b>{msg.from_user.full_name}</b>\n"
        f"🔗 Username: {username}\n"
        f"☎️ Telefon: {phone_number}\n"
        f"🆔 Telegram ID: <code>{msg.from_user.id}</code>\n"
        f"⏰ Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Chekni tekshirib, tasdiqlang yoki rad eting ⬇️"
    )

    encoded_phone = quote_plus(phone_number)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Tasdiqlash",
            callback_data=f"approve_driver:{msg.from_user.id}:{encoded_phone}"
        ),
        InlineKeyboardButton(
            text="❌ Rad etish",
            callback_data=f"reject_driver:{msg.from_user.id}"
        )
    ]])

    admins = await get_admin_users()
    for admin in admins:
        try:
            if is_document:
                await msg.bot.send_document(admin.id, file_ref, caption=caption, parse_mode="HTML", reply_markup=kb)
            else:
                await msg.bot.send_photo(admin.id, file_ref, caption=caption, parse_mode="HTML", reply_markup=kb)
        except Exception:
            continue

    if info_message_id:
        try:
            await msg.bot.delete_message(msg.chat.id, info_message_id)
        except Exception:
            pass

    await msg.answer(
        "✅ Chekingiz yuborildi. Admin tasdiqlashini kuting...\n\n"
        "Chekingiz tasdiqlangach sizga haydovchilar yopiq guruhi havolasi taqdim etiladi\n\n"
        "⚠️ <b>ESLATMA:</b> Havola taqdim etilgach guruhga darhol qo'shilib oling, aks holda havola 1 daqiqadan "
        "so'ng avtomatik o'chiriladi!"
    )
    await state.clear()


# ─── 4️⃣ Admin tasdiqlaydi — shu yerda haydovchi DB ga qo‘shiladi yoki yangilanadi ─────────
@router.callback_query(F.data.startswith("approve_driver:"))
async def approve_driver(cb: CallbackQuery):
    try:
        _, sid, encoded_phone = cb.data.split(":", 2)
        driver_id = int(sid)
        phone_number = unquote_plus(encoded_phone) if encoded_phone else None
    except Exception:
        await cb.answer("❌ Callback data noto‘g‘ri", show_alert=True)
        return

    GROUP_ID = -1002957473385
    admin_id = cb.from_user.id

    async with async_session() as session:
        driver = await get_driver_by_id(session, driver_id)

        # ❌ Agar allaqachon tasdiqlangan yoki rad etilgan bo‘lsa
        if driver and driver.added_by:
            await cb.answer("⚠️ Bu chek allaqon tasdiqlangan yoki rad etilgan!", show_alert=True)
            # tugmalarni olib tashlaymiz, lekin matnni o'zgartirmaymiz
            try:
                await cb.message.edit_reply_markup(None)
            except Exception:
                pass
            return

        # Driverni yaratish yoki yangilash
        if not driver:
            user = await cb.bot.get_chat(driver_id)
            driver = Driver(
                id=driver_id,
                fullname=user.full_name or "Noma’lum",
                username=user.username,
                phone_number=phone_number,
                is_paid=True,
                paid_until=now_tashkent() + timedelta(days=30),
                group_chat_ids=[GROUP_ID],
                added_by=admin_id,
            )
            session.add(driver)
        else:
            driver.is_paid = True
            driver.paid_until = now_tashkent() + timedelta(days=30)
            if GROUP_ID not in (driver.group_chat_ids or []):
                driver.group_chat_ids = (driver.group_chat_ids or []) + [GROUP_ID]
            driver.added_by = admin_id
            if not driver.phone_number and phone_number:
                driver.phone_number = phone_number

        await session.commit()
        # restrictni yechish
        await unrestrict_driver(bot, driver.id, GROUP_ID)

    # ✅ Haydovchiga habar
    join_link = "https://t.me/+uM-iboLNNcQ3OTAy"
    user_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📥 Guruhga qo‘shilish", url=join_link)]]
    )
    sent_msg = await cb.bot.send_message(
        driver_id,
        "<b>✅ Sizning to‘lovingiz tasdiqlandi!</b>\n\nEndi faol haydovchilar ro‘yxatidasiz\n\n"
        "Quyidagi tugma orqali yopiq guruhga qo‘shiling 👇",
        reply_markup=user_kb,
    )

    asyncio.create_task(delete_after(cb.bot, sent_msg.chat.id, sent_msg.message_id))

    # ✅ Chek ostidagi xabarni tahrirlash — eski matnni saqlaymiz
    try:
        status_line = "\n\n✅ Chek tasdiqlangan"
        if cb.message.caption:
            # eski caption saqlanadi, oxiriga qo‘shiladi
            await cb.message.edit_caption(
                caption=(cb.message.caption or "") + status_line,
                parse_mode="HTML",
                reply_markup=None
            )
        elif cb.message.text:
            await cb.message.edit_text(
                text=(cb.message.text or "") + status_line,
                parse_mode="HTML",
                reply_markup=None
            )
    except Exception as e:
        print("Edit error:", e)

    await cb.answer("✅ Tasdiqlandi")



# ─── RAD ETISH ─────────────────────────────
@router.callback_query(F.data.startswith("reject_driver:"))
async def reject_payment(cb: CallbackQuery, state: FSMContext):
    try:
        _, sid = cb.data.split(":", 1)
        driver_id = int(sid)
    except Exception:
        await cb.answer("❌ Callback data noto‘g‘ri", show_alert=True)
        return

    async with async_session() as session:
        driver = await get_driver_by_id(session, driver_id)
        if driver and driver.added_by:
            await cb.answer("❌ Bu chek allaqon tasdiqlangan yoki rad etilgan!", show_alert=True)
            try:
                await cb.message.edit_reply_markup(None)
            except Exception:
                pass
            return

    # Tugmalarni olib tashlash va “Rad etish jarayonida” yozuvi
    status_line = "\n\n❌ Rad etish jarayonida... (sababi kutilmoqda)"
    try:
        if cb.message.caption:
            await cb.message.edit_caption(cb.message.caption + status_line, parse_mode="HTML", reply_markup=None)
        elif cb.message.text:
            await cb.message.edit_text(cb.message.text + status_line, parse_mode="HTML", reply_markup=None)
    except Exception:
        pass

    await state.update_data(driver_id=driver_id, admin_message_id=cb.message.message_id)
    await state.set_state(AdminManageState.enter_reject_reason)
    await cb.message.answer("📝 Rad etish sababini kiriting:")
    await cb.answer()


# ─── RAD ETISH SABABI KIRITILGACH ───────────────────────────────
@router.message(AdminManageState.enter_reject_reason)
async def reject_reason(msg: Message, state: FSMContext):
    data = await state.get_data()
    driver_id = data.get("driver_id")
    admin_message_id = data.get("admin_message_id")
    reason = msg.text

    async with async_session() as session:
        driver = await session.get(Driver, driver_id)
        if driver:
            driver.is_paid = False
            driver.paid_until = None
            driver.added_by = msg.from_user.id
            await session.commit()

    # Chek ostidagi xabarni yangilash
    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.chat.id,
            message_id=admin_message_id,
            caption=f"❌ Chek rad etildi\n\n📝 Sabab: {reason}",
            parse_mode="HTML"
        )
    except Exception:
        try:
            await msg.bot.edit_message_text(
                chat_id=msg.chat.id,
                message_id=admin_message_id,
                text=f"❌ Chek rad etildi\n\n📝 Sabab: {reason}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    # Haydovchiga xabar yuborish
    try:
        await msg.bot.send_message(
            driver_id,
            f"❌ Siz yuborgan to‘lov cheki rad etildi\n\n📝 Sabab: {reason}",
            reply_markup=retry_register_kb(),
        )
    except Exception:
        pass

    await msg.answer("✅ Rad etish sababi yuborildi")
    await state.clear()


# ─── HELPER ─────────────────────────────
async def delete_after(bot, chat_id, message_id, delay=60):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass


