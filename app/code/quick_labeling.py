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
                f"data/img/cropped/{surv_lbl.current['match']['filename']}",
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
    curr_m = surv_lbl.current['match']
    text = (
        "<br>".join(
            [
                f"🖼️ ({curr_m['id']}) {curr_m['filename']}",
                f"📅 {curr_m['match_date']}",
                f"🆚 {curr_m['dbd_version']}",
            ]
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
