"""API related functions."""

import os

import pandas as pd
import requests
from typing import TYPE_CHECKING

from constants import NO_KILLER_PERK, NO_SURV_PERK
from options.MODEL_TYPES import MT_TO_SCHEMA_ATTR

if TYPE_CHECKING:
    from classes.base import LabelId, ModelType
    from classes.labeler import Labeler


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

    if "emoji" in perks.columns.values:
        perks["emoji"] = perks["emoji"].fillna("❓")

    return perks


def cache_function(mt: "ModelType", is_for_killer: bool, clean_f, local_fallback: bool) -> None:
    """Get predictables from the API and cache."""
    path = f"app/cache/predictables/{mt}__{'killer' if is_for_killer else 'surv'}.csv"

    try:
        ifk_key = "is_killer" if mt == "character" else "is_for_killer"
        items = requests.get(
            endp(f"/{mt}"),
            params={ifk_key: is_for_killer, "limit": 10_000},
        )
        if items.status_code != 200:
            raise AssertionError(items.reason)
    except Exception as e:
        print("[WARNING] Problem with the API.")
        if not local_fallback:
            raise Exception(items.reason) from e
        else:
            if os.path.exists(path):
                print("Using local data.")
                return
            else:
                print("[ERROR] Local data not found.")
                raise Exception(items.reason) from e

    items_json = items.json()
    items = clean_f(items_json, is_for_killer)

    items.to_csv(path, index=False)


def upload_labels(labeler: "Labeler", labels: list["LabelId"]) -> None:
    """Upload labels set by the user."""
    if labeler.current["label_id"].to_list() != labels:
        print("LABELS WERE CHANGED")
        print(labeler.current["label_id"].to_list())
        print(labels)
        labeler.update_current(labels)

    labels_wrapped = labeler.wrap(labels)

    for player_ix in range(labeler.n_players):
        match_id, player_id = labeler.get_key(player_ix)
        player_labels = labels_wrapped[player_ix].tolist()
        player_labels = (
            int(player_labels[0])
            if len(player_labels) == 1
            else [int(v) for v in player_labels]
        )

        resp = requests.put(
            endp("/labels/predictable"),
            params={"match_id": match_id, "strict": True},
            json={
                "id": player_id,
                MT_TO_SCHEMA_ATTR[labeler.mt]: player_labels,
            },
        )
        if resp.status_code != 200:
            try:
                msg = resp.json()
            except requests.exceptions.JSONDecodeError:
                msg = resp.reason
            raise Exception(msg)


def get_tc_info() -> dict[str, int]:
    """Get training corpus info.
    Nomenclature:
    - k Killer, s Survivor
    - p Pending, c Checked
    - t Total
    """
    # TODO: Change when migrated to FMT-dependent manual check
    counts = {
        "kc": parse_or_raise(
            requests.get(
                endp("/labels/count"),
                params={"is_killer": True},
                json={"perks": True},
            )
        ),
        "kp": parse_or_raise(
            requests.get(
                endp("/labels/count"),
                params={"is_killer": True},
                json={"perks": False},
            )
        ),
        "sc": parse_or_raise(
            requests.get(
                endp("/labels/count"),
                params={"is_killer": False},
                json={"perks": True},
            )
        ),
        "sp": parse_or_raise(
            requests.get(
                endp("/labels/count"),
                params={"is_killer": False},
                json={"perks": False},
            )
        ),
    }
    counts = {k: 4 * v for k, v in counts.items()}
    counts = counts | {
        "kt": counts["kc"] + counts["kp"],
        "st": counts["sc"] + counts["sp"],
        "tc": counts["kc"] + counts["sc"],
        "tp": counts["kp"] + counts["sp"],
    }

    return counts
