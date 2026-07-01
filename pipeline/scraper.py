import os
import requests
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"


def scrape_website(url: str) -> str:
    if not url:
        return ""

    api_key = os.getenv("FIRECRAWL_API_KEY", "")
    if not api_key:
        print("[scraper] FIRECRAWL_API_KEY not set")
        return ""

    try:
        response = requests.post(
            FIRECRAWL_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"url": url, "formats": ["markdown"]},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("markdown", "") or ""
    except Exception as e:
        print(f"[scraper] Failed to scrape '{url}': {e}")
        return ""


if __name__ == "__main__":
    import sys

    urls = sys.argv[1:] if len(sys.argv) > 1 else [
        "https://www.tazabarbershop.com",
        "https://www.fadekingcalgary.com",
        "https://www.freshcutsyyc.com",
        "https://www.sharpfadescalgary.com",
        "https://www.thebarberloungecalgary.com",
    ]

    for url in urls:
        print(f"\n--- {url} ---")
        content = scrape_website(url)
        if content:
            preview = content[:300].replace("\n", " ")
            print(f"OK ({len(content)} chars): {preview}...")
        else:
            print("EMPTY — no content returned")
