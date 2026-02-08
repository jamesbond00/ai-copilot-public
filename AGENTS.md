# Agentic Orchestration Layer (Alpha)

The Agentic Orchestration Layer introduces autonomous agents to the System Diagnostics Copilot. Instead of just analyzing logs upon request, these agents can coordinate, reason like an SME (Subject Matter Expert), and use specialized tools to diagnose complex issues.

## 🏗️ Architecture

The system uses a hierarchical agent pattern:

```mermaid
graph TD
    User[User Request] --> Orchestrator[Agent Orchestrator]
    
    Orchestrator -->|Complexity?| SME[SME Agent]
    Orchestrator -->|Simple?| Direct[Direct Response]
    
    subgraph "Specialist Layer"
        SME -->|Need Logs| LogAgent[Log Analysis Agent]
        SME -->|Need Metrics| MetricAgent["Metric Agent (Planned)"]
        SME -->|Need Traces| TraceAgent["Trace Agent (Planned)"]
    end
    
    LogAgent -->|Analyze| LocalLLM[Local/Hybrid LLM]
    LogAgent -->|Fetch| Logs[Log Sources]
    
    SME -->|Query| KB[Knowledge Base (RAG)]
    KB -->|Retrieve| Wiki[Wiki / Jira / Runbooks]

    SME -->|Synthesize| Report[Diagnostic Report]
```

## 🤖 Core Agents

### 1. Agent Orchestrator (`src.agents.orchestrator`)
**Role**: The "Front Desk" and Router.
- Receives all user messages.
- Analyzes intent (e.g., "Is this a greeting or a system outage?").
- Routes complex diagnostic tasks to the SME Agent.
- Handles simple queries directly.

### 2. SME Agent (`src.agents.sme`)
**Role**: The Subject Matter Expert (Site Reliability Engineer).
- Receives diagnostic requests.
- Formulates hypotheses (e.g., "If checkout is failing, I should check the payment gateway logs").
- **Delegates** work to specialist agents (currently `LogAnalysisAgent`).
- **Synthesizes** findings into a coherent Root Cause Analysis (RCA) report.

### 3. Log Analysis Agent (`src.agents.log_agent`)
**Role**: The Log Specialist.
- Specialized in fetching and interpreting logs.
- Uses `LocalLogAnalyzer` (Qwen2/Llama3) to scan logs for errors and patterns.
- Returns structured insights (summary, error rates, confidence) to the SME Agent.

### 4. Knowledge Base (`src.knowledge.knowledge_base`)
**Role**: The Institutional Memory.
- Stores and retrieves documents using Vector RAG (ChromaDB).
- Agents can query this to find past incidents, runbooks, and architectural docs.
- See `scripts/demo_knowledge_base.py` for usage.

## 🚀 Usage

The agent layer is accessible via the `AgentOrchestrator` class.

```python
from src.agents.orchestrator import AgentOrchestrator

# Initialize the orchestrator
orchestrator = AgentOrchestrator(model="qwen2:1.5b")

# Run a diagnostic request
response = orchestrator.run("Checkout service is returning 500 errors")
print(response)
```

See `scripts/demo_agent_orchestration.py` for a runnable example.

## 🔮 Future Work

- **Tool Use**: Give agents access to real tools (Jira, GitHub, Slack) via MCP or direct integration.
- **More Specialists**: Add `MetricAgent` (Prometheus) and `TraceAgent` (Jaeger/Tempo).
- **Memory**: Implement conversation history and context retention across turns.
- **Planner**: Add a planning step for the SME Agent to decompose complex problems into parallel tasks.
