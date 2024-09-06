"""API related functions"""

import os

import pandas as pd
import requests
from constants import NO_KILLER_PERK, NO_SURV_PERK


def endp(endpoint: str) -> str:
    """Get full URL of the endpoint."""
    return f"{os.environ['FASTAPI_HOST']}/{endpoint}"


def clean_perks(perks_json: list[dict], is_for_killer: bool) -> pd.DataFrame:
    """Clean raw perks."""
    perks = pd.DataFrame(perks_json)

    mask = perks["name"] == (NO_KILLER_PERK if is_for_killer else NO_SURV_PERK)
    perks = pd.concat(
        (
            perks[mask],
            perks[~mask].sort_values("name", ignore_index=True),
        ),
        axis=0,
        ignore_index=True,
    )

    perks["emoji"] = perks["emoji"].fillna("❓")
    return perks


def cache_perks(is_for_killer: bool, local_fallback: bool) -> None:
    """Get perks from the API and cache."""
    path = f"app/cache/perks__{'killer' if is_for_killer else 'surv'}.csv"

    try:
        perks = requests.get(
            endp("/perks"),
            params={"is_for_killer": is_for_killer, "limit": 3000},
        )
        if perks.status_code != 200:
            raise AssertionError(perks.reason)
    except Exception as e:
        print("[WARNING] Problem with the API.")
        if not local_fallback:
            raise Exception(perks.reason) from e
        else:
            if os.path.exists(path):
                print("Using local data.")
                return
            else:
                print("[ERROR] Local data not found.")
                raise Exception(perks.reason) from e

    perks_json = perks.json()
    perks = clean_perks(perks_json, is_for_killer)

    perks.to_csv(path, index=False)


def upload_labels(labels) -> None:
    """Upload labels set by the user."""
    # TODO: Upload labels working code
    for player_id in range(4):
        min_id = 4 * player_id
        max_id = 4 * (player_id + 1)
        print(labels[min_id:max_id], end="\t")
    print()

    # for player_id in range(4):
    #     resp = requests.post(
    #         endp(f"/perks/{id}"),
    #         json={
    #             "fmts": ["perks__killer"],
    #             "filename": "FILENAME",  # TODO
    #         },
    #     )
    #     if resp.status_code != 201:
    #         raise Exception(resp.reason)

    print(20 * "-")
