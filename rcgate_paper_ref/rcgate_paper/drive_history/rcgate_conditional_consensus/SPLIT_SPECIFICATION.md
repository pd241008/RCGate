# Split specification

**Frozen:** 23 October 2026.

## Group key

`evidence_hash` is the SHA-256 of the whitespace-normalized canonical evidence:

- Summary: the `source_info` string.
- QA and Data2txt: JSON of the `source_info` object with sorted keys and `ensure_ascii=False`.

Whitespace normalization collapses internal whitespace and strips ends, then lowercases, matching `audit_ragtruth_counts.py`. All sentences from all responses that share an `evidence_hash` are one group. This merges Summary sources `12084` and `12085`.

`source_id` remains on the row for audit. It is not the split key.

## Primary partition

Use the official `split` field.

- Train groups: evidence hashes whose responses are official train. 2,515 source ids, minus one hash because of the merged pair, so 2,514 train groups if that pair is the only collision. The implementation must count hashes rather than assume 2,514.
- Test groups: official test. 450 source ids, 150 per task, and the audit found no test-side collision. The implementation must confirm the hash count.

No official-test sentence is used to fit, calibrate, or choose a threshold.

Inside official train, 20% of evidence hashes form the calibration set and 80% form the fit set. Assignment is group-stratified by whether the hash has at least one principal positive sentence. Seed `20261023`. Hashes are shuffled with `numpy.random.Generator(np.random.PCG64(20261023))`. The duplicate pair has one hash, so it cannot divide.

Stratification uses training labels only. It does not look at official test.

## Held-out generator

For each target model `m`, in a run that is separate from the primary fit:

- Fit and calibration groups are official-train evidence hashes.
- Fit rows are sentences whose model is not `m`.
- Calibration rows are sentences whose model is not `m`.
- Test rows are official-test sentences whose model is `m`.

Other models' sentences on an official-test source are not test outcomes for this axis. Their text may still be the unlabeled peer context for a sentence from `m`.

The scorer does not receive a generator indicator. `leave_one_generator_out` in `rcgate/data/splits.py` is not this split. That function leaves the other generators inside the test frame.

## Held-out task

For each task `t`:

- Fit and calibration use official-train hashes whose task is not `t`.
- Test uses official-test hashes whose task is `t`.

Tasks do not share sources, so this is source-disjoint. Results are three separate tables. A single score that averages a generator holdout with a task holdout is not reported as a primary result.

## Combined stress

A cell that is both a held-out generator and a held-out task is exploratory. It is interpreted only when the official-test positive count is at least 30. GPT-4 QA test has 1 positive sentence, so that combined cell has no claim.

## Official-test positive counts used to set the floor

These counts are label prevalence. They were computed before any feature was scored, and they are why the floor is 30.

| Task | Model | Official-test positive sentences |
|---|---|---:|
| QA | gpt-4-0613 | 1 |
| QA | gpt-3.5-turbo-0613 | 16 |
| Summary | gpt-3.5-turbo-0613 | 9 |
| Summary | gpt-4-0613 | 9 |
| Summary | llama-2-13b-chat | 35 |
| Summary | llama-2-70b-chat | 35 |
| Data2txt | gpt-4-0613 | 38 |
| Data2txt | gpt-3.5-turbo-0613 | 40 |
| Summary | llama-2-7b-chat | 64 |
| QA | mistral-7B-instruct | 82 |
| QA | llama-2-13b-chat | 88 |
| QA | llama-2-70b-chat | 101 |
| Summary | mistral-7B-instruct | 113 |
| QA | llama-2-7b-chat | 159 |
| Data2txt | llama-2-70b-chat | 178 |
| Data2txt | llama-2-7b-chat | 183 |
| Data2txt | mistral-7B-instruct | 226 |
| Data2txt | llama-2-13b-chat | 267 |

Cells below 30 are descriptive counts only.
