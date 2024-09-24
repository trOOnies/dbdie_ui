"""Special paths related to DBDIE UI repo folder."""

import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dbdie_classes.base import FullModelType, ModelType, Path

CACHE_RP = "app/cache"

IMG_REF_RP = f"{CACHE_RP}/img_ref"
PREDICTABLES_RP = f"{CACHE_RP}/predictables"


def load_predictable_csv(
    fmt: "FullModelType",
    usecols: list[str],
) -> tuple[pd.DataFrame, "Path"]:
    path = f"{PREDICTABLES_RP}/{fmt}.csv"
    return pd.read_csv(path, usecols=usecols), path


def load_types_csv(
    mt: "ModelType",
    usecols: list[str],
) -> tuple[pd.DataFrame, "Path"]:
    """Load cached item types CSV."""
    path = f"{PREDICTABLES_RP}/{mt}_types.csv"
    return pd.read_csv(path, usecols=usecols), path
