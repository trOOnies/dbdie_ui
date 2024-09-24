"""Labeler class extra code."""

from dbdie_classes.options import MODEL_TYPE as MT
from dbdie_classes.options import PLAYER_TYPE as PT
from dbdie_classes.options.FMT import to_fmt
from dbdie_classes.options.NULL_IDS import BY_MODEL_TYPE as NULL_IDS_BY_MT
from dbdie_classes.options.NULL_IDS import INT_IDS as NULL_INT_IDS
from dbdie_classes.options.NULL_IDS import mt_is_null
from dbdie_classes.options.SQL_COLS import MT_TO_COLS
import numpy as np
import pandas as pd
from typing import TYPE_CHECKING

from paths import load_predictable_csv, load_types_csv

if TYPE_CHECKING:
    from dbdie_classes.base import (
        FullModelType,
        IsForKiller,
        LabelId,
        ModelType,
        PlayerId,
        PlayerType,
    )

    from classes.base import CurrentDataFrame
    from classes.gradio import OptionsList

TOTAL_CELLS = 16

MOST_USED = {
    MT.ITEM: {
        PT.SURV: [
            "Flashlight",
            "Sport Flashlight",
            "Utility Flashlight",
            "Camping Aid Kit",
            "First Aid Kit",
            "Emergency Med-Kit",
            "Ranger Med-Kit",
            "Worn-Out Tools",
            "Toolbox",
            "Commodious Toolbox",
            "Mechanic's Toolbox",
            "Alex's Toolbox",
            "Engineer's Toolbox",
        ],
    },
    MT.OFFERING: {
        PT.KILLER: [
            "Survivor Pudding",
            "Bloody Party Streamers",
            "Putrid Oak",
            "Annotated Blueprint",
            "Bloodied Blueprint",
            "Torn Blueprint",
            "Vigo's Blueprint",
            "Cypress Memento Mori",
            "Ivory Memento Mori",
            "Ebony Memento Mori",
            "Black Ward",
        ],
        PT.SURV: [
            "Bound Envelope",
            "Escape! Cake",
            "Bloody Party Streamers",
            "Sealed Envelope",
            "Petrified Oak",
            "Annotated Blueprint",
            "Bloodied Blueprint",
            "Torn Blueprint",
            "Vigo's Blueprint",
        ],
    },
}


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
    return (
        TOTAL_CELLS,
        int(TOTAL_CELLS / n_items),
        n_items,
    )


def init_current(
    total_cells: int,
    n_items: int,
    mt: "ModelType",
    ifk: "IsForKiller",
) -> tuple["CurrentDataFrame", "LabelId"]:
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
                "m_dbd_version": np.copy(empty_str_vals),
                "label_id": np.full(total_cells, null_id),
                "player_id": np.copy(minus_one_vals),
                "item_id": np.fromiter(
                    ((i % n_items) for i in range(total_cells)),
                    dtype=int,
                ),
            }
        ),
        null_id,
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
) -> tuple[list["LabelId" | None], list["PlayerId"]]:
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
    m_cols = ["filename", "match_date", "dbd_version"]
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


def filter_nulls(
    options: pd.DataFrame,
    mt: "ModelType",
    ifk: "IsForKiller",
) -> tuple[pd.DataFrame, str]:
    """Filter special LabelIds that represent nulls."""
    mt_null_col = NULL_IDS_BY_MT[mt][int(ifk)]
    mt_wrong_null_col = NULL_IDS_BY_MT[mt][1 - int(ifk)]
    options = options[options["name"] != mt_wrong_null_col]
    return options, mt_null_col


def add_types(options: pd.DataFrame, mt: "ModelType") -> pd.DataFrame:
    """Add item types to the 'options' DataFrame."""
    options_types, _ = load_types_csv(mt, usecols=["id", "emoji", "is_for_killer"])
    options_types.columns = ["type_id", "emoji", "is_for_killer"]
    return pd.merge(options, options_types, how="left", on="type_id")


def base_options(options: pd.DataFrame, labeler) -> "OptionsList":
    """Get base options, provided that there is no defined correlation between FMTs."""
    return [options.str_value.to_list() for _ in range(labeler.total_cells)]


def correlated_options(
    options: pd.DataFrame,
    labeler,
    fmt: "FullModelType",
    precond_mt: "ModelType",
    uniqueness: bool,
) -> "OptionsList":
    """Get options when there is a defined correlation between FMTs."""
    precond_data: pd.Series = labeler.filter_fmt_with_current(
        to_fmt(precond_mt, True)
    )
    mask_precond = ~mt_is_null(precond_data, precond_mt)
    if not mask_precond.any():
        return base_options(options, labeler)

    precond_ids = precond_data[mask_precond]

    df, _ = load_predictable_csv(fmt, usecols=["id", "user_id"])  # TODO: Change user_id to specific character_ids
    df = df[df["user_id"].isin(precond_ids)].drop_duplicates()
    df = df.set_index("user_id", drop=True, verify_integrity=uniqueness)

    if uniqueness:
        return [
            [df.at[pc_val, "id"]]
            if pc
            else options.str_value.to_list()
            for pc, pc_val in zip(mask_precond, precond_data)
        ]
    else:
        return [
            df.loc[pc_val, "id"].to_list()
            if pc
            else options.str_value.to_list()
            for pc, pc_val in zip(mask_precond, precond_data)
        ]


