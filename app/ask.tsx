"use client";

import { useLayoutEffect, useRef, useState } from "react";
import { parseBody } from "@/lib/ask/body";
import { MAX_QUESTION } from "@/lib/ask/config";
import { splitGap } from "@/lib/ask/gap";
import { segments } from "@/lib/ask/markers";
import { EXAMPLES } from "@/lib/ask/scope";
import type { AskEvent, AskResponse, LimitKind, PassageView } from "@/lib/ask/types";

// Fixed per reason (CONTRACT.md, "Refusal rule"): no model-written text in a refusal.
const REFUSAL = {
  below_threshold: { line: "Nothing in the snapshot comes close to this question.", nearest: "Closest passages (not a match)" },
  model_declined: { line: "I found related passages, but none of them answers it.", nearest: "Related, but not an answer" },
  no_valid_citation: {
    line: "I couldn't back an answer with a citation, so I'm not giving one.",
    nearest: "Passages I had",
  },
} as const;

// UI.md, "Limit": a calm notice, never styled like a refusal.
const LIMIT: Record<LimitKind, { headline: string; line: string }> = {
  ip_daily: {
    headline: "You've asked 30 questions today.",
    line: "That's the per-visitor limit for this demo. It resets at midnight Toronto time.",
  },
  global_daily: {
    headline: "The demo is resting until tomorrow.",
    line: "It has answered its 30 questions for today. It resets at midnight Toronto time.",
  },
  budget: { headline: "The demo is resting until tomorrow.", line: "This month's model budget is used up." },
  burst: { headline: "Too many questions at once.", line: "Wait a few seconds and try again." },
  too_long: { headline: "That question is over 300 characters.", line: "Shorten it and ask again." },
  unavailable: { headline: "The demo can't answer right now.", line: "A service it relies on didn't respond. Try again in a minute." },
};

/** Single-turn: each question replaces the last one and its evidence. */
export function Ask() {
  const [question, setQuestion] = useState("");
  const [asked, setAsked] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [passages, setPassages] = useState<PassageView[] | null>(null);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [active, setActive] = useState<number | null>(null); // the passage a marker points at

  async function submit(q = question) {
    if (!q.trim() || busy) return;
    setAsked(q.trim());
    setBusy(true);
    setPassages(null);
    setResponse(null);
    setActive(null);
    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      // the firewall's burst rule answers 429 before the function runs
      if (!res.ok || !res.body) return setResponse(limit(res.status === 429 ? "burst" : "unavailable"));
      const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
      let buf = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += value;
        let i;
        while ((i = buf.indexOf("\n")) >= 0) {
          const ev = JSON.parse(buf.slice(0, i)) as AskEvent;
          buf = buf.slice(i + 1);
          if (ev.type === "passages") setPassages(ev.passages);
          else if (ev.type === "final") setResponse(ev.response);
        }
      }
    } catch {
      setResponse(limit("unavailable"));
    } finally {
      setBusy(false);
    }
  }

  const cited =
    response?.kind === "answer"
      ? response.citations.map((c) => response.passages.find((p) => p.n === c.n)!)
      : [];
  const uncited = response?.kind === "answer" ? response.passages.filter((p) => !cited.includes(p)) : [];
  const answer = response?.kind === "answer" ? splitGap(response.text) : null;

  function point(n: number) {
    setActive(n);
    document.getElementById(`passage-${n}`)?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  return (
    <main className="panes">
      <section className="ask">
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
            aria-label="Your question"
            rows={3}
          />
          <div className="row">
            <span className={question.length > MAX_QUESTION ? "counter over" : "counter"}>
              {question.length} / {MAX_QUESTION}
            </span>
            <button type="submit" disabled={busy}>
              {busy ? "Asking…" : "Ask"}
            </button>
          </div>
        </form>

        <div className="chips">
          {EXAMPLES.map((ex) => (
            <button
              key={ex.question}
              type="button"
              className={ex.trick ? "chip trick" : "chip"}
              disabled={busy}
              onClick={() => {
                setQuestion(ex.question);
                submit(ex.question);
              }}
            >
              {ex.question}
              {ex.trick && <span className="muted"> · try a trick</span>}
            </button>
          ))}
        </div>

        {asked && <h2 className="asked">{asked}</h2>}
        {busy && passages && <p className="muted">Found {passages.length} passages. Writing an answer from them…</p>}
        {busy && <Skeleton lines={4} />}

        {response?.kind === "answer" && (
          <p className="answer">
            {segments(answer!.body).map((s, i) =>
              s.kind === "text" ? (
                s.text
              ) : (
                <button
                  key={i}
                  type="button"
                  className={s.n === active ? "marker active" : "marker"}
                  aria-label={`Passage ${s.n}`}
                  onMouseEnter={() => point(s.n)}
                  onMouseLeave={() => setActive(null)}
                  onFocus={() => point(s.n)}
                  onClick={() => point(s.n)}
                >
                  {s.n}
                </button>
              ),
            )}
            {answer!.gap && <span className="gap"> {answer!.gap}</span>}
          </p>
        )}

        {response?.kind === "refusal" && (
          <>
            <p className="answer">
              <strong>The documents don&apos;t cover this.</strong>
            </p>
            <p>{REFUSAL[response.reason].line}</p>
            <p className="muted">{response.scope}</p>
          </>
        )}

        {response?.kind === "limit" && (
          <div className="notice" role="status">
            <p>
              <strong>{LIMIT[response.limit].headline}</strong>
            </p>
            <p>{LIMIT[response.limit].line}</p>
            <p>The example questions and the eval results still work.</p>
          </div>
        )}
      </section>

      <aside className="sources">
        {busy && !passages && [0, 1, 2].map((i) => <Skeleton key={i} lines={5} card />)}

        {response?.kind === "limit" && <p className="muted">No search was run.</p>}

        {busy && passages && (
          <>
            <h3>Passages found</h3>
            {passages.map((p) => (
              <Card key={p.n} p={p} />
            ))}
          </>
        )}

        {response?.kind === "answer" && (
          <>
            <h3>Cited ({cited.length})</h3>
            {cited.map((p) => (
              <Card key={p.n} p={p} active={p.n === active} />
            ))}
            {uncited.length > 0 && (
              <details>
                <summary>{uncited.length} more retrieved, not cited</summary>
                {uncited.map((p) => (
                  <Card key={p.n} p={p} dim />
                ))}
              </details>
            )}
          </>
        )}

        {response?.kind === "refusal" && (
          <>
            <h3>{REFUSAL[response.reason].nearest}</h3>
            {response.nearest.map((p) => (
              <Card key={p.n} p={p} dim />
            ))}
          </>
        )}
      </aside>
    </main>
  );
}

