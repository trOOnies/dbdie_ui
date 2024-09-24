"""LabelsCounter class code."""

from dataclasses import dataclass, field


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
