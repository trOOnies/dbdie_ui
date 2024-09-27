"""UI function script."""

from dbdie_classes.options.MODEL_TYPE import ALL_MULTIPLE_CHOICE as ALL_MT
from dbdie_classes.options.MODEL_TYPE import EMOJIS as MT_EMOJIS
from dbdie_classes.paths import absp, CROPPED_IMG_FD_RP
import gradio as gr
import os
from typing import TYPE_CHECKING

from components.inference import inference_fn
from components.quick_labeling import (
    empty_fn,
    flatten_objs,
    images_box,
    make_label_fn,
    ql_button_logic,
)
from constants import ROW_COLORS_CLASSES

if TYPE_CHECKING:
    from classes.labeler_selector import LabelerSelector


def create_ui(
    css: str,
    labeler_sel: "LabelerSelector",
) -> gr.Blocks:
    """Create the Gradio Blocks-based UI."""
    # Select current labeler
    labeler = labeler_sel.labeler

    with gr.Blocks(title="DBDIE", fill_width=True, css=css) as ui:
        gr.Markdown("# DBDIE UI with Gradio")

        with gr.Tab("Quick labeling"):
            # * Confirming the predictions of a model

            with gr.Row() as ql_note_row:
                mt_dd = gr.Dropdown(
                    choices=[f"{em} {mt.capitalize()}" for em, mt in zip(MT_EMOJIS, ALL_MT)],
                    value="💠 Perks",
                    interactive=True,
                    container=False,
                )
                ks_dd = gr.Dropdown(
                    choices=["👹 Killer", "😎 Survivor"],
                    value="😎 Survivor",
                    interactive=True,
                    container=False,
                )

            with gr.Row(visible=labeler.done) as ql_note_row:
                gr.Markdown("No more labels to validate. Good job! 👻")

            with gr.Row(visible=not labeler.done) as ql_labeling_row:
                with gr.Column():
                    PERK_W = 220
                    perks_box = images_box(labeler_sel.options, PERK_W)
                    limgs = labeler.get_limgs("jpg")
                    perks_objs = {
                        i: perks_box(rcc, limgs[4 * i : 4 * (i+1)])
                        for i, rcc in enumerate(ROW_COLORS_CLASSES)
                    }
                    ql_dict = ql_button_logic(labeler)

        with gr.Tab("Current match"):
            # * Current match information

            with gr.Row(visible=labeler.done) as cr_note_row:
                gr.Markdown("No match selected. 🤷")

            with gr.Row(visible=not labeler.done) as cr_img_row:
                filename = labeler.filename(0)  # TODO: Change
                cr_match_img = gr.Image(
                    os.path.join(
                        absp(CROPPED_IMG_FD_RP),
                        filename,
                    ) if filename is not None else filename,
                    label={filename},
                    interactive=False,
                    height="83vh",
                )

        with gr.Tab("Inference"):
            # * Actual inference with a trained model (WIP)
            with gr.Row():
                inf_img = gr.Image()
                inf_ta = gr.TextArea(interactive=False, show_copy_button=True)
            inf_btt = gr.Button("Label")

        with gr.Tab("Training corpus"):
            # * Information about the DBDIE base (WIP)
            with gr.Row():
                tc_info = gr.Markdown()

        # * Button actions

        flattened_dds = flatten_objs(perks_objs, "dropdowns")
        flattened_imgs = flatten_objs(perks_objs, "images")
        flattened_fmt_dds = [mt_dd, ks_dd]
        other_lbl_related = [
            cr_match_img,
            ql_dict["match_md"],
            ql_note_row,
            ql_labeling_row,
            cr_note_row,
            cr_img_row,
            tc_info,
        ]

        label_fn = make_label_fn(labeler_sel, upload=True)
        prev_fn = make_label_fn(labeler_sel, upload=False, go_back=True)

        ql_dict["previous_btt"].click(
            prev_fn,
            inputs=flattened_dds + flattened_fmt_dds,
            outputs=flattened_imgs + flattened_dds + other_lbl_related,
        )
        ql_dict["all_empty_btt"].click(
            empty_fn,
            inputs=flattened_dds,
            outputs=flattened_dds,
        )
        ql_dict["label_btt"].click(
            label_fn,
            inputs=flattened_dds + flattened_fmt_dds,
            outputs=flattened_imgs + flattened_dds + other_lbl_related,
        )

        inf_btt.click(
            inference_fn,
            inputs=[inf_img],
            outputs=inf_ta,
        )

        change_fn = make_label_fn(labeler_sel, upload=False)

        mt_dd.change(
            change_fn,
            inputs=flattened_dds + flattened_fmt_dds,
            outputs=flattened_imgs + flattened_dds + other_lbl_related,
        )
        ks_dd.change(
            change_fn,
            inputs=flattened_dds + flattened_fmt_dds,
            outputs=flattened_imgs + flattened_dds + other_lbl_related,
        )

        # * Load actions

        sync_labels_fn = make_label_fn(labeler_sel, upload=False)

        ui.load(
            sync_labels_fn,
            inputs=flattened_dds + flattened_fmt_dds,
            outputs=flattened_imgs + flattened_dds + other_lbl_related,
        )

    return ui
