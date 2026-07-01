import os
import requests
from dotenv import load_dotenv

load_dotenv()

VERDICT_ICON = {
    "Priority": "🔴",
    "Qualified": "✅",
    "Maybe": "🟡",
    "Skip": "⬜",
}


def post_run_summary(
    city: str,
    niche: str,
    found: int,
    after_filter: int,
    scored: int,
    qualified: int,
    top_leads: list[dict],
) -> bool:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
    if not webhook_url:
        print("[notifier] DISCORD_WEBHOOK_URL not set — skipping notification")
        return False

    lines = [
        f"**Pipeline run complete — {niche.title()} in {city}**",
        f"`{found} found  |  {after_filter} passed filter  |  {scored} scored  |  {qualified} qualified`",
    ]

    if top_leads:
        lines.append("")
        for lead in top_leads:
            icon = VERDICT_ICON.get(lead.get("verdict", ""), "•")
            score = lead.get("total_score", "?")
            name = lead.get("shop_name", "Unknown")
            hook = lead.get("outreach_hook", "")
            lines.append(f"{icon} **{name}** ({score}/30)")
            if hook:
                lines.append(f"  _{hook}_")
    else:
        lines.append("_No qualified leads this run._")

    payload = {"content": "\n".join(lines)}

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        print("[notifier] Discord message sent")
        return True
    except Exception as e:
        print(f"[notifier] Failed to send Discord message: {e}")
        return False


if __name__ == "__main__":
    post_run_summary(
        city="Calgary",
        niche="barbershop",
        found=20,
        after_filter=19,
        scored=19,
        qualified=10,
        top_leads=[
            {
                "shop_name": "Barber Culture (Kensington)",
                "verdict": "Priority",
                "total_score": 24,
                "outreach_hook": "Your Fresha link sends clients off your site — embedding it could convert more of your 977 reviews into bookings.",
            },
            {
                "shop_name": "Magnum Barbershop Beltline",
                "verdict": "Qualified",
                "total_score": 22,
                "outreach_hook": "No embedded booking means you're losing walk-ins who check your site on mobile and can't book in one tap.",
            },
            {
                "shop_name": "Magnum Barbershop Kensington",
                "verdict": "Qualified",
                "total_score": 21,
                "outreach_hook": "Sending clients to an external booking tab is costing you conversions from your strong review base.",
            },
        ],
    )
