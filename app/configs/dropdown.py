"""Config for Gradio dropdown."""

from dbdie_classes.options import MODEL_TYPE as MT
from dbdie_classes.options import PLAYER_TYPE as PT

MOST_USED = {
    MT.ITEM: {
        PT.SURV: [
            "Flashlight",
            "Sport Flashlight",
            "Utility Flashlight",
            "Camping Aid Kit",
            "First Aid Kit",
            "Emergency Med-Kit",
            "Ranger Med-Kit",
            "Worn-Out Tools",
            "Toolbox",
            "Commodious Toolbox",
            "Mechanic's Toolbox",
            "Alex's Toolbox",
            "Engineer's Toolbox",
        ],
    },
    MT.OFFERING: {
        PT.KILLER: [
            "Bloody Party Streamers",
            "Survivor Pudding",
            "Screech Cobbler",
            "Terrormisu",
            "Black Ward",
            "Putrid Oak",
            "Cypress Memento Mori",
            "Ebony Memento Mori",
            "Ivory Memento Mori",
            "Annotated Blueprint",
            "Vigo's Blueprint",
            "Bloodied Blueprint",
            "Torn Blueprint",
            "Azarov's Key",
            "Heart Locket",
            "Jigsaw Piece",
            "MacMillan's Phalanx Bone",
            "RPD Badge",
        ],
        PT.SURV: [
            "Bloody Party Streamers",
            "Bound Envelope",
            "Escape! Cake",
            "Sealed Envelope",
            "Petrified Oak",
            "Annotated Blueprint",
            "Vigo's Blueprint",
            "Bloodied Blueprint",
            "Torn Blueprint",
            "White Ward",
        ],
    },
}
