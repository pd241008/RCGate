# RC-Gate Pilot Protocol v0.2

**Prepared:** 23 October 2026  
**Status:** Feasibility pilot only; not a confirmatory experiment or a validated novelty claim.  
**Supersedes:** v0.1 for new work. Preserve v0.1 unchanged as history.

## 1. Purpose and non-goals

Test whether claim-specific dependent evidence can produce false-support decisions in current verifiers, whether this persists after strong simple redundancy baselines, and whether the relationships can be annotated reliably. The pilot may kill the research direction.

This pilot does **not** establish a population failure rate, prove method superiority, or validate publication novelty. It is not the final benchmark. The old RAGTruth Stage 8 experiment is a separate task; its metrics must not be reused as results for this pilot.

## 2. Primary verifier set (freeze before scored runs)

The scored pilot has two preselected primary verifier families:

1. **V1: LLM judge.** Before any scored pilot output is inspected, record the exact model identifier and version/API snapshot, provider or local weights hash, system/user prompt, decoding settings, output schema, retry policy, and software version.
2. **V2: NLI aggregator.** Record the exact model identifier/revision, tokenizer revision, label mapping, max/mean aggregation rule, truncation policy, and software version.

The actual configurations must be selected from models genuinely available in the project environment and written into `RCGate_Pilot_Decision_Record_v0_1.md` before scoring. If a model is unavailable or cannot be frozen, replace it **before** any scored run and document why. Do not switch models after seeing their results. Other verifiers are secondary/exploratory and cannot be substituted for the primaries post hoc.

## 3. Sample and unit of analysis

Start with roughly 40–60 base claims in one manageable, source-rich domain (news/public affairs is a candidate, not a requirement). Include true and false claims where independently adjudicable, plus an `UNRESOLVED` category when needed. Specify the time at which each claim is assessed.

The independent sampling unit is the **base claim / claim family**, not the passage variant. Variants from one claim and items connected to the same source-origin family must remain grouped. This sample supports qualitative feasibility findings and case analysis; it does not support broad prevalence or superiority claims by itself.

Use a separate training/calibration set to refine annotation instructions. Do not include training examples in the scored pilot. Freeze the codebook before scored labels are produced.

## 4. Required annotation layers

Use `RCGate_Annotation_Protocol_v0_1.md`; do not invent labels ad hoc during annotation.

At minimum, separately record:

- Claim truth at a reference time: `TRUE`, `FALSE`, `UNRESOLVED`, `TIME_DEPENDENT_OR_AMBIGUOUS`.
- Claim–passage semantic stance: `ENTAILS/ASSERTS`, `CONTRADICTS`, `NEITHER`, `MIXED`; this describes content relation, not whether the passage is epistemically reliable.
- Evidence-set status: `ADEQUATE_SUPPORT`, `ADEQUATE_REFUTATION`, `INSUFFICIENT`, `CONFLICTING`.
- Text relation: exact/near reuse, paraphrase, topical similarity without demonstrated reuse, dissimilar, unknown.
- Publication lineage and claim-specific evidentiary-origin relation, with typed partial/mixed and unknown relations. Do not reduce these to one document-level duplicate cluster.

Annotators must be blinded to verifier outputs. Preserve both raw annotations, adjudication, rationale and provenance artifacts. Use `UNKNOWN` where the record does not justify a stronger statement. Absence of a citation alone is not evidence of independence.

## 5. Two separate experimental arms

### Arm A — Naturalistic duplication (practical effect)

For eligible claims, add actual syndicated reports, republished passages or reports dependent on the same underlying source/artifact. Preserve URLs, dates, source records and archived content when available. This arm measures what happens in realistic source chains. Because passage count, token count and position naturally change, **do not interpret this arm alone as isolating the causal effect of evidence dependence**.

### Arm B — Length/count-controlled intervention (mechanism diagnostic)

Construct paired evidence conditions with passage count and total token budget matched as closely as possible under the primary LLM judge's tokenizer (also record counts under the NLI tokenizer where relevant):

- `BASE`: frozen starting evidence set.
- `DEPENDENT_ADD_CONTROLLED`: dependent passage(s) replace matched control passage(s), so count and approximate token budget remain constant; source-origin relation is adjudicated.
- `TOPICAL_PLACEBO_CONTROL`: topical/length-matched material that does not add support/refutation, where a defensible match exists.
- `INDEPENDENT_CORROBORATION`: independently established, claim-relevant evidence, only when its origin and relevance can be justified.
- `SIMILAR_BUT_INDEPENDENT`: similar wording/topic with affirmative evidence of independent collection, not merely no citation found.

Record actual token counts, passage count, relevance ratings, publisher/domain metadata exposed to the model, transformation provenance and any deviations from matching. Counterbalance order with a recorded seed; use the same order assignment across compared methods where possible. On a preregistered sensitivity subset, repeat one alternate order to detect position sensitivity.

Do not force an example into the primary duplicate-invariance set if the added material changes the adjudicated evidence-set status or provides a genuinely new evidentiary basis. Move it to the appropriate corroboration/conflict analysis instead.

### Gold-status invariant for primary paired cases

For the main dependence contrast, the annotators must judge the gold evidence-set status unchanged between `BASE` and dependent-addition variants. If status changes, exclude that pair from the primary duplicate-induced false-support contrast and retain it for transparent secondary analysis. This is not a license to discard difficult cases after observing model results; eligibility is determined from annotations before scoring.

## 6. Baselines

The following are mandatory, subject to documented feasibility:

1. V1 frozen LLM judge on unfiltered passages.
2. V2 fixed NLI aggregator on unfiltered passages.
3. Exact/normalized duplicate removal.
4. Lexical near-duplicate filtering (e.g., character/word shingling).
5. Semantic near-duplicate filtering using a frozen encoder and a threshold chosen on a separate development set—not pilot outcomes if those same cases will be reported as evaluation.
6. Cluster-capped support aggregation / simple source-count heuristic.
7. An uncorrected claim–passage support aggregation baseline.
8. An **IMRRF-style redundancy-filter adaptation** only if implemented fairly with the fixed input evidence. Label it an adaptation unless the original method and full pipeline are actually reproduced. The full IMRRF retrieval pipeline is not directly comparable to a frozen-evidence intervention without a separate end-to-end experiment.
9. **Gold-provenance oracle diagnostic:** use human gold relation edges for the specified correction rule. This only tests that specific correction under perfect relation labels; it is not a general theoretical upper bound and is not deployable.

Every primary paired method receives the same frozen evidence text and the same source metadata in the main fixed-evidence test. If a baseline cannot consume identical inputs, document the information mismatch and do not treat the result as a clean head-to-head causal comparison.

## 7. Outcomes and metrics

### Primary outcomes (report together)

For each evaluated variant, define `FS=1` when the system predicts `ADEQUATE_SUPPORT` while gold evidence-set status is not `ADEQUATE_SUPPORT`; otherwise `FS=0`.

For each verifier/method, report all of:

1. **Base false-support rate:** false-support decisions divided by all evaluated base sets whose gold status is `INSUFFICIENT`, `ADEQUATE_REFUTATION`, or `CONFLICTING`.
2. **Dependent-addition false-support rate:** the same rate after dependent material is added, on the same eligible paired cases.
3. **Paired risk difference:** mean of `FS_dependent − FS_base` over paired claims/source families. Positive values indicate increased false support under dependent addition.

Report each of the three gold-status strata separately, not only pooled. A zero paired difference does not imply reliability if the verifier is wrong in both conditions; absolute rates are mandatory. The pilot result is descriptive. Show per-claim paired transitions; do not treat variants as independent rows. Any interval must account for grouping by claim/source-origin family and be labelled exploratory rather than confirmatory.

### Distinct secondary outcomes

- **Truth-level false confirmation:** separately report cases where gold claim truth is `FALSE` and the system asserts a supported/true verdict. Do not conflate this with an evidence-set error.
- **Independent-corroboration response:** on cases where independently established evidence changes the adjudicated evidence status, assess whether the verifier changes in the justified direction.
- Four-way evidence-status confusion matrix and class-wise precision/recall/macro-F1 where sample size permits.
- Numeric LLM support scores only as within-model diagnostics; they are not probabilities by default.
- Annotation reliability, unknown-label rate, adjudication frequency and annotation time.
- Cost, latency, token counts, failed calls and truncation.

## 8. Annotation reliability gate

Use the separate codebook and the pre-scored calibration batch. Report raw agreement and confusion matrices for every label layer; use nominal Krippendorff's alpha as a primary chance-corrected summary and Cohen's kappa as an additional statistic if exactly two annotators label all cases. Report partial-dependence, similar-but-independent and unknown cases separately because overall agreement can hide the cases that matter most.

Before scored annotation, record a reliability decision rule in the decision record, justified by intended use and label prevalence. Do not pick or change it after inspecting scored agreement. If provenance agreement is poor on the difficult cases central to the hypothesis, the provenance-aware method track does not proceed; revise the codebook or abandon that target.

## 9. Pilot stop/go criteria

### Feasibility signals supporting a confirmatory study

- A practically non-trivial false-support increase appears in the naturalistic arm and is not explained entirely by token count/order under the controlled arm.
- The effect is shown for the preselected primary verifier set and interpreted per verifier; one-model-only behavior is described as such.
- Exact/near-deduplication and count-capping do not fully explain the effect on the hard natural cases.
- Human annotations can distinguish the relevant relation types with a reliability level fixed before scored annotation, at reasonable workload.
- Independent-corroboration controls show the task is not solved merely by ignoring all added evidence.

These are qualitative feasibility conditions, not claims of statistical significance. Use pilot effect sizes and variance only to design the confirmatory study. Before opening the confirmatory test set, freeze a minimum practically important effect, the acceptable corroboration-sensitivity loss, coverage/abstention policy (if any), cost/latency limits, sample-size rationale and uncertainty procedure.

### Stop or pivot

Stop or revise if: (a) the closest prior art already makes the same claim from comparable inputs; (b) the apparent failure vanishes under length/count/order controls; (c) exact/near deduplication or cluster capping adequately resolves the relevant natural cases; (d) labels are unreliable on partial/ambiguous dependence; (e) only constructed examples show the effect; or (f) the proposed improvement only increases abstention or costs without a justified benefit.

## 10. Required run artifacts

Store outputs outside historical RAGTruth/Stage 8 results. At minimum record:

- Versioned input manifest and SHA-256 hashes for every passage/snapshot and annotation export.
- Frozen primary verifier configuration, prompts, model/tokenizer IDs, software versions and decoding/retry rules.
- Control matching report: passage count, token counts, order assignment and relevance comparability.
- Raw per-annotator labels, adjudicated labels and evidence trail.
- Per-variant predictions, refusal/failure details and timing/cost logs.
- Analysis script that derives all metrics from immutable raw predictions.
- Pilot decision record with deviations and stop/go rationale.

No method training, manuscript rewrite, commit or push is authorized by this protocol. First establish the environment and the pilot feasibility; only after a written go decision should method implementation be scoped.
