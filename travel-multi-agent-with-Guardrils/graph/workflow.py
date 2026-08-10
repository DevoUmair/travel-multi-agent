import os
import uuid
import psycopg
from psycopg.rows import dict_row
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from config.settings import DATABASE_URL, logger
from graph.state import TravelState
from graph.nodes import (
    flight_agent,
    hotel_agent,
    weather_agent,
    itinerary_agent,
    final_agent
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


# Assemble graph workflow
workflow = StateGraph(TravelState)

workflow.add_node("flight_agent", flight_agent)
workflow.add_node("hotel_agent", hotel_agent)
workflow.add_node("weather_agent", weather_agent)
workflow.add_node("itinerary_agent", itinerary_agent)
workflow.add_node("final_agent", final_agent)

workflow.add_edge(START, "flight_agent")
workflow.add_edge("flight_agent", "hotel_agent")
workflow.add_edge("hotel_agent", "weather_agent")
workflow.add_edge("weather_agent", "itinerary_agent")
workflow.add_edge("itinerary_agent", "final_agent")
workflow.add_edge("final_agent", END)

checkpointer = get_checkpointer()
if checkpointer is not None:
    travel_graph = workflow.compile(checkpointer=checkpointer)
else:
    travel_graph = workflow.compile()


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
        "flight_results": "",
        "hotel_results": "",
        "weather_results": "",
        "itinerary": "",
        "llm_calls": 0
    }

    result = travel_graph.invoke(initial_state, config=config)
    final_answer = result["messages"][-1].content

    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "weather_results": result.get("weather_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }

