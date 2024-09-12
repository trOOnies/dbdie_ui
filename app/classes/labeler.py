"""SurvLabeler class code."""

from __future__ import annotations

import os
import numpy as np
import pandas as pd
from typing import TYPE_CHECKING

from code.labeler import process_fmt, update_current
from options.COLUMNS import MT_TO_COLS
from paths import absp, CROPS_RP

if TYPE_CHECKING:
    from classes.base import FullModelType, LabelId, Path, PseudoPlayerId

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

        assert TOTAL_CELLS % len(self.columns) == 0
        self.n_players = int(TOTAL_CELLS / len(self.columns))
        self.n_items = len(self.columns)

        # TODO: Make it fmt-dependent
        self.pending = np.nonzero(self.labels[f"{self.mt}_mckd"])[0]  # ! CHANGE
        print(self.pending)
        self._ptr_min = - self.n_players
        self._ptr_max = 0

        self.done = False

        self.current = pd.DataFrame(
            {
                "m_id": [-1 for _ in range(TOTAL_CELLS)],
                "m_filename": ["" for _ in range(TOTAL_CELLS)],
                "m_match_date": ["" for _ in range(TOTAL_CELLS)],
                "m_dbd_version": ["" for _ in range(TOTAL_CELLS)],
                "label_id": [-1 for _ in range(TOTAL_CELLS)],
                "player_id": [-1 for _ in range(TOTAL_CELLS)],
                "item_id": [(i % self.n_items) for i in range(TOTAL_CELLS)],
            }
        )

    def _wrap(self, values: list) -> np.ndarray:
        return np.array(values).reshape(self.n_players, self.n_items)

    def filename(self, ix: int) -> str | None:
        return self.current["m_filename"].iat[ix] if not self.done else None

    # * Images

    def get_limgs(self, img_ext: str) -> dict["PseudoPlayerId", list[tuple["Path", "LabelId"]]]:
        """Get labeled images of current selection as a dict."""
        if self.done:
            return [(None, -1) for _ in range(TOTAL_CELLS)]

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
            raise ValueError("SurvLabeler pointer out of bounds.")

        # Change pointers
        self._ptr_min += -self.n_players if go_back else self.n_players
        self._ptr_max += -self.n_players if go_back else self.n_players

        # All matches have been labeled
        if self._ptr_min >= self.pending.size:
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
        assert len(new_labels) == TOTAL_CELLS

        ptrs = self.pending[self._ptr_min:self._ptr_max]
        self.labels.iloc[ptrs, self.column_ixs] = self._wrap(new_labels)

        self.current = update_current(self, update_match=False)
