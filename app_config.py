import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEMO_DB_PATH = BASE_DIR / "demo.db"
NEO4J_PAYLOAD_PATH = BASE_DIR / "neo4j_payload.json"

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

DEMO_NEO4J_URI = os.environ.get("DEMO_NEO4J_URI")
DEMO_NEO4J_USERNAME = os.environ.get("DEMO_NEO4J_USERNAME")
DEMO_NEO4J_PASSWORD = os.environ.get("DEMO_NEO4J_PASSWORD")
DEMO_NEO4J_DATABASE = os.environ.get("DEMO_NEO4J_DATABASE", "neo4j")

REAL_NEO4J_URI = os.environ.get("NEO4J_URI")
REAL_NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
REAL_NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
REAL_NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

DASH_DEBUG = os.environ.get("DASH_DEBUG", "False") == "True"
DASH_PORT = int(os.environ.get("DASH_PORT", 8050))