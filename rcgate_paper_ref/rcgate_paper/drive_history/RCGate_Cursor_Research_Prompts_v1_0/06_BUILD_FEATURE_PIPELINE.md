# Prompt 06 — Build frozen grounding and peer-agreement features

Proceed only after the reconstructed labels and split design are reviewed and the protocol features are frozen. Do not change the feature list because of observed label associations.

## General rules

- Features must be built from target sentence text, the retrieved context, and unlabelled peer response texts linked to the same source/query only.
- Gold hallucination labels, label spans, official test labels, and target quality labels must never be input to a feature function.
- Run the same feature definitions for training, validation and test. Cache keys include every text input, model snapshot, tokenizer setting and feature-code version.
- Preserve `NA`/missingness explicitly. Do not replace failed NLI loads with lexical overlap scores.

## Grounding feature family

Use the accepted, pinned DeBERTa NLI snapshot and the protocol's exact input orientation and aggregation rules. Compute target-sentence versus supplied-context/evidence passage entailment, contradiction and neutral statistics. Log truncation, number of passages, runtime and missingness. Distinguish max, mean and any contradiction-aware aggregation only if they were predeclared.

## Peer-consensus feature family

Compute the predeclared features from other generator responses to the exact same source/query. The initial protocol may include a small fixed set such as:
- maximum and/or pooled semantic match between the target sentence and peer-response sentences;
- cross-encoder entailment and contradiction match for target sentence versus peer sentence(s), if the protocol selected it;
- fraction/count of available peers that semantically or NLI-support the target proposition;
- disagreement/dispersion across peers;
- peer availability and number of peers as explicit metadata.

Do not add every plausible feature. Keep the set compact and defensible. The feature definition must explain how peer sentences are matched to the target claim, how unrelated peer sentences are excluded or handled, and whether directionality matters. Peer features must not use peer labels.

## Data separation and caches

- Fit no model and select no feature threshold using test labels.
- If a similarity threshold is required, estimate it on training/validation/calibration groups only, and record the fitted value in the run manifest.
- Feature cache must be keyed by exact raw text/context/model snapshot; caches from the 800-row historical experiment cannot be assumed equivalent to full-response features.
- For generator-held-out tests, don't use a learned target-generator embedding as a required feature; record generator ID for stratified reporting, not as a predictive input unless an explicitly fair unknown-generator policy is predeclared.

## Tests

Feature leakage test, held-out-source isolation, missing-peer test, same-source peer mapping, NLI fail-closed, deterministic cache hashes, truncation logging, no-label access in feature functions, and reproducibility from a small hand-written fixture.

## Deliverables

Implement the frozen feature pipeline in the new package, add feature dictionary and report, and generate feature tables only in `data/derived/rcgate_conditional_consensus/`. Do not fit/evaluate predictive models. Run tests, report latency and missingness, then wait for Prompt 07.
