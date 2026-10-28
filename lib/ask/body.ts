// A chunk body is plain paragraphs separated by blank lines, plus markdown pipe tables
// (CHUNKING.md, rule 6). Only tables are parsed: Code text is full of "1." and "*" that a
// general markdown renderer would turn into lists and emphasis.

export type BodyBlock = { kind: "text"; text: string } | { kind: "table"; header: string[]; rows: string[][] };

const SEPARATOR = /^\|(?:\s*:?-{3,}:?\s*\|)+$/;

function cells(line: string): string[] {
  return line
    .trim()
    .replace(/^\||\|$/g, "")
    .split(/(?<!\\)\|/)
    .map((c) => c.trim().replace(/\\\|/g, "|"));
}

export function parseBody(body: string): BodyBlock[] {
  return body
    .split(/\n{2,}/)
    .filter((p) => p.trim())
    .map((p): BodyBlock => {
      const lines = p.split("\n");
      if (lines.length >= 2 && lines.every((l) => l.trim().startsWith("|")) && SEPARATOR.test(lines[1].trim())) {
        return { kind: "table", header: cells(lines[0]), rows: lines.slice(2).map(cells) };
      }
      return { kind: "text", text: p };
    });
}
