# Sign-Off Protocol — Prompt Snippet

Embed this block verbatim into any Action Node prompt that participates in the shift handover loop. Execute before yielding control back to Router_Brain.

---

## Before exiting this node, execute these steps in order:

```
1. edit_file_chunk("ml_todo.md")
   Mark completed tasks: change [ ] to [x] for everything finished this shift.
   Do not mark tasks complete that are partially done or blocked.

2. write_file("ml_progress.txt")
   Overwrite entirely using this exact format:

   Current Objective: <what you were working on>
   Current State: <DONE | IN_PROGRESS | BLOCKED>
   Blockers:
     [BLOCKER] TYPE: <ImportError|ShapeError|MetricFloor|SubmissionFail|Other>
     MSG: <single line>
     TRACE: <last relevant traceback line or metric value>
   (Omit the Blockers section entirely if there are no blockers.)
   Next Steps: <exact file path or command the next node should start with>

3. run_bash("git add <specific files> && git commit -m '<what changed and why>'")
   Commit only relevant files — no accidental staging of data files or secrets.
   Write the commit message in imperative mood: "Add feature engineering pipeline", not "Added..."

4. Emit handoff_message
   One sentence. Tell Router what you accomplished and what state you're leaving things in.
   Example: "Feature arrays written to /data/processed/; validation AUC 0.823 logged to metrics.txt."
```

If you cannot complete Sign-Off because of an unresolved blocker, write the blocker to `ml_progress.txt` first, then commit the partial state, then emit a handoff noting the blocker type and location.
