import { describe, expect, it } from "vitest";

import { STAGE_MS, STAGES, initialPlayback, playbackReducer } from "./playback";

describe("playback controls", () => {
  it("advances until the result and then stops", () => {
    let state = initialPlayback(true);
    for (let step = 0; step < STAGES.length; step += 1) {
      state = playbackReducer(state, { type: "tick" });
    }
    expect(state.stage).toBe(STAGES.length - 1);
    expect(state.playing).toBe(false);
    expect(playbackReducer(state, { type: "tick" })).toEqual(state);
  });

  it("pauses, resumes, skips, replays, and jumps without carrying play state", () => {
    const started = initialPlayback(true);
    const paused = playbackReducer(started, { type: "pause" });
    expect(paused.playing).toBe(false);
    expect(playbackReducer(paused, { type: "tick" }).stage).toBe(0);

    const resumed = playbackReducer(paused, { type: "resume" });
    expect(resumed.playing).toBe(true);
    expect(playbackReducer(resumed, { type: "tick" }).stage).toBe(1);

    const skipped = playbackReducer(started, { type: "skip" });
    expect(skipped).toEqual({ stage: STAGES.length - 1, playing: false });

    const replay = playbackReducer(skipped, { type: "replay", autoplay: true });
    expect(replay).toEqual({ stage: 0, playing: true });

    const jumped = playbackReducer(replay, { type: "goto", stage: 2 });
    expect(jumped).toEqual({ stage: 2, playing: false });
  });

  it("does not autoplay until the reader starts it", () => {
    expect(initialPlayback().playing).toBe(false);
    expect(initialPlayback(false).playing).toBe(false);
  });

  it("keeps a full replay inside a 20 to 25 second window", () => {
    const duration = (STAGES.length - 1) * STAGE_MS;
    expect(duration).toBeGreaterThanOrEqual(20_000);
    expect(duration).toBeLessThanOrEqual(25_000);
  });
});
