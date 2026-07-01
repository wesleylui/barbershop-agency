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


GENERATOR_SYSTEM_PROMPT = f"""You are designing a new lead-scoring rubric for an AI SMB marketing
agency's qualification pipeline. The agency currently only scores barbershops. You are
extending it to a new industry.

Here is the existing barbershop rubric. Your new rubric MUST match its structure and
JSON schema exactly: the same three signals (team/ability-to-pay, utilization, funnel),
the same section headers, and the exact same OUTPUT field names
(team_score, util_score, funnel_score, total_score, verdict, leaks_found, outreach_hook).
Keep the RULES section (total_score formula and verdict thresholds) unchanged — only
re-derive what each signal actually measures and how it's scored for the new industry's
real-world proxies. Ability to pay should map to whatever this industry's equivalent of
"chair/barber count" is. Utilization should map to whatever this industry's equivalent of
"% booked" is, and the point thresholds should reflect how that industry actually books
(e.g. longer scheduling horizons look "fuller" sooner than same-day service businesses).
Funnel quality/booking-embed logic likely transfers directly, but confirm it fits and use
that industry's own common booking platforms in the inference rules, not the barbershop
ones.

--- EXISTING RUBRIC (barbershop) ---
{BASE_SCORING_PROMPT}
--- END EXISTING RUBRIC ---

Output ONLY the new rubric text, in the exact same plain-text format as above (same
section headers and order: SIGNAL 1 — TEAM SCORE, SIGNAL 2 — UTILIZATION SCORE,
SIGNAL 3 — FUNNEL SCORE, INFERENCE RULES FOR FUNNEL SCORE, RULES, OUTPUT). No preamble,
no markdown code fences, no explanation before or after — the file you produce gets
loaded verbatim as another module's system prompt."""


def generate_industry_scorer(industry: str, context: str = "") -> Path | None:
    """Drafts a new prompts/scoring_<slug>.txt for an SMB industry that doesn't have
    one yet, in the same schema as prompts/scoring.txt. This is a plain single-call
    function (same shape as scorer.py's score_shop) rather than a multi-turn loop —
    drafting a rubric doesn't need tool use, it needs one well-built prompt. It's
    also registered as a tool below so the dossier agent can call it itself mid-run
    if it discovers the prospect isn't a barbershop."""
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

    slug = _slugify(industry)
    out_path = PROMPTS_DIR / f"scoring_{slug}.txt"
    try:
        out_path.write_text(raw)
    except Exception as e:
        print(f"[agent_deepdive] Failed to write {out_path}: {e}")
        return None

    print(f"[agent_deepdive] Saved new rubric to {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Agentic dossier loop
# ---------------------------------------------------------------------------

DOSSIER_SYSTEM_PROMPT = f"""You are a prospect research analyst for an AI agency that fixes
booking funnels and local visibility for personal service SMBs, starting with barbershops.

Given a business name (and optionally city/niche), gather real signal about it using the
tools available and produce one final structured dossier by calling finalize_dossier
exactly once, last. You decide the order of tool calls and whether to skip a step based
on what you already know — do not follow a fixed sequence blindly. Examples of judgment
calls you should make yourself: if find_business returns no website, skip scrape_site
entirely and record that directly as a funnel signal ("no website at all" is itself the
worst-case funnel score per the rubric below) — don't waste a call scraping nothing. If
the niche clearly isn't "barbershop" (or whatever niche was given) and no scoring rubric
exists yet for that industry, call generate_industry_scorer before finalizing so your
scores are computed against the right rubric instead of forcing the barbershop one onto
a business it doesn't fit.

SCORING RUBRIC — use this to reason out team_score, util_score, funnel_score and verdict
yourself for lead_record (do not just pattern-match; actually weigh the evidence you
gathered against these rules):

{BASE_SCORING_PROMPT}

Two things this agency's existing one-shot scorer does NOT do, that you must:

1. Social presence. scrape_site's result already includes a "social" field (Instagram/
   Facebook links found via regex, run automatically — you don't need to call anything
   separately for this) — you reason about what it means. Most barbershop clientele comes
   through Instagram, not the website. A shop with no discoverable Instagram is a bigger
   red flag than a mediocre booking flow, not a minor footnote — weigh it that way in your
   summary and leaks_found, and note it even when the rest of the funnel looks fine.
2. Funnel reasoning, not a rule lookup. Don't just apply the INFERENCE RULES as a
   checklist. Write actual analysis: is the booking link an embed or does it redirect
   off-site? Does it look like a specific service gets pre-selected, or does the visitor
   land on a blank scheduler and have to figure it out themselves? Is there a clear
   call-to-action a mobile visitor would actually see above the fold, based on how the
   content is structured? Say why it's broken, not just that it is. Put this reasoning
   in funnel_analysis as real prose, a few sentences, not a restated rule.

Be honest in your dossier about what you can't actually know from the outside — e.g.
percent of appointment slots booked usually cannot be directly observed from a website
scrape or Maps listing. Say so and give your best-evidence estimate rather than stating
an unfounded number with false confidence.

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
        "name": "generate_industry_scorer",
        "description": (
            "Draft and save a new scoring rubric (same schema as prompts/scoring.txt) for an SMB "
            "industry that doesn't have one yet. Only call this if the prospect's industry is not "
            "barbershop and no matching prompts/scoring_<slug>.txt already exists."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "industry": {"type": "string"},
                "context": {"type": "string", "description": "Brief context to steer the rubric"},
            },
            "required": ["industry"],
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
    if name == "generate_industry_scorer":
        path = generate_industry_scorer(tool_input.get("industry", ""), tool_input.get("context", ""))
        return {"saved_to": str(path) if path else None}
    if name == "finalize_dossier":
        return {"status": "received"}
    print(f"[agent_deepdive] Unknown tool requested: {name}")
    return {"error": f"unknown tool '{name}'"}


def run_dossier_agent(business_name: str, city: str = "Calgary", niche: str = "barbershop", max_turns: int = 5) -> dict | None:
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
                system=cached_system(DOSSIER_SYSTEM_PROMPT),
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

    p_gen = sub.add_parser("generate-scorer", help="Draft a new industry scoring rubric")
    p_gen.add_argument("industry", help="e.g. 'dental clinic'")
    p_gen.add_argument("--context", default="", help="Brief context to steer the rubric")

    args = parser.parse_args()

    if args.command == "dossier":
        result = run_dossier_agent(args.name, city=args.city, niche=args.niche)
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
