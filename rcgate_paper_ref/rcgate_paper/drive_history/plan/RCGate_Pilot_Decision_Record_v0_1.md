# RC-Gate Pilot Decision Record v0.1

**Prepared:** 23 October 2026  
**Status:** Complete the freeze fields before scored annotation/model output; update the outcome section only after pilot analysis.  
**Purpose:** Create an auditable decision point, not an informal retrospective justification.

## A. Freeze record — fill before scored runs

- [ ] Exact research question/version frozen: `RCGate_Focused_Research_Pivot_v0_3.md`
- [ ] Pilot protocol frozen: `RCGate_Pilot_Protocol_v0_2.md`
- [ ] Annotation codebook frozen: `RCGate_Annotation_Protocol_v0_1.md`
- [ ] Separate training/calibration items identified and excluded from scored analysis.
- [ ] Sampling frame, claim selection rules, reference time, domain and exclusion rules recorded.
- [ ] Primary V1 LLM judge: exact model/provider or local weights hash: `________________________________`
- [ ] V1 prompt hash/version, decoding, retries, output schema, token budget frozen: `________________________________`
- [ ] Primary V2 NLI model/revision, tokenizer, label mapping and aggregation rule frozen: `________________________________`
- [ ] Passage order/counterbalancing seed and controlled-arm matching rule frozen: `________________________________`
- [ ] Annotator identities/roles, blinding procedure and adjudicator plan recorded.
- [ ] Agreement/reliability gate selected before scored annotation, with rationale: `________________________________`
- [ ] Run environment, code commit/hash, dependency lock and output path recorded: `________________________________`
- [ ] The pilot remains feasibility/descriptive; no confirmatory significance or superiority claim will be made from it.

If any essential model, annotation or data configuration remains unfilled, do not begin scored evaluation. The pilot may begin with annotation calibration and environment inventory only.

## B. Primary outcomes (do not revise after seeing predictions)

For each preselected primary verifier, report:

1. Absolute false-support rate on eligible BASE sets whose gold evidence status is not `ADEQUATE_SUPPORT`.
2. Absolute false-support rate after dependent addition on the same eligible claim/source-family pairs.
3. Paired risk difference `FS_dependent − FS_base`.
4. Results split by `INSUFFICIENT`, `ADEQUATE_REFUTATION`, and `CONFLICTING`.
5. Response to truly independent corroboration, separately from the primary dependence contrast.
6. Token-count/order sensitivity and the naturalistic versus controlled-arm difference.
7. Simple deduplication, lexical/semantic clustering, capping, NLI and fixed LLM judge comparisons.
8. Annotation agreement, unknown rate, adjudication rate and workload.

Numeric LLM scores are secondary diagnostics, not probabilities by default. Claims and variants are grouped; variants are not independent observations.

## C. Predefined interpretation rules

### Support a confirmatory study (not yet a claim of novelty)

Proceed only if a practically meaningful effect is visible in the naturalistic arm and remains after count/token/order controls; the preselected primary systems are reported separately; simple filtering does not fully explain the hard natural cases; relation labels are reliable enough under the frozen gate; and independent-corroboration cases show that the system is not simply ignoring evidence. If only one primary verifier shows the effect, the claim must be explicitly verifier-specific unless later evidence broadens it.

### Revise and rerun a limited pilot

Do this if results depend materially on passage order/token budget, only one condition/verifier shows a possible effect, hard-case labels are ambiguous, or the source-chain sampling process is biased. State exactly what changes and why, and keep the original run intact.

### Stop/pivot the proposed method

Stop if the nearest prior art already covers the same input/target/intervention, the observed failure disappears under controlled conditions, simple dedup/capping resolves natural cases, the relation labels cannot be used reliably, or benefits arise only from abstaining more/ignoring evidence. A stop decision is a successful research outcome because it prevents unsupported claims.

## D. Practical-effect thresholds and confirmatory study

Do **not** invent a numerical effect threshold now merely to make the plan look precise. Use the feasibility pilot to estimate the observed effect, annotation uncertainty, variability across claims, and practical cost. Then define and justify, in a separate dated confirmatory analysis plan **before opening confirmatory test outcomes**:

- the minimum worthwhile reduction in false support;
- the maximum acceptable loss in independent-corroboration sensitivity;
- coverage/abstention operating points, if applicable;
- cost/latency limits;
- sample-size and uncertainty procedure;
- target populations/domains and acceptable generalization degradation.

The confirmatory test set must not be used to select these thresholds, prompts, models or features.

## E. Pilot outcome log — complete after analysis

- Run ID / immutable manifest hash: `________________________________`
- Dates and deviations: `________________________________`
- Naturalistic arm result: `________________________________`
- Controlled arm result: `________________________________`
- V1 result: `________________________________`
- V2 result: `________________________________`
- Strongest simple baseline: `________________________________`
- Annotation reliability/unknown findings: `________________________________`
- Independent-corroboration guardrail: `________________________________`
- Closest prior-art issue unresolved: `________________________________`
- Decision: `GO TO CONFIRMATORY DESIGN / REVISE PILOT / STOP-PIVOT`
- Rationale and dissenting interpretation: `________________________________`
- Reviewer/sign-off and date: `________________________________`

## F. Integrity rules

- Preserve raw inputs, annotator labels, model outputs and scripts unchanged; derived analysis can be regenerated.
- Never select only favourable claim variants or report one verifier among many as though preselected.
- Never label a result an improvement until compared on paired inputs and the strongest fair simple baselines.
- Never describe source dependence, factual truth and evidence sufficiency as interchangeable.
- No repository commit/push, new model training, or manuscript replacement is implied by this decision record.
