# vibedollar — find your first customers on Reddit

> **The customers you're looking for are already complaining and asking for solutions on Reddit. vibedollar brings them to you.**

Give vibedollar your product description and it continuously monitors Reddit for **potential-customer leads** (posts + comments, with author, full text, and why-it-matches annotations). A lead is billed when **you claim it**; scoring it with your own LLM is free.

1. **MCP service** (`mcp.vibedollar.net`) — Register, subscribe a product, candidates accumulate in the background, your agent scores and claims them. Zero setup (just a product description).
2. **SKILL** — makes vibedollar part of your agent's muscle memory.

- [中文版 README](README.zh-CN.md)
- [SKILL (English)](SKILL.md) · [SKILL (中文)](SKILL.zh-CN.md)

---

## What it does for you

| Use case | How |
|----------|-----|
| Cold-start acquisition | `vibe_subscribe` → system tracks continuously, leads accumulate, open the post and reach the prospect |
| Validate a product idea | Subscribe, then look at accumulated leads: N strong-demand signals → build it |
| Ongoing acquisition | `vibe_subscribe` → `vibe_leads` (billed on claim) → score → reach out |
| Proof for investors/team | Accumulated leads (that you claimed) are ready-made demand validation |

**Business model: pay for the leads you claim.** A lead is billed the first time you claim it; scoring, re-reading and exporting are free. The server meters claims, so nothing is self-reported and nothing is billed twice.

---

## MCP tools

| Tool | What it does | Cost |
|------|-------------|------|
| `vibe_register` / `vibe_verify` | Two-step signup → API key (email code → key) | Free |
| `vibe_balance` | Check balance / tier / monthly claim allowance and daily cap | Free |
| `vibe_subscribe` | Subscribe a product (describe it; background tracking starts) | Free |
| `vibe_leads` | Claim leads (author / body / system reference score) | **Billed per lead claimed** |
| `vibe_submit_score` | Score claimed leads with your own judgment: `relevant` → delivered list; `irrelevant` → feedback for tuning | **Free** |
| `vibe_score_discuss` | View/respond to disagreements with system reference score (calibration) | Free |
| `vibe_list_subs` / `vibe_unsubscribe` | Subscription management | Free |
| `vibe_delivered` / `vibe_get_delivered` | Delivered leads (follow-up) | Free |
| `vibe_mark_leads` | Mark lead outcome (valid / invalid / contacted) | Free |
| `vibe_recover_key` / `vibe_recover_verify` | Lost your API key? Recover it via email verification | Free |

**Billing**: a lead is billed when you **first claim it** (Free 1,000/mo · Starter 5,000/mo then $5 per 1,000 · Pro 30,000/mo then $3.50 per 1,000). Scoring, re-reading and exporting are free. Daily delivery caps (Free/Starter 1,000, Pro 3,000) carry over to the next day.

---

## Quick start

1. **Connect** (remote-hosted, no local setup): add endpoint `https://mcp.vibedollar.net/mcp` to your MCP client (FastMCP HTTP transport).
2. **Register** (two-step):
   ```
   vibe_register(email="you@example.com")     # sends a 6-digit code
   vibe_verify(email="you@example.com", code="123456")   # returns api_key
   ```
   Your API key is also emailed to you. Unlock lead allowance: subscribe Starter/Pro, or top up the wallet (WeChat ¥1–¥1000 / Creem $1–$200). Free tier already includes 1,000 claimed leads/month.
3. **Configure auth**: put the key in your MCP client request header — `Authorization: Bearer <key>` (or `Api-Key: <key>` if your client disallows custom Authorization headers).
4. **Check balance/allowance**: `vibe_balance()` (key read from header automatically).
5. **Web self-service** also available: `https://vibedollar.net/account.html` (register / verify / pay).

---

## Recommended workflow

```
vibe_subscribe(product="team wiki tool for small teams")
    → {"ok": true, "subscription_id": 12, "message": "tracking started..."}
vibe_list_subs()                          # check status + pending count
vibe_leads(subscription_id=12, limit=10)  # claims 10 leads (billed per lead)
    → {"id": 1, "title": "...", "url": "...", "score": 90, "reason": "...", ...,
       "billing": {"claimed_batch": 10, "free_items": 10, "currency": "usd", "charge": 0.0, "charge_usd": 0.0,
                   "claimed_this_month": 10, "claimed_quota": 5000,
                   "daily_used": 10, "daily_cap": 1000}}
vibe_submit_score(scores=[
    {"id": 1, "verdict": "relevant",   "score": 90, "reason": "directly asking for a solution"},
    {"id": 2, "verdict": "irrelevant", "score": 10, "reason": "unrelated"},
])
    → {"ok": true, "passed": 1, "rejected": 1, "quota_used": 1, "quota_limit": 3000}  # scoring is free
```

