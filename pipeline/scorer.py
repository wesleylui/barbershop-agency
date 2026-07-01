import anthropic
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SCORING_PROMPT = (Path(__file__).parent.parent / "prompts" / "scoring.txt").read_text()


def score_shop(name: str, review_count: int, rating: float, scraped_content: str) -> dict | None:
    client = anthropic.Anthropic()
    user_message = (
        f"Shop: {name} | Reviews: {review_count} | Rating: {rating} | "
        f"Website content: {scraped_content}"
    )

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=SCORING_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception as e:
        print(f"[scorer] API error for '{name}': {e}")
        return None

    raw = message.content[0].text.strip()
    # Strip markdown code fences Claude occasionally adds despite the prompt
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1]).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"[scorer] JSON parse failed for '{name}'. Raw response:\n{raw}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score a barbershop lead")
    parser.add_argument("name", help="Shop name")
    parser.add_argument("--content", default="", help="Scraped website content")
    parser.add_argument("--reviews", type=int, default=0, help="Review count")
    parser.add_argument("--rating", type=float, default=0.0, help="Star rating")
    args = parser.parse_args()

    result = score_shop(args.name, args.reviews, args.rating, args.content)
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Scoring failed — check logs above.")
