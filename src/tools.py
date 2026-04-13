"""Tool implementations and Anthropic tool schemas for the MLE Agent.

All tools operate relative to a workspace_dir (the competition workspace).
See spec_tool.md for authoritative parameter definitions and constraints.
"""

from __future__ import annotations

import os
import subprocess

# ── Constants ────────────────────────────────────────────────────────────────

MAX_OUTPUT_CHARS = 8_000
TRUNCATION_KEEP = 2_000
MAX_FILE_LINES = 10_000

INTERACTIVE_BLOCKLIST = frozenset(
    {"vim", "vi", "nano", "emacs", "less", "more", "top", "htop"}
)

# ── 1. Execution Tools ──────────────────────────────────────────────────────


def run_bash_with_truncation(
    command: str,
    timeout_seconds: int = 120,
    *,
    workspace_dir: str = ".",
) -> str:
    """Execute a shell command with output truncation and timeout."""
    # Block interactive commands
    first_token = command.strip().split()[0] if command.strip() else ""
    if first_token in INTERACTIVE_BLOCKLIST:
        return (
            f"[ERROR: Interactive command '{first_token}' is not allowed. "
            "Use non-interactive alternatives.]"
        )
    if command.strip() in ("python", "python3"):
        return (
            "[ERROR: Interactive Python REPL is not allowed. "
            "Use 'uv run python script.py' instead.]"
        )

    # Strip venv/conda vars so workspace's own uv/venv isn't confused by the
    # parent server process's environment.
    env = {
        k: v for k, v in os.environ.items()
        if k not in ("VIRTUAL_ENV", "CONDA_PREFIX", "CONDA_DEFAULT_ENV")
    }

    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_seconds,
            cwd=workspace_dir,
            text=True,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return f"[ERROR: Command timed out after {timeout_seconds}s]\n{command}"
    except Exception as e:
        return f"[ERROR: Failed to execute command]\n{e}"

    output = result.stdout or ""
    exit_code = result.returncode

    # Truncate if combined output exceeds limit
    if len(output) > MAX_OUTPUT_CHARS:
        output = (
            output[:TRUNCATION_KEEP]
            + "\n...[OUTPUT TRUNCATED]...\n"
            + output[-TRUNCATION_KEEP:]
        )

    if exit_code != 0:
        return f"[ERROR: Command failed with exit code {exit_code}]\n{output}"

    return output


# ── 2. File Operations ───────────────────────────────────────────────────────


