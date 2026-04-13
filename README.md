# MLE Agent

## TL;DR

MLE Agent approaches each ML problem EXACTLY the way a real [MLE] (team) would: an Architect reads the problem and designs the pipeline, a Data Engineer builds the features, a Model Engineer trains and iterates, and an Evaluator does sanity checks on the final submission. Each specialist is equipped with sandboxed tools and carries domain-specific ML instincts without assuming fixed solutions — the pipeline adapts to the problem. Above all, a manager (router) coordinates — deciding who's next to work, assigning time and cost budget (Opus vs Sonnet vs Haiku), and pushing back to prior stages if the team is on a wrong route (triggering rewinds). All coordinated through a LangGraph cyclic graph that enables dynamic phase transitions.

The core design challenge mirrors how real [MLE] teams stay aligned across long projects: every agent writes its work to disk — cross-referenced architectural blueprints, task checklists, progress handovers, execution logs — in a git-versioned workspace any agent can audit on re-entry. When the context window compacts between phases, agents re-orient from persistent memory hierarchy rather than losing context. This makes the system robust on complex, multi-phase problems that need long runs. 

Cost-performance balance is a first-class concern: hard iteration caps and prompted ML instincts actively discourage over-optimizing on validation — compute is spent where it generalizes, not where it overfits. A post-run LLM-as-a-judge evaluation is also implemented to enable systematic improvement across competition runs. 

We evaluated across a diverse set of competitions spanning differnt categories and difficulties, showing competitive scores and validating the robustness of this agent design.

---

## Results

| Competition | Category | Difficulty | Score | Gold | Medal |
|---|---|---|---|---|---|
| spaceship-titanic | Tabular classification | 🟩 | 0.83218 | 0.821 | Gold 🥇 |
| aerial-cactus-identification | Image classification | 🟩 | 1.000 | 1.000 | Above median |

🟩 Easy.    🟨 Medium.    🟥 Difficult. 

Benchmarking **STILL ONGOING** across competition categories and difficulty levels.

---

## Architecture

### Agent Graph

```
                              ┌──────────────────────────────────────┐
                              │                                      │
                              ▼                                      │ rewind
                 ┌────────────────────────┐                          │ (spec wrong)
   START ──────► │    System_Architect    │                          │
                 │      Opus · Plan       │                          │
                 └───────────┬────────────┘                          │
                             │                                        │
                             ▼                                        │
                 ┌────────────────────────┐                          │
            ┌──► │      Router_Brain      │ ◄────────────────────────┘
            │    │    Haiku · Manager     │
            │    └──────┬──────┬──────────┘
            │           │      │        │
            │     ┌─────┘      │        └──────────┐
            │     │            │                   │
            │     ▼            ▼                   ▼
            │  ┌──────────┐  ┌──────────┐  ┌───────────┐
            │  │   Data   │  │  Model   │  │ Evaluator │
            │  │Engineer  │  │Engineer  │  │  Haiku    │
            │  │ Sonnet   │  │ Sonnet   │  │           │
            │  ├──────────┤  ├──────────┤  ├───────────┤
            │  │ bash     │  │ bash     │  │ bash      │
            │  │ read_file│  │ read_file│  │ read_file │
            │  │write_file│  │write_file│  │write_file │
            │  │edit_chunk│  │edit_chunk│  │           │
            │  │task_queue│  │task_queue│  │           │
            │  └────┬─────┘  └────┬─────┘  └─────┬─────┘
            │       │             │               │
            └───────┴─────────────┘               │
                      back to Router              │
                                                  ▼
                                                 END
```

### Node Roles

| Node | Model | Responsibility |
|---|---|---|
| **System_Architect** | Opus | Reads competition description, runs data discovery, writes blueprint (`ml_rules.md`, `ml_spec.md`, `ml_todo.md`) |
| **Router_Brain** | Haiku | Reads progress, decides next node, assigns model tier, triggers rewinds on typed blockers |
| **Data_Engineer** | Sonnet | Feature engineering, preprocessing pipeline, produces validated arrays |
| **Model_Engineer** | Sonnet | Model training, CV-guided iteration, hyperparameter tuning, generates `submission.csv` |
| **Evaluator** | Haiku | Submission format validation, metric sanity check, gates final submit |

### Toolset

All Action Nodes (Architect, Data Engineer, Model Engineer, Evaluator) share a focused set of sandboxed tools:

| Tool | Description |
|---|---|
| `run_bash_with_truncation` | Execute shell commands — run scripts, install packages (`uv add`), inspect data. Output truncated to 8K chars with first/last 2K preserved. 30-min timeout. |
| `read_file` | Read workspace files — code, logs, memory files. Never used on raw data CSVs directly. |
| `write_file` | Create or overwrite files — new pipeline scripts, configs, memory files. |
| `edit_file_chunk` | Surgical find-and-replace on existing files. Must match exactly once — preferred over rewriting whole files. |
| `dynamic_task_manager` | Ephemeral micro-task queue (push / pop / complete / list) for tracking sub-steps within a node. Wiped on each Router transition. |

