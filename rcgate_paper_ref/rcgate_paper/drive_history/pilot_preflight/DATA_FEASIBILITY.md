# Data feasibility

**Date:** 23 October 2026  
**Status:** Proposal for a later manual build. No pages were scraped, no corpus was downloaded, and no pilot claims were created.  
**Sample the protocol asks for:** about 40–60 base claims in one domain, plus a separate calibration batch that never enters scored analysis.

Novelty is not established. Source-lineage datasets and independence measures may already exist; Byrd (SSRN, 2026) and Belkin, Madsen, and de-Wit (2026) are still unaudited at full text and code. This note only says whether the files already in the repo can supply the pilot.

## What is already on disk

`data/raw/ragtruth/` holds the RAGTruth release already used by this repository:

- 2,965 source rows. Keys: `prompt`, `source`, `source_id`, `source_info`, `task_type`.
- Task mix: Summary 943, Data2txt 1,033, QA 989.
- 17,790 responses from six named generators, with character-span hallucination labels on a subset.
- `data/benchmarks/ragtruth.json` records an 800-claim modeling slice over 134 sources (402 QA, 398 Summary in that slice record).
- Three signal tables, `ragtruth_corrected_integrity_v1_s0` through `s2`, each have 800 rows and binary `label` plus the six historical signals.

Forty-nine source rows contain an `http` substring in `source_info` or `prompt`. The schema has no publisher, author, archive identifier, publication time, citation list, or second independent document. Each modeling row is a sentence from a model response, checked against one supplied context. That is a hallucination-span task. It does not record claim truth, evidence-set adequacy, or claim-specific origin edges.

`data/benchmarks/RAGTruth.md` and `rcgate/data/ragtruth.py` describe this mapping. Those files stay read-only.

## Why the pilot corpus should be new

Use a newly specified claim set, collected after approval, and keep RAGTruth as history.

Reasons, each sufficient on its own:

1. **Task mismatch.** Pilot labels are claim truth at a time, passage stance, evidence-set status, text reuse, publication lineage, and epistemic dependence. RAGTruth does not contain those fields.
2. **Single context.** Dependence between retrieved sources is the intervention. A single `source_info` string cannot host a naturalistic syndication chain or a similar-but-independent pair.
3. **Leakage into the existing research record.** The 800-row slices, their `question_id` values, and their claim texts are already inside signal tables, split assignments, and result directories. Any pilot item that repeats a `source_id` or claim string from those tables is entangled with the historical split. Paraphrases of those claims belong to the same claim family and would still be entangled.
4. **Metric contamination.** Stage 8 numbers must not be reported as pilot false-support rates. Building the pilot inside the same rows makes that mix easy to do by accident.
5. **Off-the-shelf NLI weights were not trained by this repo on RAGTruth,** and that fact does not make RAGTruth a lineage benchmark.

Held-out RAGTruth source ids that never appear in the 800-row tables are still the same dataset, the same single-document format, and the same missing lineage fields. They are a poor feasibility sample for this protocol.

Synthetic tables under the historical pipeline plant conditional reliability for the old gate. They are not source chains.

## Proposed source for 40–60 base claims

**Domain candidate, matching the protocol and not yet chosen:** one public-affairs topic in which a primary artifact is public and later writing both repeats it and, in some cases, adds a separately collected observation. Examples of a primary artifact include an official statistical table, a regulator notice, a court filing, or a scientific paper. The user picks one topic and one reference date. This preflight does not pick the event.

**Construction, after a separate approval to collect:**

1. Write the sampling frame: topic, geography, reference time and time zone, what counts as an atomic claim, and what is out of scope (predictions, advice, multi-hop opinions).
2. Draft about 8–12 calibration claims first. Freeze the codebook on that batch. Those ids never enter scored metrics.
3. Then draft 40–60 scored base claims. Prefer claims that can be checked against the primary artifact, including some true, some false, and some unresolved or time-ambiguous. Fifty claims is a feasible middle of the protocol range. The count is a feasibility sample, not a prevalence sample.
4. For each scored claim, record the primary artifact the annotator will use for Layer A (claim truth). Record its URL and, when collection is approved, an archived snapshot and a SHA-256 of the captured text.
5. Cap later collection at a handful of passages per claim. Hand selection with archives is enough for a pilot. A web crawl is out of scope.
6. Store raw snapshots outside `data/raw/ragtruth/` and outside `results/`. A future `pilot_data/` directory is the protocol’s intended place. Do not create the corpus in this preflight.

**Where lineage evidence comes from:** the passage’s own quotation, syndication or wire credit, outbound link, named interview or dataset, timestamp order, and the archived page. Annotators copy those cues into the edge rationale. A missing citation is recorded as unknown. A different publisher is recorded as a publisher fact, not as independence. Domain diversity is not an origin label.

