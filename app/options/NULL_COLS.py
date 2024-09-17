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
    "addons"    : [ADDONS_SURV, ADDONS_KILLER],
    "character" : [CHARACTER_SURV, CHARACTER_KILLER],
    "item"      : [ITEM_SURV, ITEM_KILLER],
    "offering"  : [OFFERING_SURV, OFFERING_KILLER],
    "perks"     : [PERKS_SURV, PERKS_KILLER],
    "status"    : [STATUS],
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
