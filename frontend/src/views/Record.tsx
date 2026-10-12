import { useEffect, useReducer, useState } from "react";

import { fetchJob, fetchRecord, postScore } from "../api";
import { PLAYBACK_LABEL } from "../researchFigures";
import { STAGE_MS, STAGES, initialPlayback, playbackReducer, stageId } from "../playback";
import type { RecordDetail, ScoreResult, StoredResponse } from "../studioTypes";
import { ScorePanel } from "./ScorePanel";

export function RecordView({
  sourceId,
  reducedMotion,
  onChangeExample,
}: {
  sourceId: string;
  reducedMotion: boolean;
  onChangeExample: () => void;
}) {
  const [record, setRecord] = useState<RecordDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [responseId, setResponseId] = useState("");
  const [sentenceIndex, setSentenceIndex] = useState(0);
  const [score, setScore] = useState<ScoreResult | null>(null);
  const [pending, setPending] = useState<string | null>(null);
  const [started, setStarted] = useState(false);
  const [playback, dispatch] = useReducer(playbackReducer, initialPlayback(false));
  const current = stageId(playback.stage);

  useEffect(() => {
    const controller = new AbortController();
    setRecord(null);
    setScore(null);
    setError(null);
    fetchRecord(sourceId)
      .then((payload) => {
        if (controller.signal.aborted) return;
        setRecord(payload);
        setResponseId(payload.scoring.default_response_id);
        setSentenceIndex(payload.scoring.default_sentence_index);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError("This record could not be loaded from the local API.");
      });
    return () => controller.abort();
  }, [sourceId]);

  useEffect(() => {
    if (!record || !responseId) return undefined;
    const controller = new AbortController();
    setScore(null);
    setPending("Checking stored features for this sentence");
    void runScore(sourceId, responseId, sentenceIndex, controller.signal, setPending, setScore);
    return () => controller.abort();
  }, [record, responseId, sentenceIndex, sourceId]);

  useEffect(() => {
    if (!playback.playing) return undefined;
    const timer = window.setTimeout(() => dispatch({ type: "tick" }), STAGE_MS);
    return () => window.clearTimeout(timer);
  }, [playback.playing, playback.stage]);

  useEffect(() => {
    const node = document.getElementById(`stage-${current}`);
    if (!node || typeof node.scrollIntoView !== "function") return;
    if (!started) return;
    node.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
  }, [current, reducedMotion, started]);

  if (error) {
    return (
      <section role="alert">
        <p>{error}</p>
        <button type="button" onClick={onChangeExample}>
          Change example
        </button>
      </section>
    );
  }
  if (!record) {
    return <p role="status">Loading the stored record…</p>;
  }

  const selected = record.responses.find((item) => item.response_id === responseId) ?? record.responses[0];
  const sentence = selected?.sentences.find((item) => item.index === sentenceIndex) ?? selected?.sentences[0];
  const last = STAGES.length - 1;
  const showPlay = !playback.playing && !started && playback.stage === 0;
  const showContinue = !playback.playing && !showPlay && playback.stage < last;

  function begin() {
    setStarted(true);
    dispatch({ type: "resume" });
  }

  return (
    <section
      className="analysis"
      aria-label={`${record.topic_label} analysis`}
      data-stage={current}
      data-playing={playback.playing ? "true" : "false"}
    >
      <div className="playback">
        <p className="playback-label">{PLAYBACK_LABEL}</p>
        <p className="note">Optional walkthrough. Nothing is narrated, and no live model is being queried.</p>
        <div className="progress-line" aria-hidden="true">
          <span style={{ width: `${((playback.stage + 1) / STAGES.length) * 100}%` }} />
        </div>
        <div className="stage-nav" role="group" aria-label="Walkthrough stages">
          {STAGES.map((stage, index) => (
            <button
              key={stage.id}
              type="button"
              aria-current={index === playback.stage ? "step" : undefined}
              onClick={() => {
                setStarted(true);
                dispatch({ type: "goto", stage: index });
              }}
            >
              {stage.label}
            </button>
          ))}
        </div>
        <div className="playback-actions">
          {playback.playing && (
            <button type="button" onClick={() => dispatch({ type: "pause" })}>
              Pause
            </button>
          )}
          {showPlay && (
            <button type="button" onClick={begin}>
              Play walkthrough
            </button>
          )}
          {showContinue && (
            <button type="button" onClick={begin}>
              Continue
            </button>
          )}
          <button
            type="button"
            onClick={() => {
              setStarted(true);
              dispatch({ type: "goto", stage: playback.stage - 1 });
            }}
            disabled={playback.stage === 0}
          >
            Previous
          </button>
          <button
            type="button"
            onClick={() => {
              setStarted(true);
              dispatch({ type: "goto", stage: playback.stage + 1 });
            }}
            disabled={playback.stage >= last}
          >
            Next
          </button>
          <button
            type="button"
            onClick={() => {
              setStarted(true);
              dispatch({ type: "skip" });
            }}
          >
            Skip to result
          </button>
          <button
            type="button"
            onClick={() => {
              setStarted(true);
              dispatch({ type: "replay", autoplay: true });
            }}
          >
            Replay
          </button>
          <button type="button" onClick={onChangeExample}>
            Change example
          </button>
        </div>
      </div>

      <section className={panelClass("task", current)} id="stage-task">
        <p className="stage-kicker">{record.task_label}</p>
        <h1 className="task-title">{record.task.question ?? record.title}</h1>
        <p>{record.task.instruction}</p>
        <p className="result-meta-line">
          {record.dataset_source} · source {record.source_id} · {record.topic_label}
        </p>
        {record.task.kind !== "qa" && (
          <p className="note">This record is a {record.task_label} task. It is not a question-answering item.</p>
        )}
        <details>
          <summary>Stored prompt and dataset fields</summary>
          <p>{record.task.prompt_note}</p>
          <pre className="prompt-block">{record.task.prompt}</pre>
        </details>
      </section>

      <section className={panelClass("context", current)} id="stage-context">
        <p className="stage-kicker">Passages provided with the question</p>
        <h2>{record.task.kind === "qa" ? "Context provided to the models" : "Source material provided with the task"}</h2>
        <p>{record.task.context_note}</p>
        {record.structured && <BusinessCard structured={record.structured} />}
        {record.passages.map((passage) => (
          <article className="passage" key={passage.id}>
            <h3>{passage.title}</h3>
            <p className="passage-kind">Original task input · used when RC-Gate calculates evidence signals</p>
            <p className="passage-text">{passage.text}</p>
          </article>
        ))}
      </section>

      <section className={panelClass("responses", current)} id="stage-responses">
        <p className="stage-kicker">Recorded answers</p>
        <h2>Answers stored for this source</h2>
        <p className="note">These six identities are the models in the local RAGTruth roster. The text is the stored response.</p>
        <div className="response-grid">
          {record.responses.map((response) => (
            <AnswerCard
              key={response.response_id}
              response={response}
              selected={response.response_id === selected?.response_id}
              sentenceIndex={response.response_id === selected?.response_id ? sentenceIndex : 0}
              onSelect={() => {
                setResponseId(response.response_id);
                setSentenceIndex(0);
              }}
            />
          ))}
        </div>
      </section>

      <section className={panelClass("crosscheck", current)} id="stage-crosscheck">
        <p className="stage-kicker">Selected sentence</p>
        <h2>Claim selected for scoring</h2>
        {selected && (
          <label className="filter-label">
            Sentence to score
            <select
              value={sentenceIndex}
              onChange={(event) => setSentenceIndex(Number(event.target.value))}
            >
              {selected.sentences.map((item) => (
                <option key={item.claim_id} value={item.index}>
                  Sentence {item.index + 1}
                  {item.score_status === "precomputed" ? " · stored features" : item.score_status === "local" ? " · needs local scoring" : " · scoring unavailable"}
                  {`: ${clip(item.text, 80)}`}
                </option>
              ))}
            </select>
          </label>
        )}
        {sentence && (
          <>
            <p className="highlight">{sentence.text}</p>
            <p>
              The score belongs only to this sentence from {selected?.model_name}. The other sentences in the answer were not given this probability.
            </p>
            <p className="note">
              Claim {sentence.claim_id}. Scoring status: {sentence.score_status}.
              {sentence.dealias_changed ? ` Scoring input: ${sentence.scoring_text}` : ""}
            </p>
          </>
        )}
      </section>

      <div className={panelClass("result", current)}>
        <ScorePanel score={score} pending={pending} />
      </div>

      <section className="references" aria-label="Independent references">
        <p className="stage-kicker">Independent references for your own verification</p>
        <h2>Separate from the supplied context</h2>
        <p>{record.independent_reference_note}</p>
        {record.independent_references.map((reference) => (
          <article className="reference-card" key={reference.id}>
            <h3>{reference.title}</h3>
            <p>
              {reference.publisher}
              {reference.verified_on ? ` · verified ${reference.verified_on}` : ""}
            </p>
            <p>{reference.excerpt}</p>
            <p className="note">{reference.relevance}</p>
            <p className="note">used_in_rcgate_score: {String(reference.used_in_rcgate_score)}. This page is not an RC-Gate feature.</p>
            <a href={reference.url} target="_blank" rel="noreferrer">
              {reference.url}
            </a>
          </article>
        ))}
      </section>
    </section>
  );
}

