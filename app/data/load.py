"""Data related functions."""

import pandas as pd
from typing import TYPE_CHECKING

from paths import IMG_REF_RP

if TYPE_CHECKING:
    from classes.base import LabelsDataFrame, MatchesDataFrame

# * Instantiation


def load_from_files() -> tuple["MatchesDataFrame", "LabelsDataFrame"]:
    data = {
        "matches": pd.read_csv(f"{IMG_REF_RP}/matches.csv"),
        "labels": pd.read_csv(f"{IMG_REF_RP}/labels.csv"),
    }
    return (
        data["matches"].set_index("id", drop=True),
        data["labels"].set_index(["match_id", "player_id"], drop=True),
    )
