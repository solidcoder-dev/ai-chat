from abc import ABC, abstractmethod

from ...domain.patch_proposal import PatchProposal


class PatchProposalRepository(ABC):
    @abstractmethod
    def save(self, proposal: PatchProposal) -> None:
        raise NotImplementedError
