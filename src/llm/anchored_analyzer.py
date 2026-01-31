"""
Anchored analyzer that uses predefined incident templates to prevent hallucinations.
This analyzer combines the template-based approach with Qwen2-1.5B for reliable monitoring analysis.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .incident_templates import IncidentAnalyzer, IncidentCategory, IncidentSeverity
from .local_analyzer import LocalLogAnalyzer
from ..data.fetchers import LogEntry

logger = logging.getLogger(__name__)


@dataclass
class AnchoredAnalysisResult:
    """Result of anchored analysis using templates."""
    summary: str
    cause: str
    next_step: str
    category: str
    severity: str
    confidence: float
    template_used: str
    alternative_categories: List[str]
    key_insights: List[str]
    recommendations: List[str]
    analysis_timestamp: datetime
    model_used: str


class AnchoredLogAnalyzer:
    """
    Anchored analyzer that uses predefined templates to prevent hallucinations.
    
    This analyzer:
    1. First categorizes incidents using predefined templates
    2. Uses Qwen2-1.5B only to fill in template blanks with specific details
    3. Provides structured, reliable outputs anchored to known incident types
    """
    
    def __init__(self, model: str = "qwen2:1.5b", host: str = "http://localhost:11434"):
        """
        Initialize the anchored analyzer.
        
        Args:
            model: Ollama model to use (e.g., "qwen2:1.5b", "llama3:8b")
            host: Ollama server host
        """
        self.incident_analyzer = IncidentAnalyzer()
        self.local_analyzer = LocalLogAnalyzer(model=model, host=host)
        self.model = model
    
    def analyze_logs(self, logs: List[LogEntry], analysis_type: str = "incident_analysis") -> AnchoredAnalysisResult:
        """
        Analyze logs using anchored templates to prevent hallucinations.
        
        Args:
            logs: List of log entries to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            AnchoredAnalysisResult with structured, reliable analysis
        """
        if not logs:
            return self._create_empty_result()
        
        # Group logs by service and severity for better analysis
        grouped_logs = self._group_logs_by_service(logs)
        
        # Analyze each service group
        service_analyses = []
        for service_name, service_logs in grouped_logs.items():
            analysis = self._analyze_service_logs(service_name, service_logs)
            if analysis:
                service_analyses.append(analysis)
        
        # Combine analyses into final result
        return self._combine_analyses(service_analyses, logs)
    
    def _group_logs_by_service(self, logs: List[LogEntry]) -> Dict[str, List[LogEntry]]:
        """Group logs by service name."""
        grouped = {}
        for log in logs:
            # Extract service name from source or metadata
            service_name = self._extract_service_name(log)
            if service_name not in grouped:
                grouped[service_name] = []
            grouped[service_name].append(log)
        return grouped
    
    def _extract_service_name(self, log: LogEntry) -> str:
        """Extract service name from log entry."""
        # Try to get service name from metadata first
        if log.metadata and "service" in log.metadata:
            return log.metadata["service"]
        
        # Extract from source field
        if log.source:
            # Remove common suffixes like -01, -02, etc.
            service_name = log.source.split("-")[0]
            return service_name
        
        return "unknown-service"
    
    def _analyze_service_logs(self, service_name: str, logs: List[LogEntry]) -> Optional[Dict[str, Any]]:
        """Analyze logs for a specific service."""
        critical_log = self._find_critical_log(logs)
        if not critical_log:
            return None

        fallback_incident = self.incident_analyzer.analyze_incident(
            critical_log.message,
            critical_log.metadata,
            service_name
        )

        return self._enhance_with_llm(service_name, logs, critical_log, fallback_incident)
    
    def _find_critical_log(self, logs: List[LogEntry]) -> Optional[LogEntry]:
        """Find the most critical log entry in the list."""
        # Sort by severity: ERROR > WARNING > INFO
        severity_order = {"ERROR": 3, "WARNING": 2, "INFO": 1, "DEBUG": 0}
        
        critical_log = None
        highest_severity = -1
        
        for log in logs:
            severity = severity_order.get(log.level, 0)
            if severity > highest_severity:
                highest_severity = severity
                critical_log = log
        
        return critical_log
    
    def _enhance_with_llm(
        self,
        service_name: str,
        logs: List[LogEntry],
        critical_log: LogEntry,
        fallback_incident: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use Qwen to pick a template and populate a structured response."""

        candidates, candidate_order = self._get_candidate_templates(critical_log, fallback_incident["category"])

        try:
            prompt = self._create_anchored_prompt(service_name, logs, critical_log, candidates)
            response = self.local_analyzer.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_anchored_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                options={
                    "temperature": 0.1,
                    "num_predict": 600,
                },
            )

            llm_response = response["message"]["content"]
            enhanced = self._parse_llm_structured_response(
                llm_response,
                candidates,
                candidate_order,
                fallback_incident,
            )

            if enhanced:
                return enhanced

            logger.warning("LLM returned unparseable payload; using fallback template analysis")

        except Exception as exc:  # noqa: BLE001
            logger.warning(f"LLM enhancement failed: {exc}")

        return self._add_fallback_insights(fallback_incident)

    def _get_candidate_templates(
        self,
        critical_log: LogEntry,
        primary_category: str,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Build the shortlist of templates to present to Qwen."""

        matches = self.incident_analyzer.registry.find_matching_templates(
            critical_log.message,
            critical_log.metadata or {},
        )

        candidate_templates: List[Dict[str, Any]] = []
        candidate_order: List[str] = []
        seen: set[str] = set()

        def add_template(template):
            if template.category.value in seen:
                return
            seen.add(template.category.value)
            candidate_templates.append(
                {
                    "id": template.category.value,
                    "severity": template.severity.value,
                    "summary_template": template.summary_template,
                    "cause_template": template.cause_template,
                    "next_step_template": template.next_step_template,
                    "keywords": template.keywords[:4],
                }
            )
            candidate_order.append(template.category.value)

        primary_template = self.incident_analyzer.registry.get_template_by_category_name(primary_category)
        if primary_template:
            add_template(primary_template)

        for template in matches:
            add_template(template)
            if len(candidate_templates) >= 6:
                break

        if len(candidate_templates) < 6:
            for template in self.incident_analyzer.registry.get_all_templates().values():
                if len(candidate_templates) >= 6:
                    break
                add_template(template)

        fallback_template = {
            "id": "investigate_further",
            "severity": "medium",
            "summary_template": "🚨 {service} requires further investigation",
            "cause_template": "Insufficient data to map to a known incident type; gather more telemetry",
            "next_step_template": "Escalate to on-call to review logs, metrics, and recent deployments",
            "keywords": ["investigate", "unknown", "follow up"],
        }

        if fallback_template["id"] not in seen:
            candidate_templates.append(fallback_template)
            candidate_order.append(fallback_template["id"])

        return candidate_templates, candidate_order

    def _create_anchored_prompt(
        self,
        service_name: str,
        logs: List[LogEntry],
        critical_log: LogEntry,
        candidate_templates: List[Dict[str, Any]],
    ) -> str:
        """Create the templated prompt presented to Qwen."""

        templates_section: List[str] = []
        for template in candidate_templates:
            templates_section.append(
                f"- id: {template['id']}\n"
                f"  severity: {template['severity']}\n"
                f"  summary_template: {template['summary_template']}\n"
                f"  cause_template: {template['cause_template']}\n"
                f"  next_step_template: {template['next_step_template']}"
            )
        templates_block = "\n".join(templates_section)

        metadata_text = json.dumps(critical_log.metadata or {}, indent=2, sort_keys=True)
        recent_logs_text = self._format_logs_for_prompt(logs)

        example_response = (
            "{\n"
            '  "category": "database_connection_pool_exhausted",\n'
            '  "severity": "critical",\n'
            '  "summary": "🚨 auth-api experiencing high error rate",\n'
            '  "cause": "Likely database connection pool exhaustion",\n'
            '  "next_step": "Check db-pool-size and restart pod if saturation persists",\n'
            '  "confidence": 0.82,\n'
            '  "key_insights": [\n'
            '    "Error rate spiked to 35% over the last 5 minutes",\n'
            '    "Connection pool is fully utilized with queueing"\n'
            '  ],\n'
            '  "recommendations": [\n'
            '    "Scale auth-api deployment to add capacity",\n'
            '    "Audit recent deploys touching database layer"\n'
            '  ]\n'
            "}"
        )

        prompt = (
            f"You are triaging an on-call alert for service '{service_name}'.\n"
            "Choose EXACTLY one incident type from the list below and populate its templates.\n"
            "Use the supplied data only; do not invent new incident types.\n\n"
            f"Incident types:\n{templates_block}\n\n"
            "Primary alert:\n"
            f"- level: {critical_log.level}\n"
            f"- message: {critical_log.message}\n"
            f"- metadata: {metadata_text}\n\n"
            "Recent related logs (most recent first):\n"
            f"{recent_logs_text}\n\n"
            "Respond with JSON only, matching this schema exactly:\n"
            "category, severity, summary, cause, next_step, confidence, key_insights[], recommendations[].\n"
            f"Example JSON:\n{example_response}\n\n"
            "Rules:\n"
            "1. Pick a category listed above.\n"
            "2. When filling templates, replace placeholders with concrete values or say 'Unknown'.\n"
            "3. Confidence must be between 0 and 1.\n"
            "4. Keep key_insights and recommendations short (max 3 each).\n"
            "5. Output JSON only, no prose."
        )

        return prompt

    def _get_anchored_system_prompt(self) -> str:
        """Get system prompt for anchored analysis."""

        return (
            "You are an on-call SRE."
            " Select exactly one incident type from the user prompt, fill in the provided templates,"
            " and answer with valid JSON."
            " Never invent new categories or stray from the template language."
            " If data is missing, state that it is unknown instead of guessing."
        )

    def _parse_llm_structured_response(
        self,
        llm_response: str,
        candidate_templates: List[Dict[str, Any]],
        candidate_order: List[str],
        fallback_incident: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Parse a structured JSON response coming back from Qwen."""

        json_block = self._extract_json_block(llm_response)
        if not json_block:
            logger.debug("No JSON block detected in LLM response")
            return None

        try:
            payload = json.loads(json_block)
        except json.JSONDecodeError as exc:
            logger.debug(f"Failed to decode JSON block: {exc}")
            return None

        if not isinstance(payload, dict):
            logger.debug("Parsed payload is not a JSON object")
            return None

        candidate_map = {template["id"]: template for template in candidate_templates}
        category = payload.get("category")
        if category not in candidate_map:
            logger.debug(f"Category '{category}' not in candidate shortlist")
            return None

        chosen_template = candidate_map[category]
        severity_value = (
            payload.get("severity")
            or chosen_template.get("severity")
            or fallback_incident.get("severity", "medium")
        )
        severity = str(severity_value).strip()

        summary = payload.get("summary") or fallback_incident.get("summary")
        cause = payload.get("cause") or fallback_incident.get("cause")
        next_step = payload.get("next_step") or fallback_incident.get("next_step")

        summary = "" if summary is None else str(summary).strip()
        cause = "" if cause is None else str(cause).strip()
        next_step = "" if next_step is None else str(next_step).strip()

        if not summary:
            summary = str(fallback_incident.get("summary", "")).strip()
        if not cause:
            cause = str(fallback_incident.get("cause", "")).strip()
        if not next_step:
            next_step = str(fallback_incident.get("next_step", "")).strip()

        try:
            confidence_raw = payload.get("confidence", fallback_incident.get("confidence", 0.7))
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = fallback_incident.get("confidence", 0.7)
        confidence = max(0.0, min(1.0, confidence))

        key_insights = [str(item).strip() for item in payload.get("key_insights", []) if str(item).strip()]
        recommendations = [str(item).strip() for item in payload.get("recommendations", []) if str(item).strip()]

        if not key_insights:
            key_insights = [
                f"Incident classified as {category}",
                f"Reported confidence {confidence:.0%}",
            ]

        if not recommendations:
            if next_step:
                recommendations = [next_step]
            else:
                recommendations = [fallback_incident.get("next_step", "Review incident manually")]

        alternative_categories = [cid for cid in candidate_order if cid not in {category, "investigate_further"}][:3]
        if not alternative_categories:
            alternative_categories = fallback_incident.get("alternative_categories", [])

        return {
            "summary": summary,
            "cause": cause,
            "next_step": next_step,
            "category": category,
            "severity": severity,
            "confidence": confidence,
            "template_used": category if category != "investigate_further" else fallback_incident.get("template_used", "investigate_further"),
            "alternative_categories": alternative_categories,
            "key_insights": key_insights,
            "recommendations": recommendations,
        }

    def _extract_json_block(self, llm_response: str) -> Optional[str]:
        """Pull the first JSON object (optionally fenced) from the LLM output."""

        if not llm_response:
            return None

        response = llm_response.strip()
        if not response:
            return None

        blocks = []
        if "```" in response:
            parts = response.split("```")
            for part in parts:
                cleaned = part.strip()
                if cleaned:
                    blocks.append(cleaned)
        else:
            blocks.append(response)

        for block in blocks:
            if block.lower().startswith("json"):
                block = block[4:].strip()
            if block.startswith("{") and block.endswith("}"):
                return block

        return None

    def _format_logs_for_prompt(self, logs: List[LogEntry], limit: int = 5) -> str:
        """Format recent logs for inclusion in the Qwen prompt."""

        snippets = []
        for log in logs[:limit]:
            metadata_text = json.dumps(log.metadata or {}, sort_keys=True)
            snippets.append(
                f"- [{log.timestamp}] {log.level}: {log.message}\n"
                f"  metadata: {metadata_text}"
            )

        if not snippets:
            return "- No additional context available"

        return "\n".join(snippets)

    def _add_fallback_insights(self, incident_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Add fallback insights when LLM enhancement fails."""
        enhanced = incident_analysis.copy()
        enhanced['key_insights'] = [
            f"Incident categorized as {incident_analysis['category']} with {incident_analysis['severity']} severity",
            f"Template-based analysis provides {incident_analysis['confidence']:.1%} confidence"
        ]
        enhanced['recommendations'] = [
            "Follow the template-based next steps for this incident type",
            "Review logs manually for additional context if needed"
        ]
        return enhanced
    
    def _combine_analyses(self, service_analyses: List[Dict[str, Any]], 
                         all_logs: List[LogEntry]) -> AnchoredAnalysisResult:
        """Combine multiple service analyses into a single result."""
        if not service_analyses:
            return self._create_empty_result()
        
        # Use the most critical analysis as the primary result
        primary_analysis = max(service_analyses, key=lambda x: self._get_severity_score(x['severity']))
        
        # Combine insights and recommendations from all analyses
        all_insights = []
        all_recommendations = []
        
        for analysis in service_analyses:
            all_insights.extend(analysis.get('key_insights', []))
            all_recommendations.extend(analysis.get('recommendations', []))
        
        # Remove duplicates and limit to most important
        all_insights = list(dict.fromkeys(all_insights))[:5]
        all_recommendations = list(dict.fromkeys(all_recommendations))[:5]
        
        return AnchoredAnalysisResult(
            summary=primary_analysis['summary'],
            cause=primary_analysis['cause'],
            next_step=primary_analysis['next_step'],
            category=primary_analysis['category'],
            severity=primary_analysis['severity'],
            confidence=primary_analysis['confidence'],
            template_used=primary_analysis['template_used'],
            alternative_categories=primary_analysis.get('alternative_categories', []),
            key_insights=all_insights,
            recommendations=all_recommendations,
            analysis_timestamp=datetime.now(),
            model_used=self.model
        )
    
    def _get_severity_score(self, severity: str) -> int:
        """Get numeric score for severity comparison."""
        severity_scores = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }
        return severity_scores.get(severity.lower(), 0)
    
    def _create_empty_result(self) -> AnchoredAnalysisResult:
        """Create empty result when no logs are provided."""
        return AnchoredAnalysisResult(
            summary="No logs found for analysis",
            cause="No incidents detected",
            next_step="No action required",
            category="none",
            severity="low",
            confidence=0.0,
            template_used="none",
            alternative_categories=[],
            key_insights=[],
            recommendations=[],
            analysis_timestamp=datetime.now(),
            model_used=self.model
        )
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available incident templates."""
        templates = []
        for category, template in self.incident_analyzer.registry.get_all_templates().items():
            templates.append({
                "category": category.value,
                "severity": template.severity.value,
                "keywords": template.keywords,
                "summary_template": template.summary_template
            })
        return templates
    
    def analyze_single_incident(self, log_message: str, metadata: Dict[str, Any] = None, 
                               service_name: str = "unknown") -> Dict[str, Any]:
        """
        Analyze a single incident using templates.
        
        This is useful for real-time alert processing.
        """
        return self.incident_analyzer.analyze_incident(log_message, metadata, service_name)
