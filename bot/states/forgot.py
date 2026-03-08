from aiogram.fsm.state import State, StatesGroup


class ForgotPassword(StatesGroup):
    username = State()
    phone = State()
    new_password = State()