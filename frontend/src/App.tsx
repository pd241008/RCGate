import { useState } from "react";

import { useReducedMotion } from "./motion";
import { Dataset } from "./views/Dataset";
import { Glossary } from "./views/Glossary";
import { HowItWorks } from "./views/HowItWorks";
import { Library } from "./views/Library";
import { RecordView } from "./views/Record";
import { Research } from "./views/Research";

type View = "library" | "record" | "how" | "research" | "glossary" | "dataset";

export function App() {
  const reducedMotion = useReducedMotion();
  const [view, setView] = useState<View>("library");
  const [sourceId, setSourceId] = useState<string | null>(null);

  function openRecord(id: string) {
    setSourceId(id);
    setView("record");
  }

  function goLibrary() {
    setView("library");
    setSourceId(null);
  }

  return (
    <div className="shell" data-reduced-motion={reducedMotion ? "true" : "false"}>
      <header className="header">
        <div className="header-inner">
          <button className="wordmark" type="button" onClick={goLibrary}>
            RC-Gate
          </button>
          <nav className="nav" aria-label="Primary">
            <NavButton current={view === "how"} onClick={() => setView("how")}>
              How RC-Gate works
            </NavButton>
            <NavButton current={view === "research"} onClick={() => setView("research")}>
              Research
            </NavButton>
            <NavButton current={view === "glossary"} onClick={() => setView("glossary")}>
              Glossary & FAQ
            </NavButton>
            <NavButton current={view === "dataset"} onClick={() => setView("dataset")}>
              Stored demo data
            </NavButton>
          </nav>
        </div>
      </header>
      <main className="page">
        {view === "library" && <Library onOpen={openRecord} />}
        {view === "how" && <HowItWorks />}
        {view === "research" && <Research />}
        {view === "glossary" && <Glossary />}
        {view === "dataset" && <Dataset onBrowse={goLibrary} />}
        {view === "record" && sourceId && (
          <RecordView
            key={sourceId}
            sourceId={sourceId}
            reducedMotion={reducedMotion}
            onChangeExample={goLibrary}
          />
        )}
      </main>
    </div>
  );
}

function NavButton({
  current,
  onClick,
  children,
}: {
  current: boolean;
  onClick: () => void;
  children: string;
}) {
  return (
    <button className="nav-link" type="button" aria-current={current ? "page" : undefined} onClick={onClick}>
      {children}
    </button>
  );
}