Router_Brain uses no tools — it receives a structured input block and outputs a single JSON routing decision.

---

## Memory & Context System

Each competition run gets an **isolated, git-versioned workspace**. Agents communicate not through shared memory but through files — the same way a real team uses shared docs and version control.

### The Memory Hierarchy

```
workspace/
├── ml_rules.md          ← loaded into EVERY node's system prompt each loop
│                           competition rules, I/O paths, medal targets, constraints
├── ml_spec.md           ← cold storage blueprint (read only when cross-referenced)
│                           architecture decisions, model choice, validation strategy
├── ml_todo.md           ← active task checklist with spec cross-references
│                           [x] completed  [ ] pending  → guides each node's work
├── ml_progress.txt      ← shift handover scratchpad (overwritten each Sign-Off)
│                           Current State · Blockers · Next Steps · Key Findings
├── logs/
│   ├── metrics.txt      ← all CV scores, per-fold results, hyperparameters logged here
│   ├── bash_history.log ← every Python script run and its output (Python + errors only)
│   └── all_messages.jsonl ← full LLM trace, one JSON line per tool round
│                             → feeds post-run LLM-as-a-judge evaluation
└── .git/                ← each node shift = one commit; `git log` is the audit trail
```

### Why This Works

- **Context resets are by design.** The Router wipes active message history on every phase transition. This prevents stale reasoning from bleeding across phases.
- **Files replace memory.** Every agent starts with a Wake-Up protocol: `pwd && ls` → `read ml_progress.txt` → `read ml_todo.md` → `git log`. Within 3 tool calls, any node has full context.
- **Cold storage prevents bloat.** `ml_spec.md` is only read when a task explicitly references it (`Ref: ml_spec.md → Section 2.1`). A long spec doesn't load on every iteration.
- **Git = truth.** If an agent claims it completed a task but didn't commit, the next node sees uncommitted files in `git status` and knows not to trust the claim.

---

## Repository Structure

```
mle_agent/
├── src/
│   ├── agent.py              # Entry point: unpack tar, init graph, submit artifact
│   ├── graph.py              # LangGraph StateGraph: nodes, edges, conditional routing
│   ├── nodes.py              # Node implementations: ReAct loop, Architect, Router
│   ├── state.py              # AgentState TypedDict (LangGraph shared state)
│   ├── llm.py                # Tiered LLM dispatch (Opus / Sonnet / Haiku)
│   ├── tools.py              # Tool implementations + Anthropic schemas
│   ├── tool_node.py          # Universal tool dispatcher
│   ├── prompts.py            # Prompt loader + assembly (static + protocols + ml_rules)
│   ├── medal_thresholds.py   # Pre-computed medal scores for all 82 competitions
│   ├── executor.py           # A2A task lifecycle
│   └── server.py             # A2A HTTP server entry point
├── prompts/
│   ├── nodes/                # Static system prompt per node
│   │   ├── architect.md
│   │   ├── router.md
│   │   ├── data_engineer.md
│   │   ├── model_engineer.md
│   │   └── evaluator.md
│   ├── protocols/
│   │   ├── wake_up.md        # pwd · progress · todo · git log
│   │   └── sign_off.md       # update todo · write progress · commit · handoff
│   └── dynamic/
│       └── ml_rules_template.md  # Architect fills this per competition
├── specs/                    # Design specifications (cold storage)
├── Dockerfile
├── amber-manifest.json5      # AgentBeats deployment config
└── pyproject.toml
```




---

## Design Decisions

### Why multi-agent over single-shot / tree-search?

Tree-search approaches win by sampling many independent solutions and keeping the best. This works well on simple problems where the full solution fits in one script. It breaks down on complex problems requiring multi-stage pipelines — a specialist agent can build 300 lines of well-tested preprocessing code that a single-script generator would rush. Our approach trades sampling breadth for reasoning depth: each specialist builds on the prior's artifacts, with the option to rewind rather than restart entirely.

### Why file-based memory over in-context state?

LangGraph state is wiped by the Router on each phase transition — intentionally. Keeping 50 tool rounds of model training conversation in context when the Evaluator just needs to check a CSV format is wasteful and noisy. Files are the shared medium: `ml_progress.txt` is a 10-line handover note, not a transcript. `ml_todo.md` tells the next agent exactly what's done. `git log` is an immutable audit trail. Any agent can re-orient from scratch in 3 tool calls.



