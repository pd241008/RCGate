"""RC-Gate unit tests: architecture, parameter budget, and the gate's own guarantees.

These are the tests section 9 asks for: gate output sums to 1, the ``UNK`` path does not
crash, gate weights are always returned, and the parameter count stays under the cap.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import torch

from rcgate.data.schema import CROSS_SIGNALS, EVID_SIGNALS, SIGNALS, UNK_GENERATOR
from rcgate.data.splits import grouped_split
from rcgate.data.synthetic import generate, load_planted
from rcgate.models.gate import Gate, MetadataEncoder
from rcgate.models.meta import Prediction
from rcgate.models.rcgate import (
    RCGate,
    RCGateConfig,
    RCGateModel,
    build_gate_variant,
    frame_to_batch,
)

N_GENERATORS = 5


@pytest.fixture(scope="module")
def table():
    return generate(load_planted(), seed=0, n_questions=250)


@pytest.fixture(scope="module")
def split(table):
    return grouped_split(table, seed=0)


# -- gate --------------------------------------------------------------------


def test_gate_weights_sum_to_one():
    gate = Gate(in_dim=8, hidden=16, tau=1.0)
    x = torch.randn(64, 8)
    w = gate(x)
    assert w.shape == (64, 2)
    assert torch.allclose(w.sum(dim=-1), torch.ones(64), atol=1e-6)
    assert (w >= 0).all()


def test_gate_temperature_sharpens_weights():
    x = torch.randn(256, 8)
    soft = Gate(8, 16, tau=8.0)(x)  # dividing by a large tau flattens
    sharp = Gate(8, 16, tau=0.25)(x)
    assert (soft - 0.5).abs().max() < (sharp - 0.5).abs().max()


def test_gate_rejects_non_positive_temperature():
    with pytest.raises(ValueError):
        Gate(8, 16, tau=0.0)


def test_encoder_dimensions_follow_the_spec():
    enc = MetadataEncoder(n_generators=N_GENERATORS, type_dim=4, generator_dim=4)
    assert enc.output_dim == 8
    out = enc(torch.zeros(5, dtype=torch.long), torch.zeros(5, dtype=torch.long))
    assert out.shape == (5, 8)


def test_encoder_has_a_reserved_row_for_unknown_generators():
    enc = MetadataEncoder(n_generators=N_GENERATORS, type_dim=4, generator_dim=4)
    assert enc.unk_index == N_GENERATORS
    assert enc.gen_emb.num_embeddings == N_GENERATORS + 1


def test_claim_type_only_encoder_omits_the_generator_block():
    enc = MetadataEncoder(n_generators=N_GENERATORS, type_dim=4, generator_dim=0)
    out = enc(torch.zeros(3, dtype=torch.long), torch.zeros(3, dtype=torch.long))
    assert out.shape == (3, 4)


# -- the gate must not see the signals --------------------------------------


def test_gate_input_is_metadata_only_by_default():
    cfg = RCGateConfig(n_generators=N_GENERATORS)
    model = RCGate(cfg)
    assert model.encoder.see_signals is False
    assert model.encoder.output_dim == 8


def test_weights_do_not_depend_on_signal_values():
    """The whole claim of the method: changing a signal must not move the gate weights."""
    model = RCGate(RCGateConfig(n_generators=N_GENERATORS)).eval()
    batch = frame_to_batch(pd.DataFrame(
        {
            "claim_type": [0, 1, 2, 3],
            "generator_id": [0, 1, 2, 3],
            **{c: [0.5] * 4 for c in SIGNALS},
        }
    ), N_GENERATORS)

    base = model.explain(**batch)
    bumped = {k: v.clone() for k, v in batch.items()}
    bumped["s_cross"] = bumped["s_cross"] * 0.0 + 0.99
    bumped["s_evid"] = bumped["s_evid"] * 0.0 + 0.01
    after = model.explain(**bumped)

    assert np.allclose(base["w_cross"], after["w_cross"]), "gate weights moved with the signals"
    assert np.allclose(base["w_evid"], after["w_evid"])


def test_signals_do_change_the_experts_and_the_probability():
    """Sanity check on the test above: the signals are used, just not by the gate."""
    model = RCGate(RCGateConfig(n_generators=N_GENERATORS)).eval()
    batch = frame_to_batch(pd.DataFrame(
        {
            "claim_type": [0, 1, 2, 3],
            "generator_id": [0, 1, 2, 3],
            **{c: [0.5] * 4 for c in SIGNALS},
        }
    ), N_GENERATORS)
    bumped = {k: v.clone() for k, v in batch.items()}
    bumped["s_cross"] = bumped["s_cross"] * 0.0 + 0.99
    bumped["s_evid"] = bumped["s_evid"] * 0.0 + 0.99
    assert not np.allclose(
        model.explain(**batch)["prob"], model.explain(**bumped)["prob"]
    )


def test_sees_signals_ablation_is_opt_in_and_labelled():
    model = RCGate(RCGateConfig(n_generators=N_GENERATORS, see_signals_in_gate=True))
    assert model.encoder.see_signals is True
    assert model.encoder.output_dim == 8 + len(SIGNALS)


# -- parameter budget (constraint C2) ---------------------------------------


def test_full_model_is_well_under_the_parameter_cap():
    model = RCGate(RCGateConfig(n_generators=N_GENERATORS))
    assert model.n_parameters < 50_000, f"{model.n_parameters} parameters exceeds the 50k budget"
    # The spec's architecture in full: two 4-d embeddings, a 16-unit hidden layer, three
    # single-output linear layers.
    assert model.n_parameters < 400, f"expected a very small model, got {model.n_parameters}"


# -- prediction record (constraint C5) --------------------------------------


def test_predict_returns_predictions_not_a_bare_array(split):
    model = RCGateModel(RCGateConfig(n_generators=N_GENERATORS, epochs=2, batch_size=256))
    model.fit(split.train.head(400), split.val.head(200), None)
    preds = model.predict(split.test.head(50))

    assert len(preds) == 50
    assert all(isinstance(p, Prediction) for p in preds)
    for p in preds[:10]:
        assert 0.0 <= p.prob <= 1.0
        assert p.w_cross + p.w_evid == pytest.approx(1.0, abs=1e-5)
        assert p.preferred_family in ("evidence", "cross-model")
        assert set(p.as_dict()) >= {"prob", "w_cross", "w_evid", "z_cross", "z_evid"}


def test_prediction_rejects_an_out_of_range_probability():
    with pytest.raises(ValueError):
        Prediction(prob=1.4, w_cross=0.5, w_evid=0.5, z_cross=0.0, z_evid=0.0)


# -- the UNK cold-start path -------------------------------------------------


def test_unk_generator_does_not_crash(split):
    frame = split.test.copy()
    frame["generator_id"] = UNK_GENERATOR
    model = RCGateModel(RCGateConfig(n_generators=N_GENERATORS, epochs=2, batch_size=256))
    preds = model.predict(frame)
    assert len(preds) == len(frame)
    assert all(p.w_cross + p.w_evid == pytest.approx(1.0, abs=1e-5) for p in preds)


def test_unk_path_uses_the_reserved_embedding_row(split):
    frame = split.test.copy()
    frame["generator_id"] = UNK_GENERATOR
    batch = frame_to_batch(frame, N_GENERATORS)
    assert int(batch["generator_id"].max()) == N_GENERATORS


def test_unk_and_real_generators_produce_different_weights(split):
    """If UNK collapsed onto a real generator, cold start would be silently wrong."""
    model = RCGate(RCGateConfig(n_generators=N_GENERATORS)).eval()
    n = 6
    frame = pd.DataFrame({
        "claim_type": [0] * n,
        "generator_id": [0] * (n // 2) + [UNK_GENERATOR] * (n - n // 2),
        **{c: [0.5] * n for c in SIGNALS},
    })
    w = model.explain(**frame_to_batch(frame, N_GENERATORS))["w_cross"]
    assert not np.allclose(w[: n // 2], w[n // 2 :])


# -- variants ----------------------------------------------------------------


@pytest.mark.parametrize(
    "variant,use_type,use_generator,expected_dim",
    [("A7", True, True, 8), ("A5", True, False, 4), ("A6", False, True, 4)],
)
def test_gate_variant_input_dimensions(variant, use_type, use_generator, expected_dim):
    model = build_gate_variant(variant, _cfg_stub(), seed=0)
    assert model.config.use_claim_type is use_type
    assert model.config.use_generator is use_generator
    assert model.model.encoder.output_dim == expected_dim


def test_a7_gate_is_eight_dimensional():
    model = build_gate_variant("A7", _cfg_stub(), seed=0)
    assert model.model.encoder.output_dim == 8
    assert model.model.config.fusion_input == "logit"


def test_fusion_input_config_is_honoured():
    """``fusion_input: prob`` must scale by sigmoid(z), not by the raw logit."""
    batch = frame_to_batch(
        pd.DataFrame({"claim_type": [0], "generator_id": [0], **{c: [0.5] for c in SIGNALS}}),
        N_GENERATORS,
    )
    model = RCGate(RCGateConfig(n_generators=N_GENERATORS, fusion_input="prob")).eval()
    out = model(**batch)
    expected_cross = out["w"][0, 0] * torch.sigmoid(model.cross_expert(batch["s_cross"]))
    assert torch.allclose(out["fused"][0, 0], expected_cross, atol=1e-6)

    logit_model = RCGate(RCGateConfig(n_generators=N_GENERATORS, fusion_input="logit")).eval()
    out_logit = logit_model(**batch)
    expected_cross_logit = out_logit["w"][0, 0] * logit_model.cross_expert(batch["s_cross"])
    assert torch.allclose(out_logit["fused"][0, 0], expected_cross_logit, atol=1e-6)


# -- smoke test (section 9) ---------------------------------------------------


def test_a7_trains_for_two_epochs_on_200_rows_in_under_10_seconds(split):
    import time

    model = RCGateModel(RCGateConfig(n_generators=N_GENERATORS, epochs=2, batch_size=64))
    small_train = split.train.head(200)
    started = time.perf_counter()
    info = model.fit(small_train, split.val.head(100), None)
    elapsed = time.perf_counter() - started
    assert elapsed < 10.0, f"smoke fit took {elapsed:.2f}s"
    assert info["epochs_run"] == 2
    probs = model.predict_proba(split.test.head(100))
    assert probs.shape == (100,)
    assert ((probs >= 0) & (probs <= 1)).all()


def test_experts_use_only_their_own_signal_family():
    """Perturbing one family must move its own expert logit and leave the other alone."""
    model = RCGate(RCGateConfig(n_generators=N_GENERATORS)).eval()
    n = 4
    frame = pd.DataFrame({
        "claim_type": [1] * n,
        "generator_id": [1] * n,
        **{c: [0.5] * n for c in SIGNALS},
    })
    batch = frame_to_batch(frame, N_GENERATORS)
    base = model.explain(**batch)

    cross_only = {k: v.clone() for k, v in batch.items()}
    cross_only["s_cross"] = cross_only["s_cross"] * 0.0 + 0.9
    after_cross = model.explain(**cross_only)
    assert not np.allclose(base["z_cross"], after_cross["z_cross"])
    assert np.allclose(base["z_evid"], after_cross["z_evid"]), "cross family leaked into z_evid"

    evid_only = {k: v.clone() for k, v in batch.items()}
    evid_only["s_evid"] = evid_only["s_evid"] * 0.0 + 0.9
    after_evid = model.explain(**evid_only)
    assert not np.allclose(base["z_evid"], after_evid["z_evid"])
    assert np.allclose(base["z_cross"], after_evid["z_cross"]), "evidence family leaked into z_cross"


def test_cross_and_evidence_columns_are_the_documented_three():
    assert CROSS_SIGNALS == ["agree", "contra", "sem_dist"]
    assert EVID_SIGNALS == ["support", "src_quality", "conflict"]


def _cfg_stub():
    from rcgate.config import load_named

    cfg = load_named("synthetic")
    cfg.to_dict()
    return cfg
