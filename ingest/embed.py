"""embed: build/chunks.jsonl → build/embeddings.jsonl, via Voyage directly with the ingestion key.

Cached by (model, sha256 of the embedded text): a re-run pays only for changed chunks. Prints
the token count and cost estimate and asks before spending. Batches stay under the no-card
free tier's 10K tokens/minute; a 429 is waited out, so the run goes as fast as the account's
limits allow, and an interrupted run resumes from the cache.
"""
from __future__ import annotations

import hashlib
import json
import time

import requests

from . import config
from .chunk import tokens

VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
BATCH_TOKENS = 5_000   # cl100k estimate; Voyage counts ~20-30% more


def embed_text(chunk: dict) -> str:
    return f"{chunk['breadcrumb']}\n\n{chunk['body']}"


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_cache() -> dict[str, list[float]]:
    cache = {}
    if config.EMBED_CACHE.exists():
        for line in config.EMBED_CACHE.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if (rec["model"], rec["dim"]) == (config.EMBED_MODEL, config.EMBED_DIM):
                cache[rec["hash"]] = rec["embedding"]
    return cache


def batches(items: list[tuple[str, str, int]]):
    batch, used = [], 0
    for item in items:
        if batch and used + item[2] > BATCH_TOKENS:
            yield batch
            batch, used = [], 0
        batch.append(item)
        used += item[2]
    if batch:
        yield batch


def call_voyage(texts: list[str]) -> tuple[list[list[float]], int]:
    while True:
        resp = requests.post(VOYAGE_URL, timeout=120, headers={
            "Authorization": f"Bearer {config.env('VOYAGE_API_KEY')}"}, json={
            "input": texts, "model": config.EMBED_MODEL, "input_type": "document",
            "output_dimension": config.EMBED_DIM})
        if resp.status_code == 429:
            print(f"  rate limited ({resp.text[:120]}); waiting 61 s")
            time.sleep(61)
            continue
        resp.raise_for_status()
        body = resp.json()
        return [d["embedding"] for d in sorted(body["data"], key=lambda d: d["index"])], body["usage"]["total_tokens"]


def embed(yes: bool = False) -> None:
    chunks = [json.loads(line) for line in config.CHUNKS.read_text(encoding="utf-8").splitlines()]
    cache = load_cache()

    todo: dict[str, tuple[str, str, int]] = {}
    for c in chunks:
        text = embed_text(c)
        h = text_hash(text)
        if h not in cache:
            todo[h] = (h, text, tokens(text))

    est = sum(t for _, _, t in todo.values())
    print(f"{len(chunks)} chunks, {len(chunks) - len(todo)} cached, {len(todo)} to embed")
    if todo:
        print(f"≈ {est:,} tokens (cl100k estimate) × ${config.EMBED_PRICE_PER_MTOK}/M "
              f"≈ ${est * config.EMBED_PRICE_PER_MTOK / 1e6:.4f} at list price ({config.EMBED_MODEL})")
        if not yes and input("Spend it? [y/N] ").strip().lower() != "y":
            raise SystemExit("not confirmed; nothing spent")

        spent = 0
        with config.EMBED_CACHE.open("a", encoding="utf-8", newline="\n") as f:
            for i, batch in enumerate(batches(list(todo.values()))):
                vectors, used = call_voyage([text for _, text, _ in batch])
                spent += used
                for (h, _, _), v in zip(batch, vectors):
                    if len(v) != config.EMBED_DIM:
                        raise SystemExit(f"Voyage returned {len(v)} dims, expected {config.EMBED_DIM}")
                    cache[h] = v
                    f.write(json.dumps({"model": config.EMBED_MODEL, "dim": config.EMBED_DIM,
                                        "hash": h, "embedding": v}) + "\n")
                f.flush()
                print(f"  batch {i + 1}: {len(batch)} chunks, {used:,} tokens")
        print(f"embedded {len(todo)} chunks, {spent:,} Voyage tokens")

    with config.EMBEDDINGS.open("w", encoding="utf-8", newline="\n") as f:
        for c in chunks:
            f.write(json.dumps({"chunk_id": c["id"], "model": config.EMBED_MODEL, "dim": config.EMBED_DIM,
                                "embedding": cache[text_hash(embed_text(c))]}) + "\n")