function AnswerCard({
  response,
  selected,
  sentenceIndex,
  onSelect,
}: {
  response: StoredResponse;
  selected: boolean;
  sentenceIndex: number;
  onSelect: () => void;
}) {
  const [full, setFull] = useState(false);
  const sentence = response.sentences.find((item) => item.index === sentenceIndex) ?? response.sentences[0];
  const long = response.text.length > 700;
  return (
    <article className="answer-card" data-selected={selected ? "true" : "false"}>
      <h3>{response.model_name}</h3>
      <p className="note">
        {response.provenance}
        {response.quality ? ` · quality ${response.quality}` : ""}
        {response.dataset_split ? ` · dataset split ${response.dataset_split}` : ""}
      </p>
      {selected && sentence ? <Highlighted text={response.text} start={sentence.start} end={sentence.end} full={full || !long} /> : <p className="answer-body">{full || !long ? response.text : `${response.text.slice(0, 700)}…`}</p>}
      {long && (
        <button type="button" onClick={() => setFull((value) => !value)}>
          {full ? "Show less" : "Show full response"}
        </button>
      )}
      <button type="button" onClick={onSelect} aria-pressed={selected}>
        {selected ? "Inspecting this answer" : "Inspect this answer"}
      </button>
    </article>
  );
}

function Highlighted({ text, start, end, full }: { text: string; start: number; end: number; full: boolean }) {
  const shown = full ? text : text.slice(0, Math.max(700, end));
  const safeEnd = Math.min(end, shown.length);
  const safeStart = Math.min(start, safeEnd);
  return (
    <p className="answer-body">
      {shown.slice(0, safeStart)}
      <mark>{shown.slice(safeStart, safeEnd)}</mark>
      {shown.slice(safeEnd)}
      {!full && text.length > shown.length ? "…" : ""}
    </p>
  );
}

