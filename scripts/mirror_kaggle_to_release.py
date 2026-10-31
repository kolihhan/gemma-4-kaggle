#!/usr/bin/env python3
"""Stream the full Kaggle competition archive into GitHub Release parts.

The script never stores the full ~22 GB archive on the runner. It downloads the
archive as one HTTP stream, writes one release-sized part at a time, uploads that
part, deletes it, and continues.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import requests


DEFAULT_COMPETITION = "gemma-4-developer-agent"
DEFAULT_PART_SIZE = 1_800_000_000  # comfortably below GitHub's 2 GiB asset limit


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=capture,
    )


def ensure_release(repo: str, tag: str) -> None:
    probe = subprocess.run(
        ["gh", "release", "view", tag, "--repo", repo],
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if probe.returncode == 0:
        return

    run(
        [
            "gh",
            "release",
            "create",
            tag,
            "--repo",
            repo,
            "--target",
            "main",
            "--title",
            f"Gemma 4 Kaggle full data mirror ({tag})",
            "--notes",
            (
                "Full raw competition data mirrored from Kaggle. Large data is split "
                "into <2 GiB release assets; manifests and restore tooling live in the repo."
            ),
        ]
    )


def write_kaggle_file_list(competition: str, output: Path) -> None:
    """Save Kaggle's current file inventory as CSV.

    Kaggle CLI syntax changed across releases, so support both the current
    positional form and the legacy -c form.
    """
    attempts = [
        ["kaggle", "competitions", "files", competition, "-v"],
        ["kaggle", "competitions", "files", "-c", competition, "-v"],
    ]
    last_error: subprocess.CalledProcessError | None = None
    for cmd in attempts:
        try:
            result = run(cmd, capture=True)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(result.stdout, encoding="utf-8")
            return
        except subprocess.CalledProcessError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def parse_inventory(path: Path) -> dict[str, int | None]:
    """Return best-effort file count and aggregate byte count from Kaggle CSV."""
    text = path.read_text(encoding="utf-8", errors="replace")
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        return {"file_count": None, "listed_bytes": None}

    total = 0
    saw_size = False
    for row in rows:
        raw = row.get("size") or row.get("Size")
        if raw is None:
            continue
        try:
            total += int(raw)
            saw_size = True
        except ValueError:
            pass
    return {
        "file_count": len(rows),
        "listed_bytes": total if saw_size else None,
    }


def open_kaggle_stream(competition: str, token: str) -> requests.Response:
    """Open the official download-all stream using Kaggle bearer auth."""
    endpoints = [
        f"https://api.kaggle.com/v1/competitions/data/download-all/{competition}",
        f"https://www.kaggle.com/api/v1/competitions/data/download-all/{competition}",
    ]
    errors: list[str] = []
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "kolihhan-gemma-4-kaggle-mirror/1.0",
    }

    for url in endpoints:
        try:
            response = requests.get(
                url,
                headers=headers,
                stream=True,
                allow_redirects=True,
                timeout=(30, 300),
            )
        except requests.RequestException as exc:
            errors.append(f"{url}: {exc}")
            continue

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                body = response.text[:1000]
                response.close()
                errors.append(f"{url}: unexpected JSON response: {body}")
                continue
            return response

        body = ""
        try:
            body = response.text[:1000]
        except Exception:
            pass
        errors.append(f"{url}: HTTP {response.status_code} {body}")
        response.close()

    raise RuntimeError("Unable to open Kaggle competition download:\n" + "\n".join(errors))


def upload_part(repo: str, tag: str, path: Path) -> None:
    run(["gh", "release", "upload", tag, str(path), "--repo", repo, "--clobber"])


def mirror_stream(
    response: requests.Response,
    *,
    repo: str,
    tag: str,
    competition: str,
    part_size: int,
    temp_dir: Path,
) -> tuple[list[dict[str, object]], int, str]:
    archive_name = f"{competition}.zip"
    whole_hash = hashlib.sha256()
    parts: list[dict[str, object]] = []
    total_bytes = 0
    part_index = 1
    part_file: BinaryIO | None = None
    part_path: Path | None = None
    part_hash: hashlib._Hash | None = None  # type: ignore[attr-defined]
    part_bytes = 0

    def start_part() -> None:
        nonlocal part_file, part_path, part_hash, part_bytes
        part_path = temp_dir / f"{archive_name}.part-{part_index:05d}"
        part_file = part_path.open("wb")
        part_hash = hashlib.sha256()
        part_bytes = 0

    def finish_part() -> None:
        nonlocal part_file, part_path, part_hash, part_bytes, part_index
        if part_file is None or part_path is None or part_hash is None or part_bytes == 0:
            return
        part_file.close()
        print(f"Uploading {part_path.name} ({part_bytes:,} bytes)", flush=True)
        upload_part(repo, tag, part_path)
        parts.append(
            {
                "name": part_path.name,
                "size": part_bytes,
                "sha256": part_hash.hexdigest(),
            }
        )
        part_path.unlink(missing_ok=True)
        part_file = None
        part_path = None
        part_hash = None
        part_bytes = 0
        part_index += 1

    start_part()
    try:
        for network_chunk in response.iter_content(chunk_size=8 * 1024 * 1024):
            if not network_chunk:
                continue
            whole_hash.update(network_chunk)
            total_bytes += len(network_chunk)
            view = memoryview(network_chunk)
            offset = 0
            while offset < len(view):
                assert part_file is not None and part_hash is not None
                remaining = part_size - part_bytes
                take = min(remaining, len(view) - offset)
                piece = view[offset : offset + take]
                part_file.write(piece)
                part_hash.update(piece)
                part_bytes += take
                offset += take
                if part_bytes == part_size:
                    finish_part()
                    start_part()
        finish_part()
    finally:
        response.close()
        if part_file is not None and not part_file.closed:
            part_file.close()
        if part_path is not None and part_path.exists():
            part_path.unlink(missing_ok=True)

    return parts, total_bytes, whole_hash.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--competition", default=DEFAULT_COMPETITION)
    parser.add_argument("--repo", required=True, help="GitHub repo as owner/name")
    parser.add_argument("--release-tag", required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--file-list-output", type=Path, required=True)
    parser.add_argument("--part-size", type=int, default=DEFAULT_PART_SIZE)
    args = parser.parse_args()

    token = os.environ.get("KAGGLE_API_TOKEN", "").strip()
    if not token:
        print("KAGGLE_API_TOKEN is not set", file=sys.stderr)
        return 2
    if args.part_size <= 0 or args.part_size >= 2 * 1024**3:
        raise ValueError("part size must be >0 and <2 GiB")

    write_kaggle_file_list(args.competition, args.file_list_output)
    inventory = parse_inventory(args.file_list_output)
    ensure_release(args.repo, args.release_tag)

    response = open_kaggle_stream(args.competition, token)
    content_length_raw = response.headers.get("content-length")
    content_length = int(content_length_raw) if content_length_raw and content_length_raw.isdigit() else None

    with tempfile.TemporaryDirectory(prefix="gemma4-mirror-") as tmp:
        parts, total_bytes, archive_sha256 = mirror_stream(
            response,
            repo=args.repo,
            tag=args.release_tag,
            competition=args.competition,
            part_size=args.part_size,
            temp_dir=Path(tmp),
        )

    if content_length is not None and total_bytes != content_length:
        raise RuntimeError(
            f"download size mismatch: expected Content-Length {content_length}, got {total_bytes}"
        )

    manifest = {
        "schema_version": 1,
        "competition": args.competition,
        "mirrored_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Kaggle competitions download-all API",
        "release_tag": args.release_tag,
        "archive_name": f"{args.competition}.zip",
        "archive_size": total_bytes,
        "archive_sha256": archive_sha256,
        "http_content_length": content_length,
        "inventory": inventory,
        "part_size_limit": args.part_size,
        "parts": parts,
    }
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
