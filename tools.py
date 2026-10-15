"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def _tokens(text: str) -> set[str]:
    """
    DESIGN CHOICE: how to break text into comparable words.
      - str.split(): simplest, but "S/M" stays one word and "tee," keeps its comma.
      - regex [a-z0-9]+ (chosen): lowercases, drops punctuation, splits "S/M" into
        {"s", "m"} and "US 9" into {"us", "9"}. Cost: one regex per call.
      - stemming/NLP library (nltk, spaCy): "tees" would match "tee", but adds a
        dependency and surprising matches for a 40-item dataset.
    Returns a set, so duplicates vanish and overlap is a cheap `&`. Cost: word
    counts and order are thrown away.
    """
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _size_matches(wanted: str, listed: str) -> bool:
    """
    DESIGN CHOICE: what counts as a size match. (The brief requires
    case-insensitive and "M" matching "S/M"; the method is ours.)
      - substring (`"m" in "s/m"`): rejected by the brief; "s" is in "us 9" and
        "l" is in "xl", so shoes show up for a small top.
      - exact equality: precise, but "M" would miss "S/M" and "M/L".
      - whole-token subset (chosen): "M" matches "M", "S/M", "M/L" but not "XL"
        or "US 9"; "US 9" matches only "US 9". Cost: a bare "9" also matches
        "US 9" (arguably fine), and "L" matches "L/XL" but not "XL (oversized)"
        unless the user asks for "XL".
      - size-chart normalization (map W28 -> S etc.): most accurate, but needs
        data we don't have.
    `<=` on sets means "every wanted token appears in the listed size".
    """
    return _tokens(wanted) <= _tokens(listed)


