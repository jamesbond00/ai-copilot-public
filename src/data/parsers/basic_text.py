"""Basic log line parser for plain-text syslog style records."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from ..log_models import LogEvent

_SYSLOG_PATTERN = re.compile(
    r"^(?P<timestamp>\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<process>[\w/.-]+)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.*)$"
)

_LEVEL_HINTS = {
    "error": "ERROR",
    "warn": "WARN",
    "warning": "WARN",
    "critical": "CRITICAL",
    "info": "INFO",
    "debug": "DEBUG",
}


def parse_line(line: str, source: str) -> Optional[LogEvent]:
    """Parse a raw log line into a LogEvent.

    The parser attempts to extract syslog-style metadata. Lines that do not
    match fall back to a minimal event containing the raw message.
    """

    raw_line = line.rstrip("\n")
    if not raw_line:
        return None

    match = _SYSLOG_PATTERN.match(raw_line)
    if match:
        timestamp_str = match.group("timestamp")
        # Syslog does not include the year; assume current year for now.
        timestamp = _parse_syslog_timestamp(timestamp_str)
        process = match.group("process")
        pid = match.group("pid")
        message = match.group("message").strip()
        metadata = {
            "host": match.group("host"),
            "process": process,
        }
        if pid:
            metadata["pid"] = pid
        level = _infer_level(message)
        return LogEvent(
            timestamp=timestamp,
            level=level,
            source=source,
            message=message,
            raw=raw_line,
            metadata=metadata,
        )

    return LogEvent(
        source=source,
        message=raw_line,
        raw=raw_line,
        level=_infer_level(raw_line),
    )


def _parse_syslog_timestamp(value: str) -> datetime:
    now = datetime.now(timezone.utc)
    try:
        parsed = datetime.strptime(value, "%b %d %H:%M:%S")
        return parsed.replace(year=now.year, tzinfo=timezone.utc)
    except ValueError:
        return now


def _infer_level(message: str) -> str:
    lowered = message.lower()
    for hint, level in _LEVEL_HINTS.items():
        if hint in lowered:
            return level
    return "INFO"
