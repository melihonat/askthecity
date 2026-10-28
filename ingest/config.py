"""Paths, model settings and secrets shared by every stage."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

CORPUS = ROOT / "corpus"            # raw files, gitignored
BUILD = ROOT / "build"              # extracted text, chunks, embeddings, gitignored
SNAPSHOT = ROOT / "snapshot"        # committed: manifest and hand-review files
MANIFEST = SNAPSHOT / "manifest.csv"

TEXT_DIR = BUILD / "text"
DOCUMENTS = BUILD / "documents.jsonl"
CHUNKS = BUILD / "chunks.jsonl"
EMBEDDINGS = BUILD / "embeddings.jsonl"
EMBED_CACHE = BUILD / "embed_cache.jsonl"

CODE_INDEX_URL = "https://www.toronto.ca/legdocs/bylaws/lawmcode.htm"

# The corpus and /api/ask must agree on these (lib/ask/config.ts checks them at startup).
EMBED_MODEL = "voyage-4-large"
EMBED_DIM = 1024
EMBED_PRICE_PER_MTOK = 0.12         # list price, USD; real spend is $0 inside Voyage's free tokens

CHUNKER_VERSION = "code-basic-1"

SCOPE_SENTENCE = (
    "Knows the Toronto Municipal Code, including by-laws that have amended it since, and the "
    "Infrastructure and Environment Committee's decisions and staff reports from September "
    "2025 to July 2026, as of {date}. It doesn't cover street-by-street parking schedules, "
    "zoning, or other City documents."
)


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is not set (see SETUP.md)")
    return value
