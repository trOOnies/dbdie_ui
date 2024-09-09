"""LabelsTemplate class code."""

from __future__ import annotations

from code.labels_template import PHS, player_to_dict, to_specific_player


class LabelsTemplate:
    def __init__(self, template: str) -> None:
        self.template = template
        assert all(all(ph in self.template for ph in phs_i) for phs_i in PHS.values())

    @classmethod
    def from_path(cls, path: str) -> LabelsTemplate:
        with open(path) as f:
            template = f.read()
        return LabelsTemplate(template)

    @classmethod
    def from_pt(cls, player_template: str, sep: str = "\n\n") -> LabelsTemplate:
        """From player template (less verbose, repeats itself 4 times)."""
        assert "{i}" in player_template
        players_text = [
            player_template.replace("{i}", str(pl_id)) for pl_id in range(4)
        ]
        players_text = [to_specific_player(pl, i) for i, pl in enumerate(players_text)]
        template = sep.join(players_text)
        lt = LabelsTemplate(template)
        return lt

    @classmethod
    def from_pt_path(cls, pt_path: str, sep: str = "\n\n") -> LabelsTemplate:
        """From player template (less verbose, repeats itself 4 times)."""
        with open(pt_path) as f:
            player_template = f.read()
        return cls.from_pt(player_template, sep=sep)

    def format(self, players: list) -> str:
        """Format players with the LabelsTemplate template."""
        ds = [player_to_dict(pl, i) for i, pl in enumerate(players)]
        d = ds[0] | ds[1] | ds[2] | ds[3]
        return self.template.format(**d)
