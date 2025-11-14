# import re
# import asyncio
# import logging
# from typing import List, Tuple
# from aiogram import Router, types
# from aiogram.utils.keyboard import InlineKeyboardBuilder
# from aiogram.types import ChatPermissions
# from app.data.data import TAXI_KEYWORDS, TRASH_KEYWORDS
#
# # ---------------------------
# # 🔧 Sozlamalar
# # ---------------------------
# SOURCE_CHAT_IDS: List[int] = [
#     -1002663700498,  # manba guruh
# ]
#
# TARGET_CHAT_IDS: List[int] = [
#     -1002957473385,  # haydovchilar guruhi
# ]
#
# THROTTLE_SECONDS = 0.5
#
# # ✅ Regex patternni bir marta kompilyatsiya qilamiz
# TAXI_PATTERN = re.compile('|'.join(map(re.escape, TAXI_KEYWORDS)), re.IGNORECASE)
#
# # ---------------------------
# # 🧩 Log sozlamalari
# # ---------------------------
# logger = logging.getLogger("forwarder")
# if not logger.handlers:
#     logging.basicConfig(
#         level=logging.INFO,
#         format="[%(asctime)s] %(levelname)s - %(message)s"
#     )
#
# router = Router(name="forwarder")
# _seen_messages: set[Tuple[int, int]] = set()
#
#
# # ---------------------------
# # 📤 Forward qilish
# # ---------------------------
# @router.message()
# async def forward_messages(message: types.Message):
#     if message.chat.id not in SOURCE_CHAT_IDS:
#         return
#
#     msg_key = (message.chat.id, message.message_id)
#     if msg_key in _seen_messages:
#         return
#     _seen_messages.add(msg_key)
#
#     text = (message.text or message.caption or "")
#
#     # 🔴 Trash keywords tekshirish
#     if any(word.lower() in text.lower() for word in TRASH_KEYWORDS):
#         try:
#             # Xabarni o‘chirish
#             await message.delete()
#             logger.info(f"Keraksiz xabar o‘chirildi: {message.from_user.full_name}")
#
#             # Foydalanuvchini restrict qilish
#             await message.chat.restrict(
#                 user_id=message.from_user.id,
#                 permissions=ChatPermissions(
#                     can_send_messages=False,
#                     can_send_media_messages=False,
#                     can_send_polls=False,
#                     can_send_other_messages=False,
#                     can_add_web_page_previews=False,
#                     can_change_info=False,
#                     can_invite_users=False,
#                     can_pin_messages=False
#                 ),
#                 until_date=None  # cheksiz restrict qilamiz, yoki datetime berish mumkin
#             )
#             logger.info(f"{message.from_user.full_name} foydalanuvchisi restrict qilindi")
#         except Exception as e:
#             logger.warning(f"⚠️ Keraksiz xabarni o‘chirish/restrict qilishda xato: {e}")
#         return # shu joyda to‘xtaydi, hech narsa forward qilinmaydi
#
#     # ✅ Regex orqali barcha triggerlarni birdan tekshiramiz (tezroq)
#     if not TAXI_PATTERN.search(text):
#         return
#
#     sender = message.from_user
#     full_name = sender.full_name or "Noma’lum foydalanuvchi"
#     username_display = f"@{sender.username}" if sender.username else "❌ yopiq akkaunt"
#     phone_display = "📞 Telefon: 📵 Maxfiy"
#
#     caption = (
#         f"💥 <b>Yangi buyurtma!</b>\n\n"
#         f"👤 <b>Ismi:</b> {full_name}\n"
#         f"🔗 <b>Akkaunt:</b> {username_display}\n"
#         f"🆔 <b>ID:</b> <code>{sender.id}</code>\n"
#         f"{phone_display}\n\n"
#         f"💬 <b>Mijoz xabari:</b> {message.text or message.caption}"
#     )
#
#     kb = InlineKeyboardBuilder()
#     if sender.username:
#         kb.button(text="👉 Mijozga yozish 👈", url=f"tg://resolve?domain={sender.username}")
#     else:
#         kb.button(text="👉 Mijozga yozish 👈", url=f"tg://user?id={sender.id}")
#     kb.adjust(1)
#
#     # ✅ Avval xabarni o‘chirish
#     try:
#         await message.delete()
#         logger.info(f"🗑️ Xabar o‘chirildi: {full_name}")
#     except Exception as e:
#         logger.warning(f"⚠️ Xabarni o‘chirishda muammo: {e}")
#
#     # ✅ So‘ng xabarni yuborish
#     for target_id in TARGET_CHAT_IDS:
#         try:
#             if message.photo:
#                 await message.bot.send_photo(
#                     target_id,
#                     photo=message.photo[-1].file_id,
#                     caption=caption,
#                     parse_mode="HTML",
#                     reply_markup=kb.as_markup()
#                 )
#             elif message.video:
#                 await message.bot.send_video(
#                     target_id,
#                     video=message.video.file_id,
#                     caption=caption,
#                     parse_mode="HTML",
#                     reply_markup=kb.as_markup()
#                 )
#             else:
#                 await message.bot.send_message(
#                     target_id,
#                     caption,
#                     parse_mode="HTML",
#                     reply_markup=kb.as_markup()
#                 )
#             await asyncio.sleep(THROTTLE_SECONDS)
#         except Exception as e:
#             logger.error(f"❌ Forward xatolik: {e}")


