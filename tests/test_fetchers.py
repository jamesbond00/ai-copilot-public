"""
Tests for data fetchers.
"""

import pytest
from datetime import datetime, timedelta
from src.data.fetchers import create_fetcher, LogEntry


class TestFetchers:
    """Test cases for data fetchers."""
    
    def test_create_fetcher_elk(self):
        """Test ELK fetcher creation."""
        config = {"elasticsearch_url": "http://localhost:9200"}
        fetcher = create_fetcher("elk", config)
        assert fetcher.__class__.__name__ == "ELKFetcher"
    
    def test_create_fetcher_prometheus(self):
        """Test Prometheus fetcher creation."""
        config = {"prometheus_url": "http://localhost:9090"}
        fetcher = create_fetcher("prometheus", config)
        assert fetcher.__class__.__name__ == "PrometheusFetcher"
    
    def test_create_fetcher_splunk(self):
        """Test Splunk fetcher creation."""
        config = {"splunk_url": "https://localhost:8089", "splunk_token": "test_token"}
        fetcher = create_fetcher("splunk", config)
        assert fetcher.__class__.__name__ == "SplunkFetcher"
    
    def test_create_fetcher_invalid(self):
        """Test invalid fetcher type."""
        with pytest.raises(ValueError):
            create_fetcher("invalid", {})
    
    def test_log_entry_creation(self):
        """Test LogEntry creation."""
        timestamp = datetime.now()
        log_entry = LogEntry(
            timestamp=timestamp,
            level="INFO",
            message="Test message",
            source="test_source",
            metadata={"key": "value"}
        )
        
        assert log_entry.timestamp == timestamp
        assert log_entry.level == "INFO"
        assert log_entry.message == "Test message"
        assert log_entry.source == "test_source"
        assert log_entry.metadata == {"key": "value"}
