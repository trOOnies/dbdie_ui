"""Data related functions."""

import pandas as pd

from paths import IMG_REF_RP


def load_perks(is_for_killer: bool) -> list[tuple[str, int]]:
    """Load perks from the cache."""
    kind = "killer" if is_for_killer else "surv"
    perks = pd.read_csv(f"app/cache/perks__{kind}.csv", usecols=["emoji", "name", "id"])
    perks = perks.apply(
        lambda row: (f"{row['emoji']} {row['name']}", row["id"]),
        axis=1,
    )
    perks = perks.to_list()
    return perks


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
