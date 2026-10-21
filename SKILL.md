---
name: vibedollar
description: "vibedollar helps indie founders find their first customers. Describe your product and it continuously monitors Reddit for potential-customer leads (posts and comments). A lead is billed when you claim it; scoring it with your own LLM is free. Remote-hosted, zero setup. Free 1,000 leads/mo; Starter $19/mo (5,000); Pro $79/mo (30,000); wallet top-up available."
---

# vibedollar | find your first customers on Reddit

vibedollar monitors Reddit for posts and comments where people are actively seeking
the kind of product the user builds, and surfaces them as scored **potential-customer
leads**. Division of labor: vibedollar runs the data service (Reddit collection,
candidate matching into a raw pool, and the state layer, keywords / supply-demand
scope / recycle / health); **the host agent decides what a good customer looks like**:
it scores candidates with its own LLM key and drives tuning (see **Delivery-health
tuning** and **Supply-side decisions** below).

> **Data source**: leads are records of **publicly visible posts at collection time**.
> Posts may later be removed by the platform or the author, but the historical record
> remains a valid demand signal; the author is a real person still reachable via
> Reddit DMs or their public contact info. Use leads in line with Reddit's platform
> terms and applicable laws.

**What the data is good for**: full playbooks (interviews / first 100 customers /
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
| Ongoing acquisition | `vibe_subscribe` → `vibe_leads` (billed on first claim) → score (free) → relevant leads land in the delivered list |
| Proof for investors/team | Accumulated leads (that you scored) are ready-made demand validation |

## Quick start

1. **Connect** (remote-hosted, no local setup): add endpoint `https://mcp.vibedollar.net/mcp` to your MCP client (FastMCP HTTP transport).
2. **Register (first time only)**: `vibe_register(email)` sends a 6-digit code; `vibe_register(email, code)` returns the api_key (also emailed). The free tier already includes 1,000 claimed leads/month (1,000/day); purchase Starter/Pro or top up the wallet for more. Full registration, unlock, payment and activation flow: `references/billing.md`.
3. **Configure auth header**: `Authorization: Bearer <key>` (or `Api-Key: <key>` if your client disallows custom Authorization). After that, data tools don't need `api_key` as a parameter.
4. **Check balance/allowance**: `vibe_balance()` (key read from header): returns the `claim_quota` usage block.
5. **Web self-service** also available: `https://vibedollar.net/account.html` (register/verify/pay).

## Main pipeline (one flow: every response tells you the next call)

The server is the **state layer**: every response carries a `progress` block = **current
stage + how complete it is + the next tool**. Just follow `progress.next.do`, you don't
have to reconstruct "where am I in the loop" yourself.

```
0 · STARTUP (once, and after any rebuild) — set the search face FIRST, then the word list
  sd_gen.md → vibe_subscribe            four sd fields — demand_side (audience profile) and
                                        demand_pain (buyer language) come from DIFFERENT sources
  → vibe_catalog  find subs; anchor words come ONLY from demand_side
                                        (the server extracts nothing for you — no candidate words)
  → vibe_subscribe(update_sublist=subs, sublist_mode=mode)    the search face = this explicit sub list (server queues pulls)
  → kw_init.md (derive from sd)  /  kw_mine.md (sweep a precision audience sub's own corpus)
  → vibe_keyword_edit(source=auto)
  ⚠️ missing sd or an empty sub list = every round returns at the gate and NOTHING is produced

1 · RUN (per round — driven by progress.next.do)
  ⚠️ **Check ALL FOUR actions every round — this is a loop, not a pipeline** (2026-09-24 fix: the flow
     used to read "intake … → move to outreach", and the measured result was 655 delivered leads with
     only 166 drafts — agents looped inside intake and treated drafting as "later"):
  ├─ progress.todo.supply.gate == true     → vibe_keywords (fix words/scope first, stop claiming noise)
  ├─ progress.todo.to_score > 0            → vibe_score (return what you hold first)
  ├─ to_score == 0 and claimable_now > 0   → vibe_leads (claim another batch, back to judging)
  ├─ **drafts_missing > 0**                → vibe_outreach(delivered_id=progress.next.args.delivered_id)
  │   (outreach drafting — in the SAME round as intake): read the brief, write ≤18 words with
  │   **your own LLM**, then send it back with `draft=` on the **same tool**. If
  │   `draft_check.failed_detail` complains, revise and resubmit. How many per round is bounded by the
  │   **write bucket** and the **cold-account throttle** (cold: ≤2/day, ≤1 per sub/day, ≥30 min apart).
  │   Submit each draft as soon as it is written — do not batch them up.
  └─ all of the above == 0                  → round done
  🔁 CADENCE (2026-09-22 / 2026-09-24): intake and outreach BOTH move every round;
     while gap_reason=shortfall, one batch every 30–60 min, once a day in steady state —
     see "Loop cadence" below.
after sending (writing the draft is only step one)
  ├─ drafts done but sent == 0 → post the draft first; after posting call vibe_outreach(what="log", action="sent", lead_id=…)
│  ⚠️ 2026-09-23: declaring is not sending. Once the copy is handed to the user, call
│     vibe_outreach(what="log", action="declare", delivered_id=…) once (no network) so the lead leaves "to do" for
│     "awaiting confirmation"; "sent" still requires the server to find your comment in the thread.
  │                             (the server finds your comment, marks it contacted, starts the
  │                              re-check clock; or do nothing — discovery runs every 6h by username)
  ├─ unmarked_delivered > 0 and sent > 0 → vibe_leads(mark=[{"lead_id":…, "outcome":"valid|invalid|contacted"}])
  └─ both are 0                → back to intake / review

2 · OPTIMIZE (goal-driven outer loop — runs BETWEEN rounds; details in "Agent decision loop")
  goal check first: vibe_sub_health.assessment → projected_items_month vs commitment_remaining
    ├─ committed_ok → wait (the fast loop is absorbing it; no supply action)
    └─ shortfall    → pick ONE action by gap_reason:
        supply_ceiling → widen / refresh the sub list
                         (vibe_catalog → vibe_subscribe)
        word_face      → retire a noise word (vibe_keyword_edit force) or REGENERATE the word face
                         (sd_gen → kw_init / kw_opt / kw_mine → vibe_keyword_edit)
        capacity       → nothing to do on supply (that is the daily cap)
        collecting     → alert (collection stalled — widening words is useless)
  act → write your `expect` → verify next round → back to the goal check
  Only "exhausted" (judge → retire → widen list → regenerate → report) may stop it; silent stop is forbidden.
```

**A stage only completes when that stage's `stage_done=true`** (intake = 0 to score **and**
0 claimable). As long as you can still claim, you are still in the claim→judge→return inner
loop: do not skip judging and go write drafts.

**Two things must hit zero before you call it done (measured 2026-09-21; do not repeat it)**:
- `vibe_leads(peek=true)` → `data.pending[]` / `data.unjudged_total` (`pending_count_agent`
  shares the `to_score` scope) is the **authoritative list of what you still owe**. Finishing
  means reading it to 0 **and** seeing `progress.stage_done=true`. `drain.unclaimed_total=0`
  alone only means nothing is left unclaimed: that is **not** the finish line.
- ⚠️ `vibe_score` `errors[]` is **per-item**: a receipt with `id=A, code=already_scored`
  says **item A** was judged elsewhere. **Never** use it to excuse a **different** id sitting in
  `pending` (measured: one agent treated item A's `already_scored` as proof that `pending(id=B)`
  was unfixable, reported a counting artifact that cannot be cleared, and shipped with
  `to_score=1`; B had simply never been judged; one `vibe_score` cleared it).
  There are only two honest reasons an item will not go through: `not_yours` / `not_claimed`,
  or `already_scored` **where the reported id is the one in `pending`**.

| # | Step | Call | Fields in the response that drive the next step |
|---|---|---|---|
| ① | Goal / allowance | `vibe_balance` / `vibe_sub_health` | `claim_quota{month_used,month_limit,daily_used,daily_cap}`, `assessment.gap_reason` |
| ② | Claim | `vibe_leads(subscription_id, limit)` (`peek=true` gives a free look at **what you already claimed and have not judged**; it does **not** show unclaimed candidates: there is no free candidate preview, candidates come with the claim) | `data.posts[]`, `data.pending[]`, `progress.todo.claimable_now`, `progress.next.do` |
| ③ | Judge | `vibe_score(scores=[…])` (≤100 items = 1 pipeline token) | `items[].delivered_id`, `progress.round.scored_now`, `progress.todo.to_score`, `progress.next.do` |
| ④ | Outreach | `vibe_outreach(what="advice", delivered_id=…)` → write your own ≤18 words → send it back through the same tool as `draft=`. ⚠️ **The task book now carries high-engagement reference replies** (same thread + your subscription's delivered-thread pool, same-sub first): learn the **tone/structure**, never copy the wording or reuse their product names | `draft_prompt`, `draft_check`, `draft_source`, `progress.todo.drafts_missing` |
| ⑤ | Send + mark | after posting: `vibe_outreach(what="log", action="sent", lead_id=…)` to register, then `vibe_leads(mark=[{"lead_id":…,"outcome":…}])` once a real result exists | `progress.todo.outreach.sent` (when 0, do not mark results), `todo.to_mark` |
| ⑥ | Review / iterate | `vibe_delivered` / `vibe_keywords` / `vibe_keyword_edit` | back to ① |

**Step ④ in detail (skip it and the lead shows "no draft yet" in the app forever)**:

1. right after you judge `relevant`, `progress.next.args.delivered_id` in the response (the old
   field `outreach_next_step.delivered_ids`) is this batch's **delivery-row id** (use it, not the
   candidate id);
