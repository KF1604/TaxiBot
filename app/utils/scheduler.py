from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.handlers.admin.sending_payment import send_2days_left_warning, remove_expired_drivers

scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

async def setup_scheduler(bot):

    # 1 kun qolgani haqida ogohlantirish — har kuni soat 11:00 da
    scheduler.add_job(
        send_2days_left_warning,
        trigger=IntervalTrigger(minutes=5),
        args=[bot],
        id="warn_2days_left",
        misfire_grace_time=10,
        replace_existing=True
    )

    # Har 1 soniyada to‘lov muddati o‘tgan haydovchilarni tekshirish
    scheduler.add_job(
        remove_expired_drivers,
        trigger=IntervalTrigger(minutes=1),
        args=[bot],
        id="remove_expired_drivers",
        misfire_grace_time=10,  # 10 soniyagacha kechikishga ruxsat
        replace_existing=True
    )

