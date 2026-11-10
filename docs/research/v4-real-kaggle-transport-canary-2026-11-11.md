# V4 real Kaggle transport verification — 2026-11-11

## Outcome

The production V4 submission script's prior mock-only tests **incorrectly rejected a successful real Kaggle SDK push**. Fixed using the exact authenticated `ApiSaveKernelResponse` field shape. The private CPU Notebook **version 2 completed and yielded byte-identical output**; this is genuine Kaggle backend/CLI/SDK transport evidence, **not** an official competition result or 31B issue resolution.

## Read-only reproducible evidence

1. [First authenticated live push, Actions 42873135847](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42873135847): `KaggleApi.kernels_push()` returned, but our own `verified_kernel_version()` rejected the response. This did **not** consume a competition submission. It created a private CPU test Notebook, not a 31B GPU run.
2. [Targeted SDK response-shape diagnosis, Actions 42873480975](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42873480975): the server returned `versionNumber=2`, `version_number=2`, `ref="/code/kolihhan/gemma4-v4-cpu-transport-canary-20261111"`, `url="https://www.kaggle.com/code/kolihhan/gemma4-v4-cpu-transport-canary-20261111"`, and no error. The old client code only accepted `ref="kolihhan/slug"` and rejected an otherwise valid response.
3. **Exact fix:** `verified_kernel_version()` now accepts both `owner/slug` and `/code/owner/slug` **for the exact expected Notebook only**; it still rejects unknown slugs, invalid URLs, conflicting version numbers and server errors. Regression tests use the actual server response shape.
4. [Read-only actual version-2 recovery, Actions 42873814625](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42873814625) **SUCCESS**: reran three version/identity tests, pulled the actual private Notebook source by pinned `/2`, confirmed Kaggle `KernelWorkerStatus.COMPLETE`, downloaded its output, verified the exact expected bytes (SHA-256 `520704ab16621298f85cb83efcd76c2a7fb594743dfd5211ca921448e9905ae5`). This last readback performed **no additional push, competition submission, GPU or Gemma inference**.

## Implications and limits

- This is an independently observed runtime-transport correction. Mocked server returns were not faithful to real `ref`; unit tests and official scripted ADK CPU preflight alone did not catch it.
- Real CPU transport evidence covers **push → server version return → status → versioned source/output → byte verification** across the two actual private CPU Notebook versions. It does **not** cover the competition-specific `competition_submit_code` acceptance or full hidden scoring.
- Model agent ZIP SHA is still **`5015ae18d03c1aca2e708e749e2f49b8da17ea49b7eb5c14f850558c3110c8be`**. Do not claim V4 improves the Public score (best `0.18`, ID `58183466`).
- Maintain exactly one authorized manual `workflow_dispatch` after authenticating available competition quota; never schedule or bypass the gate. Recheck actual GitHub main workflow pinned source SHA after final compiler preflight, and capture a real Kaggle official receipt before claiming submission.
