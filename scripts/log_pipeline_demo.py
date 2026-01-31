#!/usr/bin/env python3
"""CLI helper to run a one-off log ingestion and analysis pass."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Optional

# Ensure `src` imports work when executing the script directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.log_ingestor import LogIngestor, LogIngestorConfig, LogSourceConfig
from src.data.log_sink import InMemoryLogSink
from src.llm.config import ConfigManager, LogsConfig
from src.llm.log_analyzer import (
    CompletionClient,
    LogAnalyzer,
    LogAnalyzerConfig,
    LogAnalysisResult,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AI Copilot log analysis pipeline once.")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config file (defaults to ~/.ai-copilot/config.yaml).",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        help="Override the number of events included in the LLM prompt.",
    )
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Skip calling an LLM and print the generated prompt instead.",
    )
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=1_000,
        help="How many recent events to retain in the in-memory sink.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the rendered LLM prompt for inspection.",
    )
    return parser.parse_args()


def resolve_config_path(explicit_path: Optional[str]) -> Optional[str]:
    """Return a config path, preferring user-specified and sample defaults."""

    if explicit_path:
        return explicit_path

    home_config = Path.home() / ".ai-copilot" / "config.yaml"
    if home_config.exists():
        return str(home_config)

    sample_config = PROJECT_ROOT / "docs" / "examples" / "log_pipeline_config.yaml"
    if sample_config.exists():
        return str(sample_config)

    return None


def build_ingestor_config(logs_config: LogsConfig) -> LogIngestorConfig:
    sources = [
        LogSourceConfig(
            path=source.path,
            include=list(source.include),
            exclude=list(source.exclude),
            parser=source.parser,
            batch_size=source.batch_size,
        )
        for source in logs_config.ingestion.sources
    ]
    return LogIngestorConfig(
        sources=sources,
        poll_interval_seconds=logs_config.ingestion.poll_interval_seconds,
        max_events_per_poll=logs_config.ingestion.max_events_per_poll,
        enabled=logs_config.ingestion.enabled,
    )


def build_analyzer_config(logs_config: LogsConfig, args: argparse.Namespace) -> LogAnalyzerConfig:
    analyzer_config = logs_config.analyzer
    if args.max_events is not None:
        analyzer_config = replace(analyzer_config, max_events=args.max_events)
    return analyzer_config


def build_completion_client(
    provider: str,
    manager: ConfigManager,
    prompt_only: bool,
) -> Optional[CompletionClient]:
    if prompt_only:
        return None

    if provider == "local":
        try:
            model = manager.get_model_config("local")
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Warning: could not load local model config: {exc}", file=sys.stderr)
            return None

        try:
            import ollama
        except ImportError as exc:  # pragma: no cover - optional dependency
            print(f"Warning: ollama package unavailable ({exc}); falling back to prompt output.", file=sys.stderr)
            return None

        client = ollama.Client(host=model.host or "http://localhost:11434")

        def _invoke(prompt: str, *, config: LogAnalyzerConfig) -> str:
            response = client.chat(
                model=model.model_id,
                messages=[
                    {"role": "system", "content": "You are an expert SRE log analyst."},
                    {"role": "user", "content": prompt},
                ],
                options={"temperature": 0.3, "num_predict": 1000},
            )
            return response["message"]["content"]

        return _invoke

    if provider == "openai":
        try:
            model = manager.get_model_config("openai")
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Warning: could not load OpenAI model config: {exc}", file=sys.stderr)
            return None

        api_key = model.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY is missing; set it or use --prompt-only.", file=sys.stderr)
            return None

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - optional dependency
            print(f"Warning: openai package unavailable ({exc}); falling back to prompt output.", file=sys.stderr)
            return None

        client = OpenAI(api_key=api_key)

        def _invoke(prompt: str, *, config: LogAnalyzerConfig) -> str:
            completion = client.chat.completions.create(
                model=model.model_id,
                messages=[
                    {"role": "system", "content": "You are an expert SRE log analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
            )
            return completion.choices[0].message.content

        return _invoke

    print(f"Warning: provider '{provider}' not supported yet; use --prompt-only for now.", file=sys.stderr)
    return None


def print_result(result: LogAnalysisResult, verbose: bool) -> None:
    print("Summary:\n", result.summary)
    if result.anomalies:
        print("\nAnomalies:")
        for item in result.anomalies:
            print(f" - {item}")
    else:
        print("\nAnomalies: none flagged")

    if result.recommendations:
        print("\nRecommendations:")
        for rec in result.recommendations:
            print(f" - {rec}")
    else:
        print("\nRecommendations: none suggested")

    if verbose and result.metadata.get("prompt"):
        print("\n--- Prompt Preview (LLM was not invoked) ---\n")
        print(result.metadata["prompt"])


def main() -> int:
    args = parse_args()
    config_path = resolve_config_path(args.config)
    if config_path:
        manager = ConfigManager(config_file=config_path)
    else:
        manager = ConfigManager()

    sample_config = PROJECT_ROOT / "docs" / "examples" / "log_pipeline_config.yaml"
    if not args.config and config_path and Path(config_path) == sample_config:
        print(f"Using sample config file at {sample_config}")
    logs_config = manager.get_log_config()

    if not logs_config.ingestion.sources:
        default_location = Path.home() / ".ai-copilot" / "config.yaml"
        print(
            "No log sources configured. Update"
            f" {default_location} or pass --config."
            f" Sample config: {sample_config}"
        )
        return 1

    ingestor_config = build_ingestor_config(logs_config)
    sink = InMemoryLogSink(max_events=args.buffer_size)
    ingestor = LogIngestor(config=ingestor_config, sink=sink)

    analyzer_config = build_analyzer_config(logs_config, args)
    completion_client = build_completion_client(analyzer_config.provider, manager, args.prompt_only)
    analyzer = LogAnalyzer(config=analyzer_config, client=completion_client)

    events = ingestor.poll_once()
    if not events:
        print("No new log events found. Try again after new data is written.")
        return 0

    result = analyzer.analyze(events)
    print_result(result, verbose=args.verbose or completion_client is None)
    print(f"\nAnalyzed {len(events)} events from {len(set(event.source for event in events))} sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
