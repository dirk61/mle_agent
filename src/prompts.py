"""Prompt loading and assembly for the MLE Agent.

Reads static prompt bases and protocol snippets at import time.
Provides assembly functions for Action Node system prompts and
Router input blocks.

See spec_prompting.md for the authoritative architecture.
"""

from __future__ import annotations

import os
from pathlib import Path

# ── Prompt Loader ────────────────────────────────────────────────────────────

# Prompts directory: ../prompts/ relative to this file.
# Works in both dev (/home/six004/agentbeats/mle_agent/prompts/)
# and Docker (/home/agent/prompts/).
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

_node_bases: dict[str, str] = {}
_protocols: dict[str, str] = {}


def _load_all() -> None:
    """Read all prompt files from disk into module-level caches."""
    for f in (_PROMPTS_DIR / "nodes").glob("*.md"):
        _node_bases[f.stem] = f.read_text(encoding="utf-8")
    for f in (_PROMPTS_DIR / "protocols").glob("*.md"):
        _protocols[f.stem] = f.read_text(encoding="utf-8")


_load_all()

# ── Mappings ─────────────────────────────────────────────────────────────────

# Graph node name → prompt file stem
NODE_PROMPT_MAP: dict[str, str] = {
    "System_Architect": "architect",
    "Router_Brain": "router",
    "Data_Engineer": "data_engineer",
    "Model_Engineer": "model_engineer",
    "Evaluator": "evaluator",
}

# Nodes that receive the full assembly (static + protocols + ml_rules)
ACTION_NODES = frozenset(
    {"System_Architect", "Data_Engineer", "Model_Engineer", "Evaluator"}
)

# ── System Prompt Assembly ───────────────────────────────────────────────────


def assemble_system_prompt(node_name: str, *, workspace_dir: str = ".") -> str:
    """Build the complete system prompt for a graph node.

    Action Nodes: static_base + wake_up + sign_off + ml_rules (if exists).
    Router_Brain: static_base only (no protocols, no ml_rules).

    On System_Architect's first entry, ml_rules.md does not exist yet —
    the static base + protocols is sufficient for bootstrap.
    """
    stem = NODE_PROMPT_MAP.get(node_name)
    if stem is None:
        raise ValueError(
            f"Unknown node '{node_name}'. "
            f"Expected one of: {list(NODE_PROMPT_MAP.keys())}"
        )

    base = _node_bases[stem]

    # Router gets only its static base — no protocols, no ml_rules
    if node_name == "Router_Brain":
        return base

    # Action Nodes: append protocol snippets
    parts = [base, _protocols["wake_up"], _protocols["sign_off"]]

    # Append ml_rules.md from workspace if it exists
    ml_rules_path = os.path.join(workspace_dir, "ml_rules.md")
    if os.path.isfile(ml_rules_path):
        with open(ml_rules_path, encoding="utf-8") as f:
            parts.append(f.read())

    return "\n\n".join(parts)


# ── Router Input Block Assembly ──────────────────────────────────────────────

_AVAILABLE_NODES = (
    "System_Architect | Data_Engineer | Model_Engineer | Evaluator | END"
)
_PROGRESS_TAIL_LINES = 20


def assemble_router_input(
    *,
    current_phase: str,
    handoff_message: str,
    iteration_count: int,
    workspace_dir: str = ".",
) -> str:
    """Build the structured input block for Router_Brain.

    Reads the last 20 lines of ml_progress.txt from the workspace and
    formats the block per spec_prompting.md → Router Decision Interface.
    This string becomes the user message in Router's LLM call.
    """
    progress_path = os.path.join(workspace_dir, "ml_progress.txt")
    if os.path.isfile(progress_path):
        with open(progress_path, encoding="utf-8") as f:
            lines = f.readlines()
        progress_excerpt = "".join(lines[-_PROGRESS_TAIL_LINES:])
    else:
        progress_excerpt = "(ml_progress.txt does not exist yet)"

    return (
        f"CURRENT_PHASE: {current_phase}\n"
        f"HANDOFF_MESSAGE: {handoff_message}\n"
        f"PROGRESS_EXCERPT:\n{progress_excerpt}\n"
        f"AVAILABLE_NODES: {_AVAILABLE_NODES}\n"
        f"ITERATION_COUNT: {iteration_count}"
    )
