export type SignalName = "agree" | "contra" | "sem_dist" | "support" | "src_quality" | "conflict";

export interface SourceCard {
  id: string;
  title: string;
  collection: string | null;
  excerpt: string;
  url: string | null;
  used_in_scoring: boolean;
  kind: "supplied_context" | "additional_reference";
}

export interface ResponseCard {
  generator_id: number;
  model_id: string;
  model_name: string;
  response_id: string;
  claim_id: string;
  text: string;
  opening_sentence: string;
  sentence_index: number;
  n_sentences_in_answer: number;
  provenance: string;
  scored: boolean;
}

export interface Prediction {
  claim_id: string;
  claim_text: string;
  sentence_index: number;
  claim_type: number;
  claim_type_name: string;
  generator_id: number;
  model_id: string;
  model_name: string;
  prob: number;
  predicted_class: string;
  w_cross: number;
  w_evid: number;
  z_cross: number;
  z_evid: number;
  signals: Record<SignalName, number>;
  cross_n_others: number;
  evidence_source: string;
  evidence_n_passages: number;
  arithmetic_verdict: string;
  explanation: string;
  human_span_label: number;
  generation_method: string;
}

export interface Scenario {
  id: string;
  topic: string;
  summary: string;
  provenance_label: string;
  question: string;
  source_id: string;
  task_type: string;
  dataset_source: string;
  scored_claim_id: string;
  claim_scope: string;
  responses: ResponseCard[];
  sources: SourceCard[];
  additional_references: SourceCard[];
  prediction: Prediction;
}

export interface ResearchFigures {
  a0_mean_auroc: string;
  a4_mean_auroc: string;
  a7_mean_auroc: string;
  mean_a7_minus_a4: string;
  mean_a7_minus_a0: string;
  slice: string;
  n_sentences: number;
  n_questions: number;
  n_group_splits: number;
  n_model_initialisations: number;
  independent_datasets: boolean;
  evaluates_demo_claim: boolean;
  report_path: string;
  index_path: string;
}

export interface Library {
  library_id: string;
  kind: string;
  official_benchmark_result: boolean;
  live_provider_calls: boolean;
  playback_label: string;
  generation_method: string;
  checkpoint: {
    path: string;
    sha256: string;
    variant: string;
    split_seed: number;
    model_seed: number;
    namespace: string;
    note: string;
  };
  signal_table: {
    path: string;
    sha256: string;
    claim_scope: string;
    note: string;
  };
  experts: {
    fusion_input: string;
    standardize_signals: boolean;
    cross: { signals: string[]; weights: number[]; bias: number };
    evidence: { signals: string[]; weights: number[]; bias: number };
    fusion: { weights: number[]; bias: number };
    formula: string;
  };
  research: ResearchFigures;
  scenarios: Scenario[];
}
