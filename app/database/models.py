from sqlalchemy import (
    Integer, String
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, Text, Boolean, TIMESTAMP, ForeignKey, ARRAY
from datetime import datetime
from app.lib.time import now_tashkent

# ─── Bazaviy model ────────────────────────────────
class Base(DeclarativeBase):
    pass

# ─── Foydalanuvchi modeli ─────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_fullname: Mapped[str] = mapped_column(Text, nullable=False)
    username: Mapped[str | None] = mapped_column(Text)
    phone_number: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String, nullable=False, default="user")
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    joined_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=now_tashkent,
        nullable=False
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="user",
        cascade="all, delete"
    )

# ─── Buyurtma modeli ──────────────────────────────
class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))

    user_fullname: Mapped[str] = mapped_column(Text, nullable=False)
    order_type: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str | None] = mapped_column(Text)
    comment_to_driver: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=now_tashkent,
        nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="orders")

# ─── Feedback modeli ───────────────────────────────
class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_fullname: Mapped[str] = mapped_column(Text, nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)

    answer_text: Mapped[str | None] = mapped_column(Text)
    answered_by: Mapped[int | None] = mapped_column(BigInteger)
    is_answered: Mapped[bool] = mapped_column(Boolean, server_default="false")

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=now_tashkent,
    )
    answered_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(type_=BigInteger, primary_key=True)
    fullname: Mapped[str] = mapped_column(type_=Text, nullable=False)
    username: Mapped[str | None] = mapped_column(type_=Text, nullable=True)
    phone_number: Mapped[str] = mapped_column(type_=Text, nullable=False)
    group_chat_ids: Mapped[list[int]] = mapped_column(type_=ARRAY(BigInteger), default=[])
    is_paid: Mapped[bool] = mapped_column(type_=Boolean, default=False)

    added_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    joined_at: Mapped[datetime] = mapped_column(
        type_=TIMESTAMP(timezone=True),
        default=now_tashkent,
        nullable=False
    )

    paid_until: Mapped[datetime | None] = mapped_column(
        type_=TIMESTAMP(timezone=True),
        nullable=True
    )