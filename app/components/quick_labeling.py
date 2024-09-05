"""Functions for quick_labeling component"""

from typing import TYPE_CHECKING, Callable

import gradio as gr
from api import upload_labels
from img import rescale_img

if TYPE_CHECKING:
    from data import SurvLabeler

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


def extract_values(perks_objs) -> list:
    return [o for row in perks_objs.values() for o in row["dropdowns"].values()]


def ql_buttons(
    surv_labeler: "SurvLabeler",
    perks_objs: dict[int, dict],
    note_row_visible: gr.State,
    labeling_row_visible: gr.State,
) -> tuple[gr.Button, gr.Button]:
    """Create quick_labeling buttons"""
    with gr.Row():
        with gr.Column(scale=1, min_width=100):
            gr.Markdown(f"Match: {surv_labeler.current['match']['filename']}")
        with gr.Column(scale=17):
            with gr.Row():
                ql_all_empty_btt = gr.Button("All Empty", variant="stop")
                ql_label_btt = gr.Button("Label", variant="primary")

        def label_fn(*input_data):
            note_vis = False
            labeling_vis = True

            upload_labels(input_data[:16])
            updated_data = surv_labeler.next()

            if not updated_data:
                print("CHANGING")
                note_vis = True
                labeling_vis = False
                updated_data = [0 for _ in range(16)]

            print("note_vis:", note_vis)
            print("labeling_vis:", labeling_vis)

            return [gr.update(value=label) for label in updated_data] + [
                gr.update(visible=note_vis),
                gr.update(visible=labeling_vis),
            ]

        def empty_fn(*input_data):
            updated_data = [0 for _ in range(len(input_data))]
            return [gr.update(value=label) for label in updated_data]

        ql_all_empty_btt.click(
            empty_fn,
            inputs=extract_values(perks_objs),
            outputs=extract_values(perks_objs),
        )
        ql_label_btt.click(
            label_fn,
            inputs=extract_values(perks_objs)
            + [note_row_visible, labeling_row_visible],
            outputs=extract_values(perks_objs)
            + [note_row_visible, labeling_row_visible],
        )
    return ql_all_empty_btt, ql_label_btt
