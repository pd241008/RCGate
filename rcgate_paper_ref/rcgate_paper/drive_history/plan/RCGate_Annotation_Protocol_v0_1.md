# RC-Gate Annotation Protocol v0.1

**Prepared:** 23 October 2026  
**Status:** Draft codebook for calibration; freeze after a separate training batch and before scored pilot annotation.  
**Related files:** `RCGate_Focused_Research_Pivot_v0_3.md`; `RCGate_Pilot_Protocol_v0_2.md`.

## 1. Purpose and non-negotiable rule

This protocol keeps four things separate: (1) real-world claim truth at a reference time, (2) what a passage semantically says about the claim, (3) what the complete evidence set justifies, and (4) where the claim-relevant information originated. Do not collapse them into one label.

Annotators must be blinded to all verifier predictions, scores and method names. Evidence selection should be completed and frozen before scoring. Every non-obvious label must have a written rationale and a traceable source or artifact. `UNKNOWN` is a valid result, not an annotation failure.

## 2. Unit of annotation and required IDs

- `claim_id`: stable ID for one atomic, time-bounded factual claim.
- `claim_family_id`: IDs for paraphrases, restatements, or related examples derived from the same underlying proposition.
- `evidence_set_id`: one frozen set of passages provided for one claim condition.
- `passage_id`: stable ID for one retrieved passage/article excerpt.
- `evidence_fragment_id`: claim-relevant passage span or factual proposition. Use this finer unit when one document contains both dependent and independently collected content.
- `source_origin_family_id`: identifier only when an origin relationship is sufficiently evidenced; do not force unknown material into a family.
- `condition_id`: BASE, NATURALISTIC_DEPENDENT, CONTROLLED_DEPENDENT, TOPICAL_PLACEBO, INDEPENDENT_CORROBORATION, SIMILAR_BUT_INDEPENDENT, or other explicitly documented condition.

One article can contain multiple evidence fragments and multiple origin relationships. Do not assign one dependence label to an entire article if its claims derive from different sources.

## 3. Layer A — Claim truth at a reference time

Label the proposition, not whether the passage argues for it:

- `TRUE`: reliable, relevant evidence establishes the claim at the specified time and scope.
- `FALSE`: reliable, relevant evidence establishes that the claim is false at that time and scope.
- `UNRESOLVED`: available sources do not adequately establish either truth value.
- `TIME_DEPENDENT_OR_AMBIGUOUS`: wording, time, definitions, geography or conditions materially affect the answer and cannot be uniquely resolved from the record.

Record reference timestamp, time zone where material, scope/qualifiers, strongest supporting and refuting artifacts, and reason for adjudication. Do not use majority of URLs as ground truth. Prefer primary documents or independently adjudicated high-quality sources; record disagreements. If the claim requires specialist expertise that annotators do not have, mark unresolved or escalate rather than guess.

## 4. Layer B — Claim–passage semantic stance

This label describes what the passage asserts relative to the claim. It does **not** declare the passage truthful or credible.

- `ENTAILS_OR_ASSERTS`: the passage explicitly states or logically entails the claim.
- `CONTRADICTS`: the passage states something incompatible with the claim under the same time/scope.
- `NEITHER`: it is relevant/background/related but does not support or contradict the proposition.
- `MIXED`: it contains claim-relevant material in more than one direction or cannot reasonably be reduced to one stance.

For every passage, note the exact supporting span(s) and any conditions or qualifications. Semantic stance is different from epistemic evidentiary contribution: a passage can assert a false claim, while its evidence quality/origin may be inadequate to establish that claim.

## 5. Layer C — Evidence-set status

This label answers: **given this frozen set, its provenance, quality, time and relation to the claim, what conclusion is justified by the evidence—not merely asserted by the texts?**

- `ADEQUATE_SUPPORT`: the set contains sufficiently relevant and credible evidentiary basis to support the claim at the reference time. Repeating an unsupported assertion many times does not automatically make it adequate.
- `ADEQUATE_REFUTATION`: the set contains sufficiently relevant and credible evidence against the claim.
- `INSUFFICIENT`: the set does not justify support or refutation. This includes relevant assertions whose origin/quality does not establish the proposition.
- `CONFLICTING`: credible, relevant evidence supports incompatible conclusions and the set does not resolve the disagreement under the task's standard.

Annotators must apply an explicit domain standard and cite it in the record. Do not use the model's prediction to decide the label. If the domain standard cannot be stated consistently, the set is not ready for scored annotation. Keep claim truth and evidence-set status distinct: a claim can be true while the supplied set is insufficient, or false while several passages assert it.

For the primary duplicate-invariance pair, the adjudicated evidence-set status must remain the same before and after dependent material is added. If the new passage adds a genuinely independent evidentiary basis, it is not a pure dependent-addition pair and must be annotated in the corroboration arm.

## 6. Layer D — Text similarity/reuse

Record the best-supported relation for the **claim-relevant fragment**, not just whole-document similarity:

- `EXACT_REUSE`
- `NEAR_VERBATIM_REUSE`
- `PARAPHRASED_REUSE`
- `TOPICALLY_SIMILAR_NO_REUSE_EVIDENCE`
- `DISIMILAR_OR_UNRELATED`
- `UNKNOWN`

Text similarity is a surface/textual relation. It does not alone prove same underlying epistemic origin; similar language can be independently produced, and source-dependent claims can be heavily paraphrased.

## 7. Layer E — Publication/citation lineage

Use one or more directed edge labels between evidence fragments/passages:

