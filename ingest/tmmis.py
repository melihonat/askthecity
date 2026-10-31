"""TMMIS item pages: the receiver the save runbook posts to, check-saves, and the item-page chunker.

Item pages are read as windows-1252 with BeautifulSoup (CHUNKING.md, "Decisions: item pages").
Each stage of an item (IE Committee, City Council) is one card on the page; its h4 blocks are
the chunking units. Communications and Speakers name members of the public and are stripped;
Background Information only lists the bgrd/ files, which `fetch-reports` handles.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from bs4 import BeautifulSoup, NavigableString, Tag

from . import config, store

ITEM_URL = "https://secure.toronto.ca/council/agenda-item.do?item={id}"
ENCODING = "windows-1252"
# Items per meeting (INGESTION.md): the expected list must match these counts.
MEETING_COUNTS = {"2025.IE24": 15, "2025.IE25": 14, "2025.IE26": 19, "2026.IE27": 17,
                  "2026.IE28": 14, "2026.IE29": 10, "2026.IE30": 14, "2026.IE31": 12}
MIN_BYTES = 10_000
SAVE_WINDOW_DAYS = 7

STRIPPED = ("Communications", "Speakers", "Background Information")
INLINE = {"a", "abbr", "b", "em", "font", "i", "small", "span", "strong", "sub", "sup", "u"}
MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
# "May 6, 2026", "May 20 and 21, 2026", "December 16, 17 and 18, 2025": the last day counts.
DATE = re.compile(rf"({MONTH}) ([\d, and]+?),? (\d{{4}})")
COMMITTEE = "Infrastructure and Environment Committee"


def expected_ids() -> list[str]:
    return [line.strip() for line in config.TMMIS_ITEMS.read_text(encoding="utf-8").splitlines() if line.strip()]


def last_date(text: str) -> str:
    m = DATE.search(text)
    if not m:
        raise ValueError(f"no date in {text!r}")
    day = re.findall(r"\d+", m[2])[-1]
    return datetime.strptime(f"{m[1]} {day} {m[3]}", "%B %d %Y").strftime("%Y-%m-%d")


# ── receiver ─────────────────────────────────────────────────────────────────────────────

class _Receiver(BaseHTTPRequestHandler):
    """POST /<item id> with the page's bytes as the body. Headers carry what the page saw:
    X-Obtained-By (agent_fetch | browser_save), X-Last-Modified, X-Etag, X-Content-Type."""

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "https://secure.toronto.ca")
        self.send_header("Access-Control-Allow-Methods", "POST")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self) -> None:
        item_id = self.path.strip("/")
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        status, msg = 200, ""
        if item_id not in self.server.expected:
            status, msg = 400, f"{item_id} is not in {config.TMMIS_ITEMS.name}"
        elif self.headers.get("X-Obtained-By") not in ("agent_fetch", "browser_save"):
            status, msg = 400, "X-Obtained-By must be agent_fetch or browser_save"
        else:
            row = store.put(data, store.ManifestRow(
                sha256="", kind="item_page", ref=item_id, parent_ref="",
                source_url=ITEM_URL.format(id=item_id), obtained_by=self.headers["X-Obtained-By"],
                obtained_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                last_modified=self.headers.get("X-Last-Modified", ""), etag=self.headers.get("X-Etag", ""),
                bytes=0, content_type=self.headers.get("X-Content-Type", ""), encoding=ENCODING,
            ))
            msg = f"{item_id}: {row.bytes} bytes, sha256 {row.sha256[:12]}…"
        print(msg)
        self.send_response(status)
        self._cors()
        self.end_headers()
        self.wfile.write(msg.encode())

    def log_message(self, *args) -> None:
        pass


def receive(port: int) -> None:
    server = HTTPServer(("127.0.0.1", port), _Receiver)   # one request at a time: the manifest is a file
    server.expected = set(expected_ids())
    print(f"receiving item pages on http://127.0.0.1:{port}/<item id> (Ctrl+C to stop)")
    server.serve_forever()


# ── check-saves ──────────────────────────────────────────────────────────────────────────

def count_failures(ids: list[str]) -> list[str]:
    """The expected list against the per-meeting counts."""
    got = Counter(i.rsplit(".", 1)[0] for i in ids)
    fail = [f"{m}: {got.get(m, 0)} items, expected {n}" for m, n in MEETING_COUNTS.items() if got.get(m, 0) != n]
    fail += [f"{m}: not an IE24–IE31 meeting" for m in sorted(set(got) - set(MEETING_COUNTS))]
    if dupes := sorted(i for i, n in Counter(ids).items() if n > 1):
        fail.append(f"listed twice: {dupes}")
    return fail


def page_failures(item_id: str, data: bytes, obtained_at: str, snapshot_date: str) -> list[str]:
    """Why one saved item page doesn't pass; empty when it does."""
    fail = []
    if len(data) < MIN_BYTES:
        fail.append(f"{len(data)} bytes, under {MIN_BYTES}")
    try:
        text = data.decode(ENCODING)
    except UnicodeDecodeError as e:
        return [*fail, f"not {ENCODING}: {e.reason} at byte {e.start}"]
    if re.search(r"<title>\s*Access Denied", text, re.I):
        return [*fail, "Akamai Access Denied page"]
    if not re.search(rf"<h1[^>]*>\s*Item - {re.escape(item_id)}\s*</h1>", text):
        fail.append("no item heading")
    if not re.search(r"<h2[^>]*>\s*Tracking Status\s*</h2>", text):
        fail.append("no Tracking Status")
    start = date.fromisoformat(snapshot_date)
    saved = date.fromisoformat(obtained_at[:10])
    if not start <= saved <= start + timedelta(days=SAVE_WINDOW_DAYS):
        fail.append(f"saved {saved}, outside {start}…{start + timedelta(days=SAVE_WINDOW_DAYS)}")
    return fail


