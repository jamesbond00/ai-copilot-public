"""Log ingestion utilities for tailing text files and forwarding new events."""

from __future__ import annotations

import fnmatch
import io
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterator, MutableMapping, Optional, Sequence

from .log_models import LogEvent
from .log_sink import LogSink

LogParser = Callable[[str, str], Optional[LogEvent]]


@dataclass(slots=True)
class LogSourceConfig:
    """Configuration for a single log source."""

    path: str
    include: Sequence[str] = field(default_factory=list)
    exclude: Sequence[str] = field(default_factory=list)
    parser: str = "basic_text"
    batch_size: int = 200


@dataclass(slots=True)
class LogIngestorConfig:
    """Configuration for the log ingestor."""

    sources: Sequence[LogSourceConfig] = field(default_factory=list)
    poll_interval_seconds: int = 120
    max_events_per_poll: int = 1_000
    enabled: bool = True


class LogIngestor:
    """Tails configured log files and forwards parsed events to a sink."""

    def __init__(
        self,
        config: LogIngestorConfig,
        sink: LogSink,
        parser_registry: Optional[Dict[str, LogParser]] = None,
    ) -> None:
        self._config = config
        self._sink = sink
        self._parser_registry = parser_registry or {}
        self._parser_registry.setdefault("basic_text", _default_basic_text_parser())
        self._offsets: MutableMapping[Path, int] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def register_parser(self, name: str, parser: LogParser) -> None:
        self._parser_registry[name] = parser

    def start(self) -> None:
        """Start background ingestion loop."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="LogIngestor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background ingestion loop."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def poll_once(self) -> list[LogEvent]:
        """Collect a batch of new events across all sources."""
        events: list[LogEvent] = []
        for source in self._config.sources:
            parser = self._parser_registry.get(source.parser)
            if not parser:
                continue
            for file_path in self._resolve_files(source):
                events.extend(self._collect_from_file(file_path, parser, source.batch_size))
                if len(events) >= self._config.max_events_per_poll:
                    break
            if len(events) >= self._config.max_events_per_poll:
                break
        if events:
            self._sink.write(events)
        return events

    def _run(self) -> None:
        """Internal worker loop for background polling."""
        while not self._stop_event.is_set():
            try:
                if self._config.enabled:
                    self.poll_once()
            except Exception as exc:  # pragma: no cover - guardrail
                # Avoid crashing the thread; downstream logging framework should capture.
                print(f"LogIngestor encountered an error: {exc}")
            time.sleep(max(self._config.poll_interval_seconds, 1))

    def _resolve_files(self, config: LogSourceConfig) -> Iterator[Path]:
        base = Path(config.path)
        if base.is_file():
            candidates = [base]
        else:
            candidates = list(base.glob("**/*"))
        include = list(config.include) or ["*"]
        exclude = list(config.exclude)

        for candidate in candidates:
            if not candidate.is_file():
                continue
            name = candidate.name
            if not any(fnmatch.fnmatch(name, pattern) for pattern in include):
                continue
            if exclude and any(fnmatch.fnmatch(name, pattern) for pattern in exclude):
                continue
            yield candidate

    def _collect_from_file(self, path: Path, parser: LogParser, batch_size: int) -> list[LogEvent]:
        with self._lock:
            offset = self._offsets.get(path, 0)
            try:
                current_size = path.stat().st_size
                if current_size < offset:
                    offset = 0
                    self._offsets[path] = 0
                with path.open("r", encoding="utf-8", errors="ignore") as handle:
                    handle.seek(offset)
                    buffer: list[LogEvent] = []
                    for _ in range(batch_size):
                        line = handle.readline()
                        if not line:
                            break
                        event = parser(line, str(path))
                        if event:
                            buffer.append(event)
                    self._offsets[path] = handle.tell()
                    return buffer
            except FileNotFoundError:
                self._offsets.pop(path, None)
            except io.UnsupportedOperation:
                # For rotated files that disallow seek, reset offset and retry next poll.
                self._offsets[path] = 0
            except OSError as exc:
                print(f"Warning: failed to read {path}: {exc}")
        return []


def _default_basic_text_parser() -> LogParser:
    from .parsers.basic_text import parse_line

    return parse_line
