from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq

from config.settings import GROQ_API_KEY
from graph.state import TravelState
from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, api_key=GROQ_API_KEY)

def flight_agent(state: TravelState):
    response = search_flights(state["user_query"])
    
    return {
        "flight_results": response,
        "messages": [AIMessage(content="flight results fetched.")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

def hotel_agent(state: TravelState):
    query = f"Best hotel and stays for {state['user_query']}"
    response = tavily_search(query)
    
    return {
        "hotel_results": response,
        "messages": [AIMessage(content="hotel results fetched.")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

def itinerary_agent(state: TravelState):
    prompt = f"""
        create a complete travel itinerary based on the following information:
        
        user query: {state['user_query']}
        flight results: {state['flight_results']}
        hotel results: {state['hotel_results']}

        Make the itinerary practical, budget aware, and easy to follow
    """

    response = llm.invoke([
        SystemMessage(content="You are an expert travel itinerary planner and you make the best itineraries."),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [AIMessage(content="itinerary generated.")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
    
def final_agent(state: TravelState):
    prompt = f"""
        create a complete travel itinerary based on the following information:
        
        user query: {state['user_query']}
        flight results: {state['flight_results']}
        hotel results: {state['hotel_results']}
        itinerary: {state['itinerary']}

        format the final answer beautifully using these sections
        1. Trip Summary
        2. Flight information
        3. Hotel Suggestion
        4. Day-by-Day Itinerary
        5. Estimated cost
        6. Travel tips

        Important
        - Be concise but detailed in each section.
        - Mention that live flights api may not provide ticket price if pricing is unavailable or expired, so verify prices before booking.
        - keep the response useful for real travel planning  
    """

    response = llm.invoke([
        SystemMessage(content="You are professional AI Travel booking assistant"),
        HumanMessage(content=prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
