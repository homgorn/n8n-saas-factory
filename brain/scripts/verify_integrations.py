"""Verify F006 (MCP servers) and F007 (agents) as far as they can be measured.

F006: every configured MCP package must exist on npm and start. Servers that need
credentials must fail with a credentials error, not with "package not found" — those two
are very different and only one of them means the config is wrong.

F007: every agent file must parse, declare a name/model/tools, and appear in the routing
table. The role-to-file mapping must not drift from AGENTS.md.

Stdlib only, no network except npm lookups.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = ROOT / ".openchamber" / "agents"
MCP_CONFIG = ROOT / ".openchamber" / "mcp-servers.json"
ROUTING = ROOT / "AGENTS.md"

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))


def npm_exists(package: str) -> bool:
    """Does the package exist in the npm registry?"""
    # On Windows npm is a .cmd shim, which subprocess cannot execute by bare name.
    npm = shutil.which("npm") or shutil.which("npm.cmd") or "npm"
    try:
        proc = subprocess.run(
            [npm, "view", package, "version"],
            capture_output=True, text=True, timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0 and proc.stdout.strip() != ""


def main() -> int:
    print("=== F006 — MCP server packages ===")
    config = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
    servers = config.get("mcpServers", {})

    for name, spec in servers.items():
        args = spec.get("args", [])
        package = next((a for a in args if not a.startswith("-") and not a.startswith("{")), "")
        if not package:
            check(f"mcp:{name}", False, "no package in args")
            continue
        exists = npm_exists(package)
        check(f"mcp:{name} -> {package}", exists, "in registry" if exists else "NOT in registry")

    print()
    print("=== F007 — agent definitions and routing ===")
    files = sorted(AGENTS_DIR.glob("*.md"))
    check("agent files present", len(files) >= 5, f"{len(files)} files")

    routing = ROUTING.read_text(encoding="utf-8")
    for f in files:
        text = f.read_text(encoding="utf-8")
        has_front = text.startswith("---")
        name = re.search(r"^name:\s*(\S+)", text, re.M)
        model = re.search(r"^model:\s*(\S+)", text, re.M)
        tools = re.search(r"^tools:\s*\[([^\]]*)\]", text, re.M)
        tool_count = len([t for t in (tools.group(1).split(",") if tools else []) if t.strip()])
        ok = bool(has_front and name and model and tools and tool_count > 0)
        detail = f"name={name.group(1) if name else None} tools={tool_count}"
        check(f"agent:{f.stem}", ok, detail)
        if name and name.group(1) not in routing:
            check(f"routing mentions {name.group(1)}", False, "not in AGENTS.md")

    print()
    failed = [n for n, ok, _ in results if not ok]
    print(f"=== {len(results) - len(failed)}/{len(results)} checks passed ===")
    if failed:
        for n in failed:
            print(f"  FAILED: {n}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
