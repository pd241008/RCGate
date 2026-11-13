# Annotation guide checklist

**Status:** Proposal derived from `research/plan/RCGate_Annotation_Protocol_v0_1.md`.  
**Codebook state:** Draft, for a calibration batch. It is not frozen.  
**This checklist invents no labels.** Enumerations below are copied from the codebook. Where the codebook names a field and does not list allowed values, the field stays free text.

The machine-readable companion is `ANNOTATION_SCHEMA_PROPOSAL.json`. Relations are stored as edges between evidence fragments. They are not stored as a single cluster id on an article.

## Before anyone labels a scored item

- [ ] Read the codebook sections 1–12.
- [ ] Confirm the decision record still has a blank reliability gate, and do not invent a numeric cutoff after seeing labels.
- [ ] Run a separate calibration batch. Discuss disagreements. Revise examples only in a new codebook version. Exclude those claim ids from scored metrics.
- [ ] Freeze the codebook version string before scored labels.
- [ ] Resolve the condition-id mismatch: codebook `CONTROLLED_DEPENDENT` and `TOPICAL_PLACEBO` versus protocol strings `DEPENDENT_ADD_CONTROLLED` and `TOPICAL_PLACEBO_CONTROL`. Do not create a third pair of names in the labels.
- [ ] Write the domain adequacy standard that “adequate” refers to. If it cannot be stated, scored evidence-set labels are not ready.
- [ ] Blind annotators to verifier scores, model names, and each other’s labels.
- [ ] Freeze the evidence snapshots before any scoring job is started.

## Identity rules (codebook §2)

- [ ] One `claim_id` is one atomic, time-bounded factual claim.
- [ ] Paraphrases and restatements of the same proposition share `claim_family_id`.
- [ ] One `evidence_set_id` is one frozen passage set for one condition.
- [ ] `condition_id` is one of: `BASE`, `NATURALISTIC_DEPENDENT`, `CONTROLLED_DEPENDENT`, `TOPICAL_PLACEBO`, `INDEPENDENT_CORROBORATION`, `SIMILAR_BUT_INDEPENDENT`, or another condition that is explicitly documented in the decision record before use.
- [ ] `passage_id` identifies the excerpt. `evidence_fragment_id` identifies the claim-relevant span when a document mixes dependent and independent content.
- [ ] Assign `source_origin_family_id` only when the origin relationship is sufficiently evidenced. Leave it null for unknown material.
- [ ] Do not assign one dependence label to an entire article when its fragments come from different sources.

## Layer A — claim truth at a reference time (codebook §3)

Label the proposition in the world at the recorded time and scope.

- [ ] `TRUE` — reliable, relevant evidence establishes the claim at that time and scope.
- [ ] `FALSE` — reliable, relevant evidence establishes that the claim is false at that time and scope.
- [ ] `UNRESOLVED` — available sources do not adequately establish either truth value.
- [ ] `TIME_DEPENDENT_OR_AMBIGUOUS` — wording, time, definitions, geography, or conditions materially change the answer and the record does not resolve them.
- [ ] Record reference timestamp, time zone where it matters, scope, strongest supporting artifact, strongest refuting artifact, and the reason.
- [ ] Do not treat a majority of URLs as truth.
- [ ] Prefer primary documents or independently adjudicated high-quality sources.
- [ ] If the claim needs expertise the annotators do not have, mark it unresolved or escalate.

## Layer B — claim–passage semantic stance (codebook §4)

This label says what the passage asserts. It does not say the passage is true or credible.

- [ ] `ENTAILS_OR_ASSERTS` — the passage states or logically entails the claim.
- [ ] `CONTRADICTS` — the passage states something incompatible with the claim under the same time and scope.
- [ ] `NEITHER` — related or background, and neither support nor contradiction.
- [ ] `MIXED` — claim-relevant material in more than one direction, or not reducible to one stance.
- [ ] Note the exact span and any qualifier.
- [ ] The protocol’s phrase `ENTAILS/ASSERTS` is the same codebook label `ENTAILS_OR_ASSERTS`. Use the codebook spelling in files.

