---
name: vibedollar
description: "vibedollar helps indie founders find their first customers. Describe your product and it continuously monitors Reddit for potential-customer leads (posts and comments). A lead is billed when you claim it; scoring it with your own LLM is free. Remote-hosted, zero setup. Free 1,000 leads/mo; Starter $19/mo (5,000); Pro $79/mo (30,000); wallet top-up available."
---

# vibedollar | find your first customers on Reddit

vibedollar monitors Reddit for posts and comments where people are actively seeking
the kind of product the user builds, and surfaces them as scored **potential-customer
leads**. Division of labor: vibedollar runs the data service (Reddit collection,
candidate matching into a raw pool, and the state layer — keywords / supply-demand
scope / recycle / health); **the host agent decides what a good customer looks like** —
it scores candidates with its own LLM key and drives tuning (see **Delivery-health
tuning** and **Supply-side decisions** below).

> **Data source**: leads are records of **publicly visible posts at collection time**.
> Posts may later be removed by the platform or the author, but the historical record
> remains a valid demand signal; the author is a real person still reachable via
> Reddit DMs or their public contact info. Use leads in line with Reddit's platform
> terms and applicable laws.

**What the data is good for** — full playbooks (interviews / first 100 customers /
SEO-GEO) live in `references/use-cases.md`; short form:
- **Customer interviews**: authors of relevant posts are the best interview candidates.
- **First 100 customers**: demand signals are a customer list in disguise; score by
  how directly each person asks for a solution, then reach out.
- **SEO & GEO optimization**: reuse customers' own words on landing page / FAQ / content.

- [中文版 SKILL](SKILL.zh-CN.md) · [README (English)](README.md) · [Skill design guide](SKILL-DESIGN-GUIDE.md)

## When to use it

| Scenario | How |
|----------|-----|
| Cold-start acquisition | `vibe_subscribe` → continuous tracking, leads accumulate, click into the post and reach the prospect |
| Validate a product idea | Subscribe, then look at accumulated leads: N strong-demand signals → worth building |
| Ongoing acquisition | `vibe_subscribe` → `vibe_leads` (billed when claimed) → score (free) → relevant leads land in the delivered list |
| Proof for investors/team | Accumulated leads (that you scored) are ready-made demand validation |

## Quick start

1. **Connect** (remote-hosted, no local setup): add endpoint `https://mcp.vibedollar.net/mcp` to your MCP client (FastMCP HTTP transport).
2. **Register (first time only)**: `vibe_register(email)` sends a 6-digit code; `vibe_verify(email, code)` returns the api_key (also emailed). The free tier already includes 1,000 claimed leads/month (1,000/day); purchase Starter/Pro or top up the wallet for more. Full registration, unlock, payment and activation flow: `references/billing.md`.
3. **Configure auth header**: `Authorization: Bearer <key>` (or `Api-Key: <key>` if your client disallows custom Authorization). After that, data tools don't need `api_key` as a parameter.
4. **Check balance/allowance**: `vibe_balance()` (key read from header) — returns the `claim_quota` usage block.
5. **Web self-service** also available: `https://vibedollar.net/account.html` (register/verify/pay).

## Tools