def check_saves() -> None:
    ids = expected_ids()
    fail = count_failures(ids)
    rows = {r.ref: r for r in store.read_manifest() if r.kind == "item_page"}
    today = store.snapshot_date()
    passed = 0
    for item_id in ids:
        row = rows.get(item_id)
        if not row:
            problems = ["no manifest row"]
        elif not row.local_path.exists():
            problems = [f"{row.local_path.relative_to(config.ROOT)} missing (run restore)"]
        else:
            problems = page_failures(item_id, row.local_path.read_bytes(), row.obtained_at, today)
        if problems:
            fail.append(f"{item_id}: {'; '.join(problems)}")
        else:
            passed += 1
    if extra := sorted(set(rows) - set(ids)):
        fail.append(f"saved but not expected: {extra}")
    print(f"{passed}/{len(ids)} item pages pass")
    if fail:
        raise SystemExit("check-saves failed:\n  " + "\n  ".join(fail))
    from .fetch import write_snapshot_md
    write_snapshot_md()


# ── parsing ──────────────────────────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    return " ".join(s.split())


def _classes(el: Tag) -> list[str]:
    return el.get("class") or []


def flatten(node: Tag) -> list[tuple[str, object]]:
    """A card body → ("h", heading) | ("p", text) | ("t", rows), in document order. Only plain
    h4s are headings; a vote header is a line of its block. Screen-reader-only text is dropped."""
    out: list[tuple[str, object]] = []
    buf: list[str] = []

    def flush():
        if text := _norm("".join(buf)):
            out.append(("p", text))
        buf.clear()

    def walk(el: Tag):
        for child in el.children:
            if isinstance(child, NavigableString):
                if type(child) is NavigableString:   # not a comment or doctype
                    buf.append(str(child))
            elif "sr-only" in _classes(child):
                continue
            elif child.name == "br":
                flush()
            elif child.name in INLINE:
                buf.append(child.get_text())
            elif child.name == "h4" and "vote-table-header" not in _classes(child):
                flush()
                out.append(("h", _norm(child.get_text(" "))))
            elif child.name == "table":
                flush()
                rows = [[_norm(c.get_text(" ")) for c in tr.find_all(["th", "td"])] for tr in child.find_all("tr")]
                if rows := [r for r in rows if any(r)]:
                    out.append(("t", rows))
            else:
                flush()
                walk(child)
                flush()

    for tag in node.select(".sr-only"):
        tag.decompose()
    walk(node)
    flush()
    return out


