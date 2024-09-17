"""Labeler class code."""

from __future__ import annotations

import os
import numpy as np
import pandas as pd
from typing import TYPE_CHECKING

from code.labeler import update_current
from options.COLUMNS import MT_TO_COLS
from options.MODEL_TYPES import process_fmt, WITH_TYPES
from options.NULL_COLS import BY_MODEL_TYPE
from paths import absp, CROPS_RP

if TYPE_CHECKING:
    from classes.base import FullModelType, KillerSurvStr, LabelId, ModelType, Path, PseudoPlayerId

TOTAL_CELLS = 16


class Labeler:
    """Helper class for labeling purposes."""

    def __init__(
        self,
        matches: pd.DataFrame,  # TODO: disallow modifying cols other than the mt's
        labels: pd.DataFrame,
        fmt: "FullModelType",
    ) -> None:
        self.matches = matches  # id must be the index
        self.labels = labels  # idem: (match_id, player_id)

        self.fmt, self.mt, self.is_for_killer = process_fmt(fmt)
        self.folder_path = absp(f"{CROPS_RP}/{fmt}")

        self.columns = MT_TO_COLS[self.mt]
        cols = self.labels.columns.to_list()
        self.column_ixs = [cols.index(c) for c in self.columns]

        self.total_cells = TOTAL_CELLS
        assert self.total_cells % len(self.columns) == 0
        self.n_players = int(self.total_cells / len(self.columns))
        self.n_items = len(self.columns)

        # TODO: Make it fmt-dependent
        mask = self.labels.index.get_level_values(1) == 4
        if not self.is_for_killer:
            mask = np.logical_not(mask)
        mask = np.logical_and(mask, ~self.labels[f"{self.mt}_mckd"])
        self.pending = np.nonzero(mask)[0]
        self._ptr_min = - self.n_players
        self._ptr_max = 0

        # Take into account the possibility of an empty initial pending list
        self.done = self.pending.size == 0

        self.current = pd.DataFrame(
            {
                "m_id": [-1 for _ in range(self.total_cells)],
                "m_filename": ["" for _ in range(self.total_cells)],
                "m_match_date": ["" for _ in range(self.total_cells)],
                "m_dbd_version": ["" for _ in range(self.total_cells)],
                "label_id": [-1 for _ in range(self.total_cells)],
                "player_id": [-1 for _ in range(self.total_cells)],
                "item_id": [(i % self.n_items) for i in range(self.total_cells)],
            }
        )

    @property
    def ks(self) -> "KillerSurvStr":
        return "killer" if self.is_for_killer else "surv"

    def wrap(self, values: list) -> np.ndarray:
        return np.array(values).reshape(self.n_players, self.n_items)

    def filename(self, ix: int) -> str | None:
        return self.current["m_filename"].iat[ix] if not self.done else None

    def get_key(self, id: int) -> tuple[int, int]:
        """Get primary key of current labels."""
        assert id < self.n_players
        ix = id * self.n_items  # min_ix is enough
        return (
            int(self.current["m_id"].iat[ix]),
            int(self.current["player_id"].iat[ix]),
        )

    # * Images

    def get_limgs(self, img_ext: str) -> dict["PseudoPlayerId", list[tuple["Path", "LabelId"]]]:
        """Get labeled images of current selection as a dict."""
        if self.done:
            return [(None, -1) for _ in range(self.total_cells)]

        return [
            (
                os.path.join(
                    self.folder_path,
                    f"{self.filename(i)[:-4]}_{pl}_{it}.{img_ext}",
                ),
                int(lbl),
            )
            for i, (lbl, pl, it) in enumerate(
                zip(
                    self.current["label_id"].values,
                    self.current["player_id"].values,
                    self.current["item_id"].values,
                )
            )
        ]

    def get_crops(self, img_ext: str) -> list[str]:
        """Get labeled images of current selection as a flattened list."""
        return [
            os.path.join(self.folder_path, f"{self.filename(i)[:-4]}_{pl}_{it}.{img_ext}")
            for i, (pl, it) in enumerate(
                zip(
                    self.current["player_id"].values,
                    self.current["item_id"].values,
                )
            )
        ]

    # * Current pointer management

    def next(self, go_back: bool = False) -> list["LabelId"]:
        """Proceed to the next match & labels."""
        # Prevent updating the pointer beyond completion
        if not go_back and (self._ptr_min >= self.pending.size):
            return self.current["label_id"].to_list()
        elif go_back and (self._ptr_min <= 0):
            raise ValueError("Labeler pointer out of bounds.")

        # Change pointers
        self._ptr_min += -self.n_players if go_back else self.n_players
        self._ptr_max += -self.n_players if go_back else self.n_players

        # All matches have been labeled
        if (self._ptr_min >= self.pending.size) or (self._ptr_max > self.pending.size):  # TODO: For now we don't allow partial uploads
            self.done = True
            self.current = pd.DataFrame(columns=self.current.columns)
        else:
            self.current = update_current(self, update_match=True)

        return self.current["label_id"].to_list()  # (pl0p1, pl0p2, pl0p3, pl0p4, pl1p1, ...) (16)

    def previous(self) -> list["LabelId"]:
        """Go to the previous match & labels."""
        return self.next(go_back=True)

    def update_current(self, new_labels: list["LabelId"]) -> None:
        """Update current values."""
        assert len(new_labels) == self.total_cells

        ptrs = self.pending[self._ptr_min:self._ptr_max]
        self.labels.iloc[ptrs, self.column_ixs] = self.wrap(new_labels)

        self.current = update_current(self, update_match=False)