| Tool | Params | What it does | Cost | Auth |
|------|--------|-------------|------|------|
| `vibe_register` | `email` | Step 1: send 6-digit verification code | Free | None |
| `vibe_verify` | `email, code` | Step 2: verify code, return api_key (also emailed) | Free | None |
| `vibe_balance` | — | Balance / tier / monthly claim allowance used + daily cap (key via header) | Free | Header |
| `vibe_subscribe` | `product`, `enable_competitor_kw`(optional), `track_type`(optional) | **Continuous monitoring**: describe your product, system tracks and accumulates candidates (search direction managed for you). **Product description must be complete (40+ chars)**: name + one-line positioning + target users + website URL. Short descriptions produce generic keywords and low-relevance candidates; subscriptions with short descriptions are rejected. | `enable_competitor_kw` (default on): set `false` for direct-demand leads only, excluding competitor-comparison posts. `track_type` (internal use: outreach/seo/hot_content) | Free (candidates free) | Header |
| `vibe_leads` | `subscription_id, limit` | **Claim leads (billed per lead claimed)**: posts/comments with system reference score, each with a **source type** (direct demand / competitor comparison / comment, filterable via `kw_type`; excludes competitor-comparison when disabled). Returns a `billing` block (batch size, free/billable split, charge, month usage, daily cap). **Per-claim cap: free 20 / Starter 30 / Pro 50** (returns min(limit, tier cap)). Response includes `posts` (new leads), `pending` (claimed, not yet scored, with `id`) and `source_status: locked` (when 50 unscored pendings accumulate, score them to continue; see **Working with pending candidates**) | **Billed per lead claimed** | Header |
| `vibe_submit_score` | `scores` | **Score claimed leads (free)**: `relevant` = moved to delivered list, `irrelevant` = feedback for tuning. Scoring never affects billing | **Free** | Header |
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
| `vibe_sub_health` | `subscription_id` | **Supply health + delivery assessment, zero LLM**: `assessment` (can the current search face fill the monthly claim allowance: `projected_items_month` vs `commitment_remaining`, `gap_reason`, `supply_per_day`, `daily_need`) / stock (new+sent) / gap flag / collecting_ok / last optimization event. Read this first: when `gap_reason=supply_ceiling`, widening the **sub list** beats touching keywords | Free | Header |
| `vibe_opt_log` | `subscription_id`, `outcome`, `reason`, `n_new_kw`, `n_replaced` | **Record a keyword optimization event** (persisted to the optimization history shown in health) — call it after you expand/retire, so the loop is auditable | Free | Header |
| `vibe_rejected` | `subscription_id`, `limit` | **Recycle history**: candidates your engine marked irrelevant (with reason/score), persisted across sessions | Free | Header |
| `vibe_export_leads` | `subscription_id`, `status`(delivered/rejected/new), `limit`, `offset`, `include_body` | **Export customer data with attribution (2026-09-08, zero LLM)**: delivered customers / rejected / new candidates, each with kw + kw_type + last score/reason (from your scoring feedback) + outcome/marked_at follow-up state + optional body. The authoritative store is the backend PG (delivered_log/lead_pool/scoring_feedback) — this tool surfaces it over MCP so you don't touch the DB. Use for outreach lists, outcome analysis, or feeding downstream (interviews/SEO) work | Free | Header |
| `vibe_recover_lead` | `lead_id` | **Recover a misjudged lead** from recycle back to the scoring queue — re-score it (no double billing; the lead was already billed when first claimed) | Free | Header |
| `vibe_subs` | `subscription_id` | **Source subreddit hit stats** (pooled per sub, by status) — which subreddits actually contribute candidates. Note: this is *source stats*, distinct from `vibe_list_subs` (your subscriptions) | Free | Header |
| `vibe_supply_status` | `subscription_id` | **Corpus supply snapshot (zero LLM, 2026-09-07)**: sub pull pool size / reserve depth tiers / **7-day post_store intake trend** (is the corpus still growing?) / catalog freshness (total + last updated) / ArcticShift rate-limit state (shared circuit, cross-process). Read this to tell apart: *keywords exhausted* (expand) vs *corpus boundary thin* (widen subs) vs *registry stale* (catalog needs monthly refresh) vs *collection down* vs *rate-limited*. (2026-09-09: the old word-search-leg field was removed — word corpus matching is read via `pipeline_recent` below; out-of-pool probing is `vibe_search_probe`) | Free | Header |
| `vibe_search_probe` | `subscription_id`, `query`, `subreddits`, `limit`(≤5) | **Out-of-pool directed search probe (ArcticShift, 2026-09-07)**: search a keyword/phrase *inside target subreddits* before expanding it — verifies "does this phrase actually surface posts out there?" (instant feedback, no blind expansion). Found posts are upserted into the shared corpus (idempotent); **not** added to your lead pool (matching stays keyword-driven). Complements `sub_pull` (which only covers in-pool subs) | Free | Header |
| `vibe_sub_list_update` | `subscription_id`, `subs`(list), `mode`(replace/add/remove) | **Maintain this subscription's sub list — its explicit search face (v2.2 sub-anchored, 2026-09-09)**: matching runs only inside list subs. Each returned sub tagged `in_pool` (corpus searchable now, posts+comments) or `needs_pull` (server will bulk-fetch it). See "sub-anchored search" section for the decision loop | Free | Header |
| `vibe_sub_catalog` | `query`(optional), `limit` | **Candidate subs before you pick a list (v2.2, 2026-09-09)**: no query → A relevance face (subs with real `relevant` deliveries, delivered DESC — in-corpus, searchable now); with a product/niche query → B/C lexical candidates from the registry (may need pull). Each tagged `stock`(in_pool/needs_pull), `tier`(deep/shallow), `delivered` count — value semantics are scoring-relevant, not raw hits | Free | Header |

