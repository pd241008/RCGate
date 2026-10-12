/** Stage 8 figures from the final research report. They are not demo-claim scores. */
export const RESEARCH_FIGURES = {
  a0MeanAuroc: "0.6280",
  a4MeanAuroc: "0.6839",
  a7MeanAuroc: "0.5717",
  meanA7MinusA4: "−0.1122",
  meanA7MinusA0: "−0.0563",
  nSentences: 800,
  nQuestions: 134,
  nGroupSplits: 20,
  nModelInitialisations: 3,
  nHallucinated: 57,
  a7SampleSd: "0.1247",
  reportPath: "docs/RC-Gate_Final_Research_Report_v1.md",
  indexPath: "docs/RC-Gate_Experiment_Index.md",
} as const;

export const BASELINES = [
  {
    id: "A0",
    name: "Logistic regression over the six signals",
    figure: RESEARCH_FIGURES.a0MeanAuroc,
  },
  {
    id: "A4",
    name: "Gradient boosting over the six signals plus claim-type and generator metadata",
    figure: RESEARCH_FIGURES.a4MeanAuroc,
  },
  {
    id: "A7",
    name: "RC-Gate's full metadata-conditioned two-expert gate",
    figure: RESEARCH_FIGURES.a7MeanAuroc,
  },
] as const;

export const PLAYBACK_LABEL = "Recorded demo · stored RAGTruth responses";

export const EMPTY_REFERENCE_NOTE =
  "No independent reference is attached to this item yet. The score uses the supplied task context and the existing RC-Gate features; it does not include a separately retrieved reference.";

export const QA_CONTEXT_NOTE =
  "These are the passages supplied to the original models. RC-Gate also uses this context when calculating its evidence signals.";
