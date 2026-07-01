---
name: deepdive
description: Run an agentic prospect research dossier or draft a new industry scoring rubric using pipeline/agent_deepdive.py. Use this skill whenever the user types /deepdive, asks to "research this prospect", "run a dossier on", "deep dive on this business", "look into [shop] before I call them", or wants a new industry added to the scoring pipeline (e.g. "can we score dental clinics", "build a rubric for gyms"). This wraps a real Python agent that hits Google Maps, Firecrawl, and Claude — it costs real API credits and takes real time, so confirm scope before running it across a large batch of prospects.
---

# Deep-Dive Agent

A thin conversational wrapper around `pipeline/agent_deepdive.py` — the actual agentic
tool lives in that file, not in this skill. This skill's job is knowing when to run it,
how to run it, and — more importantly — how to read the result the way Matthew would,
not just dump raw JSON back at him.

## Step 0 — Check the environment before running anything

This executes real API calls (Anthropic, Google Maps, Firecrawl) and costs real money.
Before running:
- Confirm `.env` has `ANTHROPIC_API_KEY`, `GOOGLE_MAPS_API_KEY`, `FIRECRAWL_API_KEY` set.
- If the user wants to run this across more than a handful of prospects in one go, say
  so and confirm they actually want that — this is a deep-dive tool for prospects worth
  real attention, not a bulk scraper. (The cheap one-shot `scorer.py` inside `run_pipeline`
  is what bulk scoring already uses; don't replace that flow with this one.)

## Running a dossier

```bash
python -m pipeline.agent_deepdive dossier "<Business Name>" --city <City> --niche <niche>
```

`--city` defaults to Calgary, `--niche` defaults to barbershop — override niche for
anything else (e.g. `--niche "dental clinic"`). The agent decides its own tool-call
order; don't try to script its steps for it.

## Running the scorer generator directly

```bash
python -m pipeline.agent_deepdive generate-scorer "<industry>" --context "<brief context>"
```

Only run this directly if the user explicitly asks for a new industry rubric ahead of
time. Otherwise leave it — the dossier agent calls this itself mid-run if it hits a
niche with no existing `prompts/scoring_<slug>.txt`.

## Step 1 — How to read the dossier back (this is the part that matters)

Don't just paste the raw JSON at Matthew. Translate it the way he'd actually triage it:

1. **Social presence outranks funnel polish, for barbershops specifically.** If
   `raw_signals.social` shows no Instagram found, lead with that — it's a bigger red flag
   than a clunky booking link, per how this whole pipeline was built. Don't bury it under
   the funnel_score breakdown.
2. **Verdict decides the next move, not just a label:**
   - `Priority` / `Qualified` → this is a real call-list candidate. Offer to hand the
     dossier's `outreach_hook` and `leaks_found` straight to the `cold-caller` skill to
     draft the actual script — that's the natural next step, don't make Matthew re-explain
     the prospect's problem to a second skill.
   - `Maybe` → not a cold-call yet. Suggest the lighter first touch (an Instagram DM or
     email referencing the specific leak) rather than jumping straight to a phone script.
   - `Skip` → say so plainly and why (usually `util_score = 0` — at capacity or a product
     problem, not a funnel problem). Don't sugarcoat a bad lead as "worth a look."
3. **Flag low-confidence numbers as low-confidence.** `new_signals_not_in_schema.confidence_notes`
   exists specifically because things like utilization % genuinely can't be observed from
   outside. If it's there, say "this score is a best-evidence estimate, not a measured
   number" — don't present it with false certainty.
4. **If a new rubric got auto-generated** (`generate_industry_scorer` fired mid-run),
   say so explicitly and flag the new `prompts/scoring_<slug>.txt` for a human read-through
   before it gets relied on for real scoring — it's AI-drafted, not yet field-tested.
5. **Don't call `insert_lead()` yourself.** `agent_deepdive.py` deliberately doesn't write
   to Supabase — offer it as the next step ("want me to save this to the leads table?")
   rather than doing it silently. `dossier["lead_record"]` is already shaped for
   `insert_lead()` with no reshaping needed.

## What this skill is not

It doesn't replace `run_pipeline()` / the scheduled bulk scoring — that's still the cheap
one-shot `scorer.py` path for volume. This is for a prospect Matthew is specifically
about to spend real outreach effort on and wants the fuller picture first.
