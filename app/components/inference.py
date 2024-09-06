"""Inference component code."""

import gradio as gr
from classes.labels_template import LabelsTemplate
from pydantic import BaseModel

# lbl_temp = LabelsTemplate.from_path("app/configs/labels_formats/informative.txt")
lbl_temp = LabelsTemplate.from_pt_path(
    "app/configs/labels_formats/informative_player.txt"
)


class MockPerk(BaseModel):
    name: str
    emoji: str


class MockPlayer(BaseModel):
    id: int
    character: str
    perks: list[MockPerk]
    item: str
    addons: list[str]
    offering: str


def inference_fn(inf_img):
    text = lbl_temp.format(
        [
            MockPlayer(
                id=pl_id,
                character="Kate Denson",
                perks=[MockPerk(name="Fogwise", emoji="😶‍🌫") for _ in range(4)],
                item="Item 0",
                addons=["Addon 0", "Addon 1"],
                offering="Offering 0",
            )
            for pl_id in range(4)
        ]
    )
    return gr.update(value=text)