## Layer C — evidence-set status (codebook §5)

Label what this frozen set justifies, given provenance, quality, time, and relation to the claim. Repetition of an unsupported assertion does not by itself make the set adequate.

- [ ] `ADEQUATE_SUPPORT`
- [ ] `ADEQUATE_REFUTATION`
- [ ] `INSUFFICIENT`
- [ ] `CONFLICTING` — credible relevant evidence on incompatible sides, unresolved under the stated standard.
- [ ] Cite the domain standard in the rationale.
- [ ] Keep this label distinct from Layer A. A true claim can have an insufficient set. A false claim can be asserted by several passages.
- [ ] For a primary duplicate-invariance pair, status must be unchanged after the dependent addition. If the new passage adds an independent evidentiary basis, annotate it in the corroboration arm.

## Layer D — text similarity / reuse (codebook §6)

Label the claim-relevant fragment.

- [ ] `EXACT_REUSE`
- [ ] `NEAR_VERBATIM_REUSE`
- [ ] `PARAPHRASED_REUSE`
- [ ] `TOPICALLY_SIMILAR_NO_REUSE_EVIDENCE`
- [ ] `DISIMILAR_OR_UNRELATED`
- [ ] `UNKNOWN`
- [ ] Similar words do not prove shared origin. Heavy paraphrase does not prove independence.

## Layer E — publication / citation lineage (codebook §7)

Store one or more directed edge labels. Direction is null when it is not known.

- [ ] `COPIED_OR_SYNDICATED_FROM`
- [ ] `QUOTES_OR_CITES`
- [ ] `ATTRIBUTED_TO_OR_REPORTED_FROM`
- [ ] `SHARES_PRIMARY_ARTIFACT_OR_DATASET`
- [ ] `INDEPENDENT_COLLECTION_EVIDENCED`
- [ ] `PARTIAL_OR_MIXED_LINEAGE`
- [ ] `UNKNOWN_LINEAGE`
- [ ] Record the evidence for the edge, the timestamp relation, and the confidence rationale.
- [ ] A new publisher is not new underlying information.
- [ ] A missing citation is not independent collection.

## Layer F — epistemic dependence (codebook §8)

One origin relation per edge. Edges are not assumed to be symmetric or transitive. Do not add edges by transitive closure. Do not replace the edge list with a cluster.

- [ ] `SAME_UNDERLYING_ORIGIN`
- [ ] `SHARED_ORIGIN_WITH_ADDED_INDEPENDENT_COMPONENT`
- [ ] `INDEPENDENT_ORIGIN_EVIDENCED` — requires positive evidence of a distinct collection, measurement, or primary basis. Lack of a citation does not qualify.
- [ ] `DEPENDENCE_RELATION_UNKNOWN`
- [ ] `MULTIPLE_ORIGINS_OR_CONFLICT` — store separate edges and notes. This value is not a cluster id.
- [ ] Confidence in the **relationship** is `HIGH`, `MEDIUM`, or `LOW`, with a rationale. That confidence is not confidence that the claim is true.
- [ ] Unknown and low-confidence links stay unknown for the primary relation-based evaluation unless a predeclared analysis is studying uncertainty.
- [ ] A shared dataset with separate analyses needs an explicit rationale. Do not automatically call it fully independent or fully dependent.
- [ ] `source_origin_family_id` stays null when the origin relation is `DEPENDENCE_RELATION_UNKNOWN`.

## Evidence to capture when it exists (codebook §9)

- [ ] Canonical URL and archived URL or snapshot id.
- [ ] Publication and update timestamps, with time zone if it matters.
- [ ] Publisher or domain, and named author.
- [ ] Cited or quoted sources and outgoing links that bear on the claim.
- [ ] Primary artifact and the exact claim it supports.
- [ ] Passage text hash and span offsets.
- [ ] Rationale and unresolved uncertainty.
- [ ] Do not infer truth from domain reputation.
- [ ] Do not count domain diversity as independence.
- [ ] If an indirect citation path cannot be reconstructed, use unknown.

