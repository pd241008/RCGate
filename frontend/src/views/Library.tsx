import { useEffect, useState } from "react";

import { fetchLibrary } from "../api";
import type { LibraryResponse } from "../studioTypes";

const EMPTY: LibraryResponse["applied"] = {
  q: "",
  task: "",
  topic: "",
  generator: "",
  score: "",
  sort: "auto",
};

export function Library({ onOpen }: { onOpen: (sourceId: string) => void }) {
  const [draft, setDraft] = useState("");
  const [applied, setApplied] = useState(EMPTY);
  const [page, setPage] = useState(1);
  const [data, setData] = useState<LibraryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setApplied((current) => ({ ...current, q: draft }));
      setPage(1);
    }, 250);
    return () => window.clearTimeout(handle);
  }, [draft]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (applied.q) params.set("q", applied.q);
    if (applied.task) params.set("task", applied.task);
    if (applied.topic) params.set("topic", applied.topic);
    if (applied.generator) params.set("generator", applied.generator);
    if (applied.score) params.set("score", applied.score);
    if (applied.sort) params.set("sort", applied.sort);
    params.set("page", String(page));
    params.set("page_size", "20");
    const controller = new AbortController();
    setLoading(true);
    fetchLibrary(params)
      .then((payload) => {
        if (!controller.signal.aborted) {
          setData(payload);
          setError(null);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setError("The local library API is not running.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [applied, page]);

  function update(partial: Partial<typeof EMPTY>) {
    setApplied((current) => ({ ...current, ...partial }));
    setPage(1);
  }

  function clear() {
    setDraft("");
    setApplied(EMPTY);
    setPage(1);
  }

  if (error && !data) {
    return (
      <section className="offline" role="alert">
        <h1>The local question library is not running</h1>
        <p>Start the API on this machine, then refresh. It reads the local RAGTruth files only.</p>
        <pre>python -m rcgate.studio</pre>
        <p>Or start the API and this page together with <code>scripts/dev_studio.sh</code>.</p>
      </section>
    );
  }

  const filtersActive = Boolean(applied.q || applied.task || applied.topic || applied.generator || applied.score);

  return (
    <section className="library" aria-labelledby="library-title">
      <div className="library-top">
        <p className="kicker">Local RAGTruth library</p>
        <h1 id="library-title">Search the stored questions and tasks</h1>
        <p className="lede">
          Every local source is listed. Scores, when they exist, come from a saved checkpoint or from a calculation on this machine. Nothing here calls a live model provider.
        </p>
        <label className="search-label" htmlFor="library-search">
          Search questions, tasks, and answers
        </label>
        <input
          id="library-search"
          className="search-input"
          value={draft}
          placeholder="Search the stored text"
          onChange={(event) => setDraft(event.target.value)}
        />
      </div>
      <aside className="filters" aria-label="Filters">
        <FilterSelect
          label="Task"
          value={applied.task}
          onChange={(value) => update({ task: value })}
          options={data?.facets.tasks ?? []}
        />
        <FilterSelect
          label="Topic"
          value={applied.topic}
          onChange={(value) => update({ topic: value })}
          options={data?.facets.topics ?? []}
        />
        <FilterSelect
          label="Generator"
          value={applied.generator}
          onChange={(value) => update({ generator: value })}
          options={data?.facets.generators ?? []}
        />
        <FilterSelect
          label="Score status"
          value={applied.score}
          onChange={(value) => update({ score: value })}
          options={data?.facets.scores ?? []}
        />
        <label className="filter-label">
          Sort
          <select value={applied.sort} onChange={(event) => update({ sort: event.target.value })}>
            <option value="auto">Relevance when searching, otherwise source order</option>
            <option value="relevance">Relevance</option>
            <option value="task">Task</option>
            <option value="topic">Topic</option>
            <option value="source">Source id</option>
          </select>
        </label>
        <button className="quiet-button" type="button" onClick={clear}>
          Clear all filters
        </button>
        {data && <p className="note">{data.topic_note}</p>}
      </aside>
      <div className="results">
        <div className="result-meta">
          <p>
            {data
              ? `Showing ${data.total.toLocaleString("en-US")} of ${data.inventory_totals.sources.toLocaleString("en-US")} records`
              : "Loading the local library"}
            {loading ? "…" : ""}
          </p>
          {filtersActive && (
            <p className="active-filters">
              Active filters
              {applied.q ? `: “${applied.q}”` : ""}
              {applied.task ? ` · ${applied.task}` : ""}
              {applied.topic ? ` · ${labelOf(data?.facets.topics, applied.topic)}` : ""}
              {applied.generator ? ` · ${labelOf(data?.facets.generators, applied.generator)}` : ""}
              {applied.score ? ` · ${labelOf(data?.facets.scores, applied.score)}` : ""}
            </p>
          )}
        </div>
        {data && data.results.length === 0 && <p>No records match these filters. Clear them to see the full library.</p>}
        <ul className="result-list">
          {data?.results.map((row) => (
            <li key={row.source_id}>
              <button className="result-row" type="button" onClick={() => onOpen(row.source_id)}>
                <span className="card-title">{row.title}</span>
                <span className="result-meta-line">
                  {row.task_label} · {row.dataset_source} · source {row.source_id} · {row.topic_label}
                </span>
                <span className="excerpt">{row.excerpt}</span>
                <span className="result-foot">
                  {row.n_generators} recorded answers
                  {row.excerpt_model_name ? ` · excerpt from ${row.excerpt_model_name}` : ""} · {row.score_label}
                </span>
              </button>
            </li>
          ))}
        </ul>
        {data && data.n_pages > 1 && (
          <div className="pager">
            <button type="button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
              Previous page
            </button>
            <span>
              Page {data.page} of {data.n_pages}
            </span>
            <button type="button" disabled={page >= data.n_pages} onClick={() => setPage((value) => value + 1)}>
              Next page
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { id: string; label: string; count: number }[];
}) {
  return (
    <label className="filter-label">
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">All</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label} ({option.count.toLocaleString("en-US")})
          </option>
        ))}
      </select>
    </label>
  );
}

function labelOf(options: { id: string; label: string }[] | undefined, id: string): string {
  return options?.find((option) => option.id === id)?.label ?? id;
}