2. `vibe_outreach(delivered_id=<that id>, include_body=true)` → take `draft_prompt`
   (the writing brief: body excerpt + **what this lead wants (intent)** + the four-layer verdict +
   this community's key rules + 8 hard constraints + examples);
2b. **Read the intent section first** (`【这条线索要什么】`; the same object rides on the response as
   `lead_intent`, with the matched words that produced it). It answers **who the author is**. When it says
   `soliciting_feedback` (testers / feedback on their own product) the author is a **maker, not a user**:
   **never** ask "what felt unclear when you first tried it" (submitting that is flagged as an `intent_fit`
   failure); give one concrete first impression, or ask about **their** build. The brief also lists
   intent-specific example lines to copy the *shape* of;
 2c. **Then read the "what this post wants" section** (same object on the response as `poster_intent`).
   It answers **what the poster wants right now**, by post type: launch/showcase → **affirm the tradeoff
   they got right, then one concrete next step**; question → **the shortest concrete answer** (never bounce
   the question back); vent/emotion → **relate + a similar experience of your own** (**no advice**);
   milestone → **congratulate / encourage** (no KPI analysis); opinion → **take a clear side** (no fence
   sitting). Rule: **statements, not questions; at most one question mark per reply**, and **never
   challenge the product under a launch post** (the real "How are you handling multi-device users who still
   want sync?" got removed by a mod). Breaking this makes `draft_check.move_fit` fail: the four moves
   (answer / experience / affirm / relate) are all fine; cross-examining the poster is not.
3. write a **≤18 word** reply with **your** LLM from that brief (language per the `lang` field,
   Note: `verdict=dont_reply` **still wants a draft**: check `draft_hold.level`:
   * `account` (`karma_block` / `acct_age_block`, `basis=archive_gate`): the content is fine but
     your account is below the community gate, so **write the draft anyway** and submit it with
     `draft=`; send it once the gate clears (the reply carries `draft_warn` and the card shows
     "gate not met; draft kept").
   * `content` (post deleted / locked / community bans replies): `draft_allowed=false` and
     `draft_prompt` is empty; a draft would be useless, so skip it.
   default English);
4. send it back through the **same tool** as `draft=<finished text>`: the server re-checks it
   against the same rules (≤18 words / no link / no pitch / no promise to do the work) and stores
   it; the lead card in the app then shows **this** version first.
   The server is zero-LLM and serves **no generic templates** (generic lines are unrelated to the
   lead); the draft can only come from you.

**Warm-up was removed in 2026-10-19.** The `vibe_warmup_*` tools are gone from the server; calling
one now gets a **protocol-level unknown-tool error** (there is no custom `tool_removed` payload any
more, because the compatibility stubs were deleted too). **`vibe_doctor` still exists** (perf /
supply / purge); only its warm-up routing is gone; the karma answer is below. Building up an
account is left to you: pick communities with
`vibe_catalog(query=)`, check per-community rules with `vibe_community(kind="safety", sub=)`,
and study what gets engagement via `vibe_sub_posts(order="score")` / `vibe_community(kind="commenters")`.


### Cold start: **set the search face first**, then the word list (2026-09-21)

After `vibe_subscribe`, **a missing word list or sub list = the pipeline returns at the gate on every
round → it never produces candidates** (`setup.config_missing` / `source_status=config_missing`).
That is **not** the same as "running but with no material this round".

- Matching **runs only inside the corpus of the subs on your list** (v2.2 strict sub anchor); an empty
  list means zero candidates no matter how good the words are. So with an empty face,
  `progress.next.do` points straight at `vibe_subscribe`, `todo.face.config_missing=true`,
  `next.args.audience_profile` / `demand_pain` hand you both raw texts verbatim (the server does **no**
  term extraction and offers **no** candidate words: the anchor words are yours to derive, or just ask
  the customer which subs to use), and
  `stage_done=false` (the stage cannot complete).
- **⚠️ Anchor words and post-search words do NOT come from the same source (the step people get
  wrong)**: subs are split by **industry / audience / interest / topic**: so anchor words can only
  come from `sd_json.demand_side` (**target audience profile**), e.g. `lawn care operators` /
  `SaaS founders` / `indie hackers`. `demand_pain` is **what the author would say** (first-person pain,
  e.g. `how do I get my first customers`); that is the **post / comment search word**, and it must
  **never** be used as a sub anchor (`first customers` cannot be any sub's positioning).
  The receipt's `next.args` hands you both raw texts and their sources (`audience_profile` /
  `demand_pain` / `anchor_words_from` / `keyword_words_from`); **the words are yours to choose**;
  the server only supplies the raw material.
- **How to search the directory**: `vibe_catalog(query=<audience/industry short word>)`; no query → **face A**: subs with real `relevant`
  deliveries (already in corpus, searchable the moment you add them); with query → **faces B/C**: the
  directory matched lexically on **sub name + description** (may need pulling). For the whole directory
  use `vibe_catalog(query, sort)` (+ pagination + **relevance-first** ranking: `name_hits` (the sub
  is literally named this) > `rules_hits` (the rules raw text says it) > `desc_hits`, so prefer **short
  domain words** over a whole product sentence; the top `name_hits` result is usually the anchor you want).
- **Judge positioning from the rules RAW TEXT, not the description**: every candidate carries `rules[]`
  (`{short_name, description, priority}`; the moderators' own rules) and `submit_text`. E.g.
  `r/buildinpublic`: *Stay on Topic: All posts should be related to "building in public" … Off-topic
  content will be removed*: one sentence defines the sub. ⚠️ `rules_missing=true` means **we asked the
  rules API and Reddit has no public rules**: that is not "no restrictions"; when `rules_available=false`,
  fall back to `description` / `submit_text`.
- **Confirm "the people in this sub ARE the demand_side"; read its corpus, do not trust the delivery rate alone**:
  a sub's delivery rate is a function of **(sub × the judging caliber you were using at the time)**, not a
  property of the sub. Measured 2026-09-21: `r/alphaandbetausers` showed **3.2%** (7/220) under the old
  caliber and was dropped from the list; after the caliber was fixed and its 213 historical rejections were
  re-judged it is **95%** (209/220): the most on-target sub of the subscription. So (a) after any caliber
  change, per-sub history **must be recomputed** before you act on it, and (b) `n<10` was never enough to
  conclude anything. The caliber-independent check is to read what those people actually write:
  `vibe_sub_posts(sub=<candidate>, limit=200)`; if the titles are overwhelmingly "I'm recruiting my first
  users / testers", the audience IS your demand_side (`r/alphaandbetausers`: `beta testers` in 390 of 3417
  titles). That check uses no scoring result and no caliber.
- **Iterate: do not decide once**: `vibe_subscribe(subscription_id, update_sublist=[…], sublist_mode="replace")`
  (or `add` / `remove`) → then each round read `todo.supply.stats.subs` (per-sub pooled / delivered /
  rejected / **delivery rate** / unclaimed + `in_list`) and `gap_reason=supply_ceiling`: drop the
  0-delivery subs, add candidates.
- ⚠️ **An existing subscription's initial list is `source=backfill`; its historical hit surface** (filled
  at v2.2 launch from whatever it happened to search before). Treat it as a **starting point, not the
  destination**: review it on the first run (keep what has stock / drop noise / add B/C candidates).
- Zero server-side LLM: **we write neither the list nor the word list for you** (candidates and evidence
  are yours to decide on).
### `progress` block fields (same shape in every response; absent when the tool doesn't touch that stage)

```json
"progress": {
  "stage": "intake",              // intake(claim→judge→return) | outreach(outreach)
  "stage_index": 1, "stage_total": 2, "stage_label": "claim → judge → return",
  "stage_done": false,            // true = this stage is done, you may move to the next
  "round": {"claimed_now": 2, "scored_now": 0, "delivered_now": 0},
  "todo": {"to_score": 18, "to_score_web": 0, "to_score_by_sub": {"400": 18},
           "claimable_now": 32,
           "limits": {"pool_available": 57, "daily_left": 988,
                      "quota_left": 793, "gate_left": 32, "gate_limit": 50}},
  "summary": "this stage(claim → judge → return) this round: claimed 2 / judged 0 / delivered 0; remaining: 18 to score, 32 claimable",
  "next": {"do": "vibe_score", "why": "…", "args": {"n_items": 18}, "gate": "…"}
}
```

- `claimable_now` = min(immediately claimable in the pool / left today / monthly allowance left +
  wallet-affordable overage / gate left); **all four are broken out in `limits`**: see clearly
  which term is the 0 (a full gate ≠ no supply).
- **`to_score` is account-wide** (the gate counts by API key) while the pending list from
  `vibe_leads(peek=true)` is **per subscription**: use `todo.to_score_by_sub` (or
  `next.args.subscription_ids`) to find which subscriptions hold the remainder, peek each, judge,
  and submit one batch; only when **all subscriptions together** reach zero does `stage_done=true`
  (otherwise the stage can never advance).
- **Feedback gate (the supply-side closure)**: verdicts are written back to the per-keyword
  counters (`n_rejected` / `avg_score`) and to `scoring_feedback`; but **written back ≠ acted on**:
  retiring a word / dropping a sub is *your* decision, and retirement only affects *future* matching:
  rows already matched into the pool keep getting claimed (measured: after the `revenue` keyword was
  retired, the 36 rows pooled 7 minutes earlier were still handed out). Once the evidence is enough
  (a word/sub with >=10 judged and >=90% noise, or one batch with >=5 items and >=80% irrelevant) the
  response sets `todo.supply.gate=true`, lists `noise_kw` / `noise_subs`, and switches `next.do` to
  `vibe_keywords`. **A high noise rate is NOT by itself a retirement order**: retirement advice is only given for
   **zero-delivered** rows. A word/sub that has already delivered has produced buyers, so it is listed as
   evidence with `zero_delivered:false` and `why` explicitly says do-not-retire; consistent with the skill
   decision table (`delivered>0` is never self-retired; "weak" only means watch it). Read the row, not just
   the rate: a word can be 90% noise and still be your best supplier (measured: `beta users` at `410/454`
   noise had delivered **44** leads and was nearly retired).
   **Delivery rates and the scope's management history come with it** (not a
  decision made for you): `todo.supply.stats.subs` / `.kw` / **`.pairs`** = per sub / keyword / **(word x sub) pair**
