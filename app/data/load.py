"""Data related functions."""

import pandas as pd

from paths import IMG_REF_RP

# * Instantiation


def load_from_files() -> tuple[pd.DataFrame, pd.DataFrame]:
    data = {
        "matches": pd.read_csv(f"{IMG_REF_RP}/matches.csv"),
        "labels": pd.read_csv(f"{IMG_REF_RP}/labels.csv"),
    }
    return (
        data["matches"].set_index("id", drop=True),
        data["labels"].set_index(["match_id", "player_id"], drop=True),
    )
