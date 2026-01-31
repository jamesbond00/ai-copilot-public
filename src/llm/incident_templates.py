"""
Predefined incident templates for de-risking hallucinations in monitoring systems.
These templates anchor the Qwen2-1.5B model to specific, reliable categories.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import re


logger = logging.getLogger(__name__)


class IncidentSeverity(Enum):
    """Incident severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentCategory(Enum):
    """Predefined incident categories to prevent hallucinations."""
    CPU_SATURATION = "cpu_saturation"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    DISK_SPACE_LOW = "disk_space_low"
    DATABASE_CONNECTION_POOL_EXHAUSTED = "database_connection_pool_exhausted"
    DATABASE_SLOW_QUERIES = "database_slow_queries"
    DATABASE_CONNECTION_TIMEOUT = "database_connection_timeout"
    NETWORK_LATENCY_HIGH = "network_latency_high"
    API_RATE_LIMITING = "api_rate_limiting"
    API_ERROR_RATE_HIGH = "api_error_rate_high"
    AUTHENTICATION_FAILURES = "authentication_failures"
    SECURITY_SUSPICIOUS_ACTIVITY = "security_suspicious_activity"
    SERVICE_HEALTH_CHECK_FAILURE = "service_health_check_failure"
    CACHE_MEMORY_PRESSURE = "cache_memory_pressure"
    CACHE_HIT_RATE_LOW = "cache_hit_rate_low"
    LOAD_BALANCER_BACKEND_UNHEALTHY = "load_balancer_backend_unhealthy"
    EXTERNAL_SERVICE_TIMEOUT = "external_service_timeout"
    BACKGROUND_JOB_FAILURE = "background_job_failure"
    FILE_SYSTEM_ERRORS = "file_system_errors"
    SSL_CERTIFICATE_EXPIRY = "ssl_certificate_expiry"
    CONFIGURATION_DRIFT = "configuration_drift"


@dataclass
class IncidentTemplate:
    """Template for a specific incident type."""
    category: IncidentCategory
    severity: IncidentSeverity
    summary_template: str
    cause_template: str
    next_step_template: str
    keywords: List[str]
    patterns: List[str]
    metadata_fields: List[str]


