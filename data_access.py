import sqlite3

import pandas as pd

from app_config import DEMO_DB_PATH, SUPABASE_KEY, SUPABASE_URL

try:
    from supabase import create_client
except ImportError:
    create_client = None


def load_demo_data():
    conn = sqlite3.connect(DEMO_DB_PATH)
    emails = pd.read_sql("SELECT * FROM demodb", conn)
    tasks = pd.read_sql("SELECT * FROM demotasks", conn)
    conn.close()
    return emails, tasks


def load_live_data():
    if not (SUPABASE_URL and SUPABASE_KEY and create_client):
        return load_demo_data()
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    emails = pd.DataFrame(client.table("realdb").select("*").execute().data)
    tasks = pd.DataFrame(client.table("tasks").select("*").execute().data)
    return emails, tasks


def load_data(mode):
    return load_live_data() if mode == "live" else load_demo_data()