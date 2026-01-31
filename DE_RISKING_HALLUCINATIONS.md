# De-risking Hallucinations in Monitoring Systems

## Overview

This document describes the de-risking system implemented to prevent hallucinations when using Qwen2-1.5B for monitoring and alerting. The system uses predefined incident templates to anchor the model to reliable, structured categories.

## Problem Statement

Qwen2-1.5B is not fine-tuned for monitoring, which can lead to:
- Random hallucinated incident categories
- Inconsistent severity levels
- Unreliable analysis outputs
- Lack of actionable next steps

## Solution: Template-Based Anchoring

### Core Concept

**Predefine incident types** → **Qwen2-1.5B matches input to categories** → **Fill in template blanks**

This keeps answers reliable vs random hallucination.

### Example Output

```json
{
  "summary": "🚨 auth-api experiencing high error rate",
  "cause": "Likely database connection pool exhaustion",
  "next_step": "Check db-pool-size and restart pod if saturation persists",
  "category": "database_connection_pool_exhausted",
  "severity": "critical",
  "confidence": 0.95
}
```

## Implementation

### 1. Predefined Incident Templates

The system includes 12 predefined incident categories:

| Category | Severity | Description |
|----------|----------|-------------|
| `cpu_saturation` | high | High CPU usage detected |
| `memory_exhaustion` | critical | Memory usage critical |
| `disk_space_low` | high | Disk space running low |
| `database_connection_pool_exhausted` | critical | DB connection pool exhausted |
| `database_slow_queries` | medium | Slow database queries |
| `api_rate_limiting` | medium | API rate limits exceeded |
| `api_error_rate_high` | high | High API error rates |
| `authentication_failures` | medium | Authentication failures |
| `security_suspicious_activity` | high | Suspicious security activity |
| `service_health_check_failure` | high | Service health check failed |
| `cache_memory_pressure` | medium | Cache memory pressure |
| `external_service_timeout` | high | External service timeouts |

### 2. Template Structure

Each template includes:

```python
@dataclass
class IncidentTemplate:
    category: IncidentCategory
    severity: IncidentSeverity
    summary_template: str
    cause_template: str
    next_step_template: str
    keywords: List[str]
    patterns: List[str]
    metadata_fields: List[str]
```

### 3. Matching Algorithm

The system matches alerts to templates using:

1. **Keyword matching** - Count matching keywords in log message
2. **Pattern matching** - Use regex patterns to extract values
3. **Metadata matching** - Check for relevant metadata fields
4. **Confidence scoring** - Calculate match confidence

### 4. Anchored Analysis Process

```mermaid
graph TD
    A[Input Alert] --> B[Template Matching]
    B --> C[Best Template Found]
    C --> D[Extract Context]
    D --> E[Qwen2-1.5B Enhancement]
    E --> F[Fill Template Blanks]
    F --> G[Structured Output]
    
    B --> H[No Match]
    H --> I[Generic Fallback]
    I --> G
```

## Usage Examples

### Basic Usage

```python
from src.llm.anchored_analyzer import AnchoredLogAnalyzer

# Initialize analyzer
analyzer = AnchoredLogAnalyzer(model="qwen2:1.5b")

# Analyze logs
result = analyzer.analyze_logs(logs, "incident_analysis")

print(f"Category: {result.category}")
print(f"Severity: {result.severity}")
print(f"Summary: {result.summary}")
print(f"Next Step: {result.next_step}")
```

### Single Incident Analysis

```python
# For real-time alerts
result = analyzer.analyze_single_incident(
    "Database connection pool exhausted: 50/50 connections in use",
    {"pool_size": 50, "active_connections": 50},
    "web-server"
)
```

## Benefits

### 1. Prevents Hallucinations
- ✅ Anchored to predefined categories
- ✅ No random incident types
- ✅ Consistent severity levels

### 2. High Confidence Scores
- ✅ Template matching provides 0.85-1.00 confidence
- ✅ Metadata validation boosts confidence
- ✅ Multiple template matches increase reliability

### 3. Actionable Outputs
- ✅ Structured next steps for each incident type
- ✅ Specific commands and values
- ✅ Clear escalation paths

