"""Tests for agent-memory-store."""

from __future__ import annotations

import json

import pytest

from agent_memory_store import MemoryStore

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_empty_init():
    store = MemoryStore()
    assert len(store) == 0


def test_init_no_path():
    store = MemoryStore()
    assert store.path is None


def test_init_with_nonexistent_path(tmp_path):
    p = tmp_path / "memory.json"
    store = MemoryStore(p)
    assert len(store) == 0  # file missing → start empty


def test_init_loads_existing_file(tmp_path):
    p = tmp_path / "memory.json"
    p.write_text(json.dumps({"a": "1", "b": "2"}))
    store = MemoryStore(p)
    assert store.get("a") == "1"
    assert store.get("b") == "2"


def test_init_auto_load_false(tmp_path):
    p = tmp_path / "memory.json"
    p.write_text(json.dumps({"a": "1"}))
    store = MemoryStore(p, auto_load=False)
    assert len(store) == 0


def test_init_path_stored_as_path_object(tmp_path):
    p = tmp_path / "memory.json"
    store = MemoryStore(str(p))
    from pathlib import Path

    assert isinstance(store.path, Path)


# ---------------------------------------------------------------------------
# set / get / delete
# ---------------------------------------------------------------------------


def test_set_get():
    store = MemoryStore()
    store.set("key", "value")
    assert store.get("key") == "value"


def test_setitem_getitem():
    store = MemoryStore()
    store["key"] = "value"
    assert store["key"] == "value"


def test_get_missing_returns_none():
    store = MemoryStore()
    assert store.get("missing") is None


def test_get_with_default():
    store = MemoryStore()
    assert store.get("missing", "fallback") == "fallback"


def test_getitem_missing_raises():
    store = MemoryStore()
    with pytest.raises(KeyError):
        _ = store["nope"]


def test_overwrite():
    store = MemoryStore()
    store.set("k", "v1")
    store.set("k", "v2")
    assert store.get("k") == "v2"
    assert len(store) == 1


def test_delitem():
    store = MemoryStore()
    store.set("k", "v")
    del store["k"]
    assert "k" not in store
    assert len(store) == 0


def test_delitem_missing_raises():
    store = MemoryStore()
    with pytest.raises(KeyError):
        del store["nope"]


def test_contains_true():
    store = MemoryStore()
    store.set("k", "v")
    assert "k" in store


def test_contains_false():
    store = MemoryStore()
    assert "nope" not in store


# ---------------------------------------------------------------------------
# Type validation
# ---------------------------------------------------------------------------


def test_non_string_key_raises():
    store = MemoryStore()
    with pytest.raises(TypeError, match="Key must be a str"):
        store[123] = "v"  # type: ignore[index]


def test_non_string_value_raises():
    store = MemoryStore()
    with pytest.raises(TypeError, match="Value must be a str"):
        store["k"] = 99  # type: ignore[assignment]


def test_set_non_string_key_raises():
    store = MemoryStore()
    with pytest.raises(TypeError):
        store.set(123, "v")  # type: ignore[arg-type]


def test_set_non_string_value_raises():
    store = MemoryStore()
    with pytest.raises(TypeError):
        store.set("k", 99)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# keys / values / items / iter / len
# ---------------------------------------------------------------------------


def test_keys_insertion_order():
    store = MemoryStore()
    store.set("z", "1")
    store.set("a", "2")
    store.set("m", "3")
    assert store.keys() == ["z", "a", "m"]


def test_overwrite_preserves_insertion_order():
    # Re-setting an existing key must NOT move it to the end; the original
    # insertion position is preserved, matching dict / OrderedDict semantics.
    store = MemoryStore()
    store.set("a", "1")
    store.set("b", "2")
    store.set("c", "3")
    store.set("a", "updated")
    assert store.keys() == ["a", "b", "c"]
    assert store.get("a") == "updated"


def test_update_preserves_insertion_order():
    store = MemoryStore()
    store.set("a", "1")
    store.set("b", "2")
    store.update({"a": "updated", "c": "3"})
    assert store.keys() == ["a", "b", "c"]
    assert store.get("a") == "updated"


def test_values():
    store = MemoryStore()
    store.set("a", "1")
    store.set("b", "2")
    assert store.values() == ["1", "2"]


def test_items():
    store = MemoryStore()
    store.set("a", "1")
    store.set("b", "2")
    assert store.items() == [("a", "1"), ("b", "2")]


def test_iter():
    store = MemoryStore()
    store.set("a", "1")
    store.set("b", "2")
    assert list(store) == ["a", "b"]


def test_len():
    store = MemoryStore()
    assert len(store) == 0
    store.set("a", "1")
    assert len(store) == 1
    store.set("b", "2")
    assert len(store) == 2


# ---------------------------------------------------------------------------
# clear / update / pop
# ---------------------------------------------------------------------------


def test_clear():
    store = MemoryStore()
    store.set("a", "1")
    store.set("b", "2")
    store.clear()
    assert len(store) == 0


