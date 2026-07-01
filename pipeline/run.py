import argparse
from datetime import datetime, timezone

from pipeline.maps import get_shops
from pipeline.scraper import scrape_website
from pipeline.scorer import score_shop
from pipeline.database import insert_lead, lead_exists, insert_pipeline_run


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

    insert_pipeline_run({
        "city": city,
        "niche": niche,
        "shops_found": found,
        "shops_after_filter": after_filter,
        "shops_scored": scored,
        "shops_qualified": qualified,
        "status": "complete",
    })

    print(
        f"\n[run] Done: {found} found | {after_filter} passed filter "
        f"| {scored} scored | {qualified} qualified"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the barbershop lead pipeline")
    parser.add_argument("--city", default="Calgary")
    parser.add_argument("--niche", default="barbershop")
    args = parser.parse_args()
    run_pipeline(args.city, args.niche)
