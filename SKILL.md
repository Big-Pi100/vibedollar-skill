---
name: vibedollar
description: >-
  vibedollar helps indie founders find their first customers. Describe your product and it
  continuously monitors Reddit for potential-customer leads (posts + comments): Reddit lead generation that finds customers looking for you, with subscription
  tracking. Your agent judges relevance with its own LLM; you pay only for leads scored relevant
  (pay-per-outcome). Remote-hosted, zero setup. Paid plans: Starter $39/mo, Pro $79/mo; wallet
  top-up (WeChat / Creem) also available.
---

# vibedollar | find your first customers on Reddit

**The customers you want are already complaining and asking for solutions on Reddit. vibedollar brings them to you.**

You've built your product, but the posts and comments where people are actively solving the problem you solve are impossible to find with regular search. Describe your product, and vibedollar continuously collects **potential-customer leads** (candidate posts and comments, with author and full text). **Your agent scores them with your own LLM**, and scored-relevant ones go to your delivered list, clickable for outreach.

**We run the data service: Reddit collection + candidate matching into a raw pool, and the state layer (keywords / supply-demand scope / recycle / health). You decide what a good customer looks like — your agent scores with your LLM, and drives tuning: read health (`vibe_sub_health`) → expand / retire keywords (`vibe_keyword_add` / `vibe_keyword_remove`) when the commitment gap shows, and record optimization events (`vibe_opt_log`).**

> **Data source**: leads are records of **publicly visible posts at collection time**.
> Posts may later be removed by the platform or the author, but the historical record
> remains a valid demand signal; the author is a real person still reachable via
> Reddit DMs or their public contact info. Use leads in line with Reddit's platform
> terms and applicable laws.

**What you can do with the data** (three proven use cases):
- **Customer interviews**: the authors of relevant posts are your best interview candidates. Reach them via Reddit DMs or public contact info, and run short discovery calls to validate demand.
- **First 100 customers**: demand signals are a customer list in disguise. Score by how directly each person asks for a solution, reach out with a relevant first message, and turn replies into paying users.
- **SEO & GEO optimization**: the words your customers use in their posts are what search engines and AI assistants reward. Reuse them in your landing page, FAQ, and content.

- [中文版 SKILL](SKILL.zh-CN.md) · [README (English)](README.md)

## When to use it

| Scenario | How |
|----------|-----|
| Cold-start acquisition | `vibe_subscribe` → continuous tracking, leads accumulate, click into the post and reach the prospect |
| Validate a product idea | Subscribe, then look at accumulated leads: N strong-demand signals → worth building |
| Ongoing acquisition | `vibe_subscribe` → `vibe_leads` (free) → score → paid only on `relevant` |
| Proof for investors/team | Accumulated leads (that you scored) are ready-made demand validation |

## Quick start

1. **Connect** (remote-hosted, no local setup): add endpoint `https://mcp.vibedollar.net/mcp` to your MCP client (FastMCP HTTP transport).
2. **Register** (two-step; email code → key; key also emailed):
   ```
   vibe_register(email="you@example.com")   # sends a 6-digit code
   vibe_verify(email="you@example.com", code="123456")  # returns api_key
   ```
   > After verification the API key is **also emailed to you** (also viewable once on the success page). Keep it safe.
   > Unlock by: upgrade to Starter/Pro, or top up the wallet (WeChat ¥1–¥1000 / Creem $1–$200). The free tier gives 30 delivered leads/month as a demo (subscribe, claim, score — full flow), upgrade when useful.
3. **Configure auth header**: `Authorization: Bearer <key>` (or `Api-Key: <key>` if your client disallows custom Authorization). After that, data tools don't need `api_key` as a parameter.
4. **Check balance/quota**: `vibe_balance()` (key read from header).
5. **Web self-service** also available: `https://vibedollar.net/account.html` (register/verify/pay).

## Tools

