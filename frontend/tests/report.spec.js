import { describe, expect, it } from "vitest";

import { buildSectionCards } from "../src/utils/report";

describe("buildSectionCards", () => {
  it("normalizes report sections for display", () => {
    const cards = buildSectionCards({
      overview: { title: "Demo", summary: "Simple summary" },
      tech_stack: { languages: ["Python"], frameworks: ["FastAPI"] },
      reading_guide: { difficulty: "beginner", steps: ["A", "B"] },
    });

    expect(cards[0].title).toBe("项目概述");
    expect(cards[0].content).toContain("Simple summary");
    expect(cards[1].content).toContain("Python");
    expect(cards[2].content).toContain("beginner");
  });
});
