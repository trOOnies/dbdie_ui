"""Code for the extract data phase."""

import pandas as pd

from dbdie_classes.options.MODEL_TYPE import TO_ID_NAMES as MT_TO_ID_NAMES
from dbdie_classes.options.SQL_COLS import MANUALLY_CHECKED_COLS

from api import getr, postr
from paths import IMG_REF_RP


def get_matches_and_labels() -> tuple[list[dict], list[dict]]:
    """Get matches and labels from the API."""
    return (
        getr("/matches", params={"limit": 3_000}),
        postr("/labels/filter-many", params={"limit": 30_000}),
    )


def process_matches(matches_json: list[dict]) -> pd.DataFrame:
    """Process matches' JSON and convert to DataFrame."""
    matches = pd.DataFrame(
        [
            {k: v for k, v in m.items()
            if k in ["id", "filename", "match_date", "dbdv_id"]}
            for m in matches_json
        ]
    )
    assert not matches.empty

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
    assert not labels.empty

    labels["manual_checks"] = labels["manual_checks"].map(lambda v: v["predictables"])
    for c in MANUALLY_CHECKED_COLS:
        labels[c] = labels["manual_checks"].map(lambda v: v[c[:-5]])
    labels = labels.drop("manual_checks", axis=1)
    
    labels[MANUALLY_CHECKED_COLS] = labels[MANUALLY_CHECKED_COLS].fillna(False)

    # Extract info from player
    labels["player_id"] = labels["player"].map(lambda pl: pl["id"])
    for mt, id_name in MT_TO_ID_NAMES.items():
        labels[mt] = labels["player"].map(lambda pl: pl[id_name])
    labels = labels.drop("player", axis=1)

    for i in range(4):
        labels[f"perks_{i}"] = labels["perks"].map(lambda ps: ps[i] if ps is not None else None)
    labels = labels.drop("perks", axis=1)

    for i in range(2):
        labels[f"addons_{i}"] = labels["addons"].map(lambda ps: ps[i] if ps is not None else None)
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