function limit(kind: LimitKind): AskResponse {
  return { kind: "limit", limit: kind };
}

function Skeleton({ lines, card }: { lines: number; card?: boolean }) {
  return (
    <div className={card ? "card skeleton" : "skeleton"} aria-hidden>
      {Array.from({ length: lines }, (_, i) => (
        <span key={i} />
      ))}
    </div>
  );
}

function Card({ p, dim, active }: { p: PassageView; dim?: boolean; active?: boolean }) {
  const body = useRef<HTMLDivElement>(null);
  const [clamped, setClamped] = useState(false); // the body overflows its ~6 lines
  const [open, setOpen] = useState(false);
  useLayoutEffect(() => {
    const el = body.current!;
    setClamped(el.scrollHeight > el.clientHeight + 1);
  }, [p.body]);

  return (
    <article
      id={`passage-${p.n}`}
      className={["card", p.companion && "companion", dim && "dim", active && "active"].filter(Boolean).join(" ")}
    >
      <div>
        <span className="tag">{p.n}</span> <strong>{p.label}</strong>
        {p.amendedSince.length > 0 && (
          <span className="badge amber">amended since by {p.amendedSince.map((n) => `By-law ${n}`).join(", ")}</span>
        )}
        {p.notYetLaw && <span className="badge red">not yet law</span>}
        {p.decided === true && <span className="badge green">adopted</span>}
        {p.decided === false && <span className="badge amber">no decision</span>}
        {p.companion && (
          <span className="badge violet">
            {p.defines.length
              ? "definition for a retrieved §"
              : p.notYetLaw
                ? "replacement for a retrieved §"
                : "amendment to a retrieved §"}
          </span>
        )}
      </div>
      <div className="muted">
        {p.sublabel} ·{" "}
        <a href={p.href} target="_blank" rel="noreferrer">
          source ↗
        </a>
      </div>
      <div ref={body} className={open ? "body open" : "body"}>
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
      {clamped && !open && (
        <button type="button" className="more" onClick={() => setOpen(true)}>
          show full passage
        </button>
      )}
    </article>
  );
}
