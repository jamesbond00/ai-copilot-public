"""Local LLM analyzer using Ollama for log analysis."""

import logging
import re
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass

try:
    import ollama  # type: ignore[import]
except ModuleNotFoundError as exc:  # pragma: no cover - exercised in environments without Ollama
    ollama = None  # type: ignore[assignment]
    _OLLAMA_IMPORT_ERROR = exc
else:
    _OLLAMA_IMPORT_ERROR = None

if TYPE_CHECKING:  # pragma: no cover - import only for type checkers
    from ollama import Client as OllamaClient  # noqa: F401

try:
    # Try relative imports first (when run as package)
    from ..data.fetchers import LogEntry
except ImportError:
    # Fall back to absolute imports (when run from notebook or standalone)
    from data.fetchers import LogEntry

logger = logging.getLogger(__name__)


@dataclass
class LocalAnalysisResult:
    """Result of local log analysis."""
    summary: str
    key_insights: List[str]
    recommendations: List[str]
    confidence_score: float
    analysis_timestamp: datetime
    model_used: str


class LocalLogAnalyzer:
    """Local AI-powered log analyzer using Ollama."""
    
    def __init__(self, model: str = "qwen2:1.5b", host: str = "http://localhost:11434"):
        """
        Initialize the local analyzer.
        
        Args:
            model: Ollama model to use (e.g., "qwen2:1.5b", "llama3:8b")
            host: Ollama server host
        """
        if ollama is None:  # pragma: no cover - requires environment without Ollama
            raise ModuleNotFoundError(
                "LocalLogAnalyzer requires the `ollama` package. Install it with "
                "`pip install ollama` or include it via the project's dependencies."
            ) from _OLLAMA_IMPORT_ERROR

        self.model = model
        self.host = host
        self.client = ollama.Client(host=host)
        
        # Verify model is available
        self._verify_model()
    
    def _verify_model(self):
        """Verify that the specified model is available."""
        try:
            models = self.client.list()
            available_models = [model.get('name', model.get('model', '')) for model in models.get('models', [])]
            
            if self.model not in available_models:
                logger.warning(f"Model {self.model} not found. Available models: {available_models}")
                # Try to use the first available model
                if available_models:
                    self.model = available_models[0]
                    logger.info(f"Using available model: {self.model}")
                else:
                    raise ValueError("No models available. Please install a model with 'ollama pull <model>'")
        except Exception as e:
            logger.error(f"Error verifying model: {e}")
            raise
    
    def analyze_logs(self, logs: List[LogEntry], analysis_type: str = "daily_summary") -> LocalAnalysisResult:
        """Analyze logs and provide insights using local LLM."""
        
        if not logs:
            return LocalAnalysisResult(
                summary="No logs found for the specified time period.",
                key_insights=[],
                recommendations=[],
                confidence_score=0.0,
                analysis_timestamp=datetime.now(),
                model_used=self.model
            )
        
        # Prepare log data for analysis
        log_text = self._prepare_logs_for_analysis(logs)
        
        # Generate prompt based on analysis type
        prompt = self._create_prompt(log_text, analysis_type)
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": 0.3,
                    "num_predict": 1000,
                }
            )
            
            analysis_text = response['message']['content']
            return self._parse_analysis_result(analysis_text, logs)
            
        except Exception as e:
            logger.error(f"Error analyzing logs with local model: {e}")
            return LocalAnalysisResult(
                summary=f"Error during analysis: {str(e)}",
                key_insights=[],
                recommendations=[],
                confidence_score=0.0,
                analysis_timestamp=datetime.now(),
                model_used=self.model
            )
    
    def _prepare_logs_for_analysis(self, logs: List[LogEntry]) -> str:
        """Prepare logs in a format suitable for LLM analysis."""
        # Sample logs to avoid token limits
        sample_size = min(50, len(logs))  # Smaller sample for local models
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
        """Get the system prompt for the local AI assistant."""
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
            "daily_summary": f"""Analyze these production logs and provide a structured daily summary:

{log_text}

Please provide your analysis in the following EXACT format:

SUMMARY: [2-3 sentence overview of system health and critical issues]

KEY INSIGHTS:
- [Most critical issue with context and impact]
- [Performance or reliability concern]
- [Security or operational insight]

RECOMMENDATIONS:
- [Immediate action needed - specific and actionable]
- [Medium-term improvement - with rationale]

CONFIDENCE: [0.0-1.0 based on log clarity and issue specificity]

Focus on the most important issues that need immediate attention.""",
            
            "error_analysis": f"""Analyze these logs focusing specifically on errors and failures:

{log_text}

Please provide your analysis in the following EXACT format:

SUMMARY: [Brief overview of error patterns and severity]

KEY INSIGHTS:
- [Most critical error with context]
- [Error patterns and trends]
- [Root cause analysis where possible]

RECOMMENDATIONS:
- [Immediate actions needed]
- [Prevention strategies]

CONFIDENCE: [0.0-1.0 based on error clarity and available context]""",
            
            "performance_analysis": f"""Analyze these logs for performance issues:

{log_text}

Please provide your analysis in the following EXACT format:

SUMMARY: [Brief overview of performance status]

KEY INSIGHTS:
- [Performance bottlenecks identified]
- [Response time issues]
- [Resource utilization problems]

RECOMMENDATIONS:
- [Immediate optimization actions]
- [Long-term performance improvements]

CONFIDENCE: [0.0-1.0 based on performance data clarity]"""
        }
        
        return prompts.get(analysis_type, prompts["daily_summary"])
    
    def _parse_analysis_result(self, analysis_text: str, logs: List[LogEntry]) -> LocalAnalysisResult:
        """Parse the LLM response into structured format."""
        
        lines = analysis_text.strip().split('\n')

        def extract_bullet_content(line: str) -> Optional[str]:
            """Return bullet body if the line represents a list item."""
            bullet_match = re.match(r"^(?:[-*•]\s*|\d+[.)]\s*)(.+)$", line)
            if bullet_match:
                content = bullet_match.group(1).strip()
                return content if content else None
            return None

        summary = ""
        key_insights = []
        recommendations = []
        confidence_score = 0.8  # Default confidence
        
        current_section = None
        summary_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # More flexible parsing - handle various formats
            if (line.upper().startswith("**SUMMARY:**") or line.upper().startswith("SUMMARY:") or 
                line.upper().startswith("SUMMARY") or line.upper().startswith("DAILY SUMMARY:")):
                current_section = "summary"
                # Extract summary text after the colon
                if ":" in line:
                    summary_text = line.split(":", 1)[-1].strip()
                    if summary_text:
                        summary_lines.append(summary_text)
            elif (line.upper().startswith("**KEY INSIGHTS:**") or line.upper().startswith("KEY INSIGHTS:") or 
                  line.upper().startswith("INSIGHTS:") or line.upper().startswith("KEY INSIGHTS") or
                  line.upper().startswith("**KEY INSIGHTS**")):
                current_section = "insights"
            elif (line.upper().startswith("**ACTIONABLE RECOMMENDATIONS:**") or line.upper().startswith("RECOMMENDATIONS:") or 
                  line.upper().startswith("RECOMMENDATIONS") or line.upper().startswith("**RECOMMENDATIONS**")):
                current_section = "recommendations"
            elif line.upper().startswith("**CONFIDENCE:**") or line.upper().startswith("CONFIDENCE:"):
                try:
                    confidence_text = line.split(":", 1)[-1].strip()
                    # Try to extract number from text like "Based on the severity of these issues, the confidence level is high"
                    if "high" in confidence_text.lower():
                        confidence_score = 0.9
                    elif "medium" in confidence_text.lower():
                        confidence_score = 0.7
                    elif "low" in confidence_text.lower():
                        confidence_score = 0.5
                    else:
                        # Try to find a number in the text
                        numbers = re.findall(r'\d+\.?\d*', confidence_text)
                        if numbers:
                            confidence_score = float(numbers[0])
                except ValueError:
                    confidence_score = 0.8
            elif current_section == "summary":
                # Collect summary lines
                if line and not line.startswith(("**", "KEY", "RECOMMENDATIONS", "CONFIDENCE", "EXPLANATION")):
                    summary_lines.append(line)
            elif current_section == "insights":
                bullet_body = extract_bullet_content(line)
                if bullet_body is None and line.startswith("**") and "**" in line:
                    bullet_body = line.replace("**", "").strip()
                if bullet_body:
                    clean_line = bullet_body.replace("**", "").strip()
                    if clean_line and not clean_line.lower().startswith("recommend"):
                        key_insights.append(clean_line)
            elif current_section == "recommendations":
                bullet_body = extract_bullet_content(line)
                if bullet_body is None and line.startswith("**") and "**" in line:
                    bullet_body = line.replace("**", "").strip()
                if bullet_body:
                    clean_line = bullet_body.replace("**", "").strip()
                    if clean_line:
                        recommendations.append(clean_line)
        
        # Combine summary lines
        if summary_lines:
            summary = " ".join(summary_lines).strip()
        
        # If we still don't have a summary, try to extract from the beginning
        if not summary:
            # Look for the first substantial line that could be a summary
            for line in lines:
                line = line.strip()
                if line and len(line) > 20 and not line.startswith(("**", "KEY", "RECOMMENDATIONS", "CONFIDENCE", "-", "•", "*")):
                    summary = line
                    break
        
        # If still no summary, use the first part of the response
        if not summary:
            summary = analysis_text.split('\n')[0].strip()[:200] + "..." if len(analysis_text) > 200 else analysis_text.strip()
        
        return LocalAnalysisResult(
            summary=summary or "Analysis completed",
            key_insights=key_insights,
            recommendations=recommendations,
            confidence_score=confidence_score,
            analysis_timestamp=datetime.now(),
            model_used=self.model
        )


