"""Glass-box demo (milestone M7).

Run with::

    streamlit run rcgate/demo/app.py -- --config ragtruth

or headless (writes the per-claim table to stdout instead of a browser)::

    python -m rcgate.demo.app --question "..." --answer "..." [--context ...] [--other-answer ...]

Scope, stated plainly:

* The app **loads** a serialized checkpoint and never trains (spec section 8, M7). If no
  checkpoint exists it refuses and names the command that produces one; a model fitted
  inside the request path would make the demo's numbers dependent on a random split
  chosen mid-presentation.
* One answer is analysed at a time. If the user pastes *other* models' answers to the same
  question, the real cross-model extractor runs against them; otherwise the cross family
  is neutral (0.5/0.5/1.0) and the row is flagged via ``cross_n_others``, exactly as in the
  batch pipeline. Nothing is invented to make the bars look interesting.
* Claims are sentences of the answer, de-aliased against the question and prior sentences,
  typed by the rule-based classifier, and scored by the same extractors the real builds
  use -- the demo is the batch pipeline with a UI, not a parallel implementation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from ..claims.claim_type import classify
from ..claims.dealias import (
    dealias_answer,
    split_sentences,  # noqa: F401  (re-exported for tests)
)
from ..config import Config, load_named
from ..data.schema import CLAIM_TYPE_NAMES, validate
from ..explain import one_line
from ..paths import SUMMARY_DIR

DEMO_QUESTION_ID = "demo"

#: What the sidebar shows when metrics.json (written by every pipeline run) is present.
_PROVENANCE_KEYS = ["variant", "seed", "git", "config", "table"]


# ---------------------------------------------------------------------------
# checkpoint resolution
# ---------------------------------------------------------------------------


def resolve_checkpoint(
    checkpoint: str | Path | None = None, cfg: Config | None = None
) -> tuple[Path, dict]:
    """Find the newest A7 checkpoint under ``results/summary`` and its provenance.

    Returns ``(path, provenance)``. ``provenance`` is ``{}`` when no ``metrics.json``
    sits next to the checkpoint. Raises ``FileNotFoundError`` with the exact remedy
    rather than falling back to training: constraint C5 wants the demo's numbers
    traceable to a recorded run, and spec M7 wants no training in the app.

    Both checkpoint forms the pipeline writes are accepted: ``model.pt`` (a bare
    ``torch.nn.Module``) and ``model.joblib`` (the usual case -- the wrapper
    :class:`RCGateModel` is not itself an ``nn.Module``, so ``persist`` pickles it).
    """
    candidates: list[Path] = []
    if checkpoint is not None:
        candidates.append(Path(checkpoint))
    tag = str(cfg.get("report.tag", "run")) if cfg is not None else None
    if SUMMARY_DIR.exists():
        found = sorted(
            SUMMARY_DIR.glob(f"{'*' if tag is None else tag}/A7_seed*/model.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        candidates.extend(found)
    for path in candidates:
        if path.exists():
            provenance = {}
            metrics_json = path.parent / "metrics.json"
            if metrics_json.exists():
                try:
                    payload = json.loads(metrics_json.read_text())
                    provenance = {k: payload.get(k) for k in _PROVENANCE_KEYS}
                except (json.JSONDecodeError, OSError):
                    provenance = {}
            return path, provenance
    searched = ", ".join(str(c) for c in candidates) or str(SUMMARY_DIR / "<tag>/A7_seed*/model.pt")
    raise FileNotFoundError(
        "no trained RC-Gate checkpoint found (searched: "
        f"{searched}). Train one first, e.g. `python -m rcgate.evaluate --config synthetic` "
        "-- the demo loads checkpoints and never trains."
    )


# ---------------------------------------------------------------------------
# signal extraction for a single answer
# ---------------------------------------------------------------------------


def build_frame(
    question: str,
    answer: str,
    context: str = "",
    other_answers: list[str] | None = None,
    benchmark: str = "demo",
) -> pd.DataFrame:
    """One answer -> a claim frame with metadata columns; signals are filled later.

    ``other_answers`` are the other generators' answers to the same question. Rows carry
    ``generator_id=0`` (the analysed answer) and the others are numbered from 1, matching
    the ``answers_by_question`` mapping the batch pipeline passes to the extractors.
    """
    results = dealias_answer(answer, question=question)
    rows = []
    for i, res in enumerate(results):
        text = res.text
        if not text.strip():
            continue
        kind = classify(text, context or None)
        rows.append(
            {
                "question_id": DEMO_QUESTION_ID,
                "claim_id": f"demo-{i}",
                "benchmark": benchmark,
                "claim_text": text,
                "claim_type": int(kind.claim_type),
                "generator_id": 0,
                "label": 0,  # the demo has no ground truth; the contract requires the column
            }
        )
    return pd.DataFrame(rows)


def analyse(
    question: str,
    answer: str,
    context: str = "",
    other_answers: list[str] | None = None,
    model=None,
    cfg: Config | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Extract signals for one answer and score it with the loaded model.

    Returns ``(per_claim, info)`` where ``per_claim`` is one row per claim with the
    verdict, both gate weights and the one-line explanation, and ``info`` records the
    backend and how many cross-model comparisons were actually available.
    """
    from ..signals.extract import extract_signals
    from ..signals.nli import build_cached

    cfg = cfg if cfg is not None else load_named("ragtruth")
    frame = build_frame(question, answer, context, benchmark=str(cfg.get("data.benchmark", "demo")))
    if frame.empty:
        return pd.DataFrame(), {"backend": "none", "n_claims": 0}

    answers_by_question = {DEMO_QUESTION_ID: {0: answer}}
    for j, other in enumerate(other_answers or [], start=1):
        answers_by_question[DEMO_QUESTION_ID][j] = other

    scorer, embedder, _cache = build_cached(cfg)
    filled, _report = extract_signals(
        frame, cfg=cfg, answers_by_question=answers_by_question, scorer=scorer, embedder=embedder
    )
    validate(filled).raise_if_failed()

    n_others = max((len(v) - 1 for v in answers_by_question.values()), default=0)
    info = {
        "backend": getattr(scorer, "name", "unknown"),
        "n_claims": len(filled),
        "n_other_answers": n_others,
    }

    preds = model.predict(filled)
    rows = []
    for i, p in enumerate(preds):
        claim_type = int(filled["claim_type"].iloc[i])
        row = filled.iloc[i]
        rows.append(
            {
                "claim_id": row["claim_id"],
                "claim_text": str(row["claim_text"]),
                "claim_type": claim_type,
                "prob": round(p.prob, 4),
                "w_cross": round(p.w_cross, 4),
                "w_evid": round(p.w_evid, 4),
                "z_cross": round(p.z_cross, 4),
                "z_evid": round(p.z_evid, 4),
                "cross_n_others": int(row["cross_n_others"]) if "cross_n_others" in filled else 0,
                "explanation": one_line(
                    p.prob, p.w_evid, CLAIM_TYPE_NAMES[claim_type], p.z_cross, p.z_evid
                ),
            }
        )
    return pd.DataFrame(rows), info


