# AI Copilot Technical Documentation

## Overview

AI Copilot helps SRE and platform teams synthesize monitoring signals into clear, actionable
summaries. It ingests logs and metrics from common observability stacks, analyses the data with
LLM-powered agents, and surfaces the results via REST APIs and a Streamlit dashboard.

**Key capabilities**
- Unified fetcher interface for ELK, Prometheus, and Splunk
- Cloud, local, and hybrid LLM analyzers with consistent result schema
- FastAPI service exposing health checks, summaries, and targeted investigations
- Streamlit dashboard for exploration, quick actions, and trend visualization
- Pytest-backed suite with mock server to validate UI and integration flows

## Architecture at a Glance

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        AI Copilot End-to-End Flow                           │
├───────────────┬───────────────────────┬───────────────────────┬────────────┤
│  Monitoring   │   Data Connectors     │   LLM Analyzers        │  Surfaces  │
│  Systems      │   (`src/data/`)       │   (`src/llm/`)         │            │
├───────────────┼───────────────────────┼───────────────────────┼────────────┤
│ • ELK         │ • `create_fetcher()`  │ • OpenAI (`LogAnalyzer`)│ • FastAPI │
│ • Prometheus  │   returns provider-   │ • Local (`LocalLogAnalyzer`)
│ • Splunk      │   specific fetchers   │ • Hybrid (`HybridLogAnalyzer`)
├───────────────┼───────────────────────┼───────────────────────┼────────────┤
│ Logs &        │   Normalized `LogEntry` objects               │ Streamlit │
│ metrics feed  └───────────────┬───────────────────────────────┴────────────┘
│ into API                      │
├───────────────┐              ▼
│ External or   │      FastAPI service (`src/api/main.py`)
│ dashboard     │      • Dependency-injected `CopilotService`
│ clients call  │      • `/health`, `/summary/daily`, `/analysis/*`
│ endpoints     │      • Config-driven analyzer creation
└───────────────┘              │
                               ▼
                       Streamlit dashboard (`src/ui/dashboard.py`)
                       • Calls API via REST wrapper
                       • Renders insights, recommendations, metrics
```

## Codebase Layout

The top-level `README.md` summarizes quick-start tasks. This document deep-dives into the
modules that power the assistant:

- `src/api/main.py` – FastAPI entrypoint with dependency-injected `CopilotService`
- `src/data/fetchers.py` – ELK, Prometheus, and Splunk connectors sharing a common `LogEntry`
- `src/llm/` – Analyzer infrastructure, configuration utilities, and local LLM helpers
- `src/ui/dashboard.py` – Streamlit experience for analysts and on-call engineers
- `tests/` – Pytest suite (unit, UI, and integration) plus `mock_api_server.py` harness
- `LOCAL_LLM_SETUP.md`, `SECURITY.md`, `TESTING.md` – supporting operational guides

## Runtime Data Flow

1. **Source selection** – Environment variables choose a monitoring backend (`MONITORING_SYSTEM`).
2. **Fetcher provisioning** – `create_fetcher()` builds the ELK/Prometheus/Splunk client and
   normalizes provider responses into `LogEntry` dataclasses.
3. **Analysis routing** – `CopilotService` delegates to the configured analyzer (OpenAI, local
   Ollama model, or hybrid) using `src/llm/config.py` preferences.
4. **Insight packaging** – analyzers return structured summaries (`summary`, `key_insights`,
   `recommendations`, `confidence_score`, timestamps, and log counts).
5. **Surface delivery** – FastAPI endpoints serialize results for REST clients, and the Streamlit
   dashboard renders them with Plotly charts and quick action panels.

## Service Layers

### FastAPI service (`src/api/main.py`)
- Lazy-initializes `CopilotService` via dependency injection to avoid start-up failures when
  configuration is missing.
- Exposes `GET /`, `GET /health`, `POST /analyze`, `GET /summary/daily`, and scoped analysis
  endpoints for errors and performance.
- Converts HTTP requests into time windows, pulls logs via the active fetcher, and formats
  analyzer output into `AnalysisResponse` Pydantic models.
- Uses `python-dotenv` for local `.env` loading and `CORSMiddleware` for dashboard access.

### Data connectors (`src/data/fetchers.py`)
- `LogEntry` dataclass unifies log shape across providers.
- `ELKFetcher` posts range queries to Elasticsearch indices, extracting metadata and normalizing
  log levels.
- `PrometheusFetcher` converts time-series data (`query_range`) into pseudo-log events for trend
  analysis.
- `SplunkFetcher` streams exported search results, supports token-based auth, and enriches
  metadata.
- `_safe_request()` centralizes HTTP error handling with timeouts to keep API responses resilient.

### Analyzer stack (`src/llm/`)
- `LogAnalyzer` (OpenAI) wraps `openai.OpenAI` chat completions with a monitoring-focused system
  prompt and parsing helpers.
- `LocalLogAnalyzer` drives Ollama models, validates availability, and adapts parsing for less
  structured responses.
- `HybridLogAnalyzer` chooses between local and OpenAI analyzers, supporting manual overrides
  (`force_local` / `force_openai`).
- `config.py` persists analyzer preferences in `~/.ai-copilot/config.yaml` or environment
  variables, providing `validate_config()` for readiness checks.
- `create_copilot_service()` factories bundle fetchers with analyzers for notebooks or external
  services.

### Streamlit dashboard (`src/ui/dashboard.py`)
- Client-side utility `call_api()` hits the FastAPI endpoints and handles failures gracefully.
- Provides configurable time ranges and analysis types, displays insights, recommendations, and a
  Plotly gauge for confidence scores.
- Offers quick-action buttons for common analyses and expands health status using `/health`.
- Designed to run alongside `uvicorn` for interactive inspection.

## Environment Setup

1. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. **Install runtime dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Install development tooling**
   ```bash
   pip install -e ".[dev]"
   ```
4. **Populate environment variables** – copy and edit `.env.example`; key variables include
   `OPENAI_API_KEY`, `MONITORING_SYSTEM`, `ELASTICSEARCH_URL`, `PROMETHEUS_URL`, `SPLUNK_URL`, and
   provider-specific tokens.

## Running the Stack

- **API** – `uvicorn src.api.main:app --reload`
- **Dashboard** – `streamlit run src/ui/dashboard.py` (ensure the API is reachable)
- **Mock backend for UI iteration** – `python -m tests.mock_api_server` (serves realistic dummy
  payloads on port 8001)
- **Jupyter experiments** – notebooks live under `notebooks/`; launch with `jupyter lab` inside the
  activated environment.

## API Usage

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Basic service liveness message |
| `/health` | GET | Verifies monitoring connectivity via `test_connection()` |
| `/analyze` | POST | Ad-hoc analysis; accepts `analysis_type`, `time_range_hours`, `system_type` |
| `/summary/daily` | GET | Daily roll-up; `days_back` query param |
| `/analysis/errors` | GET | Focused error investigation; `hours_back` query param |
| `/analysis/performance` | GET | Performance insight; `hours_back` query param |

Example request:
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"analysis_type": "error_analysis", "time_range_hours": 12, "system_type": "elk"}'
```

