import { describe, expect, it } from "vitest";
import { segments } from "./markers";

describe("segments", () => {
  it("splits markers out of the prose, dropping the space before each", () => {
    expect(segments("Until 7 p.m. [3]. Weekends differ [1][2].")).toEqual([
      { kind: "text", text: "Until 7 p.m." },
      { kind: "marker", n: 3 },
      { kind: "text", text: ". Weekends differ" },
      { kind: "marker", n: 1 },
      { kind: "marker", n: 2 },
      { kind: "text", text: "." },
    ]);
  });

  it("keeps text without markers whole", () => {
    expect(segments("No.")).toEqual([{ kind: "text", text: "No." }]);
  });

  it("ends on a trailing marker", () => {
    expect(segments("Until 7 p.m. [3]")).toEqual([
      { kind: "text", text: "Until 7 p.m." },
      { kind: "marker", n: 3 },
    ]);
  });
});