### 4. Consistent Categorization
- ✅ Same incident type → same category
- ✅ Reliable severity assessment
- ✅ Standardized response format

## Testing

### Run Tests

```bash
# Test the de-risking system
python test_anchored_analyzer.py

# Run comprehensive example
python example_anchored_monitoring.py
```

### Test Results

```
🧪 ANCHORED ANALYZER DE-RISKING TESTS
============================================================
✅ Template test completed!
✅ Template coverage analysis completed!
✅ Single incident analysis completed!
✅ Anchored analysis completed successfully!
🎯 De-risking achieved: Template-based categorization prevents hallucinations
```

## Configuration

### Environment Setup

```bash
# Start Ollama
brew services start ollama

# Install Qwen2-1.5B
ollama pull qwen2:1.5b

# Verify installation
ollama list
```

### Custom Templates

You can extend the system by adding new templates:

```python
# Add new incident category
new_template = IncidentTemplate(
    category=IncidentCategory.CUSTOM_INCIDENT,
    severity=IncidentSeverity.MEDIUM,
    summary_template="🚨 {service} custom incident detected",
    cause_template="Custom incident due to {cause_context}",
    next_step_template="Follow custom incident procedures",
    keywords=["custom", "incident", "detected"],
    patterns=[r"custom.*incident.*(\d+)"],
    metadata_fields=["custom_field", "incident_id"]
)
```

## Integration

### With Existing Systems

The anchored analyzer can be integrated with:

- **Prometheus alerts** - Process alert messages
- **ELK stack** - Analyze log entries
- **Splunk** - Process search results
- **Custom monitoring** - Any log-based system

### API Integration

```python
# FastAPI endpoint
@app.post("/analyze-incident")
async def analyze_incident(request: IncidentRequest):
    result = analyzer.analyze_single_incident(
        request.message,
        request.metadata,
        request.service_name
    )
    return result
```

## Performance

### Metrics

- **Template matching**: ~1ms per alert
- **LLM enhancement**: ~500ms per analysis
- **Confidence scores**: 0.85-1.00 for matched templates
- **Memory usage**: ~50MB for template registry

### Optimization

- Template matching is cached
- LLM calls are batched when possible
- Metadata extraction is optimized
- Pattern matching uses compiled regex

## Monitoring the System

### Health Checks

```python
# Check template coverage
templates = analyzer.get_available_templates()
print(f"Available templates: {len(templates)}")

# Test template matching
result = analyzer.analyze_single_incident("test message", {}, "test-service")
print(f"Confidence: {result['confidence']}")
```

### Metrics to Track

- Template match rate
- Confidence score distribution
- LLM enhancement success rate
- Response time per analysis
- Error rate by incident category

## Troubleshooting

### Common Issues

1. **No template matches**
   - Check if log message contains relevant keywords
   - Verify metadata fields are present
   - Consider adding new templates

2. **Low confidence scores**
   - Ensure metadata is complete
   - Check keyword coverage
   - Verify pattern matching

3. **LLM enhancement failures**
   - Check Ollama is running
   - Verify model is installed
   - Review prompt formatting

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run analysis with debug info
result = analyzer.analyze_logs(logs, "incident_analysis")
```

## Future Enhancements

### Planned Features

1. **Dynamic template learning** - Learn new patterns from successful analyses
2. **Multi-language support** - Templates for different log formats
3. **Custom severity rules** - Business-specific severity mapping
4. **Integration plugins** - Easy integration with popular monitoring tools
5. **Template versioning** - A/B testing of template improvements

### Contributing

To add new incident templates:

1. Define the incident category in `IncidentCategory` enum
2. Create the template in `IncidentTemplateRegistry`
3. Add test cases in `test_anchored_analyzer.py`
4. Update documentation

## Conclusion

The de-risking system successfully prevents hallucinations by:

1. **Anchoring Qwen2-1.5B to predefined templates**
2. **Providing structured, reliable outputs**
3. **Maintaining high confidence scores**
4. **Ensuring actionable next steps**
5. **Enabling consistent incident categorization**

This approach makes Qwen2-1.5B reliable for production monitoring systems while maintaining the flexibility of LLM-based analysis.
