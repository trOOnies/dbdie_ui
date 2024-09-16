import requests
import pandas as pd

from api import endp
from paths import IMG_REF_RP
from options.MODEL_TYPES import ALL_MULTIPLE_CHOICE as ALL_MT

MANUALLY_CHECKED_COLS = [f"{fmt}_mckd" for fmt in ALL_MT]


def get_matches_and_labels() -> tuple[list[dict], list[dict]]:
    """Get matches and labels from the API."""
    matches = requests.get(endp("/matches"), params={"limit": 3000})
    if matches.status_code != 200:
        raise Exception(matches.reason)

    labels = requests.get(endp("/labels"), params={"limit": 3000})
    if labels.status_code != 200:
        raise Exception(labels.reason)

    return matches.json(), labels.json()


def process_matches(matches_json: list[dict]) -> pd.DataFrame:
    """Process matches' JSON and convert to DataFrame."""
    matches = pd.DataFrame(
        [
            {k: v for k, v in m.items() if k in ["id", "filename", "match_date", "dbd_version"]}
            for m in matches_json
        ]
    )

    matches["dbd_version_id"] = matches["dbd_version"].map(lambda v: v["id"])
    matches["dbd_version"] = matches["dbd_version"].map(lambda v: v["name"])

    matches = matches.sort_values("id")
    matches = matches.set_index("id", drop=True)
    return matches


def process_labels(labels_json: list[dict]) -> pd.DataFrame:
    """Process labels' JSON and convert to DataFrame."""
    labels = pd.DataFrame(
        [
            {k: v for k, v in lbl.items() if k in ["match_id", "player", "manual_checks"]}
            for lbl in labels_json
        ]
    )

    labels["manual_checks"] = labels["manual_checks"].map(lambda v: v["predictables"])
    for c in MANUALLY_CHECKED_COLS:
        labels[c] = labels["manual_checks"].map(lambda v: v[c[:-5]])
    labels = labels.drop("manual_checks", axis=1)
    
    labels[MANUALLY_CHECKED_COLS] = labels[MANUALLY_CHECKED_COLS].fillna(False)

    # Extract info from player
    labels["player_id"] = labels["player"].map(lambda pl: pl["id"])
    labels["character"] = labels["player"].map(lambda pl: pl["character_id"])
    labels["perks"] = labels["player"].map(lambda pl: pl["perk_ids"])
    labels["item"] = labels["player"].map(lambda pl: pl["item_id"])
    labels["addons"] = labels["player"].map(lambda pl: pl["addon_ids"])
    labels["offering"] = labels["player"].map(lambda pl: pl["offering_id"])
    labels["status"] = labels["player"].map(lambda pl: pl["status_id"])
    labels["points"] = labels["player"].map(lambda pl: pl["points"])
    labels["prestige"] = labels["player"].map(lambda pl: pl["prestige"])
    labels = labels.drop("player", axis=1)

    for i in range(4):
        labels[f"perk_{i}"] = labels["perks"].map(lambda ps: ps[i] if ps is not None else None)
    labels = labels.drop("perks", axis=1)

    for i in range(2):
        labels[f"addon_{i}"] = labels["addons"].map(lambda ps: ps[i] if ps is not None else None)
    labels = labels.drop("addons", axis=1)

    labels = labels.sort_values(["match_id", "player_id"])
    labels = labels.set_index(["match_id", "player_id"], drop=True)

    return labels


def split_killer_surv(labels: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split labels df and return killer and surv labels dfs."""
    mask = labels["player_id"] == 4
    return labels[mask], labels[~mask]


# * Main function


def extract_from_api() -> None:
    """Extract data from DBDIE API."""
    print("Getting data... ", end="")

    try:
        matches_json, labels_json = get_matches_and_labels()

        matches = process_matches(matches_json)
        labels = process_labels(labels_json)

        matches.to_csv(f"{IMG_REF_RP}/matches.csv", index=True)
        labels.to_csv(f"{IMG_REF_RP}/labels.csv", index=True)
    except Exception:
        print()
        raise

    print("✅")
