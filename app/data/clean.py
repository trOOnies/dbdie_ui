"""Code for the clean data phase."""

from dbdie_classes.options.NULL_IDS import BY_MT as NULL_IDS_BY_MT
import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dbdie_classes.base import IsForKiller, ModelType


def make_clean_function(mt: "ModelType", ifk: "IsForKiller"):
    def clean_item(item_json: list[dict]) -> pd.DataFrame:
        """Clean raw item."""
        item = pd.DataFrame(item_json)

        mask = item["name"].isin(NULL_IDS_BY_MT[mt])
        item = pd.concat(
            (
                item[mask],
                item[~mask].sort_values("name", ignore_index=True),
            ),
            axis=0,
            ignore_index=True,
        )

        if "emoji" in item.columns.values:
            item["emoji"] = item["emoji"].fillna("❓")

        return item

    return clean_item
