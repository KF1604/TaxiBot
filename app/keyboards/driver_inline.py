from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def registered_driver_menu_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="👤 Shaxsiy kabinet", callback_data="driver_profile")],
        [InlineKeyboardButton(text="◀️ Ortga qaytish", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def unregistered_driver_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📝 Ro'yxatdan o'tish", callback_data="register_driver")],
        [InlineKeyboardButton(text="◀️ Ortga qaytish", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


#-----Shaxsiy kabinet bosqichidagi tugmalar--------------------
def driver_profile_options_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="☎️ Telefon raqamni o‘zgartirish", callback_data="edit_driver_phone")],
        [InlineKeyboardButton(text="◀️ Ortga qaytish", callback_data="driver_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def driver_profile_options_kb2() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="☎️ Telefon raqamni o‘zgartirish", callback_data="edit_phone")],
        [InlineKeyboardButton(text="◀️ Ortga qaytish", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def driver_phone_confirm_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_driver_phone")],
        [InlineKeyboardButton(text="❌ Xato, qayta kiritish", callback_data="retry_driver_phone")],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def to_main_menu_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")]]
    )

def confirm_payment_kb(payment_uid: str):
    buttons = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_driver_{payment_uid}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_payment_{payment_uid}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
    # kb.button(text="✅ Tasdiqlash", callback_data=f"approve_driver_{payment_uid}")
    # kb.button(text="❌ Rad etish", callback_data=f"reject_payment_{payment_uid}")
    # kb.adjust(2)
    # return kb.as_markup()

def retry_register_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Chekni qayta yuborish", callback_data="register_driver")
    return kb.as_markup()

def retry_payment_kb(driver_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Chekni qayta yuborish", callback_data=f"payment_start:{driver_id}")
    return kb.as_markup()