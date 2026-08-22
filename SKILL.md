---
name: vibedollar
description: >-
  vibedollar helps indie founders find their first customers — describe your product and it
  continuously monitors Reddit for potential-customer leads (posts + comments), with subscription
  tracking. Your agent judges relevance with its own LLM; you pay only for leads scored relevant
  (pay-per-outcome). Remote-hosted, zero setup. Paid plans: Starter $39/mo, Pro $79/mo; wallet
  top-up (WeChat / Creem) also available.
---

# vibedollar — find your first customers on Reddit

**The customers you want are already complaining and asking for solutions on Reddit. vibedollar brings them to you.**

You've built your product, but the posts and comments where people are actively solving the problem you solve are impossible to find with regular search. Describe your product, and vibedollar continuously collects **potential-customer leads** (candidate posts and comments, with author and full text) — **your agent scores them with your own LLM**, and scored-relevant ones go to your delivered list, clickable for outreach.

**We handle lead discovery and continuous tuning** (search direction and data sources adjust automatically), **you decide what a good customer looks like** (your agent scores with your LLM) — each side does what it's best at, and pushes get more accurate over time.

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
   > Unlock by: subscribe Starter/Pro, or top up the wallet (WeChat ¥1–¥1000 / Creem $1–$200); **$1 Welcome Credit** for new users (once per person).
3. **Configure auth header**: `Authorization: Bearer <key>` (or `Api-Key: <key>` if your client disallows custom Authorization). After that, data tools don't need `api_key` as a parameter.
4. **Check balance/quota**: `vibe_balance()` (key read from header).
5. **Web self-service** also available: `https://vibedollar.net/account.html` (register/verify/pay).

## Tools

| Tool | Params | What it does | Cost | Auth |
|------|--------|-------------|------|------|
| `vibe_register` | `email` | Step 1: send 6-digit verification code | Free | None |
| `vibe_verify` | `email, code` | Step 2: verify code, return api_key (also emailed) | Free | None |
| `vibe_balance` | — | Balance / tier / quota remaining (key via header) | Free | Header |
| `vibe_subscribe` | `product`, `enable_competitor_kw`(optional) | **Continuous monitoring**: describe your product, system tracks and accumulates candidates (search direction managed for you). `enable_competitor_kw` (default on): set `false` for direct-demand leads only, excluding competitor-comparison posts | Free (candidates free) | Header |
| `vibe_leads` | `subscription_id, limit` | **Claim candidates (free)**: posts/comments with system reference score, each with a **source type** (direct demand / competitor comparison / comment, filterable via `kw_type`; excludes competitor-comparison when disabled). Billed only on pass. **Per-claim cap: free 20 / Starter 30 / Pro 50** (returns min(limit, tier cap)) | **Free** | Header |
| `vibe_submit_score` | `scores` | **Score candidates**: `relevant` = 1 delivered (1 quota), `irrelevant` = feedback for tuning | Billed on pass | Header |
| `vibe_score_discuss` | `limit, respond_id, response` | **Calibration (optional)**: view/respond to disagreements with the system reference score — we tune the standard to match your judgment | Free | Header |
| `vibe_set_notify` | `enabled` | Email alerts on candidate backlog (default on) | Free | Header |
| `vibe_list_subs` | — | Your subscriptions + candidate accumulation status | Free | Header |
| `vibe_unsubscribe` | `subscription_id` | Cancel subscription (accumulated leads kept) | Free | Header |
| `vibe_mark_leads` | `lead_ids, outcome` | Mark lead outcome (valid / invalid / contacted) — track outreach quality | Free | Header |
| `vibe_get_delivered` | `lead_id` | Single delivered lead detail (follow-up) | Free | Header |
| `vibe_delivered` | `limit, offset` | Delivered leads list (follow-up history) | Free | Header |
| `vibe_recover_key` | `email` | **Lost your API key?** Step 1: send a verification code to a registered email (no auth) | Free | None |
| `vibe_recover_verify` | `email, code` | Step 2: verify the code, your API key is emailed to you (no auth) | Free | None |

