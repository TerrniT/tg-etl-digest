# FILE: src/bot/states.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Define FSM states used by multi-step bot command flows.
#   SCOPE: Hold state group for /add follow-up input handling.
#   DEPENDS: none
#   LINKS: docs/knowledge-graph.xml#M-BOT-STATES
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   AddChannelsFSM — FSM state group for collecting channel list after /add without args.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE module contract and map.
# END_CHANGE_SUMMARY

from aiogram.fsm.state import State, StatesGroup


class AddChannelsFSM(StatesGroup):
    WAITING_CHANNELS_INPUT = State()
