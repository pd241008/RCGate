# Model selection proposal

**Date:** 23 October 2026  
**Status:** Proposal only. No model was loaded for scoring, no API call was made, and no checkpoint was downloaded.  
**Decision record:** V1 and V2 blanks in `research/plan/RCGate_Pilot_Decision_Record_v0_1.md` stay blank until the user freezes them.

This note names the only candidates already available on this machine. Availability is not evidence that either model exhibits, or fails to exhibit, dependence-related false support. Novelty relative to Byrd (SSRN, 2026) and Belkin, Madsen, and de-Wit (2026) is not established.

## V2 proposal — NLI aggregator

**Proposed id:** `cross-encoder/nli-deberta-v3-small`  
**Local snapshot:** `fa2804872c3b4bd748f38c0185cc85775361e735`  
**Pointer file:** `.cache/models/hub/models--cross-encoder--nli-deberta-v3-small/refs/main` contains that snapshot id.  
**Config base name:** `microsoft/deberta-v3-small`  
**Architecture:** `DebertaV2ForSequenceClassification`, 6 layers, hidden size 768, float32.  
**Label map in the local `config.json`:** `0=contradiction`, `1=entailment`, `2=neutral`. This matches the resolver in `CrossEncoderScorer._resolve_labels` (`rcgate/signals/nli.py`).  
**Tokenizer:** `DebertaV2Tokenizer`, `model_max_length` 512. The project loader defaults to truncating each premise–hypothesis pair at 256 tokens (`CrossEncoderScorer`, `max_length=256`).  
**Code entry points:** `rcgate/signals/nli.py` `CrossEncoderScorer.score`; `rcgate/signals/evidence.py` `score_claim` with `aggregate="max"` or `"mean"`.  
**Hardware:** Apple M4, 24 GiB RAM. The historical project runs this model on CPU. MPS is built into torch 2.14.1 and was not selected. A pilot of tens of claims is within this machine’s CPU budget.  
**License:** The local snapshot contains weights, tokenizer files, and `config.json`. It does not contain a README or license file. Redistribution and the exact usage terms are unverified in this preflight. Confirm the model card before sharing weights.  
**Installed software that would load it:** transformers 5.19.0, sentence-transformers 6.1.0, torch 2.14.1. The checkpoint’s own `transformers_version` field is `4.11.3`. Freeze both the snapshot and these library versions together so a later library upgrade is visible.

### What is not yet frozen for V2

The protocol requires the identifier, tokenizer revision, label mapping, max/mean rule, truncation policy, and software version before scoring.

The weights and label map can be named now. The verdict rule cannot. Current `score_claim` returns continuous support and conflict features for a hallucination detector. It does not emit `ADEQUATE_SUPPORT`, `ADEQUATE_REFUTATION`, `INSUFFICIENT`, or `CONFLICTING`. A pilot adapter has to declare that mapping, and whether the primary aggregation is max, mean, or a contradiction-aware combination, before any scored output is inspected.

`build_scorer` substitutes `LexicalScorer` if the checkpoint fails to load and warns. A frozen V2 run has to fail closed instead. `LexicalScorer` is an offline test double. It is not an NLI model.

### Version-freezing risks for V2

- `refs/main` can move if the cache is refreshed. The scored run must record `fa2804872c3b4bd748f38c0185cc85775361e735`, not the floating main pointer.
- Truncation at 256 versus the tokenizer maximum of 512 changes behavior on long passages. The pilot must log both the cap and the untruncated token count.
- `pyproject.toml` does not pin torch or transformers. The venv versions above are an observation, not a lockfile.
- Pair length is the sum of premise and hypothesis under this tokenizer. The protocol also asks for token counts under the V1 tokenizer. Those are a different count.

## Semantic encoder used beside V2, not as V2

**Id:** `sentence-transformers/all-MiniLM-L6-v2`  
**Local snapshot:** `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`  
**Local README front matter:** `license: apache-2.0`  
**Shape:** BERT, 6 layers, hidden size 384, `max_position_embeddings` 512, WordPiece tokenizer, `model_max_length` 512.  
**Role:** candidate encoder for the semantic near-duplicate baseline only.  
**Threshold:** not chosen. It must be chosen on a calibration or development split that is excluded from reported pilot cases.

