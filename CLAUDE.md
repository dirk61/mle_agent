# CLAUDE.md — MLE Agent Development Guide

## 1. Competition Overview
This is a **purple agent** on the AgentBeats MLE-Bench leaderboard. Agents solve ML problems autonomously. The green agent (`mle-bench-green` at `/home/six004/agentbeats/mle-bench-green/`) orchestrates each assessment: it sends competition data, receives the submission, and scores it.

## 2. Green Agent Interaction Protocol
The A2A communication protocol is already implemented in `src/agent.py`. Refer to that file for exact message formats and implementation details.

**The Assessment Loop:**
* **Receive:** The Green Agent provides task instructions and a dataset archive (`competition.tar.gz`).
* **Validate (Debug):** Before finalizing, you can verify your output format by sending a `status_update` message containing the text `"validate"` and your `submission.csv`. This can print the validation result to stdout.
* **Submit:** Call `updater.add_artifact(...)` with `submission.csv`. The Green Agent will score the submission and return a JSON artifact containing your metrics.

## 3. Ethics
Adhere to standard open-source and dataset licensing.

## 4. Repository Architecture
**Root:** `/home/six004/agentbeats/mle_agent/`
Do not modify files outside this root. Update this section if the structure changes.

* `src/agent.py`: MAIN LOGIC — edit freely; extend with new files/dirs as needed.
* `src/executor.py`: Task lifecycle — edit ONLY if changing task handling.
* `src/server.py`: Agent metadata — edit ONLY to update agent card.
* `src/messenger.py`: A2A messaging utility — DO NOT EDIT.
* `tests/`: A2A conformance tests — DO NOT REMOVE.
* `.github/workflows/test-and-publish.yml`: CI — edit ONLY to change build logic.
* `Dockerfile`: Edit ONLY for base image or system deps.
* `pyproject.toml` / `uv.lock`: See Section 7 for strict dependency rules.
* `amber-manifest.json5`: Edit ONLY for image tag or env changes.
* `specs/`: Design specifications (cold storage — read on demand, not routinely).
  * `spec_state.md`: LangGraph node definitions and context protocols.
  * `spec_tool.md`: Tool definitions and usage constraints.
  * `spec_memory.md`: Macro- and micro-memory architecture.
  * `spec_LLM.md`: Model tier assignments.
  * `spec_prompting.md`: Prompting architecture, node contracts, Router interface.
* `prompts/`: Pre-written prompt bases — do not edit during a competition run.
  * `nodes/`: Static system prompt base for each node (`architect`, `router`, `data_engineer`, `model_engineer`, `evaluator`).
  * `protocols/`: Wake-Up and Sign-Off ritual snippets (embedded in node prompts).
  * `dynamic/ml_rules_template.md`: Fillable template for competition-specific `ml_rules.md`.

## 5. Local Testing
Local testing = full end-to-end assessment, not unit testing. For quick function-level checks, use plain Python scripts.

```bash
# Run full assessment with logs (both agents auto-started)
cd /home/six004/agentbeats/agentbeats-tutorial
uv run agentbeats-run scenario.toml --show-logs
```

**[MANDATORY VERIFICATION] - Toy Data Testing:**
After finishing or editing any new phase, function, or submodule, you **MUST** write and execute a temporary Python script using minimal dummy data. You must verify dimensional correctness, data types, and logic *before* moving on.

## 6. Local Storage (Strict Limit)
System disk (`/`) has ~13 GB free. Check `df -h /` before any large download.
**RULE:** Large files (datasets, models, caches) must be written to `/data1/six004/`. Never write large downloads directly under `/home/six004/`.

**Execution Pattern:**
1. `mv /home/six004/<name> /data1/six004/<name>`
2. `ln -s /data1/six004/<name> /home/six004/<name>`

## 7. Dependency Management (Strict uv Conformance)

The build environment strictly relies on `uv`. All dependencies must be resolvable via `pyproject.toml` and `uv.lock`, or the Docker build will fail.

* **Standard Flow:** Prefer `uv add <package>` to automatically update configuration files. 
* **Edge-Case Installations:** If a specific package requires `uv pip install` or `pip install` to resolve correctly, you are permitted to use them. However, you **must** immediately manually add that package to `pyproject.toml` and run `uv lock` to synchronize the environment.
* **Pre-Commit Verification:** Before completing any task that alters dependencies, you must ensure `uv sync --locked` executes successfully. Never edit `uv.lock` manually.


## 8. Version Control

**Remote:** `https://github.com/dirk61/mle_agent` — pushing to `main` triggers CI and publishes `ghcr.io/dirk61/mle_agent:latest`.

- Commit locally after each completed, tested sub-module or feature, or made a major change or fixed a major bug.
- Stage all relevant files 
- Never auto-push — user decides when to push
- Write descriptive commit messages (what and why)

## 9. Shift Handover Memory Protocol
Your context window might reset between sessions. You MUST follow this protocol to maintain continuity.

**The Memory Stack:**
1. `CLAUDE.md`: The permanent rules and constraints (this file).
2. `progress.txt`: Immediate state (Objective, Blockers, Next Steps).
3. `todo.md`: Task checklist with cross-references to the spec.
4. `spec.md`: Technical blueprint (Cold Storage).



**[WAKE-UP] - Execute immediately on new prompt:**
* Read `progress.txt` and `todo.md`.
* Run `git status` and `git log -n 5`.

**[READ LIMITS & UPDATES] - `spec.md` is Cold Storage:**
* NEVER read `spec.md` for routine coding or debugging. 
* ONLY read specific sections of `spec.md` if explicitly referenced by a `todo.md` item, or when architecting a brand new phase.
* **CASCADE RULE:** If you modify `spec.md`, you MUST immediately review and update `todo.md` to ensure the task list accurately reflects the new architectural blueprint.

**[SIGN-OFF] - Execute before ending your turn or asking for feedback:**
1. **Mark Done:** Change `[ ]` to `[x]` in `todo.md` for completed work.
2. **State Sync:** Overwrite `progress.txt` strictly using this format:
   * *Current Objective:* [...]
   * *Current State/Blockers:* [Include specific errors/tracebacks if stuck]
   * *Next Steps:* [Exact command or file the next agent should start with]
3. **Commit:** `git commit -m` if a sub-task is complete or stable.