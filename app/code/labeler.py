"""Labeler class extra code."""

import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import DataFrame

PERK_COLS = ["perk_0", "perk_1", "perk_2", "perk_3"]

# * Current pointer management


def update_current(lbl, update_match: bool) -> pd.DataFrame:
    """Update current information."""
    ptrs = lbl.pending[lbl._ptr_min:lbl._ptr_max]

    c_labels: DataFrame = lbl.labels.iloc[ptrs, lbl.column_ixs]

    # Labels info
    labels = sum(([row[c] for c in lbl.columns] for _, row in c_labels.iterrows()), [])
    players = sum(
        (
            [pl_id for _ in lbl.columns]
            for pl_id in c_labels.index.get_level_values(1).values
        ),
        [],
    )

    # Match info
    m_cols = ["filename", "match_date", "dbd_version"]
    m_cols_ext = ["id"] + m_cols
    if update_match:
        match_ids = sum(
            ([mid for _ in lbl.columns] for mid in c_labels.index.get_level_values(0).values),
            [],
        )
        c_matches: DataFrame = lbl.matches[m_cols].loc[match_ids]
        c_matches = c_matches.reset_index(drop=False)
        c_matches = c_matches.rename({c: f"m_{c}" for c in m_cols_ext}, axis=1)
    else:
        c_matches = lbl.current[[f"m_{c}" for c in m_cols_ext]]

    return pd.concat(
        (
            c_matches,
            pd.Series(labels, name="label_id"),
            pd.Series(players, name="player_id"),
            lbl.current["item_id"],
        ),
        axis=1,
    )
