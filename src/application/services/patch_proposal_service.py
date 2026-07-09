from __future__ import annotations

import difflib
from pathlib import Path
from uuid import uuid4

from ..ports.patch_proposal_repository import PatchProposalRepository
from ...domain.patch_proposal import PatchProposal
from ...domain.workspace import Workspace


class PatchProposalService:
    def __init__(
        self,
        workspace: Workspace,
        proposals: PatchProposalRepository,
    ) -> None:
        self._workspace = workspace
        self._proposals = proposals

    def propose_file_replacement(self, path: str, new_content: str) -> PatchProposal:
        target_path = self._resolve_workspace_file(path)
        with target_path.open("r", encoding="utf-8", newline="") as file:
            original_content = file.read()
        target_file = self._target_file_name(target_path)
        proposal = PatchProposal(
            id=str(uuid4()),
            workspace_id=self._workspace.id,
            target_file=target_file,
            unified_diff=self._unified_diff(
                target_file=target_file,
                original_content=original_content,
                new_content=new_content,
            ),
        )
        self._proposals.save(proposal)
        return proposal

    def _resolve_workspace_file(self, path: str) -> Path:
        requested_path = Path(path).expanduser()
        if requested_path.is_absolute():
            target_path = requested_path.resolve()
        else:
            target_path = (self._workspace.root_path / requested_path).resolve()
        if not target_path.is_relative_to(self._workspace.root_path):
            raise ValueError("Path is outside the workspace")
        if not target_path.exists():
            raise ValueError("Target file does not exist")
        if not target_path.is_file():
            raise ValueError("Target path is not a file")
        return target_path

    def _target_file_name(self, target_path: Path) -> str:
        return str(target_path.relative_to(self._workspace.root_path))

    @staticmethod
    def _unified_diff(
        target_file: str,
        original_content: str,
        new_content: str,
    ) -> str:
        return "".join(
            difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=target_file,
                tofile=target_file,
                lineterm="\n",
            )
        )
