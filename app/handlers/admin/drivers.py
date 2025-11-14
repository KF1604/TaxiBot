import asyncio
import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from app.database.session import async_session
from app.database.models import Driver, User
from app.database.queries import get_user_by_id
from app.handlers.admin.forwarder import unrestrict_driver
from app.lib.time import now_tashkent
from app.states.admin_states import AdminManageState
from app.utils import escape_html
from app.utils.helpers import normalize_phone
from app.keyboards.admin_reply import cancel_reply_kb
from app.keyboards.admin_inline import (
    kb_main,
    drivers_menu_buttons, confirm_remove_buttons, confirm_driver_edit_buttons, kb_back2
)
from datetime import timedelta

from dispatcher import bot

router = Router(name="admin_drivers")

GROUP_ID = int(os.getenv("SOURCE_CHAT_IDS"))

# ─── Haydovchilar menyusi ─────────────────────────────
@router.callback_query(F.data == "driver_manage")
async def open_driver_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    admin = await get_user_by_id(cb.from_user.id)
    role = admin.role or "admin"
    await cb.message.edit_text(
        "<b>🚖 Haydovchilar bo‘limi</b>\n\nKerakli amalni tanlang:",
        reply_markup=drivers_menu_buttons(role),
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

# ─── Haydovchi qo‘shish ───────────────────────────────
@router.callback_query(F.data == "add_driver")
async def add_driver_prompt(cb: CallbackQuery, state: FSMContext):
    """1) Admindan haydovchi Telegram ID so‘raladi"""
    await state.clear()
    await state.set_state(AdminManageState.adding_driver_id)
    await cb.message.answer(
        "🆔 Iltimos, haydovchi Telegram ID’sini kiriting:",
        reply_markup=cancel_reply_kb()
    )
    await cb.answer()


@router.message(AdminManageState.adding_driver_id)
async def input_driver_id(msg: Message, state: FSMContext):
    """Telegram ID tekshiriladi va guruh ID bosqichiga o‘tiladi"""
    if not msg.text or not msg.text.strip().isdigit():
        return await msg.answer("⚠️ Faqat raqamli ID yuboring. Misol: 123456789")

    user_id = int(msg.text.strip())
    if user_id > 9223372036854775807:
        return await msg.answer("❌ Juda katta ID")

    # Bazadagi foydalanuvchini olish
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            return await msg.answer("❌ Bunday Telegram ID li foydalanuvchi topilmadi")

        existing_driver = await session.get(Driver, user_id)
        if existing_driver:
            return await msg.answer("⚠️ Ushbu foydalanuvchi allaqachon haydovchi sifatida ro‘yxatlangan")

    # Telefon raqami users jadvalidan olinadi
    phone = user.phone_number
    username = f"@{user.username}" if user.username else None

    await state.update_data(
        driver_id=user.id,
        driver_fullname=user.user_fullname or "—",
        driver_phone=phone,
        driver_username=username
    )
    await state.set_state(AdminManageState.adding_driver_groups)
    await msg.answer(
        f"✅ Foydalanuvchi topildi:\n\n"
        f"👤 <b>Ismi:</b> {user.user_fullname or '—'}\n"
        f"🔗 <b>Username:</b> {username if username else ''}\n"
        f"☎️ <b>Telefon:</b> {user.phone_number or 'aniqlanmadi'}\n\n"
        "📌 Endi haydovchining guruh ID’larini kiriting (vergul bilan ajrating, agar bir nechta bo‘lsa):",
        parse_mode=ParseMode.HTML,
        reply_markup=cancel_reply_kb()
    )

@router.message(AdminManageState.adding_driver_groups)
async def input_driver_groups(msg: Message, state: FSMContext):
    """Guruh ID’lari kiritilib, haydovchi ro‘yxatga qo‘shiladi va xabar yuboriladi"""
    groups_text = msg.text.strip()
    try:
        group_ids = [int(x.strip()) for x in groups_text.split(",") if x.strip()]
    except ValueError:
        return await msg.answer("❌ Guruh ID’lari faqat raqam bo‘lishi kerak, vergul bilan ajrating.")

    data = await state.get_data()
    driver_id = data.get("driver_id")
    fullname = data.get("driver_fullname")
    username = data.get("driver_username")
    phone = data.get("driver_phone")
    admin_id = msg.from_user.id

    async with async_session() as session:
        existing_driver = await session.get(Driver, driver_id)
        if existing_driver:
            await state.clear()
            return await msg.answer(
                "⚠️ Ushbu foydalanuvchi allaqachon haydovchi sifatida ro‘yxatlangan",
                reply_markup=kb_main()
            )

        paid_until = now_tashkent() + timedelta(days=30)

        driver = Driver(
            id=driver_id,
            fullname=fullname,
            username=username,
            phone_number=phone,
            group_chat_ids=group_ids,
            added_by=admin_id,
            is_paid=True,
            paid_until=paid_until
        )
        session.add(driver)
        await session.commit()
        await unrestrict_driver(bot, driver.id, GROUP_ID)

    await state.clear()

    # ✅ Haydovchiga shaxsiy xabar yuborish
    join_link = "https://t.me/+uM-iboLNNcQ3OTAy"
    user_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📥 Guruhga qo‘shilish", url=join_link)]]
    )
    sent_msg = await msg.bot.send_message(
        driver_id,
        "<b>✅ Siz haydovchi sifatida ro‘yxatga olindingiz!</b>\n\n"
        "Quyidagi tugma orqali yopiq haydovchilar guruhiga qo‘shilishingiz mumkin 👇",
        reply_markup=user_kb,
        parse_mode=ParseMode.HTML
    )

    # Xabarni 30 soniyadan keyin avtomatik o'chirish
    import asyncio
    asyncio.create_task(delete_after(msg.bot, sent_msg.chat.id, sent_msg.message_id))

    await msg.answer(
        (
            f"✅ Haydovchi muvaffaqiyatli qo‘shildi\n\n"
            f"👤 <b>Ismi: </b>{fullname}\n"
            f"🔗 <b>Username: </b>{username}\n"
            f"☎️ <b>Telefon: </b>{phone or '—'}\n"
            f"👥 <b>Guruhlar: </b>{group_ids}\n"
            f"💰 <b>To‘lov holati: </b>Tasdiqlangan (avtomatik)\n"
            f"📅 <b>Obuna muddati: </b>{paid_until.strftime('%d.%m.%Y | %H:%M gacha')}\n"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=kb_main()
    )


# ─── HELPER ─────────────────────────────
async def delete_after(bot, chat_id, message_id, delay=30):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

# ─── Haydovchini o‘chirish ───────────────────────────
@router.callback_query(F.data == "remove_driver")
async def prompt_driver_id_removal(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AdminManageState.removing_driver_id)
    await cb.message.answer("🗑 O‘chiriladigan haydovchi ID’sini kiriting:", reply_markup=cancel_reply_kb())
    await cb.answer()

@router.message(AdminManageState.removing_driver_id)
async def confirm_driver_removal(msg: Message, state: FSMContext):
    try:
        driver_id = int(msg.text.strip())
    except:
        return await msg.answer("⚠️ Noto‘g‘ri ID")

    async with async_session() as session:
        driver = await session.get(Driver, driver_id)
        if not driver:
            return await msg.answer("❌ Haydovchi topilmadi")

    await state.update_data(driver_id=driver.id, fullname=driver.fullname)

    # Guruh ID larni ko‘rsatish
    group_list = driver.group_chat_ids or []
    groups_text = "\n".join([f"• <code>{gid}</code>" for gid in group_list]) if group_list else "❌ Yo‘q"

    text = (
        f"<b>Haydovchini o‘chirish:</b>\n\n"
        f"<b>👤 Ismi:</b> {escape_html(driver.fullname)}\n"
        f"<b>🆔:</b> <code>{driver.id}</code>\n"
        f"<b>🔗 Username:</b> @{driver.username or '—'}\n"
        f"<b>☎️ Telefon:</b> <code>{driver.phone_number or '❌ Yo‘q'}</code>\n"
        f"<b>👥 Guruh ID(lar)i:</b> {groups_text}\n\n"
        f"<b>⚠️ Ushbu haydovchini rostdan ham o‘chirmoqchimisiz?</b>"
    )

    await state.set_state(AdminManageState.confirming_driver_rm)
    await msg.answer(text, parse_mode="HTML", reply_markup=confirm_remove_buttons())

@router.callback_query(AdminManageState.confirming_driver_rm, F.data.in_([
    "confirm_rm", "retry_rm", "cancel_rm"]))
async def finish_driver_removal(cb: CallbackQuery, state: FSMContext):
    if cb.data == "cancel_rm":
        await state.clear()
        await cb.message.edit_text("❌ O‘chirish bekor qilindi")  # Inline bo‘lgani uchun markup olib tashlandi
        return await cb.answer()

    if cb.data == "retry_rm":
        await state.set_state(AdminManageState.removing_driver_id)
        await cb.message.delete()
        await cb.message.answer("🔁 Haydovchi ID’sini qayta kiriting:", reply_markup=cancel_reply_kb())
        return await cb.answer()

    # confirm_rm holati:
    data = await state.get_data()
    async with async_session() as session:
        driver = await session.get(Driver, data["driver_id"])
        if driver:
            await session.delete(driver)
            await session.commit()

    await state.clear()
    await cb.message.edit_text("✅ Haydovchi o‘chirildi", reply_markup=kb_main())
    await cb.answer()

# ─── Telefon raqamni tahrirlash ──────────────────────
@router.callback_query(F.data == "edit_driver_phone2")
async def ask_driver_id_for_edit(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AdminManageState.editing_driver_id)
    await cb.message.answer("🆔 Haydovchi Telegram ID’sini kiriting:", reply_markup=cancel_reply_kb())
    await cb.answer()

@router.message(AdminManageState.editing_driver_id)
async def show_current_phone_and_ask_new(msg: Message, state: FSMContext):
    try:
        driver_id = int(msg.text.strip())
    except:
        return await msg.answer("⚠️ Noto‘g‘ri ID")

    async with async_session() as session:
        driver = await session.get(Driver, driver_id)
        if not driver:
            return await msg.answer("❌ Haydovchi topilmadi")

    await state.update_data(driver_id=driver_id, fullname=driver.fullname)

    current_phone = driver.phone_number or "—"
    await state.set_state(AdminManageState.editing_driver_phone)
    await msg.answer(
        f"<b>👤 Haydovchi:</b> {escape_html(driver.fullname)}\n"
        f"<b>🆔:</b> <code>{driver.id}</code>\n"
        f"<b>☎️ Joriy telefon raqami:</b> {current_phone}\n\n"
        f"☎️ Yangi telefon raqamni kiriting:",
        parse_mode="HTML",
        reply_markup=cancel_reply_kb()
    )

@router.message(AdminManageState.editing_driver_phone)
async def confirm_new_phone(msg: Message, state: FSMContext):
    phone = normalize_phone(msg.text)
    if not phone:
        return await msg.answer("⚠️ Telefon raqam noto‘g‘ri\n\nMasalan: +998901234567")

    data = await state.get_data()
    driver_id = data.get("driver_id")

    async with async_session() as session:
        driver = await session.get(Driver, driver_id)
        if not driver:
            return await msg.answer("❌ Haydovchi topilmadi")
        current_phone = driver.phone_number

    if phone == current_phone:
        return await msg.answer("⚠️ Yangi telefon raqam joriy raqam bilan bir xil\n\nIltimos, boshqacha raqam kiriting.")

    await state.update_data(new_phone=phone)

    text = (
        f"<b>👤 Haydovchi:</b> {escape_html(driver.fullname)}\n"
        f"<b>🆔:</b> <code>{driver.id}</code>\n"
        f"<b>☎️ Yangi telefon:</b> {phone}\n\n"
        f"<b>⚠️ Tasdiqlaysizmi?</b>"
    )
    await msg.answer(text, parse_mode="HTML", reply_markup=confirm_driver_edit_buttons())
    await state.set_state(AdminManageState.confirming_driver_phone_edit)

@router.callback_query(AdminManageState.confirming_driver_phone_edit, F.data.in_([
    "confirm_driver_edit", "cancel_driver_edit"]))
async def finish_editing_driver_phone(cb: CallbackQuery, state: FSMContext):
    if cb.data == "cancel_driver_edit":
        await state.clear()
        return await cb.message.edit_text("❌ Bekor qilindi", reply_markup=kb_main())

    data = await state.get_data()
    async with async_session() as session:
        driver = await session.get(Driver, data["driver_id"])
        if not driver:
            return await cb.message.edit_text("❌ Topilmadi")
        driver.phone_number = data["new_phone"]
        await session.commit()

    await state.clear()
    await cb.message.edit_text("✅ Telefon raqami yangilandi!", reply_markup=kb_main())
    await cb.answer()


@router.callback_query(F.data == "find_driver")
async def prompt_driver_search(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AdminManageState.finding_driver_id)
    await cb.message.answer("🔍 Haydovchi ID’sini kiriting:", reply_markup=cancel_reply_kb())
    await cb.answer()

@router.message(AdminManageState.finding_driver_id)
async def process_driver_search(msg: Message, state: FSMContext):
    if not msg.text or not msg.text.strip().isdigit():
        return await msg.answer("⚠️ Faqat raqamli ID ni yuboring.")

    driver_id = int(msg.text.strip())
    async with async_session() as session:
        driver = await session.get(Driver, driver_id)
        if not driver:
            return await msg.answer("❌ Haydovchi topilmadi.")

    group_list = driver.group_chat_ids or []
    groups_text = "\n".join([f"<code>{gid}</code>" for gid in group_list]) if group_list else "❌ Yo‘q"

    # To‘lov holati va obuna muddati alohida oling
    tolov_holati = "✅ To‘langan" if driver.is_paid else "❌ To‘lanmagan"
    obuna_muddati = driver.paid_until.strftime("%d.%m.%Y | %H:%M") if driver.paid_until else "—"

    text = (
        f"<b>🚖 Haydovchi ma’lumotlari:</b>\n\n"
        f"👤 <b>Ismi:</b> {escape_html(driver.fullname)}\n"
        f"🆔 <b>ID:</b> <code>{driver.id}</code>\n"
        f"🔗 <b>Username:</b> @{driver.username or '—'}\n"
        f"☎️ <b>Telefon raqami:</b> {driver.phone_number or '—'}\n"
        f"👥 <b>Joriy guruhlar:</b> {groups_text}\n"
        f"🧑‍💼 <b>Qo‘shgan admin:</b> <code>{driver.added_by}</code>\n"
        f"📅 <b>Qo‘shilgan sana:</b> {driver.joined_at.strftime('%d.%m.%Y | %H:%M') if driver.joined_at else '—'}\n"
        f"⏳ <b>Obuna muddati:</b> {obuna_muddati}"
    )

    await state.clear()
    await msg.answer(text, parse_mode="HTML", reply_markup=kb_back2())