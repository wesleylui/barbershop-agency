import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        _client = create_client(url, key)
    return _client


def insert_lead(lead_dict: dict) -> dict | None:
    client = _get_client()
    try:
        result = client.table("leads").insert(lead_dict).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"[database] insert_lead failed: {e}")
        return None


def lead_exists(place_id: str) -> bool:
    if not place_id:
        return False
    client = _get_client()
    try:
        result = (
            client.table("leads")
            .select("id")
            .eq("google_place_id", place_id)
            .limit(1)
            .execute()
        )
        return len(result.data) > 0
    except Exception as e:
        print(f"[database] lead_exists failed: {e}")
        return False


def get_leads_by_status(status: str) -> list[dict]:
    client = _get_client()
    try:
        result = (
            client.table("leads")
            .select("*")
            .eq("outreach_status", status)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"[database] get_leads_by_status failed: {e}")
        return []


def get_all_outcomes() -> list[dict]:
    client = _get_client()
    try:
        result = (
            client.table("leads")
            .select("*")
            .not_.is_("outcome", "null")
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"[database] get_all_outcomes failed: {e}")
        return []


if __name__ == "__main__":
    import json

    test_lead = {
        "shop_name": "Test Barbershop (delete me)",
        "google_place_id": "test_place_id_abc123",
        "website_url": "https://example.com",
        "phone": "+1 403 555 0000",
        "address": "123 Test St, Calgary, AB",
        "rating": 4.8,
        "review_count": 99,
        "verdict": "Qualified",
        "total_score": 20,
        "outreach_status": "Not contacted",
    }

    print("Inserting test lead...")
    inserted = insert_lead(test_lead)
    if inserted:
        print(f"Inserted: {json.dumps(inserted, indent=2, default=str)}")
    else:
        print("Insert failed — check logs above.")
        exit(1)

    place_id = test_lead["google_place_id"]
    exists = lead_exists(place_id)
    print(f"\nlead_exists('{place_id}'): {exists}")
    if not exists:
        print("FAIL — lead_exists returned False after insert")
        exit(1)

    print("\nAll checks passed.")
