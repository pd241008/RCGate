import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const css = readFileSync(join(process.cwd(), "src/styles.css"), "utf8");

describe("layout and motion", () => {
  it("stacks the response grid on a phone-width viewport", () => {
    expect(css).toContain(".response-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }");
    expect(css).toContain("@media (max-width: 720px)");
    expect(css).toMatch(/@media \(max-width: 720px\)[\s\S]*\.response-grid \{ grid-template-columns: 1fr; \}/);
  });

  it("turns animation off when reduced motion is requested", () => {
    expect(css).toContain("@media (prefers-reduced-motion: reduce)");
    expect(css).toContain("animation: none !important");
  });
});