## V1 proposal — LLM judge

### What is already on disk

Ollama 0.33.3 is installed at `/opt/homebrew/bin/ollama`. During this inspection the server was not running (`ollama list` could not connect). Local manifests were read without starting the server and without generating text.

| Tag | Same weights? | Config digest | Weight digest | Recorded type |
|---|---|---|---|---|
| `llama3.2:1b` | Yes | `sha256:4f659a1e86d7f5a33c389f7991e7224b7ee6ad0358b53437d54c02d2e1b1118d` | `sha256:74701a8c35f6c8d9a4b91f3f3497643001d63e0c7a84e085bed452548fa88d45` | GGUF, family `llama`, `model_type` `1.2B`, quantization `Q8_0`, about 1.32 GB |
| `llama3.2:latest` | Same config digest and same weight digest as `1b` | same | same | same |

The template blob records a knowledge cutoff of December 2023. Two license blobs are stored with the model: the Llama 3.2 Community License Agreement (version release date printed in the file: 25 September 2024) and the Llama 3.2 Acceptable Use Policy. This preflight does not reproduce those texts. Read them before a scored run. Research use still has to stay inside that license and policy.

No OpenAI, Anthropic, or other provider SDK is installed. No `.env` file exists. The API key names checked in the environment were unset. `configs/budget.yaml` does not make those named APIs callable.

### Proposed accessible V1, with the limitation stated

**Propose:** Ollama model identity `llama3.2:1b`, frozen by weight digest `sha256:74701a8c35f6c8d9a4b91f3f3497643001d63e0c7a84e085bed452548fa88d45`, not by the tag `latest`.

This is the only LLM whose weights are already on the machine. It can run locally at no API cost on this M4. It is a 1.2B-parameter quantized model. A feasibility result on it is about this verifier. It does not stand in for a current frontier LLM judge. A null result here would not show that larger judges are unaffected. A positive false-support shift here would not show that larger judges have the same shift.

### Fields still unknown, so V1 is not frozen

| Field the protocol requires | Current evidence |
|---|---|
| Provider snapshot | Local GGUF digest above. Ollama tag `latest` is the same file today and can change later. |
| System and user prompt | No pilot prompt exists. `rcgate/prompts/` is empty. |
| Decoding | Not set. Temperature, seed, and whether this Ollama build is deterministic were not tested, because no generation was run. |
| Output schema | Not defined. The judge must be required to return one of the four evidence-status labels plus passage citations. |
| Retry policy | Not defined. |
| Context length | Not stored in the small Ollama config blob. The 1.3 GB GGUF was not parsed. The running server’s `num_ctx` was not queried. Public Llama 3.2 materials describe a long context; the runtime value can be much smaller. This must be chosen and logged before scoring. |
| Tokenizer for the controlled arm | No separate tokenizer file is in the manifest. Token budgets for Arm B cannot be computed for V1 until a tokenizer or a count API is frozen. |
| Software version | Client reports 0.33.3. Server version was not read. |

### Options if this V1 is rejected

These options were not executed.

1. **Keep the on-disk 1.2B model** and describe every result as specific to it. Smallest path. No download.
2. **Authorize a later download** of a larger local instruct model. Nothing larger is in the Hugging Face cache or the Ollama manifests. A download needs a separate approval, a named id, a digest check, and a license check before scoring.
3. **Authorize an API judge later.** That needs a key, a client, a dated model snapshot, and a spend cap written into the decision record. The historical `$2` / `400` call dry-run cap is not that authorization. No call should be made to discover model lists.

Until one option is written into the decision record, scored V1 runs stay blocked. Annotation calibration and schema work do not need V1.

## Explicit non-selections

- RAGTruth’s generator names (`gpt-4-0613`, `gpt-3.5-turbo-0613`, Mistral 7B Instruct, Llama-2 7B/13B/70B chat) are models that produced the historical corpus. Their weights are not a local judge, and their stored answers are not a verifier configuration.
- A8 majority vote is unimplemented for this data because judge columns are absent. It is not V1.
- `LexicalScorer` is not V2.
- MiniLM is the semantic-duplicate encoder, not the NLI aggregator.
- Stage 8 checkpoints under `results/summary/` score the old hallucination task. They are not a pilot verifier.
