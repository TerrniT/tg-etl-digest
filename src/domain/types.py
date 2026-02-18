# FILE: src/domain/types.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Hold primitive domain type aliases used across parser, storage, and services.
#   SCOPE: Define canonical type wrappers for semantic clarity.
#   DEPENDS: none
#   LINKS: docs/development-plan.xml#M-DOMAIN-TYPES, docs/knowledge-graph.xml#M-DOMAIN-TYPES
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   ChannelHandle — Typed alias for Telegram channel handle string.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE module contract and map.
# END_CHANGE_SUMMARY

from typing import NewType

ChannelHandle = NewType("ChannelHandle", str)
