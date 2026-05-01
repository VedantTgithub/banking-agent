from langgraph.checkpoint.sqlite import SqliteSaver
import os

DB_PATH = os.getenv("SQLITE_DB_PATH", "./memory/checkpoints.db")

def get_checkpointer():
    """
    Returns a SqliteSaver checkpointer.
    SqliteSaver persists the full AgentState after every node.
    Zero setup needed — just a local .db file.
    """
    checkpointer = SqliteSaver.from_conn_string(DB_PATH)
    return checkpointer