Rules:
- **A lead is billed when you claim it** (`vibe_leads` returns a `billing` block: batch, free/billable split, charge, month usage, daily cap)
- **Scoring is free**: `verdict="relevant"` moves the lead to your delivered list (`vibe_delivered`); `irrelevant` feeds back to sharpen matching
- **Please also return `irrelevant`** — that's how the system learns your judgment standard
- Each lead can be scored only once (re-scoring is rejected)
- The `score` field is a system reference score — your judgment wins
- **Daily cap**: Free/Starter 1,000, Pro 3,000 claimed leads/day; beyond the cap delivery resumes automatically next day (nothing lost)
- Unprocessed claimed leads come back with ids (never lock your subscription); leads older than 7 days auto-expire
- **Someone else may be judging in parallel**: the web app (https://vibedollar.net/app.html → **To score**) claims and judges on the same tools and the same gate — manual verdicts arrive as `score: 60` (relevant) / `1` (irrelevant), **whoever claims first judges**, and a lead already judged there is rejected as already-scored, so skip that id instead of retrying. The pending queue (50 unscored) is shared between your agent and the web app: either end scoring it unlocks the next batch.

---

## Pricing

| Tier | Price | **Claimed leads / month** (billed on first claim) | Daily cap | Rate limit |
|------|-------|---------------------------------------------------|-----------|------------|
| **Free** | $0 (sign-up) | **1,000/mo** — use them as fast as you like | 1,000/day | 5 req/min |
| **Starter** | **$19/mo** | **5,000/mo**, then **$5 per 1,000** extra | 1,000/day | 10 req/min |
| **Pro** | **$79/mo** | **30,000/mo**, then **$3.50 per 1,000** extra | 3,000/day | 20 req/min |
| **Wallet top-up** | Any amount (Creem $1–$200 / WeChat ¥1–¥1000) | Covers leads beyond your monthly allowance | — | — |

- **Billing unit = a lead you claim**: 1 post or 1 comment = 1 lead (both author and commenter are prospects), billed the **first time you claim it**. **Scoring, re-reading and exporting are free** — the server meters claims, so there is nothing to self-report.
- **Daily delivery cap**: Free/Starter 1,000 leads/day, Pro 3,000/day. Anything beyond the cap **carries over to the next day — nothing is lost** and nothing is billed twice.
- **Beyond the monthly allowance**: extra leads deduct **$5/1,000** (Starter) or **$3.50/1,000** (Pro) from wallet credit; insufficient wallet pauses delivery and the leads stay reserved. Free has no overage — upgrade when the 1,000 is used up.
- **Sign-up gives 1,000 free leads/month** (1,000/day) — enough to run the full subscribe → claim → score → deliver loop.
- **No usage-inducement**: how many subreddits or keywords you track is your call; a bigger plan is never needed just to unlock more.
- **Upgrade**: Creem (global) or WeChat Pay (CN) at `mcp.vibedollar.net` — auto-activation after payment. **Annual 20% off** (coming soon). **No trial**.

---

## Payment & activation (agent workflow)

The only user action is **scanning a QR code / clicking a link**. You (the agent) do the rest:

1. **Confirm/register api_key**: `vibe_balance()` → if "Missing API key", register via `vibe_register` → user gives you the emailed 6-digit code → `vibe_verify`. Don't ask the user to self-register.
2. **Pick channel by user location**:
   | Location | Channel | Price |
   |----------|---------|-------|
   | Global (default) | **Creem** (USD card) | Starter $19/mo / Pro $79/mo / Top-up $1–$200 |
   | Mainland China | **WeChat Pay** (CNY) | Starter ¥99/mo / Pro ¥399/mo / Top-up ¥1–¥1000 |
3. **Generate payment entry**:
   - **Creem**: `POST https://mcp.vibedollar.net/creem/checkout` `{"api_key": "<key>", "plan": "starter|pro|topup", "email": "..."}` → `{"url": "<payment link>"}` → send the url. **Never put api_key in URLs**.
   - **WeChat**: `POST https://mcp.vibedollar.net/pay/native` `{"api_key": "<key>", "email": "...", "tier": "starter|pro|topup"}` → `code_url` → render as QR → user scans. For top-up add `"amount_cents": <CNY×100>`.
4. **Confirm activation**: poll `GET https://mcp.vibedollar.net/pay/orders/<out_trade_no>` or re-check `vibe_balance()` — tier/credit auto-updates via webhook/callback.

Troubleshooting:
- User already has a key → use it directly, don't re-register
- User prefers web → point them to `https://vibedollar.net/account.html` (equivalent flow)
- Tier not updated after payment → wait 1–2s and re-check `vibe_balance()`; if still stale, report `out_trade_no` and contact support@vibedollar.net
- Cancel: Starter/Pro downgrade at expiry (no hard cut), no agent action needed

---

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

Some clients (Claude Desktop / Cursor) also support headers via env/config — set `Authorization: Bearer <key>` on the server's headers per your client's docs. Alternative header: `Api-Key: <key>`.

Connect → `vibe_register` → put the key in the header → call data tools. We handle lead discovery and optimization; you handle judgment.

---

## Status (2026-09-05)

- **Claim-based billing (2026-09-10)**: a lead is billed when **first claimed**; scoring, re-reading and exporting are free (server-metered, nothing self-reported)
- **Data-service architecture**: server = pure data/state layer (collection + matching + SQL state); judging & keyword tuning are yours (your LLM)
- **2026-09-05 tools expansion**: 9 management tools added — keywords/keyword_add/keyword_remove (word management), sd_update (judgement scope), sub_health/opt_log (delivery-health-driven tuning), rejected/recover_lead (recycle), subs (source stats)
- **2026-09-06 keyword_add_batch**: `vibe_keyword_add_batch` adds N keywords in one call (same per-word semantics as keyword_add) — use it for init/expand lists instead of looping, to stay inside the per-account rate window
- **Delivery-health loop**: read `vibe_sub_health` → expand/retire keywords on commitment gap → record with `vibe_opt_log` (replaces old "system auto-tunes")
- **Recycle flow**: `irrelevant` lands in `vibe_rejected`; recover & re-score with `vibe_recover_lead` (no double billing)
- **Abuse protection**: batch unlocking + claim validation + consistency guardrails
