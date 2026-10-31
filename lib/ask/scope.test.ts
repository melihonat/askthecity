import { describe, expect, it } from "vitest";
import { EXAMPLES, formatSnapshotDate, scopeLine } from "./scope";

describe("formatSnapshotDate", () => {
  it("matches the scope sentence's date wording", () => {
    expect(formatSnapshotDate("2026-10-29")).toBe("October 29, 2026");
    expect(formatSnapshotDate("2026-01-01")).toBe("January 1, 2026");
  });
});

describe("scopeLine", () => {
  it("ends with the snapshot date", () => {
    expect(scopeLine("October 29, 2026")).toMatch(/, as of October 29, 2026\.$/);
  });
});

describe("EXAMPLES", () => {
  it("has four chips, exactly one a trick question", () => {
    expect(EXAMPLES).toHaveLength(4);
    expect(EXAMPLES.filter((e) => e.trick)).toHaveLength(1);
  });
});