| Tool | Params | What it does | Cost | Auth |
|------|--------|-------------|------|------|
| `vibe_register` | `email` | Step 1: send 6-digit verification code | Free | None |
| `vibe_verify` | `email, code` | Step 2: verify code, return api_key (also emailed) | Free | None |
| `vibe_balance` | — | Balance / tier / quota remaining (key via header) | Free | Header |
| `vibe_subscribe` | `product`, `enable_competitor_kw`(optional), `track_type`(optional) | **Continuous monitoring**: describe your product, system tracks and accumulates candidates (search direction managed for you). **Product description must be complete (40+ chars)**: name + one-line positioning + target users + website URL. Short descriptions produce generic keywords and low-relevance candidates; subscriptions with short descriptions are rejected. | `enable_competitor_kw` (default on): set `false` for direct-demand leads only, excluding competitor-comparison posts. `track_type` (internal use: outreach/seo/hot_content) | Free (candidates free) | Header |
| `vibe_leads` | `subscription_id, limit` | **Claim candidates (free)**: posts/comments with system reference score, each with a **source type** (direct demand / competitor comparison / comment, filterable via `kw_type`; excludes competitor-comparison when disabled). Billed only on pass. **Per-claim cap: free 20 / Starter 30 / Pro 50** (returns min(limit, tier cap)). Response includes `posts` (new candidates), `pending` (claimed, not yet scored, with `id`) and `source_status: locked` (score pending items first to unlock). See **Working with pending candidates** below | **Free** | Header |
| `vibe_submit_score` | `scores` | **Score candidates**: `relevant` = 1 delivered (1 quota), `irrelevant` = feedback for tuning | Billed on pass | Header |
| `vibe_score_discuss` | `limit, respond_id, response` | **Calibration (optional)**: view/respond to disagreements with the system reference score, and we tune the standard to match your judgment. Use it when a candidate's reference score surprises you; it also flags where your scoring may be drifting, so the pipeline stays aligned with your real definition of a good lead | Free | Header |
| `vibe_set_notify` | `enabled` | Email alerts on candidate backlog (default on) | Free | Header |
| `vibe_list_subs` | — | Your subscriptions + candidate accumulation status | Free | Header |
| `vibe_unsubscribe` | `subscription_id` | Cancel subscription (accumulated leads kept) | Free | Header |
| `vibe_cancel_plan` (指引) | — | **Paid plans (Starter/Pro) cancel via the payment platform** (Creem customer portal / WeChat Pay management), not via this API. After cancellation your tier stays until the current period ends, then downgrades to free; leads already delivered are kept. Product subscriptions are cancelled with `vibe_unsubscribe`. | Free | Header |
| `vibe_mark_leads` | `lead_ids, outcome` | Mark lead outcome (valid / invalid / contacted), track outreach quality | Free | Header |
| `vibe_get_delivered` | `lead_id` | Single delivered lead detail (follow-up), including **full body** for context | Free | Header |
| `vibe_delivered` | `limit, offset` | Delivered leads list (follow-up history) | Free | Header |
| `vibe_recover_key` | `email` | **Lost your API key?** Step 1: send a verification code to a registered email (no auth) | Free | None |
| `vibe_recover_verify` | `email, code` | Step 2: verify the code, your API key is emailed to you (no auth) | Free | None |

> All tools except `vibe_register` authenticate via the HTTP header `Authorization: Bearer <api_key>`; **the key never appears in tool params or call logs**.

### Management tools (2026-09-05 — keyword / health / recycle / scope)

