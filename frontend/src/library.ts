import raw from "../../demo_fixtures/scenarios.json";

import type { Library, Scenario } from "./types";

export const library = raw as Library;

export function scenarioById(id: string): Scenario {
  const found = library.scenarios.find((item) => item.id === id);
  if (!found) {
    throw new Error(`unknown scenario ${id}`);
  }
  return found;
}
