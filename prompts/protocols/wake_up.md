# Wake-Up Protocol — Prompt Snippet

Embed this block verbatim into any Action Node prompt that participates in the shift handover loop (Data_Engineer, Model_Engineer, Evaluator). System_Architect runs a lighter variant (no ml_progress.txt to read on first entry).

---

## On every entry to this node, before doing anything else:

Execute these steps in order — sequence matters:

```
1. run_bash_with_truncation("pwd && ls -la")
   Orient yourself: confirm your working directory and see what files exist.

2. read_file("ml_progress.txt")
   Understand where the last shift ended: what was the objective, what blocked it, what the next step was.

3. read_file("ml_todo.md")
   Understand the active roadmap. Identify which tasks are yours in the current phase.
   Tasks describe WHAT to achieve — use your own judgment on HOW to implement them.
   If a task references ml_spec.md for context, read only that specific section.

4. run_bash_with_truncation("git status && git log -n 5 --oneline")
   Ground yourself in what actually exists on disk. If git shows unexpected files or uncommitted changes,
   investigate before proceeding — do not assume the previous state is clean.
```

Do **not** read `ml_spec.md` during Wake-Up unless your active `ml_todo.md` task contains an explicit reference such as:
> `Ref: ml_spec.md → Section 2.1`

Cold storage is loaded on demand, not on entry.

If `ml_progress.txt` contains a `[BLOCKER]` entry that was not resolved by a previous node, treat that as your first task before advancing.
