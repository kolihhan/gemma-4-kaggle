"""Fail-closed one-shot launch guard, using authenticated SDK responses.

Never infer absence from CLI text, arbitrary errors, or an unavailable listing.
Use a known existing notebook in the same owner account as a positive control.
"""
from __future__ import annotations

KNOWN = "kolihhan/gemma4-fork-v1-paired-20261127"


def _refs(api, target):
    slug = target.split("/", 1)[1]
    response = api.kernels_list_with_response(mine=True, search=slug, page=1, page_size=100)
    if response is None:
        raise RuntimeError("owner listing unavailable")
    rows = response.kernels
    if not isinstance(rows, list) or response.next_page_token or len(rows) >= 100:
        raise RuntimeError("owner listing incomplete")
    refs = [getattr(row, "ref", None) for row in rows]
    if any(not isinstance(ref, str) or "/" not in ref for ref in refs):
        raise RuntimeError("owner listing malformed")
    return [ref.lower() for ref in refs]


def verify_absent(api, target, known=KNOWN):
    target = target.lower()
    known = known.lower()
    if target == known or target.split("/", 1)[0] != known.split("/", 1)[0]:
        raise ValueError("candidate and positive control must be distinct, same owner")
    if known not in _refs(api, known):
        raise RuntimeError("known owner notebook not found: authentication/search unverified")
    if str(api.kernels_status(known).status) != "KernelWorkerStatus.COMPLETE":
        raise RuntimeError("known notebook status unverified")
    try:
        api.kernels_status(target)
    except ValueError as exc:
        # SDK 2.2.5 translates 401/403 into this ValueError; not absence alone.
        if not str(exc).startswith(f"Cannot access kernel '{target}' (Permission 'kernels.get' was denied)."):
            raise
    else:
        raise RuntimeError("candidate status exists: duplicate launch refused")
    if target in _refs(api, target):
        raise RuntimeError("candidate exists in owner listing: duplicate launch refused")
    return {"positive_control": True, "owner_listing_complete": True,
            "exact_ref_found": False, "status_permission_denied": True}


if __name__ == "__main__":
    import json
    import sys
    from importlib.metadata import version
    from kaggle.api.kaggle_api_extended import KaggleApi

    if version("kaggle") != "2.2.5":
        raise RuntimeError("unexpected Kaggle SDK version")
    api = KaggleApi()
    api.authenticate()
    result = verify_absent(api, sys.argv[1])
    print("CORE6_ABSENCE_VERIFIED=" + json.dumps(result, sort_keys=True), flush=True)
