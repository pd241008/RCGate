"""CLI surface and the variant registry."""

from __future__ import annotations

import pytest

from rcgate.train import build_parser, main
from rcgate.variants import ALL_VARIANTS, VARIANTS, is_runnable


def test_train_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--all-variants" in out
    assert "--config" in out


def test_parser_defaults_to_full_rcgate():
    args = build_parser().parse_args([])
    assert args.variant == "A7"
    assert args.config == "synthetic"


def test_every_variant_is_documented():
    for vid in ALL_VARIANTS:
        v = VARIANTS[vid]
        assert v.name and v.purpose, vid


def test_a8_is_skipped_without_judge_votes():
    import pandas as pd

    df = pd.DataFrame({"claim_id": ["a"], "label": [0]})
    ok, reason = is_runnable("A8", df)
    assert not ok
    assert "skipped" in reason

    df["judge_votes"] = [1]
    df["judge_n"] = [3]
    assert is_runnable("A8", df)[0]
