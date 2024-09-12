import os
from typing import Any
import gradio as gr
from img import rescale_img

GradioUpdate = dict[str, Any]


def next_info(surv_lbl, updated_data: list[int]) -> tuple[str | None, list[int], str]:
    if not surv_lbl.done:
        return (
            surv_lbl.get_crops("jpg"),
            updated_data,
            os.path.join(
                os.environ["DBDIE_MAIN_FD"],
                f"data/img/cropped/{surv_lbl.filename(0)}",  # TODO: Change
            ),
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


def update_match_md(surv_lbl) -> list[GradioUpdate]:
    curr = surv_lbl.current.iloc[0]
    text = (
        "<br>".join(
            [
                f"🖼️ ({curr['m_id']}) {curr['m_filename']}",
                f"📅 {curr['m_match_date']}",
                f"🆚 {curr['m_dbd_version']}",
            ]  # TODO: Change
        )
        if not surv_lbl.done
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
