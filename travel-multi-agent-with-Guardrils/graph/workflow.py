import os
import uuid
import psycopg
from psycopg.rows import dict_row
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from langgraph.types import Command, interrupt
from typing import Any

from utils.helpers import get_empty_constraints
from config.settings import DATABASE_URL, logger
from graph.state import TravelState
from graph.nodes import (
    flight_agent,
    hotel_agent,
    weather_agent,
    budget_agent,
    itinerary_agent,
    final_agent,
    supervisor_agent,
    guardrail_blocked_agent,
    human_approval_agent,
)


def get_checkpointer():
    """Set up PostgresSaver if DATABASE_URL is available, otherwise fallback to MemorySaver (or None for LangGraph CLI)."""
    if os.getenv("LANGGRAPH_DEV") == "1":
        logger.info("LangGraph CLI/Studio mode detected: disabling custom checkpointer.")
        return None

    if not DATABASE_URL:
        logger.info("DATABASE_URL not found. Falling back to MemorySaver checkpointer.")
        return MemorySaver()

    try:
        db_url = DATABASE_URL
        if "sslmode=" not in db_url:
            separator = "&" if "?" in db_url else "?"
            db_url += f"{separator}sslmode=require"

        conn = psycopg.connect(
            db_url,
            autocommit=True,
            row_factory=dict_row
        )
        saver = PostgresSaver(conn=conn)
        saver.setup()
        logger.info("Successfully initialized PostgresSaver checkpointer.")
        return saver
    except Exception as e:
        logger.warning(f"Could not initialize PostgresSaver ({e}). Falling back to MemorySaver.")
        return MemorySaver()


# =========================
# Dynamic Supervisor Routing
# =========================
ROUTE_MAP = {
    "guardrail_blocked": "guardrail_blocked",
    "flight_agent": "flight_agent",
    "hotel_agent": "hotel_agent",
    "weather_agent": "weather_agent",
    "budget_agent": "budget_agent",
    "itinerary_agent": "itinerary_agent",
}

AGENT_ORDER = [
    "flight_agent",
    "hotel_agent",
    "weather_agent",
    "budget_agent",
    "itinerary_agent",
]


def _selected_agents(state: TravelState) -> list[str]:
    selected = state.get("selected_agents", [])
    return [agent for agent in AGENT_ORDER if agent in selected]


def route_from_supervisor(state: TravelState) -> str:
    if not state.get("guardrail_allowed", True):
        return "guardrail_blocked"

    selected = _selected_agents(state)
    return selected[0] if selected else "itinerary_agent"


def route_after_agent(current_agent: str):
    def route(state: TravelState) -> str:
        selected = _selected_agents(state)
        current_index = AGENT_ORDER.index(current_agent)

        for next_agent in AGENT_ORDER[current_index + 1 :]:
            if next_agent in selected:
                return next_agent

        return "itinerary_agent"

    return route


# =========================
# Build Graph
# =========================
workflow = StateGraph(TravelState)

workflow.add_node("supervisor", supervisor_agent)
workflow.add_node("guardrail_blocked", guardrail_blocked_agent)
workflow.add_node("flight_agent", flight_agent)
workflow.add_node("hotel_agent", hotel_agent)
workflow.add_node("weather_agent", weather_agent)
workflow.add_node("budget_agent", budget_agent)
workflow.add_node("itinerary_agent", itinerary_agent)
workflow.add_node("human_approval", human_approval_agent)
workflow.add_node("final_agent", final_agent)

workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges("supervisor", route_from_supervisor, ROUTE_MAP)

workflow.add_conditional_edges(
    "flight_agent", route_after_agent("flight_agent"), ROUTE_MAP
)
workflow.add_conditional_edges(
    "hotel_agent", route_after_agent("hotel_agent"), ROUTE_MAP
)
workflow.add_conditional_edges(
    "weather_agent", route_after_agent("weather_agent"), ROUTE_MAP
)
workflow.add_conditional_edges(
    "budget_agent", route_after_agent("budget_agent"), ROUTE_MAP
)

workflow.add_edge("itinerary_agent", "human_approval")
workflow.add_edge("human_approval", "final_agent")
workflow.add_edge("final_agent", END)
workflow.add_edge("guardrail_blocked", END)

checkpointer = get_checkpointer()
if checkpointer is not None:
    travel_graph = workflow.compile(checkpointer=checkpointer)
else:
    travel_graph = workflow.compile()


# =========================
# FastAPI-facing helpers
# =========================
def _interrupt_payload(result: dict[str, Any]) -> dict[str, Any] | None:
    interrupts = result.get("__interrupt__", [])
    if not interrupts:
        return None

    first_interrupt = interrupts[0]
    payload = getattr(first_interrupt, "value", first_interrupt)
    return payload if isinstance(payload, dict) else {"value": payload}


def _serialize_result(
    result: dict[str, Any],
    thread_id: str,
) -> dict[str, Any]:
    messages = result.get("messages", [])
    last_message = messages[-1].content if messages else ""
    answer = result.get("final_response") or last_message
    interrupt_payload = _interrupt_payload(result)

    if interrupt_payload:
        answer = interrupt_payload.get("draft_itinerary") or result.get(
            "itinerary", ""
        )

    return {
        "thread_id": thread_id,
        "answer": answer,
        "requires_approval": interrupt_payload is not None,
        "approval_request": (
            interrupt_payload.get("approval_request", "")
            if interrupt_payload
            else result.get("approval_request", "")
        ),
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "weather_results": result.get("weather_results", ""),
        "budget_results": result.get("budget_results", ""),
        "itinerary": (
            interrupt_payload.get("draft_itinerary", "")
            if interrupt_payload
            else result.get("itinerary", "")
        ),
        "selected_agents": result.get("selected_agents", []),
        "trip_constraints": result.get("trip_constraints", {}),
        "supervisor_reasoning": result.get("supervisor_reasoning", ""),
        "guardrail_allowed": result.get("guardrail_allowed", True),
        "guardrail_reason": result.get("guardrail_reason", ""),
        "approved": result.get("approved"),
        "human_feedback": result.get("human_feedback", ""),
        "llm_calls": result.get("llm_calls", 0),
    }

def run_travel_agent(user_input: str, thread_id: str | None = None) -> dict:
    """Synchronous runner using sync travel_graph.invoke(...) compatible with PostgresSaver."""
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "user_query": user_input,
        "guardrail_allowed": True,
        "guardrail_reason": "",
        "selected_agents": [],
        "trip_constraints": get_empty_constraints(),
        "supervisor_reasoning": "",
        "flight_results": "",
        "hotel_results": "",
        "weather_results": "",
        "budget_results": "",
        "itinerary": "",
        "approval_request": "",
        "approved": False,
        "human_feedback": "",
        "final_response": "",
        "llm_calls": 0,
    }

    result = travel_graph.invoke(initial_state, config=config)
    return _serialize_result(result, thread_id)


def resume_travel_agent(
    thread_id: str,
    approved: bool,
    feedback: str = "",
):
    """Resume the paused LangGraph thread after human review."""
    if not thread_id:
        raise ValueError("thread_id is required to resume a travel plan.")

    config = {"configurable": {"thread_id": thread_id}}
    result = travel_graph.invoke(
        Command(
            resume={
                "approved": approved,
                "feedback": feedback.strip(),
            }
        ),
        config=config,
    )

    return _serialize_result(result, thread_id)