import yaml

from src.llm.config import ConfigManager


def test_logs_config_loaded_from_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    yaml.safe_dump(
        {
            "preferred_provider": "local",
            "logs": {
                "ingestion": {
                    "enabled": True,
                    "poll_interval_seconds": 30,
                    "max_events_per_poll": 250,
                    "sources": [
                        {
                            "path": "/var/log",
                            "include": ["*.log"],
                            "exclude": ["*debug*"],
                            "parser": "basic_text",
                            "batch_size": 100,
                        }
                    ],
                },
                "analyzer": {
                    "provider": "local",
                    "prompt_template": "log_summary_v1",
                    "max_events": 150,
                    "anomaly_threshold": "high",
                    "include_raw_lines": True,
                },
            },
        },
        config_file.open("w", encoding="utf-8"),
    )

    manager = ConfigManager(config_file=str(config_file))
    logs_config = manager.get_log_config()

    assert logs_config.ingestion.enabled is True
    assert logs_config.ingestion.poll_interval_seconds == 30
    assert logs_config.ingestion.sources[0].path == "/var/log"
    assert logs_config.analyzer.anomaly_threshold == "high"
    assert logs_config.analyzer.include_raw_lines is True


def test_logs_config_env_overrides(tmp_path, monkeypatch):
    config_file = tmp_path / "missing.yaml"
    monkeypatch.delenv("AI_COPILOT_LOG_SOURCES", raising=False)
    monkeypatch.setenv("AI_COPILOT_LOG_ENABLED", "true")
    monkeypatch.setenv("AI_COPILOT_LOG_POLL_INTERVAL", "45")
    monkeypatch.setenv("AI_COPILOT_LOG_MAX_EVENTS", "300")
    monkeypatch.setenv(
        "AI_COPILOT_LOG_SOURCES",
        "[{'path': '/var/log/auth.log', 'parser': 'basic_text'}]".replace("'", '"'),
    )

    manager = ConfigManager(config_file=str(config_file))
    logs_config = manager.get_log_config()

    assert logs_config.ingestion.enabled is True
    assert logs_config.ingestion.poll_interval_seconds == 45
    assert logs_config.ingestion.max_events_per_poll == 300
    assert logs_config.ingestion.sources[0].path == "/var/log/auth.log"

    monkeypatch.delenv("AI_COPILOT_LOG_ANALYZER", raising=False)
