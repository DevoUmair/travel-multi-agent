import os
import certifi
from dotenv import load_dotenv

load_dotenv()

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_database_url() -> str | None:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return None
    if "sslmode=" not in db_url:
        seperator = "&" if "?" in db_url else "?"
        db_url += f"{seperator}sslmode=require"
    return db_url

DATABASE_URL = get_database_url()
