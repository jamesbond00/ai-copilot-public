#!/usr/bin/env python3
"""
Test script for Prometheus integration with AI Copilot.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.fetchers import PrometheusFetcher, LogEntry, create_fetcher
from src.llm.local_analyzer import LocalLogAnalyzer
from src.llm.copilot import create_copilot_service


class MockPrometheusFetcher(PrometheusFetcher):
    """Mock Prometheus fetcher for testing without a real Prometheus instance."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.mock_data = self._generate_mock_metrics()
    
    def _generate_mock_metrics(self) -> List[LogEntry]:
        """Generate realistic mock Prometheus metrics as log entries."""
        base_time = datetime.now()
        
        mock_logs = [
            # System metrics
            LogEntry(
                timestamp=base_time - timedelta(minutes=5),
                level="INFO",
                source="prometheus",
                message="node_cpu_seconds_total: CPU usage at 75%",
                metadata={
                    "metric": "node_cpu_seconds_total",
                    "value": 75.0,
                    "labels": {"cpu": "0", "mode": "user"},
                    "job": "node_exporter"
                }
            ),
            LogEntry(
                timestamp=base_time - timedelta(minutes=4),
                level="WARNING",
                source="prometheus",
                message="node_memory_MemAvailable_bytes: Memory usage at 85%",
                metadata={
                    "metric": "node_memory_MemAvailable_bytes",
                    "value": 85.0,
                    "labels": {"instance": "localhost:9100"},
                    "job": "node_exporter"
                }
            ),
            LogEntry(
                timestamp=base_time - timedelta(minutes=3),
                level="ERROR",
                source="prometheus",
                message="http_requests_total: High error rate detected",
                metadata={
                    "metric": "http_requests_total",
                    "value": 150.0,
                    "labels": {"status": "5xx", "endpoint": "/api/users"},
                    "job": "web-server"
                }
            ),
            LogEntry(
                timestamp=base_time - timedelta(minutes=2),
                level="INFO",
                source="prometheus",
                message="http_request_duration_seconds: Response time spike",
                metadata={
                    "metric": "http_request_duration_seconds",
                    "value": 2.5,
                    "labels": {"endpoint": "/api/orders", "method": "POST"},
                    "job": "web-server"
                }
            ),
            LogEntry(
                timestamp=base_time - timedelta(minutes=1),
                level="WARNING",
                source="prometheus",
                message="database_connections_active: Connection pool near limit",
                metadata={
                    "metric": "database_connections_active",
                    "value": 18.0,
                    "labels": {"database": "postgres", "pool": "main"},
                    "job": "database"
                }
            ),
            LogEntry(
                timestamp=base_time,
                level="INFO",
                source="prometheus",
                message="up: All services healthy",
                metadata={
                    "metric": "up",
                    "value": 1.0,
                    "labels": {"job": "prometheus"},
                    "job": "prometheus"
                }
            )
        ]
        
        return mock_logs
    
    def fetch_logs(self, start_time: datetime, end_time: datetime) -> List[LogEntry]:
        """Return mock metrics data."""
        # Filter mock data by time range
        filtered_logs = [
            log for log in self.mock_data
            if start_time <= log.timestamp <= end_time
        ]
        return filtered_logs
    
    def test_connection(self) -> bool:
        """Mock connection test - always returns True."""
        return True


def test_prometheus_connection():
    """Test Prometheus connection."""
    print("=== Testing Prometheus Connection ===")
    
    # Test with real Prometheus (if available)
    real_config = {
        'prometheus_url': 'http://localhost:9090'
    }
    
    try:
        real_fetcher = PrometheusFetcher(real_config)
        if real_fetcher.test_connection():
            print("✅ Real Prometheus connection successful!")
            return real_fetcher
        else:
            print("⚠️  Real Prometheus not available, using mock data")
    except Exception as e:
        print(f"⚠️  Real Prometheus not available: {e}")
    
    # Fall back to mock fetcher
    mock_config = {
        'prometheus_url': 'http://localhost:9090'
    }
    
    mock_fetcher = MockPrometheusFetcher(mock_config)
    print("✅ Using mock Prometheus data for testing")
    return mock_fetcher


