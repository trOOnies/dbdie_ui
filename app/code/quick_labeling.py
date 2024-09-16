import os
from typing import Any, TYPE_CHECKING
import gradio as gr

from img import rescale_img
from paths import absp

if TYPE_CHECKING:
    from classes.base import LabelId

GradioUpdate = dict[str, Any]


def next_info(
    labeler,
    updated_data: list["LabelId"],
) -> tuple[str | None, list["LabelId"], str]:
    if not labeler.done:
        return (
            labeler.get_crops("jpg"),
            updated_data,
            absp(f"data/img/cropped/{labeler.filename(0)}"),  # TODO: Change
        )
    else:
        print("LABELING DONE")
        return (
            [None for _ in range(16)],
            [0 for _ in range(16)],
            None,
        )


def update_images(crops: list[str | None], match_img_path: str) -> list[GradioUpdate]:
    return [
        gr.update(
            value=rescale_img(img, 120) if isinstance(img, str) else None,
            label=match_img_path,
            interactive=False,
            height="11em",
            container=False,
        )
        for img in crops
    ]


def update_dropdowns(
    labeler_orch,
    updated_data: list["LabelId"],
):
    if labeler_orch.labeler_has_changed:
        labeler_orch.labeler_has_changed = False
        return [
            gr.update(choices=labeler_orch.options, value=label)
            for label in updated_data
        ]
    else:
        return [gr.update(value=label) for label in updated_data]


def update_match_markdown(labeler) -> list[GradioUpdate]:
    if labeler.done:
        text = ""
    else:
        curr = labeler.current.iloc[0]
        text = (
            "<br>".join(
                [
                    f"🖼️ ({curr['m_id']}) {curr['m_filename']}",
                    f"📅 {curr['m_match_date']}",
                    f"🆚 {curr['m_dbd_version']}",
                ]  # TODO: Change
            )
            if not labeler.done
            else ""
        )
    return [gr.update(value=text)]


def toggle_rows_visibility(done: bool) -> list[GradioUpdate]:
    return [
        gr.update(visible=done),  # note row
        gr.update(visible=not done),  # labeling row
        gr.update(visible=done),  # current match note row
        gr.update(visible=not done),  # current match row
    ]
