# Feature specification

**Frozen:** 23 October 2026.  
The set is small on purpose. Nothing is added because a later test table looks better.

## Models

- NLI: `cross-encoder/nli-deberta-v3-small` at revision `fa2804872c3b4bd748f38c0185cc85775361e735`.
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` at revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.

Both are already in the local Hugging Face cache. A mismatch aborts the run. No new checkpoint is downloaded under this protocol.

The NLI head's entailment and contradiction probabilities are the two numbers used below. If the cached head's label order is not entailment, neutral, contradiction, the implementation stops and records the label map rather than guessing an index.

## Evidence text

- Summary: `source_info` as a string, split into sentences with `sentence_spans`.
- QA: the `passages` string, split the same way. The question string is not evidence for or against the answer sentence.
- Data2txt: a deterministic plain-text rendering of the JSON object, one field per line, keys sorted, nested objects flattened with dotted keys, lists joined by a single space. That rendering is then split into sentences. The rendering function is fixed in the implementation prompt and hashed in the manifest. It is not tuned on labels.

BM25 uses the existing tokenizer in `rcgate/signals/evidence.py` over those evidence sentences. Top 3 sentences are kept. If fewer than 3 exist, all are kept. If none exist, grounding features are missing and the row is reported as a missingness count rather than filled with 0.5.

## Grounding features

Three numbers, each in `[0, 1]`:

1. `g_max_entail`: maximum entailment probability of the target sentence given each of the top evidence sentences.
2. `g_max_contradict`: maximum contradiction probability on the same pairs.
3. `g_mean_entail`: mean entailment probability on the same pairs.

`src_quality` is not included. On this corpus it would be a constant or a task code.

## Lexical baseline

`lex_overlap`: size of the whitespace-token intersection of the target sentence and the concatenated top evidence sentences, divided by the number of tokens in the target sentence. This baseline does not use the NLI model.

## Peer features

Peers are the other models' full `response` texts on the same `evidence_hash`. Labels on those responses are not read.

Peer order is the fixed roster in `rcgate/data/ragtruth.py`, skipping the target model. k uses the first k names that remain:

`gpt-4-0613`, `gpt-3.5-turbo-0613`, `mistral-7B-instruct`, `llama-2-7b-chat`, `llama-2-13b-chat`, `llama-2-70b-chat`.

This order is a deployment rule, "ask the earlier roster models first," not a search for the peer that predicts the label. It does mean k=1 is GPT-4 whenever the target is not GPT-4. The paper has to say that in the cost section. A sensitivity, exploratory, repeats k=1 once for each single other model and reports the mean of those six-minus-one contrasts. It does not pick the best peer on the test set.

For each selected peer response, BM25 selects the top 3 sentences of that response against the target sentence, using the same tokenizer. One NLI call uses those sentences joined by spaces as the premise and the target sentence as the hypothesis. One embedding comparison uses the maximum cosine similarity between the target sentence and any sentence of that peer response.

At a given k, with at least one peer:

1. `p_agree`: mean entailment across the k peers.
2. `p_contra`: maximum contradiction across the k peers.
3. `p_sem_dist`: 1 minus the mean of the k maximum cosine similarities.

k=0 uses no peer features. The primary contrast is k=5. The curve also reports k=1 and k=2.

If a peer response has no sentence, that peer is skipped and `k_effective` is stored. A row with `k_effective=0` is a missing peer row, not a filled 0.5, and its count is reported.

## Explicitly excluded

Gold spans, peer labels, `implicit_true`, `due_to_null`, `meta`, `split`, `model`, `task_type`, `temperature`, `quality`, the domain tag, `src_quality`, and `claim_type`.

## Call pattern for the cost table

Per target sentence, before cache hits: up to 3 evidence NLI calls, plus 1 NLI call per peer used, plus 1 embedding encoding of the target sentence and the peer sentences. The manifest records actual calls after caching. It does not record a dollar figure the corpus does not contain.
