import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { EMPTY_REFERENCE_NOTE, QA_CONTEXT_NOTE, RESEARCH_FIGURES } from "./researchFigures";
import type { ScoreResult } from "./studioTypes";

const MODELS = [
  ["gpt-4-0613", "GPT-4-0613", "111"],
  ["gpt-3.5-turbo-0613", "GPT-3.5-turbo-0613", "112"],
  ["mistral-7B-instruct", "Mistral-7B-Instruct", "113"],
  ["llama-2-7b-chat", "Llama-2-7B-chat", "114"],
  ["llama-2-13b-chat", "Llama-2-13B-chat", "115"],
  ["llama-2-70b-chat", "Llama-2-70B-chat", "116"],
] as const;

function sigmoid(logit: number): number {
  return 1 / (1 + Math.exp(-logit));
}

function scoreFor(responseId: string, sentenceIndex: number): ScoreResult {
  const prob = sentenceIndex === 0 ? sigmoid(0.15) : 0.12;
  const logit = sentenceIndex === 0 ? 0.15 : Math.log(prob / (1 - prob));
  const zCross = sentenceIndex === 0 ? 0.2 : 0.24;
  const zEvid = sentenceIndex === 0 ? 0.1 : 0;
  const claim = sentenceIndex === 0 ? "The flight takes 3.7 hours." : "A second stored sentence.";
  return {
    status: "complete",
    reason: null,
    feature_source: "precomputed_row",
    demo_inference: true,
    benchmark_evaluation: false,
    partition: "train",
    partition_note: "This source is in the training partition. The probability is a recorded demo inference, not a benchmark score.",
    checkpoint: {
      path: "results/summary/ragtruth_factorial_seed_v1/A7_split0_model0/model.joblib",
      sha256: "abc",
      variant: "A7",
      split_seed: 0,
      model_seed: 0,
    },
    claim: {
      source_id: "12226",
      response_id: responseId,
      claim_id: `${responseId}#${sentenceIndex}`,
      sentence_index: sentenceIndex,
      original_sentence: claim,
      claim_text: claim,
      dealias_changed: false,
      claim_type_name: "numeric",
      model_name: MODELS.find((item) => item[2] === responseId)?.[1] ?? "GPT-4-0613",
      human_span_label: 0,
      n_sentences: 2,
    },
    prediction: {
      prob,
      predicted_class: prob >= 0.5 ? "Likely hallucinated" : "Likely supported",
      threshold: 0.5,
      close_to_threshold: Math.abs(prob - 0.5) <= 0.05,
      close_note: Math.abs(prob - 0.5) <= 0.05 ? "Close to the classification threshold; interpret cautiously." : null,
      w_cross: 0.5,
      w_evid: 0.5,
      z_cross: zCross,
      z_evid: zEvid,
      logit,
      signals: { agree: zCross, contra: 0, sem_dist: 0, support: zEvid, src_quality: 0.9, conflict: 0 },
      cross_n_others: 5,
      evidence_source: "context",
      evidence_n_passages: 3,
      arithmetic_verdict: "unverifiable",
    },
    experts: {
      standardize_signals: false,
      fusion_input: "logit",
      cross: { signals: ["agree", "contra", "sem_dist"], weights: [1, 0, 0], bias: 0 },
      evidence: { signals: ["support", "src_quality", "conflict"], weights: [1, 0, 0], bias: 0 },
      fusion: { weights: [1, 1], bias: 0 },
    },
    worked: {
      signal_values: [zCross, 0, 0, zEvid, 0.9, 0],
      matches_model: true,
      tolerance: 0.001,
      z_cross: zCross,
      z_evid: zEvid,
      logit,
      prob,
    },
    cache_path: null,
    notes: ["Features came from a stored signal-table row."],
  };
}

