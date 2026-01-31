# Log Ingestion & Analysis Pipeline

This document describes the architecture that powers periodic text log ingestion and LLM-backed analysis.

## Components

- **`src/data/log_models.py`** — canonical definitions for `LogEvent` and `LogBatch` objects shared across ingestion and analysis layers.
- **`src/data/log_ingestor.py`** — polls configured filesystem paths, tails new lines, and forwards parsed events to a sink.
- **`src/data/parsers/basic_text.py`** — syslog-style parser that converts raw lines into structured `LogEvent` payloads.
- **`src/data/log_sink.py`** — sink interfaces (`InMemoryLogSink`, `QueueLogSink`, `NullLogSink`) that collect events or hand them off to workers.
- **`src/llm/log_analyzer.py`** — builds prompts, invokes LLM clients, and parses analysis responses. Includes a `LogAnalyzerPipeline` helper that wires the ingestor to downstream result handlers.

## Configuring Sources

Define sources in `~/.ai-copilot/config.yaml` under a top-level `logs:` key:

```yaml
logs:
  ingestion:
    enabled: true
    poll_interval_seconds: 120
    max_events_per_poll: 500
    sources:
      - path: /var/log
        include: ["*.log", "syslog"]
        exclude: ["*debug*"]
        parser: basic_text
        batch_size: 200
  analyzer:
    provider: local
    prompt_template: log_summary_v1
    max_events: 200
    anomaly_threshold: medium
    include_raw_lines: false
```

Each `path` can point to a directory or a specific file. `include`/`exclude` accept glob patterns. Parsers are looked up by name; `basic_text` ships with the project, and additional parsers can be registered at runtime via `LogIngestor.register_parser`.

## Environment Variable Overrides

- `AI_COPILOT_LOG_ENABLED` — when `true`, enables ingestion even without YAML config.
- `AI_COPILOT_LOG_POLL_INTERVAL` — polling cadence (seconds).
- `AI_COPILOT_LOG_MAX_EVENTS` — cap on events processed per poll cycle.
- `AI_COPILOT_LOG_SOURCES` — JSON list of source objects or a comma-separated list of file paths.
- `AI_COPILOT_LOG_ANALYZER` — JSON object mirroring the `logs.analyzer` section for quick overrides.

## CLI Smoke Test

Use `python scripts/log_pipeline_demo.py` to run a single ingestion + analysis pass from the terminal. The script reads the same configuration, prints summaries, and can be pointed at real providers or run with `--prompt-only` to inspect the generated prompt without invoking an LLM.

## Next Steps

1. Wire a scheduler (e.g., APScheduler) to call `LogIngestor.poll_once()` or run the built-in background thread.
2. Implement a concrete result handler to persist `LogAnalysisResult` objects (database, queue, dashboard cache).
3. Expand parser coverage for multi-line stack traces and structured formats (JSON logs, CSV, etc.).