pooled · delivered · rejected · **delivery rate** · unclaimed. `.pairs` is the layer that matters most: **the same word
can be 95% in one sub and 0% in another** (measured: `closed testing` 95% overall vs 13% in `b2bmarketing`), so a low
number must first be attributed. Each pair carries `kw_rate_elsewhere` (that word's rate in the **other** subs, this
cell removed), `sub_rate_other_kw` (that sub's rate on other words) and a `hint` (**pair problem** = word and sub are
both fine elsewhere, only this combination is bad / **word problem** / **sub problem** /
**both word and sub are bad** (retiring the word will not help) / **null** (**the comparison sample is too
small, so no attribution is given**). Every threshold is in the row itself and **recomputable**: the cell is
low-yield when judged >= 5 and rate < 0.20; `kw_rate_elsewhere` / `sub_rate_other_kw` are computed with
**this cell removed** and only count when `kw_elsewhere_judged` / `sub_other_kw_judged` are >= 5; >= 0.40 counts
as "fine elsewhere"). The `hint` is a
**deterministic classification and only a hint**; the server never retires a word, drops a sub or excludes a cell
because of it. Try a **narrower word shape** first (`closed testing` → `closed testing testers`). Also per sub/keyword: `每个
  rejected · **delivery rate** · unclaimed, plus `in_list` (still in the search scope) and
  `list_added_at` / `list_source`; `stats.sub_history` = the add/remove/replace log for that scope
  (who · when · why, auto-recorded like `kw_change_log`; you only pass `note`); `stats.low_yield` =
  subs/keywords with >=5 judged and <20% delivery rate: **just the same data sorted differently, not
  a gate**: it is yours to decide. `gate` is likewise evidence + a suggestion (`override_allowed:
  true`); you may simply keep claiming.
  **But mind the boundary**: supply-side cleanup (retire a word / drop a sub / purge old stock) **is the
  agent's job: it is not something to wait for approval on**. The server only supplies the data and the
  entry points (`todo.supply.stats` + those three tools). Only four things need the human first: **spending
  money / changing the billing model / posting or emailing / deleting billed history**. Measured lesson
  (sub 355): while the gate was open and the agent merely reported and waited, noise kept getting claimed:
  act there and then, then log it. When you do act: call `vibe_keyword_edit(action="remove", items=[{"kw":…, "force":true}], note=…)` (**it also purges that word's
  unclaimed pool rows**; `pool_purged` in the reply) / `vibe_subscribe(update_sublist=subs, sublist_mode="remove")` /
  `vibe_doctor(what="purge", subscription_id=…, kw=…)` (keep the word, drop its old stock),
  log it with `vibe_keyword_edit`, then resume the inner loop.
- **Result write-back (the server supplies the objective evidence; you make the call)**: the
  monitoring leg re-checks your posted replies at T+24h/72h/7d: alive / removed / self-deleted /
  score / **someone replied**. Two things ride along: `todo.outreach{sent,alive,removed,replied,
  reply_rate,replied_ids,last_checked_at}` (evidence) and `todo.to_mark{n,delivered_ids,
  outcome_legend}` (how many are still unmarked, with ids). Once drafts are done `next.do` points at
  `vibe_leads` (outcome = valid | invalid | contacted): **a reply is a strong valid signal**,
  but valid/deal is still your call. Rows judged "do not reply" (e.g. karma too low) are marked
  `draft_skip` and **never block the flow** (`todo.vetoed_n` is listed separately) while the
  `drafts_missing` definition stays unchanged. The customer-facing value evidence lives in
  `vibe_delivered`'s `outreach_stats` (sent -> alive -> replied -> reply rate).
- **`next` is only the single best action, not the whole backlog**: the reply also carries
  `next.alternatives` (the other things owed; e.g. "46 delivered leads with no draft / 50 more you
  can claim"): the server states the facts, the choice stays yours.
- **Outreach backlog is counted per subscription**: `todo.outreach_scope` (`subscription 355` or
  `account`) states the scope; when it is account-wide, `todo.outreach_by_sub` breaks the backlog
  down per subscription (how many drafts/marks each one owes). Measured lesson: the account-wide
  count showed 122 missing drafts while working subscription 355 and put another subscription's
  delivered_id into `next.args`.
- **Field quick-reference (added after the clean-agent test, each with a measured source)**:
  · `data.billing` (inside `data`, not top level): `billable_items` = items on their **first claim** (the billing base, including the free-within-quota ones); `charged_items` = how many actually charged the wallet; `free_items` = free within quota; `takeover_items` = already billed elsewhere and reclaimed free. All three can coexist; read `billing_note`.
  · Candidates may have **no** system pre-score: `score: null` + `prescored: false` (then `score_note` says so explicitly). Older doc text claiming a system reference score is superseded by `score_note`.
  · `vibe_delivered` rows now carry `has_draft` / `draft_len` (**per-row draft discovery without fanning out advice**), plus `draft_skip`, `outreach_state`, `outreach_replies_n`.
  · `todo.to_mark.delivered_ids` returns at most 20 ids; beyond that `ids_truncated: true` + `ids_limit: 20`.
  · **Not enough karma**: the warm-up feature was retired on 2026-10-19 (the `vibe_doctor` route split, target karma, gap and ETA all went with it). Use `vibe_community(kind="safety", sub=)` to see a community's rules and removal rate, `vibe_catalog(query=)` to pick communities; whether to post is your call. **The server never farms karma** (no posting, no voting).
  · `publish_verdict` = "can my account post in this community" (a different question from `verdict`). The **platform-level prior (new account / low karma) is advice only**: when `publish_verdict.basis == "archive_gate"` the conclusion rests on this community's archived rule; otherwise there is no archived basis and it is only a general prior, not this community's rule. Only **evidence-based** cases yield `hold`/`no`: account profile missing, an archived gate with no numeric value, or a gate you genuinely miss (`blocks: karma_block|acct_age_block`). So once a draft is ready you can **test the waters in a small community**; do not let the prior scare you off.
  · Every `vibe_delivered` row carries both `id` and `delivered_id` (same value); other receipts use `delivered_id`, so you cannot feed the wrong one.
  · A failing `draft_check` now also returns `failed_detail[{k,hit,note}]`: the **offending snippet** shows which phrase tripped it.
  · The three draft flags: `draft_stored` = is a draft in the DB right now (authoritative); `draft_written` = did **this call** write one; `draft_saved` is a deprecated alias of `draft_written` (same value). Reading back a lead that already has a draft gives `stored=true / written=false / saved=false`: that is **not** a contradiction.
  · `next.advisory: true` = this next is a **supply-side suggestion** (the feedback gate); when retiring words/subscriptions is out of your scope, just take `next.alternatives` (usually claiming); the server does not block it.
  · **Where `progress` lives**: `vibe_leads` → `data.progress`; `vibe_score` and `vibe_outreach` → **top-level** `progress` (historical; read it where this doc says).
  · `vibe_leads(peek=true)` returns only the **claimed-but-unjudged** list (`pending`); unclaimed candidates are not in peek (`posts=[]`, check `pool_stats.new`); claiming is what returns candidates.
  · When `vibe_outreach` cannot find your comment it records only `outreach_state=unknown` and does **not** write an outcome (no comment found means nothing was reached); auto-marking `contacted` happens only on a real hit.
  · `progress` rides on **three pipeline tools only** (`vibe_leads` / `vibe_score` / `vibe_outreach`); other read tools (`vibe_balance` / `vibe_delivered` / `vibe_delivery` …) return their own data without `progress`.
  · If `next` needs something outside your scope (retiring a word, dropping a sub, posting on the customer's behalf), **hand it over**: take `next.alternatives` (usually claiming) or pass it to the human; the server **never blocks** claiming. `next.advisory: true` marks a suggestion (the supply-side feedback gate); `alternatives` will **not** suggest `vibe_leads` while nothing has been sent (with `sent=0` it points at `vibe_outreach` instead).
  · **id cheat sheet (this tripped three clean-agent runs; delivery tools now accept both)**: `delivered_id` (delivery-row id, the `delivered_ids` in receipts) is the **recommended argument** for `vibe_delivered` / `vibe_outreach` / `vibe_leads`; candidate ids (`lead_pool.id`, 7 digits, the `lead_ids` in receipts) belong to `vibe_score` / `vibe_recover_lead`: but the delivery tools now accept them too (mapped internally), so a mix-up no longer fails silently.
  · `vibe_delivered(lead_id|delivered_id)` accepts either and returns `has_draft` / `draft_len`; `vibe_leads` lists any id it could not resolve in `unresolved_ids` (no more silent `updated=0`).
  · On `vibe_score` the `unmarked_delivered` count is **account-scoped** (carries `unmarked_delivered_scope: account`); for the subscription(s) in play read `progress.todo.to_mark` (with `scope` and the id lists).
- outreach-stage `todo`: `drafts_missing` / `drafts_open` / `vetoed_n` / `drafts_written` /
  `unmarked_delivered` / `to_mark` / `outreach` / `delivered_total`.
- language/scope hints (`lang` / `lang_source` / `sd_missing`) coexist with the progress block,
  each minding its own business.

### Demand-side response fields → your action (parallel to the supply-side table in §2)

| Response field | Meaning | Your action |
|---|---|---|
| `progress.next.do` | the next tool the server computed for the current stage | **call it** (the pipeline's main driver) |
| `progress.todo.to_score` | claimed but unjudged (gate scope, agent claims only) | >0 → `vibe_score` (one batch) |
| `progress.todo.claimable_now` | what you can really claim now (min of four terms) | >0 and to_score=0 → `vibe_leads` another batch |
| `progress.todo.limits.*` | which term caps the claimable number (pool/day/quota/gate) | treat the cause: gate → judge first; pool → wait for intake / widen the list; quota → `vibe_balance` |
| `items[].delivered_id` | delivery-row id of what you just judged relevant | pass to `vibe_outreach` (**not** the candidate id) |
| `unmarked_delivered` | sent but outcome not marked | >0 → `vibe_leads(mark=[{"lead_id":…, "outcome":…}])` |
| `data.source_status` | `ok` / `pending` / `locked` / `waiting` / `exhausted` / `config_missing` | only `ok` has new supply; `locked` → judge first; `config_missing` → fix config per `next_steps` |
| `billing{claimed_batch,billable_items,charge…}` | billing for this claim batch (first claim = billed) | tell the user the cost; overage is charged to the settlement-currency wallet |
| `data.lang` / `lang_source` | language for this subscription's judging and drafts | write sd four fields, verdict reasons and drafts in it |

## Tools

| Tool | Params | What it does | Cost | Auth |
|------|--------|-------------|------|------|
| `vibe_register` | `email`, `mode`(`send` \| `verify`), `code` | Register (two steps in one): `send` = mail a 6-digit code; `verify` = exchange it for an API key (Free tier) | Free | None |
| `vibe_account` | `action`(`recover_send` \| `recover_verify`), `email`, `code` | Lost your key: `recover_send` mails a code, `recover_verify` mails the key back | Free | None |
| `vibe_balance` | `set_currency`(optional `usd`/`cny`/empty=auto), `lang`(optional `en`/`zh`/empty=auto), `subscription_id`(optional) | Balance / tier / two wallets / settlement currency / monthly allowance. Passing `set_currency` or `lang` also applies it (write bucket); omitting both is a pure read | Free | Header |
| `vibe_set_notify` | `enabled` | Email alerts on candidate backlog (default on) | Free | Header |
| `vibe_subscribe` | `product`, `action`(`create` \| `cancel`), `subscription_id`, `enable_competitor_kw`, `track_type`, `update_sd`, `update_sublist`, `sublist_mode`, `note` | All subscription writes in one: `create` (needs `product`) / `cancel` (needs `subscription_id`) / `update_sd={supply_side,demand_side,core_friction,demand_pain}` / `update_sublist=[...]` with `sublist_mode=replace\|add\|remove\|list` | Free | Header |
| `vibe_subs` | `subscription_id`(optional) | Everything about your subscriptions in one call: list + per-sub stats (new/sent/delivered/rejected) + per-subreddit hit stats | Free | Header |
| `vibe_catalog` | `query`, `offset`, `limit`, `sort` | Sub directory. `sort` empty = recommendation (A: proven deliveries + B/C: lexical candidates); `sort` non-empty (`subscribers`/`active`/`name`/`volume`) = full directory search | Free | Header |
| `vibe_sub_health` | `subscription_id` | Why this subscription is not producing enough: quota / daily line / stock / gap / `gap_reason` / setup completeness / delivery totals | Free | Header |
| `vibe_leads` | `subscription_id`, `status`(`new` \| `rejected`), `limit`, `offset`, `source`, `peek`, `include_body`, `format`, `mark` | Claim leads (billed on first claim). Also: `status=rejected` = recycle list; `format=export` = export; `mark=[{lead_id,outcome}]` = mark results; `peek=true` = free read-only list of already-claimed-unscored items | Billed on first claim | Header |
| `vibe_score` | `scores`, `override`, `discuss`, `limit`, `respond_id`, `response` | Score claimed leads (`relevant` -> delivered). `discuss=true` or `respond_id` = view/respond to disagreements (free) | Free (scoring) | Header |
| `vibe_delivered` | `lead_id`, `delivered_id`, `limit`, `offset`, `subscription_id`, `order` | Delivered leads. Passing an id = single detail (both id types accepted), omitting = list | Free | Header |
| `vibe_recover_lead` | `lead_ids` | Restore wrongly-filtered candidates back to pending-score | Free | Header |
| `vibe_keywords` | `subscription_id`, `status`, `history`, `limit` | Keyword list + hit stats; `history=true` = change history (who changed what, manual/auto) | Free | Header |
| `vibe_keyword_edit` | `subscription_id`, `action`(`add`\|`remove`\|`exclude_pair`\|`log_opt`), `items`, `source`(`manual`\|`auto`), `note` | The only write entry for keywords. `items` is an array whose shape follows `action`: add `{kw,kw_type}` / remove `{kw,force,purge_pool}` / exclude_pair `{kw,sub,mode}` / log_opt `{outcome,reason,n_new_kw,n_replaced}` | Free | Header |
| `vibe_sub_posts` | `sub`, `order`(`score`\|`comments`\|`new`\|`old`), `window_days`, `limit`, `offset`, `cursor`, `body_max_chars`, `refresh`, `refresh_max` | Posts of one subreddit. `score`/`comments` = server-ranked board (paginate with `offset`); `new`/`old` = zero-semantics time paging (paginate with `cursor`). Returns full posts incl. body by default | Billed as a claim (full post = one lead) | Header |
| `vibe_community` | `kind`(`commenters`\|`profile`\|`safety`), `sub`, `author`, `focus_sub`, `limit`, `min_n`, `min_avg`, `sort`, `include_bots` | People and rules of a community: top commenters / a user's active communities / safety reference | Free | Header |
| `vibe_outreach` | `what`(`advice`\|`profile`\|`log`), `action`(`sent`\|`declare`\|`confirm`), `delivered_id`, `lead_id`, `permalink`, `draft`, `include_body`, `include_prompt`, `reddit_username`, `reddit_karma`, `reddit_account_age_days` | Outreach assistant + send log. Credibility ladder: `declare` (claim only) -> `sent` (self-confirm) -> `confirm` (server verifies by comment id) | Free | Header |
| `vibe_bundle` | `calls` | Run N read-only tools in one round trip | Free | Header |
| `vibe_app_bootstrap` | — | First-screen aggregate read | Free | Header |
| `vibe_delivery` | `subscription_id`, `format`, `limit`, `include_body`, `fields`, `since`, `before_id` | Delivery artifact (JSON is the single source of truth) | Free | Header |
| `vibe_doctor` | `what`(`perf`\|`supply`\|`purge`), `minutes`, `subscription_id`, `kw`, `sub`, `out_of_scope`, `dry_run` | Internal diagnostics (perf p50/p95 / supply snapshot / pool purge). For "why is my subscription underperforming" use `vibe_sub_health` instead | Free | Header |

> All tools except `vibe_register` authenticate via the HTTP header `Authorization: Bearer <api_key>`; **the key never appears in tool params or call logs**.

### Management tools: see the table above

> 2026-10-19: 原「Management tools (2026-09-05)」这张表已删除 —— 它与上面的主表**完全重复**，
> 而且工具面合并后同一个工具会在一张表里出现多次、每次一套旧参数（`vibe_keyword_edit` 出现过 6 次），
> 照着调必错。**参数以主表为准**，各工具的完整语义看 tool docstring。
### Loop cadence: re-enter on **stock**, not on a clock (2026-09-22)

The loop is **not a one-time setup**: the server keeps filing candidates into the pool every
~30 min, so a face that is configured but never re-run silently piles up leads nobody judges.
Measured on the live service (2026-09-22): among **active customer** subscriptions several had
**3,000–6,000** claimed/unclaimed candidates waiting while their **last judgement was 1–2 weeks
old**, and two had never judged anything at all. Their dashboard said "no leads" while the pool
was full; the face was fine, nothing was running the loop.

**Trigger: read these, then act (no clock-watching, no guessing)**

| What you read | What it means | What you do now |
|---|---|---|
| `progress.todo.to_score > 0` (any response) or `vibe_leads(peek=true).data.unjudged_total > 0` | you are holding claimed-but-unjudged items | `vibe_score`: **finish the batch before claiming another** |
| `to_score == 0` and `progress.todo.claimable_now > 0` | stock is waiting and your allowance is free | `vibe_leads(subscription_id, limit)` → judge → return |
| `vibe_sub_health.stock` rising while `assessment.projected_items_month` stays short | the face produces, nobody judges | run the loop; if you are the host agent, **schedule it** |
| `to_score == 0`, `claimable_now == 0`, `progress.stage_done == true` | intake is complete for now | move to outreach, then re-check on the next tick |

- **Cadence**: while `assessment.gap_reason=shortfall` (goal not met) run **at least one batch
  every 30–60 minutes**; in steady state (`committed_ok`) **once a day** is enough; a daily pass
  also keeps `sent` items from hitting the 7-day expiry.
- **Batch**: one `vibe_leads(limit)` + one `vibe_score` (≤100 items = **1 pipeline
  token**). Claim up to your tier's limit (free 20 / starter 30 / pro 50), judge it, return it,
  repeat. Do **not** claim a big stack and judge it "later": `to_score` counts against your own
  next claim (the gate is per account).
- **Every subscription, not just the first**: `to_score` is account-wide while the pending list
  is per subscription: use `todo.to_score_by_sub` (or `next.args.subscription_ids`) to see
  **which** subscription is behind, and run the loop for each of them.
- **Ready-made timer: `scripts/loop_runner.py`** (2026-09-22). The skill now ships the timer,
  not just the executor: it does **intake** (calls `score_batch.py`: claim → judge → return) and the
  mechanical half of **outreach** (fetch the draft task → your LLM writes ≤18 words → the server
  re-checks and stores it). **It never posts**: sending stays with you/your agent
  (`vibe_outreach` → `vibe_leads`). BYOK: `VIBEDOLLAR_API_KEY` + `LLM_API_KEY`
  (+ `VIBEDOLLAR_MCP_URL` for a self-hosted endpoint); cost gates `--limit`/`--daily-cap`/
  `--outreach-per-sub`; `--stage intake|outreach|both`; install snippets (cron + systemd
  timer) are in the script's docstring. Measured why it matters: without a timer the loop stops
  half-way: 8 non-marketing subscriptions had 6 with judging stale 11–14 days (or never), and
  sub 355 had 655 delivered leads but only 166 drafts (its latest 10: none).
- **Per-subscription manual recipe** (if you prefer to drive it yourself): every 30–60 min,
  `python3 scripts/score_batch.py --sub <sid> --limit <tier limit>` → then read
  `vibe_sub_health` and act on `assessment.gap_reason` (see "Agent decision loop" below). Stop
  scheduling a subscription when `assessment.committed_ok` is true and stock is flat.
- **Anti-pattern (the failure this prevents)**: "set up the face, judged a few early leads, never
  came back". Nothing errors, nothing alerts, and the dashboard stays empty: measured twice on
  2026-09-22 (`345` ≈5k to score, last judged 09-08; `397`/`398` never judged at all).

### Agent decision loop (per subscription, per round; v2.1 delivery-driven)

vibedollar is the **data/state layer: server makes zero decisions**. It collects Reddit,
matches candidates into the pool, records your scoring feedback as signals, and returns
health data; **you (the host agent) decide everything**: expand / retire / regenerate /
probe / wait / report. There is no server-side auto-retire to wait for: hit=0, avg_score,
n_rejected etc. are *signals for you to act on*, not actions the server takes.

**The loop is driven by the delivery goal, not by "is there a pool to score".** Each round:

```
goal check → perceive → plan (one action) → act → verify → back to goal check
```

#### 0. Goal check (before anything: the loop's engine)

Goal = can the current search face fill the customer's monthly claim allowance this month
(see `vibe_sub_health.assessment`: `projected_items_month` vs `commitment_remaining`,
plus `gap_reason`). Every round asks:

- **`committed_ok`** → `wait` (fast loop digests; no supply action needed)
- **`shortfall`** → the task is NOT done. Pick the next action from the decision table
  below, act, verify, and **return to the goal check**. You may only stop (report
  exhausted) after trying every available direction and verifying none improved supply.
  **Never end a round silently after scoring**: "scored 15, all irrelevant" is a signal
  to change direction, not a completed task.

#### 1. Perceive (read tools, zero LLM)

```
vibe_sub_health(sid)     → assessment (projected_items_month / commitment_remaining / gap_reason /
                           supply_per_day / daily_need / backlog stock) + stock / gap / collecting_ok / last_opt
