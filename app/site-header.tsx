import { EVALS } from "./evals/data";

/** The header on every page. The Evals link's count comes from the generated eval data. */
export function SiteHeader({ current, date }: { current: "ask" | "evals"; date?: string | null }) {
  return (
    <header className="site">
      <div className="site-inner">
        <a href="/" className="brand">
          <CityHall />
          Ask the City
        </a>
        <nav>
          <a href="/" aria-current={current === "ask" ? "page" : undefined}>
            Ask
          </a>
          <a href="/evals" aria-current={current === "evals" ? "page" : undefined}>
            {EVALS.headerLink}
          </a>
        </nav>
        {date && <span className="asof">Documents as of {date}</span>}
      </div>
    </header>
  );
}

/** Toronto City Hall: two curved towers around the council chamber. */
function CityHall() {
  return (
    <svg className="mark" viewBox="0 0 24 24" aria-hidden>
      <path d="M2.5 20V9.5C2.5 6.6 4.4 4.7 8.5 4.2V20Z" />
      <path d="M21.5 20V5.5C21.5 2.9 19.6 1.3 15.5 1V20Z" />
      <path d="M8.9 17.6c0-1.6 1.4-2.6 3.1-2.6s3.1 1 3.1 2.6Z" />
      <rect x="1" y="20" width="22" height="2" rx=".5" />
    </svg>
  );
}
