"""LLM-driven log analysis pipeline built on top of structured log events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Protocol, Sequence

from ..data.log_models import LogEvent
from ..data.log_ingestor import LogIngestor


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CompletionClient(Protocol):
    """Protocol for LLM completion clients."""

    def __call__(self, prompt: str, *, config: "LogAnalyzerConfig") -> str:
        ...


class ResultHandler(Protocol):
    """Simple protocol for persisting analysis results."""

    def __call__(self, result: "LogAnalysisResult") -> None:
        ...


@dataclass(slots=True)
class LogAnalyzerConfig:
    """Configuration options that control log analysis behaviour."""

    provider: str = "local"
    prompt_template: str = "log_summary_v1"
    max_events: int = 200
    anomaly_threshold: str = "medium"
    include_raw_lines: bool = False


@dataclass(slots=True)
class LogAnalysisResult:
    """Structured output returned from the LLM analyzer."""

    summary: str
    anomalies: list[str]
    recommendations: list[str]
    raw_event_ids: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=_utcnow)
    provider: str = "local"
    prompt_token_count: Optional[int] = None
    metadata: dict[str, str] = field(default_factory=dict)


class DefaultPromptBuilder:
    """Renders a prompt for the configured log events."""

    def build(self, events: Sequence[LogEvent], config: LogAnalyzerConfig) -> str:
        header = (
            "You are an experienced site reliability engineer. Provide a concise "
            "summary of the operational state, anomalies, and next actions."
        )
        lines = [header, "\nRecent log events:"]
        for event in events[: config.max_events]:
            snippet = event.message.replace("\n", " ")
            timestamp = event.timestamp.isoformat()
            lines.append(f"- [{timestamp}] {event.level.upper()} {snippet}")
        lines.append(
            "\nReturn your findings in JSON with keys summary, anomalies, recommendations."
        )
        return "\n".join(lines)


class LogAnalyzer:
    """Coordinates prompt building, LLM execution, and response parsing."""

    def __init__(
        self,
        config: LogAnalyzerConfig,
        client: Optional[CompletionClient] = None,
        prompt_builder: Optional[DefaultPromptBuilder] = None,
    ) -> None:
        self._config = config
        self._client = client
        self._prompt_builder = prompt_builder or DefaultPromptBuilder()

    @property
    def config(self) -> LogAnalyzerConfig:
        return self._config

    def analyze(self, events: Sequence[LogEvent]) -> LogAnalysisResult:
        if not events:
            return LogAnalysisResult(
                summary="No log events to analyze.",
                anomalies=[],
                recommendations=[],
                provider=self._config.provider,
            )

        prompt = self._prompt_builder.build(events, self._config)
        raw_ids = [event.event_id for event in events]

        if not self._client:
            return LogAnalysisResult(
                summary="LLM client not configured; generated prompt for manual review.",
                anomalies=[],
                recommendations=[],
                raw_event_ids=raw_ids,
                provider=self._config.provider,
                metadata={"prompt": prompt},
            )

        response = self._client(prompt, config=self._config)
        return self._parse_response(response, raw_ids)

    def _parse_response(self, response: str, event_ids: list[str]) -> LogAnalysisResult:
        summary = response.strip()
        anomalies: list[str] = []
        recommendations: list[str] = []

        try:
            import json

            parsed = json.loads(response)
            summary = str(parsed.get("summary", summary))
            anomalies = [str(item) for item in parsed.get("anomalies", [])]
            recommendations = [str(item) for item in parsed.get("recommendations", [])]
        except Exception:
            segments = [segment.strip() for segment in response.split("RECOMMENDATIONS:")]
            if len(segments) == 2:
                summary_section, rec_section = segments
                summary = summary_section
                recommendations = [line.strip("- ") for line in rec_section.splitlines() if line.strip()]

        return LogAnalysisResult(
            summary=summary,
            anomalies=anomalies,
            recommendations=recommendations,
            raw_event_ids=event_ids,
            provider=self._config.provider,
        )


class LogAnalyzerPipeline:
    """High-level pipeline that connects ingestion with the analyzer and sink."""

    def __init__(
        self,
        ingestor: LogIngestor,
        analyzer: LogAnalyzer,
        result_handler: Optional[ResultHandler] = None,
    ) -> None:
        self._ingestor = ingestor
        self._analyzer = analyzer
        self._result_handler = result_handler

    def process_once(self) -> Optional[LogAnalysisResult]:
        events = self._ingestor.poll_once()
        if not events:
            return None
        result = self._analyzer.analyze(events)
        if result and self._result_handler:
            self._result_handler(result)
        return result
