import { expertLogit, fusedLogit, sigmoid } from "./fusion";
import type { ScoreResult } from "./studioTypes";

export interface WorkedCheck {
  zCross: number;
  zEvid: number;
  logit: number;
  prob: number;
  matchesModel: boolean;
}

/** Recompute the linear expert and fusion steps from the values the scorer returned. */
export function verifyWorked(score: ScoreResult): WorkedCheck | null {
  if (!score.prediction || !score.experts || !score.worked) {
    return null;
  }
  const values = score.worked.signal_values;
  if (!values || values.length !== 6) {
    return null;
  }
  const zCross = expertLogit(score.experts.cross.weights, score.experts.cross.bias, values.slice(0, 3));
  const zEvid = expertLogit(score.experts.evidence.weights, score.experts.evidence.bias, values.slice(3));
  const logit = fusedLogit(
    score.experts.fusion.weights,
    score.experts.fusion.bias,
    score.prediction.w_cross,
    zCross,
    score.prediction.w_evid,
    zEvid,
  );
  const prob = sigmoid(logit);
  const tolerance = score.worked.tolerance;
  const matchesModel =
    Math.abs(zCross - score.prediction.z_cross) <= tolerance &&
    Math.abs(zEvid - score.prediction.z_evid) <= tolerance &&
    Math.abs(logit - score.prediction.logit) <= tolerance &&
    Math.abs(prob - score.prediction.prob) <= tolerance;
  return { zCross, zEvid, logit, prob, matchesModel };
}
