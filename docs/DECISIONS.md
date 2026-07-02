# Decision Log — Barbershop Agency

This file is the single source of truth for *why* things are built the way they are. Code
shows what exists; this file shows why it exists that way instead of some other way. When
you're onboarding a new session of Claude Code, reviewing with Matthew, or just can't
remember why you made a call three weeks ago — this is where you look.

## How to use this file

- Add a new entry every time you make a real decision: an architecture choice, a process
  change, a "we tried X and switched to Y." Not every code change needs an entry — only ones
  where you picked between real alternatives for a reason worth remembering.
- Keep entries short. Context, options considered, what you picked, why. A few sentences
  each is enough — this is a log, not a report.
- Newest entries at the top.
- If a later decision reverses an earlier one, don't delete the old entry — add a new one and
  note which entry it supersedes. The history of *why we changed our mind* is often more
  useful than the current state alone.
- At the end of any Claude Code session where real decisions got made, ask it directly:
  *"Append today's decisions to DECISIONS.md."* This is the same discipline the `learn`/
  `reflect` skill already uses for per-skill lessons — this file is that same pattern, applied
  to architecture instead of skill behavior.

---

## 2026-07-01 — Skills folder location needs fixing

**Context:** Existing skills (`cold-caller`, `website-builder`, `learn`) live at
`skills/<name>/SKILL.md` at the repo root. Claude Code auto-discovers project-level skills
from `.claude/skills/<name>/SKILL.md` — one directory level different.

**Decision:** Relocate skills into `.claude/skills/`.

**Why:** The current location matches the convention used in claude.ai's chat sandbox (where
these skills were likely originally built), not Claude Code's project-skill convention. Until
moved, Claude Code won't auto-trigger them by relevance — they'd need to be invoked some other
way, defeating the point.

---

## 2026-07-01 — Skills vs. Subagents: how we split AI-assisted work

**Decision:** Creative or judgment-heavy tasks where we want to watch the output form and
correct it mid-stream (cold call scripts, website builds) stay as in-thread **Skills**.
Bounded tasks where we just want a result back, and don't need to see the intermediate steps,
become isolated **Subagents**.

**Why:** Skills run inside the main conversation — same context window, full visibility, easy
to steer. Subagents run in a separate context window and only return a summary — good for
"go check this and tell me what you found" work that would otherwise just fill up the main
session with stuff we'll never re-read (see `docs/SUBAGENTS.md` for the specific ones
proposed).

---

## 2026-07-01 — CLAUDE.md added for persistent session context

**Decision:** Added `CLAUDE.md` at the repo root — auto-read by Claude Code at the start of
every session. Covers repo purpose, a one-line summary of each file in `pipeline/`, our
commit conventions, the rule against silently changing scoring logic, and current pipeline
state (e.g. "auto-scrape is intentionally paused, don't turn it back on without asking").

**Why:** Without it, every new Claude Code session starts from zero and has to re-derive
context from the code alone — slower, and risks a future session "fixing" something that was
actually an intentional decision (like the paused cron below).

---

## 2026-07-01 — Commit convention: Conventional Commits, one logical change per commit

**Decision:** All commits use `type: short imperative summary` (`feat`, `fix`, `chore`,
`docs`), body explains *why* not *what*. One task/change = one commit — no bundling unrelated
changes together.

**Why:** With only one of us (Wesley) actually writing code, commit history is the audit
trail Matthew and future-you rely on to understand what changed and when. Bundled commits
make that history useless for anything except "everything changed at once."

---

## 2026-07-01 — Documentation split: repo docs vs. Google Drive

**Decision:** Technical/feature documentation (how the pipeline works, cadence rules, what
each script does) lives in `docs/` inside the repo, as markdown. Business documentation
(partnership terms, pricing, sales scripts, offer decks) lives in Google Drive, shared with
Matthew.

**Options considered:** All documentation in Drive (simpler for Matthew, but drifts out of
sync with code silently). All documentation in the repo (single source, but Matthew would
need git familiarity for the business-side docs he edits directly).

**Why:** Rule of thumb — if it changes when the code changes, it lives in the repo (version
controlled, diffable, can't silently go stale). If it changes when a business decision
changes, it lives in Drive. GitHub renders markdown in-browser, so Matthew can read repo docs
without needing git knowledge, he just can't casually edit them there.

---

## 2026-07-01 — Curated, rotating search queries instead of one fixed query

**Context:** The pipeline queried a fixed `barbershop Calgary` search every day. Google
Places Text Search caps around 60 results per distinct query, so after the first run, nearly
every subsequent run just hit `lead_exists()` filtering with little new to find.

**Decision:** Built `pipeline/search_queries.py` — a curated list combining niche variants
(barbershop, mens grooming, fade specialist, barber studio, hair salon) with Calgary
neighborhoods (Kensington, Beltline, Bridgeland, etc.), selectable at trigger time instead of
hardcoded in `railway.toml`.

**Why:** Each niche/neighborhood combination counts as a distinct query to the Places API, so
rotating through them surfaces shops the city-wide search's result cap was hiding, instead of
re-scraping an exhausted pool.

---

## 2026-07-01 — Manual scrape trigger instead of automatic daily cron

**Context:** Railway's cron ran the pipeline every morning at 8am against the same fixed
query. By the time this was reviewed, the query pool was exhausted and 16–30 Qualified/
Priority leads were sitting uncontacted in Supabase — the lead pipeline was outpacing our
outreach capacity.

**Options considered:**
1. Keep daily auto-run as-is
2. Reduce cron frequency (e.g. weekly) but keep it automatic
3. Remove the cron entirely; pipeline only runs when manually triggered, with a chosen query

**Decision:** Option 3 — `cronSchedule` removed from `railway.toml`. Pipeline now runs only
via manual trigger (`python -m pipeline.run`), which shows a menu built from
`search_queries.py` if no explicit query is passed.

**Why:** A scraped lead's outreach hook ("we noticed your booking is broken *right now*")
weakens the longer it sits uncontacted. Generating leads faster than a two-person team can
act on them just creates a decaying backlog, not progress.

**Resume condition:** Bring automatic/frequent scraping back only once uncontacted
Qualified/Priority leads drop below roughly 5.

---

## Template for new entries

```
## YYYY-MM-DD — Short decision title

**Context:** What situation prompted this decision.

**Options considered:** (if relevant) what alternatives were on the table.

**Decision:** What we actually did.

**Why:** The reasoning — this is the part worth preserving most.
```