class LabelerSelector:
    """Labeler selector. Also harbors the current dropdown dictionary."""
    def __init__(self, labelers: dict["FullModelType", Labeler]) -> None:
        self.labelers = labelers
        self._fmt: "FullModelType" = "perks__surv"
        self._mt: "ModelType" = "perks"
        self._is_for_killer: bool = False

        for lbl in self.labelers.values():
            lbl.next()

        self.labeler_has_changed = False
        self.load()
        self.labeler_has_changed = False

    @property
    def ks(self) -> "KillerSurvStr":
        """'killer/surv' string."""
        return "killer" if self._is_for_killer else "surv"

    @ks.setter
    def ks(self, _) -> None:
        raise PermissionError("'ks' cannot be set manually. Use 'is_for_killer' bool instead.")

    @property
    def fmt(self) -> str:
        """Full model type."""
        return self._fmt

    @fmt.setter
    def fmt(self, fmt: "FullModelType") -> None:
        self._fmt, self._mt, self._is_for_killer = process_fmt(fmt)
        self.load()

    @property
    def mt(self) -> str:
        """Model type."""
        return self._mt

    @mt.setter
    def mt(self, mt: "ModelType") -> None:
        self.fmt = f"{mt}__{self.ks}"

    @property
    def is_for_killer(self) -> bool:
        return self._is_for_killer

    @is_for_killer.setter
    def is_for_killer(self, ifk: bool) -> None:
        self.fmt = f"{self._mt}__{'killer' if ifk else 'surv'}"

    @property
    def labeler(self) -> Labeler:
        """Current labeler."""
        return self.labelers[self._fmt]

    def load(self) -> None:
        """Load current predictables from the cache."""
        assert not self.labeler_has_changed
        self.labeler_has_changed = True

        path = f"app/cache/predictables/{self.fmt}.csv"

        if self.mt in WITH_TYPES:
            options = pd.read_csv(path, usecols=["name", "id", "type_id"])

            mt_wrong_null_col = BY_MODEL_TYPE[self.mt][1 - int(self.is_for_killer)]
            options = options[options["name"] != mt_wrong_null_col]

            path_types = f"app/cache/predictables/{self.mt}_types.csv"
            options_types = pd.read_csv(path_types, usecols=["id", "emoji", "is_for_killer"])
            options_types.columns = ["type_id", "emoji", "is_for_killer"]

            options = pd.merge(options, options_types, how="left", on="type_id")

            options = options[
                options["is_for_killer"].isnull() |
                (options["is_for_killer"] == self.is_for_killer)
            ]
            options = options.drop("is_for_killer", axis=1)

            options["emoji"] = options["emoji"].fillna("❓")
            options = options.sort_values(["type_id", "name"])
            options = options.drop("type_id", axis=1)

            options = options.apply(
                lambda row: (f"{row['emoji']} {row['name']}", row["id"]),
                axis=1,
            )
        else:
            try:
                options = pd.read_csv(path, usecols=["emoji", "name", "id"])
                options = options.apply(
                    lambda row: (f"{row['emoji']} {row['name']}", row["id"]),
                    axis=1,
                )
            except (KeyError, ValueError):
                options = pd.read_csv(path, usecols=["name", "id"])
                options = options.apply(
                    lambda row: (f"{row['name']}", row["id"]),
                    axis=1,
                )

        self.options: list[tuple[str, "LabelId"]] = options.to_list()