def filter_correlated_mts(
    options: pd.DataFrame,
    mt: "ModelType",
    ifk: "IsForKiller",
    labeler,
) -> "OptionsList":
    conds = {
        "killer item": ifk and (mt == MT.ITEM),
        "killer addons": ifk and (mt == MT.ADDONS),
        "surv addons": (not ifk) and (mt == MT.ADDONS),
    }
    if not any(conds.values()):
        return base_options(options, labeler)

    fmt = to_fmt(mt, ifk)
    if conds["killer item"]:  # if character is filled, set item
        return correlated_options(options, labeler, fmt, precond_mt=MT.CHARACTER, uniqueness=True)
    elif conds["killer addons"]:  # if character is filled, set addons
        return correlated_options(options, labeler, fmt, precond_mt=MT.CHARACTER, uniqueness=False)
    elif conds["surv addons"]:  # if item is filled, set addons
        return correlated_options(options, labeler, fmt, precond_mt=MT.ITEM, uniqueness=False)
    else:
        raise Exception("Correlation MT condition not mapped by the ifs.")


def process_options(options: pd.DataFrame, ifk: "IsForKiller") -> pd.DataFrame:
    """Process options DataFrame."""
    options = options[
        options["is_for_killer"].isnull() |
        (options["is_for_killer"] == ifk)
    ]
    options = options.drop("is_for_killer", axis=1)

    options["emoji"] = options["emoji"].fillna("❓")

    return options.sort_values(["type_id", "name"])


def reorder_mu(
    options: pd.DataFrame,
    mt: "ModelType",
    pt: "PlayerType",
    mt_null_col: str,
) -> pd.DataFrame:
    """Reorder most used items."""
    if mt in MOST_USED and pt in MOST_USED[mt]:
        options = options.set_index("name", drop=True)
        most_used_df = options.loc[[mt_null_col] + MOST_USED[mt][pt]]
        options = pd.concat(
            (
                most_used_df,
                options[~options.index.isin(most_used_df.index.values)]
            ),
            axis=0,
        )
        options = options.reset_index(drop=False)
    return options


def reorder_lu_and_np(
    options: pd.DataFrame,
    mt: "ModelType",
    ifk: "IsForKiller",
) -> pd.DataFrame:
    """Reorder least used and non-possible item types."""
    if mt == MT.ITEM:
        mask = options["type_id"] == 7
    elif mt == MT.ADDONS and not ifk:
        mask = options["type_id"].isin([3, 4, 7])
    elif mt == MT.OFFERING:
        mask = options["type_id"].isin([3, 6, 9, 12, 13])

    return pd.concat(
        (options[~mask], options[mask]),
        axis=0,
        ignore_index=True,
    )


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


def options_with_types(labeler) -> "OptionsList":
    """Get current labeler's options if the model type item has item types."""
    mt = labeler.mt
    ifk = labeler.ifk
    pt = PT.ifk_to_pt(ifk)

    # Options as DataFrame
    options, _ = load_predictable_csv(to_fmt(mt, ifk), cols=["name", "id", "type_id"])
    options, mt_null_col = filter_nulls(options, mt, ifk)

    options = add_types(options, mt)
    options = process_options(options, ifk)

    options = reorder_mu(options, mt, pt, mt_null_col)
    options = reorder_lu_and_np(options, mt, ifk)

    options["str_value"] = options.apply(
        lambda row: (f"{row['emoji']} {row['name']}", row["id"]),
        axis=1,
    )
    options = options.drop("emoji", axis=1)

    # Options as list[DataFrame]
    return filter_correlated_mts(options, mt, ifk, labeler)


def options_wo_types(
    mt: "ModelType",
    ifk: "IsForKiller",
    total_cells: int,
) -> "OptionsList":
    """Get current labeler's options if the model type item doesn't have item types."""
    fmt = to_fmt(mt, ifk)

    try:
        options, _ = load_predictable_csv(fmt, usecols=["emoji", "name", "id"])
        options = options.apply(
            lambda row: (f"{row['emoji']} {row['name']}", row["id"]),
            axis=1,
        )
    except (KeyError, ValueError):
        options, _ = load_predictable_csv(fmt, usecols=["name", "id"])
        options = options.apply(
            lambda row: (f"{row['name']}", row["id"]),
            axis=1,
        )

    return [options.to_list() for _ in range(total_cells)]
