# Cursor task: RC-Gate feasibility-pilot preflight (no algorithm development)

You are operating in the user's existing RC-Gate repository. Treat the following research files as the governing design documents:

- `RCGate_Focused_Research_Pivot_v0_3.md`
- `RCGate_Pilot_Protocol_v0_2.md`
- `RCGate_Annotation_Protocol_v0_1.md`
- `RCGate_Pilot_Decision_Record_v0_1.md`

If they are not yet in the repository, ask the user to place/copy them into a new `research/plan/` directory (do not overwrite the historical manuscript or experiments). Do not assume that this prompt's sandbox download path exists on the user's machine.

## Goal

Perform a repository/environment audit and prepare a reproducible **pilot preflight**, not a new hallucination detector. Determine which parts of the proposed pilot can be run with the currently installed/open models, available data, code and compute budget.

## Mandatory safety and preservation rules

1. First inspect `git status --short --branch`, current branch, recent commits, untracked files, current diff, and root structure. Save that inspection to `research/pilot_preflight/REPO_STATE_BEFORE.md` (create folder only if safe). Do not checkout, reset, clean, stash, commit, push, or overwrite any files.
2. Treat all historical Stage 8 / RAGTruth data, results, manuscripts and user changes as read-only. Do not reuse Stage 8 metrics as pilot findings. Do not delete or regenerate files under existing results directories.
3. Do not train a new model, call paid model APIs, download large checkpoints, run bulk web retrieval, or run scored model inference yet. No long-running or expensive job without a separate explicit approval.
4. Do not implement a provenance model or rewrite the app. Keep changes confined to a new `research/pilot_preflight/` folder and report any proposed source changes before making them.
5. Never claim novelty has been established. The Byrd source-independence SSRN preprint and Belkin et al. 2026 source-dependence study are required novelty threats to inspect; current plan documents flag them as not fully audited.

## Tasks

A. **Repository and environment inventory**
- List relevant Python/Node versions, lockfiles, existing model libraries, local model cache metadata (do not expose secrets), dataset locations, annotation tools and available tests.
- Identify existing NLI model code, LLM judge wrappers, dedup/clustering code, input schemas and output schemas that might be reusable.
- Do not print `.env` values or API keys. You may report only variable names and whether they are set.

B. **Protocol-to-code feasibility matrix**
Create `research/pilot_preflight/FEASIBILITY_MATRIX.md` with each pilot requirement, existing support (`READY`, `PARTIAL`, `MISSING`, `BLOCKED`), exact file/function path and line references where possible, dependency/cost, and smallest safe next step. Explicitly cover: frozen V1 LLM judge, frozen V2 NLI model, lexical duplicate baseline, semantic duplicate baseline, cap/count baseline, token counting, order randomization, source metadata, immutable manifests/hashes, per-annotator labels and metric scripts.

C. **Model-selection report**
Create `research/pilot_preflight/MODEL_SELECTION.md` that proposes one accessible LLM judge and one accessible NLI model from what is already available or genuinely affordable/free, but does not execute them. Include exact IDs and revisions if determinable, licenses/usage restrictions if known, token limits, version-freezing risks, hardware need, and any uncertainty. If no suitable LLM judge is already available, state the blocker and offer options without making API calls.

D. **Data feasibility report**
Create `research/pilot_preflight/DATA_FEASIBILITY.md`: propose how to source 40–60 base claims in one domain, where source lineage evidence comes from, risks to truth/evidence-set annotation, how to avoid training/validation/test leakage, and what constitutes a naturalistic versus controlled pair. Do not scrape or download the pilot corpus yet.

E. **Annotation scaffold proposal**
Create `research/pilot_preflight/ANNOTATION_SCHEMA_PROPOSAL.json` and `ANNOTATION_GUIDE_CHECKLIST.md` derived exactly from the annotation codebook. These are proposals only; do not invent labels outside it. Ensure source relations can represent partial dependence/non-transitive edges and `UNKNOWN` without forcing clusters.

F. **Minimal implementation plan**
Create `research/pilot_preflight/IMPLEMENTATION_SEQUENCE.md` listing the smallest components needed to run the pilot, ordered by dependency. Start with manifest/schema/annotation export/metrics before verifier adapter implementations. Distinguish what can reuse existing modules from new code. Include test plan and command examples, but do not execute scored runs.

G. **Report findings in chat**
Summarize the repository state, blockers, required user decisions, and a recommended next action. The next action should be one small, reversible task. Do not write method code until the pilot configuration is frozen and the user explicitly approves.

At completion, state exactly which files you created/changed, confirm no historical data/manuscripts/results were modified, and report the current branch/status without making commits.
