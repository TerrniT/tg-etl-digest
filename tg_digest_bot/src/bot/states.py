from aiogram.fsm.state import State, StatesGroup


class AddChannelsFSM(StatesGroup):
    WAITING_CHANNELS_INPUT = State()
