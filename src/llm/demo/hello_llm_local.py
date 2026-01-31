"""
Simple example of using local LLM for log analysis.
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.llm.local_analyzer import LocalLogAnalyzer
from src.data.fetchers import LogEntry


def main():
    """Demonstrate local LLM log analysis."""
    print("🤖 Local LLM Log Analysis Demo")
    print("=" * 40)
    
    # Create realistic production logs
    base_time = datetime.now()
    logs = [
        # Database issues
        LogEntry(
            timestamp=base_time - timedelta(hours=3, minutes=15),
            level="ERROR",
            source="web-server-01",
            message="Database connection pool exhausted: 50/50 connections in use, queue depth: 127",
            metadata={
                "component": "database",
                "pool_size": 50,
                "active_connections": 50,
                "queue_depth": 127,
                "host": "db-primary-01.prod.internal",
                "port": 5432,
                "database": "user_service",
                "error_code": "CONNECTION_POOL_EXHAUSTED",
                "request_id": "req-7f8a9b2c-3d4e-5f6g-7h8i-9j0k1l2m3n4o",
                "user_id": "user_12345",
                "endpoint": "/api/v1/users/profile",
                "method": "GET",
                "response_time_ms": 30000,
                "trace_id": "trace-abc123def456"
            }
        ),
        
        # Cache service memory warning
        LogEntry(
            timestamp=base_time - timedelta(hours=2, minutes=45),
            level="WARNING",
            source="cache-service-02",
            message="Redis memory usage critical: 2.1GB/2.5GB (84%) - evicting LRU keys",
            metadata={
                "component": "redis",
                "memory_used_gb": 2.1,
                "memory_total_gb": 2.5,
                "memory_usage_percent": 84,
                "eviction_policy": "allkeys-lru",
                "keys_evicted": 1250,
                "hit_rate": 0.67,
                "miss_rate": 0.33,
                "operations_per_sec": 15420,
                "connected_clients": 45,
                "host": "redis-cluster-02.prod.internal",
                "port": 6379,
                "instance_id": "redis-02"
            }
        ),
        
        # API rate limiting
        LogEntry(
            timestamp=base_time - timedelta(hours=2, minutes=30),
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
                "user_agent": "Mozilla/5.0 (compatible; Bot/1.0)",
                "api_key": "ak_*****789",
                "throttle_duration_ms": 5000,
                "request_id": "req-8g9h0i1j-2k3l-4m5n-6o7p-8q9r0s1t2u3v"
            }
        ),
        
        # Authentication failure
        LogEntry(
            timestamp=base_time - timedelta(hours=2, minutes=15),
            level="WARNING",
            source="auth-service-01",
            message="Failed login attempt: Invalid credentials for user john.doe@company.com",
            metadata={
                "component": "authentication",
                "event_type": "login_failed",
                "username": "john.doe@company.com",
                "failure_reason": "invalid_credentials",
                "client_ip": "10.0.1.45",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "attempt_count": 3,
                "lockout_remaining": 2,
                "session_id": None,
                "request_id": "req-9h0i1j2k-3l4m-5n6o-7p8q-9r0s1t2u3v4w",
                "endpoint": "/api/v1/auth/login",
                "method": "POST"
            }
        ),
        
        # Successful authentication
        LogEntry(
            timestamp=base_time - timedelta(hours=2, minutes=10),
            level="INFO",
            source="auth-service-01",
            message="User authentication successful: jane.smith@company.com logged in via OAuth2",
            metadata={
                "component": "authentication",
                "event_type": "login_success",
                "username": "jane.smith@company.com",
                "user_id": "usr_67890",
                "auth_method": "oauth2",
                "provider": "google",
                "client_ip": "10.0.1.67",
                "session_id": "sess_abc123def456ghi789",
                "jwt_token_id": "jwt_xyz789abc123def456",
                "token_expires_at": (base_time + timedelta(hours=8)).isoformat(),
                "request_id": "req-0i1j2k3l-4m5n-6o7p-8q9r-0s1t2u3v4w5x",
                "response_time_ms": 245
            }
        ),
        
        # Database query performance issue
        LogEntry(
            timestamp=base_time - timedelta(hours=1, minutes=50),
            level="WARNING",
            source="web-server-02",
            message="Slow query detected: SELECT * FROM orders WHERE user_id = ? took 2.3s (threshold: 1s)",
            metadata={
                "component": "database",
                "query_type": "slow_query",
                "query": "SELECT * FROM orders WHERE user_id = ?",
                "execution_time_ms": 2300,
                "threshold_ms": 1000,
                "database": "order_service",
                "table": "orders",
                "rows_examined": 150000,
                "rows_returned": 25,
                "index_used": "idx_user_id",
                "host": "db-replica-02.prod.internal",
                "connection_id": "conn_456789",
                "request_id": "req-1j2k3l4m-5n6o-7p8q-9r0s-1t2u3v4w5x6y"
            }
        ),
        
        # Microservice communication error
        LogEntry(
            timestamp=base_time - timedelta(hours=1, minutes=35),
            level="ERROR",
            source="payment-service-01",
            message="Failed to communicate with external payment gateway: Connection timeout after 10s",
            metadata={
                "component": "payment_gateway",
                "service": "stripe",
                "operation": "charge_card",
                "error_type": "connection_timeout",
                "timeout_seconds": 10,
                "retry_count": 3,
                "max_retries": 3,
                "endpoint": "https://api.stripe.com/v1/charges",
                "request_id": "req-2k3l4m5n-6o7p-8q9r-0s1t-2u3v4w5x6y7z",
                "order_id": "ord_98765",
                "amount": 99.99,
                "currency": "USD",
                "customer_id": "cus_12345"
            }
        ),
        
        # Load balancer health check failure
        LogEntry(
            timestamp=base_time - timedelta(hours=1, minutes=20),
            level="ERROR",
            source="load-balancer-01",
            message="Health check failed for backend server web-server-03: HTTP 503 Service Unavailable",
            metadata={
                "component": "load_balancer",
                "backend_server": "web-server-03",
                "backend_ip": "10.0.3.15",
                "backend_port": 8080,
                "health_check_url": "/health",
                "response_code": 503,
                "response_time_ms": 5000,
                "consecutive_failures": 3,
                "max_failures": 3,
                "server_status": "unhealthy",
                "pool_name": "web-servers",
                "algorithm": "round_robin"
            }
        ),
        
        # File system disk space warning
        LogEntry(
            timestamp=base_time - timedelta(hours=1, minutes=5),
            level="WARNING",
            source="file-service-01",
            message="Disk space low: /var/logs 89% full (8.9GB/10GB used)",
            metadata={
                "component": "filesystem",
                "mount_point": "/var/logs",
                "disk_usage_percent": 89,
                "used_gb": 8.9,
                "total_gb": 10.0,
                "available_gb": 1.1,
                "filesystem_type": "ext4",
                "device": "/dev/sda1",
                "inodes_used": 125000,
                "inodes_total": 131072,
                "host": "file-server-01.prod.internal"
            }
        ),
        
        # Successful database recovery
        LogEntry(
            timestamp=base_time - timedelta(minutes=45),
            level="INFO",
            source="web-server-01",
            message="Database connection pool recovered: 5/50 connections active, queue depth: 0",
            metadata={
                "component": "database",
                "pool_size": 50,
                "active_connections": 5,
                "queue_depth": 0,
                "host": "db-primary-01.prod.internal",
                "port": 5432,
                "database": "user_service",
                "recovery_time_ms": 15000,
                "request_id": "req-3l4m5n6o-7p8q-9r0s-1t2u-3v4w5x6y7z8a",
                "status": "healthy"
            }
        ),
        
        # API endpoint performance
        LogEntry(
            timestamp=base_time - timedelta(minutes=30),
            level="INFO",
            source="api-gateway-01",
            message="API endpoint performance: /api/v1/products/search avg response time 145ms (95th percentile: 320ms)",
            metadata={
                "component": "api_gateway",
                "endpoint": "/api/v1/products/search",
                "method": "GET",
                "avg_response_time_ms": 145,
                "p95_response_time_ms": 320,
                "p99_response_time_ms": 850,
                "requests_per_minute": 1250,
                "success_rate": 0.998,
                "error_rate": 0.002,
                "cache_hit_rate": 0.73,
                "request_id": "req-4m5n6o7p-8q9r-0s1t-2u3v-4w5x6y7z8a9b"
            }
        ),
        
        # Security event
        LogEntry(
            timestamp=base_time - timedelta(minutes=15),
            level="WARNING",
            source="security-service-01",
            message="Suspicious activity detected: Multiple failed API calls from IP 203.0.113.45",
            metadata={
                "component": "security",
                "event_type": "suspicious_activity",
                "source_ip": "203.0.113.45",
                "country": "Unknown",
                "failed_attempts": 15,
                "time_window_minutes": 5,
                "endpoints_accessed": ["/api/v1/auth/login", "/api/v1/users", "/api/v1/admin"],
                "user_agents": ["curl/7.68.0", "python-requests/2.25.1"],
                "threat_level": "medium",
                "action_taken": "rate_limited",
                "block_duration_minutes": 30
            }
        ),
        
        # Background job completion
        LogEntry(
            timestamp=base_time - timedelta(minutes=5),
            level="INFO",
            source="worker-service-01",
            message="Background job completed: email_notification_batch processed 1,250 emails in 45s",
            metadata={
                "component": "background_jobs",
                "job_type": "email_notification_batch",
                "job_id": "job_abc123def456",
                "queue_name": "email_queue",
                "processed_count": 1250,
                "failed_count": 3,
                "success_count": 1247,
                "execution_time_seconds": 45,
                "worker_id": "worker-01",
                "memory_peak_mb": 256,
                "cpu_usage_percent": 23.5
            }
        )
    ]
    
    try:
        # Initialize local analyzer
        analyzer = LocalLogAnalyzer(model="qwen2:1.5b")
        print(f"✅ Using model: {analyzer.model}")
        
        # Analyze logs
        print(f"📊 Analyzing {len(logs)} log entries...")
        result = analyzer.analyze_logs(logs, "daily_summary")
        
        # Display results
        print("\n=== Analysis Results ===")
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
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Ollama is running: brew services start ollama")
        print("2. Check if model is installed: ollama list")
        print("3. Install model if needed: ollama pull qwen2:1.5b")


if __name__ == "__main__":
    main()
