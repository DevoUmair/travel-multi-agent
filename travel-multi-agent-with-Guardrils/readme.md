# ✈️ TripMate AI — Multi-Agent Travel Planner (MCP & LangGraph)

An enterprise-grade AI travel planner that converts natural-language prompts into actionable travel itineraries featuring flight research, hotel options, weather forecasts, and day-by-day schedules. Built with **LangGraph**, **FastAPI**, **LangChain**, and **Model Context Protocol (MCP)**.

---

## 🏗️ Refactored Modular Architecture

```text
travel-multi-agent-with-MCP/
├── config/
│   ├── settings.py              # Environment configuration, API keys, SSL settings & logging
├── graph/
│   ├── state.py                 # LangGraph TravelState schema definition
│   ├── nodes.py                 # Specialized AI agent nodes (flight, hotel, weather, itinerary, final)
│   └── workflow.py              # StateGraph assembly, compilation & runner functions
├── mcp_client/
│   ├── client.py                # MultiServerMCPClient instance connecting Tavily, AviationStack & Weather
│   └── adapters.py              # MCP tool invocation adapters & extractors
├── mcp_server/
│   └── weather_server.py        # FastMCP custom local Weather server
├── static/                      # Frontend static assets (CSS, JS)
├── templates/                   # Jinja2 HTML templates
├── tests/                       # Diagnostic test scripts (e.g. debug_aviation.py)
├── app.py                       # FastAPI web application server
├── langgraph.json               # LangGraph CLI & Studio manifest
├── readme.md                    # Module documentation
└── test.py                      # Diagnostic runner for MCP connections
```

---

## ⚡ MCP Integrations

1. **Tavily Web & Hotel Search** (`streamable_http`): Connected via remote MCP endpoint `https://mcp.tavily.com/mcp/?tavilyApiKey=...`.
2. **AviationStack Flight Data** (`stdio`): Launched via `uvx --with fastmcp aviationstack-mcp`.
3. **Weather Server** (`stdio`): Launched as a sub-process running `mcp_server/weather_server.py` via `sys.executable`.

---

## 🌐 API & Web Interface

Start the FastAPI server:
```bash
python app.py
```
Open `http://127.0.0.1:8000/` in your browser.

### API Endpoints
* `GET /health`: Health check endpoint.
* `POST /api/travel`: Process a travel request message.

```bash
curl -X POST http://127.0.0.1:8000/api/travel \
  -H "Content-Type: application/json" \
  -d '{"message":"Plan a 3-day trip to Tokyo with a budget of $1200"}'
```