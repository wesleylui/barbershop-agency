import re
import json
import argparse
import difflib
from pathlib import Path
from datetime import datetime, timezone

import anthropic
from dotenv import load_dotenv

from pipeline.maps import get_shops
from pipeline.scraper import scrape_website

load_dotenv()

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
BASE_SCORING_PROMPT = (PROMPTS_DIR / "scoring.txt").read_text()

# Sonnet, not Haiku — scorer.py's one-shot classification is a cheap job that fits
# Haiku. This is a multi-step agent that has to reason about *why* a funnel is
# broken and draft a whole new rubric from scratch, so it gets the heavier model.
MODEL = "claude-sonnet-4-5-20250929"

INSTAGRAM_RE = re.compile(r"https?://(?:www\.)?instagram\.com/[\w\.\-/]+", re.IGNORECASE)
FACEBOOK_RE = re.compile(r"https?://(?:www\.)?facebook\.com/[\w\.\-/]+", re.IGNORECASE)

# Cap on scraped content echoed back into the conversation. run.py's own lead
# dict already truncates scraped_content to 5000 chars before storage, so this
# just applies that same ceiling one step earlier — no reason to let a large
# page balloon every subsequent turn's input tokens for the rest of the loop.
MAX_SCRAPE_CHARS = 5000


# Reused verbatim by both the dossier loop and the generator prompt below —
# wrapped in a helper so both call sites get prompt caching (see cached_system())
# instead of copy-pasting the cache_control block twice.
def cached_system(text: str) -> list:
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


# ---------------------------------------------------------------------------
# Plain-function tools the agent can call. Each one degrades gracefully like
# the rest of the pipeline — never raises, returns an empty/falsy result and
# logs instead.
# ---------------------------------------------------------------------------

def find_business(name: str, city: str, niche: str = "barbershop") -> dict:
    """Targeted single-place lookup, built on top of maps.get_shops rather than
    changing maps.py. Places Text Search already ranks close name matches near
    the top when you query '<name> <city>', so we search on the business name
    itself first and pick the closest match client-side; if that comes back
    empty we retry with the niche + city as a fallback."""
    try:
        shops = get_shops(name, city) or []
    except Exception as e:
        print(f"[agent_deepdive] find_business primary search failed: {e}")
        shops = []

    if not shops:
        try:
            shops = get_shops(niche, city) or []
        except Exception as e:
            print(f"[agent_deepdive] find_business fallback search failed: {e}")
            shops = []

    if not shops:
        print(f"[agent_deepdive] No Maps results for '{name}' in '{city}'")
        return {}

    names = [s.get("name", "") for s in shops]
    close = difflib.get_close_matches(name, names, n=1, cutoff=0.4)
    if close:
        match = next(s for s in shops if s.get("name") == close[0])
    else:
        match = shops[0]
    return match


def detect_social_links(content: str) -> dict:
    """Regex scan for Instagram/Facebook links. No content or no matches is
    itself a real signal — per Matthew's own operating knowledge, most
    barbershop clientele comes through Instagram, not the website, so a shop
    with no discoverable Instagram link is a bigger red flag than a mediocre
    booking flow.

    Not exposed as its own agent tool (it was in the first version of this
    file — see design note in the report). It runs automatically as part of
    scrape_site's result instead, because making it a separate tool call
    forced the model to echo the entire scraped page back out as a JSON tool
    argument just to ask a deterministic regex to run on it — pure output-
    token waste for zero reasoning benefit. Still a plain, directly testable
    function; just not a round-trip."""
    if not content:
        return {
            "instagram_found": False,
            "instagram_url": None,
            "facebook_found": False,
            "facebook_url": None,
        }
    ig = INSTAGRAM_RE.search(content)
    fb = FACEBOOK_RE.search(content)
    return {
        "instagram_found": bool(ig),
        "instagram_url": ig.group(0) if ig else None,
        "facebook_found": bool(fb),
        "facebook_url": fb.group(0) if fb else None,
    }


