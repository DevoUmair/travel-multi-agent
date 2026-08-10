# ✈️ Travel Multi-Agent System (LangGraph & MCP)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange)](https://github.com/langchain-ai/langgraph)
[![MCP Protocol](https://img.shields.io/badge/MCP-Model_Context_Protocol-green)](https://modelcontextprotocol.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)

A comprehensive multi-agent AI travel planning platform built with **LangGraph**, **FastAPI**, and the **Model Context Protocol (MCP)**. The system orchestrates specialized AI agents (Flights, Hotels, Weather, Itinerary, and Synthesis) to turn natural language travel prompts into complete, actionable travel itineraries.

---

## 📂 Repository Structure

This repository is organized into distinct project implementations and architectural assets:

```text
travel-multi-agent/
├── travel-multi-agent-with-MCP/         # 🌟 Primary Application (Modular MCP + LangGraph + FastAPI)
│   ├── config/                          # Centralized settings & environment loading
│   ├── graph/                           # LangGraph state, nodes, checkpointer & workflow definitions
│   ├── mcp_client/                      # Multi-server MCP client & adapters (Tavily, AviationStack, Weather)
│   ├── mcp_server/                      # Custom FastMCP Weather server implementation
│   ├── static/                          # Modern web UI assets (CSS, JS)
│   ├── templates/                       # Jinja2 HTML templates
│   ├── tests/                           # Diagnostic test scripts & debugging utilities
│   ├── app.py                           # FastAPI web application entrypoint
│   └── langgraph.json                   # LangGraph CLI & Studio configuration
├── travel-multi-agent-with-Guardrils/   # 🛡️ Implementation with Input Guardrails and Human-in-the-Loop (HITL) approval
│   ├── config/                          # Settings & environment loading
│   ├── graph/                           # Supervisor, HITL nodes, and dynamic routing
│   ├── mcp_client/                      # MCP adapters
│   ├── mcp_server/                      # Local Weather server
│   ├── utils/                           # Shared utility functions
│   ├── app.py                           # FastAPI web application with /approve endpoint
│   └── langgraph.json                   # LangGraph CLI configuration
├── travel-multi-agent-with-LangGraph/   # 🏛️ Baseline implementation (Standard LangGraph workflow)
│   ├── config/                          # Settings & environment loading
│   ├── graph/                           # Standard LangGraph definitions and nodes
│   ├── tools/                           # Flight and web search integrations
│   └── app.py                           # FastAPI app entry point
├── excalidraw/                          # 🎨 Architecture diagrams & workflow visual designs
├── .env.example                         # Environment configuration template
└── requirements.txt                     # Combined dependencies
```

---

## 🌟 1. Multi-Agent System with MCP (`travel-multi-agent-with-MCP`)

The primary implementation features a modular, enterprise-grade architecture where each agent leverages **Model Context Protocol (MCP)** adapters to communicate with external APIs and services securely.

### Key Architecture Components
* **Flight Agent**: Communicates with the `aviationstack-mcp` server via `stdio` transport to retrieve real-time airport and airline data.
* **Hotel Agent**: Queries the `tavily` remote MCP server via `streamable_http` to find optimized accommodations and pricing.
* **Weather Agent**: Calls a custom local `FastMCP` weather server (`mcp_server/weather_server.py`) via `stdio` to provide live weather and 5-day forecasts.
* **Itinerary & Final Agents**: Synthesizes flight options, stay choices, and weather conditions into structured day-by-day itineraries using Groq (`llama-3.3-70b-versatile`).

---

## 🛡️ 2. Guardrails and Human-in-the-Loop (`travel-multi-agent-with-Guardrils`)

This implementation builds upon the MCP architecture by adding safety and human oversight:
* **Input Guardrail**: A supervisor agent verifies whether user requests are valid travel inquiries and filters out irrelevant or unsafe prompts.
* **Specialized Budget Agent**: Analyzes trip feasibility, cost categories, and money-saving tips.
* **Human-in-the-Loop (HITL)**: LangGraph is configured to pause workflow execution and present a draft itinerary to the user for approval or revision via the web UI. Once the user approves or supplies feedback, the system generates the final output.

---

## 🏛️ 3. Standard LangGraph System (`travel-multi-agent-with-LangGraph`)

The original baseline implementation demonstrating core **LangGraph StateGraph** orchestration, PostgreSQL thread checkpointing (`PostgresSaver`), and state transitions prior to integrating Model Context Protocol abstractions.

---

## 🎨 4. Architectural Diagrams & Resources (`excalidraw`)

Contains visual flowcharts and state diagrams (`.excalidraw` files) detailing the multi-agent graph state transitions, MCP client-server topology, and node execution order.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* **Python 3.10+** installed
* **`uv` / `uvx`** toolchain installed (`pip install uv`) for running `stdio` MCP servers
* **PostgreSQL** database (optional for state persistence)

### 2. Environment Setup
Copy the `.env.example` file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:
```env
GROQ_API_KEY=gsk_your_groq_key
TAVILY_API_KEY=tvly_your_tavily_key
AVIATIONSTACK_API_KEY=your_aviationstack_key
OPENWEATHER_API_KEY=your_openweather_key
DATABASE_URL=postgresql://user:password@localhost:5432/travel_db
```

### 3. Installation
Create virtual environment and install dependencies:

```bash
python -m venv .venv
# Activate virtual environment:
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
```

---

## 💻 Running the Application

### A. Run FastAPI Web Server
Navigate to your desired project directory (e.g., `travel-multi-agent-with-MCP` or `travel-multi-agent-with-Guardrils`) and run `app.py`:

```bash
cd travel-multi-agent-with-MCP
python app.py
```
Open your browser at `http://127.0.0.1:8000` to interact with the web UI.

### B. Run with LangGraph Studio / CLI
To test and visualize the agent workflow in **LangGraph Studio**, navigate to a directory with a `langgraph.json` file:

```bash
cd travel-multi-agent-with-MCP
langgraph dev
```

---

## 🧪 Verification & Testing

Run diagnostic tests for the MCP adapters and server connections:

```bash
cd travel-multi-agent-with-MCP
python test.py
```

---

## 📜 License
This project is licensed under the MIT License.
