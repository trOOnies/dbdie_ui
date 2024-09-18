from typing import Literal

# Paths
Filename = str
PathToFolder = str
RelPath = str
Path = str

# Model type
PlayerType = Literal["killer", "surv"]
ModelType = str
FullModelType = str  # i.e. character__killer

# Labeling
MatchId = int
PlayerId = Literal[0, 1, 2, 3, 4]
LabelId = int
