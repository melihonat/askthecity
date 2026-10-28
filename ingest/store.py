"""Snapshot store: raw files in R2 by sha256, one committed manifest row per file."""
from __future__ import annotations

import csv
import hashlib
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from . import config


@dataclass
class ManifestRow:
    sha256: str
    kind: str              # code_chapter | amending_bylaw | item_page | staff_report
    ref: str               # ch-591, bylaw-470-2026, 2026.IE29.6, backgroundfile-286369
    parent_ref: str
    source_url: str
    obtained_by: str       # script | agent_fetch | browser_save
    obtained_at: str       # UTC, ISO 8601
    last_modified: str
    etag: str
    bytes: int
    content_type: str
    encoding: str

    @property
    def ext(self) -> str:
        return "html" if self.kind == "item_page" else "pdf"

    @property
    def key(self) -> str:
        return f"raw/{self.sha256}.{self.ext}"

    @property
    def local_path(self) -> Path:
        return config.CORPUS / self.kind / f"{self.ref}.{self.ext}"


COLUMNS = [f.name for f in fields(ManifestRow)]


def read_manifest() -> list[ManifestRow]:
    if not config.MANIFEST.exists():
        return []
    with config.MANIFEST.open(newline="", encoding="utf-8") as f:
        return [ManifestRow(**{**r, "bytes": int(r["bytes"])}) for r in csv.DictReader(f)]


def write_manifest(rows: list[ManifestRow]) -> None:
    config.MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: (r.kind, r.ref))
    with config.MANIFEST.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(asdict(r) for r in rows)


def _r2():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{config.env('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=config.env("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=config.env("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )


def put(data: bytes, row: ManifestRow) -> ManifestRow:
    """Store bytes in R2 and corpus/ under their sha256, and upsert the manifest row by (kind, ref)."""
    row.sha256 = hashlib.sha256(data).hexdigest()
    row.bytes = len(data)

    r2, bucket = _r2(), config.env("R2_BUCKET")
    try:
        r2.head_object(Bucket=bucket, Key=row.key)
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("404", "NoSuchKey"):
            raise
        r2.put_object(Bucket=bucket, Key=row.key, Body=data, ContentType=row.content_type)

    row.local_path.parent.mkdir(parents=True, exist_ok=True)
    row.local_path.write_bytes(data)

    rows = [r for r in read_manifest() if (r.kind, r.ref) != (row.kind, row.ref)]
    write_manifest([*rows, row])
    return row


def restore(r2=None, bucket: str | None = None) -> None:
    """Pull every manifest row from R2 into corpus/, verifying sha256. Bad bytes are never written."""
    r2, bucket = r2 or _r2(), bucket or config.env("R2_BUCKET")
    rows, bad = read_manifest(), []
    for row in rows:
        data = r2.get_object(Bucket=bucket, Key=row.key)["Body"].read()
        if hashlib.sha256(data).hexdigest() != row.sha256:
            bad.append(f"{row.ref} ({row.key})")
            continue
        row.local_path.parent.mkdir(parents=True, exist_ok=True)
        row.local_path.write_bytes(data)
    if bad:
        raise SystemExit(f"sha256 mismatch for {len(bad)} of {len(rows)} files; corpus/ is incomplete:\n  "
                         + "\n  ".join(bad))
    print(f"restored {len(rows)} files into {config.CORPUS.relative_to(config.ROOT)}/, sha256 verified")
