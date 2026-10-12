import { describe, expect, it } from "vitest";

import { fusedLogit, sigmoid } from "./fusion";
import { library } from "./library";

describe("recorded fusion", () => {
  it("reproduces each stored probability from that scenario's logits and weights", () => {
    for (const scenario of library.scenarios) {
      const prediction = scenario.prediction;
      const logit = fusedLogit(
        library.experts.fusion.weights,
        library.experts.fusion.bias,
        prediction.w_cross,
        prediction.z_cross,
        prediction.w_evid,
        prediction.z_evid,
      );
      expect(Math.abs(sigmoid(logit) - prediction.prob)).toBeLessThan(0.005);
      expect(prediction.claim_id).toBe(scenario.scored_claim_id);
    }
  });
});