def _price_matches(max_price: float, listed_price: float) -> bool:
    """REQUIRED by the brief: the ceiling is inclusive, so $30 matches max_price=30."""
    return listed_price <= max_price


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    -------------------------------------------------------------------------------------------------------       

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

    DESIGN NOTES — which parts were required and which were our choice:

    Required by the brief: use load_listings(); filter on all three inputs;
    inclusive price; case-insensitive size; score by keyword overlap; drop
    zero scores; best match first; at most SEARCH_RESULT_LIMIT; return [] (never
    None, never raise) when nothing matches.

    Our choices, with alternatives and tradeoffs:

    1. Filter order. Filter-then-score (chosen) vs score-then-filter. Same
       result; filtering first skips scoring items we'd discard. Price and size
       are optional, so each check is guarded (`None`/empty means "skip").
       `continue` per rule (chosen) vs one big `and` expression: `continue`
       reads top to bottom and is easy to extend with a fourth filter.

    2. What goes in the haystack. Title only: precise but misses "vintage" when
       it only appears in tags. Everything (chosen: title, description, tags,
       category, colors, brand): better recall, so "black" or "tops" match.
       Cost: description text adds noise and can match common words. Fields are
       joined into one string and tokenized once (see `_tokens`) rather than
       tokenizing each field, because only "does the word appear anywhere"
       matters here. `brand or ""` because brand is None for most listings.

    3. Scoring. Count of query words found (chosen) vs TF-IDF/BM25 vs model
       embeddings. Counting is explainable in one line and easy to debug in
       unit 4; TF-IDF/embeddings rank better but are overkill for 40 listings.
       Title matches are counted twice (haystack includes the title, then we
       add it again) on the theory that a word in the title is stronger
       evidence than a word buried in a description. The weight of 2 is a
       judgement call, not a tuned number.

    4. Sorting. Score descending, then cheaper first on ties (chosen) vs score
       only. Python's sort is stable, so score-only would leave ties in file
       order, which is arbitrary; price is a sensible shopper-facing tiebreak.
       Negating the score lets one ascending sort handle both keys.

    5. Output. Top N by SEARCH_RESULT_LIMIT (required) as plain listing dicts,
       dropping the scores, so the return shape matches the spec. The agent
       uses the first result; the rest are there for display or retries.
    """
    query = _tokens(description)
    results = []
    for item in load_listings():
        # Required: filter on price and size, but only when the caller gave them.
        if max_price is not None and not _price_matches(max_price, item["price"]):
            continue
        if size and not _size_matches(size, item["size"]):
            continue

        # Our choice: one bag of words from every searchable field (see note 2).
        haystack = _tokens(
            " ".join([
                item["title"],
                item["description"],
                " ".join(item["style_tags"]),
                item["category"],
                " ".join(item["colors"]),
                item["brand"] or "",  # brand is None for most listings
            ])
        )
        title = _tokens(item["title"])

        # Our choice: overlap count, title hits counted twice (see note 3).
        score = len(query & haystack) + len(query & title)

        # Required: drop anything scoring zero.
        if score:
            results.append((score, item))

    # Our choice: best score first, cheaper first on ties (see note 4).
    results.sort(key=lambda r: (-r[0], r[1]["price"]))
    # Required: at most SEARCH_RESULT_LIMIT, as listing dicts; [] if no results.
    return [item for _, item in results[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def _describe(item: dict) -> str:
    """
    DESIGN CHOICE: how to show a listing to the model.
      - dump the whole dict/JSON: complete, but spends tokens on id, platform,
        condition and price, none of which affect how a piece is styled.
      - one readable sentence (chosen): title, description, size, colors, tags.
        Only the style-relevant fields; the model reads prose better than keys.
    """
    return (
        f"{item['title']} — {item['description']} "
        f"(size {item['size']}, {', '.join(item['colors'])}, tags: {', '.join(item['style_tags'])})"
    )


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"

    DESIGN NOTES — which parts were required and which were our choice:

    Required by the brief: call the model through generate(); return a
    non-empty str; with items in the wardrobe, name specific pieces the user
    owns; with an empty wardrobe, return general advice instead of raising or
    returning "".

    Our choices, with alternatives and tradeoffs:

    1. Who does the matching. Ask the model to pick combinations (chosen) vs
       code that scores compatibility (color wheel rules, category pairing such
       as top + bottom + shoes) vs a trained recommender. The model already
       "knows" fashion and handles vague tags like "streetwear" or "baggy" for
       free; hand-written rules would be brittle and take far longer to build.
       Cost: output varies run to run and can't be unit-tested for exact text,
       which is why acceptance criteria for this tool must be written as
       properties (names an owned piece, non-empty) rather than exact strings.
       It can also invent a piece the user doesn't own, so the prompt tells it
       to use wardrobe names exactly as listed.

    2. Wardrobe in the prompt. Full item list (chosen: name, category, colors,
       tags) vs only names vs pre-filtering to "compatible" items in code.
       Names alone lose color/style signal; pre-filtering saves tokens but
       needs the rules from choice 1. A wardrobe is ~10 items, so sending all
       of it is cheap. `notes` is omitted to keep each line short.

    3. Empty wardrobe. Separate prompt for general advice (chosen) vs reusing
       the wardrobe prompt with an empty list vs raising or returning a canned
       string. A separate prompt stops the model saying "your wardrobe is
       empty" or inventing owned pieces; a canned string would skip the model
       call but give every item the same useless answer. Treating a missing
       wardrobe or missing 'items' key as empty (`or []`) keeps the tool from
       crashing on a malformed input.

    4. Length. "Under 120 words" in the prompt keeps the text short enough to
       feed into create_fit_card. This is a soft limit; the model may overshoot.

    5. Temperature. Uses config.TEMPERATURE (0.9) and the cache, so repeated
       identical calls during development reuse one answer. Outfit advice
       benefits from some variety, but this tool is less sensitive to it than
       the fit card.

    6. Fallback. If the model returns blank text, return a generic sentence so
       the "non-empty string" promise holds and the loop never passes "" on.
    """
    # Our choice: treat a missing wardrobe or missing 'items' as empty (note 3).
    items = (wardrobe or {}).get("items") or []
    item_text = _describe(new_item)
    # Required: the empty wardrobe gets general advice, never "" or an error.
    if not items:
        prompt = (
            f"Someone is thinking of buying this thrifted piece:\n{item_text}\n\n"
            "They haven't told us what they own. Give general styling advice: one or two "
            "outfit ideas built around it, naming the kinds of pieces that would pair well. "
            "Keep it under 120 words."
        )
    else:
        # Required: name pieces the user owns. Our choice: full line per item (note 2).
        owned = "\n".join(
            f"- {w['name']} ({w['category']}; {', '.join(w.get('colors', []))}; "
            f"{', '.join(w.get('style_tags', []))})" for w in items
        )
        prompt = (
            f"Someone is thinking of buying this thrifted piece:\n{item_text}\n\n"
            f"Their wardrobe:\n{owned}\n\n"
            "Suggest one or two outfits that combine the new piece with items from the "
            "wardrobe. Refer to the new piece by its exact title, word for word, "
            f"\"{new_item['title']}\", and to each wardrobe piece by its exact name as listed "
            "above, including any words after a comma. Do not describe pieces with colors, tags "
            "or parenthetical lists. Keep it under 120 words."
        )
    # Our choice: generic fallback keeps the non-empty promise (note 6).
    return generate(prompt, temperature=config.TEMPERATURE).strip() or (
        "Try pairing it with simple neutral basics and let it be the focus of the outfit."
    )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"

    DESIGN NOTES — which parts were required and which were our choice:

    Required by the brief: guard an empty/whitespace outfit with a descriptive
    message (no raise); 2-4 sentences; item, price and platform mentioned once
    each; a specific vibe; different output on different runs (so no cache and
    temperature above 0).

    Our choices, with alternatives and tradeoffs:

    1. Guard. Return a message string (chosen, matches the README spec) vs
       raise vs return "". The loop can show the message as-is; an exception
       would need a try/except in the loop, and "" would look like success.

    2. Ask for the facts vs fill them in. We hand the model the price and
       platform and ask it to mention them (chosen) vs template the caption in
       code ("Found {title} on {platform} for ${price}"). A template is
       guaranteed accurate but reads like a product description, which the
       brief forbids. Cost: the model may drop or repeat a fact, or change the
       price format, so acceptance criteria should check the output rather than
       trust the prompt.

    3. Variation. cache=False plus config.TEMPERATURE (chosen) vs relying on
       the global CACHE_ENABLED flag. Bypassing the cache here means two calls
       with the same inputs are really two answers, which is what the
       "run it three times" test needs. Cost: every call spends quota.

    4. Output cleanliness. "Return only the caption" (chosen) avoids
       "Here's a caption:" preambles; .strip() removes stray whitespace. The
       model can still add hashtags or emoji, which fits a real post.

    5. Item fields. Only title, price and platform go in, alongside the outfit
       text, because the caption should be about the find and not repeat the
       whole listing.
    """
    # Required: empty/whitespace outfit returns a message, never raises (note 1).
    if not outfit or not outfit.strip():
        return "No outfit suggestion to write a caption from."
    prompt = (
        f"Write a 2-4 sentence social media caption for a thrift find, the way a real person "
        f"would post it, not a product description.\n\nItem: {new_item['title']}\n"
        f"Price: ${new_item['price']:.2f}\nPlatform: {new_item['platform']}\n"
        f"Outfit idea: {outfit}\n\n"
        "Mention the item, its price, and its platform once each, and be specific about the "
        "vibe. Return only the caption."
    )
    # Required: variation. cache=False + TEMPERATURE (note 3).
    return generate(prompt, cache=False, temperature=config.TEMPERATURE).strip()
