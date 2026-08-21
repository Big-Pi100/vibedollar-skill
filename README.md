# vibedollar — find your first customers on Reddit

> **The customers you're looking for are already complaining and asking for solutions on Reddit. vibedollar brings them to you.**

Give vibedollar your product description and it continuously monitors Reddit for **potential-customer leads** (posts + comments, with author, full text, and why-it-matches annotations). Your agent scores each candidate with **your own LLM** — you only pay for leads you score as `relevant` (pay-per-outcome).

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
| Ongoing acquisition | `vibe_subscribe` → `vibe_leads` (free) → score → paid on `relevant` |
| Proof for investors/team | Accumulated leads (that you scored) are ready-made demand validation |

**Business model: pay-per-outcome.** Candidates are free. You (or your agent) judge relevance. Only `relevant` scores count (1 lead = 1 quota). Not scored → not billed.

---

## MCP tools

| Tool | What it does | Cost |
|------|-------------|------|
| `vibe_register` / `vibe_verify` | Two-step signup → API key (email code → key) | Free |
| `vibe_balance` | Check balance / tier / quota remaining | Free |
| `vibe_subscribe` | Subscribe a product (describe it; background tracking starts) | Free |
| `vibe_leads` | Claim candidate leads (author / body / system reference score) | **Free** |
| `vibe_submit_score` | Score candidates: `relevant` = 1 quota + delivered; `irrelevant` = feedback for tuning | **Billed only on pass** |
| `vibe_score_discuss` | View/respond to disagreements with system reference score (calibration) | Free |
| `vibe_list_subs` / `vibe_unsubscribe` | Subscription management | Free |
| `vibe_delivered` / `vibe_get_delivered` | Delivered leads (follow-up) | Free |
| `vibe_mark_leads` | Mark lead outcome (valid / invalid / contacted) | Free |

**Billing**: candidates are **free**; `vibe_submit_score` with `relevant` costs 1 quota per lead and moves it to your delivered list; `irrelevant` is free (feeds back to make future pushes more accurate). Score the whole batch before claiming the next one. New users get a **$1 Welcome Credit** (once per person).

---

## Quick start

1. **Connect** (remote-hosted, no local setup): add endpoint `https://mcp.vibedollar.net/mcp` to your MCP client (FastMCP HTTP transport).
2. **Register** (two-step):
   ```
   vibe_register(email="you@example.com")     # sends a 6-digit code
   vibe_verify(email="you@example.com", code="123456")   # returns api_key
   ```
   Your API key is also emailed to you. Pay to unlock: subscribe Starter/Pro, or top up the wallet (WeChat ¥1–¥1000 / Creem $1–$200). New users get a **$1 Welcome Credit**.
3. **Configure auth**: put the key in your MCP client request header — `Authorization: Bearer <key>` (or `Api-Key: <key>` if your client disallows custom Authorization headers).
4. **Check balance/quota**: `vibe_balance()` (key read from header automatically).
5. **Web self-service** also available: `https://vibedollar.net/account.html` (register / verify / pay).

---

## Recommended workflow

```
vibe_subscribe(product="team wiki tool for small teams")
    → {"ok": true, "subscription_id": 12, "message": "tracking started..."}
vibe_list_subs()                          # check status + pending count
vibe_leads(subscription_id=12, limit=10)  # free candidates
    → {"id": 1, "title": "...", "url": "...", "score": 90, "reason": "...", ...}
vibe_submit_score(scores=[
    {"id": 1, "verdict": "relevant",   "score": 90, "reason": "directly asking for a solution"},
    {"id": 2, "verdict": "irrelevant", "score": 10, "reason": "unrelated"},
])
    → {"ok": true, "passed": 1, "rejected": 1, "quota_used": 1, "quota_limit": 3000}
```

Rules:
- Candidates are **free** (`vibe_leads` costs nothing)
- **Pay only on pass**: `verdict="relevant"` → 1 quota, added to delivered list (`vibe_delivered`)
- **Please also return `irrelevant`** — that's how the system learns your judgment standard
- Each candidate can be scored only once (re-scoring is rejected)
- The `score` field is a system reference score — your judgment wins
- **Finish the current batch before claiming the next**; unprocessed candidates come back with ids (never lock your subscription); candidates older than 7 days auto-expire

---

## Pricing

| Tier | Price | **Delivered leads** (scored relevant) | Rate limit |
|------|-------|----------------------------------------|------------|
| **Free** | Sign-up | **30/mo** (demo: 1 subscription, 20 per claim; overage $0.05/lead from wallet) | 30 req/min |
| **Starter** | **$39/mo** | **800/mo** (paid on pass; candidates free; score the batch to unlock the next) | 60 req/min |
| **Pro** | **$79/mo** | **3000/mo** (paid on pass; candidates free; score the batch to unlock the next) | 120 req/min |
| **Wallet top-up** | Any amount (Creem $1–$200 / WeChat ¥1–¥1000) | Extends quota at **$0.05/lead** after the tier quota runs out | — |

- **"Lead" = one scored-relevant item**: 1 post or 1 comment = 1 lead (both author and commenter are prospects). Candidates free; only `relevant` consumes quota; no oversell.
- **After quota**: paid leads auto-deduct $0.05 from wallet (insufficient balance → prompt to top up); Free tier has 30/mo then wallet.
- **Sign-up gives no quota**: register for the API key, then subscribe Starter/Pro or top up the wallet. $1 Welcome Credit for new users (once).
- **Upgrade**: Creem (global) or WeChat Pay (CN) at `mcp.vibedollar.net` — auto-activation after payment. **Annual 20% off** (coming soon). **No trial**.

---

## Payment & activation (agent workflow)

The only user action is **scanning a QR code / clicking a link**. You (the agent) do the rest:

1. **Confirm/register api_key**: `vibe_balance()` → if "Missing API key", register via `vibe_register` → user gives you the emailed 6-digit code → `vibe_verify`. Don't ask the user to self-register.
2. **Pick channel by user location**:
   | Location | Channel | Price |
   |----------|---------|-------|
   | Global (default) | **Creem** (USD card) | Starter $39/mo / Pro $79/mo / Welcome Credit $1 / Top-up $1–$200 |
   | Mainland China | **WeChat Pay** (CNY) | Starter ¥280.8/mo / Pro ¥568.8/mo / Welcome Credit ¥0.01 / Top-up ¥1–¥1000 |
3. **Generate payment entry**:
   - **Creem**: `POST https://mcp.vibedollar.net/creem/checkout` `{"api_key": "<key>", "plan": "starter|pro|welcome_credit|topup", "email": "..."}` → `{"url": "<payment link>"}` → send the url. **Never put api_key in URLs**.
   - **WeChat**: `POST https://mcp.vibedollar.net/pay/native` `{"api_key": "<key>", "email": "...", "tier": "starter|pro|welcome_credit|topup"}` → `code_url` → render as QR → user scans. For top-up add `"amount_cents": <CNY×100>`.
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

## Status (2026-08-21)

- **v3.1 user-scoring mode**: candidates free → your agent scores → `relevant` billed (pay-per-outcome)
- **Background pipeline**: continuous Reddit monitoring per subscription, candidates accumulate automatically
- **Feedback loop**: your scores (including irrelevant) tune future pushes; disagreements viewable for calibration
- **Abuse protection**: batch unlocking + claim validation + consistency guardrails
