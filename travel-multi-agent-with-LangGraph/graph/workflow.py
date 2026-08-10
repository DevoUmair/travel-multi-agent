import uuid
import psycopg
from psycopg.rows import dict_row
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import HumanMessage

from config.settings import DATABASE_URL
from graph.state import TravelState
from graph.nodes import flight_agent, hotel_agent, itinerary_agent, final_agent


def get_checkpointer():
    if not DATABASE_URL:
        return None
    try:
        conn = psycopg.connect(
            DATABASE_URL,
            autocommit=True,
            row_factory=dict_row
        )
        saver = PostgresSaver(conn=conn)
        saver.setup()
        return saver
    except Exception as e:
        print(f"Warning: Could not setup PostgresSaver: {e}")
        return None


workflow = StateGraph(TravelState)

workflow.add_node("flight_agent", flight_agent)
workflow.add_node("hotel_agent", hotel_agent)
workflow.add_node("itinerary_agent", itinerary_agent)
workflow.add_node("final_agent", final_agent)

workflow.add_edge(START, "flight_agent")
workflow.add_edge("flight_agent", "hotel_agent")
workflow.add_edge("hotel_agent", "itinerary_agent")
workflow.add_edge("itinerary_agent", "final_agent")
workflow.add_edge("final_agent", END)

checkpointer = get_checkpointer()

if checkpointer:
    travel_graph = workflow.compile(checkpointer=checkpointer)
else:
    travel_graph = workflow.compile()


def run_travel_agent(user_input: str, thread_id: str | None = None):
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = travel_graph.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    )

    final_answer = result["messages"][-1].content

    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }
