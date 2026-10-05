# Benchmark records

Provenance for every real dataset this project reads. The machine-readable twin of
`RAGTruth.md` is `ragtruth.json`, written by `rcgate.data.ragtruth.write_schema_record` at
build time, so the numbers in a results table and the bytes that produced them cannot drift
apart.

| file | benchmark | licence | pinned by |
|---|---|---|---|
| `ragtruth.json` | RAGTruth (Niu et al., ACL 2024) | MIT | sha256 of both JSONL files |

Nothing else is listed until it has a loader: a provenance record for a dataset the code
cannot read would be decoration.

Rule that applies to all of them: the raw download is never committed (`data/raw/` is
gitignored), every file is verified against a recorded sha256 before it is parsed, and the
dataset's own split field is ignored in favour of the question-grouped split this repo
applies to every benchmark.