"""Gradio related classes."""

import gradio as gr
from typing import Callable

Options = list[tuple[str, int]]
LabeledImages = list[tuple[str, int]]
LabelBox = Callable[[str, int], tuple[gr.Image, gr.Dropdown]]

ImageDict = dict[int, gr.Image]
DropdownDict = dict[int, gr.Dropdown]
ImageBox = Callable[
    [str, LabeledImages],
    dict[str, ImageDict | DropdownDict],
]
