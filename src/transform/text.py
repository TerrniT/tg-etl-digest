# FILE: src/transform/text.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Provide reusable text normalization primitives for ETL pipeline.
#   SCOPE: Clean whitespace and truncate strings with ellipsis behavior.
#   DEPENDS: none
#   LINKS: docs/development-plan.xml#M-TRANSFORM-TEXT, docs/knowledge-graph.xml#M-TRANSFORM-TEXT
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   clean_text — Collapse whitespace and strip text.
#   truncate_text — Truncate text to max length with trailing ellipsis.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

import re

_WS_RE = re.compile(r"\s+")


# START_CONTRACT: clean_text
#   PURPOSE: Normalize arbitrary text by collapsing whitespace into single spaces.
#   INPUTS: { text: str }
#   OUTPUTS: { str - cleaned text }
#   SIDE_EFFECTS: none
#   LINKS: M-TRANSFORM-TEXT
# END_CONTRACT: clean_text
def clean_text(text: str) -> str:
    # START_BLOCK_CLEAN_WHITESPACE
    if not text:
        return ""
    return _WS_RE.sub(" ", text).strip()
    # END_BLOCK_CLEAN_WHITESPACE


# START_CONTRACT: truncate_text
#   PURPOSE: Trim text to maximum length preserving readability with ellipsis.
#   INPUTS: { text: str, max_chars: int }
#   OUTPUTS: { str - truncated or original text }
#   SIDE_EFFECTS: none
#   LINKS: M-TRANSFORM-TEXT
# END_CONTRACT: truncate_text
def truncate_text(text: str, max_chars: int) -> str:
    # START_BLOCK_TRUNCATE_WITH_ELLIPSIS
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 1)].rstrip() + "…"
    # END_BLOCK_TRUNCATE_WITH_ELLIPSIS
