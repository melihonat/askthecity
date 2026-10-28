"use client";

import { useState } from "react";
import { parseBody } from "@/lib/ask/body";
import type { AskEvent, AskResponse, PassageView } from "@/lib/ask/types";

const REFUSAL_LINE = {
  below_threshold: "Nothing in the snapshot comes close to this question.",
  model_declined: "I found related passages, but none of them answers it.",
  no_valid_citation: "I couldn't back an answer with a citation, so I'm not giving one.",
} as const;

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [passages, setPassages] = useState<PassageView[] | null>(null);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!question.trim() || busy) return;
    setBusy(true);
    setPassages(null);
    setResponse(null);
    setError(null);
    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok || !res.body) throw new Error((await res.json().catch(() => null))?.error ?? res.statusText);
      const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
      let buf = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += value;
        let i;
        while ((i = buf.indexOf("\n")) >= 0) {
          const ev = JSON.parse(buf.slice(0, i)) as AskEvent | { type: "error"; message: string };
          buf = buf.slice(i + 1);
          if (ev.type === "passages") setPassages(ev.passages);
          else if (ev.type === "final") setResponse(ev.response);
          else setError(ev.message);
        }
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const cited =
    response?.kind === "answer"
      ? response.citations.map((c) => response.passages.find((p) => p.n === c.n)!)
      : [];

  return (
    <main>
      <h1>Ask the City</h1>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="How late can my neighbour run a leaf blower?"
          rows={3}
        />
        <button type="submit" disabled={busy}>
          {busy ? "Asking…" : "Ask"}
        </button>
      </form>

      {busy && passages && <p className="muted">Found {passages.length} passages. Writing an answer from them…</p>}
      {error && <p className="error">{error}</p>}

      {response?.kind === "answer" && (
        <section>
          <p className="answer">{response.text}</p>
          <h2>Cited ({cited.length})</h2>
          {cited.map((p) => (
            <Card key={p.n} p={p} />
          ))}
        </section>
      )}

      {response?.kind === "refusal" && (
        <section>
          <p className="answer">
            <strong>The documents don&apos;t cover this.</strong> {REFUSAL_LINE[response.reason]}
          </p>
          <p className="muted">{response.scope}</p>
          {response.nearest.map((p) => (
            <Card key={p.n} p={p} dim />
          ))}
        </section>
      )}

      {response?.kind === "limit" && <p className="notice">That question is over 300 characters. Shorten it and ask again.</p>}

      <footer className="muted">
        Source documents © City of Toronto. Quoted for reference. Official versions at toronto.ca.
      </footer>
    </main>
  );
}

function Card({ p, dim }: { p: PassageView; dim?: boolean }) {
  return (
    <article className={dim ? "card dim" : "card"}>
      <div>
        <span className="tag">{p.n}</span> <strong>{p.label}</strong>
      </div>
      <div className="muted">
        {p.sublabel} ·{" "}
        <a href={p.href} target="_blank" rel="noreferrer">
          source ↗
        </a>
      </div>
      <div className="body">
        {parseBody(p.body).map((b, i) =>
          b.kind === "text" ? (
            <p key={i}>{b.text}</p>
          ) : (
            <table key={i}>
              <thead>
                <tr>
                  {b.header.map((h, j) => (
                    <th key={j}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {b.rows.map((r, j) => (
                  <tr key={j}>
                    {r.map((c, k) => (
                      <td key={k}>{c}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ),
        )}
      </div>
    </article>
  );
}
