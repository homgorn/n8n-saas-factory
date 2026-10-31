#!/usr/bin/env python3
"""
analyzer.py — Workflow Analyzer (F003).

Reads an n8n workflow JSON file and produces a structured analysis that the SaaS
generator (F005) consumes. Pure parsing, no API keys, no network.

Usage:
    python brain/scripts/analyzer.py <workflow.json>                 # stdout
    python brain/scripts/analyzer.py <workflow.json> --out analysis.json
    python brain/scripts/analyzer.py --all                           # all docs/_workflows/*.json
    python brain/scripts/analyzer.py --all --out-dir brain/research/workflow-analyses
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF_DIR = ROOT / "n8n-docs-source" / "docs" / "_workflows"


# node type taxonomy — derived from the n8n docs, not guessed
TRIGGER_TYPES = {
    "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.webhook",
    "n8n-nodes-base.manualTrigger",
    "n8n-nodes-base.formTrigger",
    "n8n-nodes-base.chatTrigger",
    "@n8n/n8n-nodes-langchain.chatTrigger",
    "n8n-nodes-base.emailReadImap",
    "n8n-nodes-base.telegramTrigger",
    "n8n-nodes-base.gmailTrigger",
    "n8n-nodes-base.googleSheetsTrigger",
    "n8n-nodes-base.googleDriveTrigger",
    "n8n-nodes-base.facebookTrigger",
    "n8n-nodes-base.executeWorkflowTrigger",
    "n8n-nodes-base.activationTrigger",
    "n8n-nodes-base.errorTrigger",
}

AI_NODE_MARKERS = (
    "@n8n/n8n-nodes-langchain.",
    "n8n-nodes-langchain.",
    "n8n-nodes-base.aiTransform",
    "n8n-nodes-base.aiExtract",
)

CREDENTIAL_NODE_REQUIRES = {
    "n8n-nodes-base.httpRequest": "httpHeaderAuth",
    "n8n-nodes-base.slack": "slackApi",
    "n8n-nodes-base.gmail": "gmailOAuth2",
    "n8n-nodes-base.googleSheets": "googleSheetsOAuth2Api",
    "n8n-nodes-base.googleDrive": "googleDriveOAuth2Api",
    "n8n-nodes-base.telegram": "telegramApi",
    "n8n-nodes-base.postgres": "postgres",
    "n8n-nodes-base.mysql": "mySql",
    "n8n-nodes-base.mongodb": "mongoDb",
    "n8n-nodes-base.notion": "notionApi",
    "n8n-nodes-base.airtable": "airtableTokenApi",
    "n8n-nodes-base.supabase": "supabaseApi",
    "n8n-nodes-base.openAi": "openAiApi",
    "n8n-nodes-base.anthropic": "anthropicApi",
}


def classify_node(node: dict) -> str:
    ntype = node.get("type", "")
    name = node.get("name", "")
    if ntype in TRIGGER_TYPES or "trigger" in ntype.lower() or "trigger" in name.lower():
        return "trigger"
    if any(marker in ntype for marker in AI_NODE_MARKERS):
        if "agent" in ntype.lower():
            return "ai_agent"
        if "chain" in ntype.lower():
            return "ai_chain"
        if "tool" in ntype.lower():
            return "ai_tool"
        if "lm" in ntype.lower() or "chat" in ntype.lower():
            return "ai_model"
        if "memory" in ntype.lower():
            return "ai_memory"
        if "retriever" in ntype.lower() or "vector" in ntype.lower():
            return "ai_retriever"
        if "outputparser" in ntype.lower():
            return "ai_parser"
        if "embeddings" in ntype.lower():
            return "ai_embeddings"
        return "ai_component"
    if ntype.startswith("n8n-nodes-base."):
        core = ntype.split(".", 1)[-1]
        if core in ("if", "switch", "merge", "splitInBatches", "wait", "loop", "executeWorkflow"):
            return "flow_control"
        if core in ("code", "function", "functionItem", "set", "editFields", "aggregate",
                    "sort", "limit", "removeDuplicates", "compareDatasets", "itemLists"):
            return "data_transform"
        if core in ("httpRequest", "graphql", "webhook", "respondToWebhook"):
            return "http"
        if core in ("readFile", "writeFile", "convertToFile", "extractFromFile", "compression"):
            return "file"
        if core in ("postgres", "mysql", "mongodb", "redis", "sqlite", "microsoftSql"):
            return "database"
        if core in ("stickyNote", "stopAndError", "noOp", "debugHelper"):
            return "utility"
        return "app_action"
    if ntype.startswith("@n8n/"):
        return "ai_component"
    return "unknown"


def extract_ai_agent(node: dict) -> dict | None:
    ntype = node.get("type", "")
    if "agent" not in ntype.lower():
        return None
    params = node.get("parameters", {}) or {}
    return {
        "node_id": node.get("id"),
        "node_name": node.get("name"),
        "type": ntype,
        "system_prompt": (
            params.get("systemMessage")
            or params.get("prompt")
            or params.get("text")
            or params.get("options", {}).get("systemMessage")
        ),
        "model": None,  # resolved from connected sub-nodes
        "tools": [],
        "memory": None,
        "output_parser": None,
    }


def analyze_workflow(wf: dict, source_path: str) -> dict:
    nodes = wf.get("nodes") or []
    connections = wf.get("connections") or {}
    settings = wf.get("settings") or {}

    # index by id and name
    by_id = {n.get("id"): n for n in nodes if isinstance(n, dict)}
    by_name = {n.get("name"): n for n in nodes if isinstance(n, dict)}

    # classify
    classified = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        classified.append({
            "id": n.get("id"),
            "name": n.get("name"),
            "type": n.get("type"),
            "role": classify_node(n),
            "position": n.get("position"),
            "parameters": n.get("parameters", {}),
            "credentials": n.get("credentials", {}),
            "disabled": n.get("disabled", False),
        })

    triggers = [c for c in classified if c["role"] == "trigger"]
    ai_agents = [c for c in classified if c["role"] == "ai_agent"]
    ai_components = [c for c in classified if c["role"].startswith("ai_") and c["role"] != "ai_agent"]

    # credential inventory
    cred_inventory: dict[str, list[str]] = defaultdict(list)
    for c in classified:
        for cred_name, cred_info in (c.get("credentials") or {}).items():
            if isinstance(cred_info, dict):
                cred_type = cred_info.get("type") or cred_name
                cred_inventory[cred_type].append(c["name"] or c["id"])

    # node type counts
    type_counts = Counter(n.get("type") for n in nodes if isinstance(n, dict))

    # connection graph summary
    conn_summary = []
    for source_name, targets in connections.items():
        if not isinstance(targets, dict):
            continue
        for port, target_list in targets.items():
            if not isinstance(target_list, list):
                continue
            for target in target_list:
                if isinstance(target, list):
                    for t in target:
                        if isinstance(t, dict):
                            conn_summary.append({
                                "from": source_name,
                                "to": t.get("node"),
                                "type": t.get("type", "main"),
                                "index": t.get("index", 0),
                            })
                elif isinstance(target, dict):
                    conn_summary.append({
                        "from": source_name,
                        "to": target.get("node"),
                        "type": target.get("type", "main"),
                        "index": target.get("index", 0),
                    })

    # resolve AI agent sub-nodes (model, tools, memory, parser)
    agent_details = []
    for agent in ai_agents:
        agent_name = agent["name"]
        # find nodes connected INTO this agent (sub-nodes)
        sub_nodes = []
        for conn in conn_summary:
            if conn["to"] == agent_name:
                sub_nodes.append(conn["from"])
        model = None
        tools = []
        memory = None
        parser = None
        for sub in sub_nodes:
            sub_node = by_name.get(sub, {})
            stype = sub_node.get("type", "")
            if "lmChat" in stype or "lmOpenAi" in stype or "lmOllama" in stype or "lmAnthropic" in stype or "lmBedrock" in stype or "lmCohere" in stype or "lmGoogle" in stype or "lmMistral" in stype or "lmHuggingFace" in stype or "lmGroq" in stype:
                model = stype
            elif "tool" in stype.lower():
                tools.append(stype)
            elif "memory" in stype.lower():
                memory = stype
            elif "parser" in stype.lower():
                parser = stype
        agent_details.append({
            "node_id": agent["id"],
            "node_name": agent_name,
            "type": agent["type"],
            "system_prompt": agent["parameters"].get("systemMessage")
                or agent["parameters"].get("prompt")
                or agent["parameters"].get("text"),
            "model": model,
            "tools": tools,
            "memory": memory,
            "output_parser": parser,
            "sub_nodes": sub_nodes,
            "disabled": agent["disabled"],
        })

    # data flow: trigger → ... → output
    flow_path = []
    if triggers:
        # BFS from first trigger
        visited = set()
        queue = [triggers[0]["name"]]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            flow_path.append(current)
            for conn in conn_summary:
                if conn["from"] == current and conn["to"] not in visited:
                    queue.append(conn["to"])

    # complexity score (0-10)
    score = 0
    score += min(3, len(nodes) / 5)          # node count
    score += min(2, len(triggers))            # trigger count
    score += min(2, len(ai_agents) * 2)       # AI agents
    score += min(1, len(cred_inventory))       # credential diversity
    score += min(1, sum(1 for c in classified if c["role"] == "flow_control"))  # branching
    score += min(1, len(conn_summary) / 10)   # connection density
    complexity = round(min(10, score), 1)

    # estimate SaaS components
    estimated_endpoints = max(1, len(triggers))
    estimated_tables = 2 + len(cred_inventory) + (1 if ai_agents else 0)
    # users, workflows, executions, api_keys, tenant_n8n_reference, (agent_config)

    # required env vars
    env_vars = set()
    for cred_type in cred_inventory:
        env_vars.add(f"{cred_type.upper().replace('API', '_API').replace('OAUTH2', '_OAUTH2')}_KEY")
    if ai_agents:
        for agent in agent_details:
            if agent["model"] and "openai" in (agent["model"] or "").lower():
                env_vars.add("OPENAI_API_KEY")
            if agent["model"] and "anthropic" in (agent["model"] or "").lower():
                env_vars.add("ANTHROPIC_API_KEY")

    # webhook endpoints
    webhook_paths = []
    for t in triggers:
        params = t.get("parameters", {}) or {}
        if "path" in params:
            webhook_paths.append({
                "node": t["name"],
                "path": params["path"],
                "method": params.get("httpMethod", "POST"),
                "responseMode": params.get("responseMode", "onReceived"),
            })

    return {
        "workflow_id": wf.get("id") or hashlib.sha1(json.dumps(wf, sort_keys=True).encode()).hexdigest()[:12],
        "name": wf.get("name") or Path(source_path).stem,
        "source_path": source_path,
        "trigger_type": triggers[0]["type"] if triggers else "manual",
        "trigger_count": len(triggers),
        "triggers": triggers,
        "webhook_paths": webhook_paths,
        "node_count": len(nodes),
        "node_type_counts": dict(type_counts.most_common()),
        "classified_nodes": classified,
        "ai_agents": agent_details,
        "ai_component_count": len(ai_components),
        "flow_control_count": sum(1 for c in classified if c["role"] == "flow_control"),
        "data_transform_count": sum(1 for c in classified if c["role"] == "data_transform"),
        "flow_path": flow_path,
        "connections": conn_summary,
        "credential_inventory": {k: v for k, v in cred_inventory.items()},
        "required_credentials": sorted(cred_inventory.keys()),
        "environment_variables": sorted(env_vars),
        "complexity_score": complexity,
        "estimated_api_endpoints": estimated_endpoints,
        "estimated_db_tables": estimated_tables,
        "settings": settings,
        "tags": wf.get("tags", []),
        "active": wf.get("active", False),
        "version_id": wf.get("versionId"),
    }


def format_markdown(analysis: dict) -> str:
    """Human-readable summary for a SPEC.md or review."""
    lines = [
        f"# Workflow Analysis: {analysis['name']}",
        "",
        f"**Source**: `{analysis['source_path']}`",
        f"**Workflow ID**: `{analysis['workflow_id']}`",
        f"**Active**: {analysis['active']}",
        "",
        "## Summary",
        "",
        f"- **Trigger**: {analysis['trigger_type']} ({analysis['trigger_count']} trigger(s))",
        f"- **Nodes**: {analysis['node_count']} ({analysis['flow_control_count']} flow control, "
        f"{analysis['data_transform_count']} data transform, {analysis['ai_component_count']} AI components)",
        f"- **AI Agents**: {len(analysis['ai_agents'])}",
        f"- **Credentials**: {len(analysis['credential_inventory'])} types",
        f"- **Complexity**: {analysis['complexity_score']}/10",
        f"- **Estimated API endpoints**: {analysis['estimated_api_endpoints']}",
        f"- **Estimated DB tables**: {analysis['estimated_db_tables']}",
        "",
    ]

    if analysis["webhook_paths"]:
        lines += ["## Webhook endpoints", ""]
        for w in analysis["webhook_paths"]:
            lines.append(f"- `{w['method']} {w['path']}` (node: {w['node']}, mode: {w['responseMode']})")
        lines.append("")

    if analysis["ai_agents"]:
        lines += ["## AI Agents", ""]
        for a in analysis["ai_agents"]:
            lines += [
                f"### {a['node_name']}",
                f"- Type: `{a['type']}`",
                f"- Model: `{a['model'] or 'not resolved from sub-nodes'}`",
                f"- Tools: {a['tools'] or 'none'}",
                f"- Memory: `{a['memory'] or 'none'}`",
                f"- Output parser: `{a['output_parser'] or 'none'}`",
                f"- System prompt: {(a['system_prompt'] or 'n/a')[:200]}",
                "",
            ]

    if analysis["credential_inventory"]:
        lines += ["## Credentials", ""]
        for cred, nodes in analysis["credential_inventory"].items():
            lines.append(f"- `{cred}`: used by {', '.join(nodes)}")
        lines.append("")

    if analysis["environment_variables"]:
        lines += ["## Environment variables", ""]
        for v in analysis["environment_variables"]:
            lines.append(f"- `{v}`")
        lines.append("")

    lines += ["## Data flow", ""]
    lines.append(" → ".join(f"`{n}`" for n in analysis["flow_path"]))
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow", nargs="?", help="path to workflow JSON")
    ap.add_argument("--all", action="store_true", help="analyse every workflow in docs/_workflows")
    ap.add_argument("--out", help="write analysis JSON to this file")
    ap.add_argument("--out-dir", help="write per-workflow analyses to this directory")
    ap.add_argument("--format", choices=["json", "md", "both"], default="json")
    args = ap.parse_args()

    if args.all:
        if not WF_DIR.exists():
            sys.exit(f"workflow dir not found: {WF_DIR}")
        out_dir = Path(args.out_dir) if args.out_dir else ROOT / "brain" / "research" / "workflow-analyses"
        out_dir.mkdir(parents=True, exist_ok=True)

        all_analyses = []
        for path in sorted(WF_DIR.rglob("*.json")):
            try:
                wf = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(f"  ! {path.name}: invalid JSON ({exc})", file=sys.stderr)
                continue
            if not isinstance(wf, dict) or "nodes" not in wf:
                continue
            a = analyze_workflow(wf, str(path.relative_to(ROOT)))
            all_analyses.append(a)
            slug = a["name"].lower().replace(" ", "-").replace("_", "-")
            slug = "".join(c for c in slug if c.isalnum() or c == "-")[:60]
            if args.format in ("json", "both"):
                (out_dir / f"{slug}.json").write_text(
                    json.dumps(a, indent=2, ensure_ascii=False), encoding="utf-8"
                )
            if args.format in ("md", "both"):
                (out_dir / f"{slug}.md").write_text(format_markdown(a), encoding="utf-8")
            print(f"  analysed {a['name']!r}: {a['node_count']} nodes, "
                  f"{len(a['ai_agents'])} agents, complexity {a['complexity_score']}/10")

        summary = {
            "generated": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "count": len(all_analyses),
            "workflows": [
                {
                    "name": a["name"],
                    "nodes": a["node_count"],
                    "agents": len(a["ai_agents"]),
                    "triggers": a["trigger_count"],
                    "credentials": len(a["credential_inventory"]),
                    "complexity": a["complexity_score"],
                    "endpoints": a["estimated_api_endpoints"],
                    "tables": a["estimated_db_tables"],
                }
                for a in all_analyses
            ],
        }
        (out_dir / "_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\n  {len(all_analyses)} workflows analysed -> {out_dir}")
        return

    if not args.workflow:
        ap.error("provide a workflow path or --all")
    path = Path(args.workflow)
    if not path.exists():
        ap.error(f"file not found: {path}")
    wf = json.loads(path.read_text(encoding="utf-8"))
    a = analyze_workflow(wf, str(path))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(a, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {args.out}")
    if args.format in ("md", "both"):
        print(format_markdown(a))
    if args.format == "json" and not args.out:
        print(json.dumps(a, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()