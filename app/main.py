"""Main script for DBDIE UI."""

from dotenv import load_dotenv

from api import cache_function
from classes.labeler import Labeler, LabelerSelector
from data.clean import make_clean_function
from data.extract import extract_from_api
from data.load import load_from_files
from options.MODEL_TYPES import ALL_MULTIPLE_CHOICE as ALL_MT_MULT
from ui import create_ui

with open("app/styles.css") as f:
    CSS = f.read()


def main() -> None:
    load_dotenv(".env")

    for mt in ALL_MT_MULT:
        for ifk in [True, False]:
            cache_function(
                mt,
                ifk,
                make_clean_function(mt, ifk),
                local_fallback=False,
            )

    extract_from_api()
    matches, labels = load_from_files()

    labelers = {
        f"{mt}__{ks}": Labeler(matches, labels, fmt=f"{mt}__{ks}")
        for mt in ALL_MT_MULT
        for ks in ["killer", "surv"]
    }
    labeler_orch = LabelerSelector(labelers)

    ui = create_ui(CSS, labeler_orch)
    ui.launch()


if __name__ == "__main__":
    main()