# import os
# import re
# import asyncio
# import logging
# from typing import List, Tuple
# from aiogram import Router, types
# from aiogram.utils.keyboard import InlineKeyboardBuilder
# from aiogram.types import ChatPermissions
# from sqlalchemy import select
# from app.data.data import TAXI_KEYWORDS, TRASH_KEYWORDS, DRIVER_KEYWORDS
# from app.database.session import async_session
# from app.database.models import Driver
#
# # ---------------------------
# # 🔧 Sozlamalar
# # ---------------------------
# SOURCE_CHAT_IDS: List[int] = list(map(int, os.getenv("SOURCE_CHAT_IDS", "").split(",")))
# TARGET_CHAT_IDS: List[int] = list(map(int, os.getenv("TARGET_CHAT_IDS", "").split(",")))
# THROTTLE_SECONDS = 0.5
#
# TAXI_PATTERN = re.compile('|'.join(map(re.escape, TAXI_KEYWORDS)), re.IGNORECASE)
#
# # Haydovchi e'lonlarini aniqlash uchun keywords
# DRIVER_PATTERN = re.compile('|'.join(map(re.escape, DRIVER_KEYWORDS)), re.IGNORECASE)
#
# logger = logging.getLogger("forwarder")
# if not logger.handlers:
#     logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")
#
# router = Router(name="forwarder")
# _seen_messages: set[Tuple[int, int]] = set()
#
#
# async def is_registered_driver(user_id: int) -> bool:
#     """DB orqali foydalanuvchi haydovchi ekanligini tekshiradi."""
#     async with async_session() as session:
#         result = await session.execute(
#             select(Driver).where(Driver.id == user_id)
#         )
#         driver = result.scalar_one_or_none()
#         return driver is not None
#
# @router.message()
# async def handle_message(message: types.Message):
#     if message.chat.id not in SOURCE_CHAT_IDS:
#         return
#
#     msg_key = (message.chat.id, message.message_id)
#     if msg_key in _seen_messages:
#         return
#     _seen_messages.add(msg_key)
#
#     text = message.text or message.caption or ""
#
#     # ---------------------------
#     # 🔴 Trash keywords tekshirish
#     # ---------------------------
#     if any(word.lower() in text.lower() for word in TRASH_KEYWORDS):
#         try:
#             await message.delete()
#             logger.info(f"Keraksiz xabar o‘chirildi: {message.from_user.full_name}")
#             await message.chat.restrict(
#                 user_id=message.from_user.id,
#                 permissions=ChatPermissions(can_send_messages=False),
#                 until_date=None
#             )
#             logger.info(f"{message.from_user.full_name} restrict qilindi")
#         except Exception as e:
#             logger.warning(f"⚠️ Trash xabarni o‘chirish/restrict qilishda xato: {e}")
#         return
#
#     # ---------------------------
#     # 👤 Haydovchi aniqlash
#     # ---------------------------
#     if DRIVER_PATTERN.search(text):
#         try:
#             await message.delete()
#
#             full_name = message.from_user.full_name or "Foydalanuvchi"
#
#             kb = InlineKeyboardBuilder()
#             kb.button(text="Ro'yxatdan o'tish", url="https://t.me/YourBot?start=register")
#             kb.adjust(1)
#
#             warning_text = (
#                 f"❗ Hurmatli {full_name}, "
#                 "bizning guruhda e'lon joylashtirish uchun avval ro'yxatdan o'tishingiz zarur."
#             )
#
#             # ⚡ Bot orqali xabar yuborish
#             await message.bot.send_message(
#                 chat_id=message.chat.id,
#                 text=warning_text,
#                 reply_markup=kb.as_markup()
#             )
#
#             await message.chat.restrict(
#                 user_id=message.from_user.id,
#                 permissions=ChatPermissions(can_send_messages=False),
#                 until_date=None
#             )
#
#             logger.info(f"Begona foydalanuvchi {full_name} restrict qilindi va ogohlantirildi")
#         except Exception as e:
#             logger.warning(f"⚠️ Begona haydovchi xabari bilan ishlashda xato: {e}")
#
#     # ---------------------------
#     # 💬 Mijoz xabarlari forward
#     # ---------------------------
#     if TAXI_PATTERN.search(text):
#         sender = message.from_user
#         full_name = sender.full_name or "Noma’lum foydalanuvchi"
#         username_display = f"@{sender.username}" if sender.username else "❌ yopiq akkaunt"
#         phone_display = "📞 Telefon: 📵 Maxfiy"
#
#         caption = (
#             f"💥 <b>Yangi buyurtma!</b>\n\n"
#             f"👤 <b>Ismi:</b> {full_name}\n"
#             f"🔗 <b>Akkaunt:</b> {username_display}\n"
#             f"🆔 <b>ID:</b> <code>{sender.id}</code>\n"
#             f"{phone_display}\n\n"
#             f"💬 <b>Mijoz xabari:</b> {message.text or message.caption}"
#         )
#
#         kb = InlineKeyboardBuilder()
#         if sender.username:
#             kb.button(text="👉 Mijozga yozish 👈", url=f"tg://resolve?domain={sender.username}")
#         else:
#             kb.button(text="👉 Mijozga yozish 👈", url=f"tg://user?id={sender.id}")
#         kb.adjust(1)
#
#         try:
#             await message.delete()
#         except Exception as e:
#             logger.warning(f"⚠️ Xabarni o‘chirishda muammo: {e}")
#
#         for target_id in TARGET_CHAT_IDS:
#             try:
#                 if message.photo:
#                     await message.bot.send_photo(
#                         target_id,
#                         photo=message.photo[-1].file_id,
#                         caption=caption,
#                         parse_mode="HTML",
#                         reply_markup=kb.as_markup()
#                     )
#                 elif message.video:
#                     await message.bot.send_video(
#                         target_id,
#                         video=message.video.file_id,
#                         caption=caption,
#                         parse_mode="HTML",
#                         reply_markup=kb.as_markup()
#                     )
#                 else:
#                     await message.bot.send_message(
#                         target_id,
#                         caption,
#                         parse_mode="HTML",
#                         reply_markup=kb.as_markup()
#                     )
#                 await asyncio.sleep(THROTTLE_SECONDS)
#             except Exception as e:
#                 logger.error(f"❌ Forward xatolik: {e}")