> Cost note: the fifteen tools above are read/write state operations — **a lead is billed when first claimed** (Free 1,000/mo · Starter 5,000/mo, then $5 per 1,000 · Pro 30,000/mo, then $3.50 per 1,000); **scoring, re-reading and exporting are free**; daily-cap overflow carries to the next day.

### Agent decision loop (per subscription, per round — v2.1 delivery-driven)

vibedollar is the **data/state layer — server makes zero decisions**. It collects Reddit,
matches candidates into the pool, records your scoring feedback as signals, and returns
health data; **you (the host agent) decide everything** — expand / retire / regenerate /
probe / wait / report. There is no server-side auto-retire to wait for: hit=0, avg_score,
n_rejected etc. are *signals for you to act on*, not actions the server takes.

**The loop is driven by the delivery goal, not by "is there a pool to score".** Each round:

```
goal check → perceive → plan (one action) → act → verify → back to goal check
```

#### 0. Goal check (before anything — the loop's engine)

Goal = can the current search face fill the customer's monthly claim allowance this month
(see `vibe_sub_health.assessment`: `projected_items_month` vs `commitment_remaining`,
plus `gap_reason`). Every round asks:

- **`committed_ok`** → `wait` (fast loop digests; no supply action needed)
- **`shortfall`** → the task is NOT done. Pick the next action from the decision table
  below, act, verify, and **return to the goal check**. You may only stop (report
  exhausted) after trying every available direction and verifying none improved supply.
  **Never end a round silently after scoring** — "scored 15, all irrelevant" is a signal
  to change direction, not a completed task.

#### 1. Perceive (read tools, zero LLM)

```
vibe_sub_health(sid)     → assessment (projected_items_month / commitment_remaining / gap_reason /
                           supply_per_day / daily_need / backlog stock) + stock / gap / collecting_ok / last_opt
vibe_supply_status(sid)  → corpus intake trend / catalog age / arctic.limited
vibe_keywords(sid, all)  → per word: status/source/query/hit/pooled/avg_score/
                           n_delivered/n_rejected/invalid_sample/created_at
vibe_subs(sid)           → which subreddits actually contribute candidates
vibe_sub_list_update(sid, subs=[], mode="list")  → your current sub list (v2.2: your explicit search face)
```

**v2.2 (2026-09-09) — your search face is your sub list.** Matching now runs **only
inside the subs you listed** (`vibe_sub_list_update`), never the whole corpus. So the
loop's supply side is: *keep the list healthy* — subs you've proven deliver stay;
subs you've never scored relevant on are noise; subs you haven't listed aren't
searched at all. Before expanding words, check your list:

#### 2. Health-data semantics (what each returned number means → what you decide)

The server only *reports* these; **you** act on them (v2.1 — server makes zero decisions):

