"""Core data models for log ingestion and analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, MutableSequence, Optional
import uuid


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class LogEvent:
    """Represents a single log entry after basic parsing."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=_utcnow)
    level: str = "INFO"
    source: str = "unknown"
    message: str = ""
    raw: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class LogBatch:
    """Collection of log events emitted together from a source or poll cycle."""

    events: MutableSequence[LogEvent]
    source: str
    collected_at: datetime = field(default_factory=_utcnow)

    def __iter__(self) -> Iterable[LogEvent]:
        return iter(self.events)

    def __len__(self) -> int:
        return len(self.events)
