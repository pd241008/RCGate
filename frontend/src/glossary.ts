export interface GlossaryEntry {
  id: string;
  term: string;
  plain: string;
  technical?: string;
}

export const GLOSSARY: GlossaryEntry[] = [
  {
    id: "hallucination",
    term: "Hallucination",
    plain:
      "In this project, a hallucinated sentence is one that overlaps a span human annotators marked as conflicting with the supplied material or as baseless. A model probability is a prediction about that kind of sentence, not a verdict that the words are false in the world.",
    technical:
      "RAGTruth labels are Evident Conflict, Subtle Conflict, Evident Baseless Info, and Subtle Baseless Info. The binary label is 1 when the sentence overlaps any of those spans.",
  },
  {
    id: "claim",
    term: "Claim or sentence",
    plain:
      "The unit RC-Gate scores is one sentence from one recorded answer. The rest of the answer does not receive that probability.",
    technical:
      "Sentences are cut with the repository's offset splitter. Pronouns may be rewritten for the scoring input. The displayed answer text stays the stored response.",
  },
  {
    id: "evidence",
    term: "Evidence or context",
    plain:
      "The context is the material supplied with the original task: passages, an article, or a business record. RC-Gate's evidence signals read that material. It was not fetched after the answer was written.",
  },
  {
    id: "entailment",
    term: "Entailment",
    plain:
      "A text entails a sentence when a separate checker judges that the text supports the sentence. Entailment here is a model score, not a logical proof.",
  },
  {
    id: "contradiction",
    term: "Contradiction",
    plain:
      "A contradiction score says how strongly one text conflicts with a sentence. The cross-model signal keeps the strongest conflict among the other answers, not the average.",
  },
  {
    id: "semantic",
    term: "Semantic difference",
    plain:
      "This signal is high when the sentence is unlike the closest sentences in the other answers, and low when the wording or meaning is close. Closeness is not the same as truth.",
  },
  {
    id: "signal",
    term: "Signal",
    plain:
      "A signal is one number between 0 and 1 computed from the texts. RC-Gate uses six: agreement, contradiction, semantic difference, support, source quality, and conflict.",
    technical:
      "The names in the code are agree, contra, sem_dist, support, src_quality, and conflict. src_quality is constant on the evaluated RAGTruth slice.",
  },
  {
    id: "expert",
    term: "Expert",
    plain:
      "An expert is a small linear scorer. One reads the three cross-model signals. The other reads the three evidence signals. Each produces a logit, which is an unbounded score before it becomes a probability.",
  },
  {
    id: "gate",
    term: "Gating or routing weight",
    plain:
      "The gate looks at the claim type and which model wrote the sentence. It does not look at the signal values. Its two weights scale the expert scores. The weights are visible, and they are not proof that one family is reliable.",
  },
  {
    id: "logit",
    term: "Logit",
    plain:
      "A logit is the score before the final squashing step. Zero is the middle. Positive logits push the hallucination probability above one half. Negative logits push it below.",
  },
  {
    id: "sigmoid",
    term: "Sigmoid",
    plain:
      "The sigmoid turns a logit into a probability between 0 and 1. A logit of zero becomes 0.5.",
  },
  {
    id: "probability",
    term: "Probability versus confidence",
    plain:
      "The number shown is the model's estimated probability that the sentence is hallucinated. It is not a separate confidence rating, and it is not proof. When it sits near 0.5, the classification is close to the threshold.",
  },
  {
    id: "auroc",
    term: "AUROC",
    plain:
      "AUROC summarizes how well a scorer ranks hallucinated sentences above the others across every threshold. 0.5 is no better than chance. It is a property of a whole test set, not of one sentence in this studio.",
  },
  {
    id: "prf",
    term: "Precision, recall, and F1",
    plain:
      "Precision is the share of sentences flagged as hallucinated that really were. Recall is the share of hallucinated sentences that were flagged. F1 combines the two. The studio does not treat one sentence's probability as any of these.",
  },
  {
    id: "calibration",
    term: "Calibration and ECE",
    plain:
      "A calibrated probability matches how often sentences at that probability are actually hallucinated. ECE, expected calibration error, summarizes the mismatch. The Stage 8 reports include it. This studio does not recompute it.",
  },
  {
    id: "benchmark",
    term: "Benchmark",
    plain:
      "A benchmark here is the repeated-fit evaluation on the corrected 800-sentence slice. A probability in the studio is a demo inference on one stored sentence. It is not that benchmark score.",
  },
  {
    id: "ids",
    term: "Source ID, response ID, and claim ID",
    plain:
      "The source ID identifies the task. The response ID identifies one model's stored answer. The claim ID is the response ID plus the sentence index, such as 16406#0 for the first sentence of response 16406.",
  },
  {
    id: "precomputed",
    term: "Precomputed versus locally calculated score",
    plain:
      "A precomputed score uses a row already stored in the corrected signal table, then the saved checkpoint. A local score runs the same extractor on this machine for a sentence that has no stored row. Both are demo inferences. Neither is a new experiment.",
  },
];
