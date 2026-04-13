# Handoff Context: State Graph Node Definitions (`spec_state`)

This document defines the discrete workers (nodes) of the `mle_agent`'s LangGraph. To prevent context collapse, **conversation history (`messages`) is wiped upon transitioning between distinct macro-phases**. Context is preserved through local file tracking and a lightweight LangGraph State variable.

## 1. The Macro-Memory Files
The agent maintains its context across wiped sessions using four core files:
* **`ml_rules.md` (The System Prompt):** Persistent rules, I/O boundaries, and competition constraints. Loaded into context on every loop.
* **`ml_spec.md` (Cold Storage Blueprint):** The chosen ML architecture and pipeline design. Only read when explicitly cross-referenced by a task.
* **`ml_todo.md` (Submodule Tracker):** The actionable project roadmap with checkboxes. Must include cross-references to `ml_spec.md`.
* **`ml_progress.txt` (Shift Handover):** An overwritten scratchpad tracking the immediate state: *Current Objective*, *Current Blocker/Traceback*, and *Next Step*.

## 2. Standard Context Protocols
All Action Nodes MUST execute these routines to bridge the amnesia between LangGraph state transitions.

* **Context Start (The "Wake-Up" Protocol):**
  1. Read the LangGraph `handoff_message`.
  2. Run `bash("git status && git log -n 5")` to ground the LLM in the physical codebase.
  3. Read `ml_progress.txt` and `ml_todo.md` to identify the exact sub-task and active blockers.

* **Context End (The "Sign-Off" Protocol):**
  1. Overwrite `ml_progress.txt` with the new immediate state (or blocker).
  2. Check off completed items in `ml_todo.md`.
  3. Run `bash("git commit -m '[Descriptive Message]'")` to snapshot the codebase.
  4. Generate a 1-2 sentence `handoff_message` for the LangGraph State and yield to Router.

## 3. LangGraph State Schema (The "Clipboard")
The dictionary passed between nodes contains:
* `messages`: The active ReAct loop history (wiped on macro-node transitions).
* `handoff_message`: A brief instruction passed from the exiting node to the next.
* `current_phase`: The active phase tracking.
* `target_model`: Dictated by the Router (e.g., `haiku`, `opus` or `sonnet`) to optimize cost vs. reasoning capabilities. Use `haiku` for routing.

## 4. Global Toolset
Action Nodes share these core primitives, executed by the `Universal_ToolNode`:
* `read_file` / `write_file` / `edit_file_chunk`
* `run_bash_with_truncation`: Executes shell commands/Python. Enforces timeouts and truncates outputs into limited characters.
* `dynamic_task_manager`: The micro-memory to-do list. **Usage Note:** This is highly dynamic. Agents are expected to push initial steps, check them off, and if an error forces a pivot, pop the old steps and push new adaptive steps mid-loop.

---

## Node Definitions

### 0. `Universal_ToolNode` (The Execution Engine)
* **Definition:** A non-LLM LangGraph node that strictly executes the tool calls requested by the Action Nodes.
* **Persona:** N/A
* **Tools Access:** N/A (Hosts the tools).
* **Edges:** Returns strictly back to the calling Action Node.
* **On Start:** Receives tool arguments from the LLM.
* **On Exit:** Appends execution results (stdout, stderr, file contents) back into the calling node's `messages` array.

### 1. `System_Architect` (The Planner)
* **Definition:** The strategic core. Translates the Kaggle problem into a concrete ML pipeline and updates the blueprint if fundamental assumptions fail.
* **Persona:** Lead MLE Architect. Break the project into verifiable submodules. 
* **Tools Access:** Full Global Toolset. May use `run_bash` strictly for *Data Discovery* (not pipeline building).
* **Edges:** Routes strictly to `Router_Brain`.
* **On Start:** Reads raw Kaggle prompt or failure logs. 
* **On Exit:** Writes/updates `ml_rules.md`, `ml_spec.md`, and `ml_todo.md`. Passes a `handoff_message` summarizing the strategy.

### 2. `Router_Brain` (Traffic Cop & Model Dispatcher)
* **Definition:** Orchestration node. Decides *which* phase happens next and *what model tier* is required.
* **Persona:** Project Manager. Review trackers. Select the next node and LLM tier (use Opus for architecture/rewinds, Sonnet for execution). Do not write code.
* **Tools Access:** `read_file`, `route_to_node`.
* **Edges:** `Data_Engineer`, `Model_Engineer`, `Evaluator`, or `System_Architect`.
* **On Start (Context Cleanser):** Reads `handoff_message`, `ml_todo.md`, and `ml_progress.txt`. **Wipes the `messages` array.**
* **On Exit:** Sets `target_model`. Generates a *new* `handoff_message` directing the next node.

