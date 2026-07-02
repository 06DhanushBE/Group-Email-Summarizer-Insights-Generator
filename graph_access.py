from app_config import (
    DEMO_NEO4J_DATABASE,
    DEMO_NEO4J_PASSWORD,
    DEMO_NEO4J_URI,
    DEMO_NEO4J_USERNAME,
    GROQ_API_KEY,
    GROQ_MODEL,
    REAL_NEO4J_DATABASE,
    REAL_NEO4J_PASSWORD,
    REAL_NEO4J_URI,
    REAL_NEO4J_USERNAME,
)

try:
    from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
    from langchain_groq import ChatGroq
except ImportError:
    Neo4jGraph = None
    GraphCypherQAChain = None
    ChatGroq = None


_qa_chains = {}


def get_qa_chain(mode):
    if mode in _qa_chains:
        return _qa_chains[mode]

    if not (Neo4jGraph and GraphCypherQAChain and ChatGroq and GROQ_API_KEY):
        return None

    if mode == "live":
        uri, user, pw, db = REAL_NEO4J_URI, REAL_NEO4J_USERNAME, REAL_NEO4J_PASSWORD, REAL_NEO4J_DATABASE
    else:
        uri, user, pw, db = DEMO_NEO4J_URI, DEMO_NEO4J_USERNAME, DEMO_NEO4J_PASSWORD, DEMO_NEO4J_DATABASE

    if not (uri and user and pw):
        return None

    graph = Neo4jGraph(url=uri, username=user, password=pw, database=db)
    llm = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0)

    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        allow_dangerous_requests=True,
        top_k=10,
    )
    _qa_chains[mode] = chain
    return chain