## Workflow (codebook §10)

- [ ] Two annotators label scored claims, stances, evidence sets, and relations independently.
- [ ] Save raw labels before adjudication. Report raw agreement, a confusion matrix, and nominal Krippendorff’s alpha for each layer. Add Cohen’s kappa when exactly two annotators label every unit with no missing values.
- [ ] Report class prevalence and the unknown rate next to agreement.
- [ ] Hard-case report, separately: `SHARED_ORIGIN_WITH_ADDED_INDEPENDENT_COMPONENT`, `INDEPENDENT_ORIGIN_EVIDENCED`, `TOPICALLY_SIMILAR_NO_REUSE_EVIDENCE`, paraphrased reuse, and unknown cases. State how often adjudication changes each.
- [ ] Adjudicate only after the raw-agreement report, with a third reviewer or a documented consensus.
- [ ] Preserve both original labels and the adjudicated label. Never overwrite the originals.
- [ ] Record annotation time per claim and per relation, how often a chain could be traced, which evidence types were missing, and the proportion of relationships left unknown.

## Exclusion from the primary contrast (codebook §11)

Keep the case in the file. Point `exclusion_reason` at one or more of these codebook conditions:

- [ ] The added passage contributes a new independent factual measurement or primary artifact.
- [ ] The addition changes gold evidence-set status.
- [ ] A source-origin relation required by the pair is unknown.
- [ ] Temporal or scope ambiguity prevents a valid paired comparison.
- [ ] The snapshot cannot be reproduced or the relevant text is unavailable.

Decide exclusion from annotations before model predictions are opened.

## Export (codebook §12)

Each export includes the identifiers and labels named in the codebook: `claim_id`, `claim_family_id`, `reference_time`, `claim_text`, `claim_truth`, `truth_rationale`, `evidence_set_id`, `condition_id`, `passage_id`, `evidence_fragment_id`, `passage_url`, `archive_id_or_hash`, `published_at`, `publisher`, `claim_passage_stance`, `evidence_set_status`, `text_relation`, `lineage_edge_type`, `origin_relation`, `origin_confidence`, `origin_rationale`, `annotator_id`, `annotation_version`, `adjudication_status`, `adjudicated_label`, `exclusion_reason`.

- [ ] The graph in the JSON proposal is authoritative when a fragment has more than one lineage edge. A flat row may repeat once per edge. It must not collapse two edges into one cluster.
- [ ] `adjudication_status` is required by name and has no value list in the codebook. Leave the vocabulary unset until the decision record defines it. Do not invent statuses in the export.
- [ ] Do not store a binary certainty flag in place of `UNKNOWN`, `UNKNOWN_LINEAGE`, or `DEPENDENCE_RELATION_UNKNOWN`.

## Worked shape, not a real annotation

Two fragments, two edges, no cluster. Labels are codebook labels. The fragments are placeholders, not pilot data.

```json
{
  "edges": [
    {
      "evidence_fragment_id_from": "frag_a",
      "evidence_fragment_id_to": "frag_b",
      "text_relation": "PARAPHRASED_REUSE",
      "lineage_edge_types": ["QUOTES_OR_CITES"],
      "origin_relation": "SHARED_ORIGIN_WITH_ADDED_INDEPENDENT_COMPONENT",
      "origin_confidence": "MEDIUM",
      "source_origin_family_id": null
    },
    {
      "evidence_fragment_id_from": "frag_b",
      "evidence_fragment_id_to": "frag_c",
      "text_relation": "UNKNOWN",
      "lineage_edge_types": ["UNKNOWN_LINEAGE"],
      "origin_relation": "DEPENDENCE_RELATION_UNKNOWN",
      "origin_confidence": "LOW",
      "source_origin_family_id": null
    }
  ]
}
```

The second edge is stored. It is not dropped, and it does not pull `frag_c` into a family with `frag_a`. No edge is inferred from `frag_a` to `frag_c`.