> All tools except `vibe_register` authenticate via the HTTP header `Authorization: Bearer <api_key>` — **the key never appears in tool params or call logs**.

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
- **Also return `irrelevant`**: that's how the system learns your standard; the more you return, the more accurate pushes get
- Each candidate can be scored only once (repeat submission rejected)
- The candidate `score` is a system reference — your judgment wins

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
- No keyword/source maintenance — describe the product, we manage the search direction
- **Paid on pass only** (pay-per-outcome); subscription itself is free
- **Score the batch to unlock the next**: claimed candidates must all be scored (relevant or not) before the next claim; claiming early returns the pending list with ids (ids recoverable — never locks your subscription). Candidates un-scored for 7 days auto-expire.

Cancel with `vibe_unsubscribe` (accumulated leads kept).

## Agent usage tips

- **User lost their API key?** Guide them through recovery — no re-registration needed:/n  ```
  vibe_recover_key(email=...)          # sends a verification code to their registered email
  vibe_recover_verify(email=..., code=...)  # verifies → API key is emailed to them
  ```
  (Or point them to https://vibedollar.net/account.html → "Lost your API key? Recover it")
- **Register first, then configure the header**: key goes in `Authorization: Bearer <key>`. Missing header → `"Missing API key"`; unregistered key → `"Unknown API key"`.
- **Self-manage via the `quota` block**: each response carries `quota: {scope, used, limit}` (e.g. `{"scope": "3000/mo", "used": 5, "limit": 3000}` = 5/3000 used). Proactively suggest an upgrade (Starter/Pro) before exhaustion.
- **`vibe_leads` returns candidates (posts + comments, free)**: id / title / url / body — your agent reads and judges, then returns scores via `vibe_submit_score`.
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

- **"Lead" = one scored-relevant item**: 1 post or 1 comment = 1 lead (poster/commenter are both prospects). Candidates free; `relevant` consumes 1 quota; auto-limited when insufficient — no oversell.
- **After quota**: paid leads auto-deduct $0.05 from wallet (prompt top-up when low); Free tier 30/mo then wallet.
- **No free quota at signup**: register for the key, then subscribe Starter/Pro or top up. $1 Welcome Credit for new users (once).
- **Upgrade (Starter/Pro)**: Creem (global) or WeChat Pay (CN) at `mcp.vibedollar.net` — auto-activation after payment. **Annual 20% off** (coming soon). **No trial**.

## Payment & activation (agent workflow)

**The only user action is scanning a QR / clicking a link** — registration, ordering, generating the QR, confirming activation are all done by you (the agent).

1. **Confirm/register api_key**: `vibe_balance()` → "Missing API key" means no header configured. If the user has no key: `vibe_register(email=...)` → user gives you the emailed 6-digit code → `vibe_verify(email, code)` → api_key. **Don't ask the user to self-register** — that's your job; the user only provides email and code.
2. **Pick channel by location**:
   | Location | Channel | Price |
   |----------|---------|-------|
   | Global (default) | **Creem** (USD card) | Starter $39/mo / Pro $79/mo / Welcome Credit $1.00 / Top-up $1–$200 (Pay What You Want) |
   | Mainland China | **WeChat Pay** (CNY) | Starter ¥280.8/mo / Pro ¥568.8/mo / Welcome Credit ¥0.01 / Top-up ¥1–¥1000 |
3. **Generate payment entry**:
   - **Creem (global)**: `POST https://mcp.vibedollar.net/creem/checkout` `{"api_key": "<key>", "plan": "starter|pro|welcome_credit|topup", "email": "..."}` → `{"ok": true, "url": "<payment link>"}` → send the url (top-up: user enters $1–$200 on the Creem page). **Never put api_key in URLs**.
   - **WeChat (CN)**: `POST https://mcp.vibedollar.net/pay/native` `{"api_key": "<key>", "email": "...", "tier": "starter|pro|welcome_credit|topup"}` → `code_url` → render as QR → user scans (top-up: add `"amount_cents": <CNY×100>`, e.g. ¥36 → 3600).
4. **User pays → confirm activation**: poll `GET https://mcp.vibedollar.net/pay/orders/<out_trade_no>` or re-check `vibe_balance()` — tier/credit auto-updates via WeChat callback / Creem webhook, no manual step.

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

Some clients (Claude Desktop / Cursor) allow headers via env/config — set `Authorization: Bearer <key>` on the server headers per their docs. Alternative header: `Api-Key: <key>`.

Connect → `vibe_register` → configure the key in the header → call data tools (lead discovery and search-direction tuning are ours; judgment is yours).
