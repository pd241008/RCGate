import { useMemo, useState } from "react";

import { GLOSSARY } from "../glossary";

export function Glossary() {
  const [query, setQuery] = useState("");
  const terms = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return GLOSSARY;
    return GLOSSARY.filter((entry) =>
      `${entry.term} ${entry.plain} ${entry.technical ?? ""}`.toLowerCase().includes(needle),
    );
  }, [query]);

  return (
    <article className="prose guide">
      <p className="kicker">Glossary and FAQ</p>
      <h1>Words this studio uses</h1>
      <label className="search-label" htmlFor="glossary-search">
        Search the glossary
      </label>
      <input
        id="glossary-search"
        className="search-input"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      {terms.length === 0 && <p>No glossary entry matches that search.</p>}
      <dl className="glossary">
        {terms.map((entry) => (
          <div key={entry.id} id={entry.id}>
            <dt>{entry.term}</dt>
            <dd>
              <p>{entry.plain}</p>
              {entry.technical && (
                <details>
                  <summary>Technical note</summary>
                  <p>{entry.technical}</p>
                </details>
              )}
            </dd>
          </div>
        ))}
      </dl>
    </article>
  );
}
