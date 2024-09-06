"""SurvLabeler class extra code."""

import pandas as pd
import requests
from api import endp


def get_matches_and_labels() -> tuple[list[dict], list[dict]]:
    matches = requests.get(endp("/matches"), params={"limit": 3000})
    if matches.status_code != 200:
        raise Exception(matches.reason)

    labels = requests.get(endp("/labels"), params={"limit": 3000})
    if labels.status_code != 200:
        raise Exception(labels.reason)

    matches = matches.json()
    labels = labels.json()
    return matches, labels


def process_matches(matches_json: list[dict]) -> pd.DataFrame:
    """Process matches' JSON and convert to DataFrame."""
    matches = pd.DataFrame(
        [{k: v for k, v in m.items() if k in ["id", "filename"]} for m in matches_json]
    )
    matches = matches.set_index("id", drop=True)
    return matches


def process_labels(labels_json: list[dict]) -> pd.DataFrame:
    """Process labels' JSON and convert to DataFrame."""
    labels = pd.DataFrame(
        [
            {k: v for k, v in lbl.items() if k in ["match_id", "player"]}
            for lbl in labels_json
        ]
    )

    labels["player_id"] = labels["player"].map(lambda pl: pl["id"])
    labels["perks"] = labels["player"].map(lambda pl: pl["perk_ids"])
    labels = labels[["match_id", "player_id", "perks"]]
    for i in range(4):
        labels[f"perk_{i}"] = labels["perks"].map(lambda ps: ps[i])
    labels = labels.drop("perks", axis=1)
    labels = labels[labels["player_id"] != 4]

    labels = labels.set_index(["match_id", "player_id"], drop=True)

    return labels


def calc_labels(
    labels: pd.DataFrame,
    current_id: int,
    perk_cols: list[str],
) -> dict:
    mask = labels.index.get_level_values(0) == current_id
    perks = labels[perk_cols][mask].apply(
        lambda row: [int(row[p]) for p in perk_cols],
        axis=1,
    )
    assert not perks.empty
    assert perks.size == 4
    return {i: p for i, p in enumerate(perks.values)}
