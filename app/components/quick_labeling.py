"""Functions for quick_labeling component."""

from typing import TYPE_CHECKING, Union

import gradio as gr

from img import rescale_img
from code.quick_labeling import (
    next_info,
    process_fmt,
    process_tc_info,
    toggle_rows_visibility,
    update_data,
    update_dropdowns,
    update_images,
    update_match_markdown,
)

if TYPE_CHECKING:
    from classes.gradio import (
        DropdownDict, ImageBox, ImageDict, LabeledImages, OptionsList
    )
    from classes.labeler import Labeler
    from classes.labeler_selector import LabelerSelector


def images_box(options: "OptionsList", w: int) -> "ImageBox":
    """Create function that creates images in a Gradio Row."""

    def form_images(
        rcc: str,
        limgs: "LabeledImages",
    ) -> dict[str, Union["ImageDict", "DropdownDict"]]:
        """Create images in a Gradio Row."""
        with gr.Row(elem_classes=rcc):
            with gr.Column(scale=1, min_width=10, elem_classes="option-col"):
                gr.Markdown(f"Player {rcc}", elem_classes="vertical-text")
            with gr.Column(scale=40):
                with gr.Row(equal_height=True):
                    imgs = {
                        i: gr.Image(
                            rescale_img(vs[0], w),
                            interactive=False,
                            height="22em",
                            container=False,
                        )
                        for i, vs in enumerate(limgs)
                    }
            with gr.Column(scale=10, min_width=200, elem_classes="option-col"):
                dds = {
                    i: gr.Dropdown(
                        choices=opts,
                        value=vs[1],
                        interactive=True,
                        container=False,
                    )
                    for i, (vs, opts) in enumerate(zip(limgs, options))
                }

        return {"images": imgs, "dropdowns": dds}

    return form_images


def flatten_objs(
    objs: dict[int, dict[str, Union["ImageDict", "DropdownDict"]]],
    kind: str,
) -> list[gr.Image | gr.Dropdown]:
    return [o for row in objs.values() for o in row[kind].values()]


def empty_fn(*input_data):
    """Empty labels function."""
    updated_data = [0 for _ in range(len(input_data))]
    return [gr.update(value=label) for label in updated_data]


def make_label_fn(lbl_sel: "LabelerSelector", upload: bool, go_back: bool = False):
    """Make the main label (button) function.

    upload: Toggles the upload and the changing of the labels for the following ones.
        If false, it's useful for synching when refreshing.
    """
    if go_back:
        assert not upload, "You can't upload labels when going backwards"

    def label_fn(*input_data):
        """Main label function. Also used for synching objects when refreshing.
        
        Flattened input: First 16 images, and then 16 dropdowns.
        """
        assert len(input_data) == lbl_sel.labeler.total_cells + 2

        process_fmt(lbl_sel, input_data)

        # Select new current labeler
        labeler = lbl_sel.labeler

        updated_data = update_data(labeler, input_data, upload, go_back)
        crops, updated_data, match_img_path = next_info(labeler, updated_data)

        print("match_img_path:", match_img_path)
        print(30 * "-")

        return (
            update_images(crops, match_img_path)
            + update_dropdowns(lbl_sel, updated_data)
            + [gr.update(value=match_img_path)]
            + update_match_markdown(labeler)
            + toggle_rows_visibility(labeler.done)
            + [gr.update(value=process_tc_info(lbl_sel))]  # training corpus info
        )

    return label_fn


# * Main logic


def ql_button_logic(
    labeler: "Labeler",
) -> dict[str, gr.Button | gr.Markdown]:
    """Create quick_labeling buttons."""
    with gr.Row():
        with gr.Column(scale=1, min_width=200):
            filename = labeler.filename
            match_md = gr.Markdown(f"Match: {filename if filename is not None else ''}")
        with gr.Column(scale=17):
            with gr.Row():
                previous_btt = gr.Button("Previous")
                all_empty_btt = gr.Button("All Empty", variant="stop")
                label_btt = gr.Button("Label", variant="primary")


    return {
        "match_md": match_md,
        "previous_btt": previous_btt,
        "all_empty_btt": all_empty_btt,
        "label_btt": label_btt,
    }
