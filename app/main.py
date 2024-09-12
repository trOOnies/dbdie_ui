"""Main script for DBDIE UI."""

from api import cache_perks
from classes.labeler import Labeler
from dotenv import load_dotenv
from ui import create_ui

from data.extract import extract_from_api
from data.load import load_perks, load_from_files

with open("app/styles.css") as f:
    CSS = f.read()


def main() -> None:
    load_dotenv(".env")

    is_for_killer = False

    cache_perks(is_for_killer=is_for_killer, local_fallback=False)
    perks = load_perks(is_for_killer)

    extract_from_api()
    matches, labels = load_from_files()

    perks_slb = Labeler(matches, labels, fmt="perks__surv")
    perks_slb.next()

    ui = create_ui(CSS, perks_slb, perks)
    ui.launch()


if __name__ == "__main__":
    main()
