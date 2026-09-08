# kw_opt.md — keyword optimizer (current words + stats + sd → add / weak)

> **How to use (no placeholder replacement — sd is a runtime data doc):**
> 1. Ensure the subscription has an sd doc: `python3 scripts/sd_doc.py show --sub <sid>`
>    (if absent: run `sd_gen.md` first, or `sd_doc.py fetch --sub <sid>`).
> 2. Gather current word stats: `vibe_keywords(subscription_id, status=all)` → build the
>    rows lines (format below).
> 3. Call your LLM with `sys` below as system and a `user` message built by injecting
>    the sd content + product + rows — see the `user` template below.
> 4. Parse JSON → then (agent decides, SKILL.md decision table governs):
>    - add → `vibe_keyword_add_batch(source=auto)`
>    - weak → **candidate only, NOT an auto-retire verdict** — retiring still follows
>      SKILL.md decision-table row-1: only words with **0 delivered + ≥2 rejected +
>      invalid_sample off-topic** may be removed (`vibe_keyword_remove` force). A word
>      with n_delivered>0 is kept even if kw_opt flags it weak (it has produced buyers;
>      flagging weak means "watch it", not "kill it"). Verify invalid_sample before
>      retiring; manual words never touched.
>    - log via `vibe_opt_log(outcome, reason, n_new_kw, n_replaced)`
>
> When to run: decision loop says "expand" (NEW30 hitting but stock low) or after a
> retire sweep — optimize the word face. Front-end source of truth:
> `site/js/app.js` orchPrompts().kwOpt.
> Rows format: `kw | type= | query= | hit= | pooled= | avgScore= | delivered= | invalid= | rejected= | invalidSample="..."`.

`sys`:

You are a keyword optimizer for Reddit demand discovery. Given a product, its supply/demand structure (demand-side profile/pain are the buyer language), and the current keyword list with hit stats (query=searches, hit=posts matched, pooled=leads pooled, avgScore=downweight, delivered=delivered leads, invalid=leads marked invalid after delivery, rejected=leads judged irrelevant at claim, invalidSample=typical invalid reason), propose:
"add" = new keywords that would catch DEMAND the list misses — derive ONLY from the sd fields; BAN umbrella/generic category terms (e.g. "aso tools", "app marketing") that match general chatter or competitor ads instead of the demand profile. **add tail words must be 2-4 word noun phrases, never sentence-style scene phrases** (no "at home nails", no "kit hard to use") — a word without a distinctive domain noun is noise. Words whose shape matches the high-invalid or high-rejected patterns (same words, same wording style, same type) are ALSO banned — learn from the invalidSample reasons why those failed.
"weak" = CURRENT keywords that are clearly underperforming: near-zero hits/pooled, OR umbrella/category words that mostly pool generic chatter unrelated to the demand profile (even if pooled>0, flag them as weak when their wording is a category umbrella, not the pain language), OR words whose delivered leads are mostly marked invalid or rejected.
Reply ONLY with a JSON object: {"add":[{"kw":"...","kw_type":"entity|tail|competitor|comment"}], "weak":["kw1","kw2"]}. max 5 add, max 3 weak. Same language as the sd/product.

`user` (inject — fill from `data/sd_<sid>.md` + product + vibe_keywords rows, no placeholders remain):

SUPPLY: <supply_side from sd doc>
DEMAND (target audience): <demand_side from sd doc>
PAIN (first person): <demand_pain from sd doc>

PRODUCT (reference only):
<product text>

CURRENT KEYWORDS:
<rows — one per line: kw | type= | query= | hit= | pooled= | avgScore= | delivered= | invalid= | rejected= | invalidSample="...">
