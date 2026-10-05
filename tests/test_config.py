"""Config loading: inheritance, dot access, defaults, and provenance."""

from __future__ import annotations

import pytest

from rcgate.config import available_configs, load_config, load_named, write_config


def test_named_config_loads():
    cfg = load_named("synthetic")
    assert cfg.get("data.benchmark") == "synthetic"
    assert cfg.get("model.gate_hidden") == 16


def test_inheritance_overrides_only_the_named_key():
    base = load_named("base")
    syn = load_named("synthetic")
    # overridden in synthetic.yaml
    assert syn.get("data.n_generators") == 5
    # inherited from base.yaml, not restated in synthetic.yaml
    assert syn.get("train.weight_decay") == base.get("train.weight_decay")
    assert syn.get("eval.ece_bins") == 15


def test_dot_access_returns_config_for_nested_maps():
    cfg = load_named("base")
    assert cfg.model.gate_hidden == 16
    assert cfg.data.n_generators == 3


def test_missing_key_raises_unless_default_given():
    cfg = load_named("base")
    with pytest.raises(KeyError):
        cfg.get("train.does_not_exist")
    assert cfg.get("train.does_not_exist", "fallback") == "fallback"


def test_config_files_are_reported_without_extension():
    names = available_configs()
    assert "base" in names and "synthetic" in names and "smoke" in names


def test_write_config_roundtrips(tmp_path):
    cfg = load_named("smoke")
    path = write_config(tmp_path / "resolved.yaml", cfg)
    again = load_config(path)
    assert again.get("train.epochs") == 2
    assert again.to_dict() == cfg.to_dict()


def test_every_variant_relevant_key_is_defined_in_base():
    """Guard against a typo silently falling back to a default."""
    cfg = load_named("base")
    for key in [
        "model.gate_hidden",
        "model.gate_temp",
        "model.fusion_input",
        "model.unk_dropout",
        "train.lr",
        "train.epochs",
        "train.patience",
        "eval.n_bootstrap",
        "eval.n_seeds",
        "eval.ece_bins",
        "data.n_generators",
        "budget.max_usd",
        "budget.dry_run",
    ]:
        cfg.get(key)
