"""Utilities for retrieving logs and metrics from monitoring systems."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import requests

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 5


@dataclass
class LogEntry:
    """Representation of a single log entry returned by a fetcher."""

    timestamp: datetime
    level: str
    message: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseLogFetcher:
    """Base class for fetchers that retrieve logs from external systems."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.timeout = self.config.get("timeout", DEFAULT_TIMEOUT)

    def test_connection(self) -> bool:
        """Return ``True`` when the underlying monitoring system is reachable."""

        raise NotImplementedError

    def fetch_logs(self, start_time: datetime, end_time: datetime) -> List[LogEntry]:
        """Return logs between ``start_time`` and ``end_time`` inclusive."""

        raise NotImplementedError

    def _safe_request(self, method: str, url: str, **kwargs: Any) -> Optional[requests.Response]:
        """Wrapper around :func:`requests.request` that logs failures."""

        kwargs.setdefault("timeout", self.timeout)

        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:  # pragma: no cover - network failure path
            logger.warning("Request to %s failed: %s", url, exc)
            return None

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        """Best effort conversion of timestamps returned by providers."""

        if isinstance(value, datetime):
            return value

        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value))

        if isinstance(value, str):
            cleaned = value.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(cleaned)
            except ValueError:
                logger.debug("Unable to parse timestamp %r", value)

        return datetime.now()

    @staticmethod
    def _normalise_level(level: Any, default: str = "INFO") -> str:
        if isinstance(level, str) and level:
            return level.upper()
        return default


class ELKFetcher(BaseLogFetcher):
    """Fetch logs from an Elasticsearch (ELK) deployment."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.base_url = (self.config.get("elasticsearch_url") or "").rstrip("/")
        self.index_pattern = self.config.get("index_pattern", "logstash-*")

    def test_connection(self) -> bool:
        if not self.base_url:
            logger.warning("Elasticsearch URL is not configured")
            return False

        health_url = f"{self.base_url}/_cluster/health"
        response = self._safe_request("GET", health_url)
        return response is not None

    def fetch_logs(self, start_time: datetime, end_time: datetime) -> List[LogEntry]:
        if not self.base_url:
            logger.warning("Cannot fetch logs without an Elasticsearch URL")
            return []

        query = {
            "size": self.config.get("max_logs", 500),
            "sort": [{"@timestamp": {"order": "desc"}}],
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": start_time.isoformat(),
                        "lte": end_time.isoformat(),
                    }
                }
            },
        }

        search_url = f"{self.base_url}/{self.index_pattern}/_search"
        response = self._safe_request("POST", search_url, json=query)
        if response is None:
            return []

        try:
            payload = response.json()
        except ValueError:  # pragma: no cover - invalid payload path
            logger.warning("Elasticsearch response did not contain valid JSON")
            return []

        hits: Iterable[Dict[str, Any]] = payload.get("hits", {}).get("hits", [])
        entries: List[LogEntry] = []

        for hit in hits:
            source = hit.get("_source", {})
            timestamp = source.get("@timestamp") or source.get("timestamp")
            level = source.get("level") or source.get("log", {}).get("level", "INFO")
            message = source.get("message") or source.get("log", {}).get("message", "")
            log_source = source.get("source") or source.get("service", {}).get("name", "elasticsearch")

            metadata = {
                key: value
                for key, value in source.items()
                if key not in {"@timestamp", "timestamp", "level", "message", "source", "service"}
            }

            entries.append(
                LogEntry(
                    timestamp=self._parse_timestamp(timestamp),
                    level=self._normalise_level(level),
                    message=str(message),
                    source=str(log_source),
                    metadata=metadata,
                )
            )

        return entries


class PrometheusFetcher(BaseLogFetcher):
    """Fetch time-series data from Prometheus and convert it into log entries."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.base_url = (self.config.get("prometheus_url") or "").rstrip("/")
        self.query = self.config.get("query", "up")
        self.step = self.config.get("step", 60)

    def test_connection(self) -> bool:
        if not self.base_url:
            logger.warning("Prometheus URL is not configured")
            return False

        health_url = f"{self.base_url}/-/healthy"
        response = self._safe_request("GET", health_url)
        if response is None:
            ready_url = f"{self.base_url}/-/ready"
            response = self._safe_request("GET", ready_url)
        return response is not None

    def fetch_logs(self, start_time: datetime, end_time: datetime) -> List[LogEntry]:
        if not self.base_url:
            logger.warning("Cannot fetch metrics without a Prometheus URL")
            return []

        params = {
            "query": self.query,
            "start": start_time.timestamp(),
            "end": end_time.timestamp(),
            "step": self.step,
        }

        query_url = f"{self.base_url}/api/v1/query_range"
        response = self._safe_request("GET", query_url, params=params)
        if response is None:
            return []

        try:
            payload = response.json()
        except ValueError:  # pragma: no cover - invalid payload path
            logger.warning("Prometheus response did not contain valid JSON")
            return []

        if payload.get("status") != "success":
            logger.warning("Prometheus query failed: %s", payload.get("error", "unknown error"))
            return []

        results = payload.get("data", {}).get("result", [])
        entries: List[LogEntry] = []

        for series in results:
            metric = series.get("metric", {})
            samples = series.get("values", [])
            metric_name = metric.get("__name__", "metric")
            source = metric.get("job") or metric.get("instance") or "prometheus"

            for ts, value in samples:
                try:
                    numeric_value: Any = float(value)
                except (TypeError, ValueError):  # pragma: no cover - non numeric sample path
                    numeric_value = value

                metadata = dict(metric)
                metadata["value"] = numeric_value

                entries.append(
                    LogEntry(
                        timestamp=self._parse_timestamp(ts),
                        level="INFO",
                        message=f"{metric_name}={numeric_value}",
                        source=str(source),
                        metadata=metadata,
                    )
                )

        return entries