class IncidentTemplateRegistry:
    """Registry of predefined incident templates."""
    
    def __init__(self):
        self.templates = self._create_templates()
    
    def _create_templates(self) -> Dict[IncidentCategory, IncidentTemplate]:
        """Create all predefined incident templates."""
        return {
            IncidentCategory.CPU_SATURATION: IncidentTemplate(
                category=IncidentCategory.CPU_SATURATION,
                severity=IncidentSeverity.HIGH,
                summary_template="🚨 {service} experiencing high CPU usage ({cpu_percent}%)",
                cause_template="Likely caused by {cause_context} - check for runaway processes or resource-intensive operations",
                next_step_template="Check CPU usage by process, restart if necessary, scale horizontally if pattern persists",
                keywords=["cpu", "saturation", "high usage", "load average", "processor"],
                patterns=[
                    r"cpu.*usage.*(\d+)%",
                    r"load average.*(\d+\.\d+)",
                    r"cpu.*saturation",
                    r"processor.*overload"
                ],
                metadata_fields=["cpu_usage_percent", "load_average", "process_count", "host"]
            ),
            
            IncidentCategory.MEMORY_EXHAUSTION: IncidentTemplate(
                category=IncidentCategory.MEMORY_EXHAUSTION,
                severity=IncidentSeverity.CRITICAL,
                summary_template="🚨 {service} memory usage critical ({memory_percent}%)",
                cause_template="Memory exhaustion likely due to {cause_context} - check for memory leaks or insufficient allocation",
                next_step_template="Check memory usage by process, restart service, increase memory limits if needed",
                keywords=["memory", "exhaustion", "oom", "out of memory", "swap"],
                patterns=[
                    r"memory.*usage.*(\d+)%",
                    r"out of memory",
                    r"oom.*killer",
                    r"swap.*usage"
                ],
                metadata_fields=["memory_usage_percent", "memory_used_gb", "memory_total_gb", "host"]
            ),
            
            IncidentCategory.DISK_SPACE_LOW: IncidentTemplate(
                category=IncidentCategory.DISK_SPACE_LOW,
                severity=IncidentSeverity.HIGH,
                summary_template="🚨 {service} disk space low ({disk_percent}% full)",
                cause_template="Disk space exhaustion due to {cause_context} - check for log accumulation or data growth",
                next_step_template="Clean up old logs, archive data, or expand disk capacity",
                keywords=["disk", "space", "full", "usage", "filesystem"],
                patterns=[
                    r"disk.*space.*(\d+)%",
                    r"filesystem.*full",
                    r"no space left",
                    r"disk.*usage"
                ],
                metadata_fields=["disk_usage_percent", "used_gb", "total_gb", "mount_point", "host"]
            ),
            
            IncidentCategory.DATABASE_CONNECTION_POOL_EXHAUSTED: IncidentTemplate(
                category=IncidentCategory.DATABASE_CONNECTION_POOL_EXHAUSTED,
                severity=IncidentSeverity.CRITICAL,
                summary_template="🚨 {service} database connection pool exhausted ({active}/{max} connections)",
                cause_template="Connection pool exhaustion likely due to {cause_context} - check for connection leaks or high load",
                next_step_template="Check for connection leaks, restart service, increase pool size if needed",
                keywords=["connection", "pool", "exhausted", "database", "connections"],
                patterns=[
                    r"connection.*pool.*exhausted",
                    r"(\d+)/(\d+).*connections.*use",
                    r"database.*connection.*timeout",
                    r"pool.*size.*(\d+)"
                ],
                metadata_fields=["pool_size", "active_connections", "queue_depth", "host", "database"]
            ),
            
            IncidentCategory.DATABASE_SLOW_QUERIES: IncidentTemplate(
                category=IncidentCategory.DATABASE_SLOW_QUERIES,
                severity=IncidentSeverity.MEDIUM,
                summary_template="🚨 {service} slow database queries detected ({execution_time}ms)",
                cause_template="Slow queries likely due to {cause_context} - check for missing indexes or complex operations",
                next_step_template="Analyze query execution plans, add indexes, optimize queries",
                keywords=["slow", "query", "database", "execution", "time"],
                patterns=[
                    r"slow query.*(\d+)ms",
                    r"query.*took.*(\d+)s",
                    r"execution.*time.*(\d+)",
                    r"database.*performance"
                ],
                metadata_fields=["execution_time_ms", "query", "table", "database", "rows_examined"]
            ),
            
            IncidentCategory.API_RATE_LIMITING: IncidentTemplate(
                category=IncidentCategory.API_RATE_LIMITING,
                severity=IncidentSeverity.MEDIUM,
                summary_template="🚨 {service} rate limit exceeded ({requests} requests in {window}s)",
                cause_template="Rate limiting triggered due to {cause_context} - check for bot traffic or legitimate high usage",
                next_step_template="Review client behavior, adjust rate limits if needed, investigate source",
                keywords=["rate", "limit", "exceeded", "throttle", "requests"],
                patterns=[
                    r"rate limit.*exceeded",
                    r"(\d+).*requests.*(\d+)s",
                    r"throttle.*(\d+)ms",
                    r"rate.*limiting"
                ],
                metadata_fields=["requests_count", "time_window_seconds", "rate_limit", "client_ip", "endpoint"]
            ),
            
            IncidentCategory.API_ERROR_RATE_HIGH: IncidentTemplate(
                category=IncidentCategory.API_ERROR_RATE_HIGH,
                severity=IncidentSeverity.HIGH,
                summary_template="🚨 {service} high error rate ({error_rate}% errors)",
                cause_template="High error rate likely due to {cause_context} - check for service issues or dependency failures",
                next_step_template="Check service health, review error logs, verify dependencies",
                keywords=["error", "rate", "high", "failure", "api"],
                patterns=[
                    r"error rate.*(\d+)%",
                    r"high.*error.*rate",
                    r"failure.*rate",
                    r"api.*errors"
                ],
                metadata_fields=["error_rate", "success_rate", "endpoint", "method", "response_code"]
            ),
            
            IncidentCategory.AUTHENTICATION_FAILURES: IncidentTemplate(
                category=IncidentCategory.AUTHENTICATION_FAILURES,
                severity=IncidentSeverity.MEDIUM,
                summary_template="🚨 {service} authentication failures detected ({failures} failed attempts)",
                cause_template="Authentication failures likely due to {cause_context} - check for credential issues or security threats",
                next_step_template="Review failed attempts, check for brute force attacks, verify credentials",
                keywords=["authentication", "failed", "login", "credentials", "auth"],
                patterns=[
                    r"authentication.*failed",
                    r"login.*failed",
                    r"invalid.*credentials",
                    r"auth.*failure"
                ],
                metadata_fields=["failure_reason", "username", "client_ip", "attempt_count", "threat_level"]
            ),
            
            IncidentCategory.SECURITY_SUSPICIOUS_ACTIVITY: IncidentTemplate(
                category=IncidentCategory.SECURITY_SUSPICIOUS_ACTIVITY,
                severity=IncidentSeverity.HIGH,
                summary_template="🚨 {service} suspicious activity detected from {source_ip}",
                cause_template="Suspicious activity likely due to {cause_context} - check for potential security threats",
                next_step_template="Review activity logs, block IP if necessary, investigate further",
                keywords=["suspicious", "security", "threat", "attack", "malicious"],
                patterns=[
                    r"suspicious.*activity",
                    r"security.*threat",
                    r"malicious.*activity",
                    r"attack.*detected"
                ],
                metadata_fields=["source_ip", "threat_level", "failed_attempts", "endpoints_accessed", "action_taken"]
            ),
            
            IncidentCategory.SERVICE_HEALTH_CHECK_FAILURE: IncidentTemplate(
                category=IncidentCategory.SERVICE_HEALTH_CHECK_FAILURE,
                severity=IncidentSeverity.HIGH,
                summary_template="🚨 {service} health check failed ({response_code})",
                cause_template="Health check failure likely due to {cause_context} - check service status and dependencies",
                next_step_template="Check service logs, restart if necessary, verify dependencies",
                keywords=["health", "check", "failed", "unhealthy", "service"],
                patterns=[
                    r"health check.*failed",
                    r"service.*unhealthy",
                    r"health.*(\d+)",
                    r"backend.*unhealthy"
                ],
                metadata_fields=["response_code", "response_time_ms", "backend_server", "consecutive_failures"]
            ),
            
            IncidentCategory.CACHE_MEMORY_PRESSURE: IncidentTemplate(
                category=IncidentCategory.CACHE_MEMORY_PRESSURE,
                severity=IncidentSeverity.MEDIUM,
                summary_template="🚨 {service} cache memory pressure ({memory_percent}% usage)",
                cause_template="Cache memory pressure likely due to {cause_context} - check for memory leaks or insufficient allocation",
                next_step_template="Check cache configuration, restart cache service, increase memory if needed",
                keywords=["cache", "memory", "pressure", "redis", "eviction"],
                patterns=[
                    r"cache.*memory.*(\d+)%",
                    r"redis.*memory.*pressure",
                    r"eviction.*policy",
                    r"cache.*full"
                ],
                metadata_fields=["memory_usage_percent", "eviction_policy", "keys_evicted", "hit_rate"]
            ),
            
            IncidentCategory.EXTERNAL_SERVICE_TIMEOUT: IncidentTemplate(
                category=IncidentCategory.EXTERNAL_SERVICE_TIMEOUT,
                severity=IncidentSeverity.HIGH,
                summary_template="🚨 {service} external service timeout ({timeout}s)",
                cause_template="External service timeout likely due to {cause_context} - check network connectivity and service availability",
                next_step_template="Check network connectivity, verify external service status, implement retry logic",
                keywords=["timeout", "external", "service", "connection", "network"],
                patterns=[
                    r"timeout.*(\d+)s",
                    r"external.*service.*timeout",
                    r"connection.*timeout",
                    r"network.*timeout"
                ],
                metadata_fields=["timeout_seconds", "retry_count", "endpoint", "service", "operation"]
            )
        }
    
    def get_template(self, category: IncidentCategory) -> Optional[IncidentTemplate]:
        """Get template for a specific category."""
        return self.templates.get(category)
    
    def get_all_templates(self) -> Dict[IncidentCategory, IncidentTemplate]:
        """Get all available templates."""
        return self.templates
    
    def find_matching_templates(self, log_message: str, metadata: Dict[str, Any] = None) -> List[IncidentTemplate]:
        """Find templates that match the log message and metadata."""
        matches = []
        log_lower = log_message.lower()
        
        for template in self.templates.values():
            # Check keyword matches
            keyword_matches = sum(1 for keyword in template.keywords if keyword in log_lower)
            
            # Check pattern matches
            pattern_matches = 0
            for pattern in template.patterns:
                if re.search(pattern, log_message, re.IGNORECASE):
                    pattern_matches += 1
            
            # Check metadata field matches
            metadata_matches = 0
            if metadata:
                metadata_matches = sum(1 for field in template.metadata_fields if field in metadata)
            
            # Calculate match score
            match_score = keyword_matches + pattern_matches + (metadata_matches * 0.5)
            
            if match_score > 0:
                matches.append((template, match_score))
        
        # Sort by match score and return templates
        matches.sort(key=lambda x: x[1], reverse=True)
        return [match[0] for match in matches]
    
    def get_template_by_category_name(self, category_name: str) -> Optional[IncidentTemplate]:
        """Get template by category name string."""
        try:
            category = IncidentCategory(category_name)
            return self.get_template(category)
        except ValueError:
            return None


