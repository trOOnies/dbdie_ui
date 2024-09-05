"""API related functions"""

import os

import pandas as pd
import requests


def endp(endpoint: str) -> str:
    """Get full URL of the endpoint"""
    return f"{os.environ['FASTAPI_HOST']}/{endpoint}"


def cache_perks(local_fallback: bool) -> None:
    path = "app/cache/perks.csv"
    try:
        perks = requests.get(endp("/perks"), params={"limit": 3000})
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

    perks = perks.json()

    perks = pd.DataFrame(perks)
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
