"""Functions for quick_labeling component"""

import os
from typing import TYPE_CHECKING, Callable

import gradio as gr
from api import upload_labels
from img import rescale_img

if TYPE_CHECKING:
    from classes.surv_labeler import SurvLabeler

Options = list[tuple[str, int]]
LabeledImages = list[tuple[str, int]]
LabelBox = Callable[[str, int], tuple[gr.Image, gr.Dropdown]]
ImageBox = Callable[
    [str, LabeledImages],
    dict[str, dict[int, gr.Image] | dict[int, gr.Dropdown]],
]


def images_box(options: Options, w: int) -> ImageBox:
    """Create function that creates images in a Gradio Row."""

    def form_images(
        rcc: str,
        limgs: LabeledImages,
    ) -> dict[str, dict[int, gr.Image] | dict[int, gr.Dropdown]]:
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
                            height="11em",
                            container=False,
                        )
                        for i, vs in enumerate(limgs)
                    }
            with gr.Column(scale=10, min_width=200, elem_classes="option-col"):
                dds = {
                    i: gr.Dropdown(
                        choices=options,
                        value=vs[1],
                        interactive=True,
                        container=False,
                    )
                    for i, vs in enumerate(limgs)
                }

        return {"images": imgs, "dropdowns": dds}

    return form_images


def flatten_objs(objs: dict[int, dict], kind: str) -> list:
    return [o for row in objs.values() for o in row[kind].values()]


def empty_fn(*input_data):
    """Empty labels function."""
    updated_data = [0 for _ in range(len(input_data))]
    return [gr.update(value=label) for label in updated_data]


def make_label_fn(surv_lbl: "SurvLabeler", upload: bool):
    """Make the main label (button) function.

    upload: Toggles the upload and the changing of the labels for the following ones.
        If false, it's useful for synching when refreshing.
    """

    def label_fn(*input_data):
        """Main label function. Also used for synching objects when refreshing.
        
        Flattened input: First 16 images, and then 16 dropdowns.
        """
        assert len(input_data) == 32

        if upload:
            upload_labels(surv_lbl.current["match"]["id"], input_data[16:])
            updated_data = surv_lbl.next()
        else:
            updated_data = surv_lbl.current["labels_flat"]

        if not surv_lbl.done:
            crops = surv_lbl.get_crops("jpg")
            match_img_path = os.path.join(
                os.environ["DBDIE_MAIN_FD"],
                f"data/img/cropped/{surv_lbl.current['match']['filename']}",
            )
        else:
            print("LABELING DONE")
            crops = [None for _ in range(16)]
            updated_data = [0 for _ in range(16)]
            match_img_path = None

        print(match_img_path)

        return (
            [
                gr.update(
                    value=rescale_img(img, 120) if isinstance(img, str) else None,
                    label=match_img_path,
                    interactive=False,
                    height="11em",
                    container=False,
                )
                for img in crops
            ]  # images
            + [gr.update(value=label) for label in updated_data]  # dropdowns
            + [gr.update(value=match_img_path)]  # match image
            + [
                gr.update(
                    value=f"Match: {surv_lbl.current['match']['filename']}"
                    if not surv_lbl.done
                    else ""
                )
            ]  # match markdown
            + [
                gr.update(visible=surv_lbl.done),  # note row
                gr.update(visible=not surv_lbl.done),  # labeling row
                gr.update(visible=surv_lbl.done),  # current match note row
                gr.update(visible=not surv_lbl.done),  # current match row
            ]
        )

    return label_fn


def ql_buttons(
    surv_labeler: "SurvLabeler",
) -> tuple[gr.Button, gr.Button, gr.Markdown]:
    """Create quick_labeling buttons"""
    with gr.Row():
        with gr.Column(scale=1, min_width=100):
            ql_match_md = gr.Markdown(
                f"Match: {surv_labeler.current['match']['filename']}"
            )
        with gr.Column(scale=17):
            with gr.Row():
                ql_all_empty_btt = gr.Button("All Empty", variant="stop")
                ql_label_btt = gr.Button("Label", variant="primary")

    return ql_all_empty_btt, ql_label_btt, ql_match_md
