"""SurvLabeler class code."""

from __future__ import annotations

import os
import numpy as np
from code.surv_labeler import (
    calc_labels,
    get_matches_and_labels,
    process_labels,
    process_matches,
    PERK_COLS,
)

import pandas as pd
from paths import absp

SURV_PERKS_FD = absp("data/crops/perks__surv")


class SurvLabeler:
    """Helper class for survivor labeling purposes."""

    def __init__(self, matches: pd.DataFrame, labels: pd.DataFrame) -> None:
        self.matches = matches  # id must be the index
        self.labels = labels  # idem: (match_id, player_id)

        self.pending = self.labels.index.get_level_values(0).unique()
        self.done: bool = False

        self.current: dict = {
            "match": {
                "id": -1,
                "filename": "placeholder",
                "match_date": "placeholder",
                "dbd_version": "placeholder",
            },
            "labels": {i: [-1, -1, -1, -1] for i in range(4)},
            "labels_flat": [-1 for _ in range(16)],
        }

        self._match_iat: int = -1

    @classmethod
    def from_files(cls, matches_path: str, labels_path: str) -> SurvLabeler:
        data = {
            "matches": pd.read_csv(matches_path, usecols=["id", "filename"]),
            "labels": pd.read_csv(labels_path, usecols=["match_id", "player_id"] + PERK_COLS),
        }
        return SurvLabeler(
            matches=data["matches"].set_index("id", drop=True),
            labels=data["labels"].set_index(["match_id", "player_id"], drop=True),
        )

    @classmethod
    def from_api(cls) -> SurvLabeler:
        print("Getting data... ", end="")

        matches_json, labels_json = get_matches_and_labels()

        matches = process_matches(matches_json)
        labels = process_labels(labels_json)

        matches.to_csv("app/cache/img_ref/matches.csv", index=True)
        labels.to_csv("app/cache/img_ref/perks__surv.csv", index=True)

        surv_labeler = SurvLabeler(matches=matches, labels=labels)
        print("✅")

        return surv_labeler

    def get_limgs(self, img_ext: str) -> dict[int, list[tuple[str, int]]]:
        """Get labeled images of current selection as a dict."""
        main_img = self.current["match"]["filename"][:-4]
        labels = self.current["labels"]
        return {
            i: [
                (
                    os.path.join(SURV_PERKS_FD, f"{main_img}_{i}_{j}.{img_ext}"),
                    labels[i][j],
                )
                for j in range(4)
            ]
            for i in range(4)
        }

    def get_crops(self, img_ext: str) -> list[str]:
        """Get labeled images of current selection as a flattened list."""
        main_img = self.current["match"]["filename"][:-4]
        return [
            os.path.join(SURV_PERKS_FD, f"{main_img}_{i}_{j}.{img_ext}")
            for i in range(4)
            for j in range(4)
        ]

    def _update_current_match(self) -> None:
        self.current["match"]["id"] = self.pending[self._match_iat]

        current_row = self.matches.loc[self.current["match"]["id"]]
        self.current["match"]["filename"] = current_row["filename"]
        self.current["match"]["match_date"] = current_row["match_date"]
        self.current["match"]["dbd_version"] = current_row["dbd_version"]

    def _update_current_labels(self):
        self.current["labels"] = calc_labels(self.labels, self.current["match"]["id"])
        self.current["labels_flat"] = [
            p for pl_perks in self.current["labels"].values() for p in pl_perks
        ]

    def next(self, go_back: bool = False) -> list[int]:
        """Proceed to the next match & labels."""
        # Prevent updating the pointer beyond completion
        if not go_back and (self._match_iat == self.pending.size):
            return self.current["labels_flat"]
        elif go_back and (self._match_iat <= 0):
            raise ValueError("SurvLabeler pointer out of bounds.")
        elif self._match_iat > self.pending.size:
            raise ValueError("SurvLabeler pointer out of bounds.")

        self._match_iat += -1 if go_back else 1

        # All matches have been labeled
        if self._match_iat == self.pending.size:
            self.done = True
            self.current = {"match": {}, "labels": {}, "labels_flat": []}
        else:
            self._update_current_match()
            self._update_current_labels()

        return self.current["labels_flat"]  # (pl0p1, pl0p2, pl0p3, pl0p4, pl1p1, ...) (16)

    def previous(self) -> list[int]:
        """Go to the previous match & labels."""
        return self.next(go_back=True)

    def update_current(self, new_labels: list[int]) -> None:
        """Update current values."""
        assert len(new_labels) == 16

        mask = self.labels.index.get_level_values(0) == self.current["match"]["id"]
        rows_iloc = np.nonzero(mask)[0]
        assert rows_iloc.size == 4
        rows_loc = self.labels.index[rows_iloc]

        self.labels.loc[rows_loc, PERK_COLS] = np.array(new_labels).reshape(4, 4)
        self._update_current_labels()

    def fetch(self) -> None:
        """Delete previous information and fetch new ones."""
        raise NotImplementedError