import re
import asyncio
import logging
from typing import List, Tuple
from aiogram import Router, types, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ChatPermissions
from sqlalchemy import select
from app.database.session import async_session
from app.database.models import Driver
from app.data.data import DRIVER_KEYWORDS, TAXI_KEYWORDS, TRASH_KEYWORDS
import os
from dotenv import load_dotenv

load_dotenv()

SOURCE_CHAT_IDS: List[int] = list(map(int, os.getenv("SOURCE_CHAT_IDS", "").split(",")))
TARGET_CHAT_IDS: List[int] = list(map(int, os.getenv("TARGET_CHAT_IDS", "").split(",")))
THROTTLE_SECONDS = 0.5

DRIVER_PATTERN = re.compile('|'.join(map(re.escape, DRIVER_KEYWORDS)), re.IGNORECASE)
TAXI_PATTERN = re.compile('|'.join(map(re.escape, TAXI_KEYWORDS)), re.IGNORECASE)

logger = logging.getLogger("forwarder")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

router = Router(name="forwarder")
_seen_messages: set[Tuple[int, int]] = set()


async def is_registered_driver(user_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(select(Driver).where(Driver.id == user_id))
        driver = result.scalar_one_or_none()
        return driver is not None


@router.message()
async def handle_message(message: types.Message):
    if message.chat.id not in SOURCE_CHAT_IDS:
        return

        # 🔹 Adminlarni tekshiramiz
    member = await message.chat.get_member(message.from_user.id)
    if member.status in {"creator", "administrator"} or message.from_user.is_bot:
        return

    msg_key = (message.chat.id, message.message_id)
    if msg_key in _seen_messages:
        return
    _seen_messages.add(msg_key)

    text = message.text or message.caption or ""

    # Trash xabarlar
    if any(word.lower() in text.lower() for word in TRASH_KEYWORDS):
        try:
            await message.delete()
            logger.info(f"Keraksiz xabar o‘chirildi: {message.from_user.full_name}")
            await message.chat.restrict(
                user_id=message.from_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=None
            )
        except Exception as e:
            logger.warning(f"⚠️ Trash xabarni o‘chirish/restrict qilishda xato: {e}")
        return

    # Haydovchi ro'yxatdan o'tganligini tekshirish
    is_driver = await is_registered_driver(message.from_user.id)

    if is_driver:
        # Ro'yxatdan o'tgan haydovchi → xabari guruhda qoladi
        return

        # 🔹 Begona haydovchi e'loni
    if DRIVER_PATTERN.search(text):
        try:
            await message.delete()
            kb = InlineKeyboardBuilder()
            kb.button(
                text="Ro'yxatdan o'tish",
                url="https://t.me/toshkent1_andijon_bot?start=register"
            )
            kb.adjust(1)

            # 🔗 Foydalanuvchi uchun to‘g‘ri link
            user = message.from_user
            if user.username:
                user_link = f"<a href='https://t.me/{user.username}'>{user.full_name}</a>"
            else:
                user_link = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"

            warning_text = (
                f"❗ Hurmatli {user_link}\n\n"
                "Bizning guruhda e'lon joylashtirish uchun avval ro'yxatdan o'tishingiz zarur"
            )

            # ⚠️ Xabar obyekti sifatida saqlaymiz
            warning_msg = await message.answer(
                warning_text,
                reply_markup=kb.as_markup(),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

            # Foydalanuvchini yozishdan cheklaymiz
            await message.chat.restrict(
                user_id=message.from_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=None
            )

            logger.info(f"Begona foydalanuvchi {message.from_user.full_name} restrict qilindi va ogohlantirildi")

            # 🕐 1 daqiqa kutiladi, so‘ng ogohlantirish xabari o‘chiriladi
            asyncio.create_task(delete_warning_after_delay(warning_msg))

        except Exception as e:
            logger.warning(f"⚠️ Begona haydovchi xabari bilan ishlashda xato: {e}")
        return

    # Mijoz xabarlarini forward qilish
    if TAXI_PATTERN.search(text):
        sender = message.from_user
        full_name = sender.full_name or "Noma’lum foydalanuvchi"
        username_display = f"@{sender.username}" if sender.username else "❌ yopiq akkaunt"
        phone_display = "📞 Telefon: 📵 Maxfiy"

        caption = (
            f"💥 <b>Yangi buyurtma!</b>\n\n"
            f"👤 <b>Ismi:</b> {full_name}\n"
            f"🔗 <b>Akkaunt:</b> {username_display}\n"
            f"🆔 <b>ID:</b> <code>{sender.id}</code>\n"
            f"{phone_display}\n\n"
            f"💬 <b>Mijoz xabari:</b> {text}"
        )

        # kb = InlineKeyboardBuilder()
        # if sender.username:
        #     kb.button(text="👉 Mijozga yozish 👈", url=f"tg://resolve?domain={sender.username}")
        # else:
        #     kb.button(text="👉 Mijozga yozish 👈", url=f"tg://user?id={sender.id}")
        # kb.adjust(1)

        kb = InlineKeyboardBuilder()
        if sender.username:
            kb.button(text="👉 Mijozga yozish 👈", url=f"tg://resolve?domain={sender.username}")
            kb.adjust(1)
        else:
            # Yopiq akkaunt, tugma yaratmaymiz
            logger.info(f"Foydalanuvchi yopiq, tugma yuborilmadi: {sender.id}")

        # ✅ Avval xabarni o‘chirish
        try:
            await message.delete()
            logger.info(f"🗑️ Xabar o‘chirildi: {full_name}")
        except Exception as e:
            logger.warning(f"⚠️ Xabarni o‘chirishda muammo: {e}")

        # ✅ So‘ng xabarni yuborish
        for target_id in TARGET_CHAT_IDS:
            try:
                if message.photo:
                    await message.bot.send_photo(
                        target_id,
                        photo=message.photo[-1].file_id,
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=kb.as_markup()
                    )
                elif message.video:
                    await message.bot.send_video(
                        target_id,
                        video=message.video.file_id,
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=kb.as_markup()
                    )
                else:
                    await message.bot.send_message(
                        target_id,
                        caption,
                        parse_mode="HTML",
                        reply_markup=kb.as_markup()
                    )
                await asyncio.sleep(THROTTLE_SECONDS)
            except Exception as e:
                logger.error(f"❌ Forward xatolik: {e}")


async def unrestrict_driver(bot: Bot, user_id: int, chat_id: int):
    """Haydovchi ro'yxatdan o'tgach restrictni olib tashlaydi."""
    try:
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )
        )
    except Exception as e:
        logger.warning(f"⚠️ {user_id} restrictni yechishda xato: {e}")

# 🔸 1 daqiqadan keyin ogohlantirishni o‘chiruvchi yordamchi funksiya
async def delete_warning_after_delay(warning_msg: types.Message, delay: int = 300):
    try:
        await asyncio.sleep(delay)
        await warning_msg.delete()
    except Exception as e:
        logger.warning(f"⚠️ Ogohlantirish xabarini o‘chirishda xato: {e}")