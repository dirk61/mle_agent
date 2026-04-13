"""LangGraph node implementations for the MLE Agent.

Implements:
- make_action_node(): Factory for ReAct-loop Action Nodes
  (Data_Engineer, Model_Engineer, Evaluator)
- system_architect_node(): Workspace bootstrap + architecture planning
- router_brain_node(): Context cleansing + routing decisions

See spec_state.md Node Definitions for authoritative definitions.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import time

from src.llm import MODEL_MAP, call_llm

log = logging.getLogger("mle_agent")
from src.medal_thresholds import get_medal_thresholds
from src.prompts import assemble_router_input, assemble_system_prompt
from src.state import AgentState
from src.tool_node import dispatch_tool_calls
from src.tools import TOOL_SCHEMAS

# ── Constants ────────────────────────────────────────────────────────────

# Maximum tool-call rounds per Action Node invocation
DEFAULT_RECURSION_LIMIT = 50

# Wall-clock timeout for the entire graph run (seconds).
# Safety net — prevents unbounded token burn on external platforms.
# Ideal ~1hr, typical ~1.5hr, hard cap 2hr. Only triggers in edge cases.
GRAPH_WALL_CLOCK_TIMEOUT = int(os.environ.get("MLE_AGENT_TIMEOUT", 7200))

# Maximum Router transitions before forcing END.
# Happy path = ~5 cycles. 15 allows 2-3 rewinds within a ~1 hr budget.
MAX_ITERATIONS = 15

# Where competition workspaces are created
WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "/tmp/mle_agent_workspaces")

# Reverse mapping: Anthropic model ID -> tier name
_REVERSE_MODEL_MAP: dict[str, str] = {v: k for k, v in MODEL_MAP.items()}

# Router next_node -> phase label
_PHASE_MAP: dict[str, str] = {
    "System_Architect": "architecture",
    "Data_Engineer": "data_engineering",
    "Model_Engineer": "model_engineering",
    "Evaluator": "evaluation",
    "END": "END",
}


# ── Wall-Clock Safety Net ────────────────────────────────────────────────

_GRAPH_START_KEY = "_MLE_AGENT_GRAPH_START"


def _init_wall_clock() -> None:
    """Set the graph start time (once, on first call)."""
    if _GRAPH_START_KEY not in os.environ:
        os.environ[_GRAPH_START_KEY] = str(time.time())


def _elapsed_min() -> float:
    """Minutes elapsed since graph start."""
    start = os.environ.get(_GRAPH_START_KEY)
    if not start:
        return 0.0
    return (time.time() - float(start)) / 60.0


def _wall_clock_exceeded() -> bool:
    """Check if the total graph run has exceeded GRAPH_WALL_CLOCK_TIMEOUT."""
    start = os.environ.get(_GRAPH_START_KEY)
    if not start:
        return False
    return (time.time() - float(start)) > GRAPH_WALL_CLOCK_TIMEOUT


# ── Message Helpers ──────────────────────────────────────────────────────


def _response_to_message(response) -> dict:
    """Convert an Anthropic Message response to a state message dict."""
    content: list[dict] = []
    for block in response.content:
        if block.type == "text":
            content.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            content.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })
    return {"role": "assistant", "content": content}


def _extract_text(response) -> str:
    """Extract concatenated text content from an Anthropic response."""
    parts: list[str] = []
    for block in response.content:
        if block.type == "text":
            parts.append(block.text)
    return "\n".join(parts)


# ── Core ReAct Loop ──────────────────────────────────────────────────────


def _run_react_loop(
    *,
    node_name: str,
    state: AgentState,
    recursion_limit: int = DEFAULT_RECURSION_LIMIT,
) -> dict:
    """Run the ReAct loop for an Action Node.

    Repeats: LLM call -> tool dispatch -> LLM call ...
    until the LLM produces no tool calls (end_turn) or the
    recursion_limit is reached.

    Returns a state update dict with messages, handoff_message,
    and micro_tasks.
    """
    workspace_dir = state.get("workspace_dir", ".")
    tier = state.get("target_model", "sonnet")
    messages: list[dict] = list(state.get("messages", []))
    micro_tasks: list[dict] = list(state.get("micro_tasks", []))

    # Seed messages with handoff_message if empty (post-Router wipe)
    if not messages:
        handoff = state.get("handoff_message", "")
        messages = [{"role": "user", "content": handoff or "Begin your work."}]

    system = assemble_system_prompt(node_name, workspace_dir=workspace_dir)
    handoff_message = ""
    tool_rounds = 0
    # Track wall-clock start for the entire graph (shared via env marker)
    _init_wall_clock()
    log.info("[%s] Starting ReAct loop (tier=%s) [%.1f min elapsed]", node_name, tier, _elapsed_min())

    while tool_rounds < recursion_limit:
        # Safety net: abort if total graph time exceeds wall-clock timeout
        if _wall_clock_exceeded():
            handoff_message = (
                f"[{node_name}] Wall-clock timeout ({GRAPH_WALL_CLOCK_TIMEOUT}s) exceeded. "
                "Yielding to Router to wrap up."
            )
            log.warning(handoff_message)
            break

        response = call_llm(
            tier=tier,
            system=system,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )

        assistant_msg = _response_to_message(response)
        messages.append(assistant_msg)

        if response.stop_reason == "tool_use":
            tool_names = [b["name"] for b in assistant_msg["content"] if b.get("type") == "tool_use"]
            log.info(
                "[%s] Tool round %d/%d: %s [%.1f min]",
                node_name, tool_rounds + 1, recursion_limit, tool_names, _elapsed_min(),
            )
            tool_result_msg, micro_tasks = dispatch_tool_calls(
                assistant_msg, workspace_dir, micro_tasks
            )
            # Log brief preview of tool results
            for block in tool_result_msg.get("content", []):
                if isinstance(block, dict) and "content" in block:
                    preview = str(block["content"])[:150].replace("\n", " ")
                    log.info("[%s]   -> %s", node_name, preview)
            messages.append(tool_result_msg)
            tool_rounds += 1
            continue

        if response.stop_reason == "max_tokens":
            # Truncated — ask the LLM to continue
            messages.append({
                "role": "user",
                "content": "[System: Your response was truncated. Please continue.]",
            })
            continue

        # end_turn or other — LLM is done
        handoff_message = _extract_text(response)
        log.info(
            "[%s] Done after %d tool rounds [%.1f min]. Handoff: %.120s...",
            node_name, tool_rounds, _elapsed_min(), handoff_message,
        )
        break
    else:
        # Recursion limit hit
        handoff_message = (
            f"[{node_name}] Recursion limit ({recursion_limit}) reached. "
            "Yielding to Router with partial progress."
        )

    # Safety net: auto-commit any uncommitted work the LLM left behind.
    # The Sign-Off protocol asks the LLM to commit, but it doesn't always.
    _auto_commit(workspace_dir, node_name)

    return {
        "messages": messages,
        "handoff_message": handoff_message,
        "micro_tasks": micro_tasks,
    }


def _auto_commit(workspace_dir: str, node_name: str) -> None:
    """Commit any uncommitted files the LLM left behind after a node exit."""
    if not workspace_dir or workspace_dir == ".":
        return
    # Check if there's anything to commit
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=workspace_dir, capture_output=True, text=True, check=False,
    )
    if not status.stdout.strip():
        return  # nothing to commit
    subprocess.run(
        ["git", "add", "-A"],
        cwd=workspace_dir, capture_output=True, check=False,
    )
    subprocess.run(
        ["git", "commit", "-m", f"Auto-commit after {node_name} exit"],
        cwd=workspace_dir, capture_output=True, check=False,
    )
    log.info("[%s] Auto-committed uncommitted files", node_name)


# ── Action Node Factory ─────────────────────────────────────────────────


def make_action_node(node_name: str):
    """Create a LangGraph node function for a standard Action Node.

    Used for Data_Engineer, Model_Engineer, and Evaluator.
    System_Architect has its own node function (with bootstrap).
    """

    def node_fn(state: AgentState) -> dict:
        return _run_react_loop(node_name=node_name, state=state)

    node_fn.__name__ = node_name.lower()
    node_fn.__doc__ = f"Action Node: {node_name}"
    return node_fn


# ── System_Architect Node ────────────────────────────────────────────────


def system_architect_node(state: AgentState) -> dict:
    """System_Architect node with workspace bootstrap on first entry.

    First entry: creates workspace dir, runs git init + uv init,
    copies dataset from staging path, sets workspace_dir in state.
    Re-entry: workspace already exists, runs ReAct loop directly.
    """
    workspace_dir = state.get("workspace_dir", "")
    messages: list[dict] = list(state.get("messages", []))
    first_entry = not workspace_dir

    if first_entry:
        staging_path = state.get("handoff_message", "")
        workspace_dir = _bootstrap_workspace(staging_path)

        # Look up medal thresholds for this competition
        competition_id = state.get("competition_id", "")
        medals = get_medal_thresholds(competition_id)
        if medals:
            direction = "lower is better" if medals["is_lower_better"] else "higher is better"
            medal_block = (
                f"\n\nMedal Score Targets ({direction}):\n"
                f"  Gold:   {medals['gold']}\n"
                f"  Silver: {medals['silver']}\n"
                f"  Bronze: {medals['bronze']}\n"
                f"  Median: {medals['median']}\n"
                "Write these into the Medal Targets section of ml_rules.md."
            )
        else:
            medal_block = (
                "\n\nMedal targets: not available for this competition."
            )

        # Annotate the first user message with workspace + medal info
        bootstrap_note = (
            "\n\n---\n"
            f"[System] Workspace bootstrapped at: {workspace_dir}\n"
            "Dataset files placed in: data/raw/\n"
            "git and uv initialized. All tool paths are relative to workspace root."
            f"{medal_block}"
        )
        if messages and messages[0]["role"] == "user":
            content = messages[0]["content"]
            if isinstance(content, str):
                messages[0] = {
                    "role": "user",
                    "content": content + bootstrap_note,
                }
            else:
                # Content is a list of blocks — append a text block
                messages[0] = {
                    "role": "user",
                    "content": list(content)
                    + [{"type": "text", "text": bootstrap_note}],
                }
        else:
            messages.insert(0, {"role": "user", "content": bootstrap_note.strip()})

    # Build effective state for the ReAct loop
    effective_state = {
        **state,
        "workspace_dir": workspace_dir,
        "messages": messages,
    }
    # On first entry Router hasn't run yet — force Opus tier
    if first_entry:
        effective_state["target_model"] = "opus"

    # Architect should finish in ~15-20 tool rounds (EDA + write 3 files + commit).
    # Cap at 25 to prevent runaway EDA loops.
    result = _run_react_loop(
        node_name="System_Architect", state=effective_state, recursion_limit=25,
    )
    result["workspace_dir"] = workspace_dir
    return result


def _bootstrap_workspace(staging_path: str) -> str:
    """Create and initialize a competition workspace.

    Creates directory structure per spec_memory.md section 0,
    runs git init + uv init, copies dataset from staging_path
    into data/raw/.

    Returns absolute path to the new workspace directory.
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    workspace_name = f"competition_{timestamp}"
    workspace_dir = os.path.join(WORKSPACE_ROOT, workspace_name)

    # Create workspace directory structure
    for subdir in ("data/raw", "data/processed", "src", "models", "logs"):
        os.makedirs(os.path.join(workspace_dir, subdir), exist_ok=True)

    # Symlink project prompts into workspace so read_file("prompts/...") works.
    # Resolves the path mismatch between workspace (/tmp/...) and project root.
    project_prompts = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts"
    )
    workspace_prompts = os.path.join(workspace_dir, "prompts")
    if os.path.isdir(project_prompts) and not os.path.exists(workspace_prompts):
        os.symlink(project_prompts, workspace_prompts)

    # git init + set user config (required in containers with no global git config)
    subprocess.run(["git", "init"], cwd=workspace_dir, capture_output=True, check=False)
    subprocess.run(
        ["git", "config", "user.name", "MLE Agent"],
        cwd=workspace_dir, capture_output=True, check=False,
    )
    subprocess.run(
        ["git", "config", "user.email", "agent@mle-bench.local"],
        cwd=workspace_dir, capture_output=True, check=False,
    )

    # uv init with pinned Python — avoids picking up conda/system interpreters.
    # Strip VIRTUAL_ENV and CONDA_PREFIX so uv uses its own managed Python.
    clean_env = {
        k: v for k, v in os.environ.items()
        if k not in ("VIRTUAL_ENV", "CONDA_PREFIX", "CONDA_DEFAULT_ENV")
    }
    subprocess.run(
        ["uv", "init", "--python", "3.13"],
        cwd=workspace_dir,
        capture_output=True,
        text=True,
        check=False,
        env=clean_env,
    )

    # Copy dataset from staging path if available.
    # Green agent packages data under home/data/ inside the tar.
    if staging_path and os.path.isdir(staging_path):
        # Prefer home/data/ subdir if it exists (green agent tar layout)
        data_src = os.path.join(staging_path, "home", "data")
        if not os.path.isdir(data_src):
            data_src = staging_path  # fallback: flat staging dir

        raw_dir = os.path.join(workspace_dir, "data", "raw")
        for item in os.listdir(data_src):
            src_path = os.path.join(data_src, item)
            dst_path = os.path.join(raw_dir, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dst_path)

    return workspace_dir


