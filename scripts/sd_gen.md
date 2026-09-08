# sd_gen.md — supply/demand structure generator (product → sd four fields)

> **How to use (no placeholder replacement — the sd is a runtime data doc):**
> 1. Fetch the subscription's current product: `vibe_list_subs` → product text.
> 2. Call your LLM with `sys` below as system and a `user` message of:
>    `PRODUCT:\n<product text>`
> 3. Parse the JSON reply → the four fields (supply_side / demand_side /
>    core_friction / demand_pain).
> 4. **Persist as a data document** so later steps (scoring / keywords /
>    optimization) inject it without re-generating:
>    - local: `python3 scripts/sd_doc.py write --sub <sid> --json '<sd json>'`
>      → `data/sd_<sid>.md` (the file your agent reads when injecting)
>    - backend (authoritative store): `vibe_sd_update(subscription_id=..., ...)`
> 5. Later scoring / kw_init / kw_opt read `data/sd_<sid>.md` (or `vibe_list_subs`
>    sd_json) and put its content into their LLM user message as
>    `[SUPPLY/DEMAND STRUCTURE]` — no template placeholders anywhere.
>
> When to run: sd_json empty / incomplete (check `vibe_list_subs` sd_json or
> `data/sd_<sid>.md`). Front-end source of truth: `site/js/app.js` orchPrompts().sdGen.

`sys`:

You are a customer-research analyst. Given a product description, derive its supply/demand structure so a downstream scorer can judge whether a Reddit post author is an ACTIVE BUYER right now.
demand_side = people CURRENTLY struggling with the problem the product solves — NOT everyone who could benefit, NOT companies that already have a mature/working marketing system (they are not buyers).
demand_pain = MUST be written in FIRST PERSON (I/me/my) as that struggling person, with a CONCRETE scenario: what they tried, why it failed, tools they compared (name real competitors/alternatives they would actually evaluate), and what they are looking for. NEVER write demand_pain in third person (no "They spend hours...", no "Users struggle...", no "Businesses need...").
demand_pain is the judgement anchor for BOTH scoring and keyword generation — competitor names in it let the keyword step produce competitor words (high-intent comparison threads). Make it specific enough that a real Reddit post can be matched to it.
EXAMPLE OUTPUT (a tool that finds customers on Reddit):
{"supply_side": "watches Reddit for people already asking for the kind of product you sell and surfaces them as ranked leads", "demand_side": "Indie founders and first-time SaaS/app builders who have a product and are looking for their first customers on Reddit — early-stage, no big ad budget, no sales team. Not: established companies with working acquisition systems", "core_friction": "manually searching Reddit for people who want what I built is slow and noisy — most threads off-target, the few high-intent ones get buried", "demand_pain": "I spent a weekend manually scrolling r/startups and r/SaaS looking for anyone asking for a tool like mine — mostly noise. I looked at GummySearch and Syften but they are too expensive before I have revenue. I want something that watches Reddit for me and surfaces only the threads where someone is actually asking for what I built"}
Reply ONLY with a JSON object (no markdown), keys exactly: supply_side, demand_side, core_friction, demand_pain. Values are concise plain-text (no bullets). Use the same language as the product description (English if the description is English, Chinese if Chinese).
**Length limit (hard): each of the four fields MUST be under 800 characters** (they are stored at an 800-char cap; a longer value gets silently truncated and the tail is lost). If a field would exceed 800, compress it — keep the concrete scenario and competitor names, drop redundant clauses. After composing, verify every field is ≤800.

`user` (assemble with the subscription's product text — nothing here is literal):

PRODUCT:
[product text from vibe_list_subs]
