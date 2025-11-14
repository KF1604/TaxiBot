import asyncio
import logging
from datetime import timedelta, datetime
from html import escape

from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, or_
from aiogram import Bot, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ContentType, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from app.database.session import async_session
from app.database.models import Driver
from app.keyboards.driver_inline import retry_payment_kb
from app.lib.time import now_tashkent
from app.database.queries import get_admin_users
from app.states.click_states import PaymentState

sending_router = Router(name="payment_checker")

WARNING_DAYS = 2
BATCH_SIZE = 200
MAX_PARALLEL = 10


# ─── 1️⃣ Ogohlantirish yuborish ─────────
async def send_2days_left_warning(bot: Bot, amount: int = 50000):
    now = now_tashkent()
    warning_time = now + timedelta(days=2)

    async with async_session() as session:
        result = await session.execute(
            select(Driver).where(
                Driver.is_paid == True,
                Driver.paid_until <= warning_time,
                Driver.paid_until > now
            )
        )
        drivers = result.scalars().all()

        for driver in drivers:
            text = (
                f"⚠️ <b>Diqqat! Obuna muddati yakunlanmoqda</b>\n\n"
                f"Hurmatli <b>{driver.fullname}</b>\n\n"
                f"Sizning pullik xizmatlardan foydalanish muddati tugashiga <b>2 kun</b> qoldi\n\n"
                f"💰 To‘lov miqdori: <b>{amount:,} (ellik ming) so‘m</b>\n"
                f"⏳ Amal qilish muddati: <b>{driver.paid_until.strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
                f"Iltimos, belgilangan muddat ichida to‘lovni amalga oshiring\n"
                f"Aks holda sizning bot xizmatlaringiz cheklanadi va guruhdan avtomatik tarzda chiqarib yuborilasiz"
            )
            kb = InlineKeyboardBuilder()
            kb.button(text="To'lov qilish", callback_data=f"payment_start:{driver.id}")
            kb.adjust(1)

            try:
                await bot.send_message(chat_id=driver.id, text=text, reply_markup=kb.as_markup())
                logging.info(f"🔔 Ogohlantirish yuborildi: {driver.id}")

                # 🔹 Admin javobgarligini olib tashlash
                driver.added_by = None
                await session.commit()

            except Exception as e:
                logging.warning(f"❌ Xabar yuborilmadi: {driver.id} — {e}")

            await asyncio.sleep(0.06)


# ─── 2️⃣ To‘lov tugmasi bosilganda karta raqam ko‘rsatish ─────────
@sending_router.callback_query(F.data.startswith("payment_start:"))
async def payment_start_(cb: CallbackQuery, state: FSMContext):
    try:
        parts = cb.data.split(":")
        if len(parts) < 2 or not parts[1]:
            await cb.answer("❌ Driver ID topilmadi", show_alert=True)
            return
        driver_id = int(parts[1])
    except Exception:
        await cb.answer("❌ Driver ID noto‘g‘ri", show_alert=True)
        return

    card_number = "9860160602412274"
    try:
        sent_msg = await cb.message.edit_text(
            "🏦 <b>To‘lovni amalga oshirish</b>\n\n"
            f"💳 <b>Karta raqam:</b> {card_number}\n"
            f"👤 <b>Karta egasi:</b> SHOHRUH MIRZAYEV\n\n"
            "🧾 To‘lov qilganingizdan so‘ng chekni shu yerga yuboring",
            parse_mode="HTML"
        )
        await state.update_data(payment_card_message_id=cb.message.message_id)
    except Exception:
        pass
    await cb.answer()