class SplunkFetcher(BaseLogFetcher):
    """Fetch log events from Splunk's REST API."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.base_url = (self.config.get("splunk_url") or "").rstrip("/")
        self.token = self.config.get("splunk_token")
        self.search_query = self.config.get("search_query", "search index=_internal | head 100")
        self.verify = self.config.get("verify_ssl", False)

    def _headers(self) -> Dict[str, str]:
        if not self.token:
            return {}
        if self.token.lower().startswith("bearer "):
            return {"Authorization": self.token}
        return {"Authorization": f"Bearer {self.token}"}

    def test_connection(self) -> bool:
        if not self.base_url or not self.token:
            logger.warning("Splunk URL or token is not configured")
            return False

        info_url = f"{self.base_url}/services/server/info"
        response = self._safe_request(
            "GET", info_url, headers=self._headers(), verify=self.verify
        )
        return response is not None

    def fetch_logs(self, start_time: datetime, end_time: datetime) -> List[LogEntry]:
        if not self.base_url or not self.token:
            logger.warning("Cannot fetch Splunk logs without URL and token")
            return []

        search = self._build_search_query(start_time, end_time)
        search_url = f"{self.base_url}/services/search/jobs/export"
        response = self._safe_request(
            "POST",
            search_url,
            data={
                "search": search,
                "output_mode": "json",
            },
            headers=self._headers(),
            stream=True,
            verify=self.verify,
        )
        if response is None:
            return []

        entries: List[LogEntry] = []

        for raw_line in response.iter_lines():  # pragma: no branch - simple iteration
            if not raw_line:
                continue

            try:
                event = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):  # pragma: no cover - invalid event path
                continue

            result = event.get("result") or event.get("event")
            if not isinstance(result, dict):
                continue

            timestamp = result.get("_time") or result.get("timestamp")
            message = result.get("_raw") or result.get("message") or ""
            level = result.get("level") or result.get("severity", "INFO")
            source = result.get("source") or result.get("host") or "splunk"

            metadata = {
                key: value
                for key, value in result.items()
                if key not in {"_time", "timestamp", "_raw", "message", "level", "severity", "source", "host"}
            }

            entries.append(
                LogEntry(
                    timestamp=self._parse_timestamp(timestamp),
                    level=self._normalise_level(level),
                    message=str(message),
                    source=str(source),
                    metadata=metadata,
                )
            )

        return entries

    def _build_search_query(self, start_time: datetime, end_time: datetime) -> str:
        earliest = start_time.isoformat()
        latest = end_time.isoformat()
        query = self.search_query.strip()
        if not query.lower().startswith("search"):
            query = f"search {query}"
        return f"{query} earliest={earliest} latest={latest}"


def create_fetcher(system_type: str, config: Optional[Dict[str, Any]] = None) -> BaseLogFetcher:
    """Create a fetcher for the requested monitoring system."""

    system_key = (system_type or "").strip().lower()
    fetcher_map = {
        "elk": ELKFetcher,
        "elasticsearch": ELKFetcher,
        "prometheus": PrometheusFetcher,
        "splunk": SplunkFetcher,
    }

    if system_key not in fetcher_map:
        raise ValueError(f"Unsupported monitoring system: {system_type}")

    fetcher_cls = fetcher_map[system_key]
    return fetcher_cls(config)


__all__ = [
    "LogEntry",
    "BaseLogFetcher",
    "ELKFetcher",
    "PrometheusFetcher",
    "SplunkFetcher",
    "create_fetcher",
]
