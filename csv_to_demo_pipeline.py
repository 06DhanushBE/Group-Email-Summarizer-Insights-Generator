import os
import re
import json
import sqlite3
import time
import requests
import pandas as pd
from dotenv import load_dotenv

CSV_PATH = "ucicdemo.csv"
DB_PATH = "demo.db"
NEO4J_JSON_PATH = "neo4j_payload.json"

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"   
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are an email thread analyst for UCIC (a financial services company). You will be given the full text of an email thread (all messages, chronological, with sender and timestamp). Analyze the ENTIRE thread as one conversation, not message-by-message.

Always respond with ONLY a single valid JSON object -- no markdown code fences, no explanation, no text before or after it. The JSON must have exactly these 8 keys:

{
  "thread_title": "A short, human-readable title summarizing what this thread is about (synthesize from subject + content, 5-10 words, not just a copy of the subject line)",
  "department": "The business department this thread belongs to (e.g. HR, Collections, Compliance, IT Support, Finance, Legal, Operations, Technology, Risk, Credit Monitoring, Data Governance) -- infer from the actual content, not the group name",
  "conversation_category": "One of: Client, Vendor, Automation Project, Non-Client Topic, Customer Support, Security Incident, Reporting, Hiring, Access Request, System Issue",
  "client_project_or_topic": "The specific client name, project name, or topic this thread concerns, extracted from the content",
  "sender_role": "The likely role of the FIRST sender in the thread (e.g. Collections Manager, Credit Analyst, HR Coordinator, Client Contact, Vendor Support) -- infer from context and email domain",
  "priority": "High, Medium, or Low -- based on urgency language, deadlines, or severity mentioned",
  "summary": "A 2-3 sentence summary of what happened in this thread -- what was discussed, what was decided or is pending",
  "tasks": [
    {
      "task": "description of a specific action item mentioned in the thread",
      "owner": "the person responsible, if named or clearly implied in the thread -- otherwise null",
      "due_date": "YYYY-MM-DD if a specific date or deadline is mentioned or can be reasonably calculated from context, otherwise null",
      "status": "open"
    }
  ]
}

Each task in the "tasks" array is independent -- different tasks in the same thread may have different owners and different due dates. Extract each one separately based on what the thread actually says, don't assume they all share the same owner or deadline.

