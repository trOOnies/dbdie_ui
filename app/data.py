"""Data related functions"""

import pandas as pd


def load_perks() -> list[tuple[str, int]]:
    perks = pd.read_csv("app/cache/perks.csv", usecols=["emoji", "name", "id"])

    perks = pd.concat(
        (
            pd.DataFrame(perks.iloc[0, :]).T,
            perks.iloc[1:, :].sort_values("name"),
        ),
        axis=0,
        ignore_index=True,
    )

    perks["emoji"] = perks["emoji"].fillna("❓")
    perks = perks.apply(
        lambda row: (f"{row['emoji']} {row['name']}", row["id"]),
        axis=1,
    )
    perks = perks.to_list()
    return perks