def read_file(
    file_path: str,
    *,
    workspace_dir: str = ".",
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:
    """Read file contents, optionally a line range (1-indexed, inclusive)."""
    full_path = file_path if os.path.isabs(file_path) else os.path.join(workspace_dir, file_path)

    if not os.path.isfile(full_path):
        return f"[ERROR: File not found: {file_path}]"

    try:
        with open(full_path, encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        return f"[ERROR: File is not valid UTF-8: {file_path}]"
    except Exception as e:
        return f"[ERROR: Cannot read file: {e}]"

    if len(lines) > MAX_FILE_LINES and start_line is None:
        return (
            f"[ERROR: File has {len(lines)} lines (limit: {MAX_FILE_LINES}). "
            "Use start_line/end_line or run_bash_with_truncation with head/tail.]"
        )

    if start_line is not None or end_line is not None:
        start = (start_line - 1) if start_line else 0
        end = end_line if end_line else len(lines)
        lines = lines[start:end]

    return "".join(lines)


def write_file(
    file_path: str,
    content: str,
    *,
    workspace_dir: str = ".",
) -> str:
    """Create or overwrite a file with the given content."""
    full_path = file_path if os.path.isabs(file_path) else os.path.join(workspace_dir, file_path)
    parent = os.path.dirname(full_path)

    try:
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return f"[ERROR: Cannot write file: {e}]"

    return f"File written: {file_path} ({len(content)} chars)"


def edit_file_chunk(
    file_path: str,
    search_string: str,
    replace_string: str,
    *,
    workspace_dir: str = ".",
) -> str:
    """Surgical find-and-replace. search_string must match exactly once."""
    full_path = file_path if os.path.isabs(file_path) else os.path.join(workspace_dir, file_path)

    if not os.path.isfile(full_path):
        return f"[ERROR: File not found: {file_path}]"

    try:
        with open(full_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return f"[ERROR: Cannot read file: {e}]"

    count = content.count(search_string)

    if count == 0:
        return (
            f"[ERROR: search_string not found in {file_path}. "
            "Check leading whitespace and exact content.]"
        )
    if count > 1:
        return (
            f"[ERROR: search_string found {count} times in {file_path}. "
            "Provide a larger, more unique search_string.]"
        )

    new_content = content.replace(search_string, replace_string, 1)

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        return f"[ERROR: Cannot write file: {e}]"

    return f"Edit applied to {file_path}"


# ── 3. Micro-Memory Management ──────────────────────────────────────────────

_VALID_ACTIONS = frozenset({"push", "pop", "complete", "update", "list"})


def dynamic_task_manager(
    action: str,
    micro_tasks: list[dict],
    task_id: str | None = None,
    description: str | None = None,
) -> tuple[str, list[dict]]:
    """Manage the ephemeral micro-task queue. Returns (result_text, updated_tasks)."""
    if action not in _VALID_ACTIONS:
        return (
            f"[ERROR: Invalid action '{action}'. Must be one of: {sorted(_VALID_ACTIONS)}]",
            micro_tasks,
        )

    tasks = [dict(t) for t in micro_tasks]  # shallow copy each dict

    if action == "push":
        if not task_id or not description:
            return ("[ERROR: 'push' requires both task_id and description]", tasks)
        if any(t["task_id"] == task_id for t in tasks):
            return (f"[ERROR: task_id '{task_id}' already exists]", tasks)
        tasks.append(
            {"task_id": task_id, "description": description, "status": "pending"}
        )
        return (f"Task '{task_id}' added.", tasks)

    if action == "pop":
        if not tasks:
            return ("[INFO: Task queue is empty]", tasks)
        removed = tasks.pop(0)
        return (f"Popped task: {removed['task_id']} — {removed['description']}", tasks)

    if action == "complete":
        if not task_id:
            return ("[ERROR: 'complete' requires task_id]", tasks)
        for t in tasks:
            if t["task_id"] == task_id:
                t["status"] = "completed"
                return (f"Task '{task_id}' marked as completed.", tasks)
        return (f"[ERROR: task_id '{task_id}' not found]", tasks)

    if action == "update":
        if not task_id:
            return ("[ERROR: 'update' requires task_id]", tasks)
        for t in tasks:
            if t["task_id"] == task_id:
                if description:
                    t["description"] = description
                return (f"Task '{task_id}' updated.", tasks)
        return (f"[ERROR: task_id '{task_id}' not found]", tasks)

    # action == "list"
    if not tasks:
        return ("[INFO: Task queue is empty]", tasks)
    lines = [f"  [{t['status']}] {t['task_id']}: {t['description']}" for t in tasks]
    return ("Current tasks:\n" + "\n".join(lines), tasks)


# ── Anthropic Tool Schemas ───────────────────────────────────────────────────

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "run_bash_with_truncation",
        "description": (
            "Execute a shell command. Output over 8000 chars is truncated "
            "to the first and last 2000 chars (stack traces at the end are "
            "preserved). Use 'uv run python script.py' for Python scripts. "
            "Returns combined stdout/stderr."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Maximum execution time in seconds.",
                    "default": 120,
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": (
            "Read a file's contents. Use for code and tracker files. "
            "Do not use on raw data files (.csv, .parquet)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path to the file.",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Line number to begin reading (1-indexed).",
                },
                "end_line": {
                    "type": "integer",
                    "description": "Line number to stop reading (inclusive).",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "write_file",
        "description": (
            "Create a new file or overwrite an existing file entirely. "
            "Prefer edit_file_chunk for modifications to existing files."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path to the file.",
                },
                "content": {
                    "type": "string",
                    "description": "Complete file content to write.",
                },
            },
            "required": ["file_path", "content"],
        },
    },
    {
        "name": "edit_file_chunk",
        "description": (
            "Surgical find-and-replace in an existing file. "
            "search_string must match exactly once. "
            "Preferred over write_file for modifying existing code."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path to the file.",
                },
                "search_string": {
                    "type": "string",
                    "description": "Exact text block currently in the file to replace.",
                },
                "replace_string": {
                    "type": "string",
                    "description": "New text to insert in place of search_string.",
                },
            },
            "required": ["file_path", "search_string", "replace_string"],
        },
    },
    {
        "name": "dynamic_task_manager",
        "description": (
            "Manage an ephemeral micro-task queue for complex multi-step work. "
            "Tasks are wiped on phase transitions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["push", "pop", "complete", "update", "list"],
                    "description": "The operation to perform.",
                },
                "task_id": {
                    "type": "string",
                    "description": "Unique identifier for the task (required for push/complete/update).",
                },
                "description": {
                    "type": "string",
                    "description": "Task description (required for push, optional for update).",
                },
            },
            "required": ["action"],
        },
    },
]