| Tool | Params | What it does | Cost | Auth |
|------|--------|-------------|------|------|
| `vibe_keywords` | `subscription_id`, `status`(optional: all/active/monitor/removed/retire) | **Keyword list + hit stats** (query/hit/pooled/avg-score/source): what your subscription currently matches on and how each word performs. Read before deciding to expand or retire | Free | Header |
| `vibe_keyword_add` | `subscription_id`, `kw`, `kw_type`(tail/entity/competitor/comment), `source`(manual default / auto) | **Add a keyword** to broaden recall. `source=manual` words are yours and protected from auto-retirement; `source=auto` marks orchestrator-added words (they may be retired later). Adding the same word as an existing auto word takes ownership (manual) | Free | Header |
| `vibe_keyword_add_batch` | `subscription_id`, `keywords`(list of `{kw, kw_type}`), `source`(auto default) | **Add N keywords in ONE call** (same per-word semantics as `vibe_keyword_add`) — use this for init/expand lists of several words instead of looping, to stay inside the per-account rate window (free 5 / starter 10 / pro 20 per 60s). Per-word failures never fail the batch; returns `{added, total, results}` | Free | Header |
| `vibe_keyword_remove` | `subscription_id`, `kw`, `force`(false default) | **Retire a keyword** (status → removed, stops matching). Only manual words by default; `force=true` is for the orchestrator to retire weak auto words — don't use force manually | Free | Header |
| `vibe_sd_update` | `subscription_id`, `supply_side`, `demand_side`, `core_friction`, `demand_pain` | **Set the supply/demand judgement scope** (four fields, persisted server-side). This is the official judging context — it is injected into your scoring engine as [SUPPLY/DEMAND] on every call. Empty fields keep the previous value; it is never overwritten by the backend after you edit it | Free | Header |
| `vibe_sub_health` | `subscription_id` | **Delivery health, zero LLM**: quota / commitment line (2 × quota ÷ 30) / today's pooled / stock (new+sent) / gap flag / collecting_ok / last optimization event. Read this to decide whether to expand keywords | Free | Header |
| `vibe_opt_log` | `subscription_id`, `outcome`, `reason`, `n_new_kw`, `n_replaced` | **Record a keyword optimization event** (persisted to the optimization history shown in health) — call it after you expand/retire, so the loop is auditable | Free | Header |
| `vibe_rejected` | `subscription_id`, `limit` | **Recycle history**: candidates your engine marked irrelevant (with reason/score), persisted across sessions | Free | Header |
| `vibe_recover_lead` | `lead_id` | **Recover a misjudged lead** from recycle back to the scoring queue — re-score it (no double billing on pass) | Free | Header |
| `vibe_subs` | `subscription_id` | **Source subreddit hit stats** (pooled per sub, by status) — which subreddits actually contribute candidates. Note: this is *source stats*, distinct from `vibe_list_subs` (your subscriptions) | Free | Header |
| `vibe_supply_status` | `subscription_id` | **Corpus supply snapshot (zero LLM, 2026-09-07)**: sub pull pool size / reserve depth tiers / word-search last run / **7-day post_store intake trend** (is the corpus still growing?) / catalog freshness (total + last updated) / ArcticShift rate-limit state (shared circuit, cross-process). Read this to tell apart: *keywords exhausted* (expand) vs *corpus boundary thin* (widen subs) vs *registry stale* (catalog needs monthly refresh) vs *collection down* vs *rate-limited* | Free | Header |
| `vibe_search_probe` | `subscription_id`, `query`, `subreddits`, `limit`(≤5) | **Out-of-pool directed search probe (ArcticShift, 2026-09-07)**: search a keyword/phrase *inside target subreddits* before expanding it — verifies "does this phrase actually surface posts out there?" (instant feedback, no blind expansion). Found posts are upserted into the shared corpus (idempotent); **not** added to your lead pool (matching stays keyword-driven). Complements `sub_pull` (which only covers in-pool subs) | Free | Header |

> Cost note: the ten tools above are read/write state operations — candidates stay free; you still pay only on `relevant` verdicts via `vibe_submit_score`. (Final billing口径 confirmed separately if any of these ever charges.)

### Managing delivery health (commitment-gap driven tuning)

