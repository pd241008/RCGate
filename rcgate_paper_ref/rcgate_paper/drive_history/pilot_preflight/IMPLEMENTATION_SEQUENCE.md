# Implementation sequence

**Date:** 23 October 2026  
**Status:** Plan only. No method code was added. No scored run is authorized.  
**Rule:** Start with manifest, schema, annotation export, and metrics. Verifier adapters come after the decision record freezes V1, V2, the condition vocabulary, the domain standard, and the reliability gate.

Historical modules stay in place. New code, when approved, should live under a new package path such as `rcgate/pilot/` or under `research/pilot_preflight/tools/`. It should read and write `pilot_data/` and `pilot_results/` only. It must not rewrite `rcgate/signals/`, `rcgate/models/`, `data/raw/`, or `results/summary/`.

## Already reusable

| Need | Reuse | Limit |
|---|---|---|
| SHA-256 of files | `sha256_of` in `rcgate/data/ragtruth.py` | Hash new pilot files. Do not re-fetch RAGTruth. |
| Content hash of a prompt | `make_key` in `rcgate/signals/cache.py` | Use it to record a prompt hash. Do not point it at a paid provider. |
| Grouped partition | Idea in `grouped_split` (`rcgate/data/splits.py`) | Group by `claim_family_id` and `source_origin_family_id`. Do not reuse RAGTruth `question_id` assignments. |
| NLI probabilities | `CrossEncoderScorer.score` | Fail closed on load error. Map outputs to four evidence-status labels only after the map is frozen. |
| Max and mean aggregation | `score_claim` `aggregate` argument | This is the uncorrected support baseline, not the dependence correction. |
| MiniLM cosine | `Embedder` | Semantic baseline only, threshold fit on calibration or development ids. |
| Grouped resampling mechanics | `bootstrap_auroc_ci_grouped` and `paired_question_delta` | New estimand: paired false-support difference. Label intervals exploratory. Do not report AUROC as the pilot primary outcome. |
| Budget guard | `configs/budget.yaml` dry-run | Leave dry-run on. A local CPU scorer does not need an API budget. |

## New code, in dependency order

Do not start a later step by implementing an earlier one inside a verifier script.

