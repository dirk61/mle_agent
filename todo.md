# todo.md — MLE Agent Development Checklist

> Each task cross-references the spec section to read. Read it when starting that task — not before.
> Mark `[x]` and commit after each completed group. Update `progress.txt` at session end.

## Phase 1: Foundation
- [x] Add core dependencies (`langgraph`, `anthropic`). Verify `uv sync --locked`. — Ref: CLAUDE.md §7
- [x] Define LangGraph State TypedDict (messages, all_messages, handoff_message, current_phase, target_model, iteration_count) — Ref: spec_state.md §3
- [x] Implement LLM client wrapper: Anthropic API call with dynamic model selection from `target_model` — Ref: spec_LLM.md

## Phase 2: Tool Layer
- [x] Implement `run_bash_with_truncation` (subprocess, timeout, 8K truncation with first/last 2K preservation) — Ref: spec_tool.md §1
- [x] Implement file tools: `read_file`, `write_file`, `edit_file_chunk` (find-replace with uniqueness check) — Ref: spec_tool.md §2
- [x] Implement `dynamic_task_manager` (push/pop/complete/update/list on State queue) — Ref: spec_tool.md §3
- [x] Implement `Universal_ToolNode`: dispatch tool calls from LLM response, return results to messages — Ref: spec_state.md → Node 0
- [x] Verify: test script exercising each tool with dummy inputs — Ref: CLAUDE.md §5

## Phase 3: Prompt System
- [x] Implement prompt loader: read static bases from `prompts/nodes/` and protocol snippets from `prompts/protocols/` at startup. Update Dockerfile to `COPY prompts prompts`. — Ref: spec_prompting.md → Templates Reference, Implementation Note
- [x] Implement prompt assembly: `static_base + wake_up + sign_off + ml_rules` for Action Nodes; handle first System_Architect entry (no ml_rules yet) — Ref: spec_prompting.md → Implementation Note
- [x] Implement Router input block assembly: read `ml_progress.txt` from workspace, format structured block (CURRENT_PHASE, HANDOFF_MESSAGE, PROGRESS_EXCERPT, AVAILABLE_NODES, ITERATION_COUNT) — Ref: spec_prompting.md → Router Decision Interface

## Phase 4: Node Implementation
- [x] Implement Action Node wrapper: ReAct loop (LLM call → tool calls? → ToolNode : exit), `recursion_limit`, capture final LLM text as `handoff_message` — Ref: spec_state.md → Nodes 3-5, Graph Lifecycle
- [x] Implement System_Architect node: workspace bootstrap (mkdir, git init, uv init), first-entry vs. re-entry — Ref: spec_state.md → Node 1, spec_memory.md §0
- [x] Implement Router_Brain node: append+wipe messages, increment iteration_count, call Haiku with assembled input, parse JSON output, set state fields, enforce iteration budget — Ref: spec_state.md → Node 2

## Phase 5: Graph Construction & A2A Integration
- [ ] Build LangGraph StateGraph: register nodes, define conditional edges (Action↔ToolNode loop, Action→Router, Router→dispatch by next_node, END) — Ref: spec_state.md → Node Definitions (edges)
- [ ] Rewrite `Agent.run()`: extract competition tar, init graph state (instructions→messages, dataset path→handoff_message), invoke graph, on END read `submission.csv` and submit A2A artifact — Ref: spec_state.md → Graph Lifecycle, CLAUDE.md §2

## Phase 6: Build & End-to-End Test
- [ ] Verify Docker build: `uv sync --locked`, image builds with prompts included — Ref: CLAUDE.md §7
- [ ] Full end-to-end test: `cd /home/six004/agentbeats/agentbeats-tutorial && uv run agentbeats-run scenario.toml --show-logs` — Ref: CLAUDE.md §5
