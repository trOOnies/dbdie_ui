"""UI function script"""

import gradio as gr
from components.quick_labeling import images_box, ql_buttons
from constants import ROW_COLORS_CLASSES
from data import SurvLabeler

MAIN_IMG = "screenshot"

print("Getting data... ", end="")
surv_labeler = SurvLabeler.from_api()
# surv_labeler = SurvLabeler.from_files(
#     "app/cache/img_ref/matches.csv",
#     "app/cache/img_ref/perks__surv.csv",
# )
print("✅")

surv_labeler.next()


def create_ui(css: str, perks: list[tuple[str, int]]) -> gr.Blocks:
    """Create the Gradio Blocks-based UI"""
    with gr.Blocks(title="DBDIE", fill_width=True, css=css) as ui:
        gr.Markdown("# DBDIE UI with Gradio")

        with gr.Tab("Inference"):
            # Actual inference with a trained model (WIP)
            with gr.Row():
                img_input = gr.Image()
                img_output = gr.Image()
            img_btt = gr.Button("Flip")

        with gr.Tab("Training corpus"):
            # Information about the DBDIE base (WIP)
            with gr.Row():
                crop = gr.Image()

        with gr.Tab("Quick labeling"):
            note_row_visible = gr.State(value=False)
            labeling_row_visible = gr.State(value=True)

            # * Confirming the predictions of a model
            with gr.Row(visible=note_row_visible.value) as ql_note_row:
                gr.Markdown("No more labels to validate. Good job! 👻")

            with gr.Row(visible=labeling_row_visible.value) as ql_labeling_row:
                with gr.Column():
                    PERK_W = 120
                    perks_box = images_box(perks, PERK_W)
                    limgs = surv_labeler.get_limgs("jpg")
                    perks_objs = {
                        i: perks_box(rcc, limgs[i])
                        for i, rcc in enumerate(ROW_COLORS_CLASSES)
                    }
                    ql_all_empty_btt, ql_label_btt = ql_buttons(
                        surv_labeler,
                        perks_objs,
                        ql_note_row,
                        ql_labeling_row,
                    )

        with gr.Tab("Labeling"):
            # Manual labeling (WIP)
            with gr.Row():
                crop = gr.Image(f"images/cropped/{MAIN_IMG}.png")
            label_btt = gr.Button("Label")
            dd = gr.Dropdown(choices=perks)

        # img_btt.click(flip_text, inputs=text_input, outputs=text_output)
        # label_btt.click(flip_image, inputs=image_input, outputs=image_output)

    return ui
