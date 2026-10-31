# Runbook: save the TMMIS item pages

Stage 2 of [`INGESTION.md`](../INGESTION.md). Scripts get an Akamai 403 from
`secure.toronto.ca`, so an agent session with a real browser (the T3 Code preview browser, or
any Chromium the agent can drive) saves the pages. Run it **within 7 days of `fetch-rules`**:
`check-saves` fails any page saved outside that window. Last run: 2026-10-31, 115 of 115
saved by `agent_fetch`, none by hand.

## 1. Expected list

Open any TMMIS page in the browser, e.g.
`https://secure.toronto.ca/council/agenda-item.do?item=2026.IE29.6`, so later fetches are
same-origin. For each meeting (`2025.IE24` … `2026.IE31`), fetch
`/council/report.do?meeting=<meeting>&type=agenda` (and `type=minutes`) **inside the page**
and collect the `<h3 class="heading">IE29.1 - …` ids. Agenda and minutes must agree, and the
counts must match `MEETING_COUNTS` in `ingest/tmmis.py` (15, 14, 19, 17, 14, 10, 14, 12 = 115).
Write the full ids, one per line, to `snapshot/tmmis_items.txt`. A count that doesn't match
means stop and ask.

## 2. Save the exact bytes

Start the receiver; it accepts only ids on the expected list and writes each page through the
snapshot store (R2, `corpus/item_page/<id>.html`, a manifest row with `encoding=windows-1252`):

```
python -m ingest receive-saves            # http://127.0.0.1:8765/<item id>
```

Then, in the TMMIS tab, fetch each item page **inside the page** (the DOM is already decoded,
so only `fetch` gives the bytes as served) and POST them to the receiver, one at a time with a
pause:

```js
(() => {
  const ids = [/* the ids from snapshot/tmmis_items.txt */];
  window.__saveLog = [];
  (async () => {
    for (const id of ids) {
      const r = await fetch(`/council/agenda-item.do?item=${id}`);
      const body = await r.arrayBuffer();
      const p = await fetch(`http://127.0.0.1:8765/${id}`, {
        method: "POST", body,
        headers: {
          "X-Obtained-By": "agent_fetch",
          "X-Last-Modified": r.headers.get("last-modified") || "",
          "X-Etag": r.headers.get("etag") || "",
          "X-Content-Type": r.headers.get("content-type") || "",
        },
      });
      window.__saveLog.push(`${id} ${r.status} ${body.byteLength} ${p.status}`);
      await new Promise((s) => setTimeout(s, 400));
    }
  })();
  return ids.length;
})()
```

The loop runs in the page after the evaluate call returns (the preview tool times out at 15 s;
the loop keeps going). Watch the receiver's log: one line per saved page, about one a second.

## 3. Fallback: save by hand

A page the loop can't fetch is saved with Ctrl+S, "Webpage, HTML only" (never the `_files/`
folder), and posted to the receiver with `X-Obtained-By: browser_save` and no HTTP headers,
e.g. `curl --data-binary @page.html -H "X-Obtained-By: browser_save" http://127.0.0.1:8765/<id>`.

## 4. Check

```
python -m ingest check-saves
```

Prints `N/115 item pages pass` and every failing id with its reasons (Akamai page, not
windows-1252, under 10 KB, no item heading, no Tracking Status, saved outside the window,
wrong per-meeting counts). On a pass it rewrites `snapshot/SNAPSHOT.md`. Commit
`snapshot/tmmis_items.txt`, `snapshot/manifest.csv` and `snapshot/SNAPSHOT.md`; the pages
themselves are never committed.
