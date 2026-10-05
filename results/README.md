# results/

Everything here is gitignored except this file and `summary/`.

Per-run artefacts (`<tag>/<variant>_seed<seed>/`) stay local: they contain the resolved
config, a metrics JSON, the trained checkpoint and the split object. Only the curated
tables in `summary/` are committed, because those are what the report quotes.

Each committed summary file carries, in its header, the git hash and config it came from
and labels synthetic-benchmark numbers as **synthetic** (constraint C8).
