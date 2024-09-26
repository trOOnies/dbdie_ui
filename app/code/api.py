"""Extra code for the 'api' Python file."""

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from dbdie_classes.base import LabelId, MatchId, PlayerId
    from numpy import ndarray


def extract_player_info(
    labeler,
    labels_wrapped: "ndarray",
    player_ix: int,
) -> tuple["MatchId", "PlayerId", Union["LabelId", list["LabelId"]]]:
    match_id, player_id = labeler.get_key(player_ix)
    player_labels = labels_wrapped[player_ix].tolist()
    player_labels = (
        int(player_labels[0])
        if len(player_labels) == 1
        else [int(v) for v in player_labels]
    )
    return match_id, player_id, player_labels