| Data | What it means | Your decision |
|---|---|---|
| `assessment.gap_reason` | why supply can't fill the allowance: `supply_ceiling` (face too narrow / vertical thin) · `word_face` (relevant rate < 15%) · `capacity` (need exceeds the daily cap) · `collecting` · `no_data` · `ok` | **supply_ceiling → widen the sub list** (add subs; this is the usual fix) · `word_face` → retire/regenerate words · `capacity` → nothing to fix on supply (it's the daily throttle) · `collecting` → alert, wait for intake |
| `projected_items_month` vs `commitment_remaining` | can the face fill the monthly claim allowance (items, matching the billed unit) | **goal check**: `committed_ok` → wait; `shortfall` → act (this drives everything) |
| `hit_count` = 0 | the phrase hasn't matched yet in corpus — **not conclusive on round one** (2026-09-08 Snag: "declutter home" q1=0 then q2 hit — search intake is incremental, a word can surface once its post arrives) | don't retire on a single 0-hit round: keep observing until qc≥3; if still 0 after several rounds with the corpus growing, probe targeted subs, replace the phrasing, or retire (F3-like: sustained 0-hit across rounds with fresh corpus = phrase absent) |
| `hit_count` > 0 but all your scores `irrelevant` | the phrase exists but **matches noise** — it's a wrong word, not proof demand is exhausted | retire the word, then **regenerate the word face from sd** (`sd_gen.md` if sd missing → `kw_init.md` → `vibe_keyword_add_batch`) — wrong words are fixed by regenerating, not by giving up |
| `n_rejected` ≥ 2 + 0 delivered + `invalid_sample` off-topic | noise generator | `vibe_keyword_remove` force + `vibe_opt_log` (see Plan A) |
| `avg_score` (negative) | aggregated scoring feedback signal (−3 per your irrelevant, server records only) | the more negative, the more rejects — supports retire/regenerate decision; **server does not retire on it** |
| `query_count` < 3 | not enough observation | don't judge yet (avoid single-shot miskill) |
| `created_at` recent | NEW30 group (judge ② input) | recently-added words' hit rate → keep expanding or stop |
| `collecting_ok=false` | backend intake down today | alert — expanding is useless until collection recovers |
| `pipeline_recent` (matched=0 several rounds) | words find nothing in corpus now | word exhaustion → probe/replace/regenerate; **distinguish from corpus intake stall**: if `corpus_today` collapsed (vs ~90k/day baseline) the corpus isn't growing — wait/alert, not a word problem |
| `arctic.limited` | physical rate limit | pause supply actions until clear (not a cooldown) |

#### 3. Plan — one action, driven by the goal

**A. Close your own scoring loop first** (scoring feedback is the strongest signal).
If your last scoring round produced `irrelevant` verdicts for a word with **0 delivered**
(n_rejected ≥ 2 and `invalid_sample` shows off-topic junk it pulls) → that word is a
noise generator → **retire it now**:

```
vibe_keyword_remove(subscription_id, kw, force=true)   # auto word — your call, no server batch to wait for
vibe_opt_log(subscription_id, outcome="auto_retire", reason="0 relevant, N irrelevant")
```

`n_rejected` is cumulative across scorers — when you can't tell whose rejects they are,
let `invalid_sample` arbitrate: clearly off-topic junk confirms a noise generator; a
plausible in-scene post that was rejected suggests a misjudgment — recover it
(`vibe_recover_lead`), don't retire the word on that evidence.

**B. Then read the NEW30 marginal-yield signal** (is expanding keywords still useful?):
words added in the last ~30 days (`created_at` recent):
- mostly **hitting** (>0 hit) and delivery still short → keep expanding (probe-verified words only)
- mostly **zero-hit** → the current word face can't reach demand → don't just stop: probe
  alternative phrasings, and if the face is exhausted after retires, **regenerate from sd**
  (see C) before concluding anything about the market

**C. All-irrelevant ≠ market ceiling — regenerate the word face.** If you retired a batch
of noise words (0 relevant) and delivery is still short, the words were wrong, not the
demand. Regenerate from the supply/demand profile: sd missing → `sd_gen.md` →
`vibe_sd_update`; then `kw_init.md` (or `kw_opt.md` with current rows) → new word face →
`vibe_keyword_add_batch`. Only after a regenerated face also fails (new words hit=0 or
all-irrelevant again) do you move to corpus exploration or report.

Decision table (goal-driven, v2.2 sub-anchored — 2026-09-09):

