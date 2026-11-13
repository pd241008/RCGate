# RC-Gate v0.2 Review Resolution Log v0.1

**Prepared:** 23 October 2026  
**Purpose:** Map each point in the review of v0.2 to the document changes made for v0.3. This log records design corrections only; it does not assert that the pilot has succeeded.

| Review issue | Change made | Location | Remaining work |
|---|---|---|---|
| 1. Duplication confounded with context length/count/order | Split naturalistic duplication from a length/count-controlled arm; record token counts; counterbalance order and repeat a sensitivity subset; keep arm interpretations separate. | `RCGate_Pilot_Protocol_v0_2.md` §§5, 7; pivot v0.3 §§5–6 | Implement control matching and inspect residual confounds during preflight. |
| 2. Hypothesis too easy to satisfy | Preselect exactly two primary verifier families (one fixed LLM judge and one fixed NLI aggregator); prohibit post-hoc substitution; interpret one-model-only effects narrowly. | Pilot v0.2 §§2, 9; decision record §§A–C | Choose exact model identifiers/revisions from the real environment before scoring. |
| 3. Paired change can hide already-high error | Require base and dependent-addition absolute false-support rates, paired risk difference, separate evidence-status strata, and truth-level false confirmation as a distinct outcome. | Pilot v0.2 §7; pivot v0.3 §6 | Write metric script and test it on toy examples before any scored runs. |
| 4. Provenance cannot always be represented as clusters | Define claim-relevant evidence-fragment nodes and typed, directed, potentially partial/non-transitive relations; separate text similarity, publication lineage and epistemic dependence. | `RCGate_Annotation_Protocol_v0_1.md` §§2, 6–8; pivot v0.3 §§2, 4, 8 | Validate the codebook on training cases; report hard-case uncertainty. |
| 5. Gold-lineage oracle was called an upper bound too broadly | Rename to “gold-provenance oracle diagnostic” and state it evaluates only the specified correction with gold labels; it is not a general theoretical bound. | Pivot v0.3 §§4, 7; pilot v0.2 §6 | Compare oracle diagnostic with simple methods after implementation. |
| 6. Missing direct novelty threats / cross-disciplinary scope | Add Byrd's 2026 SSRN preprint and Belkin et al.'s 2026 source-dependence study to the novelty-threat matrix and reference list; mark full-text/code audit and peer-review status as unresolved; expand audit scope beyond NLP. | Pivot v0.3 §§1, 9, references | Full-text/method/code inspection and citation-chain audit remain open; novelty is not established. |
| 7. Annotation reliability lacked measurable plan | Specify raw agreement, confusion matrices, nominal Krippendorff's alpha, optional Cohen's kappa, hard-case stratification, unknown/adjudication rates and workload; require reliability gate before scored annotation. | `RCGate_Annotation_Protocol_v0_1.md` §10; pilot v0.2 §8; decision record §A | Set and document the acceptance rule before scored annotation after a separate calibration batch. |
| Fairness issue for IMRRF | Keep fixed-evidence comparison as the controlled test; label same-input filter as an adaptation unless original method/pipeline is reproduced; defer end-to-end retrieval comparison. | Pilot v0.2 §6; pivot v0.3 §7 | Inspect the original paper/repository and document exact feasible comparison. |
| Scope too large | Make product/human evaluation secondary and conditional; first perform preflight, annotation calibration and a feasibility pilot. | Pivot v0.3 executive decision and §§4, 10–11; Cursor prompt | Do not build the full auditor or run a human study before the scientific core survives. |

## Status

**The document-level fixes are implemented in the v0.3/v0.2 package.** The literature audit is still incomplete, the local repository has not been modified by this package, no model inference has been run, and no empirical result has been generated for the redesigned research question.
