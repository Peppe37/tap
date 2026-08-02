import { describe, expect, it } from "vitest";

import { formatRelativeTime } from "@/lib/format";

describe("formatRelativeTime", () => {
  it("describes a moment a few minutes in the past", () => {
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();

    expect(formatRelativeTime(fiveMinutesAgo)).toMatch(/5 minuti fa/);
  });

  it("describes a moment a few hours in the future", () => {
    const inThreeHours = new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString();

    expect(formatRelativeTime(inThreeHours)).toMatch(/tra 3 ore/);
  });
});