Responses follow the `AnalysisResponse` schema with `summary`, `key_insights`, `recommendations`,
`confidence_score`, `analysis_timestamp`, and `log_count` fields.

## Local & Hybrid LLM Configuration

- Follow `LOCAL_LLM_SETUP.md` for Ollama installation, model downloads, and troubleshooting.
- Use environment variables or `~/.ai-copilot/config.yaml` to switch providers:
  - `AI_COPILOT_PROVIDER` = `local` | `openai` | `hybrid`
  - `AI_COPILOT_LOCAL_MODEL` for Ollama model tags (e.g., `qwen2:1.5b`)
  - `AI_COPILOT_ENABLE_HYBRID=true` to allow automatic fallbacks
- `hello_llm_local.py` offers a realistic sample workload for validating local inference before
  wiring it into the API.

## Testing & Quality Assurance

- Run the full suite with `pytest` (default target discovers tests under `tests/`).
- UI-specific tests (`tests/test_dashboard_ui.py`, `tests/test_dashboard_integration.py`) exercise
  dashboard behaviors using the mock API server and Streamlit components.
- `tests/test_fetchers.py` validates connector factories and dataclass behavior without hitting live
  services.
- Prefer adding new fixtures or mocked responses in `tests/mock_api_server.py` when backend
  contracts change.
- Format code with `black .` and lint with `flake8` before proposing changes.

## Security & Compliance

- Review `SECURITY.md` and run `./security-check.sh` when introducing endpoints or dependencies.
- Keep secrets out of source control; document new variables in `.env.example` and reference them in
  this documentation as needed.
- For hardened deployments, install `requirements-secure.txt` and audit third-party services accessed
  by fetchers.

## Contribution Workflow

- Follow the style and testing guidance in `AGENTS.md`.
- Use feature branches, keep commit subjects imperative, and separate refactors from behavioral
  changes.
- Include Pytest output in PR descriptions and attach dashboard screenshots or GIFs for UI updates.
- When changing monitoring integrations, update this documentation alongside relevant setup guides.

## Additional Resources

- `DE_RISKING_ARCHITECTURE.md` & `DE_RISKING_HALLUCINATIONS.md` – risk mitigation strategies for the
  AI layer.
- `LINEAR_INTEGRATION.md` – outlines backlog synchronization with Linear.
- `TESTING.md` – canonical test plans and coverage expectations.
- `wiki-setup.md` – instructions for mirroring documentation to internal wikis.

Maintaining this document alongside the codebase ensures onboarding, audits, and incident response
remain fast as the AI Copilot evolves.
