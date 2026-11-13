# Group and leakage audit

**Date:** 23 October 2026.  
Question identity is the evidence, not a bare `source_id` and not a field called `question_id`. The files have no `question_id`. `rcgate/data/ragtruth.py` copies `source_id` into `question_id` when it builds a frame.

## What was compared

For every source, the official `split` values of its six responses were compared. Prompt strings, whitespace-normalized prompts, and a SHA-256 of the whitespace-normalized evidence text were compared across the official train and test sets.

Evidence text means `source_info` for Summary. For QA and Data2txt it means the canonical JSON of the `source_info` object, with sorted keys. The domain tag in `source` was not treated as evidence.

## Results

- Responses of one `source_id` never fall in both official splits. Mixed-split sources: 0.
- Exact prompts that appear in both official splits: 0.
- Normalized prompts that appear in both official splits: 0.
- Normalized evidence hashes that appear in both official splits: 0.
- Duplicate response ids: 0. Duplicate source ids: 0. Empty responses: 0. Empty evidence: 0.
- One evidence hash, and the same prompt, is shared by two source ids: Summary `12084` and `12085`. Both are official train. A split that groups only by `source_id` can place this pair on opposite sides. A split that groups by evidence hash cannot.

The official split is source-disjoint, including this duplicate pair. It is safe to use as the outer train and test partition. New random splits inside the train set must use the evidence hash as the group key so `12084` and `12085` stay together.

Tasks do not share sources. Each source has one `task_type`. Holding out a task therefore holds out its sources, provided the duplicate pair is already covered by the hash rule. Both members are Summary.

## What must not cross a split

- Gold spans, sentence labels, `implicit_true`, `due_to_null`, and `meta` are outcomes. They may define the label and they may stratify the train-versus-calibration cut inside official train. They must not enter features, and they must not be used to choose features or thresholds on official test.
- Peer features may read the other five responses' `response` text for the same evidence hash. They must not read those responses' labels, quality flags as a shortcut for the label, or split name.
- Grounding features may read the target sentence and `source_info`. They must not read gold spans.
- `model` and `task_type` identify the slice being reported. They are not inputs to the primary scorer. A task-rate baseline is allowed to use `task_type`, because that baseline exists to show what task identity alone can do.
- `temperature` and the domain tag (`MARCO`, `Yelp`, `CNN/DM`, `Recent News`) are out of the primary feature set. The domain tag is a task code in disguise: Yelp is Data2txt, MARCO is QA, and the two news tags are Summary.

## Generator holdout is a different rule

`leave_one_generator_out` in `rcgate/data/splits.py` keeps every generator in the test frame and only drops the held-out generator from train and validation. Scoring that whole test frame is not a generator-shift result. The protocol in `SPLIT_SPECIFICATION.md` replaces it for this study. Sibling text on a test source may still be an unlabeled peer feature.