def _slugify(industry: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", industry.lower()).strip("_")
    return slug or "industry"


def _rubric_path_for(niche: str) -> Path:
    return PROMPTS_DIR / f"scoring_{_slugify(niche)}.txt"


# ---------------------------------------------------------------------------
# Industry rubric generation. Rewritten so the model reasons about how the
# industry actually acquires and closes customers BEFORE it drafts scores —
# it used to just relabel the barbershop rubric's booking-platform names,
# which quietly broke for anything that isn't an instant-booking business
# (a contractor's "utilization" isn't a % of slots filled — there are no
# slots. It's closer to how fast they respond to a lead and how backed up
# their project pipeline already is, and a long lead time to start a new job
# is a GOOD demand signal there, the opposite of how "over 90% booked" reads
# for a barbershop). See generate_industry_scorer's docstring for how this
# gets called.
# ---------------------------------------------------------------------------

GENERATOR_SYSTEM_PROMPT = f"""You are designing a new lead-scoring rubric for an AI SMB marketing
agency's qualification pipeline. The agency currently only scores barbershops. You are
extending it to a new industry.

STEP 1 — Before you touch the rubric, figure out how this industry actually gets and closes
customers. Do not assume it works like a barbershop. Ask yourself which of these (or
something else entirely) actually fits:

- INSTANT / SELF-SERVICE booking — the customer picks a specific time slot themselves,
  same-day or short-notice (barbershops, salons, gyms, restaurants). Here "utilization"
  genuinely means % of appointment slots filled, and the funnel is about whether that
  booking widget is easy to use.
- QUOTE / PROJECT business — the customer submits an inquiry or asks for an estimate, the
  business quotes it, and the actual work gets scheduled with its own lead time
  (construction, roofing, remodeling, landscaping, HVAC installs, other contractors). "%
  of slots booked" means nothing here — there is no slot. What actually signals demand is
  closer to: how fast do they respond to an inquiry, how far out is their project
  backlog/lead time, do they even have a quote-request path on the site or is it
  phone-only. A LONG lead time to start a new job is a GOOD demand signal for this kind of
  business (busy, in demand) — the opposite of how "over 90% booked" reads as a cap-out
  problem for a barbershop. Being able to start next week with an empty backlog is closer
  to a red flag.
- Recurring/contract service (cleaning, lawn care, pest control), longer-horizon
  appointment business (dental, legal, medical specialists), or another model entirely —
  reason about THIS industry specifically instead of defaulting to a booking-fill-rate
  model because that's what the reference rubric below uses.

Get this right before you write anything. A wrong assumption here (e.g. treating a
contractor's booked-out project calendar as a funnel problem instead of a demand signal)
makes every downstream score wrong, not just imprecise.

STEP 2 — Draft the rubric. It MUST match the existing rubric's structure and JSON schema
exactly: the same three signals in the same order, the same OUTPUT field names
(team_score, util_score, funnel_score, total_score, verdict, leaks_found, outreach_hook),
and the RULES section (the total_score formula and the verdict point thresholds) UNCHANGED
— these are a normalized 0-10 scale per signal on purpose, so scores stay comparable
across industries no matter what each one measures underneath. What changes is what each
signal actually MEASURES for this industry, based on your Step 1 reasoning. You may adjust
each section header's parenthetical/description to name what it actually measures (e.g.
"SIGNAL 2 — UTILIZATION SCORE (0-10, lead response & project backlog)" instead of forcing
a booking-percentage framing that doesn't apply) — keep the section order and the
underlying JSON field names exactly as they are.

- Ability to pay (team_score) → this industry's real proxy for scale (barbershop:
  chair/barber count; a contractor might be crew size, number of concurrent projects, or
  years in business — pick whatever's actually observable and meaningful for THIS
  industry, not a forced analogy).
- Utilization-equivalent (still the util_score field) → the industry-appropriate demand
  signal identified in Step 1, not a forced "% booked." Re-derive the point thresholds
  around whatever that real signal is (response speed, backlog/lead time, etc.) — don't
  just relabel the barbershop thresholds with new units.
- Funnel quality (funnel_score) → this industry's real conversion mechanism and what
  "broken" looks like for it — an instant booking embed vs. an off-site redirect for a
  barbershop; a missing or clunky quote-request form, phone-only contact with no online
  path, or a slow-to-find estimate tool, for a contractor. Use that industry's own common
  tools/platforms in the inference rules, not the barbershop ones — Setmore/Vagaro/Fresha
  mean nothing to a roofer.

--- EXISTING RUBRIC (barbershop) — reference for STRUCTURE and SCHEMA only, not content to copy verbatim ---
{BASE_SCORING_PROMPT}
--- END EXISTING RUBRIC ---

Output ONLY the new rubric text, in the exact same plain-text format as above (same
section order: SIGNAL 1 — TEAM SCORE, SIGNAL 2 — UTILIZATION SCORE, SIGNAL 3 — FUNNEL
SCORE, INFERENCE RULES FOR FUNNEL SCORE, RULES, OUTPUT). No preamble, no markdown code
fences, no explanation before or after, and no trace of your Step 1 reasoning in the
output — the file you produce gets loaded verbatim as another module's system prompt."""


def generate_industry_scorer(industry: str, context: str = "") -> Path | None:
    """Drafts a new prompts/scoring_<slug>.txt for an SMB industry that doesn't have
    one yet, in the same schema as prompts/scoring.txt. Plain single-call function
    (same shape as scorer.py's score_shop) rather than a multi-turn loop — drafting a
    rubric doesn't need tool use, it needs one well-built prompt.

    Two callers: the standalone `generate-scorer` CLI command (industry known ahead of
    time), and get_scoring_rubric() below, which calls this once, up front, the first
    time a dossier run hits a niche with no existing rubric. It is deliberately NOT a
    tool the dossier agent can call mid-run anymore — see get_scoring_rubric's docstring
    for why that used to be broken."""
    client = anthropic.Anthropic()
    user_message = f"Industry: {industry}\nContext: {context or '(none provided)'}\n\nDraft the new rubric now."

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=1200,
            system=cached_system(GENERATOR_SYSTEM_PROMPT),
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception as e:
        print(f"[agent_deepdive] generate_industry_scorer API error for '{industry}': {e}")
        return None

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1]).strip()

    out_path = _rubric_path_for(industry)
    try:
        out_path.write_text(raw)
    except Exception as e:
        print(f"[agent_deepdive] Failed to write {out_path}: {e}")
        return None

    print(f"[agent_deepdive] Saved new rubric to {out_path}")
    return out_path


