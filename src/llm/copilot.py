"""
AI Copilot for log analysis and summarization.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import openai
from dataclasses import dataclass

try:
    # Try relative imports first (when run as package)
    from ..data.fetchers import LogEntry
    from .local_analyzer import LocalLogAnalyzer, HybridLogAnalyzer, LocalAnalysisResult
    from .config import get_config, get_model_config, validate_config
except ImportError:
    # Fall back to absolute imports (when run from notebook or standalone)
    from data.fetchers import LogEntry
    from llm.local_analyzer import LocalLogAnalyzer, HybridLogAnalyzer, LocalAnalysisResult
    from llm.config import get_config, get_model_config, validate_config

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of log analysis."""
    summary: str
    key_insights: List[str]
    recommendations: List[str]
    confidence_score: float
    analysis_timestamp: datetime


class LogAnalyzer:
    """AI-powered log analyzer."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def analyze_logs(self, logs: List[LogEntry], analysis_type: str = "daily_summary") -> AnalysisResult:
        """Analyze logs and provide insights."""
        
        if not logs:
            return AnalysisResult(
                summary="No logs found for the specified time period.",
                key_insights=[],
                recommendations=[],
                confidence_score=0.0,
                analysis_timestamp=datetime.now()
            )
        
        # Prepare log data for analysis
        log_text = self._prepare_logs_for_analysis(logs)
        
        # Generate prompt based on analysis type
        prompt = self._create_prompt(log_text, analysis_type)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis_text = response.choices[0].message.content
            return self._parse_analysis_result(analysis_text, logs)
            
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
            return AnalysisResult(
                summary=f"Error during analysis: {str(e)}",
                key_insights=[],
                recommendations=[],
                confidence_score=0.0,
                analysis_timestamp=datetime.now()
            )
    
    def _prepare_logs_for_analysis(self, logs: List[LogEntry]) -> str:
        """Prepare logs in a format suitable for LLM analysis."""
        # Sample logs to avoid token limits
        sample_size = min(100, len(logs))
        sampled_logs = logs[:sample_size]
        
        log_text = ""
        for log in sampled_logs:
            # Basic log entry
            log_text += f"[{log.timestamp}] {log.level} - {log.source}: {log.message}\n"
            
            # Include relevant metadata for better analysis
            if log.metadata:
                relevant_metadata = {}
                for key, value in log.metadata.items():
                    # Include key metadata fields that help with analysis
                    if key in ['request_id', 'trace_id', 'user_id', 'endpoint', 'method', 
                              'response_time_ms', 'error_code', 'component', 'host', 'port',
                              'memory_usage_percent', 'cpu_usage_percent', 'disk_usage_percent',
                              'pool_size', 'active_connections', 'queue_depth', 'retry_count',
                              'threat_level', 'auth_method', 'session_id']:
                        relevant_metadata[key] = value
                
                if relevant_metadata:
                    metadata_str = ", ".join([f"{k}={v}" for k, v in relevant_metadata.items()])
                    log_text += f"  Metadata: {metadata_str}\n"
        
        return log_text
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI assistant."""
        return """You are an expert DevOps engineer and log analyst with 10+ years of experience in production systems monitoring and incident response. Your expertise spans microservices, distributed systems, cloud infrastructure, and security operations.

## Core Responsibilities:
1. **Pattern Recognition**: Identify recurring issues, error clusters, and performance trends
2. **Root Cause Analysis**: Trace issues back to their source using request IDs, trace IDs, and service dependencies
3. **Priority Assessment**: Classify issues by severity (CRITICAL > ERROR > WARNING > INFO) and business impact
4. **Actionable Insights**: Provide specific, implementable recommendations with clear next steps
5. **Security Awareness**: Flag suspicious activities, authentication failures, and potential security threats

## Analysis Framework:
- **Correlation Analysis**: Look for related events across services using request IDs, user IDs, and timestamps
- **Resource Monitoring**: Pay attention to memory usage, CPU, disk space, connection pools, and queue depths
- **Performance Metrics**: Analyze response times, throughput, error rates, and cache hit ratios
- **Service Dependencies**: Identify cascading failures and service communication issues
- **Temporal Patterns**: Note time-based patterns, spikes, and recurring issues

## Log Types to Prioritize:
- **CRITICAL/ERROR**: Database failures, service outages, security breaches
- **WARNING**: Performance degradation, resource exhaustion, rate limiting
- **INFO**: Successful operations, health checks, routine maintenance

## Output Format:
SUMMARY: [2-3 sentence overview of system health and critical issues]
KEY INSIGHTS:
- [Most critical issue with context and impact]
- [Performance or reliability concern]
- [Security or operational insight]
RECOMMENDATIONS:
- [Immediate action needed - specific and actionable]
- [Medium-term improvement - with rationale]
CONFIDENCE: [0.0-1.0 based on log clarity and issue specificity]

## Important Notes:
- Use metadata fields (request_id, trace_id, user_id, etc.) to connect related events
- Consider service topology and dependencies when analyzing failures
- Prioritize issues that could impact user experience or system stability
- Be specific about which services, endpoints, or components are affected
- Include relevant metrics, thresholds, and timeframes in your analysis"""
    
    def _create_prompt(self, log_text: str, analysis_type: str) -> str:
        """Create analysis prompt based on type."""
        prompts = {
            "daily_summary": f"""Analyze these logs from the last 24 hours and provide a daily summary:

{log_text}

Please provide:
1. A brief summary of the overall system health
2. Key insights about errors, performance, or anomalies
3. Actionable recommendations for the team

Focus on the most important issues that need attention.""",
            
            "error_analysis": f"""Analyze these logs focusing specifically on errors and failures:

{log_text}

Please identify:
1. The most critical errors
2. Error patterns and trends
3. Root cause analysis where possible
4. Immediate actions needed""",
            
            "performance_analysis": f"""Analyze these logs for performance issues:

{log_text}

Please identify:
1. Performance bottlenecks
2. Response time issues
3. Resource utilization problems
4. Optimization recommendations"""
        }
        
        return prompts.get(analysis_type, prompts["daily_summary"])
    
    def _parse_analysis_result(self, analysis_text: str, logs: List[LogEntry]) -> AnalysisResult:
        """Parse the LLM response into structured format."""
        lines = analysis_text.strip().split('\n')
        
        summary = ""
        key_insights = []
        recommendations = []
        confidence_score = 0.8  # Default confidence
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("SUMMARY:"):
                summary = line.replace("SUMMARY:", "").strip()
                current_section = "summary"
            elif line.startswith("KEY INSIGHTS:"):
                current_section = "insights"
            elif line.startswith("RECOMMENDATIONS:"):
                current_section = "recommendations"
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence_score = float(line.replace("CONFIDENCE:", "").strip())
                except ValueError:
                    confidence_score = 0.8
            elif line.startswith("- ") and current_section in ["insights", "recommendations"]:
                if current_section == "insights":
                    key_insights.append(line[2:].strip())
                elif current_section == "recommendations":
                    recommendations.append(line[2:].strip())
        
        return AnalysisResult(
            summary=summary or "Analysis completed",
            key_insights=key_insights,
            recommendations=recommendations,
            confidence_score=confidence_score,
            analysis_timestamp=datetime.now()
        )


