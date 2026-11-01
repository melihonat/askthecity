import { connection } from "next/server";
import { getSnapshot } from "@/lib/ask/deps";
import { formatSnapshotDate, scopeLine } from "@/lib/ask/scope";
import { Ask } from "./ask";
import { SiteHeader } from "./site-header";

export default async function AskPage() {
  await connection(); // the date comes from the live snapshot row, not the build
  // A failed read drops the date and scope band; /api/ask reports the error on submit.
  const snapshot = await getSnapshot().catch((e) => {
    console.error(e);
    return null;
  });
  const date = snapshot && formatSnapshotDate(snapshot.snapshot_date);

  return (
    <>
      <SiteHeader current="ask" date={date} />
      {snapshot && (
        <div className="scope">
          {scopeLine(date!)}{" "}
          <details>
            <summary>What&apos;s included</summary>
            <p>{snapshot.scope_sentence}</p>
          </details>
        </div>
      )}
      <Ask />
      <footer className="muted">
        Source documents © City of Toronto. Quoted for reference. Official versions at{" "}
        <a href="https://www.toronto.ca" target="_blank" rel="noreferrer">
          toronto.ca
        </a>
        .
      </footer>
    </>
  );
}