class HybridLogAnalyzer:
    """Hybrid analyzer that can use both local and OpenAI models."""
    
    def __init__(self, openai_api_key: Optional[str] = None, local_model: str = "qwen2:1.5b", 
                 prefer_local: bool = True):
        """
        Initialize hybrid analyzer.
        
        Args:
            openai_api_key: OpenAI API key (optional)
            local_model: Local model to use
            prefer_local: Whether to prefer local model over OpenAI
        """
        self.prefer_local = prefer_local
        
        # Initialize local analyzer
        try:
            self.local_analyzer = LocalLogAnalyzer(model=local_model)
            self.local_available = True
        except Exception as e:
            logger.warning(f"Local analyzer not available: {e}")
            self.local_analyzer = None
            self.local_available = False
        
        # Initialize OpenAI analyzer if key provided
        if openai_api_key:
            try:
                try:
                    from .copilot import LogAnalyzer
                except ImportError:
                    from llm.copilot import LogAnalyzer
                self.openai_analyzer = LogAnalyzer(api_key=openai_api_key)
                self.openai_available = True
            except Exception as e:
                logger.warning(f"OpenAI analyzer not available: {e}")
                self.openai_analyzer = None
                self.openai_available = False
        else:
            self.openai_analyzer = None
            self.openai_available = False
    
    def analyze_logs(self, logs: List[LogEntry], analysis_type: str = "daily_summary", 
                    force_local: bool = False, force_openai: bool = False):
        """Analyze logs using the best available analyzer."""
        
        # Determine which analyzer to use
        use_local = False
        use_openai = False
        
        if force_local and self.local_available:
            use_local = True
        elif force_openai and self.openai_available:
            use_openai = True
        elif self.prefer_local and self.local_available:
            use_local = True
        elif self.openai_available:
            use_openai = True
        elif self.local_available:
            use_local = True
        else:
            raise ValueError("No analyzers available. Please check your configuration.")
        
        # Perform analysis
        if use_local:
            logger.info(f"Using local model: {self.local_analyzer.model}")
            return self.local_analyzer.analyze_logs(logs, analysis_type)
        elif use_openai:
            logger.info("Using OpenAI model")
            return self.openai_analyzer.analyze_logs(logs, analysis_type)
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available models."""
        models = {"local": [], "openai": []}
        
        if self.local_available:
            try:
                models_list = self.local_analyzer.client.list()
                models["local"] = [model['name'] for model in models_list['models']]
            except Exception as e:
                logger.error(f"Error getting local models: {e}")
        
        if self.openai_available:
            models["openai"] = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        
        return models