| Observed | Action |
|---|---|
| Goal met / exceeded | `wait` (fast loop digests) |
| Goal not met, stock(new+sent)>0 | score the pool (`score_batch.py`) — results feed this table next round |
| **sub list empty** | pick your search face: `vibe_sub_catalog` (A: subs with real deliveries — in-corpus, searchable now; B/C: niche candidates, may need pull) → `vibe_sub_list_update(subs, mode="replace")` → server bulk-fetches `needs_pull` subs automatically |
| **list subs all silent** (`pipeline_recent` matched=0 several rounds, corpus growing) | widen the list — the demand lives in subs you haven't listed: `vibe_sub_catalog(query=<product/niche words>)` → add candidates (B/C may need a one-time fetch, ~min/sub) |
| word: 0 delivered + ≥2 rejected, `invalid_sample` off-topic | `vibe_keyword_remove` force + `vibe_opt_log` |
| face cleared after retires, goal still short | **regenerate**: sd_gen (if sd missing) → kw_init/kw_opt → `vibe_keyword_add_batch` |
| new words hit=0 across rounds, list healthy | the phrase is absent in your listed subs' corpus → `vibe_search_probe` a targeted sub (pure-fetch + local match, ~2s) to verify phrasing; replace if 0; a probe-0 on chosen subs is NOT proof it's absent elsewhere — widen the list instead (v2.2: matching is list-scoped; **word-search leg retired 2026-09-09**) |
| NEW30 hitting, goal short | expand: `vibe_keyword_add_batch` (probe-verified) |
| NEW30 swept, collecting_ok | corpus boundary thin → widen your sub list (stage B), probe + record meanwhile |
| `collecting_ok=false` | alert (intake down — expanding useless) |
| `arctic.limited` | pause supply actions — physical wait, not a cooldown |

**Exhausted (only legal stop)** — delivery still short AND you have already tried, in
order, with verification at each step: score → retire noise → widen/refresh your sub
list (catalog A/B/C) → regenerate face from sd → probe → report. Then report honestly
what you tried and why the ceiling is real (market wording / corpus boundary), and log
it. **No silent stops**: every round ends with "continue toward goal" or "exhausted,
here is the evidence".

#### 4. Act

Execute **one** action. After add/remove, call `vibe_opt_log(...)` (auditable in health).
State the **expect**: what should the next round show if the action worked (e.g.
"regenerated words hit within a pipeline round" / "retired word stops pooling junk" /
"delivered increments by N")?

#### 5. Verify (next round)

Check the expect against the new perceive, then **return to the goal check**:
- Expect met → continue the same direction (same action type)
- Expect failed → **switch strategy**: score → retire → regenerate → probe → corpus —
  don't repeat a failing action
- Delivery still short with directions left → next round continues; only exhausted
  (above) permits `report_exhausted`

**Discipline** (no time cooldowns / daily caps — v2 §5.3):
- one direction action per round (convergence discipline, not throttling)
- verify-gated, not clock-gated: act → see the result → decide next
- **probe before you expand**: `vibe_search_probe(query, [subs])` gives instant feedback
  on whether a phrase surfaces posts in *chosen* subs — never blind-expand and wait for
  pipeline stats. But a probe-0 is **sub-scoped**: it proves nothing about the whole
  corpus (the pool word-search does); use probe to pick between candidate phrasings or
  to check a specific niche sub, and use `pipeline_recent`/hit_count as the corpus-wide
  truth before retiring a word on "0 hit".
- the only hard wait is the ArcticShift rate limit, surfaced via `vibe_supply_status`

#### 6. Audit log (per round)

Record each round so decisions are replayable and prompts iterable — ts / sid / round_no /
goal check result / world (raw tool returns, uncropped) / prompt sent / llm_raw / plan /
action / result / verify / cost. Persist it in your own store (exportable JSON). Without
this you cannot answer "why did the agent decide that" or iterate the loop — the log is
core infrastructure, not a post-hoc patch.

## Scoring format (agent calling convention)

```
vibe_leads(subscription_id=12, limit=10)
    → leads: [{"id": 1, "title": "...", "url": "...", "score": system_ref, ...}, ...]
      billing: {"claimed_batch": 10, "free_items": 10, "charge_usd": 0.0,
                "claimed_this_month": 10, "claimed_quota": 5000,
                "daily_used": 10, "daily_cap": 1000}
    (limit above tier cap is clamped: free 20 / Starter 30 / Pro 50)

vibe_submit_score(scores=[
    {"id": 1, "verdict": "relevant",   "score": 90, "reason": "directly asking for a solution"},
    {"id": 2, "verdict": "irrelevant", "score": 10, "reason": "unrelated"},
])
    → {"ok": true, "passed": 1, "rejected": 1, "quota_used": 1, "quota_limit": 3000}   # scoring is free
```

