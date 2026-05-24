"""Persistent key-value memory store for AI agents.

A :class:`MemoryStore` is an in-memory ordered dict of string keys and
string values backed by a JSON file.  Use it to carry facts across agent
sessions: names, preferences, task state, partial results.

Persistence
-----------
Call :meth:`MemoryStore.save` to flush to disk, :meth:`MemoryStore.load`
to reload.  Pass the store as a context manager for automatic save on exit::

    with MemoryStore("memory.json") as store:
        store.set("greeting", "Hello")
    # file written here, even if an exception occurred inside the block
"""

from __future__ import annotations

import json
from collections import OrderedDict
from collections.abc import Iterator
from pathlib import Path
from typing import Any


class MemoryStore:
    """Ordered, file-backed key-value store for agent memory.

    Keys and values are strings.  Insertion order is preserved.  The store
    can be serialised to/from a JSON file for cross-session persistence.

    Args:
        path: Optional file path to load from on construction and save to
            by default.  When *path* points to an existing file and
            *auto_load* is ``True`` (the default), the store is populated
            from that file immediately.
        auto_load: If ``True`` and *path* exists, load from it at
            construction time.  Set to ``False`` to start empty even if the
            file exists.

    Example::

        store = MemoryStore("memory.json")
        store.set("user", "Alice")
        store.save()                   # write to memory.json
    """

    def __init__(
        self,
        path: str | Path | None = None,
        *,
        auto_load: bool = True,
    ) -> None:
        self._store: OrderedDict[str, str] = OrderedDict()
        self.path: Path | None = Path(path) if path is not None else None
        if self.path is not None and auto_load:
            self.load()

    # ------------------------------------------------------------------
    # Dict-like interface
    # ------------------------------------------------------------------

    def set(self, key: str, value: str) -> None:
        """Set *key* to *value*.

        Args:
            key: String key.
            value: String value.

        Raises:
            TypeError: If *key* or *value* is not a string.
        """
        self[key] = value

    def __setitem__(self, key: str, value: str) -> None:
        if not isinstance(key, str):
            raise TypeError(f"Key must be a str, got {type(key).__name__!r}.")
        if not isinstance(value, str):
            raise TypeError(f"Value must be a str, got {type(value).__name__!r}.")
        self._store[key] = value
        self._store.move_to_end(key)

    def __getitem__(self, key: str) -> str:
        return self._store[key]

    def __delitem__(self, key: str) -> None:
        del self._store[key]

    def __contains__(self, key: object) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)

    def __iter__(self) -> Iterator[str]:
        return iter(self._store)

    def __repr__(self) -> str:
        path_repr = repr(str(self.path)) if self.path is not None else "None"
        return f"MemoryStore(path={path_repr}, entries={dict(self._store)!r})"

    def get(self, key: str, default: str | None = None) -> str | None:
        """Return the value for *key*, or *default* if absent.

        Args:
            key: Lookup key.
            default: Returned when *key* is not present.

        Returns:
            Stored string or *default*.
        """
        return self._store.get(key, default)

    def keys(self) -> list[str]:
        """Return all keys in insertion order."""
        return list(self._store.keys())

    def values(self) -> list[str]:
        """Return all values in insertion order."""
        return list(self._store.values())

    def items(self) -> list[tuple[str, str]]:
        """Return ``(key, value)`` pairs in insertion order."""
        return list(self._store.items())

    def clear(self) -> None:
        """Remove all entries from memory (does not touch the file)."""
        self._store.clear()

    def update(self, mapping: dict[str, str]) -> None:
        """Merge *mapping* into the store, updating existing keys.

        Args:
            mapping: Key-value pairs to add or overwrite.
        """
        for k, v in mapping.items():
            self[k] = v

    def pop(self, key: str, *args: Any) -> str:
        """Remove *key* and return its value.

        Args:
            key: Key to remove.
            *args: Optional default (same semantics as ``dict.pop``).

        Returns:
            Removed value or the provided default.

        Raises:
            KeyError: If *key* is absent and no default was given.
        """
        return self._store.pop(key, *args)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path | None = None) -> None:
        """Write the store to a JSON file.

        Args:
            path: Destination path.  Falls back to :attr:`self.path` when
                omitted.

        Raises:
            ValueError: If neither *path* nor :attr:`self.path` is set.
        """
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("No path specified. Pass a path to save() or set MemoryStore.path.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as fh:
            json.dump(dict(self._store), fh, indent=2, ensure_ascii=False)

    def load(self, path: str | Path | None = None) -> None:
        """Load entries from a JSON file, merging into the current store.

        Missing or empty files are silently ignored.  Corrupt JSON files
        are silently ignored (store is left unchanged for that call).

        Args:
            path: Source path.  Falls back to :attr:`self.path` when
                omitted.

        Raises:
            ValueError: If neither *path* nor :attr:`self.path` is set.
        """
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("No path specified. Pass a path to load() or set MemoryStore.path.")
        if not target.exists():
            return  # nothing to load — start empty
        try:
            raw = target.read_text(encoding="utf-8").strip()
            if not raw:
                return  # empty file → stay empty
            data: dict[str, Any] = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            return  # corrupt or unreadable — leave store unchanged
        for k, v in data.items():
            if isinstance(k, str) and isinstance(v, str):
                self._store[k] = v

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> MemoryStore:
        return self

    def __exit__(self, *args: object) -> None:
        """Auto-save when exiting the context, if a path is configured."""
        if self.path is not None:
            self.save()

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, str]:
        """Return a plain ``dict`` copy of the store."""
        return dict(self._store)

    @classmethod
    def from_dict(cls, data: dict[str, str], path: str | Path | None = None) -> MemoryStore:
        """Create a :class:`MemoryStore` from a plain dict.

        Args:
            data: ``{str: str}`` mapping.
            path: Optional file path to associate with the store.

        Returns:
            Populated :class:`MemoryStore` (not auto-saved).
        """
        store = cls(path, auto_load=False)
        store.update(data)
        return store
