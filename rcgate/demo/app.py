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
* One answer is analysed at a time. Its generator identity is the one the user selects.
  The default is the reserved unknown id, which the model maps onto its extra embedding
  row. The answer text is never used to guess a generator. If the user pastes *other*
  models' answers to the same question, the real cross-model extractor runs against them;
  otherwise the cross family keeps the extractor's documented fallback (0.5/0.5/1.0) and
  the row is flagged via ``cross_n_others``. Nothing is invented to make the bars look
  interesting.
* Claims are sentences of the answer, de-aliased against the question and prior sentences,
  typed by the rule-based classifier, and scored by the same extractors the real builds
  use -- the demo is the batch pipeline with a UI, not a parallel implementation.
* Source text the user pastes is stored on each claim. The evidence extractor and the
  arithmetic checker read that column; without it they would keep their no-context defaults
  even though a source had been provided.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:
    # `streamlit run rcgate/demo/app.py` and Streamlit's AppTest execute this file as a
    # bare script, so the package-relative imports below would fail with "attempted
    # relative import with no known parent package". Put the project root on sys.path and
    # declare the package; `python -m rcgate.demo.app` skips this branch entirely.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "rcgate.demo"

import pandas as pd

from ..claims.claim_type import classify
from ..claims.dealias import (
    dealias_answer,
    split_sentences,  # noqa: F401  (re-exported for tests)
)
from ..config import Config, load_named
from ..data.schema import CLAIM_TYPE_NAMES, SIGNALS, UNK_GENERATOR, validate
from ..explain import one_line
from ..paths import PROJECT_ROOT, SUMMARY_DIR
from ..signals.cross_model import NEUTRAL_AGREE, NEUTRAL_CONTRA, NEUTRAL_SEM_DIST

DEMO_QUESTION_ID = "demo"

#: What the sidebar shows when metrics.json (written by every pipeline run) is present.
_PROVENANCE_KEYS = ["variant", "seed", "git", "config", "table"]


# ---------------------------------------------------------------------------
# checkpoint resolution
# ---------------------------------------------------------------------------


def result_namespace(path: str | Path) -> str | None:
    """Result directory under ``results/summary`` that contains this checkpoint.

    The pipeline writes each run to ``<report tag>/<variant>_seed<seed>/``. That tag
    directory is the result namespace. A path outside ``results/summary`` has none.
    """
    try:
        relative = Path(path).resolve().relative_to(SUMMARY_DIR.resolve())
    except ValueError:
        return None
    if not relative.parts:
        return None
    return relative.parts[0]