Rules:
- **Billed per lead claimed**: `vibe_leads` returns a `billing` block; within the monthly allowance it is $0, beyond it the extra is deducted from wallet credit ($5/1,000 Starter, $3.50/1,000 Pro). Telling the user what a claim costs is your job.
- **Scoring is free**: `verdict="relevant"` moves the lead to the delivered list (`vibe_delivered`); unlike the old model, scoring never consumes allowance.
- **Also return `irrelevant`**: that's how the state layer learns your standard — every `irrelevant` verdict downgrades the keyword that produced that lead (pure SQL, server-side). **Your scoring quality drives keyword quality**: score honestly and thoroughly (read the full body, judge on your real buyer profile). Careless or bulk-scored feedback is detected by the consistency guard and weighted down.
- **Daily cap**: Free/Starter 1,000, Pro 3,000 claimed leads/day; when the cap is hit, `vibe_leads` returns `source_status: daily_cap` with "resumes at 00:00" — the leads stay reserved and nothing is lost. This is a throttle, not an allowance: do **not** suggest a top-up for it.
- **Each lead is scored once per claim; `irrelevant` verdicts land in the recycle pool (`vibe_rejected`)** — if you later decide one was misjudged (e.g. after opening the post), recover it with `vibe_recover_lead` and re-score.
- **Score what you claim**: claims accumulate as `pending` (up to 50 unscored). A `locked` response with a `pending` list is **normal flow, not an error**: score the pending leads (relevant or irrelevant) and claiming continues. Never leave claimed leads unscored for long.
- **Save every returned field**: persist the full record per lead (id/title/url/subreddit/score, and body when present). `id` is required later for `vibe_get_delivered`; don't keep only titles.
- The candidate `score` is a system reference; your judgment wins

## Working with pending candidates (`locked` is normal)

The scoring question for every candidate is always: **is the author of this post a potential customer of the subscribed product?** Judge on topic (does it sit in the problem area the product solves) and signal strength. Answer `relevant` when yes, `irrelevant` when no (irrelevant still teaches the system; scoring costs nothing).

Note the separation of concerns: **claiming is what costs money, scoring is free**. Claim only what you can actually work with — a claimed-but-ignored lead still counts against the allowance.

Standard loop:
1. `vibe_subscribe(product)` with a **complete description** (name + positioning + target users + website, 40+ chars) → get `subscription_id`. A short description (product name only) is rejected — it would generate generic keywords and low-relevance candidates.
2. `vibe_leads(subscription_id, limit)` → save the **entire returned record** for each lead (including the `billing` block). Don't drop fields.
3. Score the pending leads with `vibe_submit_score` (verdict `relevant` or `irrelevant`). Scoring is free and does not unlock billing — it keeps the feedback loop and the pending queue healthy (the queue pauses at 50 unscored).
4. For leads scored `relevant`, `vibe_get_delivered(lead_id)` returns the full post body for outreach.

## Local script tools (batch executors — call when the action is mechanical)

The host agent is the decision engine (when/what/why). The scripts below are **pure
executors**: each does one mechanical batch action fast (parallel per-item judging) —
far more efficient than hand-writing the loop. Decide when to call one and what to
pass; the script returns structured JSON for the next decision. Scripts do **not**
self-schedule or loop on their own.

**First use**: run with `--dry-run` once to verify key/connectivity before spending
LLM calls (claims candidates only, judges nothing, submits nothing).

### `scripts/score_batch.py` — score one subscription's batch (claim → judge → submit)

