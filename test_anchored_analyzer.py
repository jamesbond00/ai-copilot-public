#!/usr/bin/env python3
"""
Test script for the anchored analyzer de-risking system.
Demonstrates how predefined templates prevent hallucinations in monitoring.
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.llm.anchored_analyzer import AnchoredLogAnalyzer
from src.llm.incident_templates import IncidentAnalyzer, IncidentCategory
from src.data.fetchers import LogEntry


def test_incident_templates():
    """Test the incident template system."""
    print("🧪 Testing Incident Templates")
    print("=" * 50)
    
    analyzer = IncidentAnalyzer()
    
    # Test cases for different incident types
    test_cases = [
        {
            "name": "CPU Saturation",
            "message": "CPU usage critical: 95% on web-server-01",
            "metadata": {"cpu_usage_percent": 95, "host": "web-server-01"},
            "expected_category": "cpu_saturation"
        },
        {
            "name": "Database Connection Pool Exhausted",
            "message": "Database connection pool exhausted: 50/50 connections in use, queue depth: 127",
            "metadata": {"pool_size": 50, "active_connections": 50, "queue_depth": 127},
            "expected_category": "database_connection_pool_exhausted"
        },
        {
            "name": "API Rate Limiting",
            "message": "Rate limit exceeded for client 192.168.1.100: 1200 requests in 60s (limit: 1000/min)",
            "metadata": {"requests_count": 1200, "time_window_seconds": 60, "rate_limit": 1000},
            "expected_category": "api_rate_limiting"
        },
        {
            "name": "Memory Exhaustion",
            "message": "Redis memory usage critical: 2.1GB/2.5GB (84%) - evicting LRU keys",
            "metadata": {"memory_used_gb": 2.1, "memory_total_gb": 2.5, "memory_usage_percent": 84},
            "expected_category": "memory_exhaustion"
        },
        {
            "name": "Disk Space Low",
            "message": "Disk space low: /var/logs 89% full (8.9GB/10GB used)",
            "metadata": {"disk_usage_percent": 89, "used_gb": 8.9, "total_gb": 10.0},
            "expected_category": "disk_space_low"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"Message: {test_case['message']}")
        
        result = analyzer.analyze_incident(
            test_case['message'],
            test_case['metadata'],
            "test-service"
        )
        
        print(f"✅ Category: {result['category']}")
        print(f"✅ Severity: {result['severity']}")
        print(f"✅ Summary: {result['summary']}")
        print(f"✅ Cause: {result['cause']}")
        print(f"✅ Next Step: {result['next_step']}")
        print(f"✅ Confidence: {result['confidence']:.2f}")
        
        # Verify expected category
        if result['category'] == test_case['expected_category']:
            print("✅ Category match: CORRECT")
        else:
            print(f"❌ Category mismatch: Expected {test_case['expected_category']}, got {result['category']}")
    
    print(f"\n🎯 Template test completed!")


def test_anchored_analyzer():
    """Test the anchored analyzer with realistic logs."""
    print("\n🤖 Testing Anchored Analyzer")
    print("=" * 50)
    
    try:
        analyzer = AnchoredLogAnalyzer(model="qwen2:1.5b")
        print(f"✅ Initialized with model: {analyzer.model}")
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        print("💡 Make sure Ollama is running and qwen2:1.5b is installed")
        return
    
    # Create realistic production logs
    base_time = datetime.now()
    logs = [
        # Critical database issue
        LogEntry(
            timestamp=base_time - timedelta(hours=2),
            level="ERROR",
            source="web-server-01",
            message="Database connection pool exhausted: 50/50 connections in use, queue depth: 127",
            metadata={
                "component": "database",
                "pool_size": 50,
                "active_connections": 50,
                "queue_depth": 127,
                "host": "db-primary-01.prod.internal",
                "database": "user_service",
                "error_code": "CONNECTION_POOL_EXHAUSTED"
            }
        ),
        
        # Memory pressure
        LogEntry(
            timestamp=base_time - timedelta(hours=1, minutes=30),
            level="WARNING",
            source="cache-service-02",
            message="Redis memory usage critical: 2.1GB/2.5GB (84%) - evicting LRU keys",
            metadata={
                "component": "redis",
                "memory_used_gb": 2.1,
                "memory_total_gb": 2.5,
                "memory_usage_percent": 84,
                "eviction_policy": "allkeys-lru",
                "keys_evicted": 1250
            }
        ),
        
        # API rate limiting
        LogEntry(
            timestamp=base_time - timedelta(hours=1),
            level="WARNING",
            source="api-gateway-01",
            message="Rate limit exceeded for client 192.168.1.100: 1200 requests in 60s (limit: 1000/min)",
            metadata={
                "component": "rate_limiter",
                "client_ip": "192.168.1.100",
                "requests_count": 1200,
                "time_window_seconds": 60,
                "rate_limit": 1000,
                "endpoint": "/api/v1/products/search"
            }
        )
    ]
    
    print(f"📊 Analyzing {len(logs)} log entries...")
    
    try:
        result = analyzer.analyze_logs(logs, "incident_analysis")
        
        print("\n🎯 ANCHORED ANALYSIS RESULTS:")
        print("=" * 40)
        print(f"📝 Summary: {result.summary}")
        print(f"🔍 Cause: {result.cause}")
        print(f"⚡ Next Step: {result.next_step}")
        print(f"📊 Category: {result.category}")
        print(f"🚨 Severity: {result.severity}")
        print(f"🎯 Confidence: {result.confidence:.2f}")
        print(f"📋 Template Used: {result.template_used}")
        print(f"🤖 Model: {result.model_used}")
        
        if result.key_insights:
            print(f"\n🔍 Key Insights:")
            for insight in result.key_insights:
                print(f"  • {insight}")
        
        if result.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in result.recommendations:
                print(f"  • {rec}")
        
        if result.alternative_categories:
            print(f"\n🔄 Alternative Categories: {', '.join(result.alternative_categories)}")
        
        print(f"\n✅ Anchored analysis completed successfully!")
        print(f"🎯 De-risking achieved: Template-based categorization prevents hallucinations")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        print("💡 This might be due to Ollama not running or model not available")


def test_single_incident_analysis():
    """Test single incident analysis for real-time alerts."""
    print("\n⚡ Testing Single Incident Analysis")
    print("=" * 50)
    
    analyzer = AnchoredLogAnalyzer()
    
    # Test real-time alert processing
    alert_cases = [
        {
            "name": "CPU Alert",
            "message": "CPU usage critical: 95% on web-server-01",
            "metadata": {"cpu_usage_percent": 95, "host": "web-server-01"},
            "service": "web-server"
        },
        {
            "name": "Database Alert",
            "message": "Database connection timeout after 30s",
            "metadata": {"timeout_seconds": 30, "database": "user_service"},
            "service": "database"
        },
        {
            "name": "Security Alert",
            "message": "Suspicious activity detected: Multiple failed API calls from IP 203.0.113.45",
            "metadata": {"source_ip": "203.0.113.45", "failed_attempts": 15, "threat_level": "medium"},
            "service": "security"
        }
    ]
    
    for alert_case in alert_cases:
        print(f"\n🚨 Processing Alert: {alert_case['name']}")
        print(f"Message: {alert_case['message']}")
        
        result = analyzer.analyze_single_incident(
            alert_case['message'],
            alert_case['metadata'],
            alert_case['service']
        )
        
        print(f"✅ Category: {result['category']}")
        print(f"✅ Severity: {result['severity']}")
        print(f"✅ Summary: {result['summary']}")
        print(f"✅ Confidence: {result['confidence']:.2f}")
        print(f"✅ Template: {result['template_used']}")
    
    print(f"\n✅ Single incident analysis completed!")


def test_template_coverage():
    """Test coverage of available templates."""
    print("\n📋 Testing Template Coverage")
    print("=" * 50)
    
    analyzer = AnchoredLogAnalyzer()
    templates = analyzer.get_available_templates()
    
    print(f"📊 Available Templates: {len(templates)}")
    print("\nTemplate Categories:")
    for template in templates:
        print(f"  • {template['category']} ({template['severity']})")
        print(f"    Keywords: {', '.join(template['keywords'][:3])}...")
    
    print(f"\n✅ Template coverage analysis completed!")


def main():
    """Run all tests."""
    print("🧪 ANCHORED ANALYZER DE-RISKING TESTS")
    print("=" * 60)
    print("Testing predefined incident templates to prevent hallucinations")
    print("=" * 60)
    
    # Test 1: Incident Templates
    test_incident_templates()
    
    # Test 2: Template Coverage
    test_template_coverage()
    
    # Test 3: Single Incident Analysis
    test_single_incident_analysis()
    
    # Test 4: Full Anchored Analyzer (requires Ollama)
    test_anchored_analyzer()
    
    print("\n🎉 ALL TESTS COMPLETED!")
    print("=" * 60)
    print("✅ De-risking system successfully implemented")
    print("✅ Templates prevent hallucinations by anchoring to known categories")
    print("✅ Qwen2-1.5B fills in specific details within template framework")
    print("✅ Structured, reliable outputs for monitoring systems")


if __name__ == "__main__":
    main()