def get_scoring_rubric(niche: str, context: str = "") -> str:
    """Resolves which scoring rubric text to use for a niche BEFORE the dossier loop
    starts, instead of leaving the model to decide mid-run whether to call
    generate_industry_scorer.

    This replaces the old design, which had two real problems: (1) the system prompt
    only told the model to generate a new rubric "before finalizing" — nothing forced
    it to happen before scrape_site, so the agent could scrape and reason about funnel
    quality using barbershop-specific criteria (Setmore/Vagaro language, % of slots
    booked) before a construction- or dental-specific rubric ever existed. (2) even when
    the model did call generate_industry_scorer mid-run, the tool result only returned
    the file path it saved to — never the rubric's actual text — so the model could
    never actually use the new rubric to score the business it was in the middle of
    analyzing. The SCORING RUBRIC block baked into its system prompt for that whole run
    stayed the hardcoded barbershop one regardless. The generated file was real and
    useful for *future* runs, but decorative for the run that supposedly triggered it.

    Resolving this up front removes the ambiguity entirely: barbershop (or no niche
    given) always uses the canonical prompts/scoring.txt; any other niche reuses its
    prompts/scoring_<slug>.txt if one already exists (no reason to re-spend an API call
    regenerating a rubric that should stay stable run-over-run for the same industry);
    only a genuinely new industry triggers generate_industry_scorer, and only once,
    here — not buried as a judgment call inside the tool-use loop."""
    slug = _slugify(niche)
    if slug in ("barbershop", "industry", ""):
        return BASE_SCORING_PROMPT

    path = _rubric_path_for(niche)
    if path.exists():
        print(f"[agent_deepdive] Reusing existing rubric for '{niche}': {path}")
        return path.read_text()

    print(f"[agent_deepdive] No rubric exists yet for '{niche}' — generating one before starting the dossier.")
    generated_path = generate_industry_scorer(niche, context)
    if generated_path:
        return generated_path.read_text()

    print(f"[agent_deepdive] Rubric generation failed for '{niche}' — falling back to the barbershop rubric so the run can still proceed (scores will be less accurate for this niche).")
    return BASE_SCORING_PROMPT