def blocks_of(card_body: Tag) -> list[tuple[str, list[tuple[str, object]]]]:
    """A card body → (heading, items) per h4 block. Text before the first h4 (the d-info list) is
    dropped; stripped blocks go; an empty block ("2a - Supplementary Report …") prefixes the next."""
    blocks: list[tuple[str, list]] = []
    heading, items, prefix = None, [], ""
    for kind, value in flatten(card_body) + [("h", None)]:
        if kind != "h":
            items.append((kind, value))
            continue
        if heading is not None:
            if not items:
                prefix = f"{prefix}{heading} › "
            else:
                if not heading.startswith(STRIPPED):
                    blocks.append((prefix + heading, items))
                prefix = ""
        heading, items = value, []
    return blocks


def status_stamp(lines: list[str]) -> tuple[str, str, bool, list[str]]:
    """Tracking Status lines (newest stage first) → (stamp, decision date, decided, by-laws).
    A stamp names who did what and when; an undecided one ends "; no decision"."""
    bylaws = sorted({b for li in lines if li.startswith("See also By-law") for b in re.findall(r"\d+-\d{4}", li)},
                    key=lambda b: (b[-4:], int(b.split("-")[0])))
    latest = lines[0]
    when = last_date(latest)
    amended = " with amendments" if re.search(r"\bwith amendments\b", latest) else ""
    if latest.startswith("City Council adopted"):
        stamp, decided = f"Adopted{amended} by City Council {when}", True
    elif latest.startswith("City Council considered") and "received the item for information" in latest:
        stamp, decided = f"Received for information by City Council {when}", False
    elif "will be considered by City Council" in latest:
        raise ValueError(f"awaiting City Council: {latest!r}")
    elif "ruled out of order" in latest:
        stamp, decided = f"Ruled out of order at IE Committee {when}", False
    elif "postponed consideration" in latest:
        stamp, decided = f"Deferred by IE Committee {when}", False
    elif "referred this item" in latest:
        stamp, decided = f"Referred by IE Committee {when}", False
    elif "received the item for information" in latest:
        stamp, decided = f"Received for information by IE Committee {when}", False
    elif re.search(r"\badopted (with amendments|without amendment)", latest) and COMMITTEE in latest:
        stamp, decided = f"Adopted{amended} by IE Committee {when}", True
    else:
        raise ValueError(f"unknown Tracking Status: {latest!r}")
    if bylaws:
        stamp += f" · By-law{'s' if len(bylaws) > 1 else ''} {', '.join(bylaws)}"
    if not decided:
        stamp += "; no decision"
    return stamp, when, decided, bylaws


