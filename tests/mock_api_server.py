"""
Mock API server for testing the dashboard without backend dependencies.
"""

from fastapi import FastAPI
from datetime import datetime, timedelta
import uvicorn
from typing import Dict, Any
import random

app = FastAPI(title="Mock AI Copilot API", version="0.1.0")

# Sample data for testing
SAMPLE_INSIGHTS = [
    "System performance is within normal parameters",
    "Error rates have decreased by 15% compared to last week",
    "Memory usage is trending upward and should be monitored",
    "Database connection pool is operating efficiently",
    "API response times are consistent across all endpoints"
]

SAMPLE_RECOMMENDATIONS = [
    "Consider implementing additional monitoring for memory usage",
    "Schedule maintenance window for database optimization",
    "Review error handling in user authentication module",
    "Implement caching for frequently accessed data",
    "Consider scaling horizontal infrastructure components"
]

SAMPLE_ERRORS = [
    "Database connection timeout occurred 3 times in the last hour",
    "Authentication service returned 401 errors for 2% of requests",
    "Memory leak detected in background processing service",
    "API rate limiting triggered for external service calls"
]

SAMPLE_PERFORMANCE_ISSUES = [
    "Response time increased by 200ms for search endpoints",
    "Database query performance degraded for complex reports",
    "Memory usage spiked during peak hours",
    "Cache hit rate dropped below 80% threshold"
]


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Mock AI Copilot API is running", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint with random status for testing."""
    statuses = ["healthy", "degraded", "unhealthy"]
    status = random.choice(statuses)
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "monitoring_system_connected": status != "unhealthy"
    }


@app.get("/summary/daily")
async def get_daily_summary(days_back: int = 1):
    """Get daily summary with realistic test data."""
    log_count = random.randint(1000, 10000)
    confidence = round(random.uniform(0.7, 0.95), 2)
    
    return {
        "summary": f"Daily analysis completed for {days_back} day(s). "
                  f"Analyzed {log_count} log entries. "
                  f"System shows {'stable' if confidence > 0.8 else 'some concerns'} performance.",
        "key_insights": random.sample(SAMPLE_INSIGHTS, random.randint(2, 4)),
        "recommendations": random.sample(SAMPLE_RECOMMENDATIONS, random.randint(1, 3)),
        "confidence_score": confidence,
        "analysis_timestamp": datetime.now().isoformat(),
        "log_count": log_count
    }


@app.get("/analysis/errors")
async def analyze_errors(hours_back: int = 24):
    """Analyze errors with realistic test data."""
    error_count = random.randint(0, 50)
    confidence = round(random.uniform(0.6, 0.9), 2)
    
    if error_count == 0:
        summary = f"No errors detected in the last {hours_back} hours. System is operating normally."
        insights = ["No error patterns identified", "System stability is excellent"]
        recommendations = ["Continue current monitoring practices"]
    else:
        summary = f"Found {error_count} errors in the last {hours_back} hours. "
        summary += "Analysis indicates " + ("minor issues" if error_count < 10 else "significant concerns") + "."
        insights = random.sample(SAMPLE_ERRORS, min(random.randint(1, 3), len(SAMPLE_ERRORS)))
        recommendations = random.sample(SAMPLE_RECOMMENDATIONS, random.randint(1, 3))
    
    return {
        "summary": summary,
        "key_insights": insights,
        "recommendations": recommendations,
        "confidence_score": confidence,
        "analysis_timestamp": datetime.now().isoformat(),
        "log_count": random.randint(500, 5000)
    }


@app.get("/analysis/performance")
async def analyze_performance(hours_back: int = 24):
    """Analyze performance with realistic test data."""
    performance_score = random.uniform(0.6, 0.95)
    confidence = round(random.uniform(0.7, 0.9), 2)
    
    if performance_score > 0.8:
        summary = f"Performance analysis shows excellent system health over the last {hours_back} hours."
        insights = ["All performance metrics within acceptable ranges", "System responding efficiently"]
        recommendations = ["Continue current performance monitoring"]
    elif performance_score > 0.6:
        summary = f"Performance analysis shows some concerns over the last {hours_back} hours."
        insights = random.sample(SAMPLE_PERFORMANCE_ISSUES, random.randint(1, 2))
        recommendations = random.sample(SAMPLE_RECOMMENDATIONS, random.randint(1, 2))
    else:
        summary = f"Performance analysis indicates significant issues over the last {hours_back} hours."
        insights = random.sample(SAMPLE_PERFORMANCE_ISSUES, random.randint(2, 4))
        recommendations = random.sample(SAMPLE_RECOMMENDATIONS, random.randint(2, 4))
    
    return {
        "summary": summary,
        "key_insights": insights,
        "recommendations": recommendations,
        "confidence_score": confidence,
        "analysis_timestamp": datetime.now().isoformat(),
        "log_count": random.randint(1000, 8000)
    }


@app.get("/metrics/summary")
async def get_metrics_summary():
    """Get metrics summary for testing."""
    return {
        "total_requests": random.randint(10000, 100000),
        "error_rate": round(random.uniform(0.01, 0.05), 3),
        "avg_response_time": round(random.uniform(100, 500), 2),
        "cpu_usage": round(random.uniform(20, 80), 1),
        "memory_usage": round(random.uniform(30, 90), 1),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/logs/recent")
async def get_recent_logs(limit: int = 100):
    """Get recent logs for testing."""
    log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    sources = ["api", "database", "auth", "cache", "worker"]
    
    logs = []
    for i in range(min(limit, 50)):  # Limit to 50 for testing
        logs.append({
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 1440))).isoformat(),
            "level": random.choice(log_levels),
            "message": f"Sample log message {i+1}",
            "source": random.choice(sources),
            "metadata": {
                "request_id": f"req_{random.randint(1000, 9999)}",
                "user_id": random.randint(1, 1000) if random.random() > 0.5 else None
            }
        })
    
    return {"logs": logs, "count": len(logs)}


if __name__ == "__main__":
    print("Starting Mock API Server...")
    print("Dashboard can be tested at: http://localhost:8001")
    print("API endpoints available at: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
