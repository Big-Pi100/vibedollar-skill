# vibedollar Billing, Payment & Activation（参考 — 低频, 按需加载）

> 何时读本文件：用户问价格 / 需要升级 / 充值 / 支付后确认激活 / key 找回。
> 日常使用 vibedollar 工具不需要读本文件 —— 调 `vibe_balance()` 即可看配额。

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

**The only user action is scanning a QR / clicking a link**: registration, ordering, generating the QR, confirming activation are all done by the agent.

1. **Confirm/register api_key**: `vibe_balance()` → "Missing API key" means no header configured. If the user has no key: `vibe_register(email=...)` → user gives the emailed 6-digit code → `vibe_verify(email, code)` → api_key. **Do not ask the user to self-register** — the agent does it; the user only provides email and code.
2. **Pick channel by location**:
   | Location | Channel | Price |
   |----------|---------|-------|
   | Global (default) | **Creem** (USD card) | Starter $39/mo / Pro $79/mo / Top-up $1–$200 (Pay What You Want) |
   | Mainland China | **WeChat Pay** (CNY) | Starter ¥280.8/mo / Pro ¥568.8/mo / Top-up ¥1–¥1000 |
3. **Generate payment entry**:
   - **Creem (global)**: `POST https://mcp.vibedollar.net/creem/checkout` `{"api_key": "<key>", "plan": "starter|pro|topup", "email": "..."}` → `{"ok": true, "url": "<payment link>"}` → send the url (top-up: user enters $1–$200 on the Creem page). **Never put api_key in URLs**.
   - **WeChat (CN)**: `POST https://mcp.vibedollar.net/pay/native` `{"api_key": "<key>", "email": "...", "tier": "starter|pro|topup"}` → `code_url` → render as QR → user scans (top-up: add `"amount_cents": <CNY×100>`, e.g. ¥36 → 3600).
4. **User pays → confirm activation**: poll `GET https://mcp.vibedollar.net/pay/orders/<out_trade_no>` or re-check `vibe_balance()`: tier/credit auto-updates via WeChat callback / Creem webhook, no manual step.

### Edge cases
- User already has a key → use it directly, do not re-register
- User prefers web → point them to `https://vibedollar.net/account.html` (equivalent self-service flow)
- Tier not updated after payment → wait 1–2s, re-check `vibe_balance()`; still stale → report `out_trade_no` and contact support@vibedollar.net
- Cancel: Starter/Pro downgrade at expiry (no hard cut), no agent action
