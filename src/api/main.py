"""
FastAPI main application for AI Copilot.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from ..data.fetchers import create_fetcher
from ..llm.copilot import LogAnalyzer, CopilotService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Copilot API",
    description="AI-powered monitoring and logging analysis",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
copilot_service: Optional[CopilotService] = None


class AnalysisRequest(BaseModel):
    """Request model for log analysis."""
    analysis_type: str = "daily_summary"
    time_range_hours: int = 24
    system_type: str = "elk"


class AnalysisResponse(BaseModel):
    """Response model for log analysis."""
    summary: str
    key_insights: list
    recommendations: list
    confidence_score: float
    analysis_timestamp: datetime
    log_count: int


def get_copilot_service() -> CopilotService:
    """Dependency to get the copilot service."""
    global copilot_service
    
    if copilot_service is None:
        # Initialize service based on environment configuration
        system_type = os.getenv("MONITORING_SYSTEM", "elk")
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Create fetcher configuration
        fetcher_config = {
            "elasticsearch_url": os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
            "prometheus_url": os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
            "splunk_url": os.getenv("SPLUNK_URL", "https://localhost:8089"),
            "splunk_token": os.getenv("SPLUNK_TOKEN"),
            "index_pattern": os.getenv("ELASTICSEARCH_INDEX", "logstash-*")
        }
        
        # Create fetcher and analyzer
        fetcher = create_fetcher(system_type, fetcher_config)
        analyzer = LogAnalyzer(api_key)
        copilot_service = CopilotService(analyzer, fetcher)
    
    return copilot_service


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Copilot API is running", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        service = get_copilot_service()
        # Test connection to monitoring system
        connection_ok = service.fetcher.test_connection()
        
        return {
            "status": "healthy" if connection_ok else "degraded",
            "timestamp": datetime.now(),
            "monitoring_system_connected": connection_ok
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(),
            "error": str(e)
        }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_logs(
    request: AnalysisRequest,
    service: CopilotService = Depends(get_copilot_service)
):
    """Analyze logs and provide insights."""
    try:
        # Determine time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=request.time_range_hours)
        
        # Fetch logs
        logs = service.fetcher.fetch_logs(start_time, end_time)
        
        if not logs:
            return AnalysisResponse(
                summary="No logs found for the specified time period.",
                key_insights=[],
                recommendations=[],
                confidence_score=0.0,
                analysis_timestamp=datetime.now(),
                log_count=0
            )
        
        # Analyze logs
        result = service.analyzer.analyze_logs(logs, request.analysis_type)
        
        return AnalysisResponse(
            summary=result.summary,
            key_insights=result.key_insights,
            recommendations=result.recommendations,
            confidence_score=result.confidence_score,
            analysis_timestamp=result.analysis_timestamp,
            log_count=len(logs)
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/summary/daily")
async def get_daily_summary(
    days_back: int = 1,
    service: CopilotService = Depends(get_copilot_service)
):
    """Get daily summary of logs."""
    try:
        result = service.get_daily_summary(days_back)
        return {
            "summary": result.summary,
            "key_insights": result.key_insights,
            "recommendations": result.recommendations,
            "confidence_score": result.confidence_score,
            "analysis_timestamp": result.analysis_timestamp
        }
    except Exception as e:
        logger.error(f"Daily summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Daily summary failed: {str(e)}")


@app.get("/analysis/errors")
async def analyze_errors(
    hours_back: int = 24,
    service: CopilotService = Depends(get_copilot_service)
):
    """Analyze errors in the specified time period."""
    try:
        result = service.analyze_errors(hours_back)
        return {
            "summary": result.summary,
            "key_insights": result.key_insights,
            "recommendations": result.recommendations,
            "confidence_score": result.confidence_score,
            "analysis_timestamp": result.analysis_timestamp
        }
    except Exception as e:
        logger.error(f"Error analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Error analysis failed: {str(e)}")


@app.get("/analysis/performance")
async def analyze_performance(
    hours_back: int = 24,
    service: CopilotService = Depends(get_copilot_service)
):
    """Analyze performance issues."""
    try:
        result = service.analyze_performance(hours_back)
        return {
            "summary": result.summary,
            "key_insights": result.key_insights,
            "recommendations": result.recommendations,
            "confidence_score": result.confidence_score,
            "analysis_timestamp": result.analysis_timestamp
        }
    except Exception as e:
        logger.error(f"Performance analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance analysis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
