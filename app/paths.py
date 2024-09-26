"""Special paths related to DBDIE UI repo folder."""

import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dbdie_classes.base import FullModelType, ModelType, Path

CACHE_RP = "app/cache"

IMG_REF_RP = f"{CACHE_RP}/img_ref"
PREDICTABLES_RP = f"{CACHE_RP}/predictables"


def get_predictable_csv_path(val: str, is_type: bool) -> "Path":
    return (
        f"{PREDICTABLES_RP}/{val}_types.csv"
        if is_type
        else f"{PREDICTABLES_RP}/{val}.csv"
    )


def load_predictable_csv(
    fmt: "FullModelType",
    usecols: list[str],
) -> tuple[pd.DataFrame, "Path"]:
    path = get_predictable_csv_path(fmt, is_type=False)
    return pd.read_csv(path, usecols=usecols), path


def load_types_csv(
    mt: "ModelType",
    usecols: list[str],
) -> tuple[pd.DataFrame, "Path"]:
    """Load cached item types CSV."""
    path = get_predictable_csv_path(mt, is_type=True)
    return pd.read_csv(path, usecols=usecols), path
