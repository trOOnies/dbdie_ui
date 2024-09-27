"""Code for FullModelTypes' set labeling correlation."""

from dbdie_classes.options import KILLER_FMT
from dbdie_classes.options import MODEL_TYPE as MT
from dbdie_classes.options import SURV_FMT
from dbdie_classes.options.FMT import extract_mt_pt_ifk
from dbdie_classes.options.NULL_IDS import mt_is_null
from dbdie_classes.options.NULL_IDS import BY_MODEL_TYPE as NULL_IDS_BY_MT
import pandas as pd
from typing import TYPE_CHECKING

from paths import load_predictable_csv

if TYPE_CHECKING:
    from dbdie_classes.base import FullModelType, IsForKiller, ModelType

    from classes.gradio import Options, OptionsList


def base_options(options: pd.DataFrame) -> "Options":
    return options.str_value.to_list()


def base_options_list(options: pd.DataFrame, labeler) -> "OptionsList":
    """Get base options, provided that there is no defined correlation between FMTs."""
    return [base_options(options) for _ in range(labeler.total_cells)]


def get_fmt_correlation_dict(mt: "ModelType", ifk: "IsForKiller") -> dict[str, bool]:
    return {
        "killer character": ifk and (mt == MT.CHARACTER),
        "killer addons": ifk and (mt == MT.ADDONS),
        "surv addons": (not ifk) and (mt == MT.ADDONS),
    }


def get_item_id_col(fmt: "FullModelType") -> str:
    if fmt == KILLER_FMT.CHARACTER:
        return "power_id"
    elif fmt == KILLER_FMT.ADDONS:
        return "item_id"
    elif fmt == SURV_FMT.ADDONS:
        return "type_id"
    else:
        raise NotImplementedError


def load_df_corr(
    fmt: "FullModelType",
    mt: "ModelType",
    item_id_col: str,
    precond_ids,
) -> pd.DataFrame:
    df, _ = load_predictable_csv(
        fmt,
        usecols=(
            ["id", "rarity_id", "name", item_id_col]
            if mt in MT.WITH_TYPES
            else ["id", "emoji", "name", item_id_col]
        ),
    )
    assert not df.empty

    df = df[df[item_id_col].notnull()].astype({item_id_col: int})
    assert not df.empty

    df = df[df[item_id_col].isin(precond_ids)]
    assert not df.empty

    return df


def merge_predictable_rarity(df: pd.DataFrame, mt: "ModelType") -> pd.DataFrame:
    """Merge predictable rarity."""
    if mt in MT.WITH_TYPES:
        df_rarity, _ = load_predictable_csv("rarity", usecols=["id", "emoji"])
        df_rarity = df_rarity.rename({"id": "rarity_id"}, axis=1)
        df = pd.merge(df, df_rarity, on="rarity_id", how="left")
        df = df.sort_values(["rarity_id", "name"])
        df = df.drop("rarity_id", axis=1)
    return df


def preprend_null(
    df: pd.DataFrame,
    labeler,
    mt: "ModelType",
    ifk: "IsForKiller",
    item_id_col: str,
    uniqueness: bool,
) -> pd.DataFrame:
    df = pd.concat(
        (
            pd.DataFrame(
                [
                    [
                        labeler.null_id,
                        labeler.null_name,
                        NULL_IDS_BY_MT[mt][int(ifk)],
                        "❌",
                    ]
                ],
                columns=["id", "name", "item_id", "emoji"],
            ),
            df,
        ),
        axis=0,
        ignore_index=True,
    )
    return df.set_index(item_id_col, drop=True, verify_integrity=uniqueness)


def unique_ui_name(df: pd.DataFrame, pc_val) -> "Options":
    """Unique function for return_corr_options."""
    try:
        return [df.at[int(pc_val), "ui_name"]]
    except KeyError:
        return [df["ui_name"].iat[0]]


def not_unique_ui_name(df: pd.DataFrame, pc_val) -> "Options":
    """Not unique function for return_corr_options."""
    return (
        (
            [df["ui_name"].iat[0]] + df.loc[int(pc_val), "ui_name"].to_list()
        )
        if int(pc_val) in df.index.values
        else [df["ui_name"].iat[0]]
    )


def return_corr_options(
    df: pd.DataFrame,
    mask_precond: pd.Series,
    precond_data: pd.Series,
    uniqueness: bool,
    base_opts: "Options",
) -> "OptionsList":
    """Return set FMTs correlation options."""
    ui_name_func = unique_ui_name if uniqueness else not_unique_ui_name
    return [
        ui_name_func(df, pc_val) if pc else base_opts
        for pc, pc_val in zip(mask_precond, precond_data)
    ]


# * Higher level function


def correlated_options(
    options: pd.DataFrame,
    labeler,
    fmt: "FullModelType",
    precond_fmt: "FullModelType",
    uniqueness: bool,
) -> "OptionsList":
    """Get options when there is a defined correlation between FMTs."""
    mt, _, ifk = extract_mt_pt_ifk(fmt)
    precond_mt, _, _ = extract_mt_pt_ifk(precond_fmt)

    precond_data: pd.Series = labeler.filter_fmt_with_current(
        precond_fmt,
        types=fmt == SURV_FMT.ADDONS,
    )
    mask_precond = ~mt_is_null(precond_data, precond_mt)
    if not mask_precond.any():
        return base_options_list(options, labeler)

    item_id_col = get_item_id_col(fmt)
    precond_ids = precond_data[mask_precond].astype(int).unique()

    df = load_df_corr(fmt, mt, item_id_col, precond_ids)
    df = merge_predictable_rarity(df, mt)
    df = preprend_null(df, labeler, mt, ifk, item_id_col, uniqueness)

    id_col = "base_char_id" if mt == MT.CHARACTER else "id"
    df["ui_name"] = df.apply(
        lambda row: (row["emoji"] + " " + row["name"], row[id_col]),
        axis=1,
    )

    return return_corr_options(
        df,
        mask_precond,
        precond_data,
        uniqueness,
        base_opts=base_options(options),
    )
