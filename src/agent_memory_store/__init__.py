"""agent-memory-store: persistent key-value memory for AI agents.

A :class:`MemoryStore` is an ordered string-to-string mapping backed by a
JSON file.  It survives across agent sessions: set values during one run,
reload them in the next.

Quick start::

    from agent_memory_store import MemoryStore

    # Auto-loads from file if it exists; creates on first save()
    store = MemoryStore("agent-memory.json")

    store.set("user_name", "Alice")
    store.set("last_task", "summarise docs")

    store.save()  # persist to disk

    # Context manager: auto-saves on exit
    with MemoryStore("agent-memory.json") as store:
        store.set("session_count", "3")
"""

from .core import MemoryStore

__all__ = ["MemoryStore"]
__version__ = "0.1.0"
