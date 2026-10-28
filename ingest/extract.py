"""extract: PDFs in corpus/ → a normalised line/table stream in build/text/<ref>.jsonl.

This is the only module that touches a PDF library. Each output line is one record:

  {"kind": "page",  "page": 1, "width": 612.0, "height": 792.0}
  {"kind": "line",  "page": 1, "top": 80.5, "bottom": 92.5, "x0": 72.0, "size": 12.0, "bold": true, "text": "…"}
  {"kind": "table", "page": 3, "top": 120.0, "bottom": 300.0, "x0": 72.0, "rows": [["…", "…"], …]}

Superscript footnote markers are dropped from lines (they would fuse into numbers,
e.g. "By-law 268-2024" + "5" → "268-20245"). Text inside a table's region appears only
in its table record.
"""
from __future__ import annotations

import json
import re

import pdfplumber

from . import config, store

SUPERSCRIPT_RATIO = 0.8   # a char under 80% of its line's largest size is a superscript


def _r(v: float) -> float:
    return round(float(v), 1)


def _inside(obj: dict, bbox: tuple[float, float, float, float]) -> bool:
    x0, top, x1, bottom = bbox
    cx, cy = (obj["x0"] + obj["x1"]) / 2, (obj["top"] + obj["bottom"]) / 2
    return x0 <= cx <= x1 and top <= cy <= bottom


def extract_page(page) -> list[dict]:
    records: list[dict] = [{"kind": "page", "page": page.page_number,
                            "width": _r(page.width), "height": _r(page.height)}]
    tables = page.find_tables()
    for t in tables:
        x0, top, _, bottom = t.bbox
        rows = [[(c or "").replace("\n", " ").strip() for c in row] for row in t.extract()]
        records.append({"kind": "table", "page": page.page_number, "top": _r(top),
                        "bottom": _r(bottom), "x0": _r(x0), "rows": rows})

    superscripts = set()
    for line in page.extract_text_lines(return_chars=True):
        biggest = max(c["size"] for c in line["chars"])
        for c in line["chars"]:
            if c["size"] < SUPERSCRIPT_RATIO * biggest:
                superscripts.add((c["x0"], c["top"], c["text"]))

    def keep(obj: dict) -> bool:
        if obj.get("object_type") != "char":
            return True
        if (obj["x0"], obj["top"], obj["text"]) in superscripts:
            return False
        return not any(_inside(obj, t.bbox) for t in tables)

    for line in page.filter(keep).extract_text_lines(return_chars=True):
        # a dropped superscript leaves a gap pdfplumber reads as a space: "268-2024 ]"
        text = re.sub(r" +(?=[\]).,;:])", "", line["text"].strip())
        if not text:
            continue
        first = line["chars"][0]
        records.append({"kind": "line", "page": page.page_number, "top": _r(line["top"]),
                        "bottom": _r(line["bottom"]), "x0": _r(line["x0"]),
                        "size": _r(max(c["size"] for c in line["chars"])),
                        "bold": "Bold" in first["fontname"], "text": text})

    head, body = records[:1], records[1:]
    return head + sorted(body, key=lambda r: (r["top"], r["x0"]))


def extract() -> None:
    config.TEXT_DIR.mkdir(parents=True, exist_ok=True)
    for row in store.read_manifest():
        if row.ext != "pdf":
            continue
        out = config.TEXT_DIR / f"{row.ref}.jsonl"
        with pdfplumber.open(row.local_path) as pdf, out.open("w", encoding="utf-8", newline="\n") as f:
            for page in pdf.pages:
                for rec in extract_page(page):
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"{row.ref}: {out.relative_to(config.ROOT)}")
