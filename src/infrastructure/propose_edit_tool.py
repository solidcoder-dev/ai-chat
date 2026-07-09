from ..application.ports.tool import Tool
from ..application.services.patch_proposal_service import PatchProposalService
from ..domain.structured_data import StructuredMap, StructuredValue


class ProposeEditTool(Tool):
    def __init__(self, patch_proposal_service: PatchProposalService) -> None:
        self._patch_proposal_service = patch_proposal_service

    def run(self, args: StructuredMap) -> StructuredValue:
        path = args.get("path")
        new_content = args.get("new_content")
        if not path or new_content is None:
            raise ValueError("ProposeEditTool requires 'path' and 'new_content'")
        proposal = self._patch_proposal_service.propose_file_replacement(
            path=str(path),
            new_content=str(new_content),
        )
        return {
            "proposal_id": proposal.id,
            "target_file": proposal.target_file,
            "unified_diff": proposal.unified_diff,
            "status": proposal.status,
            "file_modified": False,
            "message": "No files were modified.",
        }
