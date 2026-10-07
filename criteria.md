# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
`suggest_outfit` calls a model and is allowed to return an empty output. When it
does, the loop branches out and never calls `create_fit_card`, so a run can
legitimately miss the third tool even when the search worked. That's why 4 of 5
and not 5 of 5.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
Once a query matches no listings, the agent must branch out and call no further
tool, with no exceptions. This path has no model in it, so there's no randomness
to excuse a miss: it's either working or it isn't.

---

## 3. The item search found is the item the next tool received

For 5 different queries, each matching at least one listing, the item passed to
`suggest_outfit` as `new_item` is exactly equal (full dict equality) to one
element of the list `search_listings()` returned for that query, found by
matching `id` — in 5 of 5 queries.

**Why this target:**
The agent only passes data from one stage to the next, so there's no randomness
to excuse a miss: either the right item arrives or it doesn't. Full dict
equality (not just "same keys") also catches an item that was edited between
the two tools. <!-- TODO: confirm nothing in agent.py picks or edits the item
between the tools; if something does, say so here. -->

---

## 4. Different items get different fit card openings

For 5 listings from 5 different categories, the 5 fit cards returned by
`create_fit_card` have 5 different opening sentences — 5 of 5. The opening
sentence is everything up to the first `.`, `!` or `?` that is followed by a
space (so the `.` in `$24.99` doesn't count), compared
after lowercasing and trimming whitespace.

**Why this target:**
The docstring in `tools.py` says the caption should come out differently for
different inputs. Two cards sharing an opening means the model is filling in a
template, so one repeat out of 5 is already a failure. Five items
give 10 pairs to compare, where two items would give only one. Items come from
different categories so that two near-identical items can't legitimately open
the same way.

---

## 5. suggest_outfit only names items that exist

For 5 different `new_item` inputs, read each
`suggest_outfit` output and list every item it names. Each named item counts as
found if, after lowercasing and trimming, it exactly equals `new_item["title"]`
or the `name` of an item in the wardrobe. In each of the 5 outputs, the number of
unfound items may be at most 25% of the items named, rounded down, but never
fewer than 1 allowed — 5 of 5 outputs.

**Why this target:**
Exact matching will wrongly flag paraphrases (e.g. "black denim jeans" for
"Black Jeans"), so I allow a small share of misses instead of 0. 

I don't know how many items a typical output names, so I loosened the
requirement a little: a quarter of the named items may go unfound. When 25%
rounds down to 0 (outputs naming fewer than 4 items), I still allow 1 unfound
item, because exact matching will miss paraphrases and I'd rather not fail an
output over one wording difference. 50% would let too many invented items
through.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
