from pathlib import Path

import pytest

from src.application.services.patch_proposal_service import PatchProposalService
from src.domain.workspace import Workspace
from src.infrastructure.patch_proposal_repository import InMemoryPatchProposalRepository
from src.infrastructure.propose_edit_tool import ProposeEditTool


def make_service(workspace_root: Path) -> PatchProposalService:
    workspace = Workspace(
        id="workspace-1",
        name="Project",
        root_path=workspace_root,
    )
    return PatchProposalService(
        workspace=workspace,
        proposals=InMemoryPatchProposalRepository(),
    )


def test_filesystem_propose_edit_generates_unified_diff(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# AI Chat\n\nOld text\n", encoding="utf-8")
    tool = ProposeEditTool(make_service(tmp_path))

    result = tool.run(
        {
            "path": "README.md",
            "new_content": "# AI Chat Coding Assistant\n\nOld text\n",
        }
    )

    assert result["target_file"] == "README.md"
    assert result["status"] == "proposed"
    assert result["file_modified"] is False
    assert "--- README.md" in result["unified_diff"]
    assert "+++ README.md" in result["unified_diff"]
    assert "-# AI Chat" in result["unified_diff"]
    assert "+# AI Chat Coding Assistant" in result["unified_diff"]
    assert result["message"] == "No files were modified."


def test_filesystem_propose_edit_does_not_modify_file(tmp_path):
    readme = tmp_path / "README.md"
    original = "# AI Chat\n"
    readme.write_text(original, encoding="utf-8")
    tool = ProposeEditTool(make_service(tmp_path))

    tool.run({"path": "README.md", "new_content": "# New Title\n"})

    assert readme.read_text(encoding="utf-8") == original


def test_patch_proposal_includes_target_path_and_proposal_id(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# AI Chat\n", encoding="utf-8")
    tool = ProposeEditTool(make_service(tmp_path))

    result = tool.run({"path": "README.md", "new_content": "# New Title\n"})

    assert result["proposal_id"]
    assert result["target_file"] == "README.md"


def test_patch_proposal_rejects_paths_outside_workspace(tmp_path):
    outside = tmp_path.parent / "outside-readme.md"
    outside.write_text("# Outside\n", encoding="utf-8")
    tool = ProposeEditTool(make_service(tmp_path))

    with pytest.raises(ValueError, match="outside the workspace"):
        tool.run({"path": "../outside-readme.md", "new_content": "# New\n"})


def test_patch_proposal_rejects_directories(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    tool = ProposeEditTool(make_service(tmp_path))

    with pytest.raises(ValueError, match="not a file"):
        tool.run({"path": "docs", "new_content": "# New\n"})


def test_patch_proposal_rejects_missing_files(tmp_path):
    tool = ProposeEditTool(make_service(tmp_path))

    with pytest.raises(ValueError, match="does not exist"):
        tool.run({"path": "README.md", "new_content": "# New\n"})


def test_patch_proposal_preserves_crlf_line_endings_in_diff(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# AI Chat\r\n\r\nOld text\r\n", encoding="utf-8", newline="")
    tool = ProposeEditTool(make_service(tmp_path))

    result = tool.run(
        {
            "path": "README.md",
            "new_content": "# AI Chat\r\n\r\nNew text\r\n",
        }
    )

    assert "-Old text\r\n" in result["unified_diff"]
    assert "+New text\r\n" in result["unified_diff"]
