# Gemma 4 Kaggle workspace

Repository for **Google - The Gemma 4 Developer Agent Competition**.

## Data layout

Small text artifacts stay in normal Git:

- `tasks.jsonl` — 129 public development tasks
- `HARNESS_README.md` — official harness guide
- `manifests/` — produced by the full-data mirror workflow

The complete competition input is roughly 22+ GB, so it is **not committed as ordinary Git blobs**. GitHub rejects ordinary files over 100 MiB and recommends keeping repositories far smaller than this dataset. The full raw Kaggle archive is therefore mirrored into this repository's **GitHub Releases**, split into parts under 2 GiB each. A manifest records every part's size and SHA-256 plus the checksum of the reconstructed original archive.

Expected competition data includes `docker/`, `embeddings/`, `graphs/`, `sample_submission/`, `sandbox/`, `snapshots/`, `wheels/`, `HARNESS_README.md`, and `tasks.jsonl`.

## Mirror the complete official data

The workflow is `.github/workflows/mirror-full-kaggle-data.yml`.

Prerequisites:

1. Join the Kaggle competition and accept its rules.
2. Generate a Kaggle API token.
3. Add it to this repository as an Actions secret named `KAGGLE_API_TOKEN`.
4. Run **Mirror full Gemma 4 Kaggle data** from GitHub Actions.

The job streams Kaggle's official `download-all` response directly into GitHub Release parts. It never needs to keep the complete ~22 GB archive on the Actions runner.

Successful completion writes:

- `manifests/latest.json`
- `manifests/kaggle-files.csv`
- `manifests/kaggle-data-YYYY-MM-DD.json`
- a release named `kaggle-data-YYYY-MM-DD` containing all archive parts

## Restore everything locally

```bash
python scripts/restore_full_dataset.py --extract-to data --delete-zip-after-extract
```

The restore script downloads every release part, validates each SHA-256, reconstructs the exact original competition zip, validates the whole-archive checksum, and then extracts it to `data/`.

Large restored files are intentionally ignored by `.gitignore` so they cannot accidentally be committed back into normal Git history.
