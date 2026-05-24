# agent-memory-store

Persistent key-value memory for AI agents — survives across sessions.

A `MemoryStore` is an ordered string-to-string mapping backed by a JSON file. Set values during one agent run, reload them in the next. Uses a dict-like interface and an optional context manager for auto-save.

## Install

```bash
pip install agent-memory-store
```

## Quick start

```python
from agent_memory_store import MemoryStore

# Auto-loads from file if it exists
store = MemoryStore("agent-memory.json")

store.set("user_name", "Alice")
store.set("last_task", "summarise docs")

store.save()  # flush to disk

# Next session — data is restored
store2 = MemoryStore("agent-memory.json")
store2.get("user_name")  # "Alice"
```

## Context manager

```python
with MemoryStore("agent-memory.json") as store:
    store.set("session_count", "3")
# auto-saved on exit, even if an exception occurred
```

## Dict-like interface

```python
store["key"] = "value"     # set
store["key"]               # get (KeyError if missing)
store.get("key")           # get or None
store.get("key", "default")
del store["key"]
"key" in store             # True / False
len(store)
list(store)                # keys in insertion order
store.keys()               # list[str]
store.values()             # list[str]
store.items()              # list[tuple[str, str]]
store.clear()
store.update({"a": "1", "b": "2"})
store.pop("key")           # remove and return
store.pop("key", "default")
```

## Persistence

```python
store.save()                  # write to self.path
store.save("other.json")      # write to explicit path
store.load()                  # reload from self.path (merge)
store.load("other.json")      # load from explicit path
```

Missing or empty files are silently ignored on load. Corrupt JSON files are ignored without modifying the current store.

## Serialisation

```python
d = store.to_dict()                         # plain dict copy
store2 = MemoryStore.from_dict(d)
store2 = MemoryStore.from_dict(d, path="memory.json")
```

## License

MIT
