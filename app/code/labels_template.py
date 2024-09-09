"""LabelsTemplate class extra code."""

# Placeholders
PHS_RAW = [
    "character",
    "perk_0",
    "perk_1",
    "perk_2",
    "perk_3",
    "item",
    "addon_0",
    "addon_1",
    "offering",
]
PHS = {i: [f"pl{i}_{ph}" for ph in PHS_RAW] for i in range(4)}


def to_specific_player(player: str, id: int) -> str:
    for ph in PHS_RAW:
        player = player.replace(
            "{" + ph + "}",
            "{" + f"pl{id}_" + ph + "}",
        )
    return player


def player_to_dict(player, id: int) -> dict:
    return {
        f"pl{id}_character": player.character,
        f"pl{id}_perk_0": player.perks[0].emoji + " " + player.perks[0].name,
        f"pl{id}_perk_1": player.perks[1].emoji + " " + player.perks[1].name,
        f"pl{id}_perk_2": player.perks[2].emoji + " " + player.perks[2].name,
        f"pl{id}_perk_3": player.perks[3].emoji + " " + player.perks[3].name,
        f"pl{id}_item": player.item,
        f"pl{id}_addon_0": player.addons[0],
        f"pl{id}_addon_1": player.addons[1],
        f"pl{id}_offering": player.offering,
    }
