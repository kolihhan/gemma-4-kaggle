#!/usr/bin/env python3
"""Restore the full Gemma 4 Kaggle dataset from private GitHub Release parts."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_REPO = "kolihhan/gemma-4-kaggle"
DEFAULT_BRANCH = "main"
DEFAULT_MANIFEST = "manifests/latest.json"
GITHUB_API = "https://api.github.com"


def discover_github_token() -> str | None:
    """Use an explicit environment token, or reuse the local gh CLI login."""
    token = (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or "").strip()
    if token:
        return token
    if shutil.which("gh"):
        probe = subprocess.run(
            ["gh", "auth", "token"],
            check=False,
            text=True,
            capture_output=True,
        )
        if probe.returncode == 0 and probe.stdout.strip():
            return probe.stdout.strip()
    return None


def github_request(url: str, token: str | None, *, accept: str) -> urllib.request.Request:
    headers = {
        "Accept": accept,
        "User-Agent": "kolihhan-gemma-4-kaggle-restore/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def fetch_json(url: str, token: str | None) -> dict:
    request = github_request(url, token, accept="application/vnd.github+json")
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403, 404) and not token:
            raise RuntimeError(
                "GitHub authentication is required for this private repository. "
                "Run `gh auth login` or set GH_TOKEN/GITHUB_TOKEN."
            ) from exc
        raise


def fetch_manifest(repo: str, branch: str, path: str, token: str | None) -> dict:
    encoded_path = urllib.parse.quote(path, safe="/")
    encoded_ref = urllib.parse.quote(branch, safe="")
    url = f"{GITHUB_API}/repos/{repo}/contents/{encoded_path}?ref={encoded_ref}"
    payload = fetch_json(url, token)
    if payload.get("encoding") != "base64" or "content" not in payload:
        raise RuntimeError(f"unexpected GitHub Contents response for {path}")
    raw = base64.b64decode(payload["content"])
    return json.loads(raw.decode("utf-8"))


def release_assets(repo: str, tag: str, token: str | None) -> dict[str, str]:
    encoded_tag = urllib.parse.quote(tag, safe="")
    url = f"{GITHUB_API}/repos/{repo}/releases/tags/{encoded_tag}"
    payload = fetch_json(url, token)
    assets = payload.get("assets", [])
    return {asset["name"]: asset["url"] for asset in assets if asset.get("name") and asset.get("url")}


def stream_asset(url: str, output, expected_sha256: str, token: str | None) -> tuple[int, str]:
    hasher = hashlib.sha256()
    total = 0
    request = github_request(url, token, accept="application/octet-stream")
    with urllib.request.urlopen(request) as response:
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

    token = discover_github_token()
    print(f"Reading manifest from {args.repo}:{args.branch}/{args.manifest}")
    manifest = fetch_manifest(args.repo, args.branch, args.manifest, token)

    tag = manifest["release_tag"]
    expected_archive_sha = manifest["archive_sha256"]
    expected_archive_size = int(manifest["archive_size"])
    parts = manifest["parts"]
    if not parts:
        raise RuntimeError("manifest has no release parts")

    assets = release_assets(args.repo, tag, token)
    missing_assets = [part["name"] for part in parts if part["name"] not in assets]
    if missing_assets:
        raise RuntimeError(f"release is missing {len(missing_assets)} part(s): {missing_assets[:5]}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    whole_hash = hashlib.sha256()
    total = 0

    with args.output.open("wb") as merged:
        for index, part in enumerate(parts, 1):
            name = part["name"]
            print(f"[{index}/{len(parts)}] {name}")

            # Verify each private Release asset before admitting its bytes to the
            # reconstructed archive.
            temp_path = args.output.parent / f".{name}.download"
            try:
                with temp_path.open("wb") as temp:
                    size, _ = stream_asset(assets[name], temp, part["sha256"], token)
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
