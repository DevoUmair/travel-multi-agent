import os
import certifi
from dotenv import load_dotenv

load_dotenv()

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

from typing import TypedDict , Annotated
import operator
import uuid
# pyrefly: ignore [missing-import]
import psycopg
import asyncio
from psycopg.rows import dict_row
from langgraph.graph import StateGraph , START , END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    AnyMessage
)
from langchain_groq import ChatGroq
# from tools.tavily_tool import tavily_search
from mcp_client import tavily_mcp_search ,aviation_mcp_call , extract_destination , forecast_mcp_search , weather_mcp_search
from tools.flight_tool import search_flights


def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found in environment variables")
    if "sslmode=" not in db_url:
        seperator = "&" if "?" in db_url else "?"
        db_url += f"{seperator}sslmode=require"
    return db_url

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, api_key=GROQ_API_KEY)

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage] , operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    weather_results: str
    itinerary: str
    llm_calls:int



# def flight_agent(state: TravelState):
#     response = search_flights(state["user_query"])
    
#     return {
#         "flight_results": response,
#         "messages": [AIMessage(content="flight results fetched.")],
#         "llm_calls": state.get("llm_calls",0) + 1
#     }


# Flight Tool Router Prompt
FLIGHT_AGENT_PROMPT = """
You are a travel flight expert.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Generate:

1. Likely departure airport
2. Likely arrival airport
3. Airlines serving this route
4. Typical flight duration
5. Estimated airfare range
6. Peak season pricing warning
7. Booking advice

Return concise travel guidance.
"""




# Flight Agent
def flight_agent(state: TravelState):
    print("\nINSIDE FLIGHT AGENT\n")

    query = state["user_query"]

    try:

        airports =  asyncio.run(aviation_mcp_call("list_airports", {}))

        airlines = asyncio.run(aviation_mcp_call("list_airlines", {}))


        print("\nAIRPORTS:", airports)
        print("\nAIRLINES:", airlines)

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:3000],
            airline_data=str(airlines)[:3000]
        )

        response = llm.invoke([
            SystemMessage(
                content="You are an expert travel flight planner."
            ),
            HumanMessage(content=prompt)
        ])

        flight_data = response.content

    except Exception as e:

        flight_data = f"Flight information unavailable: {str(e)}"

    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(
                content="Flight recommendations generated"
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }




def hotel_agent(state: TravelState):
    query = f"Best hotel and stays for {state['user_query']}"
    response = asyncio.run(tavily_mcp_search(query))
    
    return {
        "hotel_results": response,
        "messages": [AIMessage(content="hotel results fetched.")],
        "llm_calls": state.get("llm_calls",0) + 1
    }


# =========================
# Weather Agent
# =========================

def weather_agent(state: TravelState):
    city = extract_destination(state["user_query"])

    weather_data = asyncio.run(
        weather_mcp_search(city)
    )

    forecast_data = asyncio.run(
        forecast_mcp_search(city)
    )

    print(f"""
        Current Weather:
        {weather_data}

        Forecast:
        {forecast_data}
        """)

    return {
        "weather_results": f"""
        Current Weather:
        {weather_data}

        Forecast:
        {forecast_data}
        """,
        "messages": [
            AIMessage(
                content="Weather information fetched"
            )
        ]
    }

def iterniary_agent(state: TravelState):
    prompt = f"""
        create a complete travel itinerary based on the following information:
        
        user query: {state['user_query']}
        flight results: {state['flight_results']}
        weather_results: {state['weather_results']}
        hotel results: {state['hotel_results']}

        Make the iterinary practical, budget aware, and easy to follow
    """

    response = llm.invoke([
        SystemMessage(content="You are an expert travel iterinary planner and you make the best iterinaries."),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [AIMessage(content="itinerary generated.")],
        "llm_calls": state.get("llm_calls",0) + 1
    }
    
def final_agent(state: TravelState):
    prompt = f"""
        create a complete travel itinerary based on the following information:
        
        user query: {state['user_query']}
        flight results: {state['flight_results']}
        hotel results: {state['hotel_results']}
        weather_results: {state['weather_results']}
        itinerary: {state['itinerary']}

        formar the final answer beatifully using these section
        1.Trip Summary
        2.Flight information
        3.Hotel Suggestion
        4.Weather Information
        5.Day-by-Day Itinerary
        6.Estimated cost
        7.Travel tips

        Important
        - Be concise but detailed in each section.
        - Mention that live flights api may not provide ticket price if pricing is unvailable or expired , so verify prices before booking.
        - keep the response usefull for real travel planning  
    """

    response = llm.invoke([
        SystemMessage(content="You are profeesional AI Travel booking assistant"),
        HumanMessage(content=prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls",0) + 1
    }

workflow = StateGraph(TravelState)

workflow.add_node("flight_agent",flight_agent)
workflow.add_node("hotel_agent",hotel_agent)
workflow.add_node("weather_agent",weather_agent)
workflow.add_node("iterniary_agent",iterniary_agent)
workflow.add_node("final_agent",final_agent)

workflow.add_edge(START, "flight_agent")
workflow.add_edge("flight_agent", "hotel_agent")
workflow.add_edge("hotel_agent", "weather_agent")
workflow.add_edge("weather_agent", "iterniary_agent")
workflow.add_edge("iterniary_agent", "final_agent")
workflow.add_edge("final_agent", END)

DB_URL=get_database_url()
_conn = psycopg.connect(
    DB_URL,
    autocommit=True,
    row_factory=dict_row
)
checkpointer = PostgresSaver(conn=_conn)
checkpointer.setup()

travel_graph = workflow.compile(
    checkpointer=checkpointer
)


# =========================
# Function for FastAPI
# =========================

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
            "weather_results": "",
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
        "weather_results": result.get("weather_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }