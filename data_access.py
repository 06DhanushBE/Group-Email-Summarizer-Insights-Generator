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

    try:
        emails = pd.DataFrame(client.table("realdb").select("*").execute().data)
    except Exception as e:
        print(f"[data_access] Failed to load 'realdb' from Supabase, falling back to demo: {e}")
        return load_demo_data()

    try:
        tasks = pd.DataFrame(client.table("tasks").select("*").execute().data)
    except Exception as e:
        # 'tasks' table may not exist yet in live Supabase -- don't crash the whole dashboard,
        # just show emails with no task-derived KPIs/charts.
        print(f"[data_access] Failed to load 'tasks' from Supabase (table may not exist): {e}")
        tasks = pd.DataFrame()

    return emails, tasks


def load_data(mode):
    return load_live_data() if mode == "live" else load_demo_data()