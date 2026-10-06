<div align="center">

# RC-Gate

**Reliability-Conditioned Gated Mixture-of-Experts for claim-level hallucination detection — a gate that learns *which signal family to trust* per claim type and generator, and shows you its trust weights.**

[![Python](https://img.shields.io/badge/python-3.11%2B-3670A0?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Status](https://img.shields.io/badge/status-research-9B59B6?style=flat-square)]()
[![License](https://img.shields.io/badge/license-TBD-lightgrey?style=flat-square)]()

</div>

---

## Abstract

Black-box hallucination detection fuses two unreliable signal families — cross-model consensus and retrieval-based evidence — but neither family is reliable for every claim. RC-Gate conditions the fusion on metadata only (claim type, generator id): a tiny 229-parameter gate routes each atomic claim to a cross-model expert and an evidence expert, and a stacked meta-learner produces the hallucination probability *with* the trust weights that explain it. On synthetic data with planted conditional reliability, the gate beats flat fusion on numeric claims by **+0.38 AUROC** and survives an unseen inverted generator where flat fusion scores **0.17** (below random). On the first real benchmark (RAGTruth, 800 claims × 3 seeds, $0.00 API spend), the result is **negative and reported as measured**: the flat GBM control A4 leads at 0.740 AUROC vs A7's 0.631 — the honest autopsy is in [`postmortems/rcgate/002-m6-a4-beats-a7-on-real-data.md`](./postmortems/rcgate/002-m6-a4-beats-a7-on-real-data.md).

## Results

**Synthetic — planted conditional reliability (5 tables × 5 seeds, mean test AUROC):**

| Slice | A0 flat LR | A3 static α | A4 flat GBM+meta | **A7 RC-Gate** | Notes |
| --------------- | :--------: | :---------: | :--------------: | :------------: | ---------------------------- |
| numeric | 0.478 | 0.470 | **0.942** | 0.855 | A7 beats A0 by **+0.377** |
| entity | 0.858 | 0.860 | **0.927** | 0.870 | |
| all | 0.756 | 0.756 | **0.929** | 0.874 | **A4 is the honest control and it wins** |
| LOGO: inverted generator, unseen | **0.171** | — | — | **0.748** | strongest result in the project |

**Real — RAGTruth, 800 claims × 3 seeds (mean test AUROC):**

| Slice | A0 flat LR | A1 cross only | A4 flat GBM+meta | A7 RC-Gate | Paired bootstrap A7−A0 |
| --------------- | :--------: | :-----------: | :--------------: | :--------: | --------------------- |
| all | 0.681 | 0.705 | **0.740** | 0.631 | −0.050 [−0.21, 0.10], p=0.415 |

**Negative, not buried:** on this real slice the metadata carries little signal (gate weights hover near 0.45 across cells) and subtle hallucinations — retrievable sentences other models do not contradict — are close to undetectable by black-box signals. Nothing was retuned after seeing these numbers.

## Quickstart

```bash
pip install -e ".[dev,demo]"

# Run the whole build order, M0 -> M7, in sequence:
make stages

# Or one stage at a time:
make m0        # scaffold check: pytest + ruff + CLIs answer
make m1        # synthetic signal table with planted structure
make m2        # baselines A0-A4
make m3        # RC-Gate + ablations A3/A5/A6
make m4        # full evaluation (bootstrap CIs, leave-one-generator-out, heatmap)
make m5        # real RAGTruth signal table (cached NLI/embedding extractors)
make m6        # full evaluation on RAGTruth
make m7        # glass-box demo, headless verification

# Interactive demo (loads the newest trained A7 checkpoint; never trains):
streamlit run rcgate/demo/app.py
```

Every stage is idempotent and cache-aware: signal extraction is served from a disk cache (second RAGTruth build: 2.4 s vs 37.6 s), every run writes its config, git hash, wall-clock and API accounting next to its results, and all costs stay at $0.00 — NLI and embeddings run on CPU.

## What the gate outputs

Per atomic claim, not just a probability:

```
P(halluc)  = 0.83   w_cross = 0.08   w_evid = 0.92
→ "numeric claim; cross-model agreement down-weighted: shared-source numeric
   errors make every generator agree on the wrong number."
```

Gate weights are returned by every inference call and logged in every evaluation — interpretable by construction, never hidden behind a bare probability.

## Repository layout

```text
rcgate/               # package: data/, claims/, signals/, models/, demo/, train/evaluate/explain CLIs
configs/              # one YAML per benchmark + planted probabilities + budget
docs/adr/             # architecture decision records (Design Dungeons format)
postmortems/rcgate/   # failure stories: what broke, root cause, what changed
tests/                # 195 offline tests; the network is never touched
results/summary/      # committed summary tables + run artefacts with configs/checkpoints
DECISIONS.md          # one line per judgment call, per milestone
```

## Documentation

| Artifact | What it holds |
| ---------------------- | --------------------------------------------------------------- |
| [DECISIONS.md](./DECISIONS.md) | every judgment call, newest last, with acceptance results per milestone |
| [docs/adr/](./docs/adr/) | 6 ADRs: metadata-only gate, logit fusion, four claim types, span-overlap labelling, benchmark blocker policy, compute-cache split |
| [postmortems/rcgate/](./postmortems/rcgate/) | 3 postmortems: stale-table silent reuse, the M6 honest negative, inverted explanation verdicts |

## Citation

```bibtex
@misc{desai2026rcgate,
  title  = {RC-Gate: Reliability-Conditioned Gated Mixture-of-Experts for
            Claim-Type and Model-Aware Hallucination Detection},
  author = {Desai, Prathmesh P.},
  year   = {2026},
  note   = {B.Tech prototype; synthetic results validate the machinery, not the hypotheses}
}
```

---

_[pd241008](https://github.com/pd241008) · [ct-os-dev-portfolio.vercel.app](https://ct-os-dev-portfolio.vercel.app)_
