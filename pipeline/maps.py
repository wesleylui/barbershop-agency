import os
import requests
from dotenv import load_dotenv

load_dotenv()

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELDS = "places.id,places.displayName,places.formattedAddress,places.websiteUri,places.nationalPhoneNumber,places.rating,places.userRatingCount"


def get_shops(niche: str, city: str) -> list[dict]:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        print("[maps] GOOGLE_MAPS_API_KEY not set")
        return []

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELDS,
    }

    results = []
    page_token = None

    while True:
        body = {"textQuery": f"{niche} {city}"}
        if page_token:
            body["pageToken"] = page_token

        try:
            resp = requests.post(PLACES_SEARCH_URL, headers=headers, json=body, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[maps] Request failed: {e}")
            break

        for place in data.get("places", []):
            results.append({
                "place_id": place.get("id", ""),
                "name": place.get("displayName", {}).get("text", ""),
                "address": place.get("formattedAddress", ""),
                "website": place.get("websiteUri", ""),
                "phone": place.get("nationalPhoneNumber", ""),
                "rating": place.get("rating"),
                "review_count": place.get("userRatingCount"),
            })

        page_token = data.get("nextPageToken")
        if not page_token or len(results) >= 60:
            break

    return results


if __name__ == "__main__":
    import sys
    import json

    niche = sys.argv[1] if len(sys.argv) > 1 else "barbershop"
    city = sys.argv[2] if len(sys.argv) > 2 else "Calgary"

    shops = get_shops(niche, city)
    print(f"\nFound {len(shops)} shops for '{niche}' in '{city}':\n")
    for s in shops:
        print(
            f"  {s['name']:<40} rating={s['rating']}  reviews={s['review_count']}"
            f"  website={s['website'] or '(none)'}"
        )
    print(f"\nTotal: {len(shops)}")
