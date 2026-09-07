# vibedollar — Data use cases (reference — downstream, load on need)

> When to read this file: the user asks how to turn delivered leads / keywords /
> candidates into actual customers, interviews, or content. Day-to-day scoring and
> keyword tuning do not need this file — see SKILL.md for the operation loop.

Subscription data = **real people expressing real needs in their own words**
(who + where + how they say it). Beyond the lead list itself, the data feeds three
proven downstream uses — no extra service, no interface changes:

## ① Customer interviews (understand the customer, pre-PMF)

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

## ② First 100 customers (cold start, from discovery to outreach)

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

## ③ SEO/GEO content data (content strategy, from keywords to user language)

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
