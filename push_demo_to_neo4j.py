import json
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

from app_config import NEO4J_PAYLOAD_PATH

load_dotenv()

NEO4J_URI = os.environ.get("DEMO_NEO4J_URI")
NEO4J_USER = os.environ.get("DEMO_NEO4J_USERNAME")
NEO4J_PASSWORD = os.environ.get("DEMO_NEO4J_PASSWORD")
NEO4J_DATABASE = os.environ.get("DEMO_NEO4J_DATABASE", "neo4j")

JSON_PATH = NEO4J_PAYLOAD_PATH

CYPHER = """
MERGE (t:Thread {thread_id: $thread_id})
SET t.thread_title = $thread_title, t.department = $department

MERGE (top:Topic {name: $topic})
MERGE (t)-[:ABOUT]->(top)

MERGE (d:Department {name: $department})
MERGE (t)-[:BELONGS_TO]->(d)

WITH t
UNWIND $people AS person
  MERGE (p:Person {email: person.email})
  SET p.name = person.name
  MERGE (p)-[:PARTICIPATED_IN]->(t)

WITH t
UNWIND $tasks AS task
  MERGE (task_node:Task {task_id: task.task_id})
  SET task_node.task = task.task,
      task_node.due_date = task.due_date,
      task_node.status = task.status
  MERGE (task_node)-[:EXTRACTED_FROM]->(t)
  FOREACH (ignoreMe IN CASE WHEN task.owner IS NOT NULL THEN [1] ELSE [] END |
    MERGE (owner:Person {name: task.owner})
    MERGE (owner)-[:OWNS]->(task_node)
  )
"""


def main():
  if not (NEO4J_URI and NEO4J_USER and NEO4J_PASSWORD):
    raise EnvironmentError("Set DEMO_NEO4J_URI, DEMO_NEO4J_USERNAME, and DEMO_NEO4J_PASSWORD in .env for demo mode")

  with open(JSON_PATH, encoding="utf-8") as f:
    threads = json.load(f)

  driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

  with driver.session(database=NEO4J_DATABASE) as session:
    for i, thread in enumerate(threads, 1):
      session.run(
        CYPHER,
        thread_id=thread["thread_id"],
        thread_title=thread["thread_title"],
        department=thread["department"],
        topic=thread["topic"],
        people=thread["people"],
        tasks=thread["tasks"],
      )
      print(
        f"[{i}/{len(threads)}] pushed thread {thread['thread_id']} "
        f"({len(thread['people'])} people, {len(thread['tasks'])} tasks)"
      )

  driver.close()
  print("\nDone. Verify in Aura Query tab with: MATCH (n) RETURN n LIMIT 25")


if __name__ == "__main__":
    main()