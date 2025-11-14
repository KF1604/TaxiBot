from aiogram.fsm.state import StatesGroup, State

class PaymentState(StatesGroup):
    waiting_check = State()
    waiting_reject_reason = State()