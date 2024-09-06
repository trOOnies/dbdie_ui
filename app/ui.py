"""UI function script."""

import os
from typing import TYPE_CHECKING

import gradio as gr
from components.inference import inference_fn
from components.quick_labeling import (
    empty_fn,
    flatten_objs,
    images_box,
    make_label_fn,
    ql_buttons,
)
from constants import ROW_COLORS_CLASSES

if TYPE_CHECKING:
    from classes.surv_labeler import SurvLabeler


def create_ui(
    css: str,
    surv_labeler: "SurvLabeler",
    perks: list[tuple[str, int]],
) -> gr.Blocks:
    """Create the Gradio Blocks-based UI"""
    with gr.Blocks(title="DBDIE", fill_width=True, css=css) as ui:
        gr.Markdown("# DBDIE UI with Gradio")

        with gr.Tab("Quick labeling"):
            # * Confirming the predictions of a model

            with gr.Row(visible=surv_labeler.done) as ql_note_row:
                gr.Markdown("No more labels to validate. Good job! 👻")

            with gr.Row(visible=not surv_labeler.done) as ql_labeling_row:
                with gr.Column():
                    PERK_W = 120
                    perks_box = images_box(perks, PERK_W)
                    limgs = surv_labeler.get_limgs("png")
                    perks_objs = {
                        i: perks_box(rcc, limgs[i])
                        for i, rcc in enumerate(ROW_COLORS_CLASSES)
                    }
                    ql_all_empty_btt, ql_label_btt, ql_match_md = ql_buttons(
                        surv_labeler
                    )

        with gr.Tab("Current match"):
            with gr.Row(visible=surv_labeler.done) as cr_note_row:
                gr.Markdown("No match selected. 🤷")

            with gr.Row(visible=not surv_labeler.done) as cr_img_row:
                cr_match_img = gr.Image(
                    os.path.join(
                        os.environ["DBDIE_MAIN_FD"],
                        f"data/img/cropped/{surv_labeler.current['match']['filename']}",
                    ),
                    interactive=False,
                    height="83vh",
                )

        with gr.Tab("Inference"):
            # Actual inference with a trained model (WIP)
            with gr.Row():
                inf_img = gr.Image()
                inf_ta = gr.TextArea(interactive=False, show_copy_button=True)
            inf_btt = gr.Button("Label")

        with gr.Tab("Training corpus"):
            # Information about the DBDIE base (WIP)
            with gr.Row():
                tc_img = gr.Image()

        # * Button actions

        label_fn = make_label_fn(surv_labeler, upload=True)

        ql_all_empty_btt.click(
            empty_fn,
            inputs=flatten_objs(perks_objs, "dropdowns"),
            outputs=flatten_objs(perks_objs, "dropdowns"),
        )
        ql_label_btt.click(
            label_fn,
            inputs=flatten_objs(perks_objs, "images")
            + flatten_objs(perks_objs, "dropdowns"),
            outputs=flatten_objs(perks_objs, "images")
            + flatten_objs(perks_objs, "dropdowns")
            + [
                cr_match_img,
                ql_match_md,
                ql_note_row,
                ql_labeling_row,
                cr_note_row,
                cr_img_row,
            ],
        )

        inf_btt.click(
            inference_fn,
            inputs=[inf_img],
            outputs=inf_ta,
        )

        # * Load actions

        sync_labels_fn = make_label_fn(surv_labeler, upload=False)

        ui.load(
            sync_labels_fn,
            inputs=flatten_objs(perks_objs, "images")
            + flatten_objs(perks_objs, "dropdowns"),
            outputs=flatten_objs(perks_objs, "images")
            + flatten_objs(perks_objs, "dropdowns")
            + [
                cr_match_img,
                ql_match_md,
                ql_note_row,
                ql_labeling_row,
                cr_note_row,
                cr_img_row,
            ],
        )

    return ui
