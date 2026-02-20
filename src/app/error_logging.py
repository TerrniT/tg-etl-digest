# FILE: src/app/error_logging.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Provide centralized error logging configuration and global exception hooks.
#   SCOPE: Create timestamped error log files, install global exception hooks, and attach asyncio loop handler.
#   DEPENDS: M-APP-LOGGING
#   LINKS: docs/development-plan.xml#M-ERROR-LOGGING, docs/knowledge-graph.xml#M-ERROR-LOGGING
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   build_error_log_path — Build timestamped error log file path under logs/timestamps.
#   setup_error_file_logging — Attach ERROR-level file handler to target logger.
#   install_global_exception_hooks — Install sys/thread unhandled exception hooks.
#   install_asyncio_exception_handler — Install asyncio loop exception handler.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added timestamped error logging module with global hooks.
# END_CHANGE_SUMMARY

from __future__ import annotations

import asyncio
import logging
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_ERROR_LOG_DIR = Path("logs") / "timestamps"


# START_CONTRACT: build_error_log_path
#   PURPOSE: Build deterministic timestamped log file path for error storage.
#   INPUTS: { base_dir: Path|str, now: Optional[datetime] }
#   OUTPUTS: { Path - absolute or relative path to error log file }
#   SIDE_EFFECTS: none
#   LINKS: M-ERROR-LOGGING
# END_CONTRACT: build_error_log_path
def build_error_log_path(
    *,
    base_dir: Path | str = DEFAULT_ERROR_LOG_DIR,
    now: Optional[datetime] = None,
) -> Path:
    # START_BLOCK_RESOLVE_TIMESTAMPED_PATH
    base = Path(base_dir)
    dt = now.astimezone(timezone.utc) if now is not None else datetime.now(timezone.utc)
    stamp = dt.strftime("%Y%m%d-%H%M%S")
    return base / f"{stamp}.log"
    # END_BLOCK_RESOLVE_TIMESTAMPED_PATH


# START_CONTRACT: setup_error_file_logging
#   PURPOSE: Configure ERROR-level file logging into logs/timestamps for runtime failures.
#   INPUTS: { base_dir: Path|str, logger: Optional[logging.Logger], now: Optional[datetime] }
#   OUTPUTS: { Path - created error log file path }
#   SIDE_EFFECTS: creates directories/files and mutates logger handlers
#   LINKS: M-ERROR-LOGGING, M-APP-LOGGING
# END_CONTRACT: setup_error_file_logging
def setup_error_file_logging(
    *,
    base_dir: Path | str = DEFAULT_ERROR_LOG_DIR,
    logger: Optional[logging.Logger] = None,
    now: Optional[datetime] = None,
) -> Path:
    # START_BLOCK_CREATE_LOG_PATH_AND_DIRECTORY
    path = build_error_log_path(base_dir=base_dir, now=now)
    path.parent.mkdir(parents=True, exist_ok=True)
    # END_BLOCK_CREATE_LOG_PATH_AND_DIRECTORY

    # START_BLOCK_ATTACH_ERROR_FILE_HANDLER
    target_logger = logger or logging.getLogger()
    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s [%(funcName)s] %(message)s")
    )
    target_logger.addHandler(file_handler)
    # END_BLOCK_ATTACH_ERROR_FILE_HANDLER

    return path


# START_CONTRACT: install_global_exception_hooks
#   PURPOSE: Capture unhandled sync/thread exceptions and route them to structured logger output.
#   INPUTS: { logger_name: str }
#   OUTPUTS: { None }
#   SIDE_EFFECTS: mutates sys.excepthook and threading.excepthook
#   LINKS: M-ERROR-LOGGING
# END_CONTRACT: install_global_exception_hooks
def install_global_exception_hooks(*, logger_name: str = "app.unhandled") -> None:
    # START_BLOCK_REGISTER_SYNC_AND_THREAD_HOOKS
    hook_logger = logging.getLogger(logger_name)

    def _sys_hook(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        hook_logger.error(
            "[ErrorLogging][install_global_exception_hooks][SYS_UNHANDLED_EXCEPTION] uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    def _thread_hook(args: threading.ExceptHookArgs) -> None:
        hook_logger.error(
            "[ErrorLogging][install_global_exception_hooks][THREAD_UNHANDLED_EXCEPTION] uncaught thread exception",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    sys.excepthook = _sys_hook
    threading.excepthook = _thread_hook
    # END_BLOCK_REGISTER_SYNC_AND_THREAD_HOOKS


# START_CONTRACT: install_asyncio_exception_handler
#   PURPOSE: Capture unhandled asyncio loop exceptions and persist them via logger.
#   INPUTS: { loop: asyncio.AbstractEventLoop, logger_name: str }
#   OUTPUTS: { None }
#   SIDE_EFFECTS: mutates event loop exception handler
#   LINKS: M-ERROR-LOGGING
# END_CONTRACT: install_asyncio_exception_handler
def install_asyncio_exception_handler(
    loop: asyncio.AbstractEventLoop,
    *,
    logger_name: str = "app.unhandled",
) -> None:
    # START_BLOCK_REGISTER_ASYNCIO_EXCEPTION_HANDLER
    hook_logger = logging.getLogger(logger_name)

    def _handler(_loop: asyncio.AbstractEventLoop, context: dict) -> None:
        exception = context.get("exception")
        message = context.get("message", "asyncio unhandled exception")
        if exception is not None:
            hook_logger.error(
                f"[ErrorLogging][install_asyncio_exception_handler][ASYNCIO_UNHANDLED_EXCEPTION] {message}",
                exc_info=exception,
            )
            return
        hook_logger.error(
            f"[ErrorLogging][install_asyncio_exception_handler][ASYNCIO_UNHANDLED_EXCEPTION] {message}"
        )

    loop.set_exception_handler(_handler)
    # END_BLOCK_REGISTER_ASYNCIO_EXCEPTION_HANDLER