class CopilotService:
    """Main service class for the AI Copilot with support for local and cloud models."""
    
    def __init__(self, analyzer: Union[LogAnalyzer, LocalLogAnalyzer, HybridLogAnalyzer], fetcher):
        self.analyzer = analyzer
        self.fetcher = fetcher
        self.config = get_config()
    
    def get_daily_summary(self, days_back: int = 1) -> AnalysisResult:
        """Get daily summary of logs."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        logs = self.fetcher.fetch_logs(start_time, end_time)
        return self.analyzer.analyze_logs(logs, "daily_summary")
    
    def analyze_errors(self, hours_back: int = 24) -> AnalysisResult:
        """Analyze errors in the specified time period."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        logs = self.fetcher.fetch_logs(start_time, end_time)
        # Filter for error logs
        error_logs = [log for log in logs if log.level.upper() in ['ERROR', 'FATAL', 'CRITICAL']]
        return self.analyzer.analyze_logs(error_logs, "error_analysis")
    
    def analyze_performance(self, hours_back: int = 24) -> AnalysisResult:
        """Analyze performance issues."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        logs = self.fetcher.fetch_logs(start_time, end_time)
        return self.analyzer.analyze_logs(logs, "performance_analysis")


def create_analyzer(provider: str = None, **kwargs) -> Union[LogAnalyzer, LocalLogAnalyzer, HybridLogAnalyzer]:
    """
    Factory function to create the appropriate analyzer based on configuration.
    
    Args:
        provider: Force a specific provider ("local", "openai", "hybrid")
        **kwargs: Additional arguments for analyzer initialization
    
    Returns:
        Configured analyzer instance
    """
    config = get_config()
    validation = validate_config()
    
    if provider == "local":
        if not validation["local_available"]:
            raise ValueError("Local models not available. Please install Ollama and download a model.")
        return LocalLogAnalyzer(
            model=kwargs.get("model", config.local_model),
            host=kwargs.get("host", config.ollama_host)
        )
    
    elif provider == "openai":
        if not validation["openai_available"]:
            raise ValueError("OpenAI not available. Please set OPENAI_API_KEY environment variable.")
        return LogAnalyzer(
            api_key=kwargs.get("api_key", config.openai_api_key),
            model=kwargs.get("model", config.openai_model)
        )
    
    elif provider == "hybrid" or config.enable_hybrid:
        return HybridLogAnalyzer(
            openai_api_key=kwargs.get("openai_api_key", config.openai_api_key),
            local_model=kwargs.get("local_model", config.local_model),
            prefer_local=kwargs.get("prefer_local", config.preferred_provider == "local")
        )
    
    else:
        # Auto-select based on availability and preference
        if config.preferred_provider == "local" and validation["local_available"]:
            return LocalLogAnalyzer(
                model=config.local_model,
                host=config.ollama_host
            )
        elif validation["openai_available"]:
            return LogAnalyzer(
                api_key=config.openai_api_key,
                model=config.openai_model
            )
        elif validation["local_available"]:
            return LocalLogAnalyzer(
                model=config.local_model,
                host=config.ollama_host
            )
        else:
            raise ValueError("No analyzers available. Please check your configuration.")


def create_copilot_service(fetcher, provider: str = None, **kwargs) -> CopilotService:
    """
    Factory function to create a CopilotService with the appropriate analyzer.
    
    Args:
        fetcher: Log fetcher instance
        provider: Force a specific provider ("local", "openai", "hybrid")
        **kwargs: Additional arguments for analyzer initialization
    
    Returns:
        Configured CopilotService instance
    """
    analyzer = create_analyzer(provider=provider, **kwargs)
    return CopilotService(analyzer=analyzer, fetcher=fetcher)
