"""Null names and ids for the mt-bound SQL columns."""

from typing import TYPE_CHECKING

from options import MODEL_TYPES

if TYPE_CHECKING:
    from classes.base import ModelType

ADDONS_KILLER    = "NoKillerAddon"
ADDONS_SURV      = "NoSurvAddon"
CHARACTER_ALL    = "AllCharacters"
CHARACTER_KILLER = "NoKillerCharacter"
CHARACTER_SURV   = "NoSurvCharacter"
ITEM_KILLER      = "NoKillerItem"
ITEM_SURV        = "NoSurvItem"
OFFERING_KILLER  = "NoKillerOffering"
OFFERING_SURV    = "NoSurvOffering"
PERKS_KILLER     = "NoKillerPerk"
PERKS_SURV       = "NoSurvPerk"
STATUS           = "NoStatus"

BY_MODEL_TYPE = {
    MODEL_TYPES.ADDONS    : [ADDONS_SURV, ADDONS_KILLER],
    MODEL_TYPES.CHARACTER : [CHARACTER_SURV, CHARACTER_KILLER],
    MODEL_TYPES.ITEM      : [ITEM_SURV, ITEM_KILLER],
    MODEL_TYPES.OFFERING  : [OFFERING_SURV, OFFERING_KILLER],
    MODEL_TYPES.PERKS     : [PERKS_SURV, PERKS_KILLER],
    MODEL_TYPES.STATUS    : [STATUS],
}
ALL_KILLER = [
    ADDONS_KILLER,
    CHARACTER_KILLER,
    ITEM_KILLER,
    OFFERING_KILLER,
    PERKS_KILLER,
]
ALL_SURV = [
    ADDONS_SURV,
    CHARACTER_SURV,
    ITEM_SURV,
    OFFERING_SURV,
    PERKS_SURV,
]
ALL = [
    ADDONS_KILLER,
    ADDONS_SURV,
    CHARACTER_KILLER,
    CHARACTER_SURV,
    ITEM_KILLER,
    ITEM_SURV,
    OFFERING_KILLER,
    OFFERING_SURV,
    PERKS_KILLER,
    PERKS_SURV,
    STATUS,
]

INT_IDS: dict["ModelType", list[int]] = {
    MODEL_TYPES.ADDONS    : [1, 0],  # surv, killer
    MODEL_TYPES.CHARACTER : [2, 1, 0],  # surv, killer, all
    MODEL_TYPES.ITEM      : [1, 0],
    MODEL_TYPES.OFFERING  : [1, 0],
    MODEL_TYPES.PERKS     : [1, 0],
    MODEL_TYPES.STATUS    : [0, 1],
}