vibe_doctor(what="supply", subscription_id=sid)  → corpus intake trend / catalog age / arctic.limited
vibe_keywords(sid, all)  → per word: status/source/query/hit/pooled/avg_score/
                           n_delivered/n_rejected/invalid_sample/created_at
vibe_subs(sid)           → which subreddits actually contribute candidates
vibe_subscribe(sid, update_sublist=[], sublist_mode="list")  → your current sub list (v2.2: your explicit search face)
vibe_leads(peek=true)    → **glance at this every round**: progress.todo.supply.stats.pairs / low_yield.pairs
                           = the (word x sub) grid — **the same word can be 95% in one sub and 0% in
                           another** (measured: closed testing 95% overall / 13% in b2bmarketing). Each
                           cell carries kw_rate_elsewhere / sub_rate_other_kw and a hint, which tells you
                           whether to fix the word, drop the sub, or declare a pair exclusion —
                           **read the hint first, never the bare number**
```

**v2.2 (2026-09-09): your search face is your sub list.** Matching now runs **only
inside the subs you listed** (`vibe_subscribe`), never the whole corpus. So the
loop's supply side is: *keep the list healthy*: subs you've proven deliver stay;
subs you've never scored relevant on are noise; subs you haven't listed aren't
searched at all. Before expanding words, check your list:

#### 2. Health-data semantics (what each returned number means → what you decide)

The server only *reports* these; **you** act on them (v2.1: server makes zero decisions):

| Data | What it means | Your decision |
|---|---|---|
| `assessment.gap_reason` | why supply can't fill the allowance: `supply_ceiling` (face too narrow / vertical thin) · `word_face` (relevant rate < 15%) · `capacity` (need exceeds the daily cap) · `collecting` · `no_data` · `ok` | **supply_ceiling → widen the sub list** (add subs; this is the usual fix) · `word_face` → retire/regenerate words · `capacity` → nothing to fix on supply (it's the daily throttle) · `collecting` → alert, wait for intake |
| `projected_items_month` vs `commitment_remaining` | can the face fill the monthly claim allowance (items, matching the billed unit) | **goal check**: `committed_ok` → wait; `shortfall` → act (this drives everything) |
| `hit_count` = 0 | the phrase hasn't matched yet in corpus; **not conclusive on round one** (2026-09-08 Snag: "declutter home" q1=0 then q2 hit: search intake is incremental, a word can surface once its post arrives) | don't retire on a single 0-hit round: keep observing until qc≥3; if still 0 after several rounds with the corpus growing, probe targeted subs, replace the phrasing, or retire (F3-like: sustained 0-hit across rounds with fresh corpus = phrase absent) |
| `hit_count` > 0 but all your scores `irrelevant` | the phrase exists but **matches noise**: it's a wrong word, not proof demand is exhausted | retire the word, then **regenerate the word face from sd** (`sd_gen.md` if sd missing → `kw_init.md` → `vibe_keyword_edit`); wrong words are fixed by regenerating, not by giving up |
| `n_rejected` ≥ 2 + 0 delivered + `invalid_sample` off-topic | noise generator | `vibe_keyword_edit` force + `vibe_keyword_edit` (see Plan A) |
| `avg_score` (negative) | aggregated scoring feedback signal (−3 per your irrelevant, server records only) | the more negative, the more rejects: supports retire/regenerate decision; **server does not retire on it** |
| `query_count` < 3 | not enough observation | don't judge yet (avoid single-shot miskill) |
| `created_at` recent | NEW30 group (judge ② input) | recently-added words' hit rate → keep expanding or stop |
| `collecting_ok=false` | backend intake down today | alert: expanding is useless until collection recovers |
| `pipeline_recent` (matched=0 several rounds) | words find nothing in corpus now | word exhaustion → probe/replace/regenerate; **distinguish from corpus intake stall**: if `corpus_today` collapsed (vs ~90k/day baseline) the corpus isn't growing: wait/alert, not a word problem |
| `arctic.limited` | physical rate limit | pause supply actions until clear (not a cooldown) |

#### 2b. `gap_reason=word_face`: fix it yourself, then **prove** it (closed recipe, 2026-09-22)

`word_face` means: you have stock, you have quota, the rounds run, and **almost everything you
claim comes back `irrelevant`**. That is a word/face problem, not a supply or a cadence problem,
and **you (the host agent) fix it**: the server never rewrites your words or your list.

Measured example (2026-09-22, sub 362): 8 claimed → 8 judged → **0 relevant** → delivery rate
stayed `1/98 = 1%`; `config_missing=false`, stock 97, no 429, quota untouched. Nothing was
"broken": the words were simply not buyer language for that product.

**Loop (do all four steps, do not stop after step 2):**

1. **Read the per-word evidence, not the total.** `vibe_keywords(subscription_id=…)` →
   per word: `hit_count` / `n_pooled` / `n_delivered` / `n_rejected` / `avg_score` /
   `invalid_sample` (the last is a real rejected post: read it: it tells you what the word
   *actually* pulls). A word with `n_rejected ≥ 2, n_delivered = 0` is a noise generator.
2. **Act on the words**: `vibe_keyword_edit(kw)` for the noise generators, then **regenerate
   the word face from `sd.demand_side` + `demand_pain`**: `kw_init.md` (derive from sd) or
   `kw_mine.md` (sweep a precision audience sub's own corpus and mine its phrasing) →
   `vibe_keyword_edit`. If a whole sub contributes only rejects, fix the **face** too:
   `vibe_subscribe(sublist_mode=add|remove)`; the same word can be 95% in one sub and 0% in
   another (use `stats.pairs` + `vibe_keyword_edit` before dropping a word that works elsewhere).
3. **Re-run the round and measure the same thing again** (one round is ~1 batch):
   `score_batch.py --sub <sid> --limit <tier limit>` → read back `relevant/judged` per word.
   **Success criterion**: the new words' `n_delivered / (n_delivered + n_rejected)` ≥ **20%**
   over ≥ 5 judged (below that, they are the same noise with new spelling), and the
   subscription's delivery rate stops moving toward 0.
4. **Write down what you changed and why**: `vibe_keyword_edit` (or your own notes): which words
   retired, which added, the measured before/after rate. The next agent (or you, next week)
   must be able to tell "this was fixed" from "this was merely re-run".

⚠️ **Never conclude "this market has no demand" from one all-irrelevant batch**: that is the
measured failure mode this recipe exists to prevent (a face can be fixed; a market judgment
cannot be tested with words that never matched buyers).

#### 2c. Before you spend quota: **read the titles first** (free): and know the AND semantics (2026-09-22)

Found by a customer-side agent fixing a `word_face` subscription (362: 1.9% → 5.5% delivery,
new word `facebook marketplace` 3/10 = 30%). Two habits worth copying:

- **Free inspection before claiming.** `vibe_leads` (bodies/titles of stock) and
  `vibe_doctor(what="purge", subscription_id=…, out_of_scope=true)` show you **what is actually in the pool**
  without claiming anything: claiming is what gets billed. Use them to decide
  "retire this word / purge this stock" **before** one junk item costs quota. The measured
  trap: `--dry-run` on the executor is not free either: it peeks nothing and, in older
  versions, still claimed; the free reads are `vibe_leads(peek=true)`, `vibe_leads`,
  `vibe_doctor(dry_run=true)`.
- **This matcher is AND (all words must appear), so generic words are poison.**
  Measured on 362: `free stuff` / `free items` / `buy nothing` / `moving boxes` /
  `needing furniture` / `nextdoor` / `freecycle` all filled the pool with noise: every one
  was disproven by **reading the titles**, and all were retired. A word must carry the domain
  noun (`free furniture`, `curb alert`, `facebook marketplace`), not just the intent.
- **A weak word is a (word × sub) problem, not a word problem**: `free furniture` was 7%
  overall but useful in city subs and rejected in `minimalism`/`Mommit`/`ZeroWaste`:
  the fix is `vibe_keyword_edit`, not `vibe_keyword_edit`.

#### 3. Plan: one action, driven by the goal

**A. Close your own scoring loop first** (scoring feedback is the strongest signal).
If your last scoring round produced `irrelevant` verdicts for a word with **0 delivered**
(n_rejected ≥ 2 and `invalid_sample` shows off-topic junk it pulls) → that word is a
noise generator → **retire it now**:

```
vibe_keyword_edit(subscription_id, action="remove", items=[{"kw":…, "force":true}])   # auto word — your call, no server batch to wait for
vibe_keyword_edit(subscription_id, action="log_opt", items=[{"outcome":"auto_retire", "reason":"0 relevant, N irrelevant"}])
```

`n_rejected` is cumulative across scorers; when you can't tell whose rejects they are,
let `invalid_sample` arbitrate: clearly off-topic junk confirms a noise generator; a
plausible in-scene post that was rejected suggests a misjudgment: recover it
(`vibe_recover_lead`), don't retire the word on that evidence.

**B. Then read the NEW30 marginal-yield signal** (is expanding keywords still useful?):
words added in the last ~30 days (`created_at` recent):
- mostly **hitting** (>0 hit) and delivery still short → keep expanding (probe-verified words only)
- mostly **zero-hit** → the current word face can't reach demand → don't just stop: probe
  alternative phrasings, and if the face is exhausted after retires, **regenerate from sd**
  (see C) before concluding anything about the market

**C. All-irrelevant ≠ market ceiling: regenerate the word face.** If you retired a batch
of noise words (0 relevant) and delivery is still short, the words were wrong, not the
demand. Regenerate from the supply/demand profile: sd missing → `sd_gen.md` →
`vibe_subscribe`; then `kw_init.md` (or `kw_opt.md` with current rows) → new word face →
`vibe_keyword_edit`. Only after a regenerated face also fails (new words hit=0 or
all-irrelevant again) do you move to corpus exploration or report.

Decision table (goal-driven, v2.2 sub-anchored: 2026-09-09):

| Observed | Action |
|---|---|
| Goal met / exceeded | `wait` (fast loop digests) |
| Goal not met, stock(new+sent)>0 | score the pool (`score_batch.py`): results feed this table next round |
| **sub list empty** | pick your search face: `vibe_catalog` (A: subs with real deliveries: in-corpus, searchable now; B/C: niche candidates, may need pull) → `vibe_subscribe(subscription_id=…, update_sublist=subs, sublist_mode="replace")` → server bulk-fetches `needs_pull` subs automatically |
| **list subs all silent** (`pipeline_recent` matched=0 several rounds, corpus growing) | widen the list: the demand lives in subs you haven't listed: `vibe_catalog(query=<product/niche words>)` → add candidates (B/C may need a one-time fetch, ~min/sub) |
| word: 0 delivered + ≥2 rejected, `invalid_sample` off-topic | `vibe_keyword_edit` force + `vibe_keyword_edit` |
| face cleared after retires, goal still short | **regenerate**: sd_gen (if sd missing) → kw_init/kw_opt → `vibe_keyword_edit` |
| new words hit=0 across rounds, list healthy | the phrase is absent in your listed subs' corpus → **widen or replace the face**: `vibe_catalog` for candidate subs → `vibe_subscribe` to add them (the server queues the pull) → judge the phrasing from `vibe_keywords` hit stats next round. There is no agent-side probe any more (`vibe_search_probe` retired 2026-09-11: pulls go only through the sub list) |
| NEW30 hitting, goal short | expand: `vibe_keyword_edit` |
| NEW30 swept, collecting_ok | corpus boundary thin → widen your sub list (stage B), record the attempt meanwhile |
| `collecting_ok=false` | alert (intake down: expanding useless) |
| `arctic.limited` | pause supply actions, physical wait, not a cooldown |
| **a `stats.pairs` cell is low-yield** (judged ≥5 and rate <20%) | **read the `hint` first**: `pair problem` (word and sub are both fine elsewhere) → declare the exclusion with `vibe_keyword_edit`; `word problem` → fix the word (`vibe_keyword_edit`) or try a **narrower word shape** (`closed testing` → `closed testing testers`); `sub problem` → consider dropping the sub (`vibe_subscribe mode=remove`). **Never drop a sub off the bare number**: measured: that nearly deleted 4 subs whose audience was fine. **Only declare when it pays**: it must be ① a `pair problem` (`word problem` → fix the word; `sub problem` → an exclusion cannot help, that needs dropping the sub) ② the cell still has `unclaimed>0` (excluding an already-drained cell buys **nothing**) ③ if `sub_rate_other_kw` sits at 0.2–0.3 **across all words**, that is a uniformly low-yield sub rather than one bad cell: an exclusion cannot fix it; keep it (`delivered>0` means keep) or drop the sub |

**Exhausted (only legal stop)**; delivery still short AND you have already tried, in
order, with verification at each step: score → retire noise → widen/refresh your sub
list (catalog A/B/C) → regenerate face from sd → probe → report. Then report honestly
what you tried and why the ceiling is real (market wording / corpus boundary), and log
it. **No silent stops**: every round ends with "continue toward goal" or "exhausted,
here is the evidence".

#### 4. Act

Execute **one** action. The add/remove itself is **auto-logged per word** (`kw_change_log`:
who/when/which word/what action: you only pass `note` for the reason); then call
`vibe_keyword_edit(...)` to record this round's **decision narrative** (auditable in health).
State the **expect**: what should the next round show if the action worked (e.g.
"regenerated words hit within a pipeline round" / "retired word stops pooling junk" /
"delivered increments by N")?

#### 5. Verify (next round)

Check the expect against the new perceive, then **return to the goal check**:
- Expect met → continue the same direction (same action type)
- Expect failed → **switch strategy**: score → retire → regenerate → probe → corpus:
  don't repeat a failing action
- Delivery still short with directions left → next round continues; only exhausted
  (above) permits `report_exhausted`

**Discipline** (no time cooldowns / daily caps; v2 §5.3):
- one direction action per round (convergence discipline, not throttling)
- verify-gated, not clock-gated: act → see the result → decide next
- **widen the face, don't probe it**: corpus only ever arrives through the sub list:
  `vibe_catalog` to pick subs, `vibe_subscribe` to add them
  (the server queues the fetch), then read `vibe_keywords` hit stats and `pipeline_recent`
  next round. The old `vibe_search_probe` (an agent-triggered synchronous fetch) was
  retired 2026-09-11, so "0 hit" can only be read as *inside your listed subs*: to test
  a phrase elsewhere, add that sub and wait one pipeline round.
- the only hard wait is the ArcticShift rate limit, surfaced via `vibe_doctor`

#### 6. Audit log (per round)

Record each round so decisions are replayable and prompts iterable; ts / sid / round_no /
goal check result / world (raw tool returns, uncropped) / prompt sent / llm_raw / plan /
action / result / verify / cost. Persist it in your own store (exportable JSON). Without
this you cannot answer "why did the agent decide that" or iterate the loop: the log is
core infrastructure, not a post-hoc patch.

## Scoring format (agent calling convention)

```
vibe_leads(subscription_id=12, limit=10)          # peek=true = read-only preview (free, no claim)
    → data.posts: [{"id": 1, "title": "...", "url": "...", "score": system_ref, ...}, ...]
      data.pending: [ … claimed, not yet judged (with id and body) … ]   # the old key data.leads does not exist — don't read it
      progress: {stage, stage_done, round{claimed_now,scored_now,delivered_now},
                 todo{to_score,claimable_now,limits{…}}, next{do,why,args}}
      billing: {"claimed_batch": 10, "free_items": 10, "currency": "usd", "charge": 0.0, "charge_usd": 0.0,
                "claimed_this_month": 10, "claimed_quota": 5000,
                "daily_used": 10, "daily_cap": 1000}
    (limit above tier cap is clamped: free 20 / Starter 30 / Pro 50)

