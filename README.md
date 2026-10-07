# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr helps a shopper decide whether a thrifted find is worth buying. The user types a request in plain language, such as "vintage graphic tee under $30, size M", along with the clothes they already own. The agent searches a set of secondhand listings, picks the best match, and suggests one or two outfits that combine it with pieces from their wardrobe, or general styling advice if the wardrobe is empty. It ends with a short social-media caption for the find. If nothing matches, it stops early and tells the user which filter (keywords, size, or budget) to loosen instead of making up an outfit.


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:**
     Filters the listings in `data/listings.json` by size and price, then ranks the remaining items by how well their title, description, and style tags match the user's keywords.
- **Inputs:**
     - `description` (str): keywords for what the user wants, e.g. `"vintage graphic tee"`.
     - `size` (str | None): the size the user wants, e.g. `"M"`.
     - `max_price` (float | None): price ceiling in dollars, inclusive, e.g. `30.00`.
- **Returns:**
     A `list[dict]` of listing dicts. Each dict has the keys `id` (str), `title` (str), `description` (str), `category` (str), `style_tags` (list[str]), `size` (str), `condition` (str), `price` (float), `colors` (list[str]), `brand` (str), and `platform` (str).
- **When it has nothing:**
     An empty list `[]`. it never an exception.

### `suggest_outfit`

- **What it does:**
     Combine one listing with pieces the user already owns and suggest one or two outfits.
- **Inputs:**
     - `new_item` (dict): one listing dict, i.e. a single element of `search_listings`' result.
     - `wardrobe` (dict): a dict with an `items` key holding a list of dicts, each with `id` (str), `name` (str), `category` (str, one of tops / bottoms / outerwear / shoes / accessories), `colors` (list[str]), `style_tags` (list[str]), and `notes` (str | None).
- **Returns:**
     A non-empty `str` of one or two outfit suggestions. When the wardrobe has items, the text names specific pieces from it.
- **When it has nothing:**
     If `wardrobe["items"]` is empty, it returns general styling advice for `new_item` as a non-empty string. It does not raise and does not return `""`.

### `create_fit_card`

- **What it does:**
     Writes a short social-media-style caption for the thrifted find, based on the outfit suggestion.
- **Inputs:**
     - `outfit` (str): the string returned by `suggest_outfit`.
     - `new_item` (dict): the same listing dict that was passed to `suggest_outfit`.
- **Returns:**
     A `str` of two to four sentences that reads like a real post, mentions the item, its price, and its platform once each, and gives a specific vibe.
- **When it has nothing:**
     If `outfit` is empty or whitespace, it returns a descriptive message string (e.g. `"No outfit suggestion to write a caption from."`). It does not raise.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that names the filters that were applied and what to loosen (keywords, size, budget), and stop: `suggest_outfit` and `create_fit_card` are never called and `session["fit_card"]` stays `None`. Otherwise take the first result and go to `suggest_outfit`. A second, defensive check follows it: if `suggest_outfit` returns a blank string, set `session["error"]` and stop before `create_fit_card`. (An empty wardrobe is not a branch in the loop; `suggest_outfit` handles it by returning general styling advice.)

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex (`agent.py::_parse_query`), not the model, so it is free, deterministic and testable. `size` is the text after "size" ("size M", "size US 9", "size W28", "size S/M"); `max_price` is a number after under/below/max/up to/less than, or any `$N`; `description` is what remains after removing those and filler words. Known gap: phrasings like "30 dollars" or "size is M" are not recognised.

**What moves through the session:** Each result is written to the session and read back from it for the next call, in this order: `query` → `parsed` → `search_results` → `selected_item` (first result) → `outfit_suggestion` → `fit_card`. `error` is set only when the run stops early, and `wardrobe` is passed in at the start.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings as s; print([(x['title'],x['size'],x['price']) for x in s('graphic tee', size='M', max_price=30)]); print(s('xyzzy'))"

[('Y2K Baby Tee — Butterfly Print', 'S/M', 18.0), ('Mesh Long-Sleeve Top — Black', 'S/M', 15.0)]
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import *; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"

**Outfit 1: Casual Streetwear**
Pair the vintage Levi's 501 jeans with the **White ribbed tank top** tucked in for a fitted silhouette. Layer the **Oversized grey crewneck sweatshirt** over your shoulders... Step into the **Chunky white sneakers** and accessorize with the **Black crossbody bag**...
(empty wardrobe, get_empty_wardrobe(): returns general advice — "These vintage Levi's 501s are the ultimate wardrobe building block. Look 1: Casual Streetwear...")
```

```
$ python -c "from tools import create_fit_card as c; from utils.data_loader import load_listings as l; [print(c('jeans and white sneakers', l()[0])) for _ in range(3)]; print(c('  ', l()[0]))"

Found the holy grail of vintage Levi's 501 jeans while scrolling on depop today... For just $38.00, these give off the ultimate effortless 90s off-duty model vibe...
Found the holy grail of denim today—these vintage Levi's 501 jeans... Grab them on my depop for just $38.00 before I change my mind...
Found the holy grail of denim today: these broken-in Vintage Levi's 501 Jeans... Can't believe my luck finding them on depop for just $38.00...
No outfit suggestion to write a caption from.
```

Three runs differ (TEMPERATURE 0.9, cache bypassed in this tool). Size match is whole-token: "M" matches "M", "S/M", "M/L", never "XL" or "US 9".

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I described my loop as a flow (empty search → message and stop; otherwise suggest an outfit, then a fit card, with a message if there is no outfit) and asked Claude to build `run_agent()` in `agent.py` from it.
- *What came back:* A working loop, but I only caught one bug by running it: the query parser read "size W28" as size `"W"`, because the size regex stopped at the first non-letter, so a size like that could never match a listing. Claude also pointed out that the "no outfit" branch can't trigger, because `suggest_outfit` already returns a generic sentence when the model returns blank text.
- *What I changed:* I had the size regex accept letters followed by digits ("W28") and slashes ("S/M"), then re-ran the parser on "size W28", "size S/M", "size US 9" and "size M". I kept the blank-outfit check in the loop as a guard rather than deleting it.

**Moment 2**

- *What I asked for:* I wanted a message to be generated when the search comes back empty. Claude implemented it as a fixed template, not a model call, and I then asked it to read the message as a user who knows nothing about the app and say what they would try next.
- *What came back:* The message names the keywords, size and budget that were applied, so a user knows what to change, but the three suggestions are chained as "Try to … or … or …" and don't say which change is most likely to help. Running a second query ("black boots under $70") also showed that `search_listings` can put unrelated items first (biker shorts ranked above boots), because "black" matches almost every listing.
- *What I changed:* I kept the template, since a fixed message is deterministic and can be tested, and my README states that choice. I have not yet changed the wording of the message or the ranking in `search_listings`; both are open items for unit 4.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