# ─── 3️⃣ Chek yuborish ─────────
@sending_router.message(F.content_type.in_({"photo", "document"}))
async def handle_payment_check_(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == PaymentState.waiting_check:
        pass

    driver_id = msg.from_user.id
    allowed_extensions = (".pdf", ".png", ".jpg", ".jpeg")

    async with async_session() as session:
        driver = await session.get(Driver, driver_id)
        if not driver:
            return await msg.answer("❌ Siz topilmadingiz. Iltimos, qayta urinib ko‘ring")

    # Fayl turini aniqlash
    if msg.content_type == ContentType.DOCUMENT:
        doc = msg.document
        if not doc.file_name.lower().endswith(allowed_extensions):
            return await msg.answer("❌ Faqat PDF, PNG yoki JPG fayl yuboring")
        file_ref = doc.file_id
        is_document = True
    else:
        file_ref = msg.photo[-1].file_id
        is_document = False

    # Avvalgi karta raqamli xabarni o'chirish
    data = await state.get_data()
    old_message_id = data.get("payment_card_message_id")
    if old_message_id:
        try:
            await msg.bot.delete_message(chat_id=driver_id, message_id=old_message_id)
        except Exception:
            pass

    # Adminlarga yuborish
    username = f"@{msg.from_user.username}" if msg.from_user.username else "—"
    caption = (
        f"🧾 <b>Obuna muddatini uzaytirish uchun to'lov</b>\n\n"
        f"👤 Ismi: <b>{escape(msg.from_user.full_name)}</b>\n"
        f"🔗 Username: {escape(username)}\n"
        f"☎️ Telefon: {escape(getattr(driver, 'phone_number', '—'))}\n"
        f"🆔 Telegram ID: <code>{driver_id}</code>\n"
        f"⏰ Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        "Chekni tekshirib, tasdiqlang yoki rad eting ⬇️"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_payment:{driver_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_payment:{driver_id}")
        ]]
    )

    admins = await get_admin_users()
    if not admins:
        logging.warning("⚠️ Adminlar ro'yxati bo'sh, hech kimga yuborilmayapti!")
        return

    for admin in admins:
        try:
            if is_document:
                await msg.bot.send_document(chat_id=admin.id, document=file_ref, caption=caption, parse_mode="HTML", reply_markup=kb)
            else:
                await msg.bot.send_photo(chat_id=admin.id, photo=file_ref, caption=caption, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            logging.error(f"❌ Adminga yuborishda xatolik {admin.id}: {e}", exc_info=True)
            continue

    # State yangilash: yangi yuborilgan xabar
    await state.update_data(driver_id=driver_id, file_ref=file_ref, is_document=is_document)
    await state.set_state(PaymentState.waiting_check)
    await msg.answer("✅ Chekingiz yuborildi. Admin tasdiqlashini kuting...")



# ─── 2️⃣ Admin tasdiqlaydi ─────────
@sending_router.callback_query(F.data.startswith("approve_payment:"))
async def approve_driver_(cb: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == PaymentState.waiting_check:
        return

    driver_id = int(cb.data.split(":")[1])

    async with async_session() as session:
        driver = await session.get(Driver, driver_id)
        if not driver:
            await cb.answer("❌ Haydovchi topilmadi", show_alert=True)
            return

        # ✅ Bu joyni tashqariga olib chiqamiz
        if driver.added_by:
            await cb.answer("⚠️ Chek allaqachon tasdiqlangan yoki rad etilgan!", show_alert=True)
            try:
                await cb.message.edit_reply_markup(None)
            except Exception:
                pass
            return

        # Obuna muddatini yangilash
        old_paid_until = driver.paid_until or now_tashkent()
        today = now_tashkent()
        if old_paid_until > today:
            next_month = (old_paid_until.replace(day=1) + timedelta(days=32)).replace(day=old_paid_until.day)
            driver.paid_until = next_month
        else:
            driver.paid_until = today + timedelta(days=30)

        driver.is_paid = True
        driver.added_by = cb.from_user.id
        await session.commit()

    try:
        # Inline tugmalar olib tashlanadi va oxiriga status qo‘shiladi
        if cb.message.caption:
            new_caption = f"{cb.message.caption}\n\n✅ Chek tasdiqlangan"
            await cb.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
        else:
            new_text = f"{cb.message.text}\n\n✅ Chek tasdiqlangan"
            await cb.message.edit_text(text=new_text, parse_mode="HTML", reply_markup=None)
    except Exception as e:
        logging.warning(f"❌ Message update xatosi: {e}")

    # Foydalanuvchiga xabar yuborish
    await cb.bot.send_message(driver_id,
        f"Hurmatli <b>{driver.fullname}</b>!\n\n"
        f"Sizning toʻlovingiz tasdiqlandi! ✅\n"
        f"Endilikda siz botdagi barcha xizmatlardan toʻliq foydalana olasiz!\n\n"
        f"💵 Toʻlangan summa: <b>50.000 (ellik ming) so'm</b>\n"
        f"🗓 Obuna muddati: <b>{driver.paid_until.strftime('%d.%m.%Y | %H:%M')} gacha</b>\n\n"
        f"🚘 Safarlaringiz serdaromad, yo'llaringiz bexatar bo'lsin!\n"
    )
    await cb.answer("✅ Tasdiqlandi")
    await state.clear()


# ─── 3️⃣ Admin rad etadi ─────────
@sending_router.callback_query(F.data.startswith("reject_payment:"))
async def reject_payment_(cb: CallbackQuery, state: FSMContext):
    try:
        _, sid = cb.data.split(":", 1)
        driver_id = int(sid)
    except Exception:
        await cb.answer("❌ Callback data noto‘g‘ri.", show_alert=True)
        return

    async with async_session() as session:
        driver = await session.get(Driver, driver_id)
        if driver and driver.added_by:
            await cb.answer("❌ Bu chek allaqachon tasdiqlangan yoki rad etilgan!", show_alert=True)
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
    await state.set_state(PaymentState.waiting_reject_reason)
    await cb.message.answer("📝 Rad etish sababini kiriting:")
    await cb.answer()


# ─── RAD ETISH SABABI KIRITILGACH ───────────────────────────────
@sending_router.message(PaymentState.waiting_reject_reason)
async def reject_reason_(msg: Message, state: FSMContext):
    data = await state.get_data()
    driver_id = data.get("driver_id")
    admin_message_id = data.get("admin_message_id")
    reason = msg.text

    async with async_session() as session:
        driver = await session.get(Driver, driver_id)
        if driver:
            driver.is_paid = True
            driver.added_by = None  # 🔹 Admin rad etganda ham o‘chirish
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
            reply_markup=retry_payment_kb(driver_id),
        )
    except Exception:
        pass

    await msg.answer("✅ Rad etish sababi yuborildi")
    await state.clear()


async def remove_expired_drivers(bot: Bot):
    now = now_tashkent()

    async with async_session() as session:
        # 1️⃣ To‘lov muddati o‘tgan haydovchilarni olish
        result = await session.execute(
            select(Driver).where(
                or_(
                    Driver.is_paid == False,
                    Driver.paid_until == None,
                    Driver.paid_until < now
                )
            ).limit(BATCH_SIZE)
        )
        unpaid_drivers = result.scalars().all()

        if not unpaid_drivers:
            logging.info("⚠️ To‘lov muddati o‘tgan haydovchilar topilmadi")
            return

        removed_count = 0
        sem = asyncio.Semaphore(MAX_PARALLEL)

        async def process_driver(driver: Driver):
            nonlocal removed_count
            async with sem:
                group_ids = getattr(driver, "group_chat_ids", [])
                if not group_ids:
                    return

                for group_id in group_ids:
                    try:
                        # Guruhdan chiqarish: ban + unban
                        await bot.ban_chat_member(group_id, driver.id)
                        await bot.unban_chat_member(group_id, driver.id)
                        logging.info(f"🚫 Haydovchi {driver.id} guruhdan chiqarildi: {group_id}")
                        await asyncio.sleep(0.5)
                    except TelegramBadRequest as e:
                        logging.warning(f"⚠️ Haydovchi {driver.id} ({group_id}) chiqarilmadi: {e}")
                    except Exception as e:
                        logging.error(f"❌ Guruhdan chiqarishda xatolik {driver.id} ({group_id}): {e}")

                removed_count += 1

        # 2️⃣ Parallel ishlov
        await asyncio.gather(*(process_driver(d) for d in unpaid_drivers))

        # 3️⃣ Bazadan o‘chirish
        for d in unpaid_drivers:
            await session.delete(d)

        # 4️⃣ Commit qilish
        await session.commit()
        logging.info(f"🧾 Jami o‘chirilgan haydovchilar: {removed_count}")