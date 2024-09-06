"""LabelsTemplate class code."""

from __future__ import annotations

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


class LabelsTemplate:
    def __init__(self, template: str) -> None:
        self.template = template
        assert all(all(ph in self.template for ph in phs_i) for phs_i in PHS.values())

    @classmethod
    def from_path(cls, path: str) -> LabelsTemplate:
        with open(path) as f:
            template = f.read()
        return LabelsTemplate(template)

    @staticmethod
    def _to_specific_player(player: str, id: int) -> str:
        for ph in PHS_RAW:
            player = player.replace(
                "{" + ph + "}",
                "{" + f"pl{id}_" + ph + "}",
            )
        return player

    @classmethod
    def from_pt(cls, player_template: str, sep: str = "\n\n") -> LabelsTemplate:
        """From player template (less verbose, repeats itself 4 times)."""
        assert "{i}" in player_template
        players_text = [
            player_template.replace("{i}", str(pl_id)) for pl_id in range(4)
        ]
        players_text = [
            cls._to_specific_player(pl, i) for i, pl in enumerate(players_text)
        ]
        template = sep.join(players_text)
        lt = LabelsTemplate(template)
        return lt

    @classmethod
    def from_pt_path(cls, pt_path: str, sep: str = "\n\n") -> LabelsTemplate:
        """From player template (less verbose, repeats itself 4 times)."""
        with open(pt_path) as f:
            player_template = f.read()
        return cls.from_pt(player_template, sep=sep)

    @staticmethod
    def _player_to_dict(player, id: int) -> dict:
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

    def _players_to_dict(self, players: list) -> dict:
        d = [self._player_to_dict(pl, i) for i, pl in enumerate(players)]
        return d[0] | d[1] | d[2] | d[3]

    def format(self, players: list) -> str:
        return self.template.format(**self._players_to_dict(players))
