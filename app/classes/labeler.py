"""Labeler class code."""

from dbdie_classes.options.FMT import assert_mt_and_pt, from_fmt
from dbdie_classes.paths import absp, CROPS_MAIN_FD_RP
import os
import numpy as np
import pandas as pd
from typing import TYPE_CHECKING, Optional

from classes.labels_counter import LabelsCounter
from code.labeler import (
    filter_data,
    init_cols,
    init_dims,
    init_current,
    init_pending,
    merge_with_types,
    prefilter_data,
    update_current,
)

if TYPE_CHECKING:
    from dbdie_classes.base import (
        Filename,
        FullModelType,
        LabelId,
        MatchId,
        Path,
        PlayerId,
    )

    from classes.base import LabelsDataFrame, MatchesDataFrame


class Labeler:
    """Helper class for labeling purposes."""

    def __init__(
        self,
        matches: "MatchesDataFrame",  # TODO: disallow modifying cols other than the mt's
        labels: "LabelsDataFrame",
        fmt: "FullModelType",
    ) -> None:
        self.matches = matches  # id must be the index
        self.labels = labels  # idem: (match_id, player_id)

        self.fmt = fmt
        self.mt, self.pt, self.ifk = from_fmt(self.fmt)
        assert_mt_and_pt(self.mt, self.pt)
        self.folder_path = absp(f"{CROPS_MAIN_FD_RP}/{fmt}")

        self.columns, self.column_ixs = init_cols(self.mt, self.labels)

        total_cells, n_players, n_items = init_dims(self.columns)
        self.current, self.null_id, self.null_name = init_current(
            total_cells,
            n_items,
            self.mt,
            self.ifk,
        )

        # Pending labels (rows) array and its current pointers
        self.pending, total = init_pending(self.labels, self.mt, self.ifk)

        total_labels = total * n_items
        pending_labels = self.pending.size * n_items

        self.counts = LabelsCounter(
            completed=total_labels - pending_labels,
            pending=pending_labels,
            n_players=n_players,
            n_items=n_items,
        )

    @property
    def n_players(self) -> int:
        """Number of players in a labeling step that is full."""
        return self.counts.n_players

    @property
    def n_items(self) -> int:
        """Number of predictables to be labeled per player."""
        return self.counts.n_items

    @property
    def total_cells(self) -> int:
        """Number of total cells in a labeling step that is full."""
        return self.counts.total_cells

    @property
    def done(self) -> bool:
        """Whether the predictable labeling is done."""
        return self.counts.done

    def wrap(self, values: list) -> np.ndarray:
        """Wrap values as a (n_players, n_items) matrix."""
        return np.array(values).reshape(self.n_players, self.n_items)

    def filename(self, ix: int) -> Optional["Filename"]:
        """Filename of the cell with integer index 'ix'.
        Can have a value between 0 and (total_cells - 1).
        """
        assert ix >= 0
        return self.current["m_filename"].iat[ix] if not self.done else None

    def get_key(self, player_ix: int) -> tuple["MatchId", "PlayerId"]:
        """Get primary key of the player with integer index 'ix' in the current labels.
        The index can have a value between 0 and (n_players - 1).
        """
        assert player_ix >= 0
        ix = player_ix * self.n_items  # min_ix is enough
        return int(self.current["m_id"].iat[ix]), int(self.current["player_id"].iat[ix])

    # * Images

    def get_limgs(
        self,
        img_ext: str,
    ) -> list[tuple["Path", "LabelId"]]:
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

    def get_crops(self, img_ext: str) -> list["Path"]:
        """Get labeled images of current selection as a flattened list."""
        return [
            os.path.join(
                self.folder_path,
                f"{self.filename(i)[:-4]}_{pl}_{it}.{img_ext}",
            )
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
        if not go_back and (self.counts.ptr_min >= self.pending.size):
            return self.current["label_id"].to_list()
        elif go_back and (self.counts.ptr_min <= 0):
            raise ValueError("Labeler pointer out of bounds.")

        # Change pointers
        self.counts.update(go_back)

        # Check if all matches have been labeled
        self.current = (
            pd.DataFrame(columns=self.current.columns)
            if self.done
            else update_current(self, update_match=True)
        )

        return self.current["label_id"].to_list()  # (pl0p1, pl0p2, pl0p3, pl0p4, pl1p1, ...) (16)

    def previous(self) -> list["LabelId"]:
        """Go to the previous match & labels."""
        return self.next(go_back=True)

    def update_current(self, new_labels: list["LabelId"]) -> None:
        """Update current values."""
        assert len(new_labels) == self.total_cells

        ptrs = self.pending[self.counts.ptr_min:self.counts.ptr_max]
        self.labels.iloc[ptrs, self.column_ixs] = self.wrap(new_labels)

        self.current = update_current(self, update_match=False)

    # * Other predictables

    def filter_fmt_with_current(
        self,
        fmt: "FullModelType",
        types: bool,
    ) -> pd.Series:
        """Filter another fmt with the current info of the labeler's fmt."""
        assert fmt != self.fmt
        mt, _, ifk = from_fmt(fmt)

        data = prefilter_data(self.labels, mt, ifk)
        result = filter_data(data, self.current)
        result = merge_with_types(result, types, fmt, mt)

        return result