| Param | Meaning |
|-------|---------|
| `--sub` | target subscription id (**required** — one sub, one batch) |
| `--limit` | candidates to claim (default 10) |
| `--judge` | path to your judgement template (default `scripts/judge_prompt.md`) |
| `--parallel` | parallel judge lanes (default 8 — this is the efficiency win) |
| `--threshold` | score ≥ threshold → `relevant` (default 60) |
| `--out` | evidence dir (optional; relevant rows → csv/jsonl) |
| `--dry-run` | claim only, no LLM / no submit |

```bash
export VIBEDOLLAR_API_KEY=...        # from vibe_verify / account page
export LLM_API_KEY=...               # your LLM key
export LLM_BASE_URL=https://api.deepseek.com/v1
export LLM_MODEL=deepseek-chat
python3 scripts/score_batch.py --sub 12 --limit 20 --parallel 8 [--out ./evidence]
```

Returns JSON: `{sub_id, claimed, judged, relevant, submitted, failed, pending[]}` —
read it, then decide next (score another sub, expand keywords, wait).

- **Judgment is yours**: edit `scripts/judge_prompt.md` (plain template) to define what a
  good customer looks like for your market. `--threshold` sets the relevant cut.
- **Costs**: a lead is billed when claimed (within the monthly allowance it is $0; beyond it
  $5/1,000 Starter or $3.50/1,000 Pro from wallet). Scoring is free — the judging LLM calls
  are billed to **your** key.
- **Failure-safe**: a candidate whose LLM judgment fails is left pending — retried next
  run, never lost. `vibe_leads` returns `locked` with pending ids until they're scored;
  scoring everything you claimed unlocks the next batch.

### `scripts/mcp.py` — shared MCP client (library, not a CLI)

Import by other local tools: `from mcp import MCPClient`. Not called directly by you.

> **Why scripts, not you writing loops**: batch actions are mechanical (claim N →
> judge each with your LLM → submit). A script parallelises per-item judging and
> returns clean JSON — you stay the decider, the script does the grunt work faster
> than you could by hand-writing the loop each time.

## Setup & tuning prompts (assets — no placeholder replacement, sd is a data doc)

The scoring/judging and keyword-tuning LLM templates live in `scripts/*.md`. They are
**prompt assets**: load the relevant file, call your own LLM with its `sys` content and
a `user` message you build from the subscription's actual data — **the templates carry
no `{placeholders}` and there is no replacement mechanism** (that was the front-end's
JS-string approach; as an agent you read data and compose the user message natively).

**The supply/demand profile is a runtime data document** — not a template variable.
Keep it as `data/sd_<sid>.md` (git-ignored, per-host) so every later step (scoring /
kw_init / kw_opt) reads one file and injects it:

```
# first time / after rebuild — generate sd:
scripts/sd_gen.md        → LLM (product text) → 4 fields
python3 scripts/sd_doc.py write --sub <sid> --json '{...}'   → data/sd_<sid>.md
vibe_sd_update(subscription_id, supply_side=..., demand_side=..., ...)  # backend copy

# any later step — read + inject (agent's native read; no replace):
python3 scripts/sd_doc.py show --sub <sid> --values   → prints only the 4 field values
   (strip self-describing header — safe to drop straight into an LLM user message)
   (or: vibe_list_subs → sd_json — same data, backend is authoritative)
```

