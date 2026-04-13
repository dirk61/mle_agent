# MLE Agent
This Agent approaches each ML problem EXACTLY the way a real [MLE] (team) would: an Architect reads the problem and designs the pipeline, a Data Engineer builds the features, a Model Engineer trains and iterates, and an Evaluator does sanity checks on the final submission. Each specialist is equipped with sandboxed tools and carries domain-specific ML instincts without assuming fixed solutions — the pipeline adapts to the problem. Above all, a manager (router) coordinates — deciding who's next to work, assigning time and cost budget (Opus vs Sonnet vs Haiku), and pushing back to prior stages if the team is on a wrong route (triggering rewinds). All coordinated through a LangGraph cyclic graph that enables dynamic phase transitions.

The core design challenge mirrors how real [MLE] teams stay aligned across long projects: every agent writes its work to disk — cross-referenced architectural blueprints, task checklists, progress handovers, execution logs — in a git-versioned workspace any agent can audit on re-entry. When the context window compacts between phases, agents re-orient from persistent memory hierarchy rather than losing context. This makes the system robust on complex, multi-phase problems that need long runs. 

Cost-performance balance is a first-class concern: hard iteration caps and prompted ML instincts actively discourage over-optimizing on validation — compute is spent where it generalizes, not where it overfits. A post-run LLM-as-a-judge evaluation is also implemented to enable systematic improvement across competition runs. 

We evaluated across a diverse set of competitions spanning differnt categories and difficulties, showing competitive scores and validating the robustness of this agent design.



---

## Results

mle_bench leaderboard https://agentbeats.dev/agentbeater/mle-bench

| Competition | Category | Difficulty | Score | Gold | Medal |
|---|---|---|---|---|---|
| spaceship-titanic | Tabular | 🟩 | 0.83218 | 0.821 | Gold 🥇 |
| aerial-cactus-identification | Image Classification | 🟩 | 1.000 | 1.000 | Above median |

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

All agents (except Router) can run bash commands, read/write files, and edit code. Here's what they have:

| Tool | What it does |
|---|---|
| **bash** | Run commands: train scripts, install packages, check data shapes. Output limited to 8K chars. LLM-defined timeout window. |
| **read_file** | Read code, logs, memory files. Not used on raw data files. |
| **write_file** | Create new Python scripts, configs, tracking files. |
| **edit_file_chunk** | Find-and-replace edits in existing code. |
| **task_queue** | Track sub-tasks within a phase. Cleared when moving to the next phase. |



---

## Memory & Context System

Each competition gets its own isolated workspace with git version control. Instead of agents talking to each other directly, they leave notes in shared files — like a real team using Google Docs and Git.

### What's on Disk

```
workspace/
├── ml_rules.md          ← The rules of this specific competition
│                           (reloaded each phase for fresh context)
├── ml_spec.md           ← High-level architecture decisions
│                           (read only when a task needs it)
├── ml_todo.md           ← Checklist of what needs to happen
│                           (marks tasks [x] done or [ ] pending)
├── ml_progress.txt      ← Handoff note from the last phase
│                           (what was done, what's blocking, what's next)
├── logs/
│   ├── metrics.txt      ← Training scores, hyperparameters
│   ├── bash_history.log ← Every script that ran + its output
│   └── all_messages.jsonl ← Complete trace of everything (for post-run analysis)
└── .git/                ← Full history; each phase = one commit
```

### Why This Design Works

- **No context bloat.** The system forgets old messages at the end of each phase, but reads fresh files to re-orient. No stale reasoning carries over.
- **Fast handoffs.** New agents start fast: `pwd && ls` → read progress → read todo → check git log. Full context in 3 steps.
- **Trust the files.** If an agent says a task is done but didn't commit it, the next agent sees uncommitted changes and knows not to trust the claim.
- **Lazy loading.** The long spec only gets read when a task says "see ml_spec.md section X." Keeps prompt size down.

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

### Why specialists instead of one big agent?

A single agent that tries to do everything either takes too long (trying every angle) or cuts corners (rushing to solutions). Our design: each person does their job well. The Architect spends time on a solid design. The Data Engineer spends time building trustworthy features. The Model Engineer focuses on training. The Evaluator does a final check. Each one can apply deep expertise without getting pulled in five directions. And if something goes wrong, you can send work back to the right person instead of restarting from scratch.

### Why write to disk instead of keeping everything in memory?

Two reasons. First, the system needs to forget old conversations between phases — too much noise. Second, the next agent needs to pick up fast. A 10-line handoff note beats reading 100 messages. Plus git log gives you the full audit trail: who did what, when, and if they committed it.

One more thing: agents can be swapped in and out (different models, different strategies) because they all follow the same file protocol. The code is in `/src/`, the data is in `/data/`, the status is in `ml_progress.txt`. As long as you stick to that contract, you can change the agents.



