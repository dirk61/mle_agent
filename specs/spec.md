# Technical Specification — MLE Agent (`spec.md`)

> **Cold Storage.** Do not read during routine coding. Only read when explicitly cross-referenced by `todo.md`, or when architecting a new phase. See CLAUDE.md §9 for the full protocol.

---

## System Overview

The `mle_agent` is an autonomous ML engineering agent. It receives a competition problem and dataset from the Green Agent via A2A, runs a multi-node LangGraph to build an ML pipeline, and returns a `submission.csv`.

Three design principles drive every decision:
- **Context preservation over raw capability** — nodes forget; memory files and commit history don't.
- **Tiered intelligence** — Opus for strategy, Sonnet for execution, Haiku for routing.
- **Fail-forward discipline** — blockers are typed so the Router can route without interpretation.

---

## Architecture Sketch

```
Green Agent ──▶ System_Architect ──▶ Router_Brain ──┬──▶ Data_Engineer ──┐
                                          ▲          ├──▶ Model_Engineer  │
                                          └──────────┴──▶ Evaluator ──────┤
                                                                          │
                              Universal_ToolNode ◀── all Action Nodes ◀──┘

Shared file layer: ml_rules.md · ml_spec.md · ml_todo.md · ml_progress.txt
Runtime state:     LangGraph State { messages · all_messages · handoff_message · current_phase · target_model · iteration_count }
```

---

## Major Components

### Nodes (LangGraph workers)
Five nodes. Three tiers.

| Node | Model | Role |
|---|---|---|
| `System_Architect` | Opus | Blueprints the ML pipeline; writes all macro-memory files |
| `Router_Brain` | Haiku | Wipes context, reads signals, dispatches next node + model tier |
| `Data_Engineer` | Sonnet | EDA, feature engineering, produces clean arrays on disk |
| `Model_Engineer` | Sonnet (Opus on rewind) | Training, inference, metric logging |
| `Evaluator` | Sonnet | Independent QA — format, leakage, validation score; always routes to Router |
| `Universal_ToolNode` | — | Non-LLM executor; returns results back to calling node |

→ Full node definitions, edge rules, and dry-run trace: **`spec_state.md`**

### LLM Dispatch
Router sets `target_model` in State; nodes never self-select. Credentials via `CLAUDE_API_KEY` in `sample.env`.

→ Model IDs and tier rationale: **`spec_LLM.md`**

### Tool Layer
All tools hosted by `Universal_ToolNode`. Action Nodes request calls; results are appended back to `messages`.

| Tool | Purpose |
|---|---|
| `run_bash_with_truncation` | Shell, Python, Git — with timeout + output cap |
| `read_file` | Line-range reads; forbidden on raw data files |
| `write_file` | New files or full config overwrites only |
| `edit_file_chunk` | Surgical find-replace — mandatory for modifying existing pipelines |
| `dynamic_task_manager` | Ephemeral in-State micro-task queue; wiped on every Router handoff |

→ Parameters, failure modes, and usage constraints: **`spec_tool.md`**

### Memory
Two layers working together:

**Macro (files):** `ml_rules.md` loads every loop; `ml_todo.md` and `ml_progress.txt` load on Wake-Up; `ml_spec.md` is cold — only read on explicit cross-reference.

**Micro (State):** `dynamic_task_manager` queue tracks within-loop sub-steps; wiped on phase transition.

**Protocols:** Wake-Up (read trackers → read git) and Sign-Off (mark done → overwrite progress → commit → emit handoff) are enforced on every Action Node entry and exit.

→ Full memory architecture, workspace isolation, and operating rules: **`spec_memory.md`**. Protocol step sequences: **`prompts/protocols/`**.

### Prompting
Prompts assembled at runtime as `static_base + ml_rules_content`. Layer 1 (static, in `prompts/nodes/`) defines node character. Layer 2 (dynamic, from `ml_rules.md`) encodes the current competition.

Router input is a structured harness-assembled block; output is exactly one JSON: `{ next_node, target_model, rewind_reason }`. Blockers in `ml_progress.txt` use a typed schema (`[BLOCKER] TYPE: ...`) so Haiku can route without interpretation.

→ Prompting contracts, Router interface, blocker vocabulary, and template locations: **`spec_prompting.md`**

---

## Key Invariants

1. Router appends `messages` to `all_messages` before wiping — the full trace is always recoverable for post-run LLM-as-a-judge evaluation.
2. `ml_spec.md` is cold — a `ml_todo.md` cross-reference is the only read unlock.
3. `edit_file_chunk` for existing pipelines — never overwrite established scripts with `write_file`.
4. Blockers are typed — free-text fails under Haiku.
5. Commit on every Sign-Off — recovery always starts from a stable state.
6. Each competition runs in an isolated workspace — see `spec_memory.md` §0.
