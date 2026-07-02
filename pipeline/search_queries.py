"""
Curated list of search queries for the lead pipeline.
Add/remove entries here — no other file needs to change.
Format: (niche, city_or_area)
"""

NICHE_VARIANTS = [
    "barbershop",
    "barber shop",
    "mens grooming",
    "fade specialist",
    "barber studio",
    "hair salon",
]

CALGARY_AREAS = [
    "Calgary",              # city-wide, already scraped — leave for reference
    "Kensington Calgary",
    "Beltline Calgary",
    "Bridgeland Calgary",
    "Inglewood Calgary",
    "Mission Calgary",
    "Marda Loop Calgary",
    "Chinook Calgary",
    "Sunalta Calgary",
    "Hillhurst Calgary",
    "Bowness Calgary",
]

# Pre-built combos shown in the manual trigger menu.
# Keep this list short and high-signal — add new ones as we saturate old ones.
SEARCH_QUERIES = [
    {"niche": "barbershop", "city": "Kensington Calgary"},
    {"niche": "barbershop", "city": "Beltline Calgary"},
    {"niche": "barbershop", "city": "Bridgeland Calgary"},
    {"niche": "mens grooming", "city": "Calgary"},
    {"niche": "fade specialist", "city": "Calgary"},
    {"niche": "barber studio", "city": "Calgary"},
]
