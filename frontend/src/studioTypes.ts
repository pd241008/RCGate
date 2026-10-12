import type { SignalName } from "./types";

export interface Facet {
  id: string;
  label: string;
  count: number;
}

export interface LibraryCard {
  source_id: string;
  task_type: string;
  task_label: string;
  dataset_source: string;
  topic_id: string;
  topic_label: string;
  title: string;
  excerpt: string;
  excerpt_model_name: string;
  n_generators: number;
  n_precomputed_claims: number;
  score_status: string;
  score_label: string;
}

export interface LibraryResponse {
  total: number;
  page: number;
  page_size: number;
  n_pages: number;
  applied: {
    q: string;
    task: string;
    topic: string;
    generator: string;
    score: string;
    sort: string;
  };
  facets: {
    tasks: Facet[];
    topics: Facet[];
    generators: Facet[];
    scores: Facet[];
  };
  results: LibraryCard[];
  inventory_totals: { sources: number; responses: number };
  topic_note: string;
}

export interface Passage {
  id: string;
  title: string;
  text: string;
  kind: string;
  evidence_input: boolean;
}

export interface SentenceRow {
  index: number;
  claim_id: string;
  text: string;
  scoring_text: string;
  dealias_changed: boolean;
  start: number;
  end: number;
  score_status: string;
  claim_type_name: string;
  human_span_label: number;
}

export interface StoredResponse {
  response_id: string;
  model_id: string;
  model_name: string;
  generator_id: number;
  text: string;
  quality: string;
  dataset_split: string;
  provenance: string;
  sentences: SentenceRow[];
}

export interface IndependentReference {
  id: string;
  title: string;
  publisher: string;
  url: string;
  excerpt: string;
  verified_on: string;
  relevance: string;
  used_in_rcgate_score: boolean;
}

export interface RecordDetail {
  source_id: string;
  task_type: string;
  task_label: string;
  dataset_source: string;
  topic_label: string;
  title: string;
  task: {
    kind: string;
    question: string | null;
    instruction: string;
    context_note: string;
    prompt_note: string;
    prompt: string;
  };
  passages: Passage[];
  structured: {
    name?: string | null;
    address?: string | null;
    city?: string | null;
    state?: string | null;
    categories?: string | null;
    stars?: string | number | null;
    hours?: Record<string, string> | string | null;
    reviews?: { stars?: number | null; date?: string; text: string }[];
  } | null;
  responses: StoredResponse[];
  independent_references: IndependentReference[];
  independent_reference_note: string;
  partition: string | null;
  scoring: {
    default_response_id: string;
    default_sentence_index: number;
    score_status: string;
    local_extraction_ready: boolean;
    checkpoint_ready: boolean;
  };
}

export interface ExpertBlock {
  signals: string[];
  weights: number[];
  bias: number;
}

export interface ScoreResult {
  status: string;
  reason: string | null;
  feature_source: string | null;
  demo_inference: boolean;
  benchmark_evaluation: boolean;
  partition: string | null;
  partition_note: string | null;
  checkpoint: {
    path: string;
    sha256: string;
    variant: string;
    split_seed: number;
    model_seed: number;
  } | null;
  claim: {
    source_id: string;
    response_id: string;
    claim_id: string;
    sentence_index: number;
    original_sentence: string;
    claim_text: string;
    dealias_changed: boolean;
    claim_type_name: string;
    model_name: string;
    human_span_label: number | null;
    n_sentences: number;
  } | null;
  prediction: {
    prob: number;
    predicted_class: string;
    threshold: number;
    close_to_threshold: boolean;
    close_note: string | null;
    w_cross: number;
    w_evid: number;
    z_cross: number;
    z_evid: number;
    logit: number;
    signals: Record<SignalName, number>;
    cross_n_others: number;
    evidence_source: string;
    evidence_n_passages: number;
    arithmetic_verdict: string;
  } | null;
  experts: {
    standardize_signals: boolean;
    fusion_input: string;
    cross: ExpertBlock;
    evidence: ExpertBlock;
    fusion: { weights: number[]; bias: number };
  } | null;
  worked: {
    signal_values: number[];
    matches_model: boolean;
    tolerance: number;
    z_cross: number;
    z_evid: number;
    logit: number;
    prob: number;
  } | null;
  cache_path: string | null;
  notes: string[];
}

export interface ScoreEnvelope {
  job_id: string | null;
  status: string;
  message: string | null;
  result: ScoreResult | null;
}

export interface HealthResponse {
  ok: boolean;
  live_provider_calls: boolean;
  local_extraction_ready: boolean;
  checkpoint_ready: boolean;
  inventory: {
    n_sources: number;
    n_responses: number;
    citation: string;
    license: string;
    tasks: Record<string, number>;
    topics: Facet[];
    files: Record<string, { sha256: string; match: boolean }>;
    signal_table: {
      path: string;
      n_claims: number;
      n_sources: number;
      claim_scope: string;
      partial_sources: { source_id: string; n_claims: number }[];
      note: string;
    };
    scoring: {
      browseable_sources: number;
      precomputed_claims: number;
      precomputed_sources: number;
      sources_without_precomputed_rows: number;
      local_extraction_ready: boolean;
      checkpoint_path: string;
    };
    topic_note: string;
    distinctions: { id: string; title: string; detail: string }[];
  };
}
