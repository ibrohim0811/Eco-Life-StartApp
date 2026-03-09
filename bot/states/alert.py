from aiogram.fsm.state import State, StatesGroup

class EcoALert(StatesGroup):
    video=State()
    location=State()