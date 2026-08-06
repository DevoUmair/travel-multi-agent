import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("Weather MCP Server")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")


@mcp.tool()
def get_current_weather(city: str) -> dict:
    """Fetch current weather for a specified city via OpenWeather API."""
    if not OPENWEATHER_API_KEY:
        return {"error": "OPENWEATHER_API_KEY is missing"}

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            },
            timeout=10
        )
        data = response.json()

        if response.status_code != 200:
            return {"error": data.get("message", "Failed to fetch weather data")}

        return {
            "city": data.get("name", city),
            "temperature_c": data["main"]["temp"],
            "feels_like_c": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"]
        }
    except Exception as e:
        return {"error": f"Error fetching current weather: {str(e)}"}


@mcp.tool()
def get_forecast(city: str) -> dict:
    """Fetch 5-day weather forecast for a specified city via OpenWeather API."""
    if not OPENWEATHER_API_KEY:
        return {"error": "OPENWEATHER_API_KEY is missing"}

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            },
            timeout=10
        )
        data = response.json()

        if response.status_code != 200 or "list" not in data:
            return {"error": data.get("message", "Failed to fetch forecast data")}

        forecast = []
        for item in data["list"][:5]:
            forecast.append({
                "datetime": item.get("dt_txt", ""),
                "temperature": item.get("main", {}).get("temp"),
                "weather": item.get("weather", [{}])[0].get("description", "")
            })

        return {
            "city": city,
            "forecast": forecast
        }
    except Exception as e:
        return {"error": f"Error fetching forecast: {str(e)}"}


if __name__ == "__main__":
    mcp.run()
