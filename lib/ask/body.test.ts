import { describe, expect, it } from "vitest";
import { parseBody } from "./body";

describe("parseBody", () => {
  it("splits paragraphs and parses a pipe table between them", () => {
    const body = [
      "A. No person shall discharge water that exceeds the limits in Table 1:",
      "| Parameter | Limit (mg/L) |\n| --- | --- |\n| Arsenic | 1.0 |\n| Cadmium5 | 0.7 |",
      "B. Subsection A does not apply to storm water.",
    ].join("\n\n");

    expect(parseBody(body)).toEqual([
      { kind: "text", text: "A. No person shall discharge water that exceeds the limits in Table 1:" },
      { kind: "table", header: ["Parameter", "Limit (mg/L)"], rows: [["Arsenic", "1.0"], ["Cadmium5", "0.7"]] },
      { kind: "text", text: "B. Subsection A does not apply to storm water." },
    ]);
  });

  it("keeps escaped pipes inside a cell and empty cells", () => {
    const [table] = parseBody("| a | b |\n| --- | --- |\n| x \\| y |  |");
    expect(table).toEqual({ kind: "table", header: ["a", "b"], rows: [["x | y", ""]] });
  });

  it("leaves text with a stray pipe and list-like lines as text", () => {
    expect(parseBody("1. First\n2. Second")).toEqual([{ kind: "text", text: "1. First\n2. Second" }]);
    expect(parseBody("| not a table")).toEqual([{ kind: "text", text: "| not a table" }]);
  });
});