def resolve_checkpoint(
    checkpoint: str | Path | None = None, cfg: Config | None = None
) -> tuple[Path, dict]:
    """Find the newest A7 checkpoint under the config's result namespace, plus provenance.

    Returns ``(path, provenance)``. Variant, seed, git, config, and table come from the
    sibling ``metrics.json`` when that file parses. The result namespace is the artifact's
    own ``namespace`` field when it has one, otherwise the directory under
    ``results/summary``. ``provenance`` stays empty when neither source has anything to
    say. Raises ``FileNotFoundError`` with the exact remedy rather than falling back to
    training: constraint C5 wants the demo's numbers traceable to a recorded run, and
    spec M7 wants no training in the app. The search stays on the config's report tag.
    It does not substitute a checkpoint from another namespace.

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
            provenance: dict = {}
            metrics_json = path.parent / "metrics.json"
            if metrics_json.exists():
                try:
                    payload = json.loads(metrics_json.read_text())
                    if isinstance(payload, dict):
                        provenance = {k: payload.get(k) for k in _PROVENANCE_KEYS}
                        recorded = payload.get("namespace")
                        if isinstance(recorded, str) and recorded.strip():
                            provenance["namespace"] = recorded.strip()
                except (json.JSONDecodeError, OSError):
                    provenance = {}
            if "namespace" not in provenance:
                namespace = result_namespace(path)
                if namespace:
                    provenance["namespace"] = namespace
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


def _text_cell(row: pd.Series, column: str) -> str | None:
    """A provenance string from an extractor column, or None when it was not emitted."""
    if column not in row.index:
        return None
    value = row[column]
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def _int_cell(row: pd.Series, column: str) -> int | None:
    if column not in row.index:
        return None
    value = row[column]
    if value is None or pd.isna(value):
        return None
    return int(value)


UNKNOWN_GENERATOR_LABEL = "Unknown / not specified"

GENERATOR_IDENTITY_LIMITATION = (
    "This checkpoint has no generator embedding, so an unknown identity cannot be "
    "represented as its own row. The pasted answer is not given a named roster identity."
)


@dataclass(frozen=True)
class GeneratorOption:
    """One identity the loaded checkpoint can score."""

    generator_id: int
    label: str


def _model_n_generators(model) -> int:
    config = getattr(model, "config", None)
    n_generators = getattr(config, "n_generators", None)
    if n_generators is None:
        raise ValueError(
            "the loaded model does not expose n_generators; refusing to assign a roster index"
        )
    return int(n_generators)


def unknown_identity_supported(model) -> bool:
    """True when the checkpoint has the reserved UNK embedding row.

    That row is ``n_generators`` wide in the existing encoder: real roster ids occupy
    ``0 .. n_generators-1`` and :data:`UNK_GENERATOR` is mapped onto the extra row by
    :func:`rcgate.models.rcgate.frame_to_batch`.
    """
    config = getattr(model, "config", None)
    if config is None or not bool(getattr(config, "use_generator", False)):
        return False
    if int(getattr(config, "generator_emb_dim", 0)) <= 0:
        return False
    encoder = getattr(getattr(model, "model", None), "encoder", None)
    embedding = getattr(encoder, "gen_emb", None) if encoder is not None else None
    if embedding is None:
        return False
    n_generators = int(config.n_generators)
    return (
        int(embedding.num_embeddings) == n_generators + 1
        and int(getattr(encoder, "unk_index", -2)) == n_generators
    )


def generator_options(model, cfg: Config) -> list[GeneratorOption]:
    """Roster identities the loaded embedding can score, plus unknown when that row exists.

    Names come from ``data.roster``. Slots past the embedding width are omitted. The
    answer text is not consulted.
    """
    if not unknown_identity_supported(model):
        return []
    n_generators = _model_n_generators(model)
    roster = cfg.get("data.roster", [])
    names = [str(item) for item in roster] if isinstance(roster, list) else []
    options = [GeneratorOption(UNK_GENERATOR, UNKNOWN_GENERATOR_LABEL)]
    for index in range(n_generators):
        if index < len(names) and names[index].strip():
            label = names[index]
        else:
            label = f"generator {index}"
        options.append(GeneratorOption(index, label))
    return options


def generator_label(generator_id: int, model, cfg: Config) -> str:
    for option in generator_options(model, cfg):
        if option.generator_id == int(generator_id):
            return option.label
    if int(generator_id) == UNK_GENERATOR:
        return UNKNOWN_GENERATOR_LABEL
    return f"generator {int(generator_id)}"


def _answers_for_question(
    generator_id: int, answer: str, other_answers: list[str] | None
) -> dict[int, str]:
    """Map the analysed answer onto its selected id and the comparisons onto other ids.

    Comparison ids are only keys for the extractor. They are not roster labels, and a
    blank comparison is dropped rather than counted as a model.
    """
    assigned: dict[int, str] = {int(generator_id): answer}
    slot = 0
    for other in other_answers or []:
        if not str(other).strip():
            continue
        while slot == int(generator_id):
            slot += 1
        assigned[slot] = str(other)
        slot += 1
    return assigned


def build_frame(
    question: str,
    answer: str,
    context: str = "",
    other_answers: list[str] | None = None,
    benchmark: str = "demo",
    generator_id: int = UNK_GENERATOR,
) -> pd.DataFrame:
    """One answer -> a claim frame with metadata columns; signals are filled later.

    ``other_answers`` are accepted for signature compatibility and attached later, in
    :func:`analyse`. ``generator_id`` is the selected identity, defaulting to the unknown
    sentinel. It is never inferred from ``answer``. ``context`` is stored on every row so
    claim typing and the evidence extractor see the same source. An empty string leaves
    the extractor on its no-context path.
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
                "generator_id": int(generator_id),
                "label": 0,  # the demo has no ground truth; the contract requires the column
                "context": context or "",
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
    generator_id: int | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Extract signals for one answer and score it with the loaded model.

    Returns ``(per_claim, info)`` where ``per_claim`` is one row per claim with the
    verdict, both gate weights, the six extracted signals, and the one-line explanation.
    ``info`` records the backend, the generator id that reached the model, and how many
    cross-model comparisons were actually available. ``generator_id`` defaults to the
    unknown sentinel. It is taken from the caller, never from the answer text.
    """
    from ..signals.extract import extract_signals
    from ..signals.nli import build_cached

    cfg = cfg if cfg is not None else load_named("ragtruth")
    gid = UNK_GENERATOR if generator_id is None else int(generator_id)
    n_generators = _model_n_generators(model)
    if gid != UNK_GENERATOR and not 0 <= gid < n_generators:
        raise ValueError(
            f"generator_id {gid} is outside 0..{n_generators - 1} "
            f"and is not the unknown id {UNK_GENERATOR}"
        )
    frame = build_frame(
        question,
        answer,
        context,
        benchmark=str(cfg.get("data.benchmark", "demo")),
        generator_id=gid,
    )
    if frame.empty:
        return pd.DataFrame(), {
            "backend": "none",
            "n_claims": 0,
            "generator_id": gid,
            "generator_supported": unknown_identity_supported(model),
            "n_other_answers": 0,
        }

    answers = _answers_for_question(gid, answer, other_answers)
    answers_by_question = {DEMO_QUESTION_ID: answers}

    scorer, embedder, _cache = build_cached(cfg)
    filled, _report = extract_signals(
        frame, cfg=cfg, answers_by_question=answers_by_question, scorer=scorer, embedder=embedder
    )
    validate(filled).raise_if_failed()

    n_others = max(len(answers) - 1, 0)
    info = {
        "backend": getattr(scorer, "name", "unknown"),
        "n_claims": len(filled),
        "n_other_answers": n_others,
        "generator_id": gid,
        "generator_supported": unknown_identity_supported(model),
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
                "claim_type_name": CLAIM_TYPE_NAMES[claim_type],
                "cross_n_others": int(row["cross_n_others"]) if "cross_n_others" in filled else 0,
                "evidence_source": _text_cell(row, "evidence_source"),
                "evidence_n_passages": _int_cell(row, "evidence_n_passages"),
                "arithmetic_verdict": _text_cell(row, "arithmetic_verdict"),
                "explanation": one_line(
                    p.prob, p.w_evid, CLAIM_TYPE_NAMES[claim_type], p.z_cross, p.z_evid
                ),
                **{name: round(float(row[name]), 4) for name in SIGNALS},
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


# ---------------------------------------------------------------------------
# presentation — display only; prediction stays in analyse()
# ---------------------------------------------------------------------------

#: Stage 8 means from the final research report. Not confidence intervals.
STAGE8_A0_AUROC = "0.6280"
STAGE8_A4_AUROC = "0.6839"
STAGE8_A7_AUROC = "0.5717"
STAGE8_A7_MINUS_A4 = "\u22120.1122"
STAGE8_A7_MINUS_A0 = "\u22120.0563"
STAGE8_AGGREGATE_NOTE = (
    "Benchmark AUROCs are aggregate research results, not the score of the current sentence."
)
STAGE8_CHECKPOINT_SEPARATION = (
    "The checkpoint used for the current input prediction is the loaded artifact "
    "identified beside this page. Its variant, seed, and result namespace come from "
    "that artifact. The table below is the Stage 8 benchmark comparison."
)
PREDICTION_CHECKPOINT_TITLE = "Checkpoint used for this prediction"
PREDICTION_CHECKPOINT_SCOPE = (
    "This artifact scores the pasted answer. "
    "Stage 8 figures are reported separately in Research context."
)
REPORT_HREF = "docs/RC-Gate_Final_Research_Report_v1.md"
INDEX_HREF = "docs/RC-Gate_Experiment_Index.md"

_LIKELY_HALLUCINATED = "likely hallucinated"
_LIKELY_SUPPORTED = "likely supported"

SIGNAL_SPECS: tuple[tuple[str, str, str, str], ...] = (
    (
        "agree",
        "Agreement",
        "Cross-model",
        "Fraction of the other answers whose text entails the sentence.",
    ),
    (
        "contra",
        "Contradiction",
        "Cross-model",
        "Largest contradiction score among the other answers. A maximum, not a mean.",
    ),
    (
        "sem_dist",
        "Semantic distance",
        "Cross-model",
        "One minus the mean cosine similarity to each other answer's best-matching sentence.",
    ),
    (
        "support",
        "Support",
        "Evidence",
        "Highest entailment of the sentence against the retrieved sentences of the source.",
    ),
    (
        "src_quality",
        "Source quality",
        "Evidence",
        "Records where the evidence came from. It does not say whether the sentence is true.",
    ),
    (
        "conflict",
        "Conflict",
        "Evidence",
        "Highest contradiction of the sentence against those retrieved sentences.",
    ),
)


@dataclass(frozen=True)
class DemoExample:
    """Constructed field text. Loading it never calls the model."""

    id: str
    label: str
    question: str
    answer: str
    context: str
    others: str


EXAMPLES: tuple[DemoExample, ...] = (
    DemoExample(
        id="with-source",
        label="Constructed example with a source and another answer",
        question="What did the quarterly note say about revenue?",
        answer="Revenue rose 12 percent to 1,048 crores. The board approved the plan.",
        context=(
            "The quarterly note states that revenue rose 12 percent. "
            "The board will meet next month."
        ),
        others=(
            "Revenue increased by about 12 percent.\n\n"
            "The note says revenue rose 12 percent to 1,048 crores."
        ),
    ),
    DemoExample(
        id="answer-only",
        label="Constructed example with an answer only",
        question="When was the bridge opened?",
        answer="The bridge opened in 1998.",
        context="",
        others="",
    ),
)

EXAMPLE_NOTE = (
    "Constructed illustration, not a benchmark item and not a labelled case. "
    "Loading fills the fields and does not run an analysis."
)

_CSS = """
<style>
section.main > div.block-container {
  max-width: 1040px;
  padding-top: 1.6rem;
  padding-bottom: 4.5rem;
}
section[data-testid="stSidebar"] {
  border-right: 1px solid rgba(128, 124, 116, 0.28);
}
section[data-testid="stSidebar"] .block-container {
  padding-top: 1.4rem;
}
.stApp h1 {
  font-size: 2rem;
  font-weight: 560;
  letter-spacing: -0.035em;
  line-height: 1.15;
  padding-bottom: 0;
}
.stApp h2 {
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: -0.015em;
  margin-top: 0.4rem;
}
.rc-kicker { margin: 0 0 0.85rem; }
.rc-status {
  display: inline-block;
  border: 1px solid rgba(60, 79, 124, 0.45);
  border-radius: 999px;
  padding: 0.12rem 0.6rem;
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: inherit;
  background: transparent;
}
.rc-lead {
  font-size: 1.05rem;
  line-height: 1.5;
  margin: 0.15rem 0 0.2rem;
  max-width: 40rem;
}
.rc-sentence {
  font-size: 1.08rem;
  line-height: 1.5;
  margin: 0.15rem 0 0.35rem;
  overflow-wrap: anywhere;
}
.rc-prob {
  font-size: 2.75rem;
  line-height: 1;
  letter-spacing: -0.04em;
  font-weight: 560;
  font-variant-numeric: tabular-nums;
  margin: 0.35rem 0 0.2rem;
  color: inherit;
}
.rc-class {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0.85rem 0 0.15rem;
  color: inherit;
}
.rc-route-labels {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.35rem 1.25rem;
  font-size: 0.95rem;
  margin: 0.15rem 0 0.4rem;
}
.rc-route-track {
  display: flex;
  width: 100%;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(128, 124, 116, 0.18);
}
.rc-route-cross { background: #3C4F7C; height: 100%; }
.rc-route-evid { background: #2F6F68; height: 100%; }
.rc-meta {
  font-variant-numeric: tabular-nums;
  margin: 0.85rem 0 0.15rem;
}
.stApp button:focus-visible,
.stApp textarea:focus-visible,
.stApp input:focus-visible,
.stApp [role="combobox"]:focus-visible {
  outline: 2px solid Highlight;
  outline-offset: 2px;
}
button[data-testid="stBaseButton-primary"] {
  background-color: #3C4F7C;
  border: 1px solid #3C4F7C;
  color: #FFFFFF;
}
button[data-testid="stBaseButton-primary"]:hover {
  background-color: #334266;
  border-color: #334266;
  color: #FFFFFF;
}
.rc-path {
  overflow-wrap: normal;
  word-break: normal;
  font-size: 0.85rem;
  line-height: 1.45;
  margin: 0.15rem 0 0.45rem;
  color: inherit;
}
.rc-note {
  font-size: 0.92rem;
  line-height: 1.45;
  margin: 0.35rem 0 0.75rem;
  padding: 0.15rem 0 0.15rem 0.75rem;
  border-left: 3px solid #3C4F7C;
  overflow-wrap: anywhere;
}
@media (max-width: 640px) {
  section.main > div.block-container {
    padding-left: 1rem;
    padding-right: 1rem;
  }
  .rc-prob { font-size: 2.25rem; }
}
</style>
"""


def predicted_class_label(explanation: str) -> str | None:
    """Class words already chosen by :func:`rcgate.explain.one_line`.

    The UI does not apply its own cutoff. If the explanation line does not name a class,
    the caller shows the probability without inventing one.
    """
    if _LIKELY_HALLUCINATED in explanation:
        return "Likely hallucinated"
    if _LIKELY_SUPPORTED in explanation:
        return "Likely supported"
    return None


def format_probability_percent(prob: float) -> str:
    """Four stored decimal places of probability become two decimal places of percent."""
    return f"{prob * 100:.2f}%"


def split_other_answers(raw: str) -> list[str]:
    """Other answers are separated by a blank line. A single newline stays inside one answer."""
    if not raw:
        return []
    return [part for part in raw.split("\n\n") if part.strip()]


def example_by_id(example_id: str) -> DemoExample:
    for example in EXAMPLES:
        if example.id == example_id:
            return example
    raise KeyError(example_id)


def apply_example(example_id: str) -> dict[str, str]:
    """Field values for an example. Does not score them."""
    example = example_by_id(example_id)
    return {
        "question": example.question,
        "answer": example.answer,
        "context": example.context,
        "others": example.others,
    }


def input_fingerprint(
    question: str, answer: str, context: str, others: str, generator_id: int
) -> str:
    return json.dumps(
        [question, answer, context, others, int(generator_id)], ensure_ascii=False
    )


def relative_to_project(path: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def missing_comparison_notice() -> str:
    """What the page says when no other answers were submitted.

    The numbers are the extractor's documented no-comparison fallbacks. This text does
    not change those values.
    """
    return (
        "No comparison answers were provided. "
        "Cross-model features use the extractor's documented fallback values "
        f"(agreement {NEUTRAL_AGREE:.1f}, contradiction {NEUTRAL_CONTRA:.1f}, "
        f"semantic distance {NEUTRAL_SEM_DIST:.1f}). "
        "No agreement or disagreement was measured. "
        "The prediction still comes from the loaded model and should be interpreted "
        "with that limitation."
    )


def comparison_status_notice(others_provided: bool) -> str | None:
    """Missing-comparison notice, or None once a real comparison answer is present."""
    if others_provided:
        return None
    return missing_comparison_notice()


def research_note_markdown() -> str:
    """Stage 8 record. Figures are copied from the final research report."""
    return (
        f"{STAGE8_CHECKPOINT_SEPARATION}\n\n"
        f"{STAGE8_AGGREGATE_NOTE}\n\n"
        "These are the Stage 8 means on one corrected 800-sentence RAGTruth slice "
        "(134 questions, 57 hallucinated sentences). The grid is 20 question-grouped "
        "splits crossed with three model initialisations. Those fits are repeated "
        "partitions of that one pool, not 60 independent datasets. The sample standard "
        "deviation of the fits is not a confidence interval.\n\n"
        "| Variant | What was fit | Mean test AUROC |\n"
        "| --- | --- | --- |\n"
        f"| A0 | Flat logistic regression | {STAGE8_A0_AUROC} |\n"
        f"| A4 | Gradient boosting with metadata | {STAGE8_A4_AUROC} |\n"
        f"| A7 | RC-Gate | {STAGE8_A7_AUROC} |\n\n"
        f"Mean paired A7 \u2212 A4: {STAGE8_A7_MINUS_A4}. "
        f"Mean paired A7 \u2212 A0: {STAGE8_A7_MINUS_A0}.\n\n"
        "Synthetic runs recover a reliability pattern that was deliberately planted in "
        "the simulator. The real-data result does not establish an A7 advantage.\n\n"
        "`src_quality` is constant on the evaluated slice. The arithmetic checker does "
        "not fire on the original slice. The official QA support audit did not adequately "
        "identify the proposed generator-by-type reliability surface. The voting baseline "
        "A8 was not evaluated.\n\n"
        f"[Final research report]({REPORT_HREF}) · [Experiment index]({INDEX_HREF})\n\n"
        f"Repository paths: `{REPORT_HREF}` and `{INDEX_HREF}`."
    )


def routing_bar_html(w_cross: float, w_evid: float) -> str:
    """A two-segment bar. The numbers beside it are the accessible values."""
    cross = max(0.0, float(w_cross))
    evid = max(0.0, float(w_evid))
    total = cross + evid
    if total <= 0.0:
        cross_pct = evid_pct = 0.0
    else:
        cross_pct = cross / total * 100.0
        evid_pct = evid / total * 100.0
    return (
        '<div class="rc-route">'
        '<div class="rc-route-labels">'
        f"<span>Cross-model <strong>{w_cross:.4f}</strong></span>"
        f"<span>Evidence <strong>{w_evid:.4f}</strong></span>"
        "</div>"
        '<div class="rc-route-track" aria-hidden="true">'
        f'<div class="rc-route-cross" style="width:{cross_pct:.2f}%"></div>'
        f'<div class="rc-route-evid" style="width:{evid_pct:.2f}%"></div>'
        "</div>"
        "</div>"
    )


def display_path(path: str) -> str:
    """Break a repository path after slashes, not inside a filename."""
    return html.escape(path).replace("/", "/<wbr>")


def _shown(value: object, missing: str = "not recorded") -> str:
    if value is None or value == "":
        return missing
    return str(value)


def prediction_checkpoint_record(provenance: dict) -> dict[str, str]:
    """Variant, seed, and result namespace of the checkpoint that scores this input."""
    return {
        "variant": _shown(provenance.get("variant")),
        "seed": _shown(provenance.get("seed")),
        "namespace": _shown(provenance.get("namespace")),
    }


def prediction_checkpoint_lines(provenance: dict) -> list[str]:
    record = prediction_checkpoint_record(provenance)
    return [
        f"Variant {record['variant']}",
        f"Seed {record['seed']}",
        f"Result namespace {record['namespace']}",
    ]


def _ensure_widget_state(st) -> None:
    st.session_state.setdefault("question", "")
    st.session_state.setdefault("answer", "")
    st.session_state.setdefault("context", "")
    st.session_state.setdefault("others", "")
    st.session_state.setdefault("generator_id", UNK_GENERATOR)
    st.session_state.setdefault("example_id", EXAMPLES[0].id)
    st.session_state.setdefault("pending_analysis", False)


def _current_fingerprint() -> str:
    import streamlit as st

    return input_fingerprint(
        str(st.session_state.get("question", "")),
        str(st.session_state.get("answer", "")),
        str(st.session_state.get("context", "")),
        str(st.session_state.get("others", "")),
        int(st.session_state.get("generator_id", UNK_GENERATOR)),
    )


def _load_selected_example() -> None:
    import streamlit as st

    fields = apply_example(str(st.session_state.get("example_id", EXAMPLES[0].id)))
    st.session_state.question = fields["question"]
    st.session_state.answer = fields["answer"]
    st.session_state.context = fields["context"]
    st.session_state.others = fields["others"]
    st.session_state.form_error = None


def _request_analysis() -> None:
    import streamlit as st

    st.session_state.pending_analysis = True


def _execute_analysis(model, cfg: Config) -> None:
    import streamlit as st

    st.session_state.pending_analysis = False
    answer = str(st.session_state.get("answer", ""))
    if not answer.strip():
        st.session_state.form_error = "Enter an answer. Each sentence of that answer is scored."
        st.session_state.result = None
        st.session_state.result_error = None
        return
    st.session_state.form_error = None
    generator_id = int(st.session_state.get("generator_id", UNK_GENERATOR))
    try:
        per_claim, info = analyse(
            str(st.session_state.get("question", "")),
            answer,
            str(st.session_state.get("context", "")),
            split_other_answers(str(st.session_state.get("others", ""))),
            model=model,
            cfg=cfg,
            generator_id=generator_id,
        )
    except Exception as exc:
        st.session_state.result = None
        st.session_state.result_error = f"{type(exc).__name__}: {exc}"
        return
    st.session_state.backend = info.get("backend", "unknown")
    st.session_state.result_error = None
    st.session_state.result = {
        "frame": per_claim,
        "info": info,
        "fingerprint": _current_fingerprint(),
        "context_provided": bool(str(st.session_state.get("context", "")).strip()),
        "others_provided": bool(split_other_answers(str(st.session_state.get("others", "")))),
        "generator_id": info.get("generator_id", generator_id),
        "generator_label": generator_label(int(info.get("generator_id", generator_id)), model, cfg),
        "generator_supported": bool(info.get("generator_supported")),
    }


def _render_sidebar(st, path: Path, provenance: dict, model, cfg: Config, config_name: str) -> None:
    with st.sidebar:
        st.markdown("**RC-Gate**")
        st.caption("Sentence-level hallucination analysis")
        st.markdown(f"##### {PREDICTION_CHECKPOINT_TITLE}")
        st.caption("Loaded. This session does not train.")
        st.markdown(
            f"<p class='rc-path'>{display_path(relative_to_project(path))}</p>",
            unsafe_allow_html=True,
        )
        for line in prediction_checkpoint_lines(provenance):
            st.caption(line)
        st.caption(PREDICTION_CHECKPOINT_SCOPE)
        st.caption(f"Config {config_name}")
        backend = st.session_state.get("backend")
        if backend:
            st.caption(f"Signal backend {backend}")
        else:
            st.caption("Signal backend is reported after an analysis.")
        if generator_options(model, cfg):
            st.caption(
                "Generator identity is selected in the form. It is not read off the answer text."
            )
        else:
            st.caption(GENERATOR_IDENTITY_LIMITATION)
        with st.expander("Run record"):
            st.caption(f"Git {_shown(provenance.get('git'))}")
            st.caption(f"Table {_shown(provenance.get('table'))}")
            st.caption(f"Recorded config {_shown(provenance.get('config'))}")
            st.markdown(
                f"<p class='rc-path'>{display_path(str(path))}</p>",
                unsafe_allow_html=True,
            )


def _render_inputs(st, model, cfg: Config) -> None:
    st.header("Analysis")
    st.caption(
        "One pasted answer. The checkpoint is already loaded. "
        "Nothing on this page generates a new answer or repairs the one you paste."
    )
    st.selectbox(
        "Example",
        options=[example.id for example in EXAMPLES],
        format_func=lambda example_id: example_by_id(example_id).label,
        key="example_id",
    )
    st.button("Load example", on_click=_load_selected_example)
    st.caption(EXAMPLE_NOTE)

    st.text_area(
        "Question",
        key="question",
        height=88,
        placeholder="What did the note say about revenue?",
    )
    st.caption("Used to de-alias the answer. The question itself is not scored.")
    st.text_area(
        "Answer",
        key="answer",
        height=180,
        placeholder="Paste the generated answer. Each sentence is scored separately.",
    )
    if st.session_state.get("form_error"):
        st.warning(st.session_state.form_error)
    st.caption("Each sentence becomes one claim.")
    options = generator_options(model, cfg)
    if options:
        labels = {option.generator_id: option.label for option in options}
        st.selectbox(
            "Generator identity",
            options=[option.generator_id for option in options],
            format_func=lambda generator_id: labels[int(generator_id)],
            key="generator_id",
        )
        st.caption(
            "Model that wrote the pasted answer. Unknown uses the checkpoint's reserved UNK row. "
            "The answer text is not used to choose an identity."
        )
    else:
        st.caption(GENERATOR_IDENTITY_LIMITATION)
    st.text_area(
        "Source evidence",
        key="context",
        height=140,
        placeholder="Optional. Paste the source the answer was written from.",
    )
    st.caption(
        "Optional. Passed to the claim-type rules and to the evidence extractor. "
        "Leave it empty and support, source quality, and conflict stay on the no-context path."
    )
    st.text_area(
        "Other models' answers",
        key="others",
        height=120,
        placeholder="Optional. Put a blank line between answers.",
    )
    st.caption("Optional. One answer per blank line.")
    st.button("Analyse answer", type="primary", on_click=_request_analysis)


def _render_claim(st, row: pd.Series) -> None:
    st.markdown(
        f"<p class='rc-sentence'>{html.escape(str(row['claim_text']))}</p>",
        unsafe_allow_html=True,
    )
    type_name = str(row.get("claim_type_name") or row.get("claim_type"))
    st.caption(f"Rule type {type_name}.")
    st.markdown(
        f"<p class='rc-prob'>{html.escape(format_probability_percent(float(row['prob'])))}</p>",
        unsafe_allow_html=True,
    )
    st.caption(f"Hallucination probability. Stored value {float(row['prob']):.4f}.")
    label = predicted_class_label(str(row["explanation"]))
    if label is None:
        st.caption(
            "The explanation line did not name a class. The probability above is the model output."
        )
    else:
        st.markdown(f"<p class='rc-class'>{html.escape(label)}</p>", unsafe_allow_html=True)
        st.caption(
            "Model prediction, taken from the explanation line. "
            "Not a ground-truth label, and not a proof that the sentence is true or false."
        )
    st.markdown("**Routing weights**")
    st.markdown(
        routing_bar_html(float(row["w_cross"]), float(row["w_evid"])), unsafe_allow_html=True
    )
    st.caption(
        "Inspectable routing decision for this claim type and the selected generator identity. "
        "Not a validated explanation of why an expert is reliable."
    )
    st.markdown(
        "<p class='rc-meta'>Expert logits · "
        f"cross-model {float(row['z_cross']):+.4f} · "
        f"evidence {float(row['z_evid']):+.4f}</p>",
        unsafe_allow_html=True,
    )
    st.markdown(str(row["explanation"]))
    st.caption(
        "Explanation line from the existing implementation. "
        "It names the family given less than half the routing weight."
    )
    with st.expander("Input signals"):
        for key, label_text, family, detail in SIGNAL_SPECS:
            if key not in row.index or pd.isna(row[key]):
                st.markdown(f"**{label_text}** · {family}")
                st.caption("Not returned by the extractor.")
                continue
            st.markdown(f"**{label_text}** · {family} · `{float(row[key]):.4f}`")
            st.caption(detail)
        if row.get("cross_n_others") is not None:
            st.caption(f"Other answers compared: {int(row['cross_n_others'])}.")
        source = row.get("evidence_source")
        passages = row.get("evidence_n_passages")
        if source:
            passage_text = (
                f", {int(passages)} retrieved"
                if passages is not None and pd.notna(passages)
                else ""
            )
            st.caption(f"Evidence source recorded by the extractor: {source}{passage_text}.")
        verdict = row.get("arithmetic_verdict")
        if isinstance(verdict, str) and verdict:
            st.markdown(f"**Arithmetic checker** · `{verdict}`")
            st.caption(
                "Not a seventh model input. A verified or refuted expression is folded into "
                "support and conflict. Unverifiable means no explicit expression was found."
            )


def _render_results(st, cfg: Config) -> None:
    st.header("Prediction")
    error = st.session_state.get("result_error")
    if error:
        st.error(error)
        return
    result = st.session_state.get("result")
    if not result:
        if not st.session_state.get("form_error"):
            st.caption("Run an analysis to score the answer. No prediction is shown before that.")
        return
    if result.get("fingerprint") != _current_fingerprint():
        st.caption("The input has changed. Analyse the answer again to score the current fields.")
        return
    frame = result["frame"]
    info = result["info"]
    if frame is None or frame.empty:
        st.warning("No sentences were extracted from that answer.")
        return
    n = len(frame)
    noun = "sentence" if n == 1 else "sentences"
    backend = info.get("backend", "unknown")
    if result.get("generator_supported"):
        identity = str(result.get("generator_label") or UNKNOWN_GENERATOR_LABEL)
        st.caption(f"{n} {noun} scored as {identity}. Signal backend {backend}.")
    else:
        st.caption(f"{n} {noun}. {GENERATOR_IDENTITY_LIMITATION} Signal backend {backend}.")
    configured = str(cfg.get("signals.backend", ""))
    actual = str(info.get("backend", ""))
    if configured and configured not in actual:
        st.caption(
            f"The configured backend is {configured}. This run used {actual}. "
            "The numbers below belong to the backend that actually ran."
        )
    if not result.get("context_provided"):
        st.caption(
            "No source evidence was submitted. Support and conflict are the extractor's "
            "no-context values, and source quality records that there was no source."
        )
    notice = comparison_status_notice(bool(result.get("others_provided")))
    if notice:
        st.markdown(
            f"<p class='rc-note'>{html.escape(notice)}</p>",
            unsafe_allow_html=True,
        )
    for i, (_, row) in enumerate(frame.iterrows()):
        if i:
            st.divider()
        _render_claim(st, row)


def _render_research(st) -> None:
    with st.expander("Research context", expanded=False):
        st.markdown(research_note_markdown())


def _render_footer(st) -> None:
    st.divider()
    st.caption(
        "RC-Gate scores pasted sentences with a loaded checkpoint. "
        "It does not generate an answer, repair one, or collect judge votes. "
        "A probability is a prediction."
    )


def render_demo(st, path: Path, provenance: dict, model, cfg: Config, config_name: str) -> None:
    """Research-prototype viewer. Numbers come from :func:`analyse`."""
    st.set_page_config(page_title="RC-Gate", layout="wide")
    st.markdown(_CSS, unsafe_allow_html=True)
    _ensure_widget_state(st)

    _render_sidebar(st, path, provenance, model, cfg, config_name)
    st.markdown(
        '<div class="rc-kicker"><span class="rc-status">Research prototype</span></div>',
        unsafe_allow_html=True,
    )
    st.title("RC-Gate")
    st.markdown(
        "<p class='rc-lead'>Sentence-level hallucination analysis for one pasted answer, "
        "scored by a saved checkpoint.</p>",
        unsafe_allow_html=True,
    )
    _render_inputs(st, model, cfg)
    if st.session_state.get("pending_analysis"):
        with st.spinner("Scoring sentences with the loaded checkpoint."):
            _execute_analysis(model, cfg)
        st.rerun()
    _render_results(st, cfg)
    _render_research(st)
    _render_footer(st)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rcgate.demo", description="Glass-box RC-Gate demo.")
    parser.add_argument(
        "--config", default="ragtruth", help="config name; sets the model shape and backend"
    )
    parser.add_argument(
        "--checkpoint",
        default=None,
        help="path to a model.pt; default: newest A7 under results/summary",
    )
    parser.add_argument("--question", default=None, help="headless mode: the user question")
    parser.add_argument("--answer", default=None, help="headless mode: the answer to analyse")
    parser.add_argument("--context", default="", help="headless mode: optional evidence context")
    parser.add_argument(
        "--other-answer",
        action="append",
        default=[],
        help="headless mode: another model's answer (repeatable)",
    )
    parser.add_argument(
        "--generator-id",
        type=int,
        default=UNK_GENERATOR,
        help=(
            "roster index of the pasted answer, or -1 for unknown. "
            "Never inferred from the answer text."
        ),
    )
    args, _unknown = parser.parse_known_args(argv)  # unknown: streamlit's own flags, ignored
    cfg = load_named(args.config)
    path, provenance, model = _load_model(cfg, args.checkpoint)

    if args.question and args.answer:
        per_claim, info = analyse(
            args.question,
            args.answer,
            args.context,
            args.other_answer,
            model=model,
            cfg=cfg,
            generator_id=args.generator_id,
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

    render_demo(st, path, provenance, model, cfg, config_name=args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