- `COPIED_OR_SYNDICATED_FROM`
- `QUOTES_OR_CITES`
- `ATTRIBUTED_TO_OR_REPORTED_FROM`
- `SHARES_PRIMARY_ARTIFACT_OR_DATASET`
- `INDEPENDENT_COLLECTION_EVIDENCED`
- `PARTIAL_OR_MIXED_LINEAGE`
- `UNKNOWN_LINEAGE`

Record edge direction when known, evidence supporting the edge, timestamp relation and confidence rationale. A new publisher is not evidence of new underlying information. A missing citation is not evidence of independent collection.

## 8. Layer F — Claim-specific epistemic dependence graph

Represent claim-relevant evidence fragments as nodes and typed relations as edges. For each pair or fragment set, annotate one of:

- `SAME_UNDERLYING_ORIGIN`: the claim-relevant assertion depends on the same originating assertion/source/artifact.
- `SHARED_ORIGIN_WITH_ADDED_INDEPENDENT_COMPONENT`: the fragment uses a common source for part of the claim but adds a separately collected or established component.
- `INDEPENDENT_ORIGIN_EVIDENCED`: positive evidence indicates a distinct collection/measurement/primary basis relevant to this claim.
- `DEPENDENCE_RELATION_UNKNOWN`: the available record does not justify classifying the relationship.
- `MULTIPLE_ORIGINS_OR_CONFLICT`: the fragment/set combines evidence with different origins or incompatible origin relations; add separate edges/notes rather than treating this as a single cluster.

These are not necessarily symmetric or transitive. Store relation at the claim-relevant proposition level. A shared dataset with independently conducted analyses should be described explicitly; annotators should not automatically call it either fully independent or fully dependent without the claim-specific rationale. `INDEPENDENT_ORIGIN_EVIDENCED` requires positive support for independence (e.g., a separately recorded measurement or independently collected interview), not merely lack of a citation.

Annotate confidence qualitatively (`HIGH`, `MEDIUM`, `LOW`) with a rationale and evidence pointer. Confidence refers to confidence in the **relationship label**, not confidence that the factual claim is true. Unknown/low-confidence links should remain unknown for the primary relation-based evaluation unless the analysis explicitly studies uncertainty.

## 9. Source evidence and rationale requirements

For each article/passage capture, where available:

- canonical URL and archived URL/snapshot identifier;
- publication and update timestamps, timezone if applicable;
- publisher/domain and named author;
- cited/quoted sources and outgoing source links relevant to the claim;
- relevant primary artifact (report, dataset, transcript, official notice, scientific paper, direct interview record) and the exact claim it supports;
- retrieved passage text/hash and relevant span offsets;
- annotator rationale and unresolved uncertainty.

Do not infer truth from domain reputation alone. Do not count domain diversity as evidence independence. If sources cite the same underlying source indirectly, record the path when possible; otherwise use unknown.

## 10. Annotation workflow and reliability

1. **Training/calibration batch:** two annotators label a separate small batch, discuss disagreements, refine examples/rules, and freeze this codebook. Do not score that batch as pilot evidence.
2. **Independent scored annotation:** two annotators independently label every scored claim, passage stance, evidence set and relation; blind them to model outputs and to each other's labels.
3. **Agreement analysis before adjudication:** retain raw labels. Report raw agreement, confusion matrix and nominal Krippendorff's alpha for each categorical layer; report Cohen's kappa additionally if exactly two annotators label all units without missing values. Report class prevalence and UNKNOWN rate alongside agreement statistics.
4. **Hard-case report:** separately summarize `SHARED_ORIGIN_WITH_ADDED_INDEPENDENT_COMPONENT`, `INDEPENDENT_ORIGIN_EVIDENCED`, `TOPICALLY_SIMILAR_NO_REUSE_EVIDENCE`, paraphrased reuse, and unknown cases. State how often adjudication changes each label.
5. **Adjudication:** resolve cases after the raw-agreement report using a third reviewer or documented consensus. Preserve both original labels and the adjudicated label; never overwrite the originals.
6. **Feasibility threshold:** before scored labels are collected, the team records what agreement/unknown-rate/workload evidence is acceptable for proceeding and why. Do not select this threshold after seeing scored agreement. If the hard cases at the centre of the research question fail this gate, revise the codebook or stop this method direction.

The pilot must report annotation time per claim and per relation, how often a source chain could be traced, what evidence types were unavailable, and the proportion of source relationships remaining unknown. High uncertainty is a finding, not something to hide.

## 11. Exclusion and adjudication rules

Exclude a pair from the **primary pure-dependent-addition contrast** when:

- the added passage contributes a new independent factual measurement or primary artifact;
- the addition changes gold evidence-set status;
- a source-origin relation required by the pair is unknown;
- temporal/scope ambiguity prevents a valid paired comparison;
- the evidence snapshot cannot be reproduced or its relevant text is unavailable.

Do not erase excluded cases. Retain them in a flow table with the reason and analyze them in separately defined secondary groups when appropriate. Exclusion is decided from annotations before model predictions are opened.

## 12. Required output schema

At minimum, each annotation export contains:

`claim_id`, `claim_family_id`, `reference_time`, `claim_text`, `claim_truth`, `truth_rationale`, `evidence_set_id`, `condition_id`, `passage_id`, `evidence_fragment_id`, `passage_url`, `archive_id_or_hash`, `published_at`, `publisher`, `claim_passage_stance`, `evidence_set_status`, `text_relation`, `lineage_edge_type`, `origin_relation`, `origin_confidence`, `origin_rationale`, `annotator_id`, `annotation_version`, `adjudication_status`, `adjudicated_label`, `exclusion_reason`.

Maintain a data dictionary and never store unsupported certainty in binary fields when `UNKNOWN` is justified.
