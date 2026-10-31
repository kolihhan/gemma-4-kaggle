#!/usr/bin/env python3
"""Restore the full Gemma 4 Kaggle dataset from GitHub Release parts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_REPO = "kolihhan/gemma-4-kaggle"
DEFAULT_BRANCH = "main"
DEFAULT_MANIFEST = "manifests/latest.json"


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url) as response:
        return json.load(response)


def stream_asset(url: str, output, expected_sha256: str) -> tuple[int, str]:
    hasher = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(url) as response:
        while True:
            block = response.read(8 * 1024 * 1024)
            if not block:
                break
            output.write(block)
            hasher.update(block)
            total += len(block)
    digest = hasher.hexdigest()
    if digest != expected_sha256:
        raise RuntimeError(f"part checksum mismatch for {url}: {digest} != {expected_sha256}")
    return total, digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repo as owner/name")
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=Path("downloads/gemma-4-developer-agent.zip"))
    parser.add_argument("--extract-to", type=Path, default=None)
    parser.add_argument("--delete-zip-after-extract", action="store_true")
    args = parser.parse_args()

    manifest_url = (
        f"https://raw.githubusercontent.com/{args.repo}/{args.branch}/"
        f"{urllib.parse.quote(args.manifest, safe='/')}"
    )
    print(f"Reading manifest: {manifest_url}")
    manifest = fetch_json(manifest_url)

    tag = manifest["release_tag"]
    expected_archive_sha = manifest["archive_sha256"]
    expected_archive_size = int(manifest["archive_size"])
    parts = manifest["parts"]
    if not parts:
        raise RuntimeError("manifest has no release parts")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    whole_hash = hashlib.sha256()
    total = 0

    with args.output.open("wb") as merged:
        for index, part in enumerate(parts, 1):
            name = part["name"]
            encoded_name = urllib.parse.quote(name)
            url = f"https://github.com/{args.repo}/releases/download/{tag}/{encoded_name}"
            print(f"[{index}/{len(parts)}] {name}")

            # Stream through a temporary file so the part checksum is verified before
            # bytes are admitted to the final archive.
            temp_path = args.output.parent / f".{name}.download"
            try:
                with temp_path.open("wb") as temp:
                    size, _ = stream_asset(url, temp, part["sha256"])
                if size != int(part["size"]):
                    raise RuntimeError(f"part size mismatch for {name}: {size} != {part['size']}")
                with temp_path.open("rb") as temp:
                    while True:
                        block = temp.read(8 * 1024 * 1024)
                        if not block:
                            break
                        merged.write(block)
                        whole_hash.update(block)
                        total += len(block)
            finally:
                temp_path.unlink(missing_ok=True)

    if total != expected_archive_size:
        raise RuntimeError(f"archive size mismatch: {total} != {expected_archive_size}")
    digest = whole_hash.hexdigest()
    if digest != expected_archive_sha:
        raise RuntimeError(f"archive checksum mismatch: {digest} != {expected_archive_sha}")

    print(f"Restored {args.output} ({total:,} bytes, sha256={digest})")

    if args.extract_to is not None:
        args.extract_to.mkdir(parents=True, exist_ok=True)
        print(f"Extracting to {args.extract_to}")
        with zipfile.ZipFile(args.output) as archive:
            archive.extractall(args.extract_to)
        print("Extraction complete")
        if args.delete_zip_after_extract:
            args.output.unlink()
            print(f"Deleted {args.output}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