def parse_item(html: str, item_id: str) -> dict:
    """An item page → title, status stamp and its stages (newest first), each with h4 blocks."""
    soup = BeautifulSoup(html, "html.parser")
    tracking = soup.find("h2", string=re.compile(r"^\s*Tracking Status\s*$"))
    if not tracking:
        raise ValueError(f"{item_id}: no Tracking Status")
    lines = [_norm(li.get_text(" ")) for li in tracking.find_next("ul").find_all("li")]
    stamp, when, decided, bylaws = status_stamp(lines)

    stages, title = [], None
    for card in soup.select("#agenda-item-accordion > .card"):
        header = _norm(card.select_one(".card-header").get_text(" "))
        if header.startswith("City Council"):
            stage = "council"
        elif header.startswith(COMMITTEE):
            stage = "committee"
        else:
            raise ValueError(f"{item_id}: unknown stage {header!r}")
        body = card.select_one(".card-body")
        title = title or re.sub(r"^\S+\s+-\s+", "", _norm(body.find("h3", class_="heading").get_text(" ")))
        blocks = blocks_of(body)
        stages.append({"stage": stage, "date": last_date(header), "blocks": blocks,
                       "recommends": any(h.endswith("Committee Recommendations") for h, _ in blocks)})
    if not stages:
        raise ValueError(f"{item_id}: no stage cards")
    return {"item_id": item_id, "title": title, "stamp": stamp, "decision_date": when,
            "decided": decided, "bylaws": bylaws, "stages": stages}


# ── chunks ───────────────────────────────────────────────────────────────────────────────

def stage_label(stage: dict) -> str:
    """The stage is always named, so a committee recommendation never reads as Council's decision."""
    if stage["stage"] == "council":
        return "City Council decision"
    return "IE Committee recommendation" if stage["recommends"] else "IE Committee decision"


def chunk_item_page(html: str, row: store.ManifestRow) -> tuple[dict, list[dict]]:
    """One saved item page → (document, chunks). Per stage: one chunk under the ceiling, else its
    h4 blocks packed up to the ceiling (ids :1, :2, …). Every chunk carries the status stamp."""
    from . import chunk as chunker

    item = parse_item(html, row.ref)
    item_id, stamp = item["item_id"], item["stamp"]
    document = {
        "id": f"ie:{item_id}", "kind": "item_page", "family": "decisions",
        "title": f"Item {item_id} {item['title']}", "source_url": row.source_url, "sha256": row.sha256,
        "fetched_at": row.obtained_at[:10], "consolidated_as_of": None, "enacted": None, "in_force": None,
        "item_id": item_id, "status_stamp": stamp, "decision_date": item["decision_date"],
        "bylaws": item["bylaws"],
    }
    chunks = []
    for stage in item["stages"]:
        units = []
        for heading, items in stage["blocks"]:
            bs = [chunker.Block("para", 0, text=v) if k == "p" else chunker.Block("table", 0, rows=v)
                  for k, v in items]
            if bs[0].kind == "para":   # the heading rides with its first paragraph, never alone
                bs[0].text = f"{heading}\n\n{bs[0].text}"
            else:
                bs.insert(0, chunker.Block("para", 0, text=heading))
            units.append((heading, bs))
        if not units:
            continue
        whole = [b for _, bs in units for b in bs]
        pieces = [(units[0][0], units[-1][0], whole)] if chunker.size(whole) <= chunker.CEILING \
            else chunker.pack(units, lambda label, bs: chunker.pack_flat(bs, label))
        label = stage_label(stage)
        for n, (first, last, bs) in enumerate(pieces, 1):
            heading = first if first == last else f"{first} – {last}"
            split = len(pieces) > 1
            text = chunker.render(bs)
            chunks.append({
                "id": f"ie:{item_id}:{stage['stage']}" + (f":{n}" if split else ""),
                "document_id": document["id"], "family": "decisions", "kind": "item_page",
                "chapter": None, "article": None, "section": None, "subsection_range": None,
                "stage": stage["stage"], "heading": heading,
                "breadcrumb": f"[IE Committee item {item_id} · {item['title']} › {heading}]\n[Status: {stamp}]",
                "body": text,
                "label": f"Item {item_id} · {label}" + (f" ({n}/{len(pieces)})" if split else ""),
                "sublabel": f"{stage['date']} · {stamp}",
                "href": row.source_url,
                "amended_by": [], "amended_since": [], "page_start": None, "page_end": None,
                "tokens": chunker.tokens(text),
            })
    return document, chunks
