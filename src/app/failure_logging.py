import logging


def log_failure_event(
    logger: logging.Logger,
    event_code: str,
    error: Exception | str | None = None,
    *,
    severity: str = "SEV2",
) -> None:
    error_type = type(error).__name__ if isinstance(error, Exception) else error or "unknown"
    if not error_type.isidentifier():
        error_type = "unknown"
    logger.error(
        "failure_event event_code=%s severity=%s error_type=%s",
        event_code,
        severity,
        error_type,
    )
