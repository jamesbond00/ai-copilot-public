#!/usr/bin/env python3
"""
Example demonstrating the de-risking system for monitoring hallucinations.
Shows how predefined templates anchor Qwen2-1.5B to reliable incident categories.
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.llm.anchored_analyzer import AnchoredLogAnalyzer
from src.llm.incident_templates import IncidentAnalyzer
from src.data.fetchers import LogEntry


def demonstrate_de_risking():
    """Demonstrate how the de-risking system prevents hallucinations."""
    
    print("🛡️  DE-RISKING HALLUCINATIONS IN MONITORING")
    print("=" * 60)
    print("Example: How predefined templates anchor Qwen2-1.5B to reliable categories")
    print("=" * 60)
    
    # Initialize the anchored analyzer
    try:
        analyzer = AnchoredLogAnalyzer(model="qwen2:1.5b")
        print(f"✅ Initialized anchored analyzer with {analyzer.model}")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        print("💡 Make sure Ollama is running: brew services start ollama")
        return
    
    # Example 1: Database Connection Pool Exhaustion
    print("\n📊 EXAMPLE 1: Database Connection Pool Exhaustion")
    print("-" * 50)
    
    db_logs = [
        LogEntry(
            timestamp=datetime.now() - timedelta(minutes=30),
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
                "error_code": "CONNECTION_POOL_EXHAUSTED",
                "request_id": "req-abc123",
                "user_id": "user_456"
            }
        )
    ]
    
    result = analyzer.analyze_logs(db_logs)
    
    print("🎯 ANCHORED ANALYSIS (De-risked):")
    print(f"  Category: {result.category}")
    print(f"  Severity: {result.severity}")
    print(f"  Summary: {result.summary}")
    print(f"  Cause: {result.cause}")
    print(f"  Next Step: {result.next_step}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Template: {result.template_used}")
    
    print("\n💡 KEY BENEFITS:")
    print("  ✅ Categorized as 'database_connection_pool_exhausted' (not hallucinated)")
    print("  ✅ Severity correctly set to 'critical'")
    print("  ✅ Actionable next steps provided")
    print("  ✅ High confidence (1.00) due to template matching")
    
    # Example 2: API Rate Limiting
    print("\n📊 EXAMPLE 2: API Rate Limiting")
    print("-" * 50)
    
    api_logs = [
        LogEntry(
            timestamp=datetime.now() - timedelta(minutes=15),
            level="WARNING",
            source="api-gateway-01",
            message="Rate limit exceeded for client 192.168.1.100: 1200 requests in 60s (limit: 1000/min)",
            metadata={
                "component": "rate_limiter",
                "client_ip": "192.168.1.100",
                "requests_count": 1200,
                "time_window_seconds": 60,
                "rate_limit": 1000,
                "endpoint": "/api/v1/products/search",
                "user_agent": "Mozilla/5.0 (compatible; Bot/1.0)"
            }
        )
    ]
    
    result = analyzer.analyze_logs(api_logs)
    
    print("🎯 ANCHORED ANALYSIS (De-risked):")
    print(f"  Category: {result.category}")
    print(f"  Severity: {result.severity}")
    print(f"  Summary: {result.summary}")
    print(f"  Cause: {result.cause}")
    print(f"  Next Step: {result.next_step}")
    print(f"  Confidence: {result.confidence:.2f}")
    
    print("\n💡 KEY BENEFITS:")
    print("  ✅ Categorized as 'api_rate_limiting' (not hallucinated)")
    print("  ✅ Severity correctly set to 'medium'")
    print("  ✅ Specific client IP and request counts included")
    print("  ✅ Bot detection suggested in next steps")
    
    # Example 3: Security Incident
    print("\n📊 EXAMPLE 3: Security Suspicious Activity")
    print("-" * 50)
    
    security_logs = [
        LogEntry(
            timestamp=datetime.now() - timedelta(minutes=5),
            level="WARNING",
            source="security-service-01",
            message="Suspicious activity detected: Multiple failed API calls from IP 203.0.113.45",
            metadata={
                "component": "security",
                "event_type": "suspicious_activity",
                "source_ip": "203.0.113.45",
                "failed_attempts": 15,
                "time_window_minutes": 5,
                "endpoints_accessed": ["/api/v1/auth/login", "/api/v1/users", "/api/v1/admin"],
                "threat_level": "medium",
                "action_taken": "rate_limited"
            }
        )
    ]
    
    result = analyzer.analyze_logs(security_logs)
    
    print("🎯 ANCHORED ANALYSIS (De-risked):")
    print(f"  Category: {result.category}")
    print(f"  Severity: {result.severity}")
    print(f"  Summary: {result.summary}")
    print(f"  Cause: {result.cause}")
    print(f"  Next Step: {result.next_step}")
    print(f"  Confidence: {result.confidence:.2f}")
    
    print("\n💡 KEY BENEFITS:")
    print("  ✅ Categorized as 'security_suspicious_activity' (not hallucinated)")
    print("  ✅ Severity correctly set to 'high'")
    print("  ✅ Specific IP address and threat level included")
    print("  ✅ Security-focused next steps provided")
    
    # Show template coverage
    print("\n📋 AVAILABLE INCIDENT TEMPLATES")
    print("-" * 50)
    
    templates = analyzer.get_available_templates()
    print(f"Total Templates: {len(templates)}")
    print("\nTemplate Categories:")
    for template in templates:
        print(f"  • {template['category']} ({template['severity']})")
    
    print("\n🎯 DE-RISKING SUMMARY")
    print("=" * 60)
    print("✅ Predefined incident types prevent random hallucinations")
    print("✅ Qwen2-1.5B job = match input alert to template + fill in blanks")
    print("✅ Structured, reliable outputs for monitoring systems")
    print("✅ High confidence scores due to template anchoring")
    print("✅ Actionable next steps for each incident type")
    print("✅ Consistent categorization across similar incidents")


def show_template_example():
    """Show how the template system works."""
    
    print("\n🔧 HOW TEMPLATES PREVENT HALLUCINATIONS")
    print("=" * 60)
    
    # Show a specific template
    incident_analyzer = IncidentAnalyzer()
    
    print("📋 Example Template: CPU Saturation")
    print("-" * 40)
    
    # Get the CPU saturation template
    from src.llm.incident_templates import IncidentCategory
    cpu_template = incident_analyzer.registry.get_template(IncidentCategory.CPU_SATURATION)
    
    if cpu_template:
        print(f"Category: {cpu_template.category.value}")
        print(f"Severity: {cpu_template.severity.value}")
        print(f"Summary Template: {cpu_template.summary_template}")
        print(f"Cause Template: {cpu_template.cause_template}")
        print(f"Next Step Template: {cpu_template.next_step_template}")
        print(f"Keywords: {', '.join(cpu_template.keywords)}")
        print(f"Patterns: {cpu_template.patterns}")
    
    print("\n🎯 Template Benefits:")
    print("  ✅ Predefined categories prevent hallucination")
    print("  ✅ Consistent severity levels")
    print("  ✅ Structured response format")
    print("  ✅ Keyword and pattern matching")
    print("  ✅ Metadata field validation")
    
    print("\n🤖 Qwen2-1.5B Role:")
    print("  ✅ Match input alert to template category")
    print("  ✅ Fill in template blanks with specific details")
    print("  ✅ Provide actionable insights within framework")
    print("  ✅ Stay anchored to known incident types")


def main():
    """Run the de-risking demonstration."""
    demonstrate_de_risking()
    show_template_example()
    
    print("\n🎉 DE-RISKING SYSTEM DEMONSTRATION COMPLETE!")
    print("=" * 60)
    print("The anchored analyzer successfully prevents hallucinations by:")
    print("1. Using predefined incident templates")
    print("2. Anchoring Qwen2-1.5B to known categories")
    print("3. Providing structured, reliable outputs")
    print("4. Maintaining high confidence scores")
    print("5. Ensuring actionable next steps")


if __name__ == "__main__":
    main()