function libraryBody(url: string) {
  const filtered = url.includes("task=QA") || url.includes("q=nash") || url.includes("topic=logic");
  return {
    total: filtered ? 1 : 2,
    page: 1,
    page_size: 20,
    n_pages: 1,
    applied: { q: "", task: "", topic: "", generator: "", score: "", sort: "source" },
    facets: {
      tasks: [
        { id: "QA", label: "QA", count: 989 },
        { id: "Summary", label: "Summary", count: 943 },
        { id: "Data2txt", label: "Data-to-text", count: 1033 },
      ],
      topics: [
        { id: "logic", label: "Logic and game theory", count: 4 },
        { id: "other", label: "Other or unclassified", count: 234 },
      ],
      generators: [{ id: "llama-2-70b-chat", label: "Llama-2-70B-chat", count: 2965 }],
      scores: [{ id: "precomputed", label: "Precomputed first-sentence scores", count: 134 }],
    },
    results: [
      {
        source_id: "12226",
        task_type: "QA",
        task_label: "QA",
        dataset_source: "MARCO",
        topic_id: "mathematics",
        topic_label: "Mathematics and calculations",
        title: "how long would it take to fly 370 miles while flying at 100 mph",
        excerpt: "Unable to answer based on given passages.",
        excerpt_model_name: url.includes("generator=llama-2-70b-chat") ? "Llama-2-70B-chat" : "GPT-4-0613",
        n_generators: 6,
        n_precomputed_claims: 6,
        score_status: "precomputed",
        score_label: "Precomputed first-sentence scores",
      },
    ],
    inventory_totals: { sources: 2965, responses: 17790 },
    topic_note: "Topics are navigation aids.",
  };
}

function recordBody() {
  const long = `${"word ".repeat(180)}END-OF-ANSWER`;
  return {
    source_id: "12226",
    task_type: "QA",
    task_label: "QA",
    dataset_source: "MARCO",
    topic_label: "Mathematics and calculations",
    title: "how long would it take to fly 370 miles while flying at 100 mph",
    task: {
      kind: "qa",
      question: "how long would it take to fly 370 miles while flying at 100 mph",
      instruction: "Answer the stored question using the supplied passages.",
      context_note: QA_CONTEXT_NOTE,
      prompt_note: "The text below is the prompt stored in RAGTruth.",
      prompt: "Briefly answer the following question:",
    },
    passages: [
      {
        id: "passage-1",
        title: "Supplied context passage 1",
        text: "A passage about travel time that was stored with the question.",
        kind: "supplied_context",
        evidence_input: true,
      },
    ],
    structured: null,
    responses: MODELS.map(([modelId, modelName, responseId], index) => ({
      response_id: responseId,
      model_id: modelId,
      model_name: modelName,
      generator_id: index,
      text: index === 0 ? long : `Stored answer from ${modelName}.`,
      quality: "good",
      dataset_split: "train",
      provenance: `RAGTruth response.jsonl id ${responseId}`,
      sentences: [
        {
          index: 0,
          claim_id: `${responseId}#0`,
          text: index === 0 ? long.slice(0, 40) : `Stored answer from ${modelName}.`,
          scoring_text: index === 0 ? long.slice(0, 40) : `Stored answer from ${modelName}.`,
          dealias_changed: false,
          start: 0,
          end: 12,
          score_status: "precomputed",
          claim_type_name: "numeric",
          human_span_label: 0,
        },
        {
          index: 1,
          claim_id: `${responseId}#1`,
          text: "A second stored sentence.",
          scoring_text: "A second stored sentence.",
          dealias_changed: false,
          start: 20,
          end: 40,
          score_status: "local",
          claim_type_name: "abstractive",
          human_span_label: 0,
        },
      ],
    })),
    independent_references: [],
    independent_reference_note: EMPTY_REFERENCE_NOTE,
    partition: "train",
    scoring: {
      default_response_id: "111",
      default_sentence_index: 0,
      score_status: "precomputed",
      local_extraction_ready: true,
      checkpoint_ready: true,
    },
  };
}