# ---------------------------------------------------------------------------
# streamlit UI
# ---------------------------------------------------------------------------


def _load_model(cfg: Config, checkpoint: str | Path | None):
    """Load a serialized RC-Gate checkpoint, or die loudly naming the remedy."""
    from ..models.rcgate import RCGateConfig, RCGateModel

    path, provenance = resolve_checkpoint(checkpoint, cfg)
    import torch

    if path.suffix == ".pt":
        state = torch.load(path, map_location="cpu", weights_only=False)
    else:
        import joblib

        state = joblib.load(path)
    if isinstance(state, RCGateModel):
        model = state
    elif isinstance(state, torch.nn.Module):
        model = RCGateModel(RCGateConfig(n_generators=int(cfg.get("model.n_generators", 6))))
        model.model.load_state_dict(state.state_dict())
    else:
        raise ValueError(f"{path} is not an RC-Gate checkpoint")
    return path, provenance, model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rcgate.demo", description="Glass-box RC-Gate demo.")
    parser.add_argument("--config", default="ragtruth", help="config name; sets the model shape and backend")
    parser.add_argument("--checkpoint", default=None, help="path to a model.pt; default: newest A7 under results/summary")
    parser.add_argument("--question", default=None, help="headless mode: the user question")
    parser.add_argument("--answer", default=None, help="headless mode: the answer to analyse")
    parser.add_argument("--context", default="", help="headless mode: optional evidence context")
    parser.add_argument("--other-answer", action="append", default=[], help="headless mode: another model's answer (repeatable)")
    args, _unknown = parser.parse_known_args(argv)  # unknown: streamlit's own flags, ignored
    cfg = load_named(args.config)
    path, provenance, model = _load_model(cfg, args.checkpoint)

    if args.question and args.answer:
        per_claim, info = analyse(
            args.question, args.answer, args.context, args.other_answer, model=model, cfg=cfg
        )
        print(f"checkpoint: {path}")
        print(json.dumps(provenance, indent=2))
        print(json.dumps(info, indent=2))
        if per_claim.empty:
            print("no claims extracted")
            return 0
        with pd.option_context("display.width", 200, "display.max_colwidth", 80):
            print(
                per_claim[
                    ["claim_text", "claim_type", "prob", "w_cross", "w_evid", "explanation"]
                ].to_string(index=False)
            )
        return 0

    try:
        import streamlit as st
    except ModuleNotFoundError:  # pragma: no cover - streamlit is optional to import
        print(
            "streamlit is not installed; either `pip install streamlit` or use the headless "
            "mode: python -m rcgate.demo.app --question ... --answer ...",
            file=sys.stderr,
        )
        return 1

    st.set_page_config(page_title="RC-Gate glass box", layout="wide")
    st.title("RC-Gate — glass-box hallucination detection")
    st.caption(
        f"checkpoint `{path}` · variant {provenance.get('variant', 'A7')} · "
        f"seed {provenance.get('seed', '?')} · git {provenance.get('git', '?')}"
    )

    with st.sidebar:
        st.header("What you are looking at")
        st.markdown(
            "Every claim is scored by two experts: one reading **cross-model signals** "
            "(do other models agree?), one reading **evidence signals** (does the context "
            "support it?). A tiny gate decides how much to trust each family *for this "
            "claim*, based only on the claim type and which model produced it."
        )
        st.markdown(
            f"backend: `{st.session_state.get('backend', 'see run')}` · "
            "the stacked bar is the gate's trust split; it always sums to 1."
        )

    question = st.text_area("Question", height=68, placeholder="What did the report say about revenue?")
    context = st.text_area("Context / evidence (optional)", height=120)
    answer = st.text_area("Answer to analyse", height=140, placeholder="Paste one model's answer here.")
    others_raw = st.text_area(
        "Other models' answers (optional, one per blank line)",
        height=100,
        help="Enables the cross-model family. Leave empty and the cross signals stay neutral and flagged.",
    )
    others = [o for o in others_raw.split("\n\n") if o.strip()] if others_raw else []

    go = st.button("Analyse", type="primary")
    if go and not answer.strip():
        st.warning("Paste an answer first.")
    elif go:
        with st.spinner("Extracting claims and signals..."):
            per_claim, info = analyse(question, answer, context, others, model=model, cfg=cfg)
        st.session_state["backend"] = info.get("backend", "?")
        if per_claim.empty:
            st.warning("No claims extracted from that answer.")
            return 0
        st.subheader(f"{len(per_claim)} claims")
        for _, row in per_claim.iterrows():
            with st.expander(f"p={row['prob']:.2f} · {row['explanation']}"):
                st.markdown(f"**Claim** — {row['claim_text']}")
                left, right = st.columns([1, 2])
                with left:
                    st.metric("P(hallucination)", f"{row['prob']:.3f}")
                    st.caption(f"claim type: {row['claim_type']}")
                with right:
                    st.markdown("Gate trust split")
                    st.progress(
                        row["w_cross"],
                        text=f"w_cross {row['w_cross']:.2f} / w_evid {row['w_evid']:.2f}",
                    )
                    st.caption(
                        f"expert logits: z_cross {row['z_cross']:+.2f}, z_evid {row['z_evid']:+.2f}"
                        + (
                            f" · only {row['cross_n_others']} other model(s) available"
                            if row["cross_n_others"] > 0
                            else ""
                        )
                    )
        st.dataframe(
            per_claim[["claim_text", "claim_type", "prob", "w_cross", "w_evid", "explanation"]],
            use_container_width=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
