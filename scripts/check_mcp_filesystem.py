from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.composition.coding_wiring import build_filesystem_mcp_tooling
from src.domain.workspace import Workspace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=30)
    args = parser.parse_args()

    workspace = Workspace(
        id="smoke-workspace",
        name=args.workspace.expanduser().resolve().name,
        root_path=args.workspace,
    )

    tooling = None
    try:
        tooling = build_filesystem_mcp_tooling(
            workspace.root_path,
            request_timeout_seconds=args.timeout_seconds,
        )
        specs = tooling.catalog.list_all_tool_specs()
        print("Discovered tools:")
        for spec in specs:
            print(f"- {spec.name}: {spec.description}")

        print("\nDirectory listing:")
        listing = tooling.registry.get_tool("filesystem.list_directory").run(
            {"path": str(workspace.root_path)}
        )
        print(listing)

        for candidate in ("README.md", "pyproject.toml"):
            path = workspace.root_path / candidate
            if path.exists():
                print(f"\nReading {candidate}:")
                content = tooling.registry.get_tool("filesystem.read_file").run(
                    {"path": str(path)}
                )
                print(content)
                break

        return 0
    except Exception as exc:
        print(f"MCP filesystem smoke test failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if tooling is not None:
            tooling.client.close()


if __name__ == "__main__":
    raise SystemExit(main())
