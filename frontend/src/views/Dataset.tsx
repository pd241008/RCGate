import { useEffect, useState } from "react";

import { fetchHealth } from "../api";
import type { HealthResponse } from "../studioTypes";

export function Dataset({ onBrowse }: { onBrowse: () => void }) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() => setError(true));
  }, []);

  if (error) {
    return (
      <section className="offline" role="alert">
        <h1>Stored demo data</h1>
        <p>The inventory is read from the local files by the API. Start it, then refresh.</p>
        <pre>python -m rcgate.studio</pre>
      </section>
    );
  }
  if (!health) {
    return <p role="status">Reading the local dataset inventory…</p>;
  }
  const inventory = health.inventory;
  return (
    <article className="prose guide">
      <p className="kicker">Stored demo data</p>
      <h1>What is on this machine</h1>
      <p>
        {inventory.citation} Licence: {inventory.license}. The studio does not call a provider. Live provider calls: {String(health.live_provider_calls)}.
      </p>
      <p>
        {inventory.n_sources.toLocaleString("en-US")} source records and {inventory.n_responses.toLocaleString("en-US")} responses. File hashes match the pinned RAGTruth bytes: {String(health.ok)}.
      </p>
      <ul>
        {Object.entries(inventory.tasks).map(([task, count]) => (
          <li key={task}>
            {task}: {count.toLocaleString("en-US")}
          </li>
        ))}
      </ul>
      <h2>What can be browsed, and what can be scored</h2>
      {inventory.distinctions.map((item) => (
        <section key={item.id}>
          <h3>{item.title}</h3>
          <p>{item.detail}</p>
        </section>
      ))}
      <p>
        Signal table {inventory.signal_table.path}: {inventory.signal_table.n_claims} {inventory.signal_table.claim_scope.replace("_", " ")} claims across {inventory.signal_table.n_sources} sources. {inventory.signal_table.note}
      </p>
      {inventory.signal_table.partial_sources.length > 0 && (
        <p>
          Sources with fewer than six stored feature rows:{" "}
          {inventory.signal_table.partial_sources.map((item) => `${item.source_id} (${item.n_claims})`).join(", ")}.
        </p>
      )}
      <p>
        Checkpoint {inventory.scoring.checkpoint_path}. Local extraction ready: {String(inventory.scoring.local_extraction_ready)}.
      </p>
      <p>{inventory.topic_note}</p>
      <button className="pill" type="button" onClick={onBrowse}>
        Browse the library
      </button>
    </article>
  );
}
