"""Labeler class extra code."""

from dbdie_classes.options.NULL_IDS import BY_MT as NULL_IDS_BY_MT
from dbdie_classes.options.NULL_IDS import INT_IDS as NULL_INT_IDS
from dbdie_classes.options.SQL_COLS import MT_TO_COLS
import numpy as np
import pandas as pd
from typing import TYPE_CHECKING, Optional

from paths import load_predictable_csv

if TYPE_CHECKING:
    from dbdie_classes.base import (
        FullModelType,
        IsForKiller,
        LabelsDataFrame,
        LabelId,
        LabelName,
        ModelType,
        PlayerId,
    )

    from classes.base import CurrentDataFrame

TOTAL_CELLS = 16

# * Current pointer management


def init_cols(
    mt: "ModelType",
    labels: pd.DataFrame,
) -> tuple[list[str], list[int]]:
    """Initialize model type's relevant columns and their column indices."""
    columns = MT_TO_COLS[mt]
    cols = labels.columns.to_list()
    return columns, [cols.index(c) for c in columns]


def init_dims(columns: list[str]) -> tuple[int, int, int]:
    """Initialize labeling dimensions."""
    n_items = len(columns)
    assert TOTAL_CELLS % n_items == 0, "Total cells must be a multiple of n_items"
    return TOTAL_CELLS, int(TOTAL_CELLS / n_items), n_items


def init_current(
    total_cells: int,
    n_items: int,
    mt: "ModelType",
    ifk: "IsForKiller",
) -> tuple["CurrentDataFrame", "LabelId", "LabelName"]:
    """Initialize current information. Also return fmt's null id."""
    null_id = NULL_INT_IDS[mt][int(ifk)]

    minus_one_vals = np.full(total_cells, -1)
    empty_str_vals = np.full(total_cells, "")
    return (
        pd.DataFrame(
            {
                "m_id": np.copy(minus_one_vals),
                "m_filename": np.copy(empty_str_vals),
                "m_match_date": np.copy(empty_str_vals),
                "m_dbdv_id": np.copy(minus_one_vals),
                "label_id": np.full(total_cells, null_id),
                "player_id": np.copy(minus_one_vals),
                "item_id": np.fromiter(
                    ((i % n_items) for i in range(total_cells)),
                    dtype=int,
                ),
            }
        ),
        null_id,
        (
            NULL_IDS_BY_MT[mt][int(ifk)]
            if len(NULL_IDS_BY_MT[mt]) == 2
            else NULL_IDS_BY_MT[mt][0]
        ),
    )


def init_pending(
    labels: pd.DataFrame,
    mt: "ModelType",
    ifk: "IsForKiller",
) -> tuple[np.ndarray, int]:
    """Initiate pending array.

    pending: Integer (0-based) indexes that haven't been labeled yet.
        Note that this is a label-based row index. Each row can point
        to one or more pending labels (depending on the FMT).
    total: Total label rows that should be labeled (completed yet or not).

    pending can go from 0 to total.
    If pending is 0, labeling was totally completed (though the 'done'
        condition depends on allowing partial labeling or not).
    """
    pt_mask = labels.index.get_level_values(1) == 4
    if not ifk:
        pt_mask = np.logical_not(pt_mask)
    mask = np.logical_and(pt_mask, ~labels[f"{mt}_mckd"])
    return np.nonzero(mask)[0], int(pt_mask.sum())


# * Smaller functions


def process_labels_and_players(
    lbl,
    current_labels: pd.DataFrame,
) -> tuple[list[Optional["LabelId"]], list["PlayerId"]]:
    """Process labels and players function for 'update_current'."""
    return (
        sum(
            (
                [row[c] for c in lbl.columns]
                for _, row in current_labels.iterrows()
            ),
            [],
        ),
        sum(
            (
                [pl_id for _ in lbl.columns]
                for pl_id in current_labels.index.get_level_values(1).values
            ),
            [],
        )
    )


def process_matches(
    lbl,
    current_labels: pd.DataFrame,
    update_match: bool,
) -> pd.DataFrame:
    """Process matches function for 'update_current'."""
    m_cols = ["filename", "match_date", "dbdv_id"]
    m_cols_ext = ["id"] + m_cols

    if update_match:
        match_ids = sum(
            (
                [mid for _ in lbl.columns]
                for mid in current_labels.index.get_level_values(0).values
            ),
            [],
        )
        c_matches: pd.DataFrame = lbl.matches[m_cols].loc[match_ids]
        c_matches = c_matches.reset_index(drop=False)
        c_matches = c_matches.rename({c: f"m_{c}" for c in m_cols_ext}, axis=1)
    else:
        c_matches = lbl.current[[f"m_{c}" for c in m_cols_ext]]

    return c_matches


# * Functions


def update_current(lbl, update_match: bool) -> "CurrentDataFrame":
    """Update current information."""
    ptrs = lbl.pending[lbl.counts.ptr_min:lbl.counts.ptr_max]
    c_labels: pd.DataFrame = lbl.labels.iloc[ptrs, lbl.column_ixs]

    labels, players = process_labels_and_players(lbl, c_labels)
    c_matches = process_matches(lbl, c_labels, update_match)

    return pd.concat(
        (
            c_matches,
            pd.Series(labels, name="label_id").fillna(lbl.null_id).astype(int),
            pd.Series(players, name="player_id"),
            lbl.current["item_id"],
        ),
        axis=1,
    )


# * Other predictables


def prefilter_data(
    labels: "LabelsDataFrame",
    mt: "ModelType",
    ifk: "IsForKiller",
) -> pd.Series:
    """Filter data so as to make the index filtering more efficient."""
    if ifk is None:
        return labels[mt]
    else:
        mask_ifk = labels.index.get_level_values(1) == 4
        if not ifk:
            mask_ifk = np.logical_not(mask_ifk)
        return labels[mt][mask_ifk]


def filter_data(data: pd.Series, current: "CurrentDataFrame") -> pd.Series:
    keys = current[["m_id", "player_id"]].apply(
        lambda row: (row["m_id"], row["player_id"]),
        axis=1,
    )
    result = data.loc[keys]
    return result.astype(int)


def merge_with_types(
    result: pd.Series,
    types: bool,
    fmt: "FullModelType",
    mt: "ModelType",
) -> pd.Series:
    if types:
        df_types, _ = load_predictable_csv(fmt, usecols=["id", "type_id"])
        df_types = df_types.rename({"id": mt}, axis=1)
        result = pd.merge(result, df_types, how="left", on=mt)
        result = result.drop(mt, axis=1)
        result = result.rename({"type_id": mt}, axis=1)
        result = result[mt]
    return result
