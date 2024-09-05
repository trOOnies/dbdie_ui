"""Data related functions."""

from __future__ import annotations

import os
import pandas as pd
import requests
from api import endp
from paths import absp

PERK_COLS = ["perk_0", "perk_1", "perk_2", "perk_3"]
SURV_PERKS_FD = absp("data/crops/perks__surv")

# TODO: Matches and perks load functions, with pre-ordering


def load_perks() -> list[tuple[str, int]]:
    perks = pd.read_csv("app/cache/perks.csv", usecols=["emoji", "name", "id"])

    perks = pd.concat(
        (
            pd.DataFrame(perks.iloc[0, :]).T,
            perks.iloc[1:, :].sort_values("name"),
        ),
        axis=0,
        ignore_index=True,
    )

    perks["emoji"] = perks["emoji"].fillna("❓")
    perks = perks.apply(
        lambda row: (f"{row['emoji']} {row['name']}", row["id"]),
        axis=1,
    )
    perks = perks.to_list()
    return perks


class SurvLabeler:
    """Helper class for survivor labeling purposes."""

    def __init__(self, matches: pd.DataFrame, labels: pd.DataFrame) -> None:
        self.matches = matches  # id must be the index
        self.labels = labels  # idem: (match_id, player_id)
        self.pending = self.labels.index.get_level_values(0).unique()

        self.current: dict = {
            "match": {
                "id": -1,
                "filename": "placeholder",
            },
            "labels": {i: [-1, -1, -1, -1] for i in range(4)},
            "labels_flat": [-1 for j in range(16)],
        }

        self._match_iat: int = -1

    @classmethod
    def from_files(cls, matches_path: str, labels_path: str) -> SurvLabeler:
        data = {
            "matches": pd.read_csv(matches_path),
            "labels": pd.read_csv(labels_path),
        }
        return SurvLabeler(
            matches=data["matches"].set_index("id", drop=True),
            labels=data["labels"].set_index(["match_id", "player_id"], drop=True),
        )

    @classmethod
    def from_api(cls) -> SurvLabeler:
        matches = requests.get(endp("/matches"), params={"limit": 3000})
        if matches.status_code != 200:
            raise Exception(matches.reason)

        labels = requests.get(endp("/labels"), params={"limit": 3000})
        if labels.status_code != 200:
            raise Exception(labels.reason)

        matches = matches.json()
        labels = labels.json()

        matches = pd.DataFrame(
            [
                {k: v for k, v in m.items() if k in ["id", "filename"]}
                for m in matches
            ]
        )

        labels = pd.DataFrame(
            [
                {k: v for k, v in lbl.items() if k in ["match_id", "player"]}
                for lbl in labels
            ]
        )
        labels["player_id"] = labels["player"].map(lambda pl: pl["id"])
        labels["perks"] = labels["player"].map(lambda pl: pl["perk_ids"])
        labels = labels[["match_id", "player_id", "perks"]]
        for i in range(4):
            labels[f"perk_{i}"] = labels["perks"].map(lambda ps: ps[i])
        labels = labels.drop("perks", axis=1)
        labels = labels[labels["player_id"] != 4]

        matches = matches.set_index("id", drop=True)
        labels = labels.set_index(["match_id", "player_id"], drop=True)

        matches.to_csv("app/cache/img_ref/matches.csv", index=True)
        labels.to_csv("app/cache/img_ref/perks__surv.csv", index=True)

        return SurvLabeler(matches=matches, labels=labels)

    def get_limgs(self, img_ext: str) -> dict[int, list[tuple[str, int]]]:
        """Get labeled images of current selection."""
        main_img = self.current["match"]["filename"][:-4]
        labels = self.current["labels"]
        return {
            0: [
                (os.path.join(SURV_PERKS_FD, f"{main_img}_0_0.{img_ext}"), labels[0][0]),
                (os.path.join(SURV_PERKS_FD, f"{main_img}_0_1.{img_ext}"), labels[0][1]),
                (os.path.join(SURV_PERKS_FD, f"{main_img}_0_2.{img_ext}"), labels[0][2]),
                (os.path.join(SURV_PERKS_FD, f"{main_img}_0_3.{img_ext}"), labels[0][3]),
            ],
            1: [
                (os.path.join(SURV_PERKS_FD, f"{main_img}_1_0.{img_ext}"), labels[1][0]),
                (os.path.join(SURV_PERKS_FD, f"{main_img}_1_1.{img_ext}"), labels[1][1]),
                (os.path.join(SURV_PERKS_FD, f"{main_img}_1_2.{img_ext}"), labels[1][2]),
                (os.path.join(SURV_PERKS_FD, f"{main_img}_1_3.{img_ext}"), labels[1][3]),
            ],
            2: [
                (os.path.join(SURV_PERKS_FD, f"{main_img}_2_0.{img_ext}"), labels[2][0]),
                (os.path.join(SURV_PERKS_FD, f"{main_img}_2_1.{img_ext}"), labels[2][1]),
                (os.path.join(SURV_PERKS_FD, f"{main_img}_2_2.{img_ext}"), labels[2][2]),
                (os.path.join(SURV_PERKS_FD, f"{main_img}_2_3.{img_ext}"), labels[2][3]),
            ],
            3: [
                (os.path.join(SURV_PERKS_FD, f"{main_img}_3_0.{img_ext}"), labels[3][0]),
                (os.path.join(SURV_PERKS_FD, f"{main_img}_3_1.{img_ext}"), labels[3][1]),
                (os.path.join(SURV_PERKS_FD, f"{main_img}_3_2.{img_ext}"), labels[3][2]),
                (os.path.join(SURV_PERKS_FD, f"{main_img}_3_3.{img_ext}"), labels[3][3]),
            ],
        }

    # TODO: Update method for when the data has been changed by the user

    def next(self) -> list[int]:
        """Proceed to the next match & labels."""
        self._match_iat += 1

        # All matches have been labeled
        if self._match_iat >= self.pending.size:
            self.current = {"match": {}, "labels": {}, "labels_flat": []}
        else:
            self.current["match"]["id"] = self.pending[self._match_iat]
            self.current["match"]["filename"] = self.matches.at[
                self.current["match"]["id"],
                "filename",
            ]

            mask = self.labels.index.get_level_values(0) == self.current["match"]["id"]
            perks = self.labels[PERK_COLS][mask].apply(
                lambda row: [int(row[p]) for p in PERK_COLS],
                axis=1,
            )
            assert not perks.empty
            assert perks.size == 4
            self.current["labels"] = {i: p for i, p in enumerate(perks.values)}

            self.current["labels_flat"] = [
                p for pl_perks in self.current["labels"].values() for p in pl_perks
            ]

        return self.current["labels_flat"]

    def fetch(self) -> None:
        """Delete previous information and fetch new ones."""
        raise NotImplementedError
