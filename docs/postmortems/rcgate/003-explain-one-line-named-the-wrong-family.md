# Postmortem 003: The Explainer Named the Wrong Signal Family

> **Date:** October 6, 2026  
> **Severity:** High — every human-facing explanation stated the opposite of the gate's decision  
> **Status:** Complete — fixed in M7, regression-tested

## Issues Summary

`explain.py` — the module whose entire job is to make the gate's trust weights legible — shipped in M4 with two bugs in `one_line()`:

1. **`explain_claims` passed `p.w_cross` into `one_line`'s `w_evid` parameter.** Every explanation line named the *opposite* family as the trusted one, and printed the wrong weight next to it.
2. **The up/down-weighted clause compared the wrong pair**, so the sentence could call the *trusted* family "up-weighted" — semantically indefensible and contradicting the module's own docstring example ("cross-model agreement down-weighted").

Both survived four milestones because `explain.py` had **no test file**. They were found within an hour of building the M7 demo, which renders `one_line` output to the screen — the first consumer that made the bug *visible* instead of merely latent.

---

## Finding #1 — A Symmetry Bug Hiding in Plain Sight

### What Happened

`w_cross` and `w_evid` sum to 1.0, so a transposed argument produces *plausible-looking* output: the numbers are in range, the sentence is grammatical, and a reader who does not recompute the complement sees nothing wrong. The headless demo run that exposed it showed a numeric claim with `w_evid = 1.00` alongside the explanation "cross-model agreement down-weighted" attributed to the wrong weight — and the dissonance between the bar chart and the sentence is what triggered the investigation.

### Root Cause

The call site's positional argument order matched the *dataclass attribute order* (`prob, w_cross, w_evid, ...`) rather than the function's parameter order. Positional calls to functions with two same-typed adjacent parameters are an off-by-one waiting to happen.

### Honest Assessment

An evaluator reading M4's explanation tables had been given inverted evidence about the project's central claim (H3). Nothing in M4's acceptance criteria would have caught it, because the criteria tested *that explanations exist*, not *that they are true*. The demo — a mere presentation layer — caught what the evaluation harness did not, because only the demo puts the sentence next to the number.

---

## Finding #2 — The Fix Changed What the Sentence Is Allowed to Claim

### What Happened

The corrected `one_line` now always names the family that received **less than half** the trust (a checkable fact), and appends "despite its larger raw logit" when the gate overrode what the raw numbers supported — precisely the case a reviewer wants to probe.

### Root Cause

The original clause was written as an *interpretation* ("the gate up-weighted X because...") rather than an *observation* ("X received 0.08 of the trust"). Interpretations can be inverted by a bug; observations can only be transposed, which is trivially checkable.

### Prevention

- 13 offline regression tests now live in `tests/test_demo.py`, including assertions that the named family is the minority-trust family and that weights/logits in the sentence match the prediction object.
- Rule adopted: **every function that renders a model decision into words must have a test that checks the words against the numbers**, not just that the words exist.

---

## Lessons Learned

1. **Test the consumer, not the artefact.** A module with zero consumers had zero bugs *found*; the demo's arrival instantly surfaced both.
2. **Never positionally call a function with adjacent same-typed parameters** — keyword arguments at the call site would have made the transposition a visible crash or an obvious diff.
3. **Explanations are claims about numbers; test them like numbers.** "The gate trusted evidence" is an assertion with a truth value, and it was false for every claim in M4's output.
4. **Interpretation-free wording is bug-resistant wording.** "Received less than half the trust" cannot be spun; "up-weighted" can.

## Prevention (implemented)

- `tests/test_demo.py`: 13 tests, network-free, covering the argument contract, the minority-family rule, the raw-logit-override clause, and the CLI path.
- The M7 `DECISIONS.md` entry records both bugs and the render-truthfulness rule.
