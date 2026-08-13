# vibedollar — find your first customers on Reddit

**vibedollar is an MCP skill that brings you the customers who are already complaining about, or asking for, exactly what you build.**

Give it your product description, and vibedollar returns **potential-customer leads**: relevant Reddit posts and comments, each with the author and a *why-it-matches* annotation — click through and reach out. Backed by a **470+ real indie-cases library** so you can see who built it, what they make, and how.

**This service provides data only — no analysis.** All analysis is done by your own LLM (BYOK, bring your own key, zero LLM dependency).

## Quick Start

1. **Connect** (remote-hosted, no local setup): add endpoint `https://mcp.vibedollar.net/mcp` in your MCP client (FastMCP HTTP transport)
2. **Register** (two-step, no credit granted on signup): call `vibe_register(email="you@example.com")` to get a verification code, then `vibe_verify(email, code)` to receive your API key (also emailed to you). Or register directly at `https://vibedollar.net/account.html`
   After registering, unlock usage via Starter/Pro subscription, or top up your wallet with any amount (¥1–¥1000 via WeChat / $1–$200 via Creem, any number of times; plus a **$1 Welcome Credit** for new accounts, once per account) for over-quota Reddit calls.
3. **Configure auth header**: put your key in the client request header — data tools need no `api_key` parameter afterward
4. **Check balance/quota**: `vibe_balance()`

## Tools

| Tool | Params | What it gives you | Cost | Auth |
|------|--------|-------------------|------|------|
| `vibe_register` | `email` | Send 6-digit verification code (step 1 of 2) | Free | — |
| `vibe_verify` | `email, code` | Verify code → receive API key (step 2 of 2) | Free | — |
| `vibe_balance` | — | Tier + quota remaining | Free | Header |
| `vibe_knowledge` | `product_type, limit` | Similar cases / channels / toolchains (470+) | In-tier | Header |
| `vibe_reddit` | `product, keywords, max_results` | **Find customers**: posts + comments with authors, why-it-matches annotations, and a demand-validation report | In-tier / $0.05 per lead after your monthly quota | Header |

All tools except `vibe_register` authenticate via HTTP header `Authorization: Bearer <api_key>` — no key in tool params, no key in call logs.

## Pricing

| Tier | Price | Customer leads (vibe_reddit posts+comments) | Knowledge base | Rate |
|------|-------|---------------------------------------------|----------------|------|
| **Starter** | **$39/mo** | **500/mo** (posts+comments+annotations+report) | Full detail (limit≤20) | 60 req/min |
| **Pro** | **$79/mo** | **3000/mo** (posts+comments+annotations+report) | Full detail (limit≤50) | 120 req/min |
| **Wallet Top-up** | **Any amount** ($1–$200 via Creem / ¥1–¥1000 via WeChat, any number of times) | No subscription needed; wallet credit for vibe_reddit over-quota calls ($0.05 per lead after your monthly quota) | — | — |

- **1 lead = 1 post or 1 comment** (authors are your potential customers — click through to reach them). Usage is clamped to your remaining quota — no overselling.
- **No credit on signup**: register for an API key, then subscribe to Starter/Pro, or top up your wallet with any amount (¥1–¥1000 via WeChat / $1–$200 via Creem, any number of times; plus a **$1 Welcome Credit** for new accounts, once per account) for over-quota Reddit calls at **$0.05 per lead after your monthly quota**.
- **Free accounts have zero quota** (no subscription = no free allowance): every data call is billed from wallet credit ($0.05 per Reddit lead, $0.05 per knowledge/cases call); with no credit you get `Insufficient credit — please top up`.
- **`vibe_knowledge`** is the market validation tool (knowledge base + live search fallback), included in the subscription.
- **Starter/Pro upgrade**: Creem (overseas) or WeChat scan (mcp.vibedollar.net, tier applied automatically after payment); **annual 8折** (coming later); **no trial**.

## Configuration

```json
{
  "mcpServers": {
    "vibedollar": {
      "type": "http",
      "url": "https://mcp.vibedollar.net/mcp",
      "headers": {
        "Authorization": "Bearer vibedollar_你的key"
      }
    }
  }
}
```

> Alternative: if your client can't set `Authorization`, use `Api-Key: <key>` — the server recognizes both.

Register first, then configure the header, then call data tools (all zero LLM dependency, BYOK).

## License

MIT
