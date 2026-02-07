"""
Log Analysis Agent.
Specializes in querying and interpreting logs using the LocalLogAnalyzer.
"""
from typing import Optional, List
from datetime import datetime
from .base import BaseAgent, AgentContext
from ..llm.local_analyzer import LocalLogAnalyzer
from ..data.fetchers import BaseLogFetcher, LogEntry
import logging

logger = logging.getLogger(__name__)

class MockFetcher(BaseLogFetcher):
    """
    Mock fetcher for demonstration purposes.
    Returns static logs.
    """
    def fetch_logs(self, start_time: datetime = None, end_time: datetime = None) -> List[LogEntry]:
        return [
            LogEntry(
                timestamp=datetime.now(),
                level="ERROR",
                message="Connection timed out to payment-gateway",
                source="checkout-service",
                metadata={"trace_id": "abc-123"}
            ),
            LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message="Retrying connection to payment-gateway",
                source="checkout-service",
                metadata={"trace_id": "abc-123"}
            ),
             LogEntry(
                timestamp=datetime.now(),
                level="ERROR",
                message="Max retries exceeded",
                source="checkout-service",
                metadata={"trace_id": "abc-123"}
            )
        ]

class LogAnalysisAgent(BaseAgent):
    """
    Agent responsible for fetching and analyzing logs.
    """
    
    def __init__(self, model: str = "qwen2:1.5b"):
        system_prompt = (
             "You are a Log Analysis Expert. Your goal is to find relevant logs "
             "based on search queries and interpret error patterns."
        )
        super().__init__(
            name="LogAnalysisAgent",
            role="Specialist",
            system_prompt=system_prompt,
            model=model
        )
        self.analyzer = LocalLogAnalyzer(model=model)
        # For the foundation MVP, we use a MockFetcher.
        # In production, this would be injected or configured (e.g. ELKFetcher)
        self.fetcher = MockFetcher() 

    def run(self, message: str, context: Optional[AgentContext] = None) -> str:
        """
        Execute log analysis task.
        
        Expected message format (simplified for MVP): "Check logs for service X" or "Analyze errors in Y"
        """
        self.logger.info(f"Analyzing logs request: {message}")
        
        # Simple heuristic for MVP:
        # 1. Fetch recent logs (mocked or real)
        # 2. Run them through the LocalLogAnalyzer
        
        # TODO: Parse 'message' to extract filters like service name, filters, time range
        # For now, we'll fetch a standard batch of logs to demonstrate flow.
        
        logs = self._fetch_relevant_logs(message)
        analysis_result = self.analyzer.analyze_logs(logs)
        
        return (
            f"**Log Analysis Report**\n"
            f"Summary: {analysis_result.summary}\n"
            f"Key Insights: {', '.join(analysis_result.key_insights)}\n"
            f"Confidence: {analysis_result.confidence_score}"
        )

    def _fetch_relevant_logs(self, query: str) -> List[LogEntry]:
        """
        Access the data layer to get logs.
        """
        # This is where we would interpret the query to filter logs.
        # For the foundation MVP, we just fetch basic logs.
        # We assume start/end times are implicit for now.
        return self.fetcher.fetch_logs()