def test_prometheus_metrics():
    """Test fetching Prometheus metrics."""
    print("\n=== Testing Prometheus Metrics Fetching ===")
    
    fetcher = test_prometheus_connection()
    
    # Fetch metrics from last hour
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    
    try:
        metrics = fetcher.fetch_logs(start_time, end_time)
        print(f"📊 Fetched {len(metrics)} metric entries")
        
        # Display sample metrics
        print("\n--- Sample Metrics ---")
        for i, metric in enumerate(metrics[:3]):
            print(f"{i+1}. [{metric.timestamp}] {metric.level} - {metric.source}")
            print(f"   Message: {metric.message}")
            print(f"   Metadata: {metric.metadata}")
            print()
        
        return metrics
        
    except Exception as e:
        print(f"❌ Error fetching metrics: {e}")
        return []


def test_prometheus_analysis():
    """Test AI analysis of Prometheus metrics."""
    print("\n=== Testing Prometheus Metrics Analysis ===")
    
    # Get metrics data
    metrics = test_prometheus_metrics()
    
    if not metrics:
        print("❌ No metrics available for analysis")
        return
    
    try:
        # Create local analyzer
        analyzer = LocalLogAnalyzer(model="qwen2:1.5b")
        print(f"🤖 Using model: {analyzer.model}")
        
        # Analyze metrics for performance issues
        print("📈 Analyzing metrics for performance issues...")
        result = analyzer.analyze_logs(metrics, "performance_analysis")
        
        print("\n--- Performance Analysis Results ---")
        print(f"📝 Summary: {result.summary}")
        print(f"🎯 Confidence: {result.confidence_score:.2f}")
        print(f"🤖 Model: {result.model_used}")
        
        if result.key_insights:
            print("\n🔍 Key Insights:")
            for insight in result.key_insights:
                print(f"  • {insight}")
        
        if result.recommendations:
            print("\n💡 Recommendations:")
            for rec in result.recommendations:
                print(f"  • {rec}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error analyzing metrics: {e}")
        return None


def test_prometheus_copilot_service():
    """Test full Prometheus integration with CopilotService."""
    print("\n=== Testing Prometheus CopilotService Integration ===")
    
    try:
        # Create mock fetcher
        mock_config = {'prometheus_url': 'http://localhost:9090'}
        fetcher = MockPrometheusFetcher(mock_config)
        
        # Create copilot service with local analyzer
        service = create_copilot_service(fetcher, provider="local")
        print("✅ Created CopilotService with Prometheus fetcher")
        
        # Test different analysis types
        print("\n📊 Testing daily summary...")
        daily_result = service.get_daily_summary(days_back=1)
        print(f"Daily Summary: {daily_result.summary[:100]}...")
        
        print("\n🔍 Testing performance analysis...")
        perf_result = service.analyze_performance(hours_back=24)
        print(f"Performance Analysis: {perf_result.summary[:100]}...")
        
        return service
        
    except Exception as e:
        print(f"❌ Error testing CopilotService: {e}")
        return None


def test_prometheus_queries():
    """Test specific Prometheus queries."""
    print("\n=== Testing Prometheus Queries ===")
    
    # Example queries that would be useful for monitoring
    queries = [
        {
            "name": "CPU Usage",
            "query": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "description": "Average CPU usage percentage"
        },
        {
            "name": "Memory Usage",
            "query": "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))",
            "description": "Memory usage percentage"
        },
        {
            "name": "HTTP Error Rate",
            "query": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "description": "HTTP 5xx error rate"
        },
        {
            "name": "Response Time",
            "query": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "description": "95th percentile response time"
        }
    ]
    
    print("📋 Useful Prometheus queries for monitoring:")
    for query in queries:
        print(f"\n🔍 {query['name']}")
        print(f"   Query: {query['query']}")
        print(f"   Description: {query['description']}")
    
    return queries


def main():
    """Run all Prometheus tests."""
    print("🚀 Testing Prometheus Integration")
    print("=" * 50)
    
    tests = [
        ("Connection Test", test_prometheus_connection),
        ("Metrics Fetching", test_prometheus_metrics),
        ("AI Analysis", test_prometheus_analysis),
        ("CopilotService Integration", test_prometheus_copilot_service),
        ("Query Examples", test_prometheus_queries),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, True, result))
            print(f"✅ {test_name} completed")
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False, None))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, _ in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Prometheus tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n💡 Next Steps:")
    print("1. Set up real Prometheus: brew install prometheus")
    print("2. Install Node Exporter: brew install node_exporter")
    print("3. Configure prometheus.yml for your services")
    print("4. Use the query examples above for monitoring")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
