# Routing, wiring, and persistence

## 1. Finding a skill's LEARNINGS.md

When routing a lesson (Step 3), check whether the used skill has its own log:
- Claude Code / local: look for `<skills-dir>/<skill-name>/LEARNINGS.md`.
- If it exists, append the skill-specific lesson there (so that skill's own "read learnings first" step picks it up next run).
- Always also append to this skill's central `JOURNAL.md`.

## 2. Making another skill able to learn

A skill only *benefits* from lessons if it reads them at startup. `reflect` can *record* a lesson about any skill, but a skill that has no "read learnings" step won't consume it. If the user wants a target skill to actually improve, offer to add this block near the top of that skill's SKILL.md, and create an empty `LEARNINGS.md` beside it:

```markdown
## Step 0 — Read your own learnings first
Before starting, open LEARNINGS.md in this skill folder and read it. Apply
accepted patterns, avoid rejected ones. After finishing, append what the user
accepted, changed, or rejected. This only persists if the skill folder is
writable and persistent (Claude Code / Cowork / a git repo).
```

Only edit a skill the user owns and asks you to change. Don't modify Anthropic-provided skills.

## 3. Multi-skill sessions

If several skills ran between A and B, write one journal entry per skill (each tagged with its own name), and route each to its own LEARNINGS.md if present. Don't merge unrelated lessons into one entry.

## 4. Persisting via git (when a shell is available)

From the repo that holds the skills:
```bash
git add reflect/JOURNAL.md website-builder/LEARNINGS.md   # whatever changed
git commit -m "reflect: capture lesson from <subject>"
git push
```
Confirm with the user before committing if the repo has other pending changes.

## 5. No shell / claude.ai chat

The sandbox resets between conversations, so writes don't survive. Instead:
- Output the updated `JOURNAL.md` (and any `LEARNINGS.md`) in full.
- Tell the user to commit it to the repo where the skills live (web UI: open the file on GitHub, Edit, paste, Commit).

## 6. Client vs personal separation

Keep a client's brand lessons out of the personal journal. Options: a per-client journal file (`JOURNAL.<client>.md`), or only record generic, transferable patterns for client work. Raise this the first time client work is being reflected on.
