---
name: reflect
description: Capture a durable lesson from a finished stretch of work, for ANY skill or workflow. Use this whenever the user types /learn or /reflect, or says things like "save what we learned", "remember this for next time", "capture the lesson", "reflect on how that went", or wants a skill to improve based on how it was just used. It reads the current conversation from a start point (A) to now (B), extracts what was tried, accepted, changed, or rejected, and appends a dated entry to a central JOURNAL.md plus the used skill's own LEARNINGS.md when one exists. Works alongside any other skill. It cannot run in the background or watch skills passively — it only acts when invoked, and only sees the current conversation. Do not use it for writing feature code or unrelated file edits.
---

# Reflect

Turn a finished stretch of work into a lesson that lasts — for any skill or ad-hoc workflow, not just one. This is the general version of the per-skill "learn from itself" loop.

## What this is and isn't (read before running)

- **It does not run in the background and cannot watch other skills passively.** Nothing executes between the user's messages, so there is no way to silently record a skill as it runs. This skill only does something when the user invokes it.
- **It reads the current conversation, from point A to point B.** Everything in that span is already in context — it doesn't need to have "recorded" anything, it can just read it.
- **A and B must be in the same conversation.** Context is per-conversation and isolated. If the work happened in an earlier chat, this skill can't see it — the only bridge across sessions is the saved journal that skills read on future runs.

Never imply otherwise to the user.

## Point A and Point B

- **B** = now, the moment the user runs `/learn` or `/reflect`.
- **A** = the start point of what to learn from. Determine it in this order:
  1. If the user set a marker earlier ("mark A", "start learning from here"), use that point.
  2. Otherwise, use the point where the most recent skill/workflow began.
  3. If neither is clear, use the whole conversation and say so.

Tell the user, once, that they can type "mark A" mid-conversation to pin the start, and `/learn` to capture.

## Step 1 — Identify what happened between A and B

- Which skill(s) or workflow ran in that span? There may be more than one (e.g. website-builder, then cold-caller). Handle each separately.
- For each: what was the task, and what got produced.

## Step 2 — Extract the lesson

For each skill/workflow, pull out concretely:
- **Tried** — what approach was taken.
- **Accepted** — what the user kept or liked.
- **Changed / Rejected** — what they corrected, overrode, or threw out. This is the strongest signal; weight it most.
- **Lesson** — the reusable rule, preference, or pattern for next time.

Be specific and short. "User prefers a warmer palette" is weak; "User rejected terracotta accents twice, chose brass — default to metallic accents for this brand" is a lesson. Cut anything generic.

## Step 3 — Write it (routing to the right place)

Write to **both** destinations when they apply:

1. **Central journal** — append a dated entry to `JOURNAL.md` in this skill's folder. Tag every entry with the skill name so entries stay filterable across many skills.
2. **Per-skill learnings** — if the skill that was used has its own `LEARNINGS.md` (website-builder does), append the skill-specific lesson there too, so that skill picks it up on its next run via its own "read learnings first" step. If it doesn't have one and the user wants that skill to actually learn, offer to add a lightweight "read your learnings first" step to it — see `references/routing.md`.

Use this entry format in both places:
```
## YYYY-MM-DD — [skill: <name>] — <subject>
- Task: ...
- Accepted: ...
- Changed/Rejected: ...
- Lesson: ...
```

If several skills ran in one A→B span, write one entry per skill, not a merged blob.

## Step 4 — Persist (this is what makes it "learning")

State the constraint plainly, every time, because it decides whether the lesson survives:

- The write only carries into future conversations if it's stored somewhere **persistent and writable**: Claude Code / Cowork against a local folder, or a git repo.
- **In the claude.ai chat sandbox the filesystem resets between conversations.** So the update won't survive on its own there. In that case, output the updated `JOURNAL.md` (and any `LEARNINGS.md`) and tell the user to commit it to the repo where the skills live.
- If running in an environment with git and a shell, offer to commit and push the change — commands are in `references/routing.md`.

Never claim the skill silently rewrites itself. It improves only because it appends to a log, and only if that log is stored somewhere that lasts.

## A note on separation

Personal preferences and a client's brand are different memories. If the user does client work, keep per-client journals (or strip lessons back to generic patterns) rather than pooling everyone's taste into one file. Flag this the first time client work shows up.

For routing details, the "add a learnings step to another skill" snippet, git commands, and the web-UI alternative, read `references/routing.md`.
