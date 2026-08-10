# 🛡️ TripMate AI — Guardrails & HITL (MCP & LangGraph)

An enterprise-grade AI travel planner that incorporates **Input Guardrails** and **Human-in-the-Loop (HITL)** approval workflows. Built with **LangGraph**, **FastAPI**, **LangChain**, and **Model Context Protocol (MCP)**, this version adds a Supervisor agent, Budget analysis, and a paused execution state to review drafts before finalizing itineraries.

---

## 🏗️ Refactored Modular Architecture

```text
travel-multi-agent-with-Guardrils/
├── config/
│   ├── settings.py              # Environment configuration, API keys, SSL settings & logging
├── graph/
│   ├── state.py                 # LangGraph TravelState schema definition
│   ├── nodes.py                 # Specialized AI agents (supervisor, flight, hotel, weather, budget, itinerary, final)
│   └── workflow.py              # StateGraph assembly, dynamic routing, and HITL interrupt
├── mcp_client/
│   ├── client.py                # MultiServerMCPClient instance connecting Tavily, AviationStack & Weather
│   └── adapters.py              # MCP tool invocation adapters & extractors
├── mcp_server/
│   └── weather_server.py        # FastMCP custom local Weather server
├── utils/
│   └── helpers.py               # Shared utility functions (JSON extraction, constants)
├── static/                      # Frontend static assets (CSS, JS)
├── templates/                   # Jinja2 HTML templates
├── tests/                       # Diagnostic test scripts (e.g. debug_aviation.py)
├── app.py                       # FastAPI web application server
├── langgraph.json               # LangGraph CLI & Studio manifest
├── readme.md                    # Module documentation
└── test.py                      # Diagnostic runner for MCP connections
```

---

## 🛡️ Guardrails & HITL Features

1. **Supervisor Agent**: Validates the prompt. Blocks non-travel or unsafe queries with a clear reason. Routes to specific sub-agents dynamically based on user needs.
2. **Budget Agent**: Analyzes constraints and provides feasibility assessment.
3. **Human-in-the-Loop (HITL)**: Interrupts LangGraph execution before generating the final polished output, requiring human approval or revision feedback via the UI.
4. **Resumable State**: Powered by `PostgresSaver`, allowing asynchronous resumption of the graph once the human approves.

---

## ⚡ MCP Integrations

1. **Tavily Web & Hotel Search** (`streamable_http`): Connected via remote MCP endpoint.
2. **AviationStack Flight Data** (`stdio`): Launched via `uvx --with fastmcp aviationstack-mcp`.
3. **Weather Server** (`stdio`): Launched as a local Python sub-process.

---

## 🌐 API & Web Interface

Start the FastAPI server:
```bash
python app.py
```
Open `http://127.0.0.1:8000/` in your browser.

### API Endpoints
* `GET /health`: Health check endpoint.
* `POST /api/travel`: Process a travel request message and return a draft if approval is needed.
* `POST /api/travel/approve`: Resume the paused graph execution with approval status and feedback.

```bash
# Example Travel Request
curl -X POST http://127.0.0.1:8000/api/travel \
  -H "Content-Type: application/json" \
  -d '{"message":"Plan a 3-day trip to Tokyo with a budget of $1200"}'

# Example Approval
curl -X POST http://127.0.0.1:8000/api/travel/approve \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"user_12345", "approved": true, "feedback": ""}'
```