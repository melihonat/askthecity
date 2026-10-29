import { describe, expect, it } from "vitest";
import { splitGap } from "./gap";

describe("splitGap", () => {
  it("splits off the uncited final sentence", () => {
    expect(splitGap("Power devices stop at 7 p.m. [3]. The documents don't set fines for this.")).toEqual({
      body: "Power devices stop at 7 p.m. [3].",
      gap: "The documents don't set fines for this.",
    });
  });

  it("has no gap when the last sentence is cited", () => {
    const text = "No. Power devices stop at 7 p.m. [3]. Weekends differ [1][2].";
    expect(splitGap(text)).toEqual({ body: text, gap: null });
  });

  it("takes only the last of several trailing uncited sentences", () => {
    expect(splitGap("Until 7 p.m. [3]. Parks are separate. Fines aren't covered.")).toEqual({
      body: "Until 7 p.m. [3]. Parks are separate.",
      gap: "Fines aren't covered.",
    });
  });

  it("handles a marker placed after the period", () => {
    expect(splitGap("Until 7 p.m. [3] The snapshot doesn't cover Sundays.").gap).toBe(
      "The snapshot doesn't cover Sundays.",
    );
  });

  it("has no gap without any marker", () => {
    expect(splitGap("Nothing cited.")).toEqual({ body: "Nothing cited.", gap: null });
  });
});
