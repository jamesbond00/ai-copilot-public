"""
Configuration management for LLM models and analyzers.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .log_analyzer import LogAnalyzerConfig as PipelineAnalyzerConfig


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    provider: str  # "local" or "openai"
    model_id: str  # e.g., "qwen2:1.5b", "gpt-3.5-turbo"
    temperature: float = 0.3
    max_tokens: int = 1000
    host: Optional[str] = None  # For local models
    api_key: Optional[str] = None  # For OpenAI models


@dataclass
class AnalyzerConfig:
    """Configuration for the analyzer system."""
    preferred_provider: str = "local"  # "local" or "openai"
    fallback_provider: str = "openai"
    local_model: str = "qwen2:1.5b"
    openai_model: str = "gpt-3.5-turbo"
    openai_api_key: Optional[str] = None
    ollama_host: str = "http://localhost:11434"
    enable_hybrid: bool = True


@dataclass
class LogSourceSettings:
    """Configuration for a single log source target."""

    path: str
    include: Sequence[str] = field(default_factory=list)
    exclude: Sequence[str] = field(default_factory=list)
    parser: str = "basic_text"
    batch_size: int = 200


@dataclass
class LogIngestionSettings:
    """Scheduling and batching controls for log ingestion."""

    enabled: bool = False
    poll_interval_seconds: int = 120
    max_events_per_poll: int = 1_000
    sources: List[LogSourceSettings] = field(default_factory=list)


@dataclass
class LogsConfig:
    """Top-level configuration for log ingestion and analysis."""

    ingestion: LogIngestionSettings = field(default_factory=LogIngestionSettings)
    analyzer: PipelineAnalyzerConfig = field(default_factory=PipelineAnalyzerConfig)


class ConfigManager:
    """Manages configuration for LLM models and analyzers."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file or self._get_default_config_path()
        self._raw_config = self._load_raw_config()
        self.config = self._load_analyzer_config(self._raw_config)
        self.logs_config = self._load_logs_config(self._raw_config)
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        return str(Path.home() / ".ai-copilot" / "config.yaml")

    def _load_raw_config(self) -> Dict[str, Any]:
        """Load raw configuration data from disk."""
        if os.path.exists(self.config_file):
            try:
                import yaml

                with open(self.config_file, "r", encoding="utf-8") as handle:
                    data = yaml.safe_load(handle) or {}
                if not isinstance(data, dict):
                    raise ValueError("Configuration file must contain a mapping at the root level.")
                return data
            except Exception as exc:
                print(f"Warning: Could not load config file {self.config_file}: {exc}")
        return {}

    def _load_analyzer_config(self, raw: Dict[str, Any]) -> AnalyzerConfig:
        """Construct AnalyzerConfig from raw data or environment variables."""
        if raw:
            analyzer_data = raw.get("analyzer", raw)
            return self._dict_to_analyzer_config(analyzer_data)
        return self._load_analyzer_from_env()

    def _load_logs_config(self, raw: Dict[str, Any]) -> LogsConfig:
        if raw and "logs" in raw:
            return self._dict_to_logs_config(raw["logs"])
        return self._logs_from_env()

    def _load_analyzer_from_env(self) -> AnalyzerConfig:
        """Load analyzer configuration from environment variables."""
        return AnalyzerConfig(
            preferred_provider=os.getenv("AI_COPILOT_PROVIDER", "local"),
            fallback_provider=os.getenv("AI_COPILOT_FALLBACK_PROVIDER", "openai"),
            local_model=os.getenv("AI_COPILOT_LOCAL_MODEL", "qwen2:1.5b"),
            openai_model=os.getenv("AI_COPILOT_OPENAI_MODEL", "gpt-3.5-turbo"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            enable_hybrid=os.getenv("AI_COPILOT_ENABLE_HYBRID", "true").lower() == "true",
        )

    def _dict_to_analyzer_config(self, config_data: Dict[str, Any]) -> AnalyzerConfig:
        """Convert dictionary to AnalyzerConfig."""
        return AnalyzerConfig(
            preferred_provider=config_data.get("preferred_provider", "local"),
            fallback_provider=config_data.get("fallback_provider", "openai"),
            local_model=config_data.get("local_model", "qwen2:1.5b"),
            openai_model=config_data.get("openai_model", "gpt-3.5-turbo"),
            openai_api_key=config_data.get("openai_api_key"),
            ollama_host=config_data.get("ollama_host", "http://localhost:11434"),
            enable_hybrid=config_data.get("enable_hybrid", True),
        )

    def _dict_to_logs_config(self, logs_data: Dict[str, Any]) -> LogsConfig:
        ingestion_data = logs_data.get("ingestion", {})
        sources_data = ingestion_data.get("sources", [])
        sources = [self._parse_source_dict(item) for item in sources_data if isinstance(item, dict)]

        analyzer_data = logs_data.get("analyzer", {})
        analyzer = PipelineAnalyzerConfig(
            provider=analyzer_data.get("provider", "local"),
            prompt_template=analyzer_data.get("prompt_template", "log_summary_v1"),
            max_events=int(analyzer_data.get("max_events", 200)),
            anomaly_threshold=analyzer_data.get("anomaly_threshold", "medium"),
            include_raw_lines=bool(analyzer_data.get("include_raw_lines", False)),
        )

        ingestion = LogIngestionSettings(
            enabled=bool(ingestion_data.get("enabled", False)),
            poll_interval_seconds=int(ingestion_data.get("poll_interval_seconds", 120)),
            max_events_per_poll=int(ingestion_data.get("max_events_per_poll", 1_000)),
            sources=sources,
        )

        return LogsConfig(ingestion=ingestion, analyzer=analyzer)

    def _parse_source_dict(self, data: Dict[str, Any]) -> LogSourceSettings:
        include = data.get("include", [])
        if isinstance(include, str):
            include = [include]
        exclude = data.get("exclude", [])
        if isinstance(exclude, str):
            exclude = [exclude]
        return LogSourceSettings(
            path=str(data.get("path", "")),
            include=list(include),
            exclude=list(exclude),
            parser=data.get("parser", "basic_text"),
            batch_size=int(data.get("batch_size", 200)),
        )

    def _logs_from_env(self) -> LogsConfig:
        enabled = os.getenv("AI_COPILOT_LOG_ENABLED", "false").lower() == "true"
        poll_interval = int(os.getenv("AI_COPILOT_LOG_POLL_INTERVAL", "120"))
        max_events = int(os.getenv("AI_COPILOT_LOG_MAX_EVENTS", "1000"))
        sources_env = os.getenv("AI_COPILOT_LOG_SOURCES")
        sources: List[LogSourceSettings] = []

        if sources_env:
            sources = self._parse_sources_env(sources_env)

        analyzer = PipelineAnalyzerConfig()
        analyzer_env = os.getenv("AI_COPILOT_LOG_ANALYZER")
        if analyzer_env:
            try:
                overrides = json.loads(analyzer_env)
                analyzer = PipelineAnalyzerConfig(
                    provider=overrides.get("provider", analyzer.provider),
                    prompt_template=overrides.get("prompt_template", analyzer.prompt_template),
                    max_events=int(overrides.get("max_events", analyzer.max_events)),
                    anomaly_threshold=overrides.get("anomaly_threshold", analyzer.anomaly_threshold),
                    include_raw_lines=bool(overrides.get("include_raw_lines", analyzer.include_raw_lines)),
                )
            except Exception:
                print("Warning: Failed to parse AI_COPILOT_LOG_ANALYZER; using defaults.")

        ingestion = LogIngestionSettings(
            enabled=enabled,
            poll_interval_seconds=poll_interval,
            max_events_per_poll=max_events,
            sources=sources,
        )

        return LogsConfig(ingestion=ingestion, analyzer=analyzer)

    def _parse_sources_env(self, value: str) -> List[LogSourceSettings]:
        try:
            payload = json.loads(value)
            if isinstance(payload, list):
                return [self._parse_source_dict(item) for item in payload if isinstance(item, dict)]
        except json.JSONDecodeError:
            # Comma separated list of paths
            paths = [item.strip() for item in value.split(",") if item.strip()]
            return [LogSourceSettings(path=path) for path in paths]
        return []

    def save_config(self, config: AnalyzerConfig, log_config: Optional[LogsConfig] = None):
        """Save configuration to file."""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        try:
            import yaml

            payload = self._analyzer_to_dict(config)

            logs_payload = log_config or getattr(self, "logs_config", None)
            if logs_payload:
                payload["logs"] = self._logs_to_dict(logs_payload)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(payload, f, default_flow_style=False)
        except Exception as e:
            print(f"Warning: Could not save config file {self.config_file}: {e}")

    def _analyzer_to_dict(self, config: AnalyzerConfig) -> Dict[str, Any]:
        return {
            "preferred_provider": config.preferred_provider,
            "fallback_provider": config.fallback_provider,
            "local_model": config.local_model,
            "openai_model": config.openai_model,
            "openai_api_key": config.openai_api_key,
            "ollama_host": config.ollama_host,
            "enable_hybrid": config.enable_hybrid,
        }

    def _logs_to_dict(self, logs: LogsConfig) -> Dict[str, Any]:
        return {
            "ingestion": {
                "enabled": logs.ingestion.enabled,
                "poll_interval_seconds": logs.ingestion.poll_interval_seconds,
                "max_events_per_poll": logs.ingestion.max_events_per_poll,
                "sources": [
                    {
                        "path": source.path,
                        "include": list(source.include),
                        "exclude": list(source.exclude),
                        "parser": source.parser,
                        "batch_size": source.batch_size,
                    }
                    for source in logs.ingestion.sources
                ],
            },
            "analyzer": {
                "provider": logs.analyzer.provider,
                "prompt_template": logs.analyzer.prompt_template,
                "max_events": logs.analyzer.max_events,
                "anomaly_threshold": logs.analyzer.anomaly_threshold,
                "include_raw_lines": logs.analyzer.include_raw_lines,
            },
        }
    
    def get_model_config(self, provider: str = None) -> ModelConfig:
        """Get model configuration for a specific provider."""
        if provider is None:
            provider = self.config.preferred_provider
        
        if provider == "local":
            return ModelConfig(
                name="local_model",
                provider="local",
                model_id=self.config.local_model,
                host=self.config.ollama_host
            )
        elif provider == "openai":
            return ModelConfig(
                name="openai_model",
                provider="openai",
                model_id=self.config.openai_model,
                api_key=self.config.openai_api_key
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def get_available_models(self) -> Dict[str, list]:
        """Get list of available models for each provider."""
        models = {"local": [], "openai": []}
        
        # Check local models
        try:
            import ollama
            client = ollama.Client(host=self.config.ollama_host)
            models_list = client.list()
            models["local"] = [model.get('name', model.get('model', '')) for model in models_list.get('models', [])]
        except Exception:
            models["local"] = []
        
        # OpenAI models (static list)
        models["openai"] = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        
        return models
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate the current configuration."""
        validation = {
            "local_available": False,
            "openai_available": False,
            "config_valid": True
        }
        
        # Check local availability
        try:
            import ollama
            client = ollama.Client(host=self.config.ollama_host)
            models = client.list()
            if models.get('models'):
                validation["local_available"] = True
        except Exception:
            pass
        
        # Check OpenAI availability
        if self.config.openai_api_key:
            validation["openai_available"] = True
        
        # Overall validation
        if not validation["local_available"] and not validation["openai_available"]:
            validation["config_valid"] = False
        
        return validation

    def get_log_config(self) -> LogsConfig:
        """Return the configured log ingestion and analyzer settings."""
        return self.logs_config


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> AnalyzerConfig:
    """Get the current configuration."""
    return config_manager.config


def get_model_config(provider: str = None) -> ModelConfig:
    """Get model configuration for a specific provider."""
    return config_manager.get_model_config(provider)


def get_available_models() -> Dict[str, list]:
    """Get list of available models."""
    return config_manager.get_available_models()


def validate_config() -> Dict[str, bool]:
    """Validate the current configuration."""
    return config_manager.validate_config()


def get_log_config() -> LogsConfig:
    """Expose the configured log ingestion settings."""
    return config_manager.get_log_config()
