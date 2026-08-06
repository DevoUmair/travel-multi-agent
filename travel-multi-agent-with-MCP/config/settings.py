import os
import sys
import logging
from pathlib import Path
import certifi
from dotenv import load_dotenv

# Setup SSL certificates for requests/httpx
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
WEATHER_SERVER_PATH = BASE_DIR / "mcp_server" / "weather_server.py"

# API Keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
AVIATION_STACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Environment configs for MCP sub-processes
AVIATION_ENV = os.environ.copy()
AVIATION_ENV["AVIATION_STACK_API_KEY"] = AVIATION_STACK_API_KEY

WEATHER_ENV = os.environ.copy()
WEATHER_ENV["OPENWEATHER_API_KEY"] = OPENWEATHER_API_KEY

# Configure standard logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("travel_agent")
