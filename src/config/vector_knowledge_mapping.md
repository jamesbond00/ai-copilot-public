# Vector.dev Knowledge Mapping for SED RAG System

## Overview
This configuration defines how SED should index Vector.dev documentation and GitHub issues to provide contextual information for error diagnosis.

## Knowledge Sources

### 1. Vector Documentation
**Source**: https://vector.dev/docs/
**Index Strategy**: 
- Crawl all documentation pages
- Extract sections on:
  - Sinks (especially HTTP, Elasticsearch, S3)
  - Sources (internal_logs, internal_metrics)
  - Transforms (remap, filter)
  - Configuration reference
  - Troubleshooting guides

**Embedding Strategy**:
- Chunk by documentation section (H2/H3 headers)
- Include code examples in chunks
- Tag with: `source:vector-docs`, `category:<component-type>`

**Update Frequency**: Weekly

### 2. Vector GitHub Issues
**Source**: https://github.com/vectordotdev/vector/issues
**Index Strategy**:
- Index closed issues with labels: `bug`, `sink`, `source`, `transform`
- Focus on issues with resolutions
- Extract:
  - Issue title and description
  - Resolution comments
  - Related PRs

**Embedding Strategy**:
- Chunk by issue (title + description + resolution)
- Tag with: `source:vector-issues`, `status:<open|closed>`, `labels:<label-list>`

**Update Frequency**: Daily (for new issues)

### 3. Vector Release Notes
**Source**: https://github.com/vectordotdev/vector/releases
**Index Strategy**:
- Index breaking changes and bug fixes
- Track version-specific issues

**Embedding Strategy**:
- Chunk by version
- Tag with: `source:vector-releases`, `version:<version-number>`

**Update Frequency**: On new releases

## Retrieval Strategy

### Query Enhancement
When a Vector error is detected:
1. Extract component type (sink, source, transform)
2. Extract error code (403, 500, etc.)
3. Extract component name

### Search Query Construction
```
Query: "{error_message} {component_type} {error_code}"
Filters: 
  - source: vector-docs OR vector-issues
  - category: {component_type}
Top K: 5
```

### Context Injection
Retrieved documents are injected into the LLM prompt:
```
Based on Vector documentation and known issues:
{retrieved_context}

Analyze this error:
{error_message}
```

## Implementation

### ChromaDB Collection
- Collection Name: `vector_knowledge`
- Embedding Model: `sentence-transformers/all-MiniLM-L6-v2`
- Distance Metric: Cosine similarity

### Metadata Schema
```json
{
  "source": "vector-docs | vector-issues | vector-releases",
  "url": "https://...",
  "title": "...",
  "category": "sink | source | transform | config",
  "component_name": "http | elasticsearch | ...",
  "version": "0.35.0",
  "issue_number": 8821,
  "status": "open | closed"
}
```

## Example Queries

### Query 1: Sink Failure
```
Error: "HTTP sink failed with 403"
Enhanced Query: "HTTP sink 403 forbidden authentication"
Filters: category:sink, source:vector-docs OR vector-issues
Expected Results:
  - Vector HTTP sink authentication docs
  - GitHub issue #8821 (credential rotation bug)
  - Troubleshooting guide for sink failures
```

### Query 2: Schema Mismatch
```
Error: "Schema validation failed for field 'timestamp'"
Enhanced Query: "schema validation timestamp type mismatch"
Filters: category:transform OR category:sink
Expected Results:
  - Remap transform documentation
  - Type coercion examples
  - Related schema issues
```

## Maintenance

### Scripts
- `scripts/index_vector_docs.py` - Crawl and index Vector docs
- `scripts/index_vector_issues.py` - Index GitHub issues
- `scripts/update_vector_knowledge.py` - Incremental updates

### Monitoring
- Track retrieval accuracy (manual review of top-5 results)
- Monitor query latency
- Alert on stale data (>7 days old)