# ---------------------------------------------------------------------------
# Agentic dossier loop
# ---------------------------------------------------------------------------

def build_dossier_system_prompt(rubric_text: str) -> str:
    """Was a static module-level constant embedding the barbershop rubric directly.
    Now a function so run_dossier_agent can build it fresh per run from whatever
    get_scoring_rubric() resolved for that specific niche — see that function's
    docstring for why the rubric has to be resolved before this prompt is built,
    not decided by the model mid-conversation."""
    return f"""You are a prospect research analyst for an AI agency that fixes
booking funnels and local visibility for personal service SMBs, starting with barbershops.

Given a business name (and optionally city/niche), gather real signal about it using the
tools available and produce one final structured dossier by calling finalize_dossier
exactly once, last. You decide the order of tool calls and whether to skip a step based
on what you already know — do not follow a fixed sequence blindly. Example judgment call:
if find_business returns no website, skip scrape_site entirely and record that directly as
a funnel signal ("no website at all" is itself the worst-case funnel score per the rubric
below) — don't waste a call scraping nothing.

The SCORING RUBRIC below has already been matched to this business's industry before this
analysis started — if the niche isn't barbershop, this is either a rubric built
specifically for that industry, or the canonical barbershop one used as a fallback. Either
way, use exactly the rubric given below; you do not need to (and cannot) generate or select
a different one mid-run.

SCORING RUBRIC — use this to reason out team_score, util_score, funnel_score and verdict
yourself for lead_record (do not just pattern-match; actually weigh the evidence you
gathered against these rules):

{rubric_text}

Two things this agency's existing one-shot scorer does NOT do, that you must:

1. Social presence. scrape_site's result already includes a "social" field (Instagram/
   Facebook links found via regex, run automatically — you don't need to call anything
   separately for this) — you reason about what it means. Most barbershop clientele comes
   through Instagram, not the website. A shop with no discoverable Instagram is a bigger
   red flag than a mediocre booking flow, not a minor footnote — weigh it that way in your
   summary and leaks_found, and note it even when the rest of the funnel looks fine. (For
   a non-barbershop niche, weigh this using your own judgment of how much that industry's
   customers actually rely on social discovery — it may matter much less for, say, a
   commercial roofing contractor than for a barbershop.)
2. Funnel reasoning, not a rule lookup. Don't just apply the INFERENCE RULES as a
   checklist. Write actual analysis: is the booking/quote-request link an embed or does it
   redirect off-site? Does it look like a specific service gets pre-selected, or does the
   visitor land on something generic and have to figure it out themselves? Is there a
   clear call-to-action a mobile visitor would actually see above the fold, based on how
   the content is structured? Say why it's broken, not just that it is. Put this reasoning
   in funnel_analysis as real prose, a few sentences, not a restated rule.

Be honest in your dossier about what you can't actually know from the outside — e.g.
percent of appointment slots booked (or, for a quote/project business, how far out their
project backlog actually runs) usually cannot be directly observed from a website scrape
or Maps listing. Say so and give your best-evidence estimate rather than stating an
unfounded number with false confidence.

When you call finalize_dossier, lead_record must be filled in completely and must use
exactly the same field names the pipeline's insert_lead() already expects, so Matthew can
call insert_lead(dossier["lead_record"]) directly with no reshaping."""


