# De-risking Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DE-RISKING SYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   INPUT ALERT   │───▶│ TEMPLATE MATCHER│───▶│ QWEN2-1.5B  │ │
│  │                 │    │                 │    │             │ │
│  │ "DB pool        │    │ • Keywords      │    │ • Fill      │ │
│  │  exhausted"     │    │ • Patterns      │    │   blanks    │ │
│  │                 │    │ • Metadata      │    │ • Enhance   │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│           │                       │                     │       │
│           │                       ▼                     │       │
│           │              ┌─────────────────┐            │       │
│           │              │ BEST TEMPLATE   │            │       │
│           │              │                 │            │       │
│           │              │ • Category      │            │       │
│           │              │ • Severity      │            │       │
│           │              │ • Templates     │            │       │
│           │              └─────────────────┘            │       │
│           │                       │                     │       │
│           │                       ▼                     │       │
│           │              ┌─────────────────┐            │       │
│           │              │ CONTEXT EXTRACT │            │       │
│           │              │                 │            │       │
│           │              │ • Values        │            │       │
│           │              │ • Metadata      │            │       │
│           │              │ • Cause context │            │       │
│           │              └─────────────────┘            │       │
│           │                       │                     │       │
│           │                       ▼                     │       │
│           │              ┌─────────────────┐            │       │
│           │              │ TEMPLATE FILL   │◀───────────┘       │
│           │              │                 │                    │
│           │              │ • Summary       │                    │
│           │              │ • Cause         │                    │
│           │              │ • Next Step     │                    │
│           │              └─────────────────┘                    │
│           │                       │                             │
│           └───────────────────────▼─────────────────────────────┘
│                           ┌─────────────────┐
│                           │ STRUCTURED      │
│                           │ OUTPUT          │
│                           │                 │
│                           │ • Category      │
│                           │ • Severity      │
│                           │ • Summary       │
│                           │ • Cause         │
│                           │ • Next Step     │
│                           │ • Confidence    │
│                           └─────────────────┘
└─────────────────────────────────────────────────────────────────┘
```

## Template Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                    INCIDENT TEMPLATES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CRITICAL SEVERITY:                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ Memory Exhaustion   │  │ DB Pool Exhausted   │              │
│  │ • OOM killer        │  │ • Connection leaks  │              │
│  │ • Memory leaks      │  │ • High load         │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
│  HIGH SEVERITY:                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ CPU Saturation      │  │ Disk Space Low      │              │
│  │ • High usage        │  │ • Log accumulation  │              │
│  │ • Load average      │  │ • Data growth       │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ API Error Rate      │  │ Security Activity   │              │
│  │ • Service issues    │  │ • Suspicious IPs    │              │
│  │ • Dependency fails  │  │ • Failed attempts   │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ Health Check Fail   │  │ External Timeout    │              │
│  │ • Service down      │  │ • Network issues    │              │
│  │ • Backend unhealthy │  │ • Service overload  │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
│  MEDIUM SEVERITY:                                               │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ API Rate Limiting   │  │ Auth Failures       │              │
│  │ • Bot traffic       │  │ • Invalid creds     │              │
│  │ • High usage        │  │ • Security threats  │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ Slow Queries        │  │ Cache Pressure      │              │
│  │ • Missing indexes   │  │ • Memory leaks      │              │
│  │ • Complex ops       │  │ • Insufficient RAM  │              │
│  └─────────────────────┘  └─────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
INPUT: "Database connection pool exhausted: 50/50 connections in use, queue depth: 127"
│
├─ Template Matching
│  ├─ Keywords: ["connection", "pool", "exhausted"] ✓
│  ├─ Patterns: [r"connection.*pool.*exhausted"] ✓
│  └─ Metadata: ["pool_size", "active_connections"] ✓
│
├─ Best Match: database_connection_pool_exhausted
│  ├─ Severity: critical
│  ├─ Confidence: 0.95
│  └─ Template: "🚨 {service} database connection pool exhausted ({active}/{max} connections)"
│
├─ Context Extraction
│  ├─ active: 50
│  ├─ max: 50
│  ├─ queue_depth: 127
│  └─ cause_context: "high concurrent load or connection leaks"
│
├─ Qwen2-1.5B Enhancement
│  ├─ Input: Template + Context + Logs
│  ├─ Task: Fill in specific details
│  └─ Output: Enhanced cause and next steps
│
└─ Structured Output
   ├─ Category: database_connection_pool_exhausted
   ├─ Severity: critical
   ├─ Summary: "🚨 web database connection pool exhausted (50/50 connections)"
   ├─ Cause: "Connection pool exhaustion likely due to high concurrent load or connection leaks"
   ├─ Next Step: "Check for connection leaks, restart service, increase pool size if needed"
   └─ Confidence: 1.00
```

## Benefits

```
┌─────────────────────────────────────────────────────────────────┐
│                        BENEFITS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🛡️  PREVENTS HALLUCINATIONS                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ ✅ Anchored to predefined categories                        │ │
│  │ ✅ No random incident types                                 │ │
│  │ ✅ Consistent severity levels                               │ │
│  │ ✅ Reliable categorization                                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  🎯 HIGH CONFIDENCE SCORES                                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ ✅ Template matching: 0.85-1.00 confidence                 │ │
│  │ ✅ Metadata validation boosts confidence                    │ │
│  │ ✅ Multiple template matches increase reliability           │ │
│  │ ✅ Pattern matching provides strong signals                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ⚡ ACTIONABLE OUTPUTS                                          │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ ✅ Structured next steps for each incident type             │ │
│  │ ✅ Specific commands and values                             │ │
│  │ ✅ Clear escalation paths                                   │ │
│  │ ✅ Context-aware recommendations                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  🔄 CONSISTENT CATEGORIZATION                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ ✅ Same incident type → same category                       │ │
│  │ ✅ Reliable severity assessment                             │ │
│  │ ✅ Standardized response format                             │ │
│  │ ✅ Predictable behavior                                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Files

```
src/llm/
├── incident_templates.py      # Predefined incident templates
├── anchored_analyzer.py       # Main anchored analyzer
└── local_analyzer.py          # Base LLM analyzer

test_anchored_analyzer.py      # Comprehensive tests
example_anchored_monitoring.py # Usage examples
DE_RISKING_HALLUCINATIONS.md   # Documentation
DE_RISKING_ARCHITECTURE.md     # This file
```

## Usage

```python
# Initialize
analyzer = AnchoredLogAnalyzer(model="qwen2:1.5b")

# Analyze logs
result = analyzer.analyze_logs(logs, "incident_analysis")

# Single incident
result = analyzer.analyze_single_incident(
    "Database connection pool exhausted: 50/50 connections in use",
    {"pool_size": 50, "active_connections": 50},
    "web-server"
)

# Get available templates
templates = analyzer.get_available_templates()
```

## Testing

```bash
# Run tests
python test_anchored_analyzer.py

# Run examples
python example_anchored_monitoring.py
```

This architecture ensures reliable, hallucination-free monitoring analysis while leveraging the power of Qwen2-1.5B for specific detail enhancement.
