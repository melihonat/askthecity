// Shown by the Ask page shell (UI.md, "Shape").

/** `2026-10-29` → `October 29, 2026`, the same wording as the scope sentence (ingest/db.py). */
export function formatSnapshotDate(isoDate: string): string {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

/** The scope band's short line; the full scope sentence sits behind "What's included". */
export function scopeLine(date: string): string {
  return `Toronto Municipal Code + Infrastructure & Environment Committee decisions, as of ${date}.`;
}

// The README's "Try:" line mirrors these (STORY.md); swap them together.
export const EXAMPLES: { question: string; trick?: true }[] = [
  { question: "How late can my neighbour run a leaf blower?" },
  { question: "What does § 591-2.1 say?" },
  { question: "When am I allowed to set off fireworks in my backyard?" },
  { question: "Can I park on Abell Street overnight?", trick: true },
];