TOOLS = [
    {
        "name": "find_business",
        "description": (
            "Look up a business by name and city to get its Google Maps place details: "
            "rating, review count, website, phone, address. Call this first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Business name"},
                "city": {"type": "string", "description": "City to search in"},
                "niche": {
                    "type": "string",
                    "description": "Business category, used only as a fallback search if the name search finds nothing. Defaults to 'barbershop'.",
                },
            },
            "required": ["name", "city"],
        },
    },
    {
        "name": "scrape_site",
        "description": (
            "Scrape a website URL and return its markdown content plus an automatic social-link "
            "scan (Instagram/Facebook, found by regex — already done for you in the result, no "
            "separate call needed). Only call this if find_business returned a website."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "finalize_dossier",
        "description": "Call exactly once, last, when you have enough signal. Ends the analysis and returns the final dossier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_name": {"type": "string"},
                "raw_signals": {
                    "type": "object",
                    "description": "Everything gathered, unsynthesized.",
                    "properties": {
                        "place": {"type": "object"},
                        "social": {"type": "object"},
                        "scrape_status": {
                            "type": "string",
                            "enum": ["scraped", "no_website", "scrape_failed"],
                        },
                    },
                },
                "funnel_analysis": {
                    "type": "string",
                    "description": "Prose reasoning about why the funnel is or isn't broken — embed vs redirect, pre-selection, mobile CTA visibility. Not a rule restatement.",
                },
                "summary": {
                    "type": "string",
                    "description": "Synthesized human-readable summary for Matthew, weighing social presence appropriately.",
                },
                "lead_record": {
                    "type": "object",
                    "description": "Exact shape of pipeline.database.insert_lead()'s expected dict — feeds straight in, no reshaping.",
                    "properties": {
                        "shop_name": {"type": "string"},
                        "google_place_id": {"type": "string"},
                        "website_url": {"type": "string"},
                        "phone": {"type": "string"},
                        "address": {"type": "string"},
                        "rating": {"type": "number"},
                        "review_count": {"type": "integer"},
                        "scraped_content": {"type": "string"},
                        "team_score": {"type": "integer"},
                        "util_score": {"type": "integer"},
                        "funnel_score": {"type": "integer"},
                        "total_score": {"type": "integer"},
                        "verdict": {"type": "string", "enum": ["Priority", "Qualified", "Maybe", "Skip"]},
                        "leaks_found": {"type": "array", "items": {"type": "string"}},
                        "outreach_hook": {"type": "string"},
                    },
                },
                "new_signals_not_in_schema": {
                    "type": "object",
                    "description": "Signals this dossier surfaces that leads table columns don't exist for yet (social presence, funnel_analysis detail) — flagged separately so nothing gets silently dropped if Wesley wires this into insert_lead later.",
                },
            },
            "required": ["business_name", "raw_signals", "funnel_analysis", "summary", "lead_record"],
        },
        # This tool list is static across every call in the loop and across every
        # dossier run — cache_control on the last tool tells the API to cache
        # everything up through here, so turns 2+ of the same run (and any
        # dossier run within the ~5 min cache TTL) read this at the cheaper
        # cache-read rate instead of paying full input price every time.
        "cache_control": {"type": "ephemeral"},
    },
]


def _dispatch_tool(name: str, tool_input: dict) -> dict:
    if name == "find_business":
        return find_business(
            tool_input.get("name", ""),
            tool_input.get("city", ""),
            tool_input.get("niche", "barbershop"),
        )
    if name == "scrape_site":
        content = scrape_website(tool_input.get("url", ""))
        social = detect_social_links(content)
        truncated = len(content) > MAX_SCRAPE_CHARS
        return {
            "content": content[:MAX_SCRAPE_CHARS],
            "length": len(content),
            "truncated": truncated,
            "social": social,
        }
    if name == "finalize_dossier":
        return {"status": "received"}
    print(f"[agent_deepdive] Unknown tool requested: {name}")
    return {"error": f"unknown tool '{name}'"}


