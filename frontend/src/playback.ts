export const STAGES = [
  { id: "task", label: "Task" },
  { id: "context", label: "Provided context" },
  { id: "responses", label: "Recorded answers" },
  { id: "crosscheck", label: "Cross-check" },
  { id: "result", label: "RC-Gate result" },
] as const;

export type StageId = (typeof STAGES)[number]["id"];

/** Four pauses from the task to the result: 22 seconds for a full replay. */
export const STAGE_MS = 5500;

export interface PlaybackState {
  stage: number;
  playing: boolean;
}

export type PlaybackAction =
  | { type: "tick" }
  | { type: "pause" }
  | { type: "resume" }
  | { type: "skip" }
  | { type: "replay"; autoplay: boolean }
  | { type: "goto"; stage: number };

export function initialPlayback(autoplay = false): PlaybackState {
  return { stage: 0, playing: autoplay };
}

export function playbackReducer(state: PlaybackState, action: PlaybackAction): PlaybackState {
  const last = STAGES.length - 1;
  switch (action.type) {
    case "tick":
      if (!state.playing || state.stage >= last) {
        return state;
      }
      return { ...state, stage: state.stage + 1, playing: state.stage + 1 < last };
    case "pause":
      return { ...state, playing: false };
    case "resume":
      if (state.stage >= last) {
        return { ...state, playing: false };
      }
      return { ...state, playing: true };
    case "skip":
      return { stage: last, playing: false };
    case "replay":
      return { stage: 0, playing: action.autoplay };
    case "goto":
      return { stage: clampStage(action.stage), playing: false };
    default:
      return state;
  }
}

function clampStage(stage: number): number {
  if (stage < 0) {
    return 0;
  }
  if (stage > STAGES.length - 1) {
    return STAGES.length - 1;
  }
  return stage;
}

export function stageId(index: number): StageId {
  return STAGES[clampStage(index)].id;
}
