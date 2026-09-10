# vibedollar Billing, Payment & Activation（参考 — 低频, 按需加载）

> 何时读本文件：用户问价格 / 需要升级 / 充值 / 支付后确认激活 / key 找回。
> 日常使用 vibedollar 工具不需要读本文件 —— 调 `vibe_balance()` 即可看领取额度用量。

## Pricing

| Tier | Price | **Claimed leads / month** (billed on first claim) | Daily cap | Rate limit |
|------|-------|---------------------------------------------------|-----------|------------|
| **Free** | $0 (sign-up) | **1,000/mo** — use them as fast as you like | 1,000/day | 5 req/min |
| **Starter** | **$19/mo** | **5,000/mo**, then **$5 per 1,000** extra | 1,000/day | 10 req/min |
| **Pro** | **$79/mo** | **30,000/mo**, then **$3.50 per 1,000** extra | 3,000/day | 20 req/min |
| **Wallet top-up** | Any amount (Creem $1–$200 / WeChat ¥1–¥1000) | Covers leads beyond your monthly allowance | — | — |

- **Billing unit = a lead you claim.** A lead (1 post or 1 comment — poster/commenter are both prospects) is billed the **first time you claim it**. Scoring it, re-reading it, or exporting it is **free**.
- **Daily delivery cap**: Free/Starter 1,000 leads/day, Pro 3,000/day. Anything beyond the cap **carries over to the next day — nothing is lost** (delivery slows for that day, it is not billed again).
- **Beyond the monthly allowance**: extra leads deduct **$5 / 1,000** (Starter) or **$3.50 / 1,000** (Pro) from wallet credit. Insufficient wallet → delivery pauses and the leads stay reserved. Free tier has no overage: when the 1,000 is used up, upgrade to continue.
- **Fair use (not billed)**: we cap the amount we pull/match for an account per day (Free 5,000 / Starter 25,000 / Pro 50,000 items). This is invisible in normal use and only prevents extreme configurations; anything over simply spills to the next day.
- **No usage-inducement**: how many subreddits or keywords you track is entirely your call — we do not sell allowance you don't need, and a bigger plan is never required just to "unlock" more.
- **Upgrade (Starter/Pro)**: Creem (global) or WeChat Pay (CN) at `mcp.vibedollar.net`; auto-activation after payment. **Annual 20% off** (coming soon). **No trial**.

## Payment & activation (agent workflow)

**The only user action is scanning a QR / clicking a link**: registration, ordering, generating the QR, confirming activation are all done by the agent.

1. **Confirm/register api_key**: `vibe_balance()` → "Missing API key" means no header configured. If the user has no key: `vibe_register(email=...)` → user gives the emailed 6-digit code → `vibe_verify(email, code)` → api_key. **Do not ask the user to self-register** — the agent does it; the user only provides email and code.
2. **Pick channel by location**:
   | Location | Channel | Price |
   |----------|---------|-------|
   | Global (default) | **Creem** (USD card) | Starter $19/mo / Pro $79/mo / Top-up $1–$200 (Pay What You Want) |
   | Mainland China | **WeChat Pay** (CNY) | Starter ¥99/mo / Pro ¥399/mo / Top-up ¥1–¥1000 |
3. **Generate payment entry**:
   - **Creem (global)**: `POST https://mcp.vibedollar.net/creem/checkout` `{"api_key": "<key>", "plan": "starter|pro|topup", "email": "..."}` → `{"ok": true, "url": "<payment link>"}` → send the url (top-up: user enters $1–$200 on the Creem page). **Never put api_key in URLs**.
   - **WeChat (CN)**: `POST https://mcp.vibedollar.net/pay/native` `{"api_key": "<key>", "email": "...", "tier": "starter|pro|topup"}` → `code_url` → render as QR → user scans (top-up: add `"amount_cents": <CNY×100>`, e.g. ¥36 → 3600).
4. **User pays → confirm activation**: poll `GET https://mcp.vibedollar.net/pay/orders/<out_trade_no>` or re-check `vibe_balance()`: tier/credit auto-updates via WeChat callback / Creem webhook, no manual step.
5. **Tell the user what they get**: e.g. "Starter is live: 5,000 claimed leads this month, 1,000/day, then $5 per 1,000 extra from your wallet."

### What to say about usage
- Read `vibe_balance()` → `claim_quota` block: `month_used / month_limit`, `daily_used / daily_cap`, `wallet_usd`, `over_price_per_1k`.
- Read `vibe_sub_health(subscription_id)` → `assessment` block: whether the current search face can fill the allowance (`projected_items_month` vs `commitment_remaining`), plus `gap_reason` (`supply_ceiling` / `word_face` / `capacity` / `collecting` / `no_data` / `ok`). If supply is the ceiling, adding **subreddits** to the search face helps far more than adding keywords (keywords only re-attribute what is already in the corpus).

### Edge cases
- User already has a key → use it directly, do not re-register
- User prefers web → point them to `https://vibedollar.net/account.html` (equivalent self-service flow)
- Tier not updated after payment → wait 1–2s, re-check `vibe_balance()`; still stale → report `out_trade_no` and contact support@vibedollar.net
- Daily cap reached → tell the user delivery resumes automatically at 00:00 and nothing is lost; do not suggest topping up for a daily cap (it is a throttle, not an allowance)
- Cancel: Starter/Pro downgrade at expiry (no hard cut), no agent action
