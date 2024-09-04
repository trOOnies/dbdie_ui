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