def run_dossier_agent(
    business_name: str,
    city: str = "Calgary",
    niche: str = "barbershop",
    context: str = "",
    max_turns: int = 5,
) -> dict | None:
    # Resolved BEFORE the loop starts and BEFORE any scraping happens — see
    # get_scoring_rubric's docstring. `context` only matters the first time this
    # niche is seen (it steers generate_industry_scorer); ignored on reuse.
    rubric_text = get_scoring_rubric(niche, context)
    system_prompt = build_dossier_system_prompt(rubric_text)

    client = anthropic.Anthropic()
    messages = [
        {
            "role": "user",
            "content": (
                f"Business: {business_name} | City: {city} | Niche: {niche}\n\n"
                "Gather real signal using the tools available and produce the final dossier."
            ),
        }
    ]

    for turn in range(max_turns):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=2000,
                system=cached_system(system_prompt),
                tools=TOOLS,
                messages=messages,
            )
        except Exception as e:
            print(f"[agent_deepdive] API error on turn {turn + 1}: {e}")
            return None

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            print(f"[agent_deepdive] Model stopped without finalizing (stop_reason={response.stop_reason}); nudging once.")
            messages.append({"role": "user", "content": "Call finalize_dossier now with everything you've gathered so far."})
            continue

        tool_results = []
        finalized = None
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"[agent_deepdive] turn {turn + 1}: calling {block.name}({json.dumps(block.input)[:200]})")
            result = _dispatch_tool(block.name, block.input)
            if block.name == "finalize_dossier":
                finalized = block.input
                # scored_at is a real timestamp, not something the model can know —
                # stamp it in Python the same way run.py does, don't ask Claude to guess.
                if isinstance(finalized.get("lead_record"), dict):
                    finalized["lead_record"]["scored_at"] = datetime.now(timezone.utc).isoformat()
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                }
            )

        if finalized is not None:
            return finalized

        # Incremental cache breakpoint: mark the last tool_result block of this
        # turn as cacheable. Anthropic caches everything up to a cache_control
        # breakpoint, so next turn's call reads system + tools + every prior
        # turn (all now behind this breakpoint) at cache-read price instead of
        # full input price. Without this, only the static system/tools portion
        # was cached — the part of the prompt that actually grows every turn
        # (the accumulating tool-call history) was paying full price each time.
        if tool_results:
            tool_results[-1] = {**tool_results[-1], "cache_control": {"type": "ephemeral"}}

        messages.append({"role": "user", "content": tool_results})

    print(f"[agent_deepdive] Hit max_turns ({max_turns}) without a finalize_dossier call")
    return None


def dossier_to_lead_record(dossier: dict) -> dict:
    """Convenience passthrough — dossier["lead_record"] is already shaped for
    insert_lead(); this just names the intent at the call site,
    e.g. insert_lead(dossier_to_lead_record(result))."""
    return dossier.get("lead_record", {})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic prospect deep-dive + industry scorer generator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_dossier = sub.add_parser("dossier", help="Run a deep-dive dossier on a single prospect")
    p_dossier.add_argument("name", help="Business name")
    p_dossier.add_argument("--city", default="Calgary")
    p_dossier.add_argument("--niche", default="barbershop")
    p_dossier.add_argument(
        "--context",
        default="",
        help="Only used the first time this niche is scored — steers rubric generation (e.g. 'residential remodeler, not commercial').",
    )

    p_gen = sub.add_parser("generate-scorer", help="Draft a new industry scoring rubric")
    p_gen.add_argument("industry", help="e.g. 'dental clinic'")
    p_gen.add_argument("--context", default="", help="Brief context to steer the rubric")

    args = parser.parse_args()

    if args.command == "dossier":
        result = run_dossier_agent(args.name, city=args.city, niche=args.niche, context=args.context)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("Dossier failed — check logs above.")
    elif args.command == "generate-scorer":
        path = generate_industry_scorer(args.industry, args.context)
        if path:
            print(f"\nSaved: {path}\n")
            print(path.read_text())
        else:
            print("Generation failed — check logs above.")
