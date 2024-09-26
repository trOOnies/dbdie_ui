"""API related functions."""

import os

from dbdie_classes.options.FMT import to_fmt
from dbdie_classes.options.MODEL_TYPE import CHARACTER, TO_ID_NAMES, WITH_TYPES
import pandas as pd
import requests
from typing import TYPE_CHECKING

from code.api import extract_player_info
from paths import get_predictable_csv_path, load_predictable_csv, load_types_csv

if TYPE_CHECKING:
    from dbdie_classes.base import IsForKiller, LabelId, ModelType, Path
    from classes.labeler import Labeler


def endp(endpoint: str) -> str:
    """Get full URL of the endpoint."""
    return f"{os.environ['FASTAPI_HOST']}/{endpoint}"


def parse_or_raise(resp, exp_status_code: int = 200):
    """Parse Response as JSON or raise error as exception, depending on status code."""
    if resp.status_code != exp_status_code:
        try:
            msg = resp.json()
        except requests.exceptions.JSONDecodeError:
            msg = resp.reason
        raise Exception(msg)
    return resp.json()


def cache_from_endpoint(endpoint: str) -> None:
    items = requests.get(endp(endpoint))
    assert items.status_code == 200
    df = pd.DataFrame(items.json())
    df.to_csv(get_predictable_csv_path("rarity", is_type=False), index=False)


def get_items(
    mt: "ModelType",
    is_for_killer: bool,
    local_fallback: bool,
    is_type: bool,
    clean_f,
) -> tuple[list, "Path"]:
    try:
        if is_type:
            items = requests.get(endp(f"/{mt}/types"))
        else:
            ifk_key = "is_killer" if mt == CHARACTER else "is_for_killer"
            items = requests.get(
                endp(f"/{mt}"),
                params={ifk_key: is_for_killer, "limit": 10_000},
            )

        if items.status_code != 200:
            raise AssertionError(items.reason)
    except Exception as e:
        print("[WARNING] Problem with the API.")
        if not local_fallback:
            # TODO: For now we don't allow fallback
            raise Exception(items.reason) from e
        else:
            try:
                print("Trying with local data...")
                df, path = (
                    load_types_csv(mt)
                    if is_type
                    else load_predictable_csv(to_fmt(mt, is_for_killer))
                )
                print("Local data loaded successfully.")
                return df, path
            except Exception as e:
                print("[ERROR] Local data not found.")
                raise Exception(items.reason) from e

    items_json = items.json()
    items = clean_f(items_json)
    path = (
        get_predictable_csv_path(mt, is_type=True)
        if is_type
        else get_predictable_csv_path(to_fmt(mt, is_for_killer), is_type=False)
    )

    return items, path


def cache_function(
    mt: "ModelType",
    is_for_killer: "IsForKiller",
    clean_f,
    local_fallback: bool,
) -> None:
    """Get predictables from the API and cache."""
    items, path = get_items(
        mt,
        is_for_killer,
        local_fallback,
        is_type=False,
        clean_f=clean_f,
    )
    items.to_csv(path, index=False)

    if mt in WITH_TYPES:
        item_types, path_types = get_items(
            mt,
            is_for_killer,
            local_fallback,
            is_type=True,
            clean_f=clean_f,
        )
        item_types.to_csv(path_types, index=False)


def upload_labels(labeler: "Labeler", labels: list["LabelId"]) -> None:
    """Upload labels set by the user."""
    if labeler.current["label_id"].to_list() != labels:
        print("LABELS WERE CHANGED")
        print(labeler.current["label_id"].to_list())
        print(labels)
        labeler.update_current(labels)

    labels_wrapped = labeler.wrap(labels)

    for player_ix in range(labeler.n_players):
        match_id, player_id, player_labels = extract_player_info(
            labeler,
            labels_wrapped,
            player_ix,
        )

        resp = requests.put(
            endp("/labels/predictable"),
            params={"match_id": match_id, "strict": True},
            json={
                "id": player_id,
                TO_ID_NAMES[labeler.mt]: player_labels,
            },
        )

        if resp.status_code != 200:
            try:
                msg = resp.json()
            except requests.exceptions.JSONDecodeError:
                msg = resp.reason
            raise Exception(msg)
