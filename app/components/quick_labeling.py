"""Functions for quick_labeling component"""

from typing import Callable

import gradio as gr
from img import rescale_img

Options = list[tuple[str, int]]
LabeledImages = list[tuple[str, int]]
LabelBox = Callable[[str, int], tuple[gr.Image, gr.Dropdown]]
ImageBox = Callable[
    [str, LabeledImages],
    dict[str, dict[int, gr.Image] | dict[int, gr.Dropdown]],
]

# Version 1


def label_box(
    options: Options,
    w: int,
) -> LabelBox:
    def quick_label(
        path: str,
        value: int = 0,
    ) -> tuple[gr.Image, gr.Dropdown]:
        """Image with dropdown label"""
        return (
            gr.Image(rescale_img(path, w)),
            gr.Dropdown(
                choices=options,
                value=value,
                interactive=True,
                container=False,
            ),
        )

    return quick_label


def form_label_row(data: list[tuple[str, int]], lbox: LabelBox) -> None:
    """Images with dropdown labels"""
    for path, value in data:
        with gr.Column():
            lbox(path, value)


# Version 2


def images_box(options: Options, w: int) -> ImageBox:
    def form_images(
        rcc: str,
        limgs: LabeledImages,
    ) -> dict[str, dict[int, gr.Image] | dict[int, gr.Dropdown]]:
        """Images in a row"""
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
