from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.enums.parse_mode import ParseMode
from sqlalchemy import select, func
from datetime import timedelta
from app.database.session import async_session
from app.database.models import User, Driver
from app.keyboards.admin_inline import kb_back4, kb_back2, kb_main
from app.lib.time import now_tashkent

router = Router(name="admin_stats")


@router.callback_query(F.data == "statistics")
async def show_statistics(cb: CallbackQuery):
    today = now_tashkent().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    year_ago = today - timedelta(days=365)

    async with async_session() as session:
        # Umumiy foydalanuvchilar soni
        total = await session.scalar(select(func.count()).select_from(User))

        # Bir kunda ro'yxatdan o'tganlar
        day = await session.scalar(select(func.count()).where(func.date(User.joined_at) == today))

        # Oxirgi 7 kunda ro'yxatdan o'tganlar
        week = await session.scalar(select(func.count()).where(User.joined_at >= week_ago))

        # Oxirgi 30 kunda ro'yxatdan o'tganlar
        month = await session.scalar(select(func.count()).where(User.joined_at >= month_ago))

        # Oxirgi 1 yilda ro'yxatdan o'tganlar
        year = await session.scalar(select(func.count()).where(User.joined_at >= year_ago))

    text = (
        "<b>📊 Yangi foydalanuvchilar:</b>\n\n"
        f"• Bir kunda: <b>{day} ta</b>\n"
        f"• Bir haftada: <b>{week} ta</b>\n"
        f"• Bir oyda: <b>{month} ta</b>\n"
        f"• Bir yilda: <b>{year} ta</b>\n\n"
        f"👥 Umumiy foydalanuvchilar: <b>{total} ta</b>"
    )

    await cb.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb_back4())
    await cb.answer()


@router.callback_query(F.data == "driver_stats")
async def show_driver_stats(cb: CallbackQuery):
    now = now_tashkent()
    one_day_ago = now - timedelta(days=1)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    one_year_ago = now - timedelta(days=365)

    async with async_session() as session:
        # Umumiy haydovchilar soni
        total_drivers = await session.scalar(select(func.count()).select_from(Driver))

        # Qo‘shilganlar statistikasi
        one_day = await session.scalar(select(func.count()).select_from(Driver).where(Driver.joined_at >= one_day_ago))
        seven_days = await session.scalar(select(func.count()).select_from(Driver).where(Driver.joined_at >= seven_days_ago))
        thirty_days = await session.scalar(select(func.count()).select_from(Driver).where(Driver.joined_at >= thirty_days_ago))
        one_year = await session.scalar(select(func.count()).select_from(Driver).where(Driver.joined_at >= one_year_ago))

        # Pullik rejim asosida to‘lov qilgan / qilmagan haydovchilar
        paid_drivers = await session.scalar(select(func.count()).select_from(Driver).where(Driver.is_paid == True))
        unpaid_drivers = total_drivers - paid_drivers

    text = (
        "<b>📊 Haydovchilar statistikasi</b>\n\n"
        "<b>🆕 Yangi qo‘shilganlar:</b>\n"
        f"• Bir kunda: <b>{one_day} ta</b>\n"
        f"• Bir haftada: <b>{seven_days} ta</b>\n"
        f"• Bir oyda: <b>{thirty_days} ta</b>\n"
        f"• Bir yilda: <b>{one_year} ta</b>\n\n"
        "<b>💰 To‘lov holati:</b>\n"
        f"• To‘lov qilganlar: <b>{paid_drivers} ta</b>\n"
        f"• To‘lov qilmaganlar: <b>{unpaid_drivers} ta</b>\n\n"
        f"👥 Umumiy haydovchilar: <b>{total_drivers} ta</b>"
    )

    await cb.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb_back2())
    await cb.answer()


@router.callback_query(F.data == "admin_cancel_stop")
async def cancel_stop(cb: CallbackQuery, state: FSMContext):
    await cb.answer("❌ Bekor qilindi")
    await cb.message.edit_text("❌ Amal bekor qilindi", reply_markup=kb_main())
    await state.clear()