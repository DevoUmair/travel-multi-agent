import asyncio
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq

from config.settings import GROQ_API_KEY, logger
from graph.state import TravelState
from mcp_client.tools import (
    aviation_mcp_call,
    tavily_mcp_search,
    weather_mcp_search,
    forecast_mcp_search,
    extract_destination
)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=GROQ_API_KEY
)

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


def flight_agent(state: TravelState):
    logger.info("Executing Flight Agent...")
    query = state["user_query"]

    try:
        airports = asyncio.run(aviation_mcp_call("list_airports", {}))
        airlines = asyncio.run(aviation_mcp_call("list_airlines", {}))

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:3000],
            airline_data=str(airlines)[:3000]
        )

        response = llm.invoke([
            SystemMessage(content="You are an expert travel flight planner."),
            HumanMessage(content=prompt)
        ])
        flight_data = response.content
    except Exception as e:
        logger.error(f"Flight agent error: {e}")
        flight_data = f"Flight information unavailable: {str(e)}"

    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content="Flight recommendations generated")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def hotel_agent(state: TravelState):
    logger.info("Executing Hotel Agent...")
    query = f"Best hotel and stays for {state['user_query']}"
    response = asyncio.run(tavily_mcp_search(query))

    return {
        "hotel_results": str(response),
        "messages": [AIMessage(content="Hotel results fetched.")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def weather_agent(state: TravelState):
    logger.info("Executing Weather Agent...")
    city = extract_destination(state["user_query"])
    logger.info(f"Extracted destination for weather: {city}")

    weather_data = asyncio.run(weather_mcp_search(city))
    forecast_data = asyncio.run(forecast_mcp_search(city))

    weather_summary = f"""Current Weather:
{weather_data}

Forecast:
{forecast_data}"""

    logger.info(f"Weather results fetched for {city}")

    return {
        "weather_results": weather_summary,
        "messages": [AIMessage(content="Weather information fetched")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def itinerary_agent(state: TravelState):
    logger.info("Executing Itinerary Agent...")
    prompt = f"""
    Create a complete travel itinerary based on the following information:
    
    User Query: {state['user_query']}
    Flight Results: {state['flight_results']}
    Weather Results: {state['weather_results']}
    Hotel Results: {state['hotel_results']}

    Make the itinerary practical, budget aware, and easy to follow.
    """

    response = llm.invoke([
        SystemMessage(content="You are an expert travel itinerary planner."),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [AIMessage(content="Itinerary generated.")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def final_agent(state: TravelState):
    logger.info("Executing Final Agent...")
    prompt = f"""
    Create a complete travel response based on the following information:
    
    User Query: {state['user_query']}
    Flight Results: {state['flight_results']}
    Hotel Results: {state['hotel_results']}
    Weather Results: {state['weather_results']}
    Itinerary: {state['itinerary']}

    Format the final answer beautifully using these sections:
    1. Trip Summary
    2. Flight Information
    3. Hotel Suggestion
    4. Weather Information
    5. Day-by-Day Itinerary
    6. Estimated Cost
    7. Travel Tips

    Important:
    - Be concise but detailed in each section.
    - Mention that live flights API may not provide ticket price if pricing is unavailable or expired, so verify prices before booking.
    - Keep the response useful for real travel planning.
    """

    response = llm.invoke([
        SystemMessage(content="You are a professional AI Travel booking assistant."),
        HumanMessage(content=prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
