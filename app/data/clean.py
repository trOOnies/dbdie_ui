import pandas as pd
from typing import TYPE_CHECKING

from options.NULL_COLS import BY_MODEL_TYPE as NULL_COLS_BY_MT
if TYPE_CHECKING:
    from classes.base import ModelType


def make_clean_function(model_type: "ModelType", is_for_killer: bool):
    def clean_item(item_json: list[dict]) -> pd.DataFrame:
        """Clean raw item."""
        item = pd.DataFrame(item_json)

        mask = item["name"].isin(NULL_COLS_BY_MT[model_type])
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
