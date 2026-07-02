# Scraping — how it works today

## Why the daily auto-scrape is paused

The pipeline used to run automatically every morning, always searching the same thing
("barbershop Calgary"). Two reasons we turned that off:

- **The query pool is exhausted** — repeating the same city-wide search kept returning
  shops we'd already seen, so new runs found almost no fresh leads.
- **We have an outreach backlog** — there are already more qualified leads waiting to be
  contacted than we can work through, so piling on more doesn't help right now.

## How to trigger a scrape now

Scraping is now manual. From the project (or in the Railway dashboard's "Run command"),
run:

```
python -m pipeline.run
```

This shows a numbered menu of curated searches. Type the number of the one you want and
press Enter, and the pipeline runs that single search. There's also a "Custom" option to
type your own niche + city for a one-off search.

## How to add a new search to the menu

Edit **`pipeline/search_queries.py`** and add an entry to the `SEARCH_QUERIES` list, for
example:

```python
{"niche": "barbershop", "city": "Marda Loop Calgary"},
```

That's the only file you need to touch — the menu picks it up automatically the next time
you run the command. The file also keeps reference lists of niche variants and Calgary
neighborhoods you can mix and match.

## When it's OK to resume more frequent (or automatic) scraping

Resume more frequent scraping only once we've worked through the backlog — roughly, when
the number of **uncontacted Qualified/Priority leads drops below ~5**. Until then, run a
single manual search whenever the pipeline of leads to contact runs low, rather than
scraping on a daily schedule.
