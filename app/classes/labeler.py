"""Labeler class code."""

from __future__ import annotations

from dbdie_classes.options.FMT import assert_mt_and_pt, extract_mt_pt_ifk, to_fmt
from dbdie_classes.options.MODEL_TYPE import WITH_TYPES
from dbdie_classes.options.MODEL_TYPE import ALL_MULTIPLE_CHOICE as ALL_MT_MULT
from dbdie_classes.options.PLAYER_TYPE import pt_to_ifk
from dbdie_classes.paths import absp, CROPS_MAIN_FD_RP
import os
import numpy as np
import pandas as pd
from typing import TYPE_CHECKING
from dataclasses import dataclass, field

from code.labeler import (
    init_cols,
    init_dims,
    init_current,
    init_pending,
    options_with_types,
    options_wo_types,
    update_current,
)

if TYPE_CHECKING:
    from dbdie_classes.base import (
        Filename,
        FullModelType,
        IsForKiller,
        PlayerType,
        LabelId,
        MatchId,
        ModelType,
        Path,
        PlayerId,
    )

    from classes.base import LabelsDataFrame, MatchesDataFrame
    from classes.gradio import OptionsList


@dataclass
class LabelsCounter:
    """Counter for labeling status of labels.
    'total' is 'completed' plus 'pending'.
    """

    completed     : int = field(repr=True)
    pending       : int = field(repr=True)
    n_players     : int = field(repr=False)
    n_items       : int = field(repr=False)
    total         : int = field(repr=True, init=False)
    ptr_min       : int = field(repr=False, init=False)  # labels-based
    ptr_max       : int = field(repr=False, init=False)  # labels-based
    ptr_min_reach : int = field(repr=False, init=False)  # labels-based
    total_cells   : int = field(repr=False, init=False)

    def __post_init__(self):
        assert self.completed >= 0
        assert self.pending >= 0
        assert self.n_players > 0
        assert self.n_items > 0

        self.total = self.completed + self.pending
        self.ptr_min = - self.n_players
        self.ptr_max = 0
        self.ptr_min_reach = - self.n_players
        self.total_cells = self.n_players * self.n_items

    @property
    def done(self) -> bool:
        # TODO: For now we don't allow partial uploads
        return self.pending < self.total_cells

    def _get_steps(self, go_back: bool) -> tuple[int, int]:
        row_step = - self.n_players if go_back else self.n_players
        return row_step, row_step * self.n_items

    def update(self, go_back: bool) -> None:
        """Update completed labels count."""
        row_step, lbl_step = self._get_steps(go_back)

        # Labels row pointers are always updated
        self.ptr_min += row_step
        self.ptr_max += row_step

        # Label counts are only updated when the info was updated for the first time
        if not go_back:
            new_reach = self.ptr_min > self.ptr_min_reach

            if new_reach:
                self.ptr_min_reach = self.ptr_min

                # Take into account initial step
                if self.ptr_min_reach > 0:
                    self.completed = min(self.completed + lbl_step, self.total)
                    self.pending = self.total - self.completed

    def to_tc_info() -> dict:
        """To training corpus information format."""
        counts = {}
        return counts


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

        self.mt, self.pt, self.ifk = extract_mt_pt_ifk(self.fmt)
        assert_mt_and_pt(self.mt, self.pt)
        self.fmt = fmt
        self.folder_path = absp(f"{CROPS_MAIN_FD_RP}/{fmt}")

        self.columns, self.column_ixs = init_cols(self.mt, self.labels)

        total_cells, n_players, n_items = init_dims(self.columns)
        self.current, self.null_id = init_current(
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
        return self.counts.n_players

    @property
    def n_items(self) -> int:
        return self.counts.n_items

    @property
    def total_cells(self) -> int:
        return self.counts.total_cells

    @property
    def done(self) -> bool:
        return self.counts.done

    def wrap(self, values: list) -> np.ndarray:
        """Wrap values as a (n_players, n_items) matrix."""
        return np.array(values).reshape(self.n_players, self.n_items)

    def filename(self, ix: int) -> "Filename" | None:
        return self.current["m_filename"].iat[ix] if not self.done else None

    def get_key(self, id: int) -> tuple["MatchId", "PlayerId"]:
        """Get primary key of current labels."""
        assert id < self.n_players
        ix = id * self.n_items  # min_ix is enough
        return (
            int(self.current["m_id"].iat[ix]),
            int(self.current["player_id"].iat[ix]),
        )

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
        if self.done:
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

        ptrs = self.pending[self.counts.ptr_min:self.counts.ptr_max]
        self.labels.iloc[ptrs, self.column_ixs] = self.wrap(new_labels)

        self.current = update_current(self, update_match=False)

    # * Other predictables

    def filter_fmt_with_current(self, fmt: "FullModelType") -> pd.Series:
        """Filter another fmt with the current info of the labeler's fmt."""
        assert fmt != self.fmt
        mt, _, ifk = extract_mt_pt_ifk(fmt)

        # Filter data so as to make the index filtering more efficient
        if ifk is None:
            data = self.labels[mt]
        else:
            mask_ifk = self.labels.index.get_level_values(1) == 4
            if not ifk:
                mask_ifk = np.logical_not(mask_ifk)
            data = self.labels[mt][mask_ifk]

        return data[
            data.index == self.current[["m_id", "player_id"]].apply(
                lambda row: (row["m_id"], row["player_id"])
            )
        ]


class LabelerSelector:
    """Labeler selector. Also harbors the current dropdown dictionary."""
    def __init__(self, labelers: dict["FullModelType", Labeler]) -> None:
        self.labelers = labelers
        self._fmt: "FullModelType" = "perks__surv"
        self._mt: "ModelType" = "perks"
        self._ifk: "IsForKiller" = False

        for lbl in self.labelers.values():
            lbl.next()

        self.labeler_has_changed = False
        self.load()
        self.labeler_has_changed = False  # Turn off after initial load

    @property
    def fmt(self) -> "FullModelType":
        return self._fmt

    @fmt.setter
    def fmt(self, value: "FullModelType") -> None:
        self._mt, self._pt, self._ifk = extract_mt_pt_ifk(value)
        assert_mt_and_pt(self._mt, self._pt)
        self._fmt = value
        self.load()

    @property
    def mt(self) -> "ModelType":
        return self._mt

    @mt.setter
    def mt(self, value: "ModelType") -> None:
        self.fmt = to_fmt(value, self._ifk)

    @property
    def ifk(self) -> "IsForKiller":
        return self._ifk

    @ifk.setter
    def ifk(self, value: "IsForKiller") -> None:
        self.fmt = to_fmt(self._mt, value)

    @property
    def pt(self) -> "PlayerType":
        return self._pt

    @pt.setter
    def pt(self, value: "PlayerType") -> None:
        self.fmt = to_fmt(self._mt, pt_to_ifk(value))

    @property
    def labeler(self) -> Labeler:
        """Current labeler."""
        return self.labelers[self._fmt]

    def load(self) -> None:
        """Load current predictables from the cache."""
        assert not self.labeler_has_changed
        self.labeler_has_changed = True

        self.options: "OptionsList" = (
            options_with_types(self.labeler)
            if self.mt in WITH_TYPES
            else options_wo_types(self.mt, self.ifk, self.labeler.total_cells)
        )

    def get_all_labels_counters(self) -> dict["ModelType", list[LabelsCounter]]:
        """Get all labelers' LabelCounters.
        For each model type, first goes the survivor and then the killer.
        """
        return {
            mt: [
                (
                    self.labelers[to_fmt(mt, ifk)].counts
                    if to_fmt(mt, ifk) in self.labelers 
                    else LabelsCounter(completed=0, pending=0, n_players=0, n_items=0)
                ) for ifk in [False, True]
            ] for mt in ALL_MT_MULT
        }

    def get_tc_info(self) -> dict["ModelType", dict[str, int]]:
        """Get training corpus info.

        Nomenclature:
        - k Killer, s Survivor
        - p Pending, c Checked
        - t Total
        """
        lcs = self.get_all_labels_counters()
        return {
            mt: {
                "sc": mt_lcs[0].completed,
                "sp": mt_lcs[0].pending,
                "kc": mt_lcs[1].completed,
                "kp": mt_lcs[1].pending,
                "st": mt_lcs[0].completed + mt_lcs[0].pending,
                "kt": mt_lcs[1].completed + mt_lcs[1].pending,
                "tc": mt_lcs[0].completed + mt_lcs[1].completed,
                "tp": mt_lcs[0].pending + mt_lcs[1].pending,
            }
            for mt, mt_lcs in lcs.items()
        }