vibe_score(scores=[
    {"id": 1, "verdict": "relevant",   "score": 90, "reason": "directly asking for a solution"},
    {"id": 2, "verdict": "irrelevant", "score": 10, "reason": "unrelated"},
])
    → {"ok": true, "passed": 1, "rejected": 1, "quota_used": 1, "quota_limit": 3000}   # scoring is free
      # batch: {"submitted": 2, "max_batch": 100, "calls": 1, "bucket": "pipeline", "bucket_tokens": 1}
      # items: [{"id": 1, "verdict": "relevant", "delivered_id": 3488}]  ← delivered_id only when judged relevant
      # progress: {stage:"intake", round:{scored_now:2, delivered_now:1},
      #            todo:{to_score:16, claimable_now:34}, next:{do:"vibe_score"|"vibe_leads"|…}}
      # unmarked_delivered: 15   ← sent but outcome not marked (>0 → vibe_leads)
      # Put the WHOLE batch here (up to 100 items): N verdicts in ONE call = ONE pipeline token.
      # Per-item failures land in "errors" as {"index", "id", "code", "err"} and do NOT block the rest.
```

Rules:
- **Billed on the first claim**: `vibe_leads` returns a `billing` block; whichever end claims a lead first pays, the other end reclaims it free; within the monthly allowance it is $0, beyond it the extra is deducted from the wallet of the account's **settlement currency**: USD wallet `$5/1,000` (Starter) / `$3.50/1,000` (Pro), or CNY wallet `¥25/1,000` / `¥18/1,000`. The two wallets are funded separately (Creem tops up USD, WeChat tops up CNY at ¥1 = ¥1) and the user can switch with `vibe_balance`. Telling the user what a claim costs is your job.
- **Scoring is free**: `verdict="relevant"` moves the lead to the delivered list (`vibe_delivered`); unlike the old model, scoring never consumes allowance.
- **Also return `irrelevant`**: that's how the state layer learns your standard: every `irrelevant` verdict downgrades the keyword that produced that lead (pure SQL, server-side). **Your scoring quality drives keyword quality**: score honestly and thoroughly (read the full body, judge on your real buyer profile). Careless or bulk-scored feedback is detected by the consistency guard and weighted down.
- **Daily cap**: Free/Starter 1,000, Pro 3,000 claimed leads/day; when the cap is hit, `vibe_leads` returns `source_status: daily_cap` with "resumes at 00:00"; the leads stay reserved and nothing is lost. This is a throttle, not an allowance: do **not** suggest a top-up for it.
- **Each lead is scored once per claim; `irrelevant` verdicts land in the recycle pool (`vibe_leads`)**; if you later decide one was misjudged (e.g. after opening the post), recover it with `vibe_recover_lead` and re-score.
- **Score what you claim**: your claims accumulate as `pending` (up to 50 unscored **agent** pendings). A `locked` response with a `pending` list is **normal flow, not an error**: score the pending leads (relevant or irrelevant) and claiming continues. Never leave claimed leads unscored for long.
- **The web app is a peer on this same contract, not a separate world**: the user can claim and judge by hand at https://vibedollar.net/app.html: same tools, one verdict per lead. Manual verdicts arrive as `score: 60` (relevant) and `score: 1` (irrelevant), so a human judgement is distinguishable from yours. **The human wins on conflicts** (2026-09-11): verdicts submitted from the web app carry `override=true`, so they rewrite a `delivered`/`rejected` lead you already judged. Conversely, if a lead was judged by that end, your plain (non-override) submission is rejected with `该候选已评分处理过 (不可重复评分)`; **skip that id, submit the rest, don't retry and don't treat it as a failure**.
- **Shared pool, split gate** (2026-09-11): leads the user claimed in the web app but never judged stay claimable by you; a later `vibe_leads` hands them to you (they are **free**: billing happened on the first claim by either end) and they **never expire**, so nothing rots in the user's hands. Only *your* claims expire: `已过期` means one of your claims sat unscored for 7 days: billing already happened and the lead is never re-delivered, which is why claiming what you won't score is worse than not claiming.
- **Save every returned field**: persist the full record per lead (id/title/url/subreddit/score, and body when present). `id` is required later for `vibe_delivered`; don't keep only titles.
- **Bodies arrive with the claim** (server change, 2026-09-11): bodies are no longer pre-stored; they are attached from the corpus store when you claim (`sent` returns it; `delivered` keeps it permanently). For the rare candidate whose source post/comment has already aged out of the corpus store, the server **does not deliver** it (the candidate is dropped from the pool, not billed) and reports the count in `skipped_no_body`: **not an error, no retry needed**: just work with the `posts` you actually received.
- The candidate `score` is a system reference; your judgment wins

## Working with pending candidates (`locked` is normal)

The scoring question for every candidate is always: **is the author of this post a potential customer of the subscribed product?** Judge on topic (does it sit in the problem area the product solves) and signal strength. Answer `relevant` when yes, `irrelevant` when no (irrelevant still teaches the system; scoring costs nothing).

Note the separation of concerns: **claiming is what costs money, scoring is free**. Claim only what you can actually work with: a claimed-but-ignored lead still counts against the allowance.

Note also that the pending list is **shared**: the web app (`app.html` → **To score**) shows the user their own unscored claims, and leads the user never judged come back to you on the next `vibe_leads` (free, and they don't count against your 50-item gate). Whichever end judges first wins, and a web verdict can override yours.

**Full main pipeline (subscribe → claim → judge → outreach → mark → review, with every
step's "response field → next step"); see 「## Main pipeline (one flow: every response
tells you the next call)」 above**: just follow `progress.next.do`. The three easiest to trip on:

1. `vibe_subscribe(product)` needs a **complete description** (name + positioning + target users + website, 40+ chars);
2. save the **whole `vibe_leads` response** (including `billing` and `progress`), don't keep only titles;
3. return pending leads in **one batch** (≤100 items = 1 pipeline token), and right after judging `relevant` follow `progress.next` (or `outreach_next_step.delivered_ids`) to write the draft.

## Local script tools (batch executors: call when the action is mechanical)

The host agent is the decision engine (when/what/why). The scripts below are **pure
executors**: each does one mechanical batch action fast (parallel per-item judging):
far more efficient than hand-writing the loop. Decide when to call one and what to
pass; the script returns structured JSON for the next decision. Scripts do **not**
self-schedule or loop on their own.

**First use**: run with `--dry-run` once to verify key/connectivity before spending
LLM calls (claims candidates only, judges nothing, submits nothing).

### `scripts/score_batch.py`: score one subscription's batch (claim → judge → submit)

| Param | Meaning |
|-------|---------|
| `--sub` | target subscription id (**required**; one sub, one batch) |
| `--limit` | candidates to claim (default 10) |
| `--judge` | path to your judgement template (default `scripts/judge_prompt.md`) |
| `--parallel` | parallel judge lanes (default 8; this is the efficiency win) |
| `--threshold` | score ≥ threshold → `relevant` (default 60) |
| `--out` | evidence dir (optional; relevant rows → csv/jsonl) |
| `--dry-run` | claim only, no LLM / no submit |

```bash
export VIBEDOLLAR_API_KEY=...        # from vibe_register / account page
export LLM_API_KEY=...               # your LLM key
export LLM_BASE_URL=https://api.deepseek.com/v1
export LLM_MODEL=deepseek-chat
python3 scripts/score_batch.py --sub 12 --limit 20 --parallel 8 [--out ./evidence]
```

Returns JSON: `{sub_id, claimed, judged, relevant, submitted, failed, pending[]}`:
read it, then decide next (score another sub, expand keywords, wait).

- **Judgment is yours**: edit `scripts/judge_prompt.md` (plain template) to define what a
  good customer looks like for your market. `--threshold` sets the relevant cut.
- **Costs**: a lead is billed on its first claim (within the monthly allowance it is $0; beyond it
  $5/1,000 Starter or $3.50/1,000 Pro from wallet). Scoring is free; the judging LLM calls
  are billed to **your** key.
- **Failure-safe**: a candidate whose LLM judgment fails is left pending; retried next
  run, never lost. `vibe_leads` returns `locked` with pending ids until they're scored;
  scoring everything you claimed unlocks the next batch.

### `score_batch.py --engine jev`: judge with Jev/TypeSafe (optional)

Default engine is your own chat model (`--engine llm`). With **`--engine jev`** the script calls TypeSafe's.
**⚠️ The questions are written PER SUBSCRIPTION**: `--engine jev` reads `data/jev_<sid>.json` (same family as
`data/sd_<sid>.md`); a missing file **fails with a pointer to `scripts/jev_gen.md`**: deliberately no built-in
default: questions are a function of YOUR demand profile, and borrowing another subscription's questions
(e.g. "is the buyer asking for help getting customers") is simply wrong for a nail-polish or razor product.
The engine only supplies the **generic structure**: several need questions OR-ed (recall) + an optional gate pair
`gate_yes AND NOT gate_no` (for the class you keep missing); the escalation band is any deciding signal in
`[0.3,0.7]`; contract `relevant iff score>=60`. **See `scripts/jev_gen.md` for how to write and validate yours.**
TypeSafe's
System One decision model, asking **two questions in one call** (`is_buyer`, product-relative, plus
`acquisition_ask`, generic) and combining them with an **OR cascade**. Measured against the **finalized
caliber** (2026-09-21; the gold set re-judged by an independent blind pass, old labels and keyword hints
stripped): **high-confidence band 0.921 agreement / 84% precision / 100% recall** (n=38 of 50), overall 0.780.
On **real leads** (n=31) the high-confidence band was **0.952 / 100% precision / 90% recall**; the 3 misses
were milestone/celebration posts sitting in the caliber's borderline band.
What matters is not the headline number but **where the disagreement lands**: 73–80% of it falls inside the
band where your own judge is *also* unsure. So treat Jev as a **pre-filter with routing**, never as the
verdict: let the confident band through automatically, escalate the rest to `judge_prompt` yourself.
(An earlier version of this line claimed "FN=0 / nothing missed". That held only on the **pre-caliber** gold
set; on real leads it is **not** true.)

```bash
export TYPESAFE_API_KEY=...            # your own key (the server never touches it)
python3 score_batch.py --sub 355 --limit 20 --engine jev \
    --record-answers run1.json         # also persist the two answers
