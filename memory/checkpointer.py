import sqlite3
import os
from langgraph.checkpoint.sqlite import SqliteSaver

DB_PATH = os.getenv("SQLITE_DB_PATH", "./memory/checkpoints.db")

# Ensure the directory exists
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)

# Create a persistent connection
# check_same_thread=False is needed for FastAPI/Uvicorn multi-threading
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

def get_checkpointer():
    """
    Returns a persistent SqliteSaver instance.
    """
    checkpointer = SqliteSaver(conn)
    # Ensure tables exist
    # Note: in some versions this is called automatically, 
    # but calling it explicitly is safer.
    # If it's not available, we catch the error.
    try:
        checkpointer.setup()
    except AttributeError:
        pass
    return checkpointer