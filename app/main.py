"""Main script for DBDIE UI."""

from dbdie_classes.options.FMT import to_fmt
from dbdie_classes.options.MODEL_TYPE import ALL_MULTIPLE_CHOICE as ALL_MT_MULT
from dotenv import load_dotenv

from api import cache_function
from classes.labeler import Labeler, LabelerSelector
from data.clean import make_clean_function
from data.extract import extract_from_api
from data.load import load_from_files
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
        to_fmt(mt, ifk): Labeler(matches, labels, fmt=to_fmt(mt, ifk))
        for mt in ALL_MT_MULT
        for ifk in [False, True]
    }
    labeler_orch = LabelerSelector(labelers)

    ui = create_ui(CSS, labeler_orch)
    ui.launch()


if __name__ == "__main__":
    main()