python3 score_batch.py --sub 355 --engine jev --replay-answers run1.json   # offline replay (zero API)
```

- **`confidence`**: distance of the strongest evidence from the 0.5 boundary, mapped to [0,1]; submitted via
  `vibe_score`. The server **stores it and never uses it** (no verdict/score/billing effect).
- **`escalate_ids`**: items whose strongest answer lands in the **uncertain band** max(p1,p2) ∈ [0.3,0.7]; re-check them yourself with
  `judge_prompt`. The server will not change your verdict. This is the skill's `confidence-routing` pattern.
- `reason` is a **machine record** (e.g. `[jev] is_buyer=0.90 acquisition_ask=0.10 → relevant`), **not an
  explanation**; Jev does not generate text; the semantic reason is yours to add on the escalated band.
- Key and cost stay on the **consumer** side (BYOK): principle section 3.
### `scripts/mcp.py`: shared MCP client (library, not a CLI)

Import by other local tools: `from mcp import MCPClient`. Not called directly by you.

> **Why scripts, not you writing loops**: batch actions are mechanical (claim N →
> judge each with your LLM → submit). A script parallelises per-item judging and
> returns clean JSON; you stay the decider, the script does the grunt work faster
> than you could by hand-writing the loop each time.

## Setup & tuning prompts (assets; no placeholder replacement, sd is a data doc)

The scoring/judging and keyword-tuning LLM templates live in `scripts/*.md`. They are
**prompt assets**: load the relevant file, call your own LLM with its `sys` content and
a `user` message you build from the subscription's actual data: **the templates carry
no `{placeholders}` and there is no replacement mechanism** (that was the front-end's
JS-string approach; as an agent you read data and compose the user message natively).

**The supply/demand profile is a runtime data document**; not a template variable.
Keep it as `data/sd_<sid>.md` (git-ignored, per-host) so every later step (scoring /
kw_init / kw_opt) reads one file and injects it:

```
# first time / after rebuild — generate sd:
scripts/sd_gen.md        → LLM (product text) → 4 fields
python3 scripts/sd_doc.py write --sub <sid> --json '{...}'   → data/sd_<sid>.md
vibe_subscribe(subscription_id, update_sd={"supply_side":..., "demand_side":..., ...})  # backend copy

# any later step — read + inject (agent's native read; no replace):
python3 scripts/sd_doc.py show --sub <sid> --values   → prints only the 4 field values
   (strip self-describing header — safe to drop straight into an LLM user message)
   (or: vibe_subs → sd_json — same data, backend is authoritative)
```

| Asset | When to load | Produces → persist via |
|---|---|---|
| `scripts/sd_doc.py` | fetch/show/write the sd doc (`data/sd_<sid>.md`); mechanical file ops only | decision (generate/update) stays with you |
| `scripts/sd_gen.md` | Subscription has no sd (no supply_side/demand_side/demand_pain): first setup or after a rebuild | supply/demand four fields → sd_doc.py write + `vibe_subscribe` |
| `scripts/kw_init.md` | Keyword face is empty (initial setup); needs sd doc present first | initial keyword list → `vibe_keyword_edit` (source=auto); dedup vs ALL statuses |
| `scripts/kw_opt.md` | Decision loop says expand / after a retire sweep; needs sd doc + current words (active+monitor rows) | `{add, weak}` → add via `vibe_keyword_edit` (dedup vs ALL statuses; don't revive removed words); weak per decision-table guards |
| `scripts/judge_prompt.md` | Default judge template for `score_batch.py` (editable profile, fixed contract) | per-candidate verdicts → `vibe_score` |
| `scripts/eng_sys_core.md` | **READ-ONLY** scoring core (billing-bound contract). Reference verbatim; never edit | reference for judge alignment |

**Order matters**: sd first, then keywords. `sd_gen.md` makes the demand-side profile
(the buyer language) that `kw_init`/`kw_opt` derive words from and that scoring injects
as `[SUPPLY/DEMAND]`; an empty sd means judging/keywords run on product text alone,
which is exactly how generic words and 0-hit sweeps start.

## Subscription mode (continuous monitoring)

```
vibe_subscribe(product="team wiki tool for small teams")
    → {"ok": true, "subscription_id": 12, "message": "tracking started..."}
vibe_subs()
    → {"ok": true, "data": {"subscriptions": [{"id": 12, "product": "...", "new_leads": 7}]}}
vibe_leads(subscription_id=12, limit=10)
    → {"ok": true, "data": {"posts": [{"id": 1, "title": "...", "url": "...", "subreddit": "...", "score": 90}], "count": 7},
       "billing": {"claimed_batch": 7, "free_items": 7, "billable_items": 0, "currency": "usd", "charge": 0.0, "charge_usd": 0.0,
                   "claimed_this_month": 1207, "claimed_quota": 5000, "over_price_per_1k": 5.0,
                   "daily_used": 87, "daily_cap": 1000, "wallet": 0.0, "wallet": 0.0, "wallet_usd": 0.0}}
vibe_score(scores=[{"id": 1, "verdict": "relevant", "score": 90, "reason": "..."}])
    → {"ok": true, "passed": 1, "quota_used": 1, ...}
```

- For a defined product that needs **continuous** new prospects, not ad-hoc searches
- No keyword/source maintenance by hand: describe the product, we collect + match into the pool; when the face cannot fill the customer's allowance (`assessment.status=shortfall` in `vibe_sub_health`), **you** (your agent) widen the sub list / expand-retire keywords via the health tools; see **Agent decision loop** above
- **A lead is billed on its first claim (by either end); scoring is free**; the subscription itself costs nothing extra
- **Score what you claim**: your claimed leads stay `pending` until scored: after 50 unscored agent pendings, `vibe_leads` returns `locked` with the pending list (ids recoverable, your subscription is never stuck). Scoring them (relevant **or** irrelevant) resumes claiming. Your un-scored claims auto-expire after 7 days; leads the user claimed in the web app never expire and come back to you for free.

Cancel with `vibe_subscribe` (accumulated leads kept).

## Data use cases (downstream; read on need)

Delivered leads, candidates and keywords are also raw material for **customer
interviews**, **first-100-customer outreach**, and **SEO/GEO content**: full
playbooks in `references/use-cases.md` (zh: `references/use-cases.zh-CN.md`).
Read them when the user asks how to turn leads into conversations/customers/content.

## Agent usage tips

- **Lost API key?** Guide recovery: `vibe_account(action="recover_send", email=…)` → `vibe_account(action="recover_verify", email=…, code=…)`; or point to https://vibedollar.net/account.html → "Lost your API key? Recover it". No re-registration needed.
- **Watch the `claim_quota` block**: `vibe_balance()` returns `claim_quota {month_used, month_limit, currency, over_price_per_1k, daily_used, daily_cap, wallet, wallet_usd}` plus `wallets{usd,cny}` and `settlement_currency`: proactively tell the user where they stand (allowance used, daily cap, which wallet overage comes from) instead of letting them discover a charge. If they fund the other currency, point them at `vibe_balance`.
- **Registration & payment flow**: `references/billing.md` (agent does the full flow; the only user actions are providing the email/code and scanning a QR / clicking a link).
- **Typical workflow**: `vibe_subscribe` → `vibe_leads` → your agent scores with its own LLM → `vibe_score` → passed leads in delivered list (validate demand + find first customers).

## Pricing, payment & client config (reference)

Pricing tiers, wallet top-up, the full agent payment/activation workflow, and MCP
client connection config live in `references/`: read them only when needed:

- **Pricing & payment**: read `references/billing.md` when the user asks about price,
  upgrading, topping up, or after payment (confirm activation). Quick checks: call
  `vibe_balance()` for the current tier and `claim_quota` usage (month used/limit, daily cap, wallet).
- **MCP client config**: read `references/mcp-config.md` on first connect or when moving
  to another client (endpoint URL, `Authorization: Bearer <key>` header setup).