| Asset | When to load | Produces → persist via |
|---|---|---|
| `scripts/sd_doc.py` | fetch/show/write the sd doc (`data/sd_<sid>.md`) — mechanical file ops only | decision (generate/update) stays with you |
| `scripts/sd_gen.md` | Subscription has no sd (no supply_side/demand_side/demand_pain) — first setup or after a rebuild | supply/demand four fields → sd_doc.py write + `vibe_sd_update` |
| `scripts/kw_init.md` | Keyword face is empty (initial setup) — needs sd doc present first | initial keyword list → `vibe_keyword_add_batch` (source=auto); dedup vs ALL statuses |
| `scripts/kw_opt.md` | Decision loop says expand / after a retire sweep — needs sd doc + current words (active+monitor rows) | `{add, weak}` → add via `vibe_keyword_add_batch` (dedup vs ALL statuses — don't revive removed words); weak per decision-table guards |
| `scripts/judge_prompt.md` | Default judge template for `score_batch.py` (editable profile, fixed contract) | per-candidate verdicts → `vibe_submit_score` |
| `scripts/eng_sys_core.md` | **READ-ONLY** scoring core (billing-bound contract). Reference verbatim; never edit | reference for judge alignment |

**Order matters**: sd first, then keywords. `sd_gen.md` makes the demand-side profile
(the buyer language) that `kw_init`/`kw_opt` derive words from and that scoring injects
as `[SUPPLY/DEMAND]` — an empty sd means judging/keywords run on product text alone,
which is exactly how generic words and 0-hit sweeps start.

## Subscription mode (continuous monitoring)

```
vibe_subscribe(product="team wiki tool for small teams")
    → {"ok": true, "subscription_id": 12, "message": "tracking started..."}
vibe_list_subs()
    → {"ok": true, "data": {"subscriptions": [{"id": 12, "product": "...", "new_leads": 7}]}}
vibe_leads(subscription_id=12, limit=10)
    → {"ok": true, "data": {"posts": [{"id": 1, "title": "...", "url": "...", "subreddit": "...", "score": 90}], "count": 7},
       "billing": {"claimed_batch": 7, "free_items": 7, "billable_items": 0, "charge_usd": 0.0,
                   "claimed_this_month": 1207, "claimed_quota": 5000, "over_price_per_1k": 5.0,
                   "daily_used": 87, "daily_cap": 1000, "wallet_usd": 0.0}}
vibe_submit_score(scores=[{"id": 1, "verdict": "relevant", "score": 90, "reason": "..."}])
    → {"ok": true, "passed": 1, "quota_used": 1, ...}
```

- For a defined product that needs **continuous** new prospects, not ad-hoc searches
- No keyword/source maintenance by hand: describe the product, we collect + match into the pool; when the face cannot fill the customer's allowance (`assessment.status=shortfall` in `vibe_sub_health`), **you** (your agent) widen the sub list / expand-retire keywords via the health tools — see **Agent decision loop** above
- **A lead is billed when claimed; scoring is free**; the subscription itself costs nothing extra
- **Score what you claim**: claimed leads stay `pending` until scored — after 50 unscored pendings, `vibe_leads` returns `locked` with the pending list (ids recoverable, your subscription is never stuck). Scoring them (relevant **or** irrelevant) resumes claiming. Leads un-scored for 7 days auto-expire.

Cancel with `vibe_unsubscribe` (accumulated leads kept).

## Data use cases (downstream — read on need)

Delivered leads, candidates and keywords are also raw material for **customer
interviews**, **first-100-customer outreach**, and **SEO/GEO content** — full
playbooks in `references/use-cases.md` (zh: `references/use-cases.zh-CN.md`).
Read them when the user asks how to turn leads into conversations/customers/content.

## Agent usage tips

- **Lost API key?** Guide recovery: `vibe_recover_key(email)` → `vibe_recover_verify(email, code)` — or point to https://vibedollar.net/account.html → "Lost your API key? Recover it". No re-registration needed.
- **Watch the `claim_quota` block**: `vibe_balance()` returns `claim_quota {month_used, month_limit, over_price_per_1k, daily_used, daily_cap, wallet_usd}` — proactively tell the user where they stand (allowance used, daily cap, wallet) instead of letting them discover a charge.
- **Registration & payment flow**: `references/billing.md` (agent does the full flow; the only user actions are providing the email/code and scanning a QR / clicking a link).
- **Typical workflow**: `vibe_subscribe` → `vibe_leads` → your agent scores with its own LLM → `vibe_submit_score` → passed leads in delivered list (validate demand + find first customers).

## Pricing, payment & client config (reference)

Pricing tiers, wallet top-up, the full agent payment/activation workflow, and MCP
client connection config live in `references/` — read them only when needed:

- **Pricing & payment**: read `references/billing.md` when the user asks about price,
  upgrading, topping up, or after payment (confirm activation). Quick checks: call
  `vibe_balance()` for the current tier and `claim_quota` usage (month used/limit, daily cap, wallet).
- **MCP client config**: read `references/mcp-config.md` on first connect or when moving
  to another client (endpoint URL, `Authorization: Bearer <key>` header setup).
