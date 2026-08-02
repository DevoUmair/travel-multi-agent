from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
from backend import run_travel_agent

# res = tavily_search("weather in karachi")
# print(res)

# print(search_flights("plan a 7 day trip to india"))

res = run_travel_agent(
    user_input="plan a 7 day trip to south india from Sri Lanka i have to go",
    thread_id="test"
)
print(res["answer"])
print(res["flight_results"])
print(res["hotel_results"])
print(res["itinerary"])
print(res["llm_calls"])