### 3. `Data_Engineer` (Action Node)
* **Definition:** Executes EDA, feature engineering, and data processing.
* **Persona:** Meticulous Data Engineer. Maintain strict I/O hygiene. Program defensively. Use text-based summaries; never print full dataframes.
* **Tools Access:** Full Global Toolset.
* **Edges:** Internal loop to `Universal_ToolNode`. Exits to `Router_Brain`.
* **On Start:** Execute **Context Start Protocol**.
* **On Exit:** Execute **Context End Protocol**.

### 4. `Model_Engineer` (Action Node)
* **Definition:** Executes model architecture, training loops, and inference generation.
* **Persona:** Senior ML Engineer. Optimize for signal-to-noise ratio in terminal outputs. Log metrics to disk. Rely strictly on cleaned data arrays.
* **Tools Access:** Full Global Toolset.
* **Edges:** Internal loop to `Universal_ToolNode`. Exits to `Router_Brain`.
* **On Start:** Execute **Context Start Protocol**.
* **On Exit:** Execute **Context End Protocol**.

### 5. `Evaluator` (The Gatekeeper)
* **Definition:** Independent QA. Checks validation metrics, data leakage, and submission formats.
* **Persona:** Independent, skeptical Code Reviewer. You do not train models. Verify test set integrity and strict Kaggle format compliance.
* **Tools Access:** Full Global Toolset.
* **Edges:** Routes to `Router_Brain` (triggering rewind) or **END** (successful submission).
* **On Start:** Execute **Context Start Protocol**.
* **On Exit:** * *If Rewinding:* Write explicit blocker to `ml_progress.txt`. Pass a targeted `handoff_message` explaining the failure back to the Router.
    * *If Passing:* Verify `submission.csv` exists, update final trackers, and trigger system termination.



## Appendix: High-Level Dry Run (Kaggle Housing Prices)

This trace demonstrates the macro-loop handoffs and the context protocols in action.

**1. The Blueprint Phase**
* **Active Node:** `System_Architect`
* **Action:** Reads the Kaggle prompt. Uses `bash` to run `df.info()` for discovery. Realizes the dataset is tabular with heavy skew.
* **Sign-Off:** Creates `ml_rules.md`, `ml_spec.md`, and `ml_todo.md`. 
* **State Handoff:** *"Initial spec created. Dataset is tabular. Pass to Data Engineer."*

**2. The First Route**
* **Active Node:** `Router_Brain`
* **Context Cleanser:** Wipes `messages`. Reads the State Handoff and `ml_todo.md`. 
* **Action:** Routes to `Data_Engineer`.

**3. The Data Pipeline**
* **Active Node:** `Data_Engineer`
* **Wake-Up:** Reads Handoff. Runs `git log` (sees the Architect's commit). Reads `ml_todo.md`. 
* **Action:** Writes `data_prep.py` to impute missing values and log-transform the target. Runs it.
* **Sign-Off:** Checks off `ml_todo.md`. Runs `git commit -m "feat: complete imputation"`. Updates `ml_progress.txt`.
* **State Handoff:** *"Data pipeline complete. clean_train.csv saved."*

**4. The Error & The Pivot**
* **Active Node:** `Router_Brain` routes to `Model_Engineer`.
* **Active Node:** `Model_Engineer`
* **Wake-Up:** Runs Git protocol. Reads Handoff. 
* **Action:** Writes `train.py` for XGBoost. Runs it. 
* **The Bug:** `Universal_ToolNode` returns a massive Pandas error: `ValueError: DataFrame contains categorical data (Neighborhood)`.
* **Sign-Off:** Realizes it cannot fix data pipelines. Leaves `ml_todo.md` unchecked. Overwrites `ml_progress.txt` with: *"BLOCKER: Categorical column 'Neighborhood' is unencoded. XGBoost failed."*
* **State Handoff:** *"Modeling blocked by data encoding issue. Returning to Router."*

**5. The Rewind**
* **Active Node:** `Router_Brain`
* **Action:** Wipes context. Reads `ml_progress.txt`. Sees the explicit blocker regarding data encoding. 
* **Action:** Routes *backward* to `Data_Engineer`.

**6. The Fix**
* **Active Node:** `Data_Engineer`
* **Wake-Up:** Reads `ml_progress.txt`. Sees its own mistake. 
* **Action:** Uses `edit_file_chunk` to add One-Hot Encoding to `data_prep.py`. Re-runs the script. 
* **Sign-Off:** `git commit -m "fix: add one-hot encoding"`. Clears the blocker in `ml_progress.txt`.
* **State Handoff:** *"Encoding bug fixed. clean_train.csv overwritten."*

**7. Completion**
* **Router_Brain:** Routes to `Model_Engineer`.
* **Model_Engineer:** Successfully trains model. Generates draft `submission.csv`. Hands off to Router.
* **Router_Brain:** Routes to `Evaluator`.
* **Evaluator:** Wake-up. Runs `evaluate.py`. Confirms validation score is sane and `submission.csv` strictly matches Kaggle format. Triggers system termination.