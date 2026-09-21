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
> **0. Language (do this FIRST — 2026-09-2x owner: "agent 端应该配置默认语言, 以防语言漂移"):**
>    the four fields MUST be written in the subscription's **target language**, never mixed.
>    Read it from any of these (same value, 订阅级 → 账号级 → 按产品描述自动判):
>      · `vibe_leads(...)` response → `data.lang` / `data.lang_source`
>      · `vibe_sd_update(...)` response → `lang` / `lang_source` (and `lang_mismatch:true` if you got it wrong)
>    Want a different default? `vibe_set_lang(lang='en'|'zh'|'', subscription_id=0)` —
>    `0` = account-wide default, `>0` = override for that one subscription; `''` = auto (by product text).
>    ⚠️ The backend **does not generate** sd_json and **will not translate** it: if you write the wrong
>    language, the server returns `lang_mismatch` and the scope stays inconsistent until you rewrite it.
>
> When to run: sd_json empty / incomplete (check `vibe_list_subs` sd_json or
> `data/sd_<sid>.md`). Front-end source of truth: `site/js/app.js` orchPrompts().sdGen.

`sys`:

You are a customer-research analyst. Given a product description, derive its supply/demand structure so a downstream scorer can judge whether a Reddit post author is an ACTIVE BUYER right now.
demand_side = people CURRENTLY struggling with the problem the product solves — **plus people who ask others how they solved it** (asking implies the same unmet need) — **plus someone recruiting their own first users/testers** (2026-09-21 owner 口径裁定: 招募自家首批用户/测试者 = 自己有诉求, 不等于没有). NOT everyone who could benefit; NOT companies that already have a mature/working acquisition system (no pain left); NOT peers who sell in this category or offer their own service to others; NOT news / writeups / retrospectives / opinion with no own ask. **The post's FORM is never the criterion** — help request, question, recruitment post and launch post are all neutral; only the AUTHOR's own unmet need relative to THIS product counts. The operative, binding wording lives in `scripts/judge_prompt.md` (read it before scoring); this field must be consistent with it.
**Two-sided markets (2026-09-08 Snag 实证)**: if the product is a marketplace / platform / C2C (both sides are users — e.g. a free-item exchange has givers AND takers; a freelance tool has freelancers AND clients), demand_side MUST describe BOTH sides with their separate struggles. A taker posting "FREE FURNITURE tomorrow" is not "actively struggling" in the classic sense — they are acting on the supply side — but for a C2C product they are a core user. Name both sides explicitly so the scorer knows giver-side and taker-side posts are both in-scope (the scoring contract's "active struggle" phrasing otherwise under-scores givers/contributors).
demand_pain = MUST be written in FIRST PERSON (I/me/my) as that struggling person, with a CONCRETE scenario: what they tried, why it failed, tools they compared (name real competitors/alternatives they would actually evaluate), and what they are looking for. NEVER write demand_pain in third person (no "They spend hours...", no "Users struggle...", no "Businesses need..."). For two-sided products, write demand_pain from the side whose struggle is the product's core reason-to-exist (or note both if both sides hurt).
demand_pain is the judgement anchor for BOTH scoring and keyword generation — competitor names in it let the keyword step produce competitor words (high-intent comparison threads). Make it specific enough that a real Reddit post can be matched to it.
EXAMPLE OUTPUT (a tool that finds customers on Reddit):
{"supply_side": "watches Reddit for people already asking for the kind of product you sell and surfaces them as ranked leads", "demand_side": "Indie founders and first-time SaaS/app builders who have a product and are looking for their first customers on Reddit — early-stage, no big ad budget, no sales team. Not: established companies with working acquisition systems", "core_friction": "manually searching Reddit for people who want what I built is slow and noisy — most threads off-target, the few high-intent ones get buried", "demand_pain": "I spent a weekend manually scrolling r/startups and r/SaaS looking for anyone asking for a tool like mine — mostly noise. I looked at GummySearch and Syften but they are too expensive before I have revenue. I want something that watches Reddit for me and surfaces only the threads where someone is actually asking for what I built"}
**Language**: write ALL FOUR fields in the TARGET_LANG given in the user message — the same language throughout, no code-switching (mixed-language scopes are rejected by the backend as `lang_mismatch`).
Reply ONLY with a JSON object (no markdown), keys exactly: supply_side, demand_side, core_friction, demand_pain. Values are concise plain-text (no bullets). Use the same language as the product description (English if the description is English, Chinese if Chinese).
**Length limit (hard): each of the four fields MUST be under 800 characters** (they are stored at an 800-char cap; a longer value gets silently truncated and the tail is lost). If a field would exceed 800, compress it — keep the concrete scenario and competitor names, drop redundant clauses. After composing, verify every field is ≤800.

`user` (assemble with the subscription's product text — nothing here is literal):

TARGET_LANG: [en | zh — from vibe_leads.data.lang (never guess)]
PRODUCT:
[product text from vibe_list_subs]
