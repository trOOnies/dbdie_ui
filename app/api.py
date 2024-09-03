import os
import pandas as pd
import requests


def endp(endpoint: str) -> str:
    """Get full URL of the endpoint"""
    return f"{os.environ['FASTAPI_HOST']}/{endpoint}"


def cache_perks() -> None:
    perks = requests.get(endp("/perks"), params={"limit": 3000})
    if perks.status_code != 200:
        raise Exception(perks.detail)
    perks = perks.json()

    perks = pd.DataFrame(perks)
    perks.to_csv("app/cache/perks.csv", index=False)