If the thread has no clear action items, return an empty array for "tasks". Return raw JSON only. Do not wrap it in code fences or any other formatting."""


def call_groq(conversation_text, retries=3):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": conversation_text},
        ],
        "temperature": 0.2,
    }
    for attempt in range(retries):
        resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            raw = resp.json()["choices"][0]["message"]["content"]
            raw = raw.strip()
            raw = re.sub(r'^```json\s*', '', raw, flags=re.IGNORECASE)
            raw = re.sub(r'^```\s*', '', raw)
            raw = re.sub(r'```\s*$', '', raw)
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                match = re.search(r'\{[\s\S]*\}', raw)
                if match:
                    return json.loads(match.group(0))
                raise ValueError(f"Could not parse Groq output: {raw[:300]}")
        time.sleep(2 ** attempt)
    raise RuntimeError(f"Groq call failed after {retries} retries: {resp.status_code} {resp.text[:300]}")


def build_conversation_text(thread_df):
    lines = []
    for _, row in thread_df.iterrows():
        lines.append(f"[{row['sent_timestamp']}] {row['from_name']} ({row['from_email']}):\n{row['email_body']}")
    return "\n\n---\n\n".join(lines)


def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS demodb;
    DROP TABLE IF EXISTS demotasks;

    CREATE TABLE demodb (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id TEXT UNIQUE,
        thread_id TEXT,
        thread_sequence INTEGER,
        channel_type TEXT,
        department TEXT,
        conversation_category TEXT,
        client_project_or_topic TEXT,
        thread_title TEXT,
        sent_timestamp TEXT,
        from_name TEXT,
        from_email TEXT,
        sender_role TEXT,
        to_group TEXT,
        cc TEXT,
        subject TEXT,
        email_body TEXT,
        attachment_name TEXT,
        priority TEXT,
        summary TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE demotasks (
        task_id TEXT PRIMARY KEY,
        thread_id TEXT NOT NULL,
        task TEXT NOT NULL,
        owner TEXT,
        due_date TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    return conn


def main():
    if not GROQ_API_KEY:
        raise EnvironmentError("Set GROQ_API_KEY environment variable before running.")

    df = pd.read_csv(CSV_PATH)
    df["sent_timestamp"] = pd.to_datetime(df["sent_timestamp"])

    conn = setup_db()
    cur = conn.cursor()

    neo4j_payloads = []
    thread_ids = df["thread_id"].unique()
    print(f"Processing {len(thread_ids)} threads via Groq ({GROQ_MODEL})...")

    for i, thread_id in enumerate(thread_ids, 1):
        thread_df = df[df["thread_id"] == thread_id].sort_values("thread_sequence")
        conversation_text = build_conversation_text(thread_df)

        print(f"  [{i}/{len(thread_ids)}] {thread_id} ...", end=" ", flush=True)
        ai = call_groq(conversation_text)
        print("done")

        # --- demodb rows (one per email) ---
        for _, row in thread_df.iterrows():
            cur.execute("""
                INSERT INTO demodb (
                    email_id, thread_id, thread_sequence, channel_type, department,
                    conversation_category, client_project_or_topic, thread_title,
                    sent_timestamp, from_name, from_email, sender_role, to_group, cc,
                    subject, email_body, attachment_name, priority, summary
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                row["email_id"], row["thread_id"], int(row["thread_sequence"]),
                row["channel_type"], ai.get("department", ""), ai.get("conversation_category", ""),
                ai.get("client_project_or_topic", ""), ai.get("thread_title", ""),
                row["sent_timestamp"].strftime("%Y-%m-%d %H:%M"),
                row["from_name"], row["from_email"], ai.get("sender_role", ""),
                row["to_group"], row.get("cc", ""), row["subject"], row["email_body"],
                row.get("attachment_name", ""), ai.get("priority", ""), ai.get("summary", ""),
            ))

        # --- demotasks rows (one per extracted task) ---
        tasks = ai.get("tasks", []) or []
        task_rows = []
        for idx, t in enumerate(tasks, 1):
            task_id = f"{thread_id}_{idx}"
            cur.execute("""
                INSERT INTO demotasks (task_id, thread_id, task, owner, due_date, status)
                VALUES (?,?,?,?,?,?)
            """, (task_id, thread_id, t.get("task", ""), t.get("owner"),
                  t.get("due_date"), t.get("status", "open")))
            task_rows.append({
                "task_id": task_id, "task": t.get("task", ""), "owner": t.get("owner"),
                "due_date": t.get("due_date"), "status": t.get("status", "open"),
            })

        # --- neo4j payload (one object per thread) ---
        people = thread_df[["from_name", "from_email"]].drop_duplicates()
        neo4j_payloads.append({
            "thread_id": thread_id,
            "thread_title": ai.get("thread_title", ""),
            "department": ai.get("department", ""),
            "topic": ai.get("client_project_or_topic", ""),
            "people": [{"name": r["from_name"], "email": r["from_email"]} for _, r in people.iterrows()],
            "tasks": task_rows,
        })

        conn.commit()

    with open(NEO4J_JSON_PATH, "w") as f:
        json.dump(neo4j_payloads, f, indent=2)

    n_emails = cur.execute("SELECT COUNT(*) FROM demodb").fetchone()[0]
    n_tasks = cur.execute("SELECT COUNT(*) FROM demotasks").fetchone()[0]
    print(f"\nDone. {n_emails} emails, {n_tasks} tasks written to {DB_PATH}.")
    print(f"{len(neo4j_payloads)} thread payloads written to {NEO4J_JSON_PATH}.")

    conn.close()


if __name__ == "__main__":
    main()