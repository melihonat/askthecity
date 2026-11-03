"use client";

import { useLayoutEffect, useRef, useState, type ReactNode } from "react";
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

/** Single-turn: each question replaces the last one and its evidence. `idle` fills the panel before the first. */
export function Ask({ idle }: { idle: ReactNode }) {
  const [question, setQuestion] = useState("");
  const [asked, setAsked] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [passages, setPassages] = useState<PassageView[] | null>(null);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [active, setActive] = useState<number | null>(null); // the passage a marker points at
  const [seconds, setSeconds] = useState<number | null>(null); // submit → final event
  const [cached, setCached] = useState(false); // a cache hit sends only the final event (CONTRACT.md)

  async function submit(q = question) {
    if (!q.trim() || busy) return;
    setAsked(q.trim());
    setBusy(true);
    setPassages(null);
    setResponse(null);
    setActive(null);
    setSeconds(null);
    const start = performance.now();
    let sawPassages = false;
    const finish = (r: AskResponse) => {
      setResponse(r);
      setSeconds((performance.now() - start) / 1000);
      setCached(r.kind !== "limit" && !sawPassages);
    };
    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      // the firewall's burst rule answers 429 before the function runs
      if (!res.ok || !res.body) return finish(limit(res.status === 429 ? "burst" : "unavailable"));
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
          if (ev.type === "passages") {
            sawPassages = true;
            setPassages(ev.passages);
          } else if (ev.type === "final") finish(ev.response);
        }
      }
    } catch {
      finish(limit("unavailable"));
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
        {!asked && (
          <div className="intro">
            <h1>Ask about Toronto&apos;s bylaws.</h1>
            <p>
              Answers come only from the Municipal Code and committee decisions, with a numbered source for every
              claim. When the documents don&apos;t cover a question, it says so instead of guessing.
            </p>
          </div>
        )}

        <form
          className="composer"
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
            rows={2}
          />
          <div className="composer-row">
            <span className="hint">
              <kbd>Enter</kbd> to ask, <kbd>Shift</kbd> + <kbd>Enter</kbd> for a new line
            </span>
            <span className={question.length > MAX_QUESTION ? "counter over" : "counter"}>
              {question.length} / {MAX_QUESTION}
            </span>
            <button type="submit" className="send" disabled={busy || !question.trim()}>
              {busy ? <span className="spinner" aria-hidden /> : <ArrowUp />}
              {busy ? "Asking" : "Ask"}
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
              {ex.trick && <span className="chip-note"> · try a trick</span>}
            </button>
          ))}
        </div>

        {asked && (
          <article className="turn" aria-busy={busy}>
            <p className="asked">{asked}</p>

            {busy && <Progress passages={passages} />}
            {busy && <Skeleton lines={4} />}

            {response?.kind === "answer" && (
              <>
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
                <div className="actions">
                  <CopyButton text={() => plainAnswer(response.text, cited)} />
                  <Receipt
                    seconds={seconds}
                    cached={cached}
                    detail={`${cited.length} of ${response.passages.length} passages cited`}
                  />
                </div>
              </>
            )}

            {response?.kind === "refusal" && (
              <div className="refusal">
                <p className="refusal-head">The documents don&apos;t cover this.</p>
                <p>{REFUSAL[response.reason].line}</p>
                <p className="muted">{response.scope}</p>
                <Receipt seconds={seconds} cached={cached} detail="no answer given" />
              </div>
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
          </article>
        )}
      </section>

      <aside className="sources" aria-label="Sources">
        {!asked && idle}

        {busy && !passages && (
          <>
            <h3>Searching</h3>
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} lines={5} card />
            ))}
          </>
        )}

        {response?.kind === "limit" && <p className="muted empty">No search was run.</p>}

        {busy && passages && (
          <>
            <h3>
              Passages found <span className="count">{passages.length}</span>
            </h3>
            {passages.map((p) => (
              <Card key={p.n} p={p} />
            ))}
          </>
        )}

        {response?.kind === "answer" && (
          <>
            <h3>
              Cited <span className="count">{cited.length}</span>
            </h3>
            {cited.map((p) => (
              <Card key={p.n} p={p} active={p.n === active} />
            ))}
            {uncited.length > 0 && (
              <details className="uncited">
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

/** The answer with its markers, then the cited passages, for pasting elsewhere. */
function plainAnswer(text: string, cited: PassageView[]): string {
  return [text, "", "Sources:", ...cited.map((p) => `[${p.n}] ${p.label}, ${p.sublabel}: ${p.href}`)].join("\n");
}

/** The two steps a client can see: until the passages event, then until the final one (UI.md, "Waiting"). */
function Progress({ passages }: { passages: PassageView[] | null }) {
  return (
    <ol className="progress" aria-live="polite">
      <li className={passages ? "done" : "now"}>
        {passages ? `Found ${passages.length} passages in the bylaws and decisions` : "Searching the bylaws and decisions"}
      </li>
      <li className={passages ? "now" : "next"}>Writing an answer from them and checking its citations</li>
    </ol>
  );
}

function Receipt({ seconds, cached, detail }: { seconds: number | null; cached: boolean; detail: string }) {
  return (
    <span className="receipt">
      {detail}
      {seconds !== null && <>, {cached ? "served from cache" : `${seconds.toFixed(1)} s`}</>}
    </span>
  );
}

function CopyButton({ text }: { text: () => string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className="action"
      onClick={async () => {
        await navigator.clipboard.writeText(text());
        setCopied(true);
        setTimeout(() => setCopied(false), 1600);
      }}
    >
      {copied ? <Check /> : <Copy />}
      {copied ? "Copied" : "Copy answer"}
    </button>
  );
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

  const badges = [
    p.amendedSince.length > 0 && (
      <span key="amended" className="badge amber">
        amended since by {p.amendedSince.map((n) => `By-law ${n}`).join(", ")}
      </span>
    ),
    p.notYetLaw && (
      <span key="pending" className="badge red">
        not yet law
      </span>
    ),
    p.decided === true && (
      <span key="adopted" className="badge green">
        adopted
      </span>
    ),
    p.decided === false && (
      <span key="undecided" className="badge amber">
        no decision
      </span>
    ),
    p.companion && (
      <span key="companion" className="badge violet">
        {p.defines.length
          ? "definition for a retrieved §"
          : p.notYetLaw
            ? "replacement for a retrieved §"
            : "amendment to a retrieved §"}
      </span>
    ),
  ].filter(Boolean);

  return (
    <article
      id={`passage-${p.n}`}
      className={["card", `family-${p.family}`, p.companion && "companion", dim && "dim", active && "active"]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="card-head">
        <span className="tag">{p.n}</span>
        <div className="card-title">
          <strong>{p.label}</strong>
          <span className="sub">{p.sublabel}</span>
        </div>
        <a className="src" href={p.href} target="_blank" rel="noreferrer">
          source <span aria-hidden>↗</span>
        </a>
      </div>
      {badges.length > 0 && <div className="badges">{badges}</div>}
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
      {clamped && (
        <button type="button" className="more" aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? "show less" : "show full passage"}
        </button>
      )}
    </article>
  );
}

function ArrowUp() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden>
      <path d="M8 13V3M3.5 7.5 8 3l4.5 4.5" />
    </svg>
  );
}

function Copy() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden>
      <rect x="5.5" y="5.5" width="8" height="8" rx="1.5" />
      <path d="M10.5 5.5v-2a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2" />
    </svg>
  );
}

function Check() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden>
      <path d="m3 8.5 3 3 7-7" />
    </svg>
  );
}
