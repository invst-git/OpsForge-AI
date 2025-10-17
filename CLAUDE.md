# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpsForge AI is an autonomous AI operations platform that uses multiple specialized agents powered by Anthropic's Claude (via Strands framework) to handle incident correlation, predictive analysis, automated patching, and task orchestration. The system consists of a Python backend with FastAPI, a React frontend, and AWS Lambda deployment capabilities.

## Architecture

### Agent System (agents/)
The core intelligence is distributed across 5 specialized agents that collaborate on incident response:

- **Orchestrator** (`agents/orchestrator.py`): Coordinates other agents, provides unified decision synthesis. Uses perception, memory, and learning modules.
- **AlertOps** (`agents/alert_ops.py`): Correlates related alerts using graph-based analysis, accesses historical incident patterns.
- **PredictiveOps** (`agents/predictive_ops.py`): Forecasts issues from metrics using trend analysis.
- **PatchOps** (`agents/patch_ops.py`): Manages safe patching with canary deployments.
- **TaskOps** (`agents/task_ops.py`): Handles task automation and workflow execution.
- **ExecutionOrchestrator** (`agents/execution_orchestrator.py`): Manages action execution flow.

All agents use the Strands framework and are configured with Claude Sonnet 4 model ID: `us.anthropic.claude-sonnet-4-20250514-v1:0`

### Agent Capabilities (config/)
Enhanced cognitive functions shared across agents:

- **KnowledgeBase** (`config/knowledge_base.py`): Persistent storage for incidents, patterns, and agent knowledge. Supports both local (dict-based) and DynamoDB modes.
- **AgentPerception** (`config/perception.py`): Context-aware perception of alerts and metrics.
- **AgentLearning** (`config/learning.py`): Learn from outcomes to improve decisions over time.
- **ActionExecutor** (`config/action_executor.py`): Executes actions like service restarts, patch deployments.

### Tools (tools/)
Specialized tools available to agents via Strands `@tool` decorator:

- `correlation.py`: Graph-based alert correlation using NetworkX
- `prediction.py`: Time-series forecasting
- `patch_ops.py`: Patch management operations
- `task_ops.py`: Task automation tools

### Data Models (data/)
- `models.py`: Pydantic models for Alert, Metric, Severity, AlertStatus, CorrelationResult
- `alert_simulator.py`, `metrics_simulator.py`: Generate realistic test data

### API Layer
- **Backend** (`backend_api.py`): FastAPI server on port 8000, provides REST endpoints for metrics, agents, incidents, patches, audit logs
- **Frontend** (`frontend/`): React + Vite dashboard on port 5173, visualizes agent activity and incidents

### AWS Deployment (aws/)
- `lambda_handler.py`: Lambda entry point, processes alerts/metrics/incidents
- `template.yaml`: SAM template for infrastructure (DynamoDB tables, Lambda, API Gateway)

## Common Commands

### Development Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies for frontend
npm install
```

### Running the System
```bash
# Start backend API (port 8000)
python backend_api.py

# Start frontend dev server (port 5173) - in separate terminal
cd frontend
npm run dev

# Run live data generator (generates test incidents)
python live_data_generator.py
```

### Testing
```bash
# Test individual agents
python test_alert_ops.py
python test_predictive_ops.py
python test_patch_ops.py
python test_task_ops.py
python test_orchestrator.py
python test_enhanced_agents.py

# Test knowledge base and learning
python test_knowledge_base.py

# Test AWS Lambda locally
python test_lambda_local.py

# Test Strands agents connection
python test_strands.py

# Test Bedrock connection
python test_bedrock.py

# Verify complete setup
python verify_setup.py
```

### AWS Deployment
```powershell
# Package Lambda function
.\package_lambda.bat

# Deploy to AWS (requires AWS CLI and SAM CLI)
.\deploy.ps1
```

## Key Patterns

### Agent Invocation
Agents are created using the Strands framework:
```python
from strands import Agent
agent = Agent(
    name="AgentName",
    model=os.getenv("STRANDS_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
    tools=[tool1, tool2],
    system_prompt="..."
)
response = agent("Your prompt here")
```

### Knowledge Base Usage
The knowledge base supports incident memory and pattern learning:
```python
from config.knowledge_base import kb

# Store incident
incident_id = kb.store_incident({
    "alerts": [...],
    "root_cause": "...",
    "outcome": "pending"
})

# Retrieve similar incidents
similar = kb.get_similar_incidents(["keyword1", "keyword2"], limit=5)

# Store agent knowledge
kb.store_agent_knowledge("AgentName", "key", {"data": "value"})
```

### Full Incident Processing Pipeline
The `EnhancedOrchestrator` implements: Perceive → Reason → Act → Learn
```python
from agents.orchestrator import enhanced_orchestrator
result = enhanced_orchestrator.handle_incident_full(alerts, metrics)
```

## Environment Variables

Required in `.env`:
- `AWS_REGION`: AWS region (default: us-east-1)
- `STRANDS_MODEL_ID`: Claude model ID for Strands agents
- `ENVIRONMENT`: development/production
- `LOG_LEVEL`: INFO/DEBUG/WARNING

## Data Flow

1. **Alerts/Metrics** → `backend_api.py` endpoints or `lambda_handler.py`
2. **AlertOps** correlates alerts using `tools/correlation.py` (graph analysis)
3. **PredictiveOps** analyzes metrics trends
4. **Orchestrator** synthesizes insights, consults knowledge base
5. **ActionExecutor** executes remediation (restarts, patches)
6. Results stored in **KnowledgeBase** for learning
7. **Frontend** displays real-time agent activity and incident status

## Important Implementation Details

- **Local vs AWS Mode**: KnowledgeBase automatically uses dict-based storage in local mode (`use_local=True`), DynamoDB in production
- **Agent Memory**: All agents can access historical incidents via `kb.get_similar_incidents()` to learn from past patterns
- **Kill Switch**: API endpoint `/api/kill-switch/toggle` pauses all autonomous actions for safety
- **Correlation Algorithm**: Uses NetworkX graph with edges weighted by: same host (0.4), time proximity (0.3), keyword overlap (0.3)
- **FastAPI CORS**: Configured to allow frontend on localhost:5173

## Frontend Structure

- `frontend/src/App.jsx`: Main app with routing
- `frontend/src/pages/`: Dashboard, Incidents, Agents, Patches views
- `frontend/src/components/`: Reusable UI components
- Built with React 19, Vite, Chart.js, Lucide icons

## Testing Strategy

Each agent has a corresponding `test_*.py` file that creates synthetic data and verifies agent responses. Use these as examples when adding new agents or tools.
