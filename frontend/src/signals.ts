import type { SignalName } from "./types";

export interface CheckSpec {
  key: Exclude<SignalName, "src_quality">;
  label: string;
  plain: string;
  high: string;
  low: string;
  cannot: string;
  family: "Cross-model" | "Evidence";
}

export const CHECKS: CheckSpec[] = [
  {
    key: "agree",
    label: "Agreement across models",
    plain: "Share of the other recorded answers whose text entails this sentence.",
    high: "A high value means more of the other answers entail the sentence.",
    low: "A low value means little entailment was found. The answers may still be about the same topic.",
    cannot: "Agreement alone cannot prove the sentence is true.",
    family: "Cross-model",
  },
  {
    key: "contra",
    label: "Contradiction between model answers",
    plain: "The strongest contradiction between this sentence and any other recorded answer. This is a maximum, not an average.",
    high: "A high value means at least one other answer strongly contradicts the sentence.",
    low: "A low value means no strong contradiction was detected in the other answers.",
    cannot: "A low value cannot prove the answers are reliable, and a high value cannot by itself prove the sentence is false.",
    family: "Cross-model",
  },
  {
    key: "sem_dist",
    label: "Difference in wording or meaning",
    plain: "How far this sentence sits from the other answers: one minus the average similarity to each other answer’s closest sentence.",
    high: "A high value means the wording or meaning is far from the other answers.",
    low: "A low value means the sentence is close to something another answer said.",
    cannot: "Closeness is not evidence that the shared wording is supported by the source.",
    family: "Cross-model",
  },
  {
    key: "support",
    label: "Support from the provided passages",
    plain: "The strongest entailment of this sentence by sentences taken from the context that was supplied with the task.",
    high: "A high value means the supplied material entails the sentence.",
    low: "A low value means that entailment was weak or missing in the sentences the extractor checked.",
    cannot: "This is not a search of the open web, and it cannot prove the sentence is true outside that supplied material.",
    family: "Evidence",
  },
  {
    key: "conflict",
    label: "Conflict with the provided passages",
    plain: "The strongest contradiction between this sentence and sentences taken from the supplied context.",
    high: "A high value means the supplied material contradicts the sentence.",
    low: "A low value means no strong contradiction was found in the sentences that were checked.",
    cannot: "A low value does not mean the supplied material confirms the sentence.",
    family: "Evidence",
  },
];

export const SOURCE_QUALITY_NOTE =
  "src_quality records where the evidence came from. On this RAGTruth setup it is 0.9 whenever the evidence is the supplied task context. It is constant on the evaluated slice, so it does not compare one example with another.";
