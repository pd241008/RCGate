# Repository state before pilot preflight

**Inspection time:** 23 October 2026  
**Purpose:** Read-only snapshot taken before any `research/pilot_preflight/` report was written.  
**Commands that change history were not used.** No checkout, reset, clean, stash, commit, or push.

This file is a new report. It does not modify tracked source, historical results, or manuscripts.

## Branch and HEAD

| Item | Value |
|---|---|
| Current branch | `review/rcgate-handoff-v1` |
| Upstream | `origin/review/rcgate-handoff-v1` |
| HEAD | `bf9db7d` — Document Stage 8 reproducibility and verify research record (2026-10-20, Nishant Ranjan) |
| Other local branch | `main` at `4709001`, tracking `origin/main` |
| Tracked working tree | Clean. `git diff` and `git diff --cached` were empty. |
| Tracked file count | 434 |

`git status --short --branch` opened with:

```text
## review/rcgate-handoff-v1...origin/review/rcgate-handoff-v1
```

No ahead/behind suffix was printed. The status then listed untracked paths only.

## Recent commits

```text
bf9db7d 2026-10-20 Nishant Ranjan Document Stage 8 reproducibility and verify research record
6d3ef70 2026-10-12 Nishant Ranjan Record the RC-Gate integrity repairs, Stage 8 findings, and offline research studio.
4709001 2026-10-06 Prathmesh Desai Merge pull request #1 from pd241008/dev
ee8ffb7 2026-10-06 Prathmesh Desai docs: move postmortems under docs/ and drop the README citation block
3a7ce1d 2026-10-06 Prathmesh Desai chore: add M0-M7 stage targets to the Makefile
b8eebd9 2026-10-06 Prathmesh Desai docs: add README, ADRs and postmortems in the Design Dungeons format
11313ec 2026-10-05 Prathmesh Desai fix(m7): make the demo app importable when Streamlit executes it as a bare script
f1bc237 2026-10-05 Prathmesh Desai feat(m7): glass-box Streamlit demo with per-claim gate weights and a headless mode
32878ae 2026-10-05 Prathmesh Desai feat(m6): first real-data runs on RAGTruth; H1/H2 negative on this slice, reported as measured
9865b61 2026-10-05 Prathmesh Desai feat(m5): real signal extractors with RAGTruth as the first real benchmark
c208745 2026-10-05 Prathmesh Desai feat(m4): evaluation harness with per-slice metrics, bootstrap CIs, LOGO and gate heatmap
b7b5889 2026-10-05 Prathmesh Desai feat(m3): RC-Gate with gated mixture-of-experts and ablations A5-A7
3c92bbe 2026-10-05 Prathmesh Desai feat(m2): baselines A0-A4 and the M2 acceptance gate on synthetic data
1b75aaa 2026-10-05 Prathmesh Desai feat(m1): synthetic signal table with planted conditional reliability
8fcbd41 2026-10-05 Prathmesh Desai feat(m0): scaffold repo, config system, signal-table contract, cache, splits
```

## Untracked paths

`git status --porcelain` reported **739 untracked entries**. None were staged. Counts by top-level name:

| Top-level path | Untracked entries |
|---|---|
| `results/` | 732 |
| `RCGate_Final_Professor_Review/` | 1 directory |
| `RCGate_Final_Professor_Review.zip` | 1 file |
| `RCGate_Final_Professor_Review_prior/` | 1 directory |
| `RCGate_manuscript_revision/` | 1 directory |
| `RCGate_paper_final/` | 1 directory |
| `rcgate_paper/` | 1 directory |
| `research/` | 1 directory |

Untracked paths under `results/summary/`, counted by experiment directory:

| Directory | Untracked entries |
|---|---|
| `results/summary/ragtruth_factorial_seed_v1` | 483 |
| `results/summary/ragtruth_multi_seed_v1` | 184 |
| `results/summary/ragtruth_corrected_integrity_v1` | 34 |
| `results/summary/ragtruth_split_corrected_v1` | 28 |
| `results/summary/ragtruth_historical_freeze` | 3 |

`results/summary/` also contains tracked experiment output (`ragtruth`, `synthetic`, `smoke`, and summary files inside the directories above). Those historical outputs were not opened for regeneration and were not deleted.

`research/` existed only as untracked plan documents:

- `research/plan/RCGate_Focused_Research_Pivot_v0_3.md`
- `research/plan/RCGate_Pilot_Protocol_v0_2.md`
- `research/plan/RCGate_Annotation_Protocol_v0_1.md`
- `research/plan/RCGate_Pilot_Decision_Record_v0_1.md`
- `research/plan/RCGate_Review_Resolution_Log_v0_1.md`
- `research/plan/README_RCGate_Review_Fixes_v0_3.md`
- `research/plan/RCGate_Cursor_Preflight_Prompt_v0_1.md`

`research/pilot_preflight/` did not exist at inspection time.

## Root listing

Tracked project layout observed at the repository root:

- Code and config: `rcgate/`, `configs/`, `tests/`, `scripts/`, `pyproject.toml`, `Makefile`, `README.md`, `DECISIONS.md`, `docs/`
- Data and results: `data/`, `results/`
- Local environments and caches, gitignored: `.venv/`, `.cache/`, `.pytest_cache/`, `.ruff_cache/`, `node_modules/`, `frontend/node_modules/`
- App surface: `frontend/`, `demo_fixtures/`, `.streamlit/`
- Historical document files present at the root include `RC Gate_Intial_Research Paper Draft.pdf`, `RC-Gate_Project_Proposal.docx`, and `RC-Gate_UserGuide.pdf`
- Untracked review/manuscript directories listed above
- `research/` as listed above

## Diff

Staged diff: empty.  
Unstaged diff of tracked files: empty.

The untracked tree is large because result seed directories and manuscript/review folders are untracked. This preflight adds files only under `research/pilot_preflight/`.
