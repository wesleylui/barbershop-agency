import argparse
import sys
from datetime import datetime, timezone

from pipeline.maps import get_shops
from pipeline.scraper import scrape_website
from pipeline.scorer import score_shop
from pipeline.database import insert_lead, lead_exists, insert_pipeline_run
from pipeline.notifier import post_run_summary
from pipeline.search_queries import SEARCH_QUERIES


def cheap_filter(shops: list[dict]) -> list[dict]:
    kept = []
    skipped_db = skipped_rating = skipped_reviews = 0
    for s in shops:
        if lead_exists(s["place_id"]):
            skipped_db += 1
        elif (s["rating"] or 0) < 4.2:
            skipped_rating += 1
        elif (s["review_count"] or 0) < 50:
            skipped_reviews += 1
        else:
            kept.append(s)
    print(
        f"[filter] Dropped {skipped_db} already in DB, "
        f"{skipped_rating} low rating, {skipped_reviews} low reviews"
    )
    return kept


def run_pipeline(city: str, niche: str):
    print(f"\n[run] Starting pipeline: {niche} in {city}")

    raw = get_shops(niche, city)
    found = len(raw)
    print(f"[run] Maps returned {found} shops")

    filtered = cheap_filter(raw)
    after_filter = len(filtered)
    print(f"[run] {after_filter} shops passed filter")

    scored = 0
    qualified = 0
    top_leads = []

    for shop in filtered:
        name = shop["name"]
        print(f"\n[run] Processing: {name}")

        content = scrape_website(shop.get("website", ""))

        result = score_shop(
            name=name,
            review_count=shop["review_count"] or 0,
            rating=shop["rating"] or 0.0,
            scraped_content=content,
        )

        if result is None:
            print(f"[run] Scoring failed for {name}, skipping")
            continue

        scored += 1
        verdict = result.get("verdict", "")
        if verdict in ("Priority", "Qualified"):
            qualified += 1

        lead = {
            "shop_name": name,
            "google_place_id": shop["place_id"],
            "website_url": shop.get("website", ""),
            "phone": shop.get("phone", ""),
            "address": shop.get("address", ""),
            "rating": shop["rating"],
            "review_count": shop["review_count"],
            "scraped_content": content[:5000] if content else None,
            "team_score": result.get("team_score"),
            "util_score": result.get("util_score"),
            "funnel_score": result.get("funnel_score"),
            "total_score": result.get("total_score"),
            "verdict": verdict,
            "leaks_found": result.get("leaks_found"),
            "outreach_hook": result.get("outreach_hook"),
            "scored_at": datetime.now(timezone.utc).isoformat(),
        }

        insert_lead(lead)
        print(f"[run] Saved: {name} — {verdict} ({result.get('total_score')})")
        if verdict in ("Priority", "Qualified"):
            top_leads.append(lead)

    insert_pipeline_run({
        "city": city,
        "niche": niche,
        "shops_found": found,
        "shops_after_filter": after_filter,
        "shops_scored": scored,
        "shops_qualified": qualified,
        "status": "complete",
    })

    top_leads.sort(key=lambda x: x.get("total_score") or 0, reverse=True)
    post_run_summary(
        city=city,
        niche=niche,
        found=found,
        after_filter=after_filter,
        scored=scored,
        qualified=qualified,
        top_leads=top_leads[:5],
    )

    print(
        f"\n[run] Done: {found} found | {after_filter} passed filter "
        f"| {scored} scored | {qualified} qualified"
    )


def prompt_for_query() -> tuple[str, str]:
    """Show a numbered menu of curated queries and return the chosen (city, niche)."""
    print("Select a search to run:")
    for i, q in enumerate(SEARCH_QUERIES, start=1):
        print(f"  {i}) {q['niche']} — {q['city']}")
    custom_option = len(SEARCH_QUERIES) + 1
    print(f"  {custom_option}) Custom (enter your own niche + city)")

    while True:
        choice = input("> ").strip()
        if not choice.isdigit():
            print("Please enter a number.")
            continue
        n = int(choice)
        if 1 <= n <= len(SEARCH_QUERIES):
            q = SEARCH_QUERIES[n - 1]
            return q["city"], q["niche"]
        if n == custom_option:
            niche = input("Niche: ").strip()
            city = input("City: ").strip()
            if niche and city:
                return city, niche
            print("Both niche and city are required.")
            continue
        print(f"Please enter a number between 1 and {custom_option}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the barbershop lead pipeline")
    parser.add_argument("--city")
    parser.add_argument("--niche")
    args = parser.parse_args()

    if args.city and args.niche:
        # Explicit flags: run exactly that query (scripting/testing).
        run_pipeline(args.city, args.niche)
    elif sys.stdin.isatty():
        # Interactive terminal (local run / `railway run`): show the manual menu.
        city, niche = prompt_for_query()
        run_pipeline(city, niche)
    else:
        # Non-interactive (e.g. Railway auto-runs startCommand on deploy): there's
        # no stdin to answer the menu. Exit cleanly instead of crash-looping so the
        # scrape only ever runs when a human triggers it manually.
        print(
            "No --city/--niche provided and no interactive terminal detected. "
            "Skipping — trigger a scrape manually with `railway run python -m pipeline.run` "
            "(shows the menu) or pass --city and --niche explicitly."
        )
        sys.exit(0)
