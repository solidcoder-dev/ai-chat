from typing import Dict

from ..application.ports.patch_proposal_repository import PatchProposalRepository
from ..domain.patch_proposal import PatchProposal


class InMemoryPatchProposalRepository(PatchProposalRepository):
    def __init__(self) -> None:
        self._proposals: Dict[str, PatchProposal] = {}

    def save(self, proposal: PatchProposal) -> None:
        self._proposals[proposal.id] = proposal