1. **Manifest and hasher.** JSON manifest listing every passage file, snapshot, annotation export, codebook version, and SHA-256. Include model ids and digests once frozen, prompt hash, software versions, order seed, and output directory. No predictions yet.
2. **Schema validator.** Check exports against `ANNOTATION_SCHEMA_PROPOSAL.json`. Enforce null `source_origin_family_id` when origin is `DEPENDENCE_RELATION_UNKNOWN`. Reject a document-level cluster field if one is added later. Check that raw annotation objects are not rewritten by adjudication.
3. **Flat export view.** Emit the codebook §12 columns, repeating a row per annotator and per edge so partial and unknown edges remain visible.
4. **Partition assignment.** Given claim families and origin families, assign calibration versus pilot, and keep linked families together. Fail if a family intersects the RAGTruth 800-row `question_id` or claim-text set.
5. **Metric script on labels and predictions.** Inputs are immutable. Outputs are base false-support rate, dependent-addition false-support rate, paired risk difference, and the three gold-status strata (`INSUFFICIENT`, `ADEQUATE_REFUTATION`, `CONFLICTING`). Also emit the four-way confusion matrix, unknown rates, and a per-claim transition table. Drop ineligible pairs using `exclusion_reason` / `primary_contrast_eligible` that were stored before predictions existed. Separate Arm A and Arm B.
6. **Agreement script.** Raw agreement and confusion matrices per layer from `raw_annotations`. Cohen’s kappa through scikit-learn when two complete annotators exist. Krippendorff’s alpha needs a dependency decision; do not add that package until approved. Report the hard-case labels named in the codebook.
7. **Order and count report.** Store the passage permutation from a frozen seed. Count passages. Count NLI tokens with the frozen DeBERTa tokenizer after V2 acceptance. V1 token counts stay unimplemented until a Llama tokenizer or an explicit `num_ctx` procedure exists.
8. **Exact and normalized duplicate baseline.** Remove byte-identical and whitespace/case-normalized copies. Unit-test that paraphrases remain.
9. **Lexical near-duplicate baseline.** Character or word shingles. Threshold selected on calibration ids only, then copied into the manifest.
10. **Semantic near-duplicate baseline.** MiniLM snapshot `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Same threshold rule. This step is the first one that runs a model, and it waits for explicit approval.
11. **Cap and source-count baseline.** One support vote per cluster, plus a raw URL-count heuristic reported beside it. Clusters are a baseline. They do not replace edges, and `UNKNOWN` pairs stay unmerged.
12. **V2 adapter.** Frozen DeBERTa snapshot, no lexical fallback, declared truncation, declared max/mean/contradiction rule, four-way output schema, timing log. Same frozen passage text and source metadata for every method.
13. **V1 adapter.** Only after the user freezes the Llama 3.2 1.2B digest or a different judge. Local Ollama only if that is the frozen choice. Record prompt hash, decoding, retries, context length, and failures. No provider SDK in the first build.
14. **Gold-relation diagnostic.** Apply one predeclared correction using adjudicated edges. Report it as a diagnostic of that rule under those labels.
15. **IMRRF-style filter.** Deferred. Not in the smallest path. If it is built later, label it an adaptation unless the original pipeline is actually reproduced.

## Test plan

Tests use hand-written fixtures of a few claims. They do not read `results/summary/` and do not call a model, except step 10 and later when those steps are separately approved.

| Test | What it checks |
|---|---|
| Schema accept | Fixture with a partial-dependence edge and a second `DEPENDENCE_RELATION_UNKNOWN` edge validates. Family id on the unknown edge is null. |
| Schema reject | A family id on `DEPENDENCE_RELATION_UNKNOWN` fails. A label outside the codebook enums fails. |
| No transitive closure | Fixture has A→B and B→C. The validator does not require A→C. The metric fixture does not treat A and C as the same origin. |
| Raw labels survive | Adjudication object present; both annotator records still present and unchanged. |
| False-support definition | Prediction `ADEQUATE_SUPPORT` with gold `INSUFFICIENT` counts as FS=1. Prediction `ADEQUATE_SUPPORT` with gold `ADEQUATE_SUPPORT` counts as FS=0. Strata are not pooled away. |
| Pairing | Risk difference is the mean of claim-level `FS_dependent - FS_base`. Two variants are not two independent claims. |
| Exclusion | A pair whose gold status changes is omitted from the primary contrast and listed in the flow table. |
| Calibration drop | Ids marked calibration never appear in the scored denominator. |
| Duplicate baselines | Normalized copies collapse. A paraphrase fixture does not collapse under the exact baseline. |
| Order replay | The stored permutation regenerates the prompt order. |
| Hash stability | Manifest hash changes when a passage byte changes and stays put when the file is unchanged. |
| Fail closed | A missing NLI snapshot raises. It does not return lexical scores. This test uses a missing path, not a live forward pass. |

Historical `tests/` should stay green and untouched. New tests live next to the new package.

## Command examples

These commands are illustrations for later. They were not run. Paths assume a future package that does not exist yet.

```bash
# Schema file only. Safe anytime. Does not score.
.venv/bin/python -m json.tool research/pilot_preflight/ANNOTATION_SCHEMA_PROPOSAL.json >/dev/null

# Future validator, after it is written and approved:
# .venv/bin/python -m rcgate.pilot.validate_export pilot_data/calibration_export.json

# Future metrics on a fixture, no model:
# .venv/bin/python -m rcgate.pilot.metrics \
#   --annotations pilot_data/annotations.json \
#   --predictions pilot_results/fixture_predictions.json \
#   --out pilot_results/metrics.json

# Not authorized now:
# ollama serve
# ollama run llama3.2:1b
# any Hugging Face download
# any call that spends configs/budget.yaml
# python -m rcgate.train
# make m5 / make m6
```

## Stop line

The next code change waits for an explicit user approval and a filled freeze for the piece being built. The smallest approved step is the manifest plus schema validator on a fixture, with no verifier attached.
