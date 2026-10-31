// Splits answer text into prose and its [n] markers, so the UI can render each marker as a tag
// that points at its passage card. Markers are already validated (CONTRACT.md, "Citation").

export type Segment = { kind: "text"; text: string } | { kind: "marker"; n: number };

const MARKER = /\s*\[(\d+)\]/g;

export function segments(text: string): Segment[] {
  const out: Segment[] = [];
  let at = 0;
  for (const m of text.matchAll(MARKER)) {
    if (m.index > at) out.push({ kind: "text", text: text.slice(at, m.index) });
    out.push({ kind: "marker", n: Number(m[1]) });
    at = m.index + m[0].length;
  }
  if (at < text.length) out.push({ kind: "text", text: text.slice(at) });
  return out;
}
