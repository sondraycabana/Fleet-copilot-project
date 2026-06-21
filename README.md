#  Rayda Agentic Fleet Copilot — Senior Assessment Submission

This repository contains a production-grade, multi-agent orchestrator for Rayda's enterprise IT fleet telemetry data. Built using LangGraph, FastAPI, and DuckDB, the system handles complex time-series queries while enforcing strict tenant isolation boundaries and safety guardrails.

---

##  Core Agent Architecture & System Topology

The platform rejects fragile single-prompt scripts or simple Text-to-SQL wrappers. Instead, it relies on a **compiled LangGraph state machine graph** to pass state variables via plain Python dictionary envelopes. This ensures predictable behavior while maintaining flexibility during runtime.

### Specialized Agents Matrix
 **Planner Agent (`planner_node`)**: The central orchestrator. It parses intent, checks tenant metadata, and sets target sub-agent routing paths via conditional graph edge functions (`router_edge`).
 **Telemetry Agent (`telemetry_node`)**: Focuses on point-in-time snapshot processing, device properties lookup checks, and fast compliance queries.
 **Analytics Agent (`analytics_node`)**: Handles multi-day time-series aggregations, performance saturation metrics, and system trend exploration.
 **Action Agent (`action_node`)**: Safely stages configuration changes, flags assets, and issues employee warnings behind an administrative manual hold gate.

---

## 🛠️ Tool Catalog

The platform splits execution tasks into specific, parameter-bound analytical utilities:

### Telemetry & Diagnostics (Read Operations)
 **`check_compliance_failures`**: Scans table arrays to locate point-in-time devices matching security compliance anomalies.
 **`query_low_storage_devices`**: Analyzes space parameters across system storage partitions, surfacing entries with high storage saturation (`> 90%`).
 **`query_os_versions_tool`**: Evaluates system properties via string slicing to calculate devices running legacy operating systems older than macOS 15 or Windows 11.

### Insight & Multi-Day Trends (Read Operations)
 **`analyze_battery_degradation_tool`**: Scans 30-day historical time-series datasets to catch cells approaching end-of-life (`Cycle Count > 500` or flagging a `Service Condition`).
 **`detect_memory_saturation_tool`**: Measures continuous rolling averages across snapshots to identify resource bottlenecks where RAM usage consistently exceeds `85%`.
 **`calculate_compliance_drift_tool`**: **Mandated Trend Metric**. Groups failing snapshot events chronologically across daily intervals to measure changes in the fleet's overall security posture.

### Staged Operational Actions (Write Operations)
 **`create_upgrade_order`**: Stages a hardware component modification ticket for a device.
 **`open_remediation_ticket`**: Queues an issue tracker item to deploy compliance patch rings.
 **`flag_device_for_replacement`**: Flags severely degraded assets approaching critical wear limits.
 **`notify_employee`**: Triggers communication webhooks requesting a client-side machine reboot.

---

##  Security Architecture & Guardrails

### 1. Grounding & Anti-Hallucination Strategy
The system follows a strict rule: **if data is missing from the database, the LLM cannot invent a response.** Raw tool rows pulled from DuckDB are injected directly into the state channels under a dedicated `### Telemetry Database Evidence Context` flag wrapper block. This ensures that final text answers are fully grounded, completely traceable, and contain direct citations of hardware IDs and telemetry parameters.

### 2. Multi-Tenant Perimeter Guardrails
Isolation boundaries are enforced at the API request perimeter using case-insensitive, whitespace-trimmed SQL logic (`WHERE LOWER(TRIM(company_id)) = ?`). Cross-tenant request strings instantly trigger the `guardrail_node` interceptor and drop the query before any analytical tool script can run.

### 3. Human-In-The-Loop (HITL) Execution Locks
State-changing operational actions can never execute automatically on the fleet runtime interface. The agent captures parameters and generates a trackable token (`act-`). The transaction is saved inside a `PENDING_APPROVAL` queue and written directly to a physical non-repudiation audit ledger (`logs/audit.log`). The parameter is held in a paused state until an administrator hits the explicit `/action/approve` API release gate.

---

##  Installation, Ingestion & Live Execution

