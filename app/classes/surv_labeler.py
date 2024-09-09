"""SurvLabeler class code."""

from __future__ import annotations

import os
from code.surv_labeler import (
    calc_labels,
    get_matches_and_labels,
    process_labels,
    process_matches,
)

import pandas as pd
from paths import absp

PERK_COLS = ["perk_0", "perk_1", "perk_2", "perk_3"]
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
            },
            "labels": {i: [-1, -1, -1, -1] for i in range(4)},
            "labels_flat": [-1 for _ in range(16)],
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

    # TODO: Update method for when the data has been changed by the user

    def next(self) -> list[int]:
        """Proceed to the next match & labels."""
        # Prevent updating the pointer beyond completion
        if self._match_iat == self.pending.size:
            return self.current["labels_flat"]
        elif self._match_iat > self.pending.size:
            raise ValueError("SurvLabeler pointer out of bounds.")

        self._match_iat += 1

        # All matches have been labeled
        if self._match_iat == self.pending.size:
            self.done = True
            self.current = {"match": {}, "labels": {}, "labels_flat": []}
        else:
            self.current["match"]["id"] = self.pending[self._match_iat]
            self.current["match"]["filename"] = self.matches.at[
                self.current["match"]["id"],
                "filename",
            ]

            self.current["labels"] = calc_labels(
                self.labels,
                self.current["match"]["id"],
                PERK_COLS,
            )

            self.current["labels_flat"] = [
                p for pl_perks in self.current["labels"].values() for p in pl_perks
            ]

        return self.current["labels_flat"]

    def fetch(self) -> None:
        """Delete previous information and fetch new ones."""
        raise NotImplementedError
