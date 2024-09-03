import pandas as pd
import gradio as gr
from dotenv import load_dotenv
from api import cache_perks


def main():
    load_dotenv("../.env")

    cache_perks()
    perks = pd.read_csv("app/cache/perks.csv", usecols=["name", "id"])
    perks = perks.sort_values("name", ignore_index=True)
    perks = perks.apply(lambda row: (row["name"], row["id"]), axis=1)
    perks = perks.to_list()

    with gr.Blocks() as ui:
        gr.Markdown("DBDIE UI with Gradio")
        with gr.Tab("Inference"):
            with gr.Row():
                img_input = gr.Image()
                img_output = gr.Image()
            img_btt = gr.Button("Flip")  # actual inference with a trained model
        with gr.Tab("Training corpus"):
            with gr.Row():
                crop = gr.Image()  # information about the DBDIE base
        with gr.Tab("Quick labeling"):
            with gr.Row():
                crop = gr.Image()  # confirming the predictions of a model
        with gr.Tab("Labeling"):
            with gr.Row():
                crop = gr.Image()
            label_btt = gr.Button("Label")  # manual labeling
            dd = gr.Dropdown(choices=perks)

    
    # img_btt.click(flip_text, inputs=text_input, outputs=text_output)
    # label_btt.click(flip_image, inputs=image_input, outputs=image_output)

    ui.launch()


if __name__ == "__main__":
    main()
