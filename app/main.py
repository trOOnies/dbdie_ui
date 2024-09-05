"""Main script for DBDIE UI"""

from api import cache_perks
from data import load_perks
from dotenv import load_dotenv
from ui import create_ui

with open("app/styles.css") as f:
    CSS = f.read()


def main() -> None:
    load_dotenv(".env")
    cache_perks(local_fallback=False)
    perks = load_perks()
    ui = create_ui(CSS, perks)
    ui.launch()


if __name__ == "__main__":
    main()
