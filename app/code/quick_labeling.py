"""Extra code for quick_labeling component."""

from dbdie_classes.options import PLAYER_TYPE
from dbdie_classes.options.MODEL_TYPE import ALL_MULTIPLE_CHOICE as ALL_MT
from dbdie_classes.paths import absp, CROPPED_IMG_FD_RP
import gradio as gr
from typing import Any, Optional, TYPE_CHECKING

from api import upload_labels
from img import rescale_img

if TYPE_CHECKING:
    from dbdie_classes.base import LabelId, Path

GradioUpdate = dict[str, Any]


def process_fmt(lbl_sel, input_data) -> None:
    """Process new full model type."""
    mt_selected = input_data[lbl_sel.labeler.total_cells][2:].lower()
    pt_selected = input_data[lbl_sel.labeler.total_cells + 1][2:]
    pt_selected = PLAYER_TYPE.SURV if pt_selected == "Survivor" else PLAYER_TYPE.KILLER

    if lbl_sel.mt != mt_selected:
        print("MODEL TYPE CHANGED")
        lbl_sel.mt = mt_selected
    elif lbl_sel.pt != pt_selected:
        print("KILLER SURV CHANGED")
        lbl_sel.pt = pt_selected


def update_data(
    labeler,
    input_data,
    upload: bool,
    go_back: bool,
) -> list["LabelId"]:
    if upload:
        upload_labels(labeler, list(input_data[:labeler.total_cells]))
        return labeler.next()
    elif go_back:
        return labeler.next(go_back=True)
    else:
        return labeler.current["label_id"].to_list()


def next_info(
    labeler,
    updated_data: list["LabelId"],
) -> tuple[list[Optional["Path"]], list["LabelId"], Optional["Path"]]:
    if not labeler.done:
        return (
            labeler.get_crops("jpg"),
            updated_data,
            absp(f"{CROPPED_IMG_FD_RP}/{labeler.filename(0)}"),  # TODO: Change
        )
    else:
        print("LABELING DONE")
        return (
            [None for _ in range(labeler.total_cells)],
            [0 for _ in range(labeler.total_cells)],
            None,
        )


def update_images(
    crops: list[Optional["Path"]],
    match_img_path: "Path",
) -> list[GradioUpdate]:
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
    labeler_sel,
    updated_data: list["LabelId"],
):
    if labeler_sel.labeler_has_changed:
        labeler_sel.labeler_has_changed = False
        print(updated_data)
        return [
            gr.update(choices=options, value=label)
            for label, options in zip(updated_data, labeler_sel.options)
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


def process_tc_info(labeler_selector) -> str:
    """Process training corpus info.
    Return formatted text for the training corpus component.
    """
    with open("app/configs/tc_info.md") as f:
        tc_info_mt = f.read()

    tc_info = {
        mt: tc_info_mt.replace("{predictable}", mt.capitalize())
        for mt in ALL_MT
    }
    del tc_info_mt

    updated_tc_info = labeler_selector.get_tc_info()
    tc_info = "\n".join(
        [
            tci_mt.format(**updated_tc_info[mt])
            for mt, tci_mt in tc_info.items()
        ]
    )
    return tc_info