class IncidentAnalyzer:
    """Analyzer that uses predefined templates to prevent hallucinations."""
    
    def __init__(self):
        self.registry = IncidentTemplateRegistry()
    
    def analyze_incident(self, log_message: str, metadata: Dict[str, Any] = None, 
                        service_name: str = "unknown") -> Dict[str, Any]:
        """
        Analyze an incident using predefined templates.
        
        Args:
            log_message: The log message to analyze
            metadata: Additional metadata from the log
            service_name: Name of the service experiencing the issue
            
        Returns:
            Dictionary with structured incident analysis
        """
        if metadata is None:
            metadata = {}
        
        # Find matching templates
        matching_templates = self.registry.find_matching_templates(log_message, metadata)
        
        if not matching_templates:
            # Fallback to generic analysis
            return self._create_generic_analysis(log_message, metadata, service_name)
        
        # Use the best matching template
        best_template = matching_templates[0]
        
        # Extract context from log message and metadata
        context = self._extract_context(log_message, metadata, best_template)
        
        # Generate structured response
        return {
            "category": best_template.category.value,
            "severity": best_template.severity.value,
            "summary": self._format_template(best_template.summary_template, context, service_name),
            "cause": self._format_template(best_template.cause_template, context, service_name),
            "next_step": self._format_template(best_template.next_step_template, context, service_name),
            "confidence": self._calculate_confidence(matching_templates, log_message, metadata),
            "template_used": best_template.category.value,
            "alternative_categories": [t.category.value for t in matching_templates[1:3]]  # Top 3 alternatives
        }
    
    def _extract_context(self, log_message: str, metadata: Dict[str, Any], 
                        template: IncidentTemplate) -> Dict[str, Any]:
        """Extract relevant context from log message and metadata."""
        context = {}
        
        # Extract values from metadata
        for field in template.metadata_fields:
            if field in metadata:
                context[field] = metadata[field]
        
        # Extract values using regex patterns
        for pattern in template.patterns:
            match = re.search(pattern, log_message, re.IGNORECASE)
            if match:
                groups = match.groups()
                if groups:
                    # Use the first captured group as a generic value
                    context["extracted_value"] = groups[0]
        
        # Extract common patterns
        if "cpu" in template.category.value:
            cpu_match = re.search(r"(\d+)%", log_message)
            if cpu_match:
                context["cpu_percent"] = cpu_match.group(1)
        
        if "memory" in template.category.value:
            memory_match = re.search(r"(\d+)%", log_message)
            if memory_match:
                context["memory_percent"] = memory_match.group(1)
        
        if "disk" in template.category.value:
            disk_match = re.search(r"(\d+)%", log_message)
            if disk_match:
                context["disk_percent"] = disk_match.group(1)
        
        # Add generic cause context
        context["cause_context"] = self._infer_cause_context(log_message, metadata)
        
        return context
    
    def _infer_cause_context(self, log_message: str, metadata: Dict[str, Any]) -> str:
        """Infer cause context from log message and metadata."""
        log_lower = log_message.lower()
        
        if "timeout" in log_lower:
            return "network connectivity issues or service overload"
        elif "connection" in log_lower and "pool" in log_lower:
            return "high concurrent load or connection leaks"
        elif "memory" in log_lower:
            return "memory leaks or insufficient allocation"
        elif "disk" in log_lower:
            return "log accumulation or data growth"
        elif "rate limit" in log_lower:
            return "excessive requests or bot traffic"
        elif "authentication" in log_lower or "login" in log_lower:
            return "invalid credentials or security threats"
        elif "suspicious" in log_lower:
            return "potential security threats or malicious activity"
        else:
            return "system resource constraints or service issues"
    
    def _format_template(self, template: str, context: Dict[str, Any], service_name: str) -> str:
        """Format template string with context values."""
        # Add default values for common template variables
        safe_context = {
            "service": service_name,
            "cpu_percent": context.get("cpu_percent", "unknown"),
            "memory_percent": context.get("memory_percent", "unknown"),
            "disk_percent": context.get("disk_percent", "unknown"),
            "active": context.get("active_connections", context.get("active", "unknown")),
            "max": context.get("pool_size", context.get("max", "unknown")),
            "requests": context.get("requests_count", "unknown"),
            "window": context.get("time_window_seconds", "unknown"),
            "error_rate": context.get("error_rate", "unknown"),
            "failures": context.get("failed_attempts", "unknown"),
            "source_ip": context.get("source_ip", "unknown"),
            "response_code": context.get("response_code", "unknown"),
            "timeout": context.get("timeout_seconds", "unknown"),
            "execution_time": context.get("execution_time_ms", "unknown"),
            "cause_context": context.get("cause_context", "system issues"),
            **context
        }
        
        try:
            formatted = template.format(**safe_context)
            return formatted
        except KeyError as e:
            # Fallback to basic formatting if template variables are missing
            logger.warning(f"Template formatting failed for variable {e}, using fallback")
            return template.replace("{service}", service_name).replace("{cause_context}", context.get("cause_context", "system issues"))
    
    def _calculate_confidence(self, matching_templates: List[IncidentTemplate], 
                            log_message: str, metadata: Dict[str, Any]) -> float:
        """Calculate confidence score based on template matches."""
        if not matching_templates:
            return 0.3  # Low confidence for no matches
        
        best_template = matching_templates[0]
        
        # Base confidence from template match quality
        base_confidence = 0.7
        
        # Boost confidence if we have relevant metadata
        metadata_boost = 0.0
        if metadata:
            relevant_fields = sum(1 for field in best_template.metadata_fields if field in metadata)
            metadata_boost = min(0.2, relevant_fields * 0.05)
        
        # Boost confidence if multiple templates match (indicates clear pattern)
        pattern_boost = 0.0
        if len(matching_templates) > 1:
            pattern_boost = min(0.1, (len(matching_templates) - 1) * 0.05)
        
        return min(1.0, base_confidence + metadata_boost + pattern_boost)
    
    def _create_generic_analysis(self, log_message: str, metadata: Dict[str, Any], 
                               service_name: str) -> Dict[str, Any]:
        """Create generic analysis when no templates match."""
        return {
            "category": "unknown",
            "severity": "medium",
            "summary": f"🚨 {service_name} experiencing issues - manual review required",
            "cause": "Unable to categorize automatically - check logs for specific error details",
            "next_step": "Review log details manually and escalate if critical",
            "confidence": 0.3,
            "template_used": "generic_fallback",
            "alternative_categories": []
        }