# ── Router_Brain Node ────────────────────────────────────────────────────


def router_brain_node(state: AgentState) -> dict:
    """Router_Brain: context cleansing + routing decision.

    1. Append messages -> all_messages (via reducer), wipe messages
    2. Wipe micro_tasks
    3. Increment iteration_count
    4. Check iteration budget — force END if exceeded
    5. Call Haiku with assembled Router input block
    6. Parse JSON response, set state fields
    """
    messages = state.get("messages", [])
    iteration_count = state.get("iteration_count", 0) + 1
    workspace_dir = state.get("workspace_dir", ".")
    current_phase = state.get("current_phase", "architecture")
    handoff_message = state.get("handoff_message", "")

    # Context cleansing: feed messages to all_messages reducer, wipe active
    state_update: dict = {
        "all_messages": list(messages),  # operator.add reducer appends
        "messages": [],                  # wipe active history
        "micro_tasks": [],               # wipe ephemeral tasks
        "iteration_count": iteration_count,
    }

    _init_wall_clock()
    log.info(
        "[Router] Iteration %d/%d | Phase: %s [%.1f min elapsed]",
        iteration_count, MAX_ITERATIONS, current_phase, _elapsed_min(),
    )

    # Safety circuit breaker
    if iteration_count > MAX_ITERATIONS:
        state_update.update({
            "current_phase": "END",
            "target_model": "sonnet",
            "handoff_message": (
                f"Iteration budget ({MAX_ITERATIONS}) exceeded. Routing to END."
            ),
        })
        return state_update

    # Assemble Router input block
    router_input = assemble_router_input(
        current_phase=current_phase,
        handoff_message=handoff_message,
        iteration_count=iteration_count,
        workspace_dir=workspace_dir,
    )

    # Call Haiku for routing decision
    system = assemble_system_prompt("Router_Brain")
    response = call_llm(
        tier="haiku",
        system=system,
        messages=[{"role": "user", "content": router_input}],
    )

    # Parse JSON routing decision
    response_text = _extract_text(response)
    decision = _parse_router_json(response_text)

    next_node = decision.get("next_node", "END")
    raw_model = decision.get("target_model", "claude-sonnet-4-6")
    rewind_reason = decision.get("rewind_reason")

    # Map model ID to tier name
    tier = _REVERSE_MODEL_MAP.get(raw_model, "sonnet")

    # Build handoff message for next node
    if rewind_reason:
        new_handoff = rewind_reason
    else:
        new_handoff = f"Proceed with {next_node} phase."

    # Map next_node to phase label
    new_phase = _PHASE_MAP.get(next_node, current_phase)

    state_update.update({
        "current_phase": new_phase,
        "target_model": tier,
        "handoff_message": new_handoff,
    })

    log.info("[Router] -> %s (tier=%s, phase=%s) [%.1f min]", next_node, tier, new_phase, _elapsed_min())
    return state_update


def _parse_router_json(text: str) -> dict:
    """Extract JSON routing decision from Router response text.

    Handles JSON in markdown code blocks, bare JSON, or embedded
    JSON objects. Falls back to routing to END on parse failure.
    """
    # Try code block first (```json ... ```)
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try bare JSON
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try finding any JSON object in the text
    match = re.search(r"\{[^{}]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fallback — route to END
    return {
        "next_node": "END",
        "target_model": "claude-sonnet-4-6",
        "rewind_reason": None,
    }