def test_update():
    store = MemoryStore()
    store.set("a", "1")
    store.update({"b": "2", "a": "updated"})
    assert store.get("b") == "2"
    assert store.get("a") == "updated"


def test_pop_existing():
    store = MemoryStore()
    store.set("k", "v")
    val = store.pop("k")
    assert val == "v"
    assert "k" not in store


def test_pop_missing_raises():
    store = MemoryStore()
    with pytest.raises(KeyError):
        store.pop("nope")


def test_pop_missing_default():
    store = MemoryStore()
    assert store.pop("nope", "default") == "default"


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------


def test_save_creates_file(tmp_path):
    p = tmp_path / "memory.json"
    store = MemoryStore(p, auto_load=False)
    store.set("key", "value")
    store.save()
    assert p.exists()


def test_save_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "memory.json"
    store = MemoryStore(p, auto_load=False)
    store.set("k", "v")
    store.save()
    assert p.exists()


def test_save_writes_valid_json(tmp_path):
    p = tmp_path / "memory.json"
    store = MemoryStore(p, auto_load=False)
    store.set("a", "1")
    store.save()
    data = json.loads(p.read_text())
    assert data == {"a": "1"}


def test_save_no_path_raises():
    store = MemoryStore()
    with pytest.raises(ValueError, match="No path"):
        store.save()


def test_save_explicit_path(tmp_path):
    store = MemoryStore()
    store.set("k", "v")
    p = tmp_path / "out.json"
    store.save(p)
    assert p.exists()


def test_load_restores_data(tmp_path):
    p = tmp_path / "memory.json"
    p.write_text(json.dumps({"x": "10", "y": "20"}))
    store = MemoryStore(auto_load=False)
    store.load(p)
    assert store.get("x") == "10"
    assert store.get("y") == "20"


def test_load_missing_file_is_noop(tmp_path):
    p = tmp_path / "missing.json"
    store = MemoryStore(auto_load=False)
    store.load(p)  # should not raise
    assert len(store) == 0


def test_load_empty_file_is_noop(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text("")
    store = MemoryStore(auto_load=False)
    store.load(p)
    assert len(store) == 0


def test_load_corrupt_json_is_noop(tmp_path):
    p = tmp_path / "corrupt.json"
    p.write_text("{bad json")
    store = MemoryStore(auto_load=False)
    store.load(p)  # should not raise
    assert len(store) == 0


def test_load_no_path_raises():
    store = MemoryStore()
    with pytest.raises(ValueError, match="No path"):
        store.load()


def test_save_load_roundtrip(tmp_path):
    p = tmp_path / "memory.json"
    store = MemoryStore(p, auto_load=False)
    store.set("a", "hello")
    store.set("b", "world")
    store.save()

    store2 = MemoryStore(p)
    assert store2.to_dict() == store.to_dict()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


def test_context_manager_auto_saves(tmp_path):
    p = tmp_path / "memory.json"
    with MemoryStore(p) as store:
        store.set("session", "1")
    # File should exist after context exit
    assert p.exists()
    data = json.loads(p.read_text())
    assert data["session"] == "1"


def test_context_manager_saves_on_exception(tmp_path):
    p = tmp_path / "memory.json"
    try:
        with MemoryStore(p) as store:
            store.set("partial", "yes")
            raise RuntimeError("oops")
    except RuntimeError:
        pass
    # Should still have saved
    assert p.exists()
    data = json.loads(p.read_text())
    assert data["partial"] == "yes"


def test_context_manager_no_path_no_error():
    # No path → __exit__ is a no-op
    with MemoryStore() as store:
        store.set("k", "v")
    # No exception raised


# ---------------------------------------------------------------------------
# to_dict / from_dict
# ---------------------------------------------------------------------------


def test_to_dict():
    store = MemoryStore()
    store.set("a", "1")
    store.set("b", "2")
    assert store.to_dict() == {"a": "1", "b": "2"}


def test_to_dict_is_copy():
    store = MemoryStore()
    store.set("k", "v")
    d = store.to_dict()
    d["k"] = "changed"
    assert store.get("k") == "v"


def test_from_dict():
    store = MemoryStore.from_dict({"x": "1", "y": "2"})
    assert store.get("x") == "1"
    assert store.get("y") == "2"


def test_from_dict_with_path(tmp_path):
    p = tmp_path / "memory.json"
    store = MemoryStore.from_dict({"k": "v"}, path=p)
    assert store.path == p
    assert store.get("k") == "v"


def test_roundtrip():
    store = MemoryStore.from_dict({"a": "hello", "b": "world"})
    store2 = MemoryStore.from_dict(store.to_dict())
    assert store2.to_dict() == store.to_dict()


# ---------------------------------------------------------------------------
# repr
# ---------------------------------------------------------------------------


def test_repr_contains_entries():
    store = MemoryStore()
    store.set("k", "v")
    r = repr(store)
    assert "k" in r
    assert "v" in r
