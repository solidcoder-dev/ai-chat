from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PatchProposal:
    id: str
    workspace_id: str
    target_file: str
    unified_diff: str
    status: Literal["proposed"] = "proposed"