## Naturalistic pair versus controlled pair

These definitions follow pilot protocol §5. They are different arms and stay in separate tables.

**Naturalistic duplication (Arm A).** For a base claim, add a real later passage that is syndicated, republished, or dependent on the same primary artifact. Keep the URL, dates, and archive. Passage count, token count, and position will change. The arm estimates what happens when real dependent material is added. It does not, by itself, isolate dependence from length or order.

**Length/count-controlled intervention (Arm B).** Build variants that hold passage count and approximate token budget constant under the frozen V1 tokenizer, and also record NLI-tokenizer counts:

- `BASE` in the codebook: the frozen starting set.
- Dependent addition that replaces a matched passage so the count stays constant.
- A topical, length-matched passage that does not add support or refutation, when a defensible match exists.
- Independently established corroboration, only with positive evidence of a distinct collection.
- Similar wording with positive evidence of independent collection.

**Gold-status rule.** A pair enters the primary false-support contrast only when annotators judge that the dependent addition leaves evidence-set status unchanged. If the addition changes that status, or adds a new evidentiary basis, the pair stays in the export and moves to a secondary analysis. Eligibility is fixed from annotations before any model output is opened.

**Vocabulary mismatch to freeze before labeling.** The codebook `condition_id` values are `BASE`, `NATURALISTIC_DEPENDENT`, `CONTROLLED_DEPENDENT`, `TOPICAL_PLACEBO`, `INDEPENDENT_CORROBORATION`, `SIMILAR_BUT_INDEPENDENT`. Protocol Arm B also uses the strings `DEPENDENT_ADD_CONTROLLED` and `TOPICAL_PLACEBO_CONTROL`. Those protocol strings are not extra labels in the schema proposal. The user should map them onto `CONTROLLED_DEPENDENT` and `TOPICAL_PLACEBO`, or amend the codebook deliberately. This preflight does not add labels.

## Risks to truth and evidence-set annotation

- A claim can be true while the supplied passages only repeat an unsupported assertion. Truth and evidence-set status then differ. The schema stores both.
- Public-affairs claims often move with time, place, or definition. Those belong in `TIME_DEPENDENT_OR_AMBIGUOUS` unless the reference time and scope are fixed in the claim text.
- Widely copied wire errors look like corroboration. The origin edge has to say they share an origin even when many domains agree.
- Specialist numbers, law, and medicine may exceed what the annotators can adjudicate. The codebook says to mark those unresolved or escalate.
- Partial dependence is the scientifically important case: one fragment repeats a report and another adds an interview. Forcing one cluster label onto the whole article hides that case.
- `UNKNOWN` and `DEPENDENCE_RELATION_UNKNOWN` will be common when archives lack citation chains. A high unknown rate is a pilot result. It is not a hole to impute.
- Similar-but-independent items need affirmative evidence of a separate measurement or interview. Annotators will be tempted to use “no shared citation found” as independence. The codebook forbids that.
- Controlled paraphrases can accidentally add or remove a qualification and change gold status. Those pairs leave the primary contrast.
- Arm A confounds dependence with extra tokens and position. Reporting it as a causal effect would over-claim the design.

## How to avoid train, validation, and test leakage

The pilot itself is descriptive and is not the confirmatory test. The same grouping rules still apply so the pilot cannot quietly become a tuning set for a later model.

1. The sampling unit is the base claim family. Every variant, paraphrase, and passage of that family shares `claim_family_id` and stays in one partition.
2. Passages that share an evidenced origin share `source_origin_family_id` and stay in one partition. Unknown pairs do not get a family id merely to fill the field.
3. Calibration claims are a different id list. Metric scripts drop them by id, not by a flag that can be flipped after scores exist.
4. No claim text, source URL, or archive hash from `data/raw/ragtruth/` or from the 800-row signal tables enters the pilot manifest. A later build should hash-check new claim strings against those files and fail on overlap.
5. Controlled rewrites inherit the source claim’s family id. They are not “new” items that may cross a split.
6. Semantic-duplicate thresholds and any verdict thresholds are fit only on calibration or development families. The protocol forbids fitting them on cases that will be reported.
7. The confirmatory test, if one is later justified, is a new collection. This 40–60 claim set is not that test.
8. Historical grouped split code (`rcgate/data/splits.py`) groups `question_id` for RAGTruth. Reuse the grouping idea. Do not reuse the RAGTruth assignments.

## What this preflight did not do

No claim list, URL list, or archive was created. Domain, reference date, annotator names, and the adequacy standard remain user decisions. Until those are written down, collection should wait.
