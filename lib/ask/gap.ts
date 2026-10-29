// The gap sentence (CONTRACT.md, "Partial coverage is an answer"): the one uncited sentence a
// partial answer ends with. Only the final sentence counts, and only after a cited one; a
// lead "No." or other uncited sentences mid-answer render plainly.

const MARKER = /\[\d+\]/g;

export function splitGap(text: string): { body: string; gap: string | null } {
  const markers = [...text.matchAll(MARKER)];
  if (!markers.length) return { body: text, gap: null };
  const last = markers[markers.length - 1];
  const tail = text.slice(last.index + last[0].length);
  // the last sentence of what follows the final marker (and its closing punctuation)
  const gap = tail.replace(/^[.;:,!?]*/, "").trim().split(/(?<=[.!?])\s+(?=[A-Z"“])/).pop()!;
  if (!gap) return { body: text, gap: null };
  return { body: text.slice(0, text.lastIndexOf(gap)).trimEnd(), gap };
}
