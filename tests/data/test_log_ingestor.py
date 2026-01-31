from datetime import datetime, timezone

from src.data.log_ingestor import LogIngestor, LogIngestorConfig, LogSourceConfig
from src.data.log_sink import InMemoryLogSink


def _format_syslog(message: str) -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%b %d %H:%M:%S") + f" test-host app[123]: {message}\n"


def test_poll_once_reads_new_lines(tmp_path):
    log_file = tmp_path / "app.log"
    first_line = _format_syslog("First event")
    with log_file.open("w", encoding="utf-8") as handle:
        handle.write(first_line)

    sink = InMemoryLogSink(max_events=10)
    source = LogSourceConfig(path=str(log_file))
    config = LogIngestorConfig(sources=[source], max_events_per_poll=10)
    ingestor = LogIngestor(config=config, sink=sink)

    first_batch = ingestor.poll_once()
    assert len(first_batch) == 1
    assert sink.snapshot()[0].message.endswith("First event")

    second_line = _format_syslog("Second event")
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(second_line)

    second_batch = ingestor.poll_once()
    assert len(second_batch) == 1
    assert sink.snapshot()[-1].message.endswith("Second event")


def test_ingestor_skips_when_no_new_data(tmp_path):
    log_file = tmp_path / "app.log"
    with log_file.open("w", encoding="utf-8") as handle:
        handle.write(_format_syslog("Only event"))

    sink = InMemoryLogSink(max_events=10)
    source = LogSourceConfig(path=str(log_file))
    config = LogIngestorConfig(sources=[source], max_events_per_poll=10)
    ingestor = LogIngestor(config=config, sink=sink)

    ingestor.poll_once()
    subsequent = ingestor.poll_once()
    assert subsequent == []
    assert len(sink.snapshot()) == 1