### Prerequisites
 Python 3.12+ (Ubuntu/Latitude verified environments) or Docker Engine / Compose installed.
 A valid `OPENAI_API_KEY` exported in your local environment.

### Option A: Local Virtual Environment Setup
```bash
# Clone the repository and enter the project root directory
git clone https://github.com
cd fleet-copilot

# Instantiate python virtual environment binary engine
python3 -m venv venv
source venv/bin/activate

# Install dependencies pinned for production safety
pip install -r requirements.txt
```

Create a local `.env` configuration file in the project's root folder space:
```env
OPENAI_API_KEY=sk-or-v1-YOUR_ACTUAL_OPENROUTER_SECRET_KEY
OPENAI_BASE_URL=https://openrouter.ai
DATABASE_PATH=data/fleet_telemetry.db
LOG_PATH=logs/audit.log
```

Before launching the server locally, place your dataset in the `data/` directory and run the initialization script to ingest records into DuckDB:
```bash
mkdir -p data logs
cp /path/to/your/telemetry.jsonl data/telemetry.jsonl

# Ingest records to initialize data structures
python -c "from services.telemetry_service import TelemetryService; TelemetryService().ingest_jsonl('data/telemetry.jsonl')"

# Launch the application server process using Uvicorn
./venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Option B: Containerised Execution via Docker Compose
For production parity and seamless reproducibility without local Python environment installation dependencies, you can build and run the entire application stack via Docker Compose:

```bash
# 1. Export your OpenRouter credentials into your active shell environment
export OPENAI_API_KEY=sk-or-v1-YOUR_ACTUAL_OPENROUTER_SECRET_KEY
export ENVIRONMENT=production

# 2. Spin up the container stack in detached mode
docker compose up --build -d

# 3. Stream live application log updates
docker compose logs -f
```

#### Persistent Volumes Configuration
The orchestration layout safely maps two persistent structural volume locations from your host machine into the running container:
 `./data`  Maps to `/app/data` inside the container to persist your DuckDB (`fleet_telemetry.db`) analytical warehouse records.
 `./logs`  Maps to `/app/logs` to allow human reviewers to read or tail the physical `audit.log` non-repudiation ledger files directly from the host terminal.

---

##  Runnable Evaluation Suite

The project includes an automated `pytest` verification matrix suite. This suite fires runtime HTTP requests against your endpoints to dynamically confirm multi-tenant separation guardrails, data grounding, and token lifecycles.

Ensure the application stack is running on **port 8000** (via either Option A or Option B), open a separate terminal tab, and run:

```bash
PYTHONPATH=. ./venv/bin/pytest tests/ -v --asyncio-mode=auto
```

### Expected Output Matrix Pass Trace:
```text
============================= test session starts ==============================
collected 6 items                                                              

tests/test_actions.py::test_action_staging_and_approval_gate_lifecycle PASSED [ 16%]
tests/test_grounding.py::test_grounded_compliance_query PASSED           [ 33%]
tests/test_guardrails.py::test_tenant_boundary_isolation_guardrail PASSED [ 50%]
tests/test_trends.py::test_battery_end_of_life_trend_query PASSED        [ 66%]
tests/test_trends.py::test_chronic_ram_constraint_trend_query PASSED     [ 83%]
tests/test_trends.py::test_historical_compliance_drift_trend_query PASSED [100%]

============================== 6 passed in 14.55s ==============================
```

---

##  Key Design Decisions & Architectural Trade-offs

### 1. Embedded Analytical Storage (DuckDB) vs. Vector RAG Over Raw JSON Lines
 **Decision**: We chose to flatten nested telemetry JSON lines and load them into a relational schema inside DuckDB rather than chunking text files into an alternative Vector DB embedding engine.
 **Trade-off**: This adds a minor verification step during startup, but completely avoids context window bloat. It enables exact SQL aggregations across hundreds of time-series objects while minimizing token expenditure and preventing hallucinations.

### 2. Standard Native State Context Channels vs. Strict Pydantic Models
 **Decision**: We used standard Python dictionary type definitions for LangGraph state values instead of deep Pydantic validation structures.
 **Trade-off**: This approach simplifies complex data mapping adjustments while keeping the underlying framework from triggering unexpected cross-provider serialization crashes during network completion transactions.