function healthBody() {
  return {
    ok: true,
    live_provider_calls: false,
    local_extraction_ready: true,
    checkpoint_ready: true,
    inventory: {
      n_sources: 2965,
      n_responses: 17790,
      citation: "Niu et al. (2024), RAGTruth.",
      license: "MIT",
      tasks: { QA: 989, Summary: 943, Data2txt: 1033 },
      topics: [],
      files: {},
      signal_table: {
        path: "data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet",
        n_claims: 800,
        n_sources: 134,
        claim_scope: "first_sentence",
        partial_sources: [{ source_id: "11775", n_claims: 2 }],
        note: "Each stored claim is sentence index 0.",
      },
      scoring: {
        browseable_sources: 2965,
        precomputed_claims: 800,
        precomputed_sources: 134,
        sources_without_precomputed_rows: 2831,
        local_extraction_ready: true,
        checkpoint_path: "results/summary/ragtruth_factorial_seed_v1/A7_split0_model0/model.joblib",
      },
      topic_note: "Topics are navigation aids.",
      distinctions: [
        { id: "browse", title: "Available to browse", detail: "All 2,965 local source records can be searched." },
      ],
    },
  };
}

function jsonResponse(body: unknown) {
  return {
    ok: true,
    status: 200,
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as Response;
}

describe("research studio", () => {
  const requested: string[] = [];

  beforeEach(() => {
    requested.length = 0;
    vi.stubGlobal("fetch", async (input: RequestInfo, init?: RequestInit) => {
      const url = String(input);
      requested.push(`${init?.method ?? "GET"} ${url} ${String(init?.body ?? "")}`);
      if (url.startsWith("/api/health")) return jsonResponse(healthBody());
      if (url.startsWith("/api/library/")) return jsonResponse(recordBody());
      if (url.startsWith("/api/library")) return jsonResponse(libraryBody(url));
      if (url.startsWith("/api/score")) {
        const body = JSON.parse(String(init?.body ?? "{}")) as { response_id: string; sentence_index: number };
        return jsonResponse({
          job_id: null,
          status: "complete",
          message: null,
          result: scoreFor(body.response_id, body.sentence_index),
        });
      }
      throw new Error(`unexpected ${url}`);
    });
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("searches and filters the local library without autoplaying a score", async () => {
    render(<App />);
    expect(await screen.findByRole("heading", { name: /Search the stored questions/ })).toBeInTheDocument();
    expect(screen.getByText(/Showing 2 of 2,965 records/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Search questions/), { target: { value: "nash" } });
    await waitFor(() => expect(requested.some((url) => url.includes("q=nash"))).toBe(true));
    fireEvent.change(screen.getByLabelText("Task"), { target: { value: "QA" } });
    await waitFor(() => expect(requested.some((url) => url.includes("task=QA"))).toBe(true));
    fireEvent.change(screen.getByLabelText("Topic"), { target: { value: "logic" } });
    await waitFor(() => expect(requested.some((url) => url.includes("topic=logic"))).toBe(true));
    fireEvent.change(screen.getByLabelText("Generator"), { target: { value: "llama-2-70b-chat" } });
    await waitFor(() => expect(requested.some((url) => url.includes("generator=llama-2-70b-chat"))).toBe(true));
    expect(await screen.findByText(/excerpt from Llama-2-70B-chat/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Clear all filters" }));
    await waitFor(() => expect(requested.at(-1)).not.toMatch(/task=|topic=|generator=|q=/));
  });

  it("opens a source, changes the answer and sentence, and does not autoplay", async () => {
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: /how long would it take to fly/i }));
    const analysis = await screen.findByRole("region", { name: /Mathematics and calculations analysis/ });
    expect(analysis).toHaveAttribute("data-stage", "task");
    expect(analysis).toHaveAttribute("data-playing", "false");
    expect(screen.getByText("Recorded demo · stored RAGTruth responses")).toBeInTheDocument();
    expect(screen.getByText(QA_CONTEXT_NOTE)).toBeInTheDocument();
    expect(screen.getByText(EMPTY_REFERENCE_NOTE)).toBeInTheDocument();
    for (const [, name] of MODELS) {
      expect(screen.getByRole("heading", { name })).toBeInTheDocument();
    }
    expect(screen.queryByText("Claude")).not.toBeInTheDocument();
    expect(await screen.findByText("53.74%")).toBeInTheDocument();
    expect(screen.getByText(/not ground truth/)).toBeInTheDocument();
    expect(screen.getAllByText(/not a benchmark score/).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Play walkthrough" }));
    expect(analysis).toHaveAttribute("data-playing", "true");
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    expect(analysis).toHaveAttribute("data-playing", "false");
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(analysis).toHaveAttribute("data-playing", "true");
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(analysis).toHaveAttribute("data-stage", "context");
    fireEvent.click(screen.getByRole("button", { name: "Previous" }));
    expect(analysis).toHaveAttribute("data-stage", "task");
    fireEvent.click(screen.getByRole("button", { name: "Skip to result" }));
    expect(analysis).toHaveAttribute("data-stage", "result");
    fireEvent.click(screen.getByRole("button", { name: "Replay" }));
    expect(analysis).toHaveAttribute("data-stage", "task");
    expect(analysis).toHaveAttribute("data-playing", "true");

    fireEvent.click(screen.getByRole("button", { name: "How did RC-Gate score this?" }));
    expect(document.querySelector(".katex")).toBeTruthy();
    expect(screen.getByText(/matches the model output/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Sentence to score"), { target: { value: "1" } });
    expect(await screen.findByText("12.00%")).toBeInTheDocument();
    expect(screen.queryByText("53.74%")).not.toBeInTheDocument();

    const llama = screen.getByRole("heading", { name: "Llama-2-70B-chat" }).closest("article");
    expect(llama).toBeTruthy();
    fireEvent.click(within(llama as HTMLElement).getByRole("button", { name: "Inspect this answer" }));
    expect(await screen.findByText(/from the stored Llama-2-70B-chat answer/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Show full response" }));
    expect(screen.getByText(/END-OF-ANSWER/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Change example" }));
    expect(await screen.findByRole("heading", { name: /Search the stored questions/ })).toBeInTheDocument();
  });

  it("navigates to the guide, research, glossary, and dataset inventory", async () => {
    render(<App />);
    await screen.findByRole("heading", { name: /Search the stored questions/ });

    fireEvent.click(screen.getByRole("button", { name: "How RC-Gate works" }));
    const guide = screen.getByRole("article");
    expect(within(guide).getByText(/not a live call/i)).toBeInTheDocument();
    expect(within(guide).queryByRole("textbox")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Research" }));
    expect(screen.getByText(RESEARCH_FIGURES.a0MeanAuroc)).toBeInTheDocument();
    expect(screen.getByText(RESEARCH_FIGURES.a4MeanAuroc)).toBeInTheDocument();
    expect(screen.getByText(RESEARCH_FIGURES.a7MeanAuroc)).toBeInTheDocument();
    expect(screen.getAllByText(new RegExp(RESEARCH_FIGURES.meanA7MinusA4)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(new RegExp(RESEARCH_FIGURES.meanA7MinusA0)).length).toBeGreaterThan(0);
    expect(screen.getByText(/Logistic regression over the six signals/)).toBeInTheDocument();
    expect(screen.getByText(/Gradient boosting over the six signals/)).toBeInTheDocument();
    expect(screen.getByText(/full metadata-conditioned two-expert gate/)).toBeInTheDocument();
    expect(screen.getByText(/not 60 independent datasets/)).toBeInTheDocument();
    expect(screen.getByText(/not a confidence interval/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Final research report" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Experiment index" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Glossary & FAQ" }));
    fireEvent.change(screen.getByLabelText("Search the glossary"), { target: { value: "AUROC" } });
    expect(screen.getByText("AUROC")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Search the glossary"), { target: { value: "zzzz-not-a-term" } });
    expect(screen.getByText(/No glossary entry matches/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Stored demo data" }));
    expect(await screen.findByText(/2,965 source records/)).toBeInTheDocument();
    expect(screen.getByText(/800/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Browse the library" }));
    expect(await screen.findByRole("heading", { name: /Search the stored questions/ })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "RC-Gate" }));
    expect(screen.getByRole("heading", { name: /Search the stored questions/ })).toBeInTheDocument();
  });
});
