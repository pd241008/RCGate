"""Cache hit/miss, key stability, dry-run and budget behaviour (constraint C3)."""

from __future__ import annotations

import pytest

from rcgate.signals.cache import Budget, DiskCache, DryRunMiss, make_key


def test_miss_then_hit_calls_fn_once(tiny_cache):
    calls = []

    def fake(prompt):
        calls.append(prompt)
        return {"text": f"answer:{prompt}"}

    first = tiny_cache.call("openai", "gpt-4o-mini", "what is 6*7", fake)
    second = tiny_cache.call("openai", "gpt-4o-mini", "what is 6*7", fake)

    assert first == second == {"text": "answer:what is 6*7"}
    assert len(calls) == 1, "second call must be served from disk"
    assert tiny_cache.stats.hits == 1
    assert tiny_cache.stats.misses == 1
    assert tiny_cache.stats.calls_made == 1


def test_different_prompt_is_a_different_key(tiny_cache):
    seen = []

    def fake(prompt):
        seen.append(prompt)
        return prompt

    a = tiny_cache.call("openai", "m", "prompt a", fake)
    b = tiny_cache.call("openai", "m", "prompt b", fake)
    assert a != b
    assert seen == ["prompt a", "prompt b"]


def test_key_is_order_insensitive_in_params():
    assert make_key("p", "m", "x", {"a": 1, "b": 2}) == make_key("p", "m", "x", {"b": 2, "a": 1})


def test_key_changes_with_model_and_provider():
    base = make_key("openai", "m1", "x")
    assert base != make_key("openai", "m2", "x")
    assert base != make_key("anthropic", "m1", "x")


def test_dry_run_refuses_uncached_call(tmp_path):
    cache = DiskCache(root=tmp_path / "c", budget=Budget(dry_run=True))
    with pytest.raises(DryRunMiss):
        cache.call("openai", "m", "uncached", lambda p: "nope")
    assert cache.stats.blocked == 1
    assert cache.stats.calls_made == 0


def test_dry_run_still_serves_cached_call(tmp_path):
    cache = DiskCache(root=tmp_path / "c", budget=Budget(dry_run=False))
    cache.call("openai", "m", "warm", lambda p: "value")
    cache.budget.dry_run = True
    assert cache.call("openai", "m", "warm", lambda p: "explode") == "value"


def test_max_calls_cap(tmp_path):
    from rcgate.signals.cache import BudgetExceeded

    cache = DiskCache(root=tmp_path / "c", budget=Budget(dry_run=False, max_calls=2))
    for i in range(2):
        cache.call("openai", "m", f"p{i}", lambda p: p)
    with pytest.raises(BudgetExceeded):
        cache.call("openai", "m", "p3", lambda p: p)


def test_max_usd_cap(tmp_path):
    from rcgate.signals.cache import BudgetExceeded

    cache = DiskCache(root=tmp_path / "c", budget=Budget(dry_run=False, max_usd=0.0005))
    cache.call("openai", "m", "a", lambda p: p, cost_usd=0.0004)
    with pytest.raises(BudgetExceeded):
        cache.call("openai", "m", "b", lambda p: p, cost_usd=0.0004)


def test_corrupt_cache_entry_is_treated_as_a_miss(tiny_cache):
    key = make_key("openai", "m", "corrupt")
    tiny_cache.put(key, {"ok": True})
    tiny_cache.path_for(key).write_text("{not json")
    assert tiny_cache.get(key) is None
    assert tiny_cache.call("openai", "m", "corrupt", lambda p: "fresh") == "fresh"


def test_report_tracks_cost(tiny_cache):
    tiny_cache.call("openai", "m", "costed", lambda p: 1, cost_usd=0.00025)
    report = tiny_cache.report()
    assert report["calls_made"] == 1
    assert report["usd_spent"] == pytest.approx(0.00025)
