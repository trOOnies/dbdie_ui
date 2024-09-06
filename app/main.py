"""Main script for DBDIE UI"""

from api import cache_perks
from classes.surv_labeler import SurvLabeler
from data import load_perks
from dotenv import load_dotenv
from ui import create_ui

with open("app/styles.css") as f:
    CSS = f.read()


def main() -> None:
    load_dotenv(".env")

    is_for_killer = False

    cache_perks(is_for_killer=is_for_killer, local_fallback=False)
    perks = load_perks(is_for_killer)

    surv_labeler = SurvLabeler.from_api()
    # surv_labeler = SurvLabeler.from_files(
    #     "app/cache/img_ref/matches.csv",
    #     "app/cache/img_ref/perks__surv.csv",
    # )

    surv_labeler.next()

    ui = create_ui(CSS, surv_labeler, perks)
    ui.launch()


if __name__ == "__main__":
    main()
