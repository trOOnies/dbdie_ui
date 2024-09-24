"""Gradio related classes."""

import gradio as gr
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from dbdie_classes.base import LabelId

Options = list[tuple[str, "LabelId"]]
OptionsList = list[Options]
LabeledImages = list[tuple[str, "LabelId"]]
LabelBox = Callable[[str, int], tuple[gr.Image, gr.Dropdown]]

ImageDict = dict[int, gr.Image]
DropdownDict = dict[int, gr.Dropdown]
ImageBox = Callable[
    [str, LabeledImages],
    dict[str, ImageDict | DropdownDict],
]