The backend's promise is **data delivery**: Reddit collection + matching into the pool. Your job is to keep the pool feeding your buyer profile. Health is the loop driver:

```
1. vibe_sub_health(subscription_id)         → line / pooled_today / stock / gap / collecting_ok
2. If gap (today's pool under line, or stock < 20) and collecting_ok:
     vibe_keywords(subscription_id)         → current words + hit stats
     (your LLM) propose add/retire          → keyword_add (source=auto) / keyword_remove(force)
     vibe_opt_log(...)                      → record the optimization event
3. If gap but !collecting_ok: the backend pulled little today — don't churn keywords, wait
```

This replaces the old "system auto-tunes" narrative: **you (your agent) are the tuner**, the service is a pure data/state layer. The same loop runs in the vibedollar web workbench orchestrator and in our own marketing fleet.

### Supply-side decisions (2026-09-07 — expand words vs widen corpus vs wait)

`gap` from health is the *delivery* flag — but the daily line is **not** a per-day intake target (day one's stock-match burst is huge; steady state is small increments). Judge **whether more keywords would help** by marginal yield, not by the line:

```
1. vibe_supply_status(subscription_id) → pool size / 7d intake trend / catalog fresh / arctic limited?
2. If arctic.limited: pause supply actions (probe/expand/widen) until it clears — physical wait, not a cooldown
3. If intake trend healthy and stock > 0: score the pool first (fast loop) — don't churn keywords
4. Keywords recently added still all hitting (>0 hit)? → keep expanding (probe-verified words only)
5. New keywords mostly zero-hit (auto-retired) → keyword face is swept → switch to corpus: widen subs
   (vibe_widen_pool on refreshed catalog) or deepen an in-pool sub (vibe_expand_sub)
6. Catalog last_updated_at is old → registry needs its monthly refresh (backend concern — alert, don't self-scan)
```

Key habit: **probe before you expand** — `vibe_search_probe(query, [subs])` tells you in seconds whether a
phrase surfaces posts out there; expanding blind and waiting 30min for pipeline stats is how keyword lists rot.
Retire zero-hit words via `vibe_keyword_remove(force=true)` (auto words) — the server also auto-retires them (F3).

## Scoring format (agent calling convention)

```
vibe_leads(subscription_id=12, limit=10)
    → candidates: [{"id": 1, "title": "...", "url": "...", "score": system_ref, ...}, ...]
    (limit above tier cap is clamped: free 20 / Starter 30 / Pro 50)

vibe_submit_score(scores=[
    {"id": 1, "verdict": "relevant",   "score": 90, "reason": "directly asking for a solution"},
    {"id": 2, "verdict": "irrelevant", "score": 10, "reason": "unrelated"},
])
    → {"ok": true, "passed": 1, "rejected": 1, "quota_used": 1, "quota_limit": 3000}
```

Rules:
- **Candidates free**: `vibe_leads` costs nothing
- **Pay on pass**: `verdict="relevant"` → 1 quota, added to delivered list (`vibe_delivered`)
- **Also return `irrelevant`**: that's how the state layer learns your standard — every `irrelevant` verdict downgrades the keyword that produced that candidate (pure SQL, server-side). **Your scoring quality drives keyword quality**: score honestly and thoroughly (read the full body, judge on your real buyer profile). Careless or bulk-scored feedback is detected by the consistency guard and weighted down.
- **Each candidate is scored once per claim; `irrelevant` verdicts land in the recycle pool (`vibe_rejected`)** — if you later decide one was misjudged (e.g. after opening the post), recover it with `vibe_recover_lead` and re-score. `relevant` is final (billed).
- **Score everything you claim**: claiming a batch moves candidates to `pending` and pauses the subscription until they are scored. A `locked` response with a `pending` list is **normal flow, not an error**: score every pending candidate (relevant or irrelevant) and the next batch unlocks. Never leave claimed candidates unscored.
- **Save every returned field**: persist the full record per candidate (id/title/url/subreddit/score, and body when present). `id` is required later for `vibe_get_delivered`; don't keep only titles.
- The candidate `score` is a system reference; your judgment wins

## Working with pending candidates (`locked` is normal)

The scoring question for every candidate is always: **is the author of this post a potential customer of the subscribed product?** Judge on topic (does it sit in the problem area the product solves) and signal strength. Answer `relevant` when yes, `irrelevant` when no (irrelevant still teaches the system and costs nothing).

Standard loop:
1. `vibe_subscribe(product)` with a **complete description** (name + positioning + target users + website, 40+ chars) → get `subscription_id`. A short description (product name only) is rejected — it would generate generic keywords and low-relevance candidates.
2. `vibe_leads(subscription_id, limit)` → save the **entire returned record** for each candidate. Don't drop fields.
3. Score **all** pending candidates with `vibe_submit_score` (verdict `relevant` or `irrelevant`), this unlocks the subscription for the next batch.
4. For leads scored `relevant`, `vibe_get_delivered(lead_id)` returns the full post body for outreach.

## Headless auto mode (run the loop with your own LLM, no interactive agent)

Prefer a scheduled, autonomous loop over an interactive session? `scripts/lead_agent.py`
runs the exact same claim → judge → submit loop unattended, judging with **your own
LLM key** (any OpenAI-compatible provider — DeepSeek, OpenAI, ...). vibedollar's own
marketing fleet runs this same pattern in production, so it is a proven, dogfooded loop.

```bash
export VIBEDOLLAR_API_KEY=...                          # from vibe_verify / account page
export LLM_API_KEY=...                                 # your LLM key
export LLM_BASE_URL=https://api.deepseek.com/v1        # OpenAI-compatible base
export LLM_MODEL=deepseek-chat
python3 scripts/lead_agent.py --limit 10               # one pass over all your subs
python3 scripts/lead_agent.py --sub 12 --out ./evidence   # one sub + save relevant rows
python3 scripts/lead_agent.py --loop 3600              # hourly daemon loop
python3 scripts/lead_agent.py --dry-run                # claim only, no LLM / no submit
```

- **Judgment is yours**: edit `scripts/judge_prompt.md` (plain template) to define what a
  good customer looks like for your market. `--threshold` (default 60) sets the
  relevant/irrelevant score cut.
- **Costs**: candidates free; `relevant` verdicts count against your vibedollar quota
  (pay-on-pass, same as interactive). The judging LLM calls are billed to **your** key.
- **Evidence (optional)**: `--out dir` appends CSV (or `--out-format json` → JSONL) of
  your relevant judgments, with reason + score, for your own records.
- **Failure-safe**: a candidate whose LLM judgment fails is simply left for the next run
  (pending candidates are retried automatically, never lost).

## Subscription mode (continuous monitoring)

```
vibe_subscribe(product="team wiki tool for small teams")
    → {"ok": true, "subscription_id": 12, "message": "tracking started..."}
vibe_list_subs()
    → {"ok": true, "data": {"subscriptions": [{"id": 12, "product": "...", "new_leads": 7}]}}
vibe_leads(subscription_id=12, limit=10)
    → {"ok": true, "data": {"posts": [{"id": 1, "title": "...", "url": "...", "subreddit": "...", "score": 90}], "count": 7}}
vibe_submit_score(scores=[{"id": 1, "verdict": "relevant", "score": 90, "reason": "..."}])
    → {"ok": true, "passed": 1, "quota_used": 1, ...}
```

- For a defined product that needs **continuous** new prospects, not ad-hoc searches
- No keyword/source maintenance by hand: describe the product, we collect + match into the pool; when delivery runs behind the commitment line, **you** (your agent) expand/retire keywords via the health tools — see **Managing delivery health** below
- **Paid on pass only** (pay-per-outcome); subscription itself is free
- **Score the batch to unlock the next**: claimed candidates must all be scored (relevant or not) before the next claim; claiming early returns the pending list with ids (ids recoverable, never locks your subscription). Candidates un-scored for 7 days auto-expire.

Cancel with `vibe_unsubscribe` (accumulated leads kept).

## Ways to use the data (beyond the lead list, no extra service)

Subscription data = **real people expressing real needs in their own words** (who + where + how they say it). It's not just a lead list; it feeds downstream work:

### ① Customer interviews (understand the customer, pre-PMF)
```
Source: vibe_leads candidates (author + original text + subreddit)
Use it to:
  - Interview pool: candidate authors are people actively expressing the
    problem you solve, sharper than a generic persona (they already said
    the need in their own words)
  - Interview questions: extract what they actually ask, what they're torn
    about, which alternatives they compare; build the interview guide
    around their real concerns, don't guess
  - Language alignment: write product copy / landing pages in their words
    ("this was made for me" feeling)
```

### ② First 100 customers (cold start, from discovery to outreach)
```
Source: scored-relevant delivered leads (vibe_delivered, authors reachable)
Use it to:
  - Priority list: sort by score/reason: "directly asking for a solution"
    authors get contacted first
  - Outreach copy: reference the real need from their post ("saw you ask
    about X on Reddit"), which beats template blasts (door-opener: evidence
    first, personal, one soft ask)
  - Cadence: process a batch weekly (score → filter → contact → follow up);
    candidates keep accumulating, and first customers come from first delivered
    leads
```

### ③ SEO/GEO content data (content strategy, from keywords to user language)
```
Source: subscription keyword set (how your domain's users actually phrase
things on Reddit) + candidate posts
Use it to:
  - Content skeleton: extract how users describe the problem, and write
    titles/H1/FAQ in their language (more authentic than optimized
    keywords; AI engines prefer citing real community language)
  - Evidence references: candidate posts as real demand evidence in
    articles (describe patterns, don't name authors)
  - Keyword iteration: recurring phrasing in candidates → update content
    keywords (your score feedback also sharpens the subscription; a
    two-way loop)
```

**Common thread**: all three reuse **data you already receive**; no new
service, no interface changes. vibedollar provides "people expressing the
need + their own words"; how you use it (interviews / outreach / content)
is up to your agent.

## Agent usage tips

- **User lost their API key?** Guide them through recovery; no re-registration needed:/n  ```
  vibe_recover_key(email=...)          # sends a verification code to their registered email
  vibe_recover_verify(email=..., code=...)  # verifies → API key is emailed to them
  ```
  (Or point them to https://vibedollar.net/account.html → "Lost your API key? Recover it")
- **Register first, then configure the header**: key goes in `Authorization: Bearer <key>`. Missing header → `"Missing API key"`; unregistered key → `"Unknown API key"`.
- **Self-manage via the `quota` block**: each response carries `quota: {scope, used, limit}` (e.g. `{"scope": "3000/mo", "used": 5, "limit": 3000}` = 5/3000 used). Proactively suggest an upgrade (Starter/Pro) before exhaustion.
- **`vibe_leads` returns candidates (posts + comments, free)**: id / title / url / body; your agent reads and judges, then returns scores via `vibe_submit_score`.
- **Paid on pass**: `relevant` → 1 quota + delivered list (`vibe_delivered`); `irrelevant` also returned (tunes search direction, pushes get more accurate).
- **Score the batch before the next claim**.
- **Typical workflow**: `vibe_subscribe` → `vibe_leads` → your agent scores with your LLM → `vibe_submit_score` → passed leads in delivered list (validate demand + find first customers).

## Pricing

| Tier | Price | **Delivered leads** (scored relevant) | Rate limit |
|------|-------|----------------------------------------|------------|
| **Free** | Sign-up | **30/mo** (demo: 1 subscription, 20 per claim; overage $0.05/lead from wallet) | 30 req/min |
| **Starter** | **$39/mo** | **800/mo** (paid on pass; candidates free; score the batch to unlock the next; 30 per claim) | 60 req/min |
| **Pro** | **$79/mo** | **3000/mo** (paid on pass; candidates free; 50 per claim) | 120 req/min |
| **Wallet top-up** | Any amount (Creem $1–$200 / WeChat ¥1–¥1000) | Extends quota at **$0.05/lead** after tier quota runs out | — |

- **"Lead" = one scored-relevant item**: 1 post or 1 comment = 1 lead (poster/commenter are both prospects). Candidates free; `relevant` consumes 1 quota; auto-limited when insufficient, no oversell.
- **After quota**: paid leads auto-deduct $0.05 from wallet (prompt top-up when low); Free tier 30/mo then wallet.
- **Free tier at signup**: register for the key and get the free tier (30 delivered leads/month demo — subscribe, claim, score — the full flow). Upgrade to Starter/Pro or top up when you need more.
- **Upgrade (Starter/Pro)**: Creem (global) or WeChat Pay (CN) at `mcp.vibedollar.net`; auto-activation after payment. **Annual 20% off** (coming soon). **No trial**.

## Payment & activation (agent workflow)

**The only user action is scanning a QR / clicking a link**: registration, ordering, generating the QR, confirming activation are all done by you (the agent).

1. **Confirm/register api_key**: `vibe_balance()` → "Missing API key" means no header configured. If the user has no key: `vibe_register(email=...)` → user gives you the emailed 6-digit code → `vibe_verify(email, code)` → api_key. **Don't ask the user to self-register**; that's your job; the user only provides email and code.
2. **Pick channel by location**:
   | Location | Channel | Price |
   |----------|---------|-------|
   | Global (default) | **Creem** (USD card) | Starter $39/mo / Pro $79/mo / Top-up $1–$200 (Pay What You Want) |
   | Mainland China | **WeChat Pay** (CNY) | Starter ¥280.8/mo / Pro ¥568.8/mo / Top-up ¥1–¥1000 |
3. **Generate payment entry**:
   - **Creem (global)**: `POST https://mcp.vibedollar.net/creem/checkout` `{"api_key": "<key>", "plan": "starter|pro|topup", "email": "..."}` → `{"ok": true, "url": "<payment link>"}` → send the url (top-up: user enters $1–$200 on the Creem page). **Never put api_key in URLs**.
   - **WeChat (CN)**: `POST https://mcp.vibedollar.net/pay/native` `{"api_key": "<key>", "email": "...", "tier": "starter|pro|topup"}` → `code_url` → render as QR → user scans (top-up: add `"amount_cents": <CNY×100>`, e.g. ¥36 → 3600).
4. **User pays → confirm activation**: poll `GET https://mcp.vibedollar.net/pay/orders/<out_trade_no>` or re-check `vibe_balance()`: tier/credit auto-updates via WeChat callback / Creem webhook, no manual step.

Edge cases:
- User already has a key → use it directly, don't re-register
- User prefers web → point them to `https://vibedollar.net/account.html` (equivalent self-service flow)
- Tier not updated after payment → wait 1–2s, re-check `vibe_balance()`; still stale → report `out_trade_no` and contact support@vibedollar.net
- Cancel: Starter/Pro downgrade at expiry (no hard cut), no agent action

## MCP client config

```json
{
  "mcpServers": {
    "vibedollar": {
      "type": "http",
      "url": "https://mcp.vibedollar.net/mcp",
      "headers": {
        "Authorization": "Bearer <your-key>"
      }
    }
  }
}
```

Some clients (Claude Desktop / Cursor) allow headers via env/config; set `Authorization: Bearer <key>` on the server headers per their docs. Alternative header: `Api-Key: <key>`.

Connect → `vibe_register` → configure the key in the header → call data tools (Reddit collection, matching and state are ours; judging and keyword tuning are yours — see **Managing delivery health**).
