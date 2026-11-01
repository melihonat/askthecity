import { EVALS } from "./evals/data";

/** The header on every page. The Evals link's count comes from the generated eval data. */
export function SiteHeader({ current, date }: { current: "ask" | "evals"; date?: string | null }) {
  return (
    <header className="site">
      <strong>Ask the City</strong>
      <nav>
        <a href="/" aria-current={current === "ask" ? "page" : undefined}>
          Ask
        </a>
        <a href="/evals" aria-current={current === "evals" ? "page" : undefined}>
          {EVALS.headerLink}
        </a>
      </nav>
      {date && <span className="muted">documents as of {date}</span>}
    </header>
  );
}
