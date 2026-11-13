# Prompt 04 — Build only the safe experiment scaffold

Proceed only after Prompts 01–03 have outputs. Use the frozen specifications, without silently changing them.

## Scope

Implement a small, isolated, testable scaffold for the RC-Gate conditional-consensus study. This is the first code stage. It must not train a model or run feature inference.

## Required structure

Prefer a new namespace such as `rcgate/conditional_consensus/` with minimal modules for:
- configuration/manifest schema;
- deterministic data record schemas;
- hashes and provenance for raw inputs and derived outputs;
- group split validation;
- sentence-label projection interface (tests only until approved for full transform);
- experiment output paths.

Use only new outputs in `data/derived/rcgate_conditional_consensus/` and `results/rcgate_conditional_consensus/`. Never overwrite `data/raw/ragtruth/`, old signal tables, `results/summary/`, or old manuscripts.

## Tests required

- Manifest records data file hashes, code commit/hash, Python/package versions, config hashes, seeds, split hash, model snapshot IDs and exact command.
- A changed input byte changes the manifest hash.
- Group split validation detects source/query overlap across partitions.
- Every response/sentence record has stable IDs and links back to raw source and original span labels.
- Sentence-label projection tests punctuation, Unicode offsets, multiple spans and boundary cases.
- Test labels are not present in feature-builder inputs.
- Model-load errors fail closed; no fallback silently labels itself NLI.
- Output path validation cannot write to historical result directories.
- A8/majority-vote baseline availability is represented as unavailable if judge columns do not exist; never synthesize judge votes.

Run new unit tests only. Existing tests may run if they do not regenerate results or trigger model inference. Do not invoke Ollama, download weights, call APIs, build features, fit models or generate figures.

## Safety

Preserve existing changes and untracked files; do not stage, commit, push, reset, clean or switch branches. Report files, tests, exact test output and Git status. Wait for Prompt 05.
