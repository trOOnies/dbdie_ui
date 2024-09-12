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
    ql_button_logic,
)
from constants import ROW_COLORS_CLASSES
from paths import CROPPED_IMG_RP, absp

if TYPE_CHECKING:
    from classes.labeler import SurvLabeler


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
                    limgs = surv_labeler.get_limgs("jpg")
                    perks_objs = {
                        i: perks_box(rcc, limgs[4 * i : 4 * (i+1)])
                        for i, rcc in enumerate(ROW_COLORS_CLASSES)
                    }
                    ql_dict = ql_button_logic(surv_labeler)

        with gr.Tab("Current match"):
            with gr.Row(visible=surv_labeler.done) as cr_note_row:
                gr.Markdown("No match selected. 🤷")

            with gr.Row(visible=not surv_labeler.done) as cr_img_row:
                filename = surv_labeler.filename(0)  # TODO: Change
                cr_match_img = gr.Image(
                    os.path.join(
                        absp(CROPPED_IMG_RP),
                        filename,
                    ) if filename is not None else filename,
                    label={filename},
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
                tc_info = gr.Markdown()

        # * Button actions

        label_fn = make_label_fn(surv_labeler, upload=True)
        prev_fn = make_label_fn(surv_labeler, upload=False, go_back=True)

        flattened_dds = flatten_objs(perks_objs, "dropdowns")
        flattened_imgs = flatten_objs(perks_objs, "images")

        ql_dict["previous_btt"].click(
            prev_fn,
            inputs=flattened_imgs + flattened_dds,
            outputs=flattened_imgs + flattened_dds
            + [
                cr_match_img,
                ql_dict["match_md"],
                ql_note_row,
                ql_labeling_row,
                cr_note_row,
                cr_img_row,
                tc_info,
            ],
        )
        ql_dict["all_empty_btt"].click(
            empty_fn,
            inputs=flattened_dds,
            outputs=flattened_dds,
        )
        ql_dict["label_btt"].click(
            label_fn,
            inputs=flattened_imgs + flattened_dds,
            outputs=flattened_imgs + flattened_dds
            + [
                cr_match_img,
                ql_dict["match_md"],
                ql_note_row,
                ql_labeling_row,
                cr_note_row,
                cr_img_row,
                tc_info,
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
            inputs=flattened_imgs + flattened_dds,
            outputs=flattened_imgs + flattened_dds
            + [
                cr_match_img,
                ql_dict["match_md"],
                ql_note_row,
                ql_labeling_row,
                cr_note_row,
                cr_img_row,
                tc_info,
            ],
        )

    return ui
