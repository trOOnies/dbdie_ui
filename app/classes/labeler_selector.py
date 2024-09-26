"""LabelerSelector class code."""

from copy import deepcopy
from dbdie_classes.options.FMT import assert_mt_and_pt, extract_mt_pt_ifk, to_fmt
from dbdie_classes.options.MODEL_TYPE import PERKS, WITH_TYPES
from dbdie_classes.options.MODEL_TYPE import ALL_MULTIPLE_CHOICE as ALL_MT_MULT
from dbdie_classes.options.PLAYER_TYPE import pt_to_ifk, SURV
from typing import TYPE_CHECKING

from classes.labels_counter import LabelsCounter
from code.labeler import (
    options_with_types,
    options_wo_types,
)

if TYPE_CHECKING:
    from dbdie_classes.base import (
        FullModelType,
        IsForKiller,
        PlayerType,
        ModelType,
    )

    from classes.gradio import OptionsList
    from classes.labeler import Labeler


class LabelerSelector:
    """Labeler selector.
    Also holds the current list of dictionaries for the predictables' dropdowns.
    """
    def __init__(self, labelers: dict["FullModelType", "Labeler"]) -> None:
        self.labelers = labelers

        # Start the selector with perks__surv
        self._fmt: "FullModelType" = to_fmt(PERKS, False)
        self._mt: "ModelType" = deepcopy(PERKS)
        self._pt: "PlayerType" = deepcopy(SURV)
        self._ifk: "IsForKiller" = False

        for lbl in self.labelers.values():
            lbl.next()

        self.labeler_has_changed = False
        self.load()
        self.labeler_has_changed = False  # Turn off after initial load

    @property
    def fmt(self) -> "FullModelType":
        """Current full model type."""
        return self._fmt

    @fmt.setter
    def fmt(self, value: "FullModelType") -> None:
        self._mt, self._pt, self._ifk = extract_mt_pt_ifk(value)
        assert_mt_and_pt(self._mt, self._pt)
        self._fmt = value
        self.load()

    @property
    def mt(self) -> "ModelType":
        """Current model type."""
        return self._mt

    @mt.setter
    def mt(self, value: "ModelType") -> None:
        self.fmt = to_fmt(value, self._ifk)

    @property
    def ifk(self) -> "IsForKiller":
        """Current killer boolean."""
        return self._ifk

    @ifk.setter
    def ifk(self, value: "IsForKiller") -> None:
        self.fmt = to_fmt(self._mt, value)

    @property
    def pt(self) -> "PlayerType":
        """Current player type."""
        return self._pt

    @pt.setter
    def pt(self, value: "PlayerType") -> None:
        self.fmt = to_fmt(self._mt, pt_to_ifk(value))

    @property
    def labeler(self) -> "Labeler":
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
