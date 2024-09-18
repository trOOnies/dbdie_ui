"""Types of models.
They aren't 'full' (FullModelTypes) because they lack the surv / killer suffix.
"""

from typing import TYPE_CHECKING

from options import PLAYER_TYPE

if TYPE_CHECKING:
    from classes.base import FullModelType, ModelType

ADDONS = "addons"
CHARACTER = "character"
ITEM = "item"
OFFERING = "offering"
PERKS = "perks"
POINTS = "points"
PRESTIGE = "prestige"
STATUS = "status"

ALL_MULTIPLE_CHOICE = [
    ADDONS,
    CHARACTER,
    ITEM,
    OFFERING,
    PERKS,
    STATUS,
]

WITH_TYPES = [ADDONS, ITEM, OFFERING]

# ALL = [
#     ADDONS,
#     CHARACTER,
#     ITEM,
#     OFFERING,
#     PERKS,
#     POINTS,
#     PRESTIGE,
#     STATUS,
# ]

# EMOJIS = ["💡", "🧑", "🔦", "🛑", "💠", "🔢", "❇️", "💀"]
EMOJIS = ["💡", "🧑", "🔦", "🛑", "💠", "💀"]

MT_TO_SCHEMA_ATTR = {
    CHARACTER: "character_id",
    PERKS: "perk_ids",
    ITEM: "item_id",
    ADDONS: "addon_ids",
    OFFERING: "offering_id",
    STATUS: "status_id",
    # POINTS: "points",
    # PRESTIGE: "prestige",
}


def process_fmt(fmt: str) -> tuple["FullModelType", "ModelType", bool]:
    """Process FullModelType."""
    mt_and_pt = fmt.split("__")
    assert mt_and_pt[0] in ALL_MULTIPLE_CHOICE, f"'{mt_and_pt[0]}' is not a valid model type"
    assert mt_and_pt[1] in PLAYER_TYPE.ALL, "Value must be either 'killer' or 'surv'"
    return (
        fmt,
        mt_and_pt[0],
        mt_and_pt[1] == PLAYER_TYPE.KILLER,
    )
