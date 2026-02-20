from datetime import datetime, timezone
import logging

from src.app.error_logging import build_error_log_path, setup_error_file_logging


def test_build_error_log_path_uses_utc_timestamp():
    now = datetime(2026, 2, 19, 12, 34, 56, tzinfo=timezone.utc)
    path = build_error_log_path(base_dir="logs/timestamps", now=now)
    assert str(path).endswith("logs/timestamps/20260219-123456.log")


def test_setup_error_file_logging_writes_errors(tmp_path):
    logger = logging.getLogger("tests.error_logging")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.INFO)

    path = setup_error_file_logging(base_dir=tmp_path, logger=logger)
    logger.error("test-error-line")

    for handler in logger.handlers:
        handler.flush()
        handler.close()
    logger.handlers = []

    content = path.read_text(encoding="utf-8")
    assert "test-error-line" in content
