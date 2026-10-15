"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from mcp_client import call_tool
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    count = 0

    # Step 3: parse the query (regex, see _parse_query).
    session["parsed"] = _parse_query(query)
    trace.step("parse_query", inputs=query, returned=session["parsed"])

    # Step 4: search. THE BRANCH: an empty list stops the run before suggest_outfit.
    count += 1
    trace.check_iterations(count)
    parsed = session["parsed"]
    session["search_results"] = call_tool("search_listings", {
        "description": parsed["description"],
        "size": parsed["size"],
        "max_price": parsed["max_price"],
    })
    empty = not session["search_results"]
    trace.step(
        "search_listings (via MCP)",
        inputs=parsed,
        returned=session["search_results"],
        note="branch: empty, stopping before suggest_outfit" if empty else "",
    )
    if empty:
        session["error"] = _no_results_message(parsed)
        return session

    # Step 5: the first result is the pick; later steps read it from the session.
    session["selected_item"] = session["search_results"][0]
    trace.step("select_item", inputs="first of search_results",
               returned=session["selected_item"])

    # Step 6: an empty wardrobe is handled inside suggest_outfit (general advice).
    count += 1
    trace.check_iterations(count)
    try:
        session["outfit_suggestion"] = suggest_outfit(
            session["selected_item"], session["wardrobe"]
        )
    except ModelUnavailable as exc:
        session["error"] = _model_unavailable_message(exc)
        trace.step("suggest_outfit", inputs=session["selected_item"],
                   note="model unavailable, stopping")
        return session
    wardrobe_size = len((session["wardrobe"] or {}).get("items") or [])
    trace.step(
        "suggest_outfit",
        inputs=f"{session['selected_item'].get('title')} + wardrobe of {wardrobe_size} items",
        returned=session["outfit_suggestion"],
        note="empty wardrobe: general advice" if wardrobe_size == 0 else "",
    )
    if not (session["outfit_suggestion"] or "").strip():
        session["error"] = (
            "No outfit suggestion came back for this item, so no fit card was made. "
            "Try running it again or picking a different search."
        )
        trace.step("suggest_outfit", note="branch: empty suggestion, stopping")
        return session

    # Step 7
    count += 1
    trace.check_iterations(count)
    try:
        session["fit_card"] = create_fit_card(
            session["outfit_suggestion"], session["selected_item"]
        )
    except ModelUnavailable as exc:
        session["error"] = _model_unavailable_message(exc)
        trace.step("create_fit_card", note="model unavailable, stopping")
        return session
    trace.step(
        "create_fit_card",
        inputs=f"outfit + {session['selected_item'].get('title')}",
        returned=session["fit_card"],
    )
    return session


# ── query parsing and messages ────────────────────────────────────────────────

_FILLER = {"looking", "for", "a", "an", "the", "i", "want", "need", "find", "me",
           "show", "some", "in", "size", "under", "below", "max", "less", "than", "up", "to"}


def _parse_query(query: str) -> dict:
    """
    Regex parse (chosen over asking the model: free, deterministic, testable).
    size: the word(s) after "size" ("size M", "size US 9"). max_price: a number
    after under/below/max/up to, or any "$N". description: what's left, minus
    filler words. Cost: phrasings like "size is M" or "30 dollars" are missed.
    """
    text = query
    size = None
    m = re.search(r"\bsize\s+([A-Za-z]+\d*(?:/[A-Za-z]+)?(?:\s+\d+(?:\.\d+)?)?|\d+(?:\.\d+)?)", text, re.I)
    if m:
        size = m.group(1).strip()
        text = text.replace(m.group(0), " ")

    max_price = None
    m = (re.search(r"(?:under|below|max|up to|less than)\s*\$?\s*(\d+(?:\.\d+)?)", text, re.I)
         or re.search(r"\$\s*(\d+(?:\.\d+)?)", text))
    if m:
        max_price = float(m.group(1))
        text = text.replace(m.group(0), " ")

    words = [w for w in re.findall(r"[A-Za-z0-9']+", text) if w.lower() not in _FILLER]
    return {"description": " ".join(words), "size": size, "max_price": max_price}


def _model_unavailable_message(exc: Exception) -> str:
    """Say what broke (the model couldn't be reached) and what the user can try."""
    return (
        f"The model couldn't be reached, so no outfit or fit card was made. {exc} "
        "Check GEMINI_API_KEY in your .env file and your internet connection, "
        "then run the query again."
    )


def _no_results_message(parsed: dict) -> str:
    """Name the filters that were applied and what to loosen. Not just "no results"."""
    used = [f"\"{parsed['description']}\""]
    if parsed["size"]:
        used.append(f"size {parsed['size']}")
    if parsed["max_price"] is not None:
        used.append(f"under ${parsed['max_price']:.0f}")
    tips = ["use fewer or different keywords (e.g. just the item type, like \"jacket\")"]
    if parsed["size"]:
        tips.append("drop the size or try a neighbouring one")
    if parsed["max_price"] is not None:
        tips.append(f"raise the ${parsed['max_price']:.0f} budget")
    return f"Nothing matched {', '.join(used)}. Try to " + ", or ".join(tips) + "."


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
