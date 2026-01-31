"""Sinks that store or forward log events produced by the ingestor."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from threading import Lock
from typing import Deque, Iterable
from queue import Queue

from .log_models import LogEvent, LogBatch


class LogSink(ABC):
    """Abstract destination for log events."""

    @abstractmethod
    def write(self, events: Iterable[LogEvent]) -> None:
        """Persist or forward the provided events."""


class InMemoryLogSink(LogSink):
    """Keeps a bounded, thread-safe buffer of recent events in memory."""

    def __init__(self, max_events: int = 1_000) -> None:
        self._buffer: Deque[LogEvent] = deque(maxlen=max_events)
        self._lock = Lock()

    def write(self, events: Iterable[LogEvent]) -> None:
        with self._lock:
            for event in events:
                self._buffer.append(event)

    def snapshot(self) -> list[LogEvent]:
        with self._lock:
            return list(self._buffer)


class QueueLogSink(LogSink):
    """Publishes events to a queue for downstream workers."""

    def __init__(self, queue: Queue[LogBatch | LogEvent]) -> None:
        self._queue = queue

    def write(self, events: Iterable[LogEvent]) -> None:
        batch = list(events)
        if not batch:
            return
        if len(batch) == 1:
            self._queue.put(batch[0])
        else:
            self._queue.put(LogBatch(events=batch, source=batch[0].source))


class NullLogSink(LogSink):
    """Swallows events; useful for dry runs or tests."""

    def write(self, events: Iterable[LogEvent]) -> None:  # pragma: no cover - intentionally empty
        return
