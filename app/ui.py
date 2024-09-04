"""UI function script"""

import gradio as gr
from components.quick_labeling import images_box
from constants import ROW_COLORS_CLASSES

MAIN_IMG = "Screenshot 2024-04-28 023400"


def print_info(*labels) -> None:
    for player_id in range(4):
        print(labels[4 * player_id : 4 * (player_id + 1)])
    # id = -1000
    # resp = requests.patch(endp(f"/perks/{id}"))
    # if resp.status_code != 200:
    #     raise Exception(resp.reason)


def create_ui(css, perks) -> gr.Blocks:
    with gr.Blocks(title="DBDIE", fill_width=True, css=css) as ui:
        gr.Markdown("# DBDIE UI with Gradio")

        with gr.Tab("Inference"):
            # Actual inference with a trained model
            with gr.Row():
                img_input = gr.Image()
                img_output = gr.Image()
            img_btt = gr.Button("Flip")

        with gr.Tab("Training corpus"):
            # Information about the DBDIE base
            with gr.Row():
                crop = gr.Image()

        with gr.Tab("Quick labeling"):
            # Confirming the predictions of a model
            PERK_W = 120
            perks_box = images_box(perks, PERK_W)
            limgs = {
                0: [
                    (f"images/{MAIN_IMG}_0_0.jpg", 7),
                    (f"images/{MAIN_IMG}_0_1.jpg", 6),
                    (f"images/{MAIN_IMG}_0_2.jpg", 4),
                    (f"images/{MAIN_IMG}_0_3.jpg", 3),
                ],
                1: [
                    (f"images/{MAIN_IMG}_1_0.jpg", 7),
                    (f"images/{MAIN_IMG}_1_1.jpg", 6),
                    (f"images/{MAIN_IMG}_1_2.jpg", 4),
                    (f"images/{MAIN_IMG}_1_3.jpg", 3),
                ],
                2: [
                    (f"images/{MAIN_IMG}_2_0.jpg", 7),
                    (f"images/{MAIN_IMG}_2_1.jpg", 6),
                    (f"images/{MAIN_IMG}_2_2.jpg", 4),
                    (f"images/{MAIN_IMG}_2_3.jpg", 3),
                ],
                3: [
                    (f"images/{MAIN_IMG}_3_0.jpg", 7),
                    (f"images/{MAIN_IMG}_3_1.jpg", 6),
                    (f"images/{MAIN_IMG}_3_2.jpg", 4),
                    (f"images/{MAIN_IMG}_3_3.jpg", 3),
                ],
            }
            perks_objs = {
                i: perks_box(rcc, limgs[i]) for i, rcc in enumerate(ROW_COLORS_CLASSES)
            }
            quick_label_btt = gr.Button("Label")

        with gr.Tab("Labeling"):
            # Manual labeling
            with gr.Row():
                crop = gr.Image(f"images/{MAIN_IMG}.png")
            label_btt = gr.Button("Label")
            dd = gr.Dropdown(choices=perks)

        # img_btt.click(flip_text, inputs=text_input, outputs=text_output)
        # label_btt.click(flip_image, inputs=image_input, outputs=image_output)
        quick_label_btt.click(
            print_info,
            inputs=[
                o for row in perks_objs.values() for o in row["dropdowns"].values()
            ],
            # outputs=[...],
        )

    return ui
