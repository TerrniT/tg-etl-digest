# FILE: src/app/logging.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Configure baseline logging for the application runtime.
#   SCOPE: Set root logging level and message format once at startup.
#   DEPENDS: none
#   LINKS: docs/knowledge-graph.xml#M-APP-LOGGING
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   setup_logging — Apply global logging configuration.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

import logging


# START_CONTRACT: setup_logging
#   PURPOSE: Configure root Python logging settings for runtime observability.
#   INPUTS: {}
#   OUTPUTS: { None }
#   SIDE_EFFECTS: mutates global logging configuration
#   LINKS: M-APP-LOGGING
# END_CONTRACT: setup_logging
def setup_logging() -> None:
    # START_BLOCK_APPLY_GLOBAL_LOGGING_CONFIG
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # END_BLOCK_APPLY_GLOBAL_LOGGING_CONFIG
