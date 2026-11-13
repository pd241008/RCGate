# Metric definitions

**Frozen:** 23 October 2026, before any scored feature matrix.

## Average precision

For a set of sentences with binary labels `y_i` and scores `s_i`, average precision is the standard precision-at-recall integral used by scikit-learn's `average_precision_score`: the sum over positive sentences of `(R_n - R_{n-1}) P_n` as scores are sorted descending. Ties use that implementation's stable behaviour. The denominator is the set of sentences named for that contrast, not a token count and not a response count.

## Primary metric

Let `AP_t(model)` be average precision on the official-test sentences of task `t`, for `t` in {QA, Summary, Data2txt}.

`Delta_t = AP_t(grounding + peer, k=5) - AP_t(grounding only)`

`Delta_macro = (Delta_QA + Delta_Summary + Delta_Data2txt) / 3`

`Delta_macro` is the primary number. Each task has equal weight, regardless of how many sentences or positives it contains. A single AP pooled over all test sentences is secondary and is named `Delta_pooled`. It is not the headline, because Data2txt contains most of the positive sentences.

The interval is the percentile interval of `Delta_macro` under the paired group bootstrap in the protocol. A claim that peer features improve on grounding is made only if that interval lies entirely above zero.

## Per-generator reporting

For model `m` and task `t`, `Delta_{m,t}` uses only official-test sentences of that model and task. If that cell has fewer than 30 positive sentences, the table prints the positive count and does not interpret the AP. Cells at or above 30 are exploratory descriptions of the primary contrast. They are not thirty additional primary tests.

The held-out-generator summary is the unweighted mean of `Delta_{m,t}` over cells of the held-out model that meet the 30-positive floor. If no cell meets the floor, that generator has no transfer claim.

## Secondary metrics

Computed on the same sentence sets as the AP they accompany.

- **AUROC.** Rank discrimination. Secondary because the positive rate is 11% overall and about 2% for the GPT models.
- **Precision, recall, and F1.** The threshold maximizes F1 on the calibration groups inside official train, separately for each fitted scorer. That threshold is applied unchanged to official test. One global threshold, not a threshold per test task.
- **Brier score.** Only for scorers that output a probability. Logistic regression qualifies. Gradient boosting qualifies if it is fit with a probabilistic objective. The parameter-free mean does not, unless it already lies in `[0, 1]`, in which case Brier is descriptive and is not called a calibrated probability.
- **Calibration plot.** Reliability curve on official test, with bins fixed at 10 equal-width bins on `[0, 1]`. Bin edges are not chosen to improve the picture.
- **Peer curve.** `Delta_macro(k)` for k in {0, 1, 2, 5}, where k=0 is grounding only. Exploratory, except that the operational reading in the protocol uses the k=2 versus k=0 task intervals.

## What is not a metric of this study

Token-level AUC, response-level F1, and any score from the historical 800-sentence slice. Response-level rates may be described as corpus facts. They are not the estimand.