function BusinessCard({
  structured,
}: {
  structured: NonNullable<RecordDetail["structured"]>;
}) {
  const hours = structured.hours && typeof structured.hours === "object" ? structured.hours : null;
  return (
    <div className="business">
      <p>
        <strong>{structured.name}</strong>
        {structured.city ? ` · ${structured.city}` : ""}
        {structured.state ? `, ${structured.state}` : ""}
      </p>
      {structured.address && <p>{structured.address}</p>}
      {structured.categories && <p>{structured.categories}</p>}
      {structured.stars != null && <p>Business stars: {structured.stars}</p>}
      {hours && (
        <ul>
          {Object.entries(hours).map(([day, value]) => (
            <li key={day}>
              {day}: {value}
            </li>
          ))}
        </ul>
      )}
      {structured.reviews?.map((review, index) => (
        <blockquote key={`${review.date ?? "review"}-${index}`}>
          {review.text}
          {review.stars != null ? ` (${review.stars} stars)` : ""}
        </blockquote>
      ))}
    </div>
  );
}

function panelClass(id: string, current: string): string {
  return id === current ? "panel is-current" : "panel";
}

function clip(text: string, limit: number): string {
  const compact = text.replace(/\s+/g, " ").trim();
  return compact.length <= limit ? compact : `${compact.slice(0, limit - 1)}…`;
}

async function runScore(
  sourceId: string,
  responseId: string,
  sentenceIndex: number,
  signal: AbortSignal,
  setPending: (message: string | null) => void,
  setScore: (score: ScoreResult | null) => void,
) {
  try {
    let envelope = await postScore(sourceId, responseId, sentenceIndex);
    while (!signal.aborted && envelope.status === "running" && envelope.job_id) {
      setPending(envelope.message || "Calculating signals on this machine");
      await delay(400);
      if (signal.aborted) return;
      envelope = await fetchJob(envelope.job_id);
    }
    if (signal.aborted) return;
    setPending(null);
    setScore(envelope.result);
  } catch {
    if (!signal.aborted) {
      setPending(null);
      setScore({
        status: "error",
        reason: "The local scoring request failed.",
        feature_source: null,
        demo_inference: true,
        benchmark_evaluation: false,
        partition: null,
        partition_note: null,
        checkpoint: null,
        claim: null,
        prediction: null,
        experts: null,
        worked: null,
        cache_path: null,
        notes: [],
      });
    }
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}
