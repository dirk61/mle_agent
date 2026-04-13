# Handoff Context: Autonomous Memory Architecture for `mle_agent`

I am bringing in the memory architecture specification for the `mle_agent`. This section defines how the agent maintains context, tracks progress, and manages its own cognitive load during long-running machine learning tasks (e.g., MLE-bench competitions).

The overarching philosophy is "Recursive Agentic Memory": The `mle_agent` must operate with the same best practices as an autonomous AI developer. It does not rely purely on internal state variables; instead, it dynamically generates and manages a file-based macro-memory system, supplemented by a tool-based micro-memory system.

Please integrate the following architecture and operating mechanisms into the `spec.md`:

## 1. Macro-Memory (The File-Based Workspace)
Upon starting a new machine learning problem, the `mle_agent` autonomously generates and maintains these files:
* **`ml_rules.md`:** The agent's persistent System Prompt, just like CLAUDE.md for Claude Code. It contains the primary overview for the specific ML competition problem, file architectures, I/O boundaries, version controls, and hard constraints. This is loaded into context on every loop.
* **`ml_spec.md`:** The technical blueprint (Cold Storage). The agent writes this after initial EDA to document the chosen ML architecture, pipelines, and models.
* **`ml_todo.md` (The Submodule Tracker):** The high-level project roadmap. Tasks track verifiable submodules, features or pipeline stages (e.g., `[x] Implement data processing pipeline`). **Crucially, tasks must include explicit cross-references to the blueprint** (e.g., `Ref: ml_spec.md -> Section 3.2`). This enables context-efficient "lazy loading" of instructions.
* **`ml_progress.txt`:** The "Shift Handover" scratchpad. An overwritten file tracking the immediate state: *Current Objective*, *Current Blocker/Traceback*, and *Next Step*.


## 2. Micro-Memory (The Dynamic Runtime Tool)
To handle immediate, granular tasks without constantly overwriting files, the agent relies on a tool-based dynamic to-do list.
* **Dynamic Task Manager (Tool):** A tool function allowing the agent to push, pop, and update micro-tasks in real-time (e.g., the 5-10 logical steps to write a specific PyTorch script) acting as an ephemeral execution scratchpad. 

## 3. The Interaction Protocol (Operating Mechanism)
The `mle_agent` must be instructed to interact with its macro-memory using these strict, state-machine rules to prevent context collapse:

* **The Wake-Up Protocol:** At a fresh context window or a compacted cotext window, the agent MUST pick up the current progress of the project by reading `ml_progress.txt` and `ml_todo.md` to ground itself in the current state. It **MUST** also execute `git status` and `git log -n 5` to understand recent codebase changes and ensure it is building on top of a stable commit.
* **Cold Storage Read Limits:** `ml_spec.md` is strictly "Cold Storage." The agent MUST NOT read it during routine code generation. It may ONLY read specific sections if explicitly cross-referenced by an active `ml_todo.md` item, or when architecting a brand new phase of the pipeline.
* **The Cascade Rule:** If the agent makes a fundamental change to the ML pipeline and updates `ml_spec.md`, it MUST immediately trigger a review and update of `ml_todo.md` to ensure the task list accurately reflects the new blueprint.
* **The Sign-Off State Sync:** Before making a submission, pausing execution, or ending a complex sub-task (like finishing a submodule in ml_todo.md), the agent MUST overwrite ml_progress.txt with its new immediate state, update checkboxes in ml_todo.md, and execute a git commit -m "[Descriptive Message]" to snapshot the stable codebase.