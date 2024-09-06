"""Data related functions."""

import pandas as pd

# TODO: Matches and perks load functions, with pre-ordering


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
