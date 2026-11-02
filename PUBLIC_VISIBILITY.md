# Public Visibility Gate

**Status: UNSAFE — REPOSITORY IS CURRENTLY PUBLIC. RETURN TO PRIVATE BEFORE CONTINUING PUBLIC-SAFE CLEANUP.**

Last verified: 2026-11-02.

This file is a repository-wide safety gate. It is not an experiment decision and must not be weakened to save GitHub Actions minutes.

## Immediate incident state

On 2026-11-02 the repository was verified as `public` while the full Competition Data Release tagged `kaggle-data-2026-10-31` was still present and publicly readable through GitHub's Release API.

**Immediate required action:** change repository visibility back to `private` before continuing cleanup. Making the repository private again does not erase the fact that the Release was temporarily public; it only stops continuing exposure while cleanup is performed.

## Why public visibility is unsafe

### 1. Full Kaggle Competition Data exists in a GitHub Release

The repository has a Release mirror tagged `kaggle-data-2026-10-31` containing the full Gemma 4 competition archive split into large assets.

The Kaggle competition rules require reasonable measures to prevent non-participants from accessing Competition Data and prohibit transmitting, duplicating, publishing, redistributing, or otherwise making Competition Data available to non-participants.

Official rules:

- https://www.kaggle.com/competitions/gemma-4-developer-agent/rules

### 2. Public Competition Code has an additional Kaggle sharing requirement

The competition rules permit public Competition Code sharing only under the competition's public-sharing conditions. During the competition, public code sharing must also be made available through the competition's Kaggle forum or associated public notebooks, subject to the rule text in force at the time of publication.

Do not assume that making this GitHub repository public by itself satisfies that requirement.

### 3. Historical repository state still needs a final exposure audit

Before public visibility is enabled again, verify that reachable Git history, Releases, workflow artifacts intended to persist, and other repository-hosted assets contain no Competition Data or other material that cannot be publicly redistributed.

## Existing guard

`.github/workflows/mirror-full-kaggle-data.yml` fails closed when `github.event.repository.private` is not `true`.

Keep that guard. Do not weaken or remove it while this gate is active.

## Readiness checklist

The repository may be marked `READY` for public visibility only after all of the following are verified:

- [ ] Repository visibility has first been returned to `private` while cleanup is performed.
- [ ] Delete the full Competition Data GitHub Release/assets, including tag `kaggle-data-2026-10-31` or any replacement raw-data mirror.
- [ ] Verify no raw Competition Data is reachable through Git history or other persistent repository assets.
- [ ] Verify workflows cannot publish/mirror Competition Data after the repository becomes public.
- [ ] Verify repository secrets remain referenced only through GitHub Secrets and are not present in files/history/logs.
- [ ] Satisfy the current Kaggle rule for public Competition Code sharing, including any required Kaggle forum/notebook publication.
- [ ] Re-check the current official competition Rules immediately before changing visibility.
- [ ] Update this file from `UNSAFE` to `READY` with dated verification evidence.

## Agent instruction

If your task involves repository visibility, GitHub Actions billing, data mirroring, Releases, or public sharing:

1. read this file first;
2. treat `UNSAFE` as a hard stop on further public exposure;
3. do not claim this repository is public-safe;
4. do not delete Release assets or rewrite history unless the user explicitly authorizes that destructive cleanup;
5. keep scientific experiment state independent from this infrastructure cleanup.

Saving Actions minutes is not sufficient reason to bypass this gate.
