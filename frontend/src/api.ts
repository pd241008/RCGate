import type { HealthResponse, LibraryResponse, RecordDetail, ScoreEnvelope } from "./studioTypes";

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function fetchHealth(): Promise<HealthResponse> {
  return fetch("/api/health").then((response) => readJson<HealthResponse>(response));
}

export function fetchLibrary(params: URLSearchParams): Promise<LibraryResponse> {
  const query = params.toString();
  return fetch(query ? `/api/library?${query}` : "/api/library").then((response) =>
    readJson<LibraryResponse>(response),
  );
}

export function fetchRecord(sourceId: string): Promise<RecordDetail> {
  return fetch(`/api/library/${encodeURIComponent(sourceId)}`).then((response) =>
    readJson<RecordDetail>(response),
  );
}

export function postScore(
  sourceId: string,
  responseId: string,
  sentenceIndex: number,
): Promise<ScoreEnvelope> {
  return fetch("/api/score", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_id: sourceId, response_id: responseId, sentence_index: sentenceIndex }),
  }).then((response) => readJson<ScoreEnvelope>(response));
}

export function fetchJob(jobId: string): Promise<ScoreEnvelope> {
  return fetch(`/api/jobs/${encodeURIComponent(jobId)}`).then((response) =>
    readJson<ScoreEnvelope>(response),
  );
}
