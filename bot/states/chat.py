from aiogram.fsm.state import State, StatesGroup

class SupportState(StatesGroup):
    on_chat = State()  