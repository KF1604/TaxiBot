from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User, Order, Feedback, Driver
from app.lib.time import now_tashkent
from sqlalchemy import update
from sqlalchemy import select
from app.database.session import async_session

# ─── ID bo‘yicha foydalanuvchi olish ───────────────────
async def get_user_by_id(user_id: int) -> User | None:
    async with async_session() as session:
        return await session.get(User, user_id)

async def get_driver_by_id1(id: int) -> Driver | None:
    async with async_session() as session:
        return await session.get(Driver, id)

# ─── Admin foydalanuvchilar ro‘yxati ────────────────────
async def get_admin_users() -> list[User]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.role.in_(["owner", "super_admin", "admin"]))
        )
        return result.scalars().all()

# ─── Foydalanuvchini bazaga saqlash ─────────────────────
async def save_user(
    user_id: int,
    user_fullname: str,
    phone_number: str | None = None,
    username: str = "",
) -> None:
    async with async_session() as session:
        if not await session.get(User, user_id):
            user = User(
                id=user_id,
                user_fullname=user_fullname,
                phone_number=phone_number,
                username=username,
                joined_at=now_tashkent()
            )
            session.add(user)
            await session.commit()

# ─── Buyurtmani bazaga yozish ──────────────────────────
async def save_order(
    user_id: int,
    user_fullname: str,
    order_type: str,
    phone: str | None,
    comment_to_driver: str | None,
) -> int:
    async with async_session() as session:
        order = Order(
            user_id=user_id,
            user_fullname=user_fullname,
            order_type=order_type,
            phone=phone,
            comment_to_driver=comment_to_driver,
            created_at=now_tashkent()
        )
        session.add(order)
        await session.commit()
        return order.order_id

# ─── Fikr-mulohazani bazaga yozish ─────────────────────
async def save_feedback(user_id: int, fullname: str, text: str) -> Feedback:
    async with async_session() as session:
        fb = Feedback(
            user_id=user_id,
            user_fullname=fullname,
            message_text=text
        )
        session.add(fb)
        await session.commit()
        await session.refresh(fb)
        return fb

async def get_driver_by_id(session: AsyncSession, user_id: int) -> Driver | None:
    result = await session.execute(
        select(Driver).where(Driver.id == user_id)
    )
    return result.scalar_one_or_none()

async def is_driver(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(select(Driver.id).where(Driver.id == user_id))
    return result.scalar_one_or_none() is not None

async def update_driver_phone(user_id: int, new_phone: str) -> None:
    async with async_session() as session:
        result = await session.execute(select(Driver).where(Driver.id == user_id))
        driver = result.scalar_one_or_none()
        if driver:
            driver.phone_number = new_phone
            await session.commit()

async def update_user_phone(user_id: int, phone: str):
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(phone_number=phone)
        )
        await session.commit()

#----Bot rejimiga oid querylar------
async def get_unpaid_drivers():
    async with async_session() as session:
        result = await session.execute(
            select(Driver).where(Driver.is_paid == False)
        )
        return result.scalars().all()


async def get_user_phone(user_id: int) -> str | None:
    async with async_session() as session:
        stmt = select(User.phone_number).where(User.id == user_id)
        result = await session.execute(stmt)
        phone = result.scalar_one_or_none()
        return phone
