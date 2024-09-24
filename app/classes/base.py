"""Base classes of DBDIE UI."""

from pandas import DataFrame

MatchesDataFrame = DataFrame  # index = id
LabelsDataFrame = DataFrame  # index = (match_id, player_id)
CurrentDataFrame = DataFrame  # cols: m_id, m_filename, m_match_date, m_dbd_version, label_id, player_id, item_id
