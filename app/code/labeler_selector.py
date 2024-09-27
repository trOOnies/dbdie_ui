"""Labeler selector extra code."""

from dbdie_classes.options import PLAYER_TYPE as PT
from dbdie_classes.options import KILLER_FMT
from dbdie_classes.options import MODEL_TYPE as MT
from dbdie_classes.options import SURV_FMT
from dbdie_classes.options.FMT import to_fmt
from dbdie_classes.options.NULL_IDS import BY_MODEL_TYPE as NULL_IDS_BY_MT
import pandas as pd
from typing import TYPE_CHECKING

from code.fmt_correl import (
    base_options_list,
    correlated_options,
    get_fmt_correlation_dict,
)
from configs.dropdown import MOST_USED
from paths import load_predictable_csv, load_types_csv

if TYPE_CHECKING:
    from dbdie_classes.base import (
        IsForKiller,
        ModelType,
        PlayerType,
    )

    from classes.gradio import OptionsList

# * Add types functions


def merge_is_for_killer(mt: "ModelType", options: pd.DataFrame) -> pd.DataFrame:
    options_types, _ = load_types_csv(mt, usecols=["id", "is_for_killer"])
    options_types = options_types.rename({"id": "type_id"}, axis=1)
    return pd.merge(options, options_types, how="left", on="type_id")


def merge_killer_emojis(merged_opt: pd.DataFrame) -> pd.DataFrame:
    killer_emojis, _ = load_predictable_csv(
        to_fmt(MT.CHARACTER, True),
        usecols=["power_id", "emoji", "id", "base_char_id"],
    )
    killer_emojis = killer_emojis[killer_emojis["id"] == killer_emojis["base_char_id"]]
    killer_emojis = killer_emojis.drop(["id", "base_char_id"], axis=1)

    killer_emojis = killer_emojis.rename({"power_id": "id"}, axis=1)
    killer_emojis = killer_emojis[killer_emojis["id"].notnull()]
    killer_emojis = killer_emojis.astype({"id": int})

    return pd.merge(merged_opt, killer_emojis, how="left", on="id")


def add_types(options: pd.DataFrame, mt: "ModelType", ifk: "IsForKiller") -> pd.DataFrame:
    """Add item types to the 'options' DataFrame."""
    if (mt == MT.ITEM) and ifk:
        merged_opt = merge_is_for_killer(mt, options)
        merged_opt = merge_killer_emojis(merged_opt)
    else:
        options_types, _ = load_types_csv(mt, usecols=["id", "emoji", "is_for_killer"])
        options_types = options_types.rename({"id": "type_id"}, axis=1)
        merged_opt = pd.merge(options, options_types, how="left", on="type_id")

    return merged_opt


# * Other functions


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


def process_options(options: pd.DataFrame, ifk: "IsForKiller") -> pd.DataFrame:
    """Process options DataFrame."""
    options = options[options["is_for_killer"].isnull() | (options["is_for_killer"] == ifk)]
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
    if mt == MT.ADDONS and not ifk:
        mask = options["type_id"].isin([3, 4, 7])
    elif mt == MT.OFFERING:
        mask = options["type_id"].isin([3, 6, 9, 12, 13])
    else:
        return options

    return pd.concat(
        (options[~mask], options[mask]),
        axis=0,
        ignore_index=True,
    )


def filter_correlated_mts(
    options: pd.DataFrame,
    mt: "ModelType",
    ifk: "IsForKiller",
    labeler,
) -> "OptionsList":
    conds = get_fmt_correlation_dict(mt, ifk)
    if not any(conds.values()):
        return base_options_list(options, labeler)

    fmt = to_fmt(mt, ifk)

    # If item is filled, set characters (base and legendaries)
    # OR if item is filled, set addons
    if conds["killer character"] or conds["killer addons"]:
        return correlated_options(
            options, labeler, fmt, precond_fmt=KILLER_FMT.ITEM, uniqueness=False
        )
    elif conds["surv addons"]:  # if item is filled, set addons
        return correlated_options(
            options, labeler, fmt, precond_fmt=SURV_FMT.ITEM, uniqueness=False
        )
    else:
        raise Exception("Correlation MT condition not mapped by the ifs.")


# * Main options functions


def options_with_types(labeler) -> "OptionsList":
    """Get current labeler's options if the model type item has item types."""
    mt = labeler.mt
    ifk = labeler.ifk
    pt = PT.ifk_to_pt(ifk)

    # Options as DataFrame
    options, _ = load_predictable_csv(to_fmt(mt, ifk), usecols=["name", "id", "type_id"])
    options, mt_null_col = filter_nulls(options, mt, ifk)

    options = add_types(options, mt, ifk)
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
    labeler,
    mt: "ModelType",
    ifk: "IsForKiller",
) -> "OptionsList":
    """Get current labeler's options if the model type item doesn't have item types."""
    fmt = to_fmt(mt, ifk)

    try:
        options, _ = load_predictable_csv(fmt, usecols=["emoji", "name", "id"])
        options["str_value"] = options.apply(
            lambda row: (f"{row['emoji']} {row['name']}", row["id"]),
            axis=1,
        )
    except (KeyError, ValueError):
        options, _ = load_predictable_csv(fmt, usecols=["name", "id"])
        options["str_value"] = options.apply(
            lambda row: (f"{row['name']}", row["id"]),
            axis=1,
        )

    return base_options_list(options, labeler)
