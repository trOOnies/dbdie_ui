"""API related functions."""

import os

from typing import TYPE_CHECKING
import pandas as pd
import requests
from constants import NO_KILLER_PERK, NO_SURV_PERK

if TYPE_CHECKING:
    from classes.labeler import SurvLabeler


def endp(endpoint: str) -> str:
    """Get full URL of the endpoint."""
    return f"{os.environ['FASTAPI_HOST']}/{endpoint}"


def parse_or_raise(resp, exp_status_code: int = 200):
    """Parse Response as JSON or raise error as exception, depending on status code."""
    if resp.status_code != exp_status_code:
        try:
            msg = resp.json()
        except requests.exceptions.JSONDecodeError:
            msg = resp.reason
        raise Exception(msg)
    return resp.json()


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


def upload_labels(surv_lbl: "SurvLabeler", labels: list[int]) -> None:
    """Upload labels set by the user."""
    if surv_lbl.current["labels"].to_list() != labels:
        print("LABELS WERE CHANGED")
        print(surv_lbl.current["labels"].to_list())
        print(labels)
        surv_lbl.update_current(labels)

    for player_id in range(4):
        min_id = 4 * player_id
        max_id = 4 * (player_id + 1)
        print(labels[min_id:max_id], end="\t")
    print()

    for player_id in range(4):
        min_id = 4 * player_id
        max_id = 4 * (player_id + 1)

        resp = requests.put(
            endp("/labels/filter"),
            params={
                "match_id": surv_lbl.current["match"]["id"],
                "player_id": player_id,
            },
            json=labels[min_id:max_id],
        )
        if resp.status_code != 200:
            try:
                msg = resp.json()
            except requests.exceptions.JSONDecodeError:
                msg = resp.reason
            raise Exception(msg)

    print(20 * "-")


def get_tc_info() -> dict[str, int]:
    """Get training corpus info.
    Nomenclature:
    - k Killer, s Survivor
    - p Pending, c Checked
    - t Total
    """
    # TODO: Change when migrated to FMT-dependent manual check
    total = 4 * parse_or_raise(
            requests.get(
            endp("/labels/count"),
        )
    )
    kp = 4 * parse_or_raise(
            requests.get(
            endp("/labels/count"),
            params={"is_killer": True},  # TODO: For now they are not checked
        )
    )
    sc = 4 * parse_or_raise(
            requests.get(
            endp("/labels/count"),
            params={"is_killer": False},
            json={
                "perks": True,  # TODO
            },
        )
    )

    sp = total - kp - sc

    return {
        "kp": kp,
        "kc": 0,
        "sp": sp,
        "sc": sc,
        "tp": sp + kp,
        "tc": sc + 0,
        "kt": kp,
        "st": sp + sc,
    }
