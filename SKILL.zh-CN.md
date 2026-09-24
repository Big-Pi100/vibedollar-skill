---
name: vibedollar
description: "vibedollar 帮助独立开发者找到第一批客户。基于你的产品描述，持续抓取 Reddit 上正在抱怨或求方案的潜在客户线索（帖子与评论），支持订阅持续监控。线索在你**首次领取**时计费；用你自己的 LLM 评分是免费的。远程托管免部署。Free 1,000 条/月；Starter $19/mo（5,000 条）；Pro $79/mo（30,000 条）；也可自由充值钱包额度。"
---

# vibedollar — 帮你找到正在等你的客户

vibedollar 监控 Reddit，找出那些正在主动寻找用户所建产品的帖子和评论，作为评分后的**潜在客户线索**。分工：vibedollar 运行数据服务（Reddit 采集、候选匹配入池、状态层——词表 / 供需判定口径 / 回收 / 健康）；**宿主 agent 决定什么算好客户**——用自带 LLM key 评分候选，并驱动调优（见下文**Agent 决策循环**）。

> **数据源说明**：线索 = **采集时刻公开可见的帖子**的记录。帖子之后可能被平台或作者删除，但历史记录仍是有效的需求信号；作者是可通过 Reddit DM 或其公开联系方式触达的真实个人。使用线索请遵守 Reddit 平台条款与适用法律。

**数据能做什么** —— 完整玩法（访谈 / 前 100 位客户 / SEO-GEO）在 `references/use-cases.zh-CN.md`；简版：
- **客户访谈**：相关帖的作者是最佳访谈对象。
- **前 100 位客户**：需求信号就是客户名单；按"多直接地在求方案"评分，再触达。
- **SEO / GEO 优化**：把客户自己的话用进落地页 / FAQ / 内容。

- [English SKILL](SKILL.md) · [English README](README.md) · [中文 README](README.zh-CN.md) · [Skill 设计规范](SKILL-DESIGN-GUIDE.md)

## 什么时候用它

| 场景 | 用法 |
|------|------|
| 冷启动获客 | `vibe_subscribe` → 系统持续跟踪，线索自动积累，点进帖子直接触达潜在客户 |
| 验证产品点子 | 订阅后看积累的线索：有 N 条强需求信号 → 值得做 |
| 持续获客 | `vibe_subscribe` → 系统持续跟踪，候选自动积累，`vibe_leads` 领候选（首次领取计费）→ 评分免费 → 相关线索进交付 |
| 给投资人/团队证明 | 积累的线索（你评分确认相关的）就是现成的"需求真实性论证" |

## 快速开始

1. **连接服务**（远程托管，无需本地部署）: 在 MCP 客户端添加端点
   `https://mcp.vibedollar.net/mcp`（FastMCP HTTP transport）
2. **注册（仅首次）**: `vibe_register(email)` 发送 6 位验证码；`vibe_verify(email, code)`
   返回 api_key（同时邮件发送）。升级 Starter/Pro 或充值钱包后解锁。完整注册、解锁、
   支付与激活流程见 `references/billing.zh-CN.md`。
3. **配置鉴权 Header**: 把拿到的 key 配到 MCP 客户端请求头（`Authorization: Bearer <key>`；
   若客户端不允许自定义 Authorization 则用 `Api-Key: <key>`）。之后调用数据工具
   **不需要再传 api_key 参数**
4. **查余额/额度**: `vibe_balance()`（key 自动从请求头读取，返回 tier + `claim_quota` 领取额度块：本月已领/额度、每日上限、超出单价、钱包余额）
5. **也支持网页自助注册**：打开 `https://vibedollar.net/account.html` 可完成注册/验证/支付全流程（用户可直接在网页操作，无需配置 MCP）

## 主流程（一条管线 —— 每步的回执告诉你下一步调谁）

服务端是**状态层**: 每个回执都带 `progress` 块 = **当前阶段 + 完成程度 + 下一步工具**。
照 `progress.next.do` 走即可, 不必自己拼"我走到哪一步了"。

```
0 · 启动（一次性 / 重建后）—— **先定搜索面, 再定词表**
  sd_gen.md → vibe_sd_update            供需四段 —— demand_side(人群画像) 与 demand_pain(买家语言)
                                        **不同源**
  → vibe_sub_catalog / vibe_sub_search  找 sub; 锚点词**只能从 demand_side** 提 (服务端不抽词)
  → vibe_sub_list_update(subs, mode)    定搜索面 = 这份显式 sub 清单 (服务端排队取货)
  → kw_init.md (从 sd 推词)  /  kw_mine.md (扫高精度人群 sub 自己的语料)
  → vibe_keyword_add_batch(source=auto)
  ⚠️ 缺 sd 或清单为空 = 每轮在闸门处直接返回, **永远不产出候选**

1 · 运转（每轮 —— 由 progress.next.do 驱动）
  ⚠️ **每轮四件事都要看一遍, 不是一个接一个的流水线**（2026-09-24 修: 原来写成
     "intake 做完才 → 进入 outreach", 实测后果是"sub 355 交付 655 条只有 166 条有草稿"
     —— agent 在 intake 里循环, 草稿那一段被当成"以后的事"）:
  ├─ progress.todo.supply.gate == true     → vibe_keywords（先修词面/清单, 别再领噪声）
  ├─ progress.todo.to_score > 0            → vibe_submit_score（先把手上欠的交回）
  ├─ to_score == 0 且 claimable_now > 0    → vibe_leads（再领一批, 回到判定）
  ├─ **drafts_missing > 0**                → vibe_outreach_advice(delivered_id=progress.next.args.delivered_id)
  │   （触达草稿创作 —— 与 intake **同一轮**做）: 读回执/任务书 → 用**你的 LLM** 写 ≤18 词
  │   → 用**同一个工具** `draft=` 回传落库; 回执的 `draft_check.failed_detail` 不过就按它改一版再交。
  │   每轮能写几条受**写桶**与**冷号节流**约束 (冷号: 每天 ≤2 条 / 同 sub ≤1 条 / 间隔 ≥30 分钟),
  │   写完立刻回传, **不要攒着**。
  └─ 以上都 == 0                            → 本轮 done
  🔁 节奏（2026-09-22 / 2026-09-24）: intake 与 outreach **同一轮内都要推进**;
     gap_reason=shortfall 期间每 30~60 分钟一批, 稳态每天一次 —— 见下面「循环节奏」一节。
发出去之后（写草稿只是第一步）
  ├─ 草稿齐但 sent == 0        → 把草稿**发出去**, 再 vibe_outreach_sent(lead_id) 登记
  ├─ 草稿齐但 sent == 0        → 先把草稿**发出去**; 发出后 vibe_outreach_sent(lead_id) 登记
  │                             (服务端去找你的评论, 找到即自动标 contacted + 起复查时钟;
  │                              也可以什么都不做 —— 监控腿每 6 小时按用户名自动发现)
  │      ⚠️ 口径 (2026-09-23): **声明 ≠ 已发出**。文案一旦交给用户/复制走, 调
  │         vibe_outreach_declare(delivered_id) 只需一次、零网络 —— 线索从"待处理"进
  │         "待确认"(否则队列只进不出); "已发出"仍以**服务端在帖里找到你的评论**为准
  │         (vibe_outreach_sent = 声明 + 立即核对, 没找到就停在待确认, 不会误记已发出)。
  ├─ unmarked_delivered > 0 且 sent > 0 → vibe_mark_leads(outcome=valid|invalid|contacted)
  └─ 两项都为 0                → 回 intake / 复盘

2 · 优化（目标驱动的外循环 —— 插在**运转之间**; 细则见「Agent 决策循环」）
  每轮先做目标检查: vibe_sub_health.assessment → projected_items_month vs commitment_remaining
    ├─ committed_ok → wait（快环在消化, 无需供给动作）
    └─ shortfall    → 按 gap_reason 选**一个**动作:
        supply_ceiling → 扩 / 换 sub 清单
                         (vibe_sub_catalog / vibe_sub_search → vibe_sub_list_update)
        word_face      → 退役噪声词 (vibe_keyword_remove force) 或 **重生成词面**
                         (sd_gen → kw_init / kw_opt / kw_mine → vibe_keyword_add_batch)
        capacity       → 供给侧无事可做（那是每日节流）
        collecting     → alert（采集停 —— 扩词无用）
  act → 写下 expect → 下一轮 verify → 回到目标检查
  只有「穷尽」(评分 → 退役 → 扩清单 → 重生成 → 报告) 才允许停; **静默收尾 = 禁止**。
```

**进入下一阶段的唯一条件是本阶段 `stage_done=true`**（intake = 待评分 0 **且** 可领 0）。
只要还能领, 就还在「领取-判定-交回」的内循环里 —— 不要跳过判定直接去写草稿。

**收尾前必须归零的两处（2026-09-21 实测教训, 别重犯）**:
- `vibe_leads(peek=true)` 的 `data.pending[]` / `data.unjudged_total`（`pending_count_agent` 与
  `to_score` 同口径）= **你手上欠账的权威清单**。收尾就是把它读到 0, 并看到
  `progress.stage_done=true`; 只看到 `drain.unclaimed_total=0`（那只说明「未领取的领完了」）**不算收尾**。
- ⚠️ `vibe_submit_score` 的 `errors[]` 是**逐条**口径: 回执里 `id=A, code=already_scored`
  只说明 **A 这一条**被别处判过。**永远不要**拿它解释 `pending` 里的**另一个 id**（实测: 一个 agent
  把 A 的 `already_scored` 当成 `pending(id=B)` 收不掉的证据, 写进报告说这是「消不掉的计数伪影」,
  于是带着 `to_score=1` 收工 —— 而 B 其实从未被判定, 补一条 `vibe_submit_score` 立刻清零）。
  判不了的真原因只有两种: `not_yours` / `not_claimed`（不是你的 / 没领到）, 或 `already_scored`
  **且报出的 id 就是 `pending` 那一条**。

| # | 步骤 | 调用 | 回执里驱动下一步的字段 |
|---|---|---|---|
| ① | 目标 / 额度 | `vibe_balance` / `vibe_sub_health` | `claim_quota{month_used,month_limit,daily_used,daily_cap}`、`assessment.gap_reason` |
| ② | 领取 | `vibe_leads(subscription_id, limit)`（`peek=true` 免费看**手上的待评分**; **未领取的候选 peek 看不到** —— 没有免费的候选预览, 候选只在领取时返回） | `data.posts[]`、`data.pending[]`、`progress.todo.claimable_now`、`progress.next.do` |
| ②b | **养号行也从这个调用回来** | `vibe_leads(subscription_id=<养号订阅>)` | 行上带 `track_type='warmup'` **与** `warmup: true` → **绝不评分**：直接走 `vibe_warmup_prompt`（见养号一节） |
| ③ | 判定 | `vibe_submit_score(scores=[…])`（≤100 条 = 1 个 pipeline token） | `items[].delivered_id`、`progress.round.scored_now`、`progress.todo.to_score`、`progress.next.do` |
| ④ | 触达 | `vibe_outreach_advice(delivered_id, include_body=true)` → 自己写 ≤18 词 → 同工具 `draft=` 回传。⚠️ **任务书里现在带「同类高互动回复参考」**（同帖 + 你订阅的交付帖池，同社区优先）—— **学它的语气与结构，不要抄内容**，更不要用同样的产品名 | `draft_prompt`、`top_replies`、`draft_check`、`draft_source`、`progress.todo.drafts_missing` |
| ⑤ | 发出并标记 | 发出后 `vibe_outreach_sent(lead_id)` 登记 → 有真实结果后 `vibe_mark_leads(lead_ids, outcome)` | `progress.todo.outreach.sent`（=0 时先别标结果）、`todo.to_mark` |
| ⑥ | 复盘 / 迭代 | `vibe_delivered` / `vibe_keywords` / `vibe_opt_log` | 回到 ① |

**④ 的细节（不做这步 = 该线索在 app 上永远显示"暂无草稿"）**:

1. 判完 `relevant` 后, 回执里 `progress.next.args.delivered_id`（旧字段 `outreach_next_step.delivered_ids`）
   就是这一批的**交付行 id**（用它, 不要用候选 id）;
2. `vibe_outreach_advice(delivered_id=<上面那个 id>, include_body=true)` → 拿 `draft_prompt`
   （写作任务书: 正文摘录 + **这条线索要什么(意图)** + 四层判定 + 该社区规则要点 + 8 条硬约束 + 范例）;
2b. **先看「这条线索要什么」段**（同一份对象也在回执的 `lead_intent` 里, 附判据命中的词）——
   它回答的是**作者是谁**。判成 `soliciting_feedback`（招测试 / 求反馈 / 推广自己作品）时, 作者是
   **做产品的人, 不是用户**: **不要**问「你第一次试的时候哪里不清楚」这类把他当用户的问题
   （这样交稿会被 `intent_fit` 判不通过）; 该给一条**具体第一印象**, 或问**他的做法**。
   任务书还会按意图给该形状的范例（学形状, 不抄句子）;
 2c. **再看「他发这条想要什么」段**（同一份对象在回执 `poster_intent` 里）—— 它回答的是**这个帖子
   此刻想要什么**, 按帖子类型决定"动作":
   · 发布/成果 → 先**肯定他做对的取舍**, 再**顺着他当下的处境给一条下一步**;
   · 求助/提问 → 给**最短最具体的答案**（别把问题反问回去）;
   · 吐槽/情绪 → **共鸣 + 同类经历**（**别给建议**, 那是说教）;
   · 里程碑/自嘲 → **祝贺 / 鼓励**（别做 KPI 分析）;
   · 观点/争论 → **一句明确表态**（别骑墙）。
   纪律: **陈述句为主, 一条回复最多一个问号**; **绝不在发布帖下质疑产品设计**
   （实测 "How are you handling multi-device users who still want sync?" 被版主删了）。
   违反会被 `draft_check.move_fit` 判不通过 —— 四种动作（给答案/给经历/给肯定/给情绪）都可以,
   唯独不该是"考问作者"。
3. 用**你的** LLM 按任务书写一版 **≤18 词**回复（语言看 `lang` 字段, 默认英文）。
   ⚠️ `verdict=dont_reply` 也**要写草稿** —— 分两种, 看 `draft_hold.level`:
   · `account`（`karma_block`/`acct_age_block` 等账号门槛未达, `basis=archive_gate`）:
     **内容能回, 只是你的号现在发不出去/会被拦** → 草稿**照写**并 `draft=` 交稿,
     补齐门槛后再发出（回执带 `draft_warn`, 卡片显示"门槛未达, 草稿先备好"）。
   · `content`（帖子已删/locked/社区禁回等内容级否决）: `draft_allowed=false` 且
     `draft_prompt` 为空 —— 这种写了也没用, 不必写。
4. 用**同一个工具** `draft=<成稿>` 回传 → 服务端按同一套规则复核（≤18 词 / 无链接 / 不推销 /
   不承诺代做）并落库; app 的线索卡片会**优先显示**这一版。
   服务端零 LLM 且**不发通用模板**（通用句与线索无关）—— 草稿只能由你写。

**养号是同一条流水线（2026-09-23）**: `vibe_warmup_subs()` 选一个**实测低移除率**的社区 →
`vibe_warmup_threads(sub=..., limit=20)` 一次拿帖子列表 + 每条**已存的草稿** →
给没草稿的帖写 1-3 句, 用 `vibe_warmup_prompt(sub, post_id, title, body, draft=<成稿>)` 回传落库 →
**用户在 app 的「养号」页点「复制草稿」直接发**（不再复制任务书）→ 发出后
`vibe_warmup_log(sub, post_id, draft, comment_id?)` 记账（带 `comment_id` 服务端会去档案查存活）。
同样零 LLM、不发通用模板、草稿只能由 agent 写; 养号**不受触达节流限制**（那 2 条/天是推广向评论的）。

养号的几条**硬口径**（2026-09-23 一次隔离跑把歧义挖出来之后写死的）:

- **想找「前 1% 最受欢迎的评论者」那类人**: Reddit 的**徽章查不到**（achievement，不在评论字段里），
  但 **`vibe_top_commenters(sub)`** 会用我们手里的**真实赞数**算出这个社区里被点赞最多的作者 + 他们的
  **代表作** —— 这就是同一种人，而且是**你关心的那个社区**里的（比全站徽章更有用）。拿他们的评论当
  **语气参考**（学结构、不要抄句子），或者看他们在哪条帖下出现（那条帖有流量）。
- **记账必须带评论链接/ID（否则没有监控）**: `vibe_warmup_log(..., comment_id=<评论永久链接 或 comment_id>)`
  —— 服务端解析出 comment_id **与帖 id**（链接里的帖 id 是权威）、当场查一次存活/赞数，并把它放进
  **监控名单**；`vibe_warmup_logged(sub?, days?)` 就是那份名单（已发清单：存活/赞数/有人回/复查次数/链接）。
  `draft` 可以不给（服务端用这条帖已存的草稿补）。app 养号页的「我已发」框就是这个调用 —— 往里面
  **粘链接**，不是粘评论正文。
- **发出去会被监控（和触达一样）**: `vibe_warmup_log` 带上 `comment_id` → 服务端**每 6 小时复查**一轮
  存活 / 赞数（评论赞 ≈ karma）/ 有没有人回（最近 7 天）；`vibe_warmup_subs(recheck=true)` 可**立刻复查**。
  回执 `effect{logged, alive_rate, score_sum, replies_sum, by_sub[], best[]}` = 养号效果账；app 的养号卡片上
  「我已发」会变成「已记录 · 存活 +3」这种带状态与赞数的标签。**没带 `comment_id` 的记账查不了证** ——
  想被监控就必须带上那条评论的 id。
- **列表是「最新帖」**: 打开一个养号社区时, 服务端按 **TTL(10 分钟)** 增量拉一次**真·最新帖**再返回 ——
  不拉的话卡片还是几周前的调研快照, 那种帖子没人看, 评论上去也**攒不到 karma**。排序写死: **有草稿的在前 → 新的在前**,
  每行带 `age_h`; `force=true` 跳过 TTL(界面点「刷新」就是它)。
- **列表带正文**: `vibe_warmup_threads` 每行给 `title` **和 `body` 摘要**(1200 字) —— 把 body 一起传给
  `vibe_warmup_prompt`, 任务书里才有「这条帖子的事实」。只凭标题写稿 = 泛泛而谈。
- **交稿有复核**: `vibe_warmup_prompt(..., draft=)` 回执带 `draft_check`(bool) 与 `failed_detail[{k,hit,note}]`
  —— 确定性检查(链接/产品名/推销/套话开头/复述标题/超 3 句), **只报命中, 不拦截落库**。命中就改一版再交。
- **存稿 ≠ 今天发完**: 每天 **3-5 条**, **分散到 2-3 个社区**, 同一个社区连发要隔开 **30 分钟**以上。
  `next.why` 里的「N 条还没草稿」不是让你写满 —— 只写你真有话说的那几条。
- **选哪个社区**: `vibe_warmup_subs` 按**实测评论移除率**升序排, 并列时按固定的人工清单顺序(问答类在前);
  回执直接给 `pick`(推荐的社区 + 理由)。要发多条就顺着 `subs` 往下取, 别都发在同一个社区。
- **两套档位别混读**: `vibe_warmup_subs.data.tier` = `t0/t1/t2` 是**养号档位**(按 karma/账号年龄),
  `rate.tier` = `free/starter/pro` 是**计费档位**; 回执里的 `tier_note` 就是在说这件事。
- **和 `vibe_account_ramp` 的分工**: `vibe_warmup_subs`/`vibe_warmup_*` = 在**没有门槛的社区**攒 karma(与线索池
  完全无关); `vibe_account_ramp(subscription_id)` = 体检**你自己的线索社区**能不能发帖(门槛差多少/多久)。
  先养号攒 karma, 够了再用 account_ramp 看推广社区。
- **养号现在是一条订阅**（2026-09-24）: 它作为**独立条目出现在左侧栏**（`track_type='warmup'`, **默认开**,
  社区 = 我们实测的低移除率清单），并且能像其它订阅一样**暂停 / 取消** —— 暂停后既不发帖单也不再复查。
  **配额**: 包含在所有档（免费档也能开），并**占用你的 leads 配额 —— 发出 1 条评论 = 1 条 lead**；
  计费点在 `vibe_warmup_log`，所以**从 `vibe_leads` 领取养号行是免费的**（别把养号行当成已计费线索）。
  节奏不变：**每天最多 5 条**，分散到 2-3 个社区。
- **暂停 / 恢复养号**: 它现在是一条**订阅**, 所以能停也能回来 —— `vibe_warmup_status(enabled=false)` →
  状态 `paused`（不再发帖单、也不再复查；**已发出的评论仍在监控名单里**）,
  `enabled=true` → 回到 `active`。app 的养号页右上角有「暂停养号 / 恢复养号」按钮。
  注意: `vibe_unsubscribe` 写的是 `cancelled`（另一种状态）—— 想回来用这个工具。
- **养号行会从 `vibe_leads` 回来**: 行上带 `track_type='warmup'` 与 `warmup: true`。它们是**用来攒 karma 的帖子**,
  不是需求线索：**不要**评分（它们不进「未判定」闸门）、**不要**写触达草稿 —— 用
  `vibe_warmup_prompt(sub, post_id, title, body, draft=)` 写一句像普通用户的话，再用 `vibe_warmup_log` 记账。
- **台账语义**: `vibe_warmup_log` 记的是**已发出**; 不带 `comment_id` 也照记(算进今天条数), 带的话服务端会去
  档案查存活。养号评论**不进**触达熔断(那条 48 小时熔断只数触达评论), 但被删同样是信号 —— 换社区/换写法。

### 冷启动：**先定搜索面**，再谈词表（2026-09-21）

`vibe_subscribe` 之后**缺词表或 sub 清单 = 管线每轮在闸门处直接返回 → 永远不会产出候选**
（回执里 `setup.config_missing` / `source_status=config_missing`）。这**不是**「在跑但这一轮没料」。

- 匹配**只在你的 sub 清单内的语料里跑**（v2.2 彻底 sub 锚点）—— 清单为空，词表再好也是 0 候选。
  所以空搜索面时 `progress.next.do` 直接指向 `vibe_sub_list_update`、`todo.face.config_missing=true`、
  `next.args.audience_profile` / `demand_pain` 把两段原文**原样**给你（服务端**不抽词、不给候选词** —— 锚点词由你自己提，也可以直接问客户要 sub）、
  且 `stage_done=false`（阶段不可能走完）。
- **⚠️ sub 锚点词与帖子搜索词不同源（最容易搞错的一步）**：sub 是按**行业 / 人群 / 兴趣 /
  话题**区分的 —— 所以锚点词只能从 `sd_json.demand_side`（**目标人群画像**）来，例如
  `lawn care operators` / `SaaS founders` / `indie hackers`。而 `demand_pain` 是**作者会说的话**
  （第一人称痛点，如 `how do I get my first customers`）—— 那是**帖子 / 评论的搜索词**，
  **绝不能**拿它当 sub 定位词（`first customers` 不可能是任何 sub 的定位）。
  回执的 `next.args` 把两段原文与来源都给你（`audience_profile` / `demand_pain` /
  `anchor_words_from` / `keyword_words_from`）—— **词由你自己定**，服务端只给原料。
- **怎么搜目录**：`vibe_sub_catalog(query=<人群/行业短词>)` ——
  无 query → **A 面**：真实 `relevant` 交付过的 sub（库内已有货，加入清单立即可搜）；
  带 query → **B/C 面**：名录按 **sub 名 + 简介**词法匹配（可能需取货）。要更全用
  `vibe_sub_search(query, sort)`（全量目录 + 分页 + **相关度优先**：先 `name_hits`(名字就叫这个)
  再 `rules_hits`(规则原文写着这个) 最后 `desc_hits`，所以用**短领域词**而不是整句产品描述；
  排序里 `name_hits` 最高的那条通常就是你要锚的 sub）。
- **判定位看 rules 原文，不是看简介**：每条候选带 `rules[]`（`{short_name, description, priority}`，
  版主写的原始规则）与 `submit_text`。例如 `r/buildinpublic` 的 *Stay on Topic: All posts should
  be related to "building in public" … Off-topic content will be removed* —— 一句话就是这个 sub
  的定位。⚠️ `rules_missing=true` = **问过 rules API 但 Reddit 侧没有公开规则**，不等于这个 sub
  没限制；`rules_available=false` 时退回 `description` / `submit_text` 判。
- **确认「这个 sub 的人就是 demand_side」—— 读它的语料, 别只信交付率**: 交付率是
  **(sub × 你当时的判定口径)** 的函数, 不是 sub 的性质。实测 2026-09-21: `r/alphaandbetausers`
  在旧口径下 **3.2%** (7/220) 被移出清单; 口径修正 + 重判 213 条历史后是 **95%** (209/220) ——
  全订阅最对口的 sub。所以 (a) **口径变更后 per-sub 历史必须重算**才能拿来决策;
  (b) `n<10` 本来就不够下结论。与口径无关的确认法是**读他们自己写的话**:
  `vibe_sub_corpus(sub=<候选>, limit=200)` —— 标题若成片是"我在招第一批用户/测试者",
  这个 sub 的人群就是你的 demand_side (`r/alphaandbetausers`: 3417 帖里 `beta testers` 出现 390 次)。
  这一步不看任何评分结果, 也不受口径影响。
- **写完就迭代，不要一次拍死**：`vibe_sub_list_update(subscription_id, subs=[…], mode="replace")`
  （也可 `add` / `remove`）→ 之后每轮看 `todo.supply.stats.subs`（每个 sub 的入池/交付/拒绝/**交付率**/
  未领取 + `in_list`）与 `gap_reason=supply_ceiling`：0 交付的移出，候选补进来。
- ⚠️ **存量订阅的初始清单是 `source=backfill` 的历史命中面**（v2.2 上线时按「过去碰巧搜到过的 sub」
  回填）—— 它是**起点，不是终点**：首轮就该 review 一遍（保留有货 / 删噪声 / 加 B/C 候选）。
- 服务端零 LLM：**不代生成清单，也不代生成词表**（候选与证据全给你，决定归你）。
### `progress` 块字段（回执同构；本工具不涉及该阶段时不出现）

```json
"progress": {
  "stage": "intake",              // intake(领取→判定→交回) | outreach(触达)
  "stage_index": 1, "stage_total": 2, "stage_label": "领取 → 判定 → 交回",
  "stage_done": false,            // true = 本阶段走完, 可以进下一阶段
  "round": {"claimed_now": 2, "scored_now": 0, "delivered_now": 0},
  "todo": {"to_score": 18, "to_score_web": 0, "to_score_by_sub": {"400": 18},
           "claimable_now": 32,
           "limits": {"pool_available": 57, "daily_left": 988,
                      "quota_left": 793, "gate_left": 32, "gate_limit": 50}},
  "summary": "本阶段(领取 → 判定 → 交回) 本轮: 领 2 / 判 0 / 交付 0; 还差: 待评分 18, 可领 32",
  "next": {"do": "vibe_submit_score", "why": "…", "args": {"n_items": 18}, "gate": "…"}
}
```

- `claimable_now` = min(池里可立即领的 / 今日剩余 / 月额度剩余+钱包可负担的超额 / 闸门剩余);
  **四项都在 `limits` 里分列** —— 0 是哪一项造成的必须看清（闸门满 ≠ 没货）。
- **`to_score` 是账号口径**（闸门只按 API key 数），而 `vibe_leads(peek=true)` 的待评分清单是
  **逐订阅**的 —— 所以用 `todo.to_score_by_sub`（或 `next.args.subscription_ids`）找出欠在哪个订阅，
  逐个 `peek` → 判定 → 一次批量交回；**所有订阅合计清零**才会 `stage_done=true`（否则阶段永远进不去）。
- **回灌门（供给侧闭环）**: 判定会写回词级计数（`n_rejected` / `avg_score`）与 `scoring_feedback`；
  但**回灌 ≠ 自动动作** —— 停词/移 sub 由你决定, 而且停词只影响**今后匹配**: 池里已匹配好的
  旧货照样会被领出来（实测: `revenue` 词停用后, 停用前入池的 36 条仍被领出）。
  证据够了（某词/sub 判过 ≥10 条且噪声率 ≥90%, 或本批 ≥5 条且 ≥80% 判无关）回执会置
  `todo.supply.gate=true` 并给出 `noise_kw` / `noise_subs`, `next.do` 改指 `vibe_keywords`:
  **噪声率高 ≠ 退役令**: 退役建议**只给零交付的项** —— 已经交付过的词/sub 说明它产出过买家, 只作为
  证据列出并带 `zero_delivered:false`, `why` 会明说**不建议停**（与决策表一致: `delivered>0`
  永不自停, flagging weak 只等于"观察"）。**看那一行, 不要只看比率** —— 一个词可以 90% 噪声同时
  是你最好的供给源（实测: `beta users` `410/454` 噪声但**交付了 44 条**, 差点被停掉）。
  **交付率与清单管理历史也一并给你**（不是替你决定）: `todo.supply.stats.subs` / `.kw` / **`.pairs`** = 每个
  sub / 词 / **（词 × sub）组合** 的入池·交付·拒绝·**交付率**·未领取 —— `.pairs` 是关键的一层: **同一个词能在一个 sub
  95%、在另一个 sub 0%**（实测 `closed testing` 全局 95% / 在 `b2bmarketing` 13%），所以低精度要先看是哪一层的问题。
  每格带 `kw_rate_elsewhere`（该词扣掉本格后在**别的 sub** 的交付率）、`sub_rate_other_kw`（该 sub 用别的词时的交付率）
  与 `hint`（**配对问题** = 词与 sub 各自在别处都不错, 只有这个组合差 / **词面问题** / **sub 问题** / **词与 sub 都差**（两个都低产, 停词救不了）/ **None**（**对照样本不足, 不给归因**）——
  阈值全写死在这行自带的数据里, **可自行复算**: 本格判过 ≥5 且交付率 <0.20 才算低产; 
  `kw_rate_elsewhere` / `sub_rate_other_kw` 是**扣掉本格**后的别处率, 且要看 `kw_elsewhere_judged` / 
  `sub_other_kw_judged` **≥5 才配下结论**; ≥0.40 才算「在别处还行」）——
  `hint` 是**确定性分类, 只是提示**: 服务端不据此停词/移 sub/排除任何格。也可以先试**更窄的词形**
  (`closed testing` → `closed testing testers`) 再谈排除。每个 sub / 词的后面还有: `每个
  sub / 词的入池·交付·拒绝·**交付率**·未领取 + `in_list`（是否仍在搜索面）+ `list_added_at` /
  `list_source`; `stats.sub_history` = 该清单的 add/remove/replace 流水（谁·何时·为什么,
  与 `kw_change_log` 同款、**自动留痕**, 你只要传 `note`）; `stats.low_yield` = 判过 ≥5 且
  交付率 <20% 的 sub / 词 —— **这只是同一份数据的另一种排法, 不是门**: 收不收由你定。
  `gate` 同样只是证据 + 建议（`override_allowed: true`）—— 你也可以照常领取。
  **但注意边界**: 供给侧收噪声（停词 / 移 sub / 清旧库存）**是 agent 的活, 不是等人批准的事** ——
  服务端只给数据与入口（`todo.supply.stats` + 三个工具）。只有这四类才需要先问人: **花钱 / 改计费口径 /
  发帖发信 / 删除已计费历史**。实测教训（355）: 门开着时如果 agent 只是报告并等, 噪声会一直被领出来 ——
  该做的是当场 `vibe_keyword_remove(force=true, note=理由)`（自带清库存）/
  `vibe_sub_list_update(mode="remove")` / `vibe_pool_purge(...)`（留词清库存）, 再 `vibe_opt_log` 记账。
  要动手时: 先 `vibe_keyword_remove(kw, force=true, note=理由)`（**会自动清掉该词未领取的旧库存**,
  回执里 `pool_purged` 是条数）/ `vibe_sub_list_update(subs, mode="remove")`, 再
  `vibe_opt_log` 记一笔, 然后回内循环继续领。
- **结果回填（客观证据服务端给, 判定你来做）**: 监控腿按 T+24h/72h/7d 自动复查你发出去的回复 ——
  存活 / 被删 / 自删 / 赞数 / **有人回**。回执里同时给两样: `todo.outreach{sent,alive,removed,
  replied,reply_rate,replied_ids,last_checked_at}`（客观证据）与 `todo.to_mark{n,delivered_ids,
  outcome_legend}`（还剩多少条没标 + 具体 id）。草稿写完后 `next.do` 会指向
  `vibe_mark_leads`（outcome = valid | invalid | contacted）—— **有人回 = 强有效信号**, 但
  valid/成交仍由你判。判定"不该回"的条目（如 karma 不够）会被标 `draft_skip`, 它们
  **不会卡住流程**（`todo.vetoed_n` 单列）, 而 `drafts_missing` 口径不变。
  客户端要看的价值证据在 `vibe_delivered` 的 `outreach_stats`（已发 → 存活 → 有人回 → 回复率）。
- **`next` 只是"当前最优的一个", 不是"只有这一件欠账"**: 回执会同时给 `next.alternatives`
  （其余还欠着的事, 如"46 条交付没草稿 / 50 条还能领"）—— 服务端并列事实, 取舍仍是你。
- **触达欠账按订阅统计**: `todo.outreach_scope`（`subscription 355` 或 `account`）标明口径;
  账号口径时 `todo.outreach_by_sub` 把欠账摊到各订阅（哪个订阅欠多少草稿/多少没标）。
  （实测教训: 账号口径会让人在 sub 355 上看到别的订阅的 122 条欠稿, 并把别人的 delivered_id
  塞进 `next.args`。）
- **回执字段速查（干净 agent 实测补全, 都有实测出处）**:
  · `data.billing`（**在 `data` 里**, 不是顶层）: `billable_items` = 本次**首次领取**条目数（计费基数, 含额度内免费的）; `charged_items` = 真扣钱的条数; `free_items` = 其中免费; `takeover_items` = 他端已计费本次免费领回。三个数同时在是正常的, 看 `billing_note`。
  · 候选可能**没有**系统预评分: `score: null` + `prescored: false`（此时 `score_note` 会明说「本批无系统预评分」）—— 旧文案说「含系统参考分」, 以 `score_note` 为准。
  · `vibe_delivered` 每行现在带 `has_draft` / `draft_len`（**逐行判断缺草稿不用再扇出 advice**）、`draft_skip`、`outreach_state`、`outreach_replies_n`。
  · `todo.to_mark.delivered_ids` 每次最多 20 个, 超过时 `ids_truncated: true` + `ids_limit: 20`。
  · **karma 不够 / 养号**: 先调 `vibe_account_ramp(subscription_id)` —— 它把 17 个社区分成「现在就能发」/「门槛差 N」/「门槛未知」/「实测被删过」，并给目标 karma、还差多少、按 5-15 karma/天估的天数。**服务端不代养号**（不代发/不刷），养号=本人在真实对话里持续提供价值；攒到门槛后再更新 `vibe_outreach_profile`（会自动记快照，`karma_trend` 看曲线）。
  · `publish_verdict` = 「我这个账号在这个社区发得出去吗」(与 verdict 是两个问题)。**平台级先验 (新号/低 karma) 只是建议**（`prior.advisory=true`, `basis=platform_prior_advisory`）—— 它不是该社区归档里的规则; 实测同账号在多个社区发评论**并未被删**。会 `hold`/`no` 的只有**有证据**的情形: 账号没填 / 归档门槛抽不到数值 / 归档门槛确实不达标（`blocks: karma_block|acct_age_block`）。所以草稿写好后**可以先在小社区试水**，别被先验吓住。
  · `vibe_delivered` 每行同时给 `id` 与 `delivered_id`（同一个值）—— 别的回执都叫 `delivered_id`, 免得喂错。
  · `draft_check` 失败时除 `failed` 还给 `failed_detail[{k,hit,note}]` —— **命中片段**直接告诉你哪个词踩线。
  · 草稿三字段: `draft_stored` = 库里现在有没有稿（权威）; `draft_written` = **本次调用**是否写入; `draft_saved` 是 `draft_written` 的兼容别名（同值, 已弃用）。读回一条已有草稿的条目时三者是 `stored=true / written=false / saved=false` —— **不矛盾**。
  · `next.advisory: true` = 这条 next 是**供给侧建议**（回灌门）: 停词/移 sub 不在你的职责范围时, 直接按 `next.alternatives` 继续领取即可, 服务端不拦。
  · `progress` 的**路径**: `vibe_leads` 在 `data.progress`; `vibe_submit_score` 与 `vibe_outreach_advice` 在**顶层** `progress`（历史原因, 两种都按文档写的位置读）。
  · `vibe_leads(peek=true)` 只回**已领取未判定**的清单（`pending`）; 未领取的候选不在 peek 里（`posts=[]`, 用 `pool_stats.new` 看库存）—— 领取才会拿到候选。
  · `vibe_outreach_sent` 找不到评论时只记 `outreach_state=unknown`（**不会**写 outcome —— 没找到评论就没有"已触达"）; 真找到才会自动标 `contacted`。
  · `progress` 只挂在**三个管道工具**上（`vibe_leads` / `vibe_submit_score` / `vibe_outreach_advice`）; 其余只读工具（`vibe_balance`/`vibe_delivered`/`vibe_sub_delivery` 等）各自返回自己的数据面, 不带 progress。
  · `next` 若超出你的职责/授权（例如停词、移 sub、替客户发布）——**换个手**: 按 `next.alternatives` 走（通常是继续领取）或交给负责人; 服务端**从不拦**你领取。`next.advisory: true` = 这条 next 是建议（供给侧回灌门）; `alternatives` 里**不会**在你还没发出任何东西时推 `vibe_mark_leads`（sent=0 时改成推 `vibe_outreach_sent`）。
  · **id 速查（实测踩过三次, 现在交付类工具两种 id 都认）**: `delivered_id`（交付行 id, 回执里的 `delivered_ids`）是 `vibe_delivered` / `vibe_get_delivered` / `vibe_outreach_advice` / `vibe_outreach_sent` / `vibe_mark_leads` 的**推荐参数**; 候选 id（`lead_pool.id`, 7 位, 回执里的 `lead_ids`）只给 `vibe_submit_score` / `vibe_recover_lead` 用 —— 但交付类工具现在也接受它（内部自动映射）, 传错不会静默失败。
  · `vibe_get_delivered(lead_id|delivered_id)` 两种都认, 并返回 `has_draft`/`draft_len`; `vibe_mark_leads` 解析不到的 id 会在 `unresolved_ids` 里显式列出（不再静默 `updated=0`）。
  · `vibe_submit_score` 回执里的 `unmarked_delivered` 是**账号口径**（带 `unmarked_delivered_scope: account`）; 本次涉及订阅的欠账看 `progress.todo.to_mark`（带 `scope` 与 id 清单）。
- 触达阶段的 `todo`: `drafts_missing` / `drafts_open` / `vetoed_n` / `drafts_written` /
  `unmarked_delivered` / `to_mark` / `outreach` / `delivered_total`。
- 语言与口径提示（`lang` / `lang_source` / `sd_missing`）与进度块并存, 各管一摊。

### 需求侧回执字段 → 你的动作（对齐 §2 供给侧那张表）

| 回执字段 | 含义 | 你的动作 |
|---|---|---|
| `progress.next.do` | 服务端按当前阶段算出的下一个工具 | **直接调它**（本管线的主驱动） |
| `progress.todo.to_score` | 已领取未判定（闸门口径, 只数 agent 领的） | >0 → `vibe_submit_score`（一次批量回传） |
| `progress.todo.claimable_now` | 现在真能领多少（四项取最小） | >0 且 to_score=0 → `vibe_leads` 再领一批 |
| `progress.todo.limits.*` | 可领数被哪一项卡住（池/日/额度/闸门） | 对症: 闸门→先判定; 池→等采集/扩清单; 额度→`vibe_balance` |
| `items[].delivered_id` | 本次判 relevant 的交付行 id | 传给 `vibe_outreach_advice`（**不是**候选 id） |
| `unmarked_delivered` | 已发出但没标结果的条数 | >0 → `vibe_mark_leads(outcome=…)` |
| `data.source_status` | `ok` / `pending` / `locked` / `waiting` / `exhausted` / `config_missing` | 只有 `ok` 有新货; `locked` → 先判定; `config_missing` → 按 `next_steps` 补配置 |
| `billing{claimed_batch,billable_items,charge…}` | 本批领取计费（首领即计费） | 告知用户成本; 超额度从结算币种钱包扣 |
| `data.lang` / `lang_source` | 该订阅的判定与草稿语言 | 供需四段、判定理由、草稿都照它写 |

## 可用工具

| 工具 | 参数 | 说明 | 成本 | 鉴权 |
|------|------|------|------|------|
| `vibe_register` | `email` | 注册第 1 步: 发送 6 位邮箱验证码 | 免费 | 无需 |
| `vibe_verify` | `email, code` | 注册第 2 步: 验证码验证, 返回 api_key（同时邮件发送） | 免费 | 无需 |
| `vibe_balance` | `（无）` | 查余额/tier/**双钱包**（`wallets{usd,cny}`）/结算币种/`claim_quota` 领取额度（key 走 Header） | 免费 | Header |
| `vibe_set_currency` | `currency`（`usd` \| `cny` \| 空=自动） | 选**结算币种**：决定超量从哪个钱包扣（美元钱包 $5/$3.5 每千条 · 人民币钱包 ¥25/¥18 每千条） | 免费 | Header |
| `vibe_subscribe` | `product`, `enable_competitor_kw`(可选), `track_type`(可选) | **订阅持续监控**：输入产品描述，系统持续抓取匹配入池（词表由你的 agent 按决策循环扩/停——见"Agent 决策循环"）。**产品描述必须完整（40+ 字）**：名称 + 一句定位 + 目标用户 + 网站 URL。过短描述会生成泛词与低相关候选，会被拒绝。`enable_competitor_kw`（默认开）：设 `false` 只收直接需求线索，排除竞品对比帖。`track_type`（内部用：outreach/seo/hot_content） | 免费（订阅本身不收费；线索在领取时计费） | Header |
| `vibe_leads` | `subscription_id, limit, source, peek` | **领取线索（按首次领取计费）**：返回线索（含系统参考分）+ **`billing` 记账块**；每条还带 `track_type`（`outreach` / `warmup`）—— **养号行（`warmup: true`）领取不计费、也绝不评分**（它们的评论走 `vibe_warmup_prompt`）（本批条数、免费/计费拆分、`billable_items`/`takeover_items`、扣费、本月用量、每日上限）。`peek=true` = **纯只读预览**（不领取/不计费/不改归属, 字段带 `claimed_by`）—— 看的是**手上已领未判**的清单（**不是**未领取候选; 没有免费的候选预览）。回执还回显 `requested_limit` / `limit_applied` / `limit_clamped`（超档位会被夹到 free 20 / starter 30 / pro 50）。**单次上限：free 20 / Starter 30 / Pro 50 条**（实际返回 = min(limit, 档位上限)）。回执带 `progress`（阶段/完成程度/下一步）。响应含 `posts`（新线索）、`pending`（已领未评分，含 `id`）与 `source_status: locked`（你未评分的待处理累积到 50 条时暂停领取；`daily_cap` = 当日上限已满、次日自动继续）。`source`（**2026-09-11**）：`agent`（默认）或 `web` —— 网页端用 `source='web'` 领取，它未评分的条**不占**你的 50 条闸门，且你可以自己领回（**免费**，首领已计费）；你带 `source='web'` 时会把你自己未评的条目原样回吐给你（不放新货、不计费）。见下方"待处理候选" | **首领即计费**（两端任一端首次领取） | Header |
| `vibe_submit_score` | `scores, override` | **评分回传（免费）**：`relevant` 进交付列表，`irrelevant` 回灌优化。**评分不影响计费**。`override=true`（**2026-09-11**）受理已被判过 `delivered`/`rejected` 的条目并**以本次判定为准**（relevant→irrelevant 会**撤回**交付记录，当月交付数随之回正），响应里 `overridden` 为实际翻转条数；人在网页端推翻你的判定时用得上。不带 `override` 时仍拒收已评分条目 | **免费** | Header |
| `vibe_score_discuss` | `limit, respond_id, response` | **评分分歧对齐（可选）**：查看你与系统参考评分不一致的候选，可说明你的理由——我们据此校准标准，推送更贴合你的判断 | 免费 | Header |
| `vibe_set_notify` | `enabled` | 邮件提醒开关：候选积压时是否发邮件通知你（默认开启，可关闭）| 免费 | Header |
| `vibe_list_subs` | `（无）` | 查看我的订阅列表及候选线索积累状态 | 免费 | Header |
| `vibe_unsubscribe` | `subscription_id` | 取消订阅（已积累的线索保留） | 免费 | Header |
| `vibe_cancel_plan`（指引） | — | **付费档位（Starter/Pro）通过支付平台取消**（Creem 客户门户 / 微信支付管理），不走本 API。取消后档位保留到当期结束再降级 free；已领取的线索保留。产品订阅用 `vibe_unsubscribe` 取消 | 免费 | Header |
| `vibe_pair_exclude` | `subscription_id`, `kw`, `sub`, `mode`(list/add/remove), `note` | **声明「这个词，但不要在那个 sub」——（词 × sub）排除格（2026-09-21）**。搜索面是（词表 × 清单）的**笛卡尔积**，而质量信号是 per（词, sub）——实测**同一个词能在一个 sub 95%、在另一个 sub 0%**。**服务端只执行不决策**：证据看 `todo.supply.stats.pairs` 的 `hint`（配对问题/词面问题/sub 问题），排除格由你声明。`mode=list` 纯读（read 桶），add/remove 走写桶；撤销是软删；生效在入池前（**写 scored_posts 之前**，撤销后可重新考虑） | 免费 |
| `vibe_pool_purge` | `subscription_id`, `kw`(可选), `sub`(可选), `out_of_scope`(默认 false), `dry_run`(默认 true) | **清未领取库存**（`status='new'`，从未计费 → 删除**零账目影响**；`sent/delivered/rejected` 一律不动）。供给侧收噪声的第三个动作：**想留的词**其旧库存会垄断领取轮转，**已移出清单的 sub** 的存量行仍能被领出来 —— 这两种都只能靠它清。先 `dry_run=true` 看会删多少 + 抽样，再 `dry_run=false`；做完 `vibe_opt_log` 记一笔 | 免费 | Header |
| `vibe_account_ramp` | `subscription_id`(可选) | **账号养号体检 + 路线（只读, 零 LLM）**：量出**门槛差多少**、**哪些社区现在就能发**、**大约多久**。逐社区判定：`postable`（无已归档门槛且本账号未被删）· `gate_unmet`（有数值门槛未达 + `gap`）· `gate_unknown`（归档只说有门槛没给数值）· `self_removed`（**本账号实测被删过**，比归档更硬）· `high_removal`。回执给 `plan{postable_now, ramp_first, target_karma, karma_gap, eta_days, steps}` 与 `next`；每次更新 `vibe_outreach_profile` 会记 karma 快照，`karma_trend` 看趋势。**边界：服务端不代养号**（不代发/不代评/不刷 karma —— 那是 spam），养号只能由本人在真实对话里做 | 免费 | Header |
| `vibe_outreach_declare` | `delivered_id` | **声明已发（零网络）**：复制草稿后调它 → 线索从「待处理」进「待确认」；**声明 ≠ 已发出**，只有服务端在帖里确认到你的评论才算（见 `vibe_outreach_confirm_link`） | 免费 | Header |
| `vibe_outreach_confirm_link` | `delivered_id`, `permalink` | **贴回复链接确认触达**：回复被 Reddit 删掉时作者会变 `[deleted]`，按用户名永远认不出 —— 这时把那条回复的**永久链接**贴进来，服务端按 comment_id 查证（存在性 + 帖归属）后登记为已发出 | 免费 | Header |
| `vibe_commenter_profile` | `author`, `focus_sub`(可选), `limit`(默认 100) | **某个人在哪些社区活跃**：`our_corpus`（我们采集过的社区里的条数/赞数 + 代表作）+ `archive`（**档案里他最近 ≤100 条评论按社区聚合** = 真实活跃面）。传 `focus_sub` 给 **常驻(≥30%) / 兼有(10-30%) / 路过(<10%)** 的确定性判定 —— **学语气要挑目标社区的常驻写手**：实测 r/Accounting 的 `Helpful_Dev` 主战场其实是 r/Warhammer、r/3Dprinting（Accounting 只占 11%），属路过型高手 | 免费 | Header |
| `vibe_top_commenters` | `sub`, `limit`(默认 20), `min_n`(默认 3), `sort`(total/avg，默认 total), `min_avg`(默认 0), `include_bots`(默认 false) | **社区头部评论者**（按我们手里的**真实赞数**）：该 sub 内条数 ≥ `min_n` 的作者按**总赞数**排，每人再给一条**代表作**（原文片段 + 链接）+ 条数/总赞/均赞/最高赞。用途：①学这个社区**最会说话的人**（学语气、不抄内容）②看**哪条帖有流量**（这些人出现在哪条帖下）。⚠️ Reddit 的「前 1% 评论者」**徽章本身查不到**（那是 achievement，不在评论对象字段里；实测档案原始行零命中）——这里给的是**行为等价物**，而且是你关心的那个社区里的。**边界**：只给公开事实，**不提供 DM 名单、不代发、不判断该不该联系**（批量私信 = spam）。**这份达人参考已经真的进任务书了**：触达的 `draft_prompt` 与养号任务书里都有一段「这个社区里写得最好的人是怎么说话的」（默认 ≤14 条，**轮转取满**——保证每位被选中的达人都出现）。**养号社区常常选不出人**（我们库里它们的评论很少、且多数 0 赞）→ 按下面规则换成**同类目养号社区**的达人，任务书里会标「[来自同类社区 r/X]」。**选人（每个 sub 各自选，看平均值 + 剔偶发爆款）**：选人键是**该 sub 内的中位赞**（不是均赞、更不是总赞 —— 均赞/总赞会被一条 187 赞的爆款拉飞），并**剔掉**「单条占他总赞 ≥50%」与「有赞评论 <3 条」的人（偶发爆款 / 薄记录）。**目标社区选不出 2 个人时不降标准**，自动改用**同类社区**（触达 = 该订阅清单里的其它社区；养号 = 同类目的养号社区），所以任何订阅都能拿到足量范例。回执里 `target_sub_picks` / `fallback_used` / `excluded_one_hit` 讲清这次用的是谁的案例。**挑人看「常驻」**：`vibe_commenter_profile(author, focus_sub)` 告诉你这个人是目标社区的**常驻**还是**路过**型高手 —— 学语气要挑常驻。**学法（owner 定调）**：回执里的 **`style_corpus`** = 该社区**几个**写得最好的作者（默认 4 位、按均赞；冷社区门槛自适应降到 3 条）+ 每人**多条**真实评论（默认每人 8 条、共 24 条）+ 确定性**风格统计**（平均句数/字数、含数字比例、第一人称比例、结尾问句比例、高频开头词）—— 这份**案例富集**（集中几个人 + 每人多条）已经写进任务书（触达 `draft_prompt` 和养号任务书），拿来**模仿**语气与结构，不许抄句子 | 免费 | Header |
| `vibe_warmup_subs` | `recheck`(默认 false) | **养号社区清单**（与线索池独立）：梗图/猫狗/问答等社区 + 我们**实测的评论/发帖移除率**、评论是否受限、明确劝退清单 + 今日档位/纪律/ETA。回执另给 **`pick`**（按实测移除率升序的推荐社区 + 排序规则，解决并列 tie-break）、`tier_note`（`t0/t1/t2` 养号档位 ≠ `rate.tier` 计费档位）、`progress`（今日条数 + 分社区分布）、**`effect`**（养号效果：已发/存活率/累计赞数≈karma/有人回/分社区/最好的几条）；`recheck=true` = 立刻复查一轮（默认由 6h 巡检腿自动跑） | 免费 | Header |
| `vibe_warmup_threads` | `sub`, `limit`(默认 20), `order`(new/hot), `refresh`(默认 true), `force`(默认 false) | **养号帖列表（界面同款）**：**先按 TTL(10 分钟) 拉一次最新帖**（否则是几周前的快照，老帖没人看、攒不到 karma），再返回帖 + 它**已存的养号草稿** + 是否已记账 —— 一次调用渲染整屏（不用逐卡扇出）。排序写死「**有草稿的在前** → 新的在前」(`order=hot` 换成评论多的在前)；`force=true` 跳过 TTL。回执 `freshness` 段说明这次拉没拉、快照多旧。每行含 `title` **和 `body` 摘要**（写稿要有依据，别只凭标题）、`draft`、`logged`；`next.why` 说明「**不用全写**，今天按纪律 3-5 条」 | 免费 | Header |
| `vibe_warmup_prompt` | `sub`, `post_id`(可选), `title`(可选), `body`(可选), `draft`(可选，**交稿**) | **养号评论任务书 + 交稿**：与触达**完全同构** —— 把写好的 1-3 句放进 `draft=` 回传 → 服务端落库（`draft_written`/`draft_stored`）**并做确定性复核**（`draft_check` + `failed_detail[{k,hit,note}]`：链接/产品名/推销/套话开头/复述标题/超 3 句；只报命中、不拦截落库），**用户在 app 养号页点「复制草稿」直接发**（不再复制任务书）。写死禁止链接/产品名/推销语气，且「没话说就跳过这条」 | 免费 | Header |
| `vibe_warmup_status` | `enabled`(bool) | **暂停/恢复养号订阅**: `false` → `paused`（不发帖单、不复查；已发出的评论仍在监控名单）, `true` → `active`。幂等；缺订阅时按「默认开」先建。与 `vibe_unsubscribe`（`cancelled`）不是一回事 | 免费 | 头 |
| `vibe_warmup_logged` | `sub`(可选), `days`(默认 30), `limit`(默认 50) | **已发清单 = 监控名单**：每条养号评论现在的 `state`（alive/removed/self_deleted）、`score`（评论赞 ≈ karma）、`replies_n`、`checks_n`（复查过几次）、`declared_at`/`checked_at`、`permalink`；`stages` 给计数（在监控 / **没 id 查不了证** / 存活 / 被删） | 免费 | Header |
| `vibe_warmup_log` | `sub`, `post_id`(可选), `draft`(可选), `comment_id`(**推荐**：评论链接或 id), `permalink`(同上) | **养号台账**（与线索/交付分开）：记一次养号动作（= **已发出**；不带 `comment_id` 也照记，算进今天条数）；**这里也是养号配额的计费点：发出 1 条评论 = 1 条 lead**（从 `vibe_leads` 领养号行不计费），回执带 `quota{daily{used,cap,left}}` 与 `subscription`，超 5 条/天会给节奏提示；带 `comment_id` 就**进入监控**：每 6 小时复查存活/赞数(≈karma)/有人回（最近 7 天），回执带 `effect` 汇总；不带 id 也照记（算今天条数）但**查不了证**。养号**不受触达节流限制**，且养号评论**不进**触达熔断（那条 48 小时熔断只数触达评论） | 免费 | Header |
| `vibe_outreach_sent` | `lead_id`（**候选 id**） | **「我已发出」登记**：服务端立刻去那条帖里找你账号的评论（1 个请求），找到就登记 `comment_id`/发布时间/存活/赞数/回复数，并在你没标过时**自动把结果标成 `contacted`**；之后按 T+24h/72h/7d 自动复查。找不到就先记 `unknown`，交给按用户名的增量发现（每 6 小时）继续盯。前置：app 侧栏填过 Reddit 用户名 | 免费 | Header |
| `vibe_mark_leads` | `lead_ids, outcome` | 标记线索结果（valid 有效 / invalid 无效 / contacted 已触达）——帮你跟踪线索跟进质量。⚠️ 前提是**真的发出过**（`todo.outreach.sent > 0`）：没发过就没有结果可标，回执此时会把 `next` 指向 `vibe_outreach_sent` | 免费 | Header |
| `vibe_outreach_advice` | `delivered_id`, `draft`(可选), `include_body`(默认 true) | **触达建议 + 写作任务书（零 LLM）**：`delivered_id` 用**交付行 id**（`vibe_delivered`/`vibe_submit_score` 回执里的 `delivered_id`，**不是**候选 `lead_id`）。回执含四层判定（`verdict` 可回/谨慎回/别回）、`rules`（该社区规则要点）、`draft_prompt`（**给 agent 的写作任务书**：正文摘录 + 硬约束 + 范例）、`progress`（触达阶段进度）。把成稿放进 `draft` 参数回传 = 交稿, 服务端按同一套规则复核并落库（`draft_check`/`draft_saved`/`draft_source`）| 免费 | Header |
| `vibe_get_delivered` | `lead_id` | 单条已交付线索详情（回访用），含**完整正文** | 免费 | Header |
| `vibe_delivered` | `limit, offset` | 已交付线索列表（回访历史客户） | 免费 | Header |
| `vibe_recover_key` | `email` | **丢了 API key？** 第 1 步：给已注册邮箱发验证码（无鉴权）| 免费 | 无 |
| `vibe_recover_verify` | `email, code` | 第 2 步：验证码验证后，key 邮件发送到邮箱（无鉴权）| 免费 | 无 |

> 除 `vibe_register` 外，所有工具通过 HTTP 请求头 `Authorization: Bearer <api_key>` 鉴权，
> **工具参数中不再出现 api_key**（key 不裸奔、不进调用日志）。

### 管理工具（2026-09-05 —— 词表 / 健康 / 回收 / 判定口径）

| 工具 | 参数 | 作用 | 费用 | 鉴权 |
|------|------|------|------|------|
| `vibe_keywords` | `subscription_id`, `status`(可选: all/active/monitor/removed/retire) | **词表 + 命中统计**（query/hit/pooled/avg-score/source）：当前靠哪些词在匹配、每个词表现如何——扩/停前先读它 | 免费 | Header |
| `vibe_keyword_add` | `subscription_id, kw, kw_type`(tail/entity/competitor/comment), `source`(manual 默认 / auto), `note`(可选) | **加词扩召回**。`source=manual`（默认）= 你的词、受保护不会被自动停；`source=auto` = 编排器加的词（未来弱了可被停）。同词覆盖 auto 词 = 你接管（变 manual）。**每次真实变更自动写词级变更日志**（谁/何时/哪个词/做了什么），`note` 记理由 | 免费 | Header |
| `vibe_keyword_add_batch` | `subscription_id, keywords`(list of `{kw, kw_type}`), `source`(默认 auto), `note`(可选) | **一次调用加 N 词**（逐条语义同 `vibe_keyword_add`）——初始词/扩词列表请用批量而非循环，留在账号限流窗内（free 5 / starter 10 / pro 20 每 60s）。单词失败不影响整批；返回 `{added, total, batch_id, results}`。同批共享一个 `batch_id`，日志里可整批归组 | 免费 | Header |
| `vibe_keyword_remove` | `subscription_id, kw, force`(默认 false), `note`(可选) | **停用词**（→ removed 不再匹配）。默认只停 manual 词；`force=true` 仅供编排器停 auto 弱词——手动勿用。**建议传 `note`**：这是"为什么停这个词"唯一按词留痕的地方 | 免费 | Header |
| `vibe_sd_update` | `subscription_id, supply_side, demand_side, core_friction, demand_pain` | **设供需判定口径**（四段，服务端持久化）——这是评分引擎的官方判定上下文，每次评分注入为 [SUPPLY/DEMAND]。空字段保留旧值；你编辑后后端永不覆盖 | 免费 | Header |
| `vibe_sub_health` | `subscription_id` | **供给健康 + 交付评估（零 LLM）**：`assessment`（当前搜索面能否填满月领取额度：`projected_items_month` vs `commitment_remaining`、`gap_reason`、`supply_per_day`、`daily_need`）/ 候选存量(new+sent) / 缺口 / 采集是否足量 / 上次优化。**先读它**：`gap_reason=supply_ceiling` 时扩 **sub 清单**比动词更有效 | 免费 | Header |
| `vibe_opt_log` | `subscription_id, outcome, reason, n_new_kw, n_replaced` | **记录一次扩词/优化事件**（按次：outcome + reason ≤800 字，写入优化历史，健康页的"上次优化"读它）——扩/停后调用，闭环可审计。注意分工：**按词的变更流水由 `vibe_keyword_*` 自动记录**（`kw_change_log`，无需你手动写）；本工具记的是**决策叙事**（为什么这么调） | 免费 | Header |
| `vibe_kw_history` | `subscription_id, limit`(默认 30, 上限 200) | **变更历史（按词 + 按次，时间倒序）**：`kind=kw` 是词级变更（哪时/哪个词/新增|复活|更新|停用/来源/批次），`kind=opt` 是你自己记的按次决策（outcome/reason）。**回顾"我上一轮对这个订阅做过什么"用这个**——按词的操作无需你补记，工具会自动留痕 | 免费 | Header |
| `vibe_rejected` | `subscription_id, limit` | **回收历史**：引擎判不相关的候选（含理由分），跨会话持久 | 免费 | Header |
| `vibe_export_leads` | `subscription_id`, `status`(delivered/rejected/new), `limit`, `offset`, `include_body` | **导出客户数据（2026-09-08，零 LLM）**：已交付客户 / 回收 / 候选，每条带 kw + kw_type + 最近评分 score/reason（你的评分反馈）+ outcome/marked_at 跟进状态 + 可选正文。权威存储在 PG（delivered_log/lead_pool/scoring_feedback）——本工具经 MCP 暴露给你，不用碰数据库。用于触达名单、产出分析、下游（访谈/SEO）素材 | 免费 | Header |
| `vibe_recover_lead` | `lead_ids`（列表） | **恢复误判线索**：从回收池回到待评分队列，可重新评分（领取时已计费，不重复扣费）| 免费 | Header |
| `vibe_subs` | `subscription_id` | **来源 sub 命中统计**（各 sub 入池/状态分布）——哪些 subreddit 真在贡献。注意与 `vibe_list_subs`（你的订阅列表）区分 | 免费 | Header |
| `vibe_supply_status` | `subscription_id` | **语料供给状态快照（零 LLM，2026-09-07）**：拉取池规模 / 储备分层 / **近 7 天 post_store 入帖趋势**（语料是否还在增长）/ 名录新鲜度（总量 + 最后更新）/ ArcticShift 限流态（共享熔断，跨进程）。用于区分：*词面耗尽*（应扩词）vs *语料边界窄*（应扩 sub）vs *名录旧*（catalog 需月度刷新）vs *采集停* vs *限流中*（2026-09-09：词搜腿字段已移除——词全语料匹配看下方 `pipeline_recent`） | 免费 | Header |
| `vibe_sub_list_update` | `subscription_id`, `subs`(list), `mode`(replace/add/remove/list) | **维护本订阅的 sub 清单——它的显式搜索面（v2.2 sub 锚点，2026-09-09）**：匹配只在清单 sub 语料内跑。每条返回 `in_pool`（库内可立即搜，帖+评论）或 `needs_pull`（服务器将批量取货）。**这也是获取你没有的语料的唯一途径**：加 sub 即入服务端取货队列；agent 侧没有拉取工具（原 `vibe_search_probe` 已于 2026-09-11 下线） | 免费 | Header |
| `vibe_sub_catalog` | `query`(可选), `limit` | **定清单前的候选 sub（v2.2，2026-09-09）**：无 query → A 有货面（真实 `relevant` 交付过的 sub，delivered 降序——库内已有货可直接搜）；带产品/领域词 → B/C 名录词法候选（可能需取货）。每条标注 `stock`(in_pool/needs_pull)、`tier`(deep/shallow)、`delivered` 数，以及 **`description`**（sub 简介，2026-09-11 起返回） | 免费 | Header |
| `vibe_sub_search` | `query`(可选), `offset`, `limit`(≤100), `sort`(subscribers/active/name/volume) | **全量目录检索（2026-09-11 新增）**：全量目录（体量看回执 `total`）按**名称或简介**匹配（多词 OR 并集）+ 分页。每条：`description`、`subscribers`、`num_posts`、`posts_90d` + `volume_measured`、`stock`(in_pool/needs_pull)、`tier`、`delivered`、`listed`（已被某订阅清单引用）。用来**精准找 sub**，再用 `vibe_sub_list_update` 加入。每条带 **`rules[]` 版主规则原文** + `submit_text`（**判 sub 定位用原文**；`rules_missing=true` = 问过但 Reddit 侧无公开规则，≠ 无限制） | 免费 | Header |

> 费用说明：上面 16 个是读写状态操作——**线索在首次领取时计费**（Free 1,000/月 · Starter 5,000/月，超出 $5/千条 · Pro 30,000/月，超出 $3.50/千条）；**评分、重复查看、导出免费**；每日上限超出顺延次日。
>
> 限流是**每账号三个独立桶**（2026-09-11），读不会再吃掉你的管道预算：**读**（delivered / keywords / subs / sub_health / sub_catalog / sub_search / supply_status / balance…）free·starter·pro = **120 · 240 · 480** 次/分钟；**管道**（`vibe_leads` / `vibe_submit_score` / `vibe_recover_lead`）= **10 · 20 · 40**；**写**（subscribe / keyword_* / sd_update / mark_leads / sub_list_update…）= **15 · 30 · 60**。所以一轮感知（5 次读）很便宜 —— 节奏要压在写桶上。**桶按「调用」计数，不按条目数**：一次 `vibe_submit_score` 最多收 **100** 条，只吃 **1 个** pipeline token —— 领 N 条后**一次**回传 N 条（`vibe_leads(limit=N)` + 一次 `vibe_submit_score(scores=[…])` = **2 次** pipeline 调用，不是 N+1 次）。一次超过 100 条返回 `code=batch_too_large`，**整单不落库**。

### 循环节奏 —— 按**库存**重入，不按钟表（2026-09-22）

这条循环**不是一次性配置**：服务端每 ~30 分钟往池子里补候选，所以"面配好了但从此不再跑"会静默
堆起一堆没人判定的线索。线上实测（2026-09-22）：在**真实客户**的 active 订阅里，好几个订阅手上
积了 **3,000~6,000** 条已领/未领候选，而**最后一次判定是 1~2 周前**，另有两个订阅**一次都没判过**。
它们的面板显示"没有线索"，而池子其实是满的 —— 面没问题，是没人跑循环。

**触发条件 —— 读到就动（不靠掐表、不靠猜）**

| 你读到什么 | 含义 | 现在做什么 |
|---|---|---|
| `progress.todo.to_score > 0`（任一回执）或 `vibe_leads(peek=true).data.unjudged_total > 0` | 手上压着"已领未判" | `vibe_submit_score` —— **先把这批交回，再谈领取** |
| `to_score == 0` 且 `progress.todo.claimable_now > 0` | 有货、额度也空着 | `vibe_leads(subscription_id, limit)` → 判 → 交回 |
| `vibe_sub_health.stock` 在涨而 `assessment.projected_items_month` 一直不达 | 面在产出，但没人判定 | 立刻跑；你是宿主 agent 就**把它排进调度** |
| `to_score == 0`、`claimable_now == 0`、`progress.stage_done == true` | 本阶段暂时做完了 | 去 outreach；下一拍再回来看 |

- **节奏**：`assessment.gap_reason=shortfall`（目标未达）期间**每 30~60 分钟至少一批**；
  稳态（`committed_ok`）**每天一次**就够 —— 每天一趟也顺带避免 `sent` 撞 7 天过期。
- **批量**：一次 `vibe_leads(limit)` + 一次 `vibe_submit_score`（≤100 条 = **1 个 pipeline
  token**）。按档位领满（free 20 / starter 30 / pro 50），判完交回，再领下一批。**不要**一次
  领一大摞留着"回头判"：`to_score` 会占着你自己的下一次领取（闸门是账号口径）。
- **每个订阅都要跑，不只第一个**：`to_score` 是账号口径，而待判清单是逐订阅的 —— 用
  `todo.to_score_by_sub`（或 `next.args.subscription_ids`）看出**欠在哪个订阅**，逐个跑。
- **现成的定时器：`scripts/loop_runner.py`**（2026-09-22）。技能包现在**连定时器一起给**，不再只给执行器：
  它跑 **intake**（内部调 `score_batch.py`：领取→判真→交回）和 **outreach 的机械一半**
  （取任务书 → 你的 LLM 写 ≤18 词 → 服务端复核落库）。**它绝不自动发帖** —— 发出仍归你/你的 agent
  （`vibe_outreach_sent` → `vibe_mark_leads`）。BYOK：`VIBEDOLLAR_API_KEY` + `LLM_API_KEY`
  （自建端点再加 `VIBEDOLLAR_MCP_URL`）；成本闸门 `--limit`/`--daily-cap`/`--outreach-per-sub`；
  `--stage intake|outreach|both`；cron 与 systemd timer 的安装片段写在脚本 docstring 里。
  **实测为什么必须有它**：没有定时器时循环会停在半路 —— 8 个非营销订阅里 6 个判定停在
  11~14 天前（或从未判过）；sub 355 交付 655 条却只有 166 条有草稿（最近 10 条一条都没有）。
- **逐订阅手工配方**（你想自己驱动时）：每 30~60 分钟执行
  `python3 scripts/score_batch.py --sub <sid> --limit <档位上限>` → 再读 `vibe_sub_health`，
  按 `assessment.gap_reason` 选动作（见下面「Agent 决策循环」）。当
  `assessment.committed_ok` 且库存走平，就可以停止给这个订阅排期。
- **反模式（这条节奏就是为了防它）**："面配好、早期判了几条、然后再也没回来"。没有报错、没有告警，
  客户面板一直空着 —— 2026-09-22 一天内实测到两例（`345` 待判 ~5k / 最后判定 09-08；
  `397`/`398` 一次都没判过）。

### Agent 决策循环（每订阅、每轮 —— v2.1 交付目标驱动）

vibedollar 是**数据/状态层 —— 服务端零决策**。它采集 Reddit、候选匹配入池、把评分
反馈记录成信号、返回健康数据；**一切决定由你（宿主 agent）做** —— 扩词 / 停用 /
重生成 / probe / wait / 报告。没有"服务端自动退役"可等：hit=0、avg_score、n_rejected
都是**供你行动的信号**，不是服务端会替你执行的动作。

**循环由交付目标驱动，不是由"有没有池可评"驱动。** 每轮：

```
目标检查 → perceive → plan（一个动作）→ act → verify → 回到目标检查
```

#### 0. 目标检查（每轮最先 —— 循环的引擎）

目标 = 当前搜索面能否填满客户的月领取额度（见 `vibe_sub_health.assessment`：
`projected_items_month` vs `commitment_remaining`，以及 `gap_reason`）。每轮先问：

- **`committed_ok`** → `wait`（快环消化即可，无供给动作）
- **`shortfall`** → 任务**没完成**。从下方决策表选下一个动作，执行、verify、
  **回到目标检查**。只有把每个可用方向都试过且验证无改善后，才允许停
  （report exhausted）。**评分完静默收尾 = 禁止**——"评了 15 条全 irrelevant"
  是换方向的信号，不是任务完成。

#### 1. Perceive（读工具，零 LLM）

```
vibe_sub_health(sid)     → assessment（projected_items_month / commitment_remaining / gap_reason /
                           supply_per_day / daily_need / 存量）+ stock / gap / collecting_ok / last_opt
vibe_supply_status(sid)  → 语料入库趋势 / 名录新鲜度 / arctic.limited
vibe_keywords(sid, all)  → 每词: status/source/query/hit/pooled/avg_score/
                           n_delivered/n_rejected/invalid_sample/created_at
vibe_subs(sid)           → 哪些 subreddit 真在贡献候选
vibe_sub_list_update(sid, subs=[], mode="list")  → 你当前的 sub 清单（v2.2：你的显式搜索面）
vibe_leads(peek=true)    → **每轮必扫一眼** progress.todo.supply.stats.pairs / low_yield.pairs:
                           (词 × sub) 网格 —— **同一个词能在一个 sub 95%、在另一个 sub 0%**
                           (实测 closed testing 全局 95% / 在 b2bmarketing 13%)。每格带
                           kw_rate_elsewhere / sub_rate_other_kw 与 hint, 直接告诉你该改词
                           / 移 sub / 还是声明排除格 —— **先看 hint, 别只看那个低数字**
```

**v2.2（2026-09-09）——搜索面 = 你的 sub 清单。** 匹配现在**只在你列出的 sub
语料内跑**（`vibe_sub_list_update`），不再全语料。循环的供给侧变成：*把清单养
健康*——交付过的 sub 留下；从未评过 relevant 的 sub 是噪声；没列进清单的 sub
根本不会被搜。扩词前先看清单：

#### 2. 健康数据语义（每个数字代表什么 → 你该决定什么）

服务端只**报告**这些数据；**行动的是你**（v2.1 —— 服务端零决策）：

| 数据 | 含义 | 你的决定 |
|---|---|---|
| `assessment.gap_reason` | 供给为什么填不满额度：`supply_ceiling`（搜索面太窄 / 垂直语料薄）· `word_face`（相关率 < 15%）· `capacity`（需求速度超过每日上限）· `collecting` · `no_data` · `ok` | **`supply_ceiling` → 扩 sub 清单**（加 sub，通常就是这一步）· `word_face` → 退役/重生成词面 · `capacity` → 供给侧无事可做（那是每日节流）· `collecting` → alert，等采集恢复 |
| `projected_items_month` vs `commitment_remaining` | 当前搜索面能否填满月领取额度（**条目**口径 = 计费单位）| **目标检查**：`committed_ok` → wait；`shortfall` → act（驱动一切）|
| `hit_count` = 0 | 该短语**还没命中** —— **首轮 0 命中非结论**（2026-09-08 Snag 实证：declutter home q1=0 → q2 命中；语料增量入库，词可能等帖子出现才命中）| 别凭单轮 0 命中退役：观察到 qc≥3；语料在长仍多轮 0 → probe 目标 sub / 换词 / 退役（持续 0 命中 + 语料新鲜 = 表达确实不存在）|
| `hit_count` > 0 但你的评分全 `irrelevant` | 表达存在但**匹配的是噪声**——是词错了，不是需求到头了 | 退役该词，然后**从 sd 重生成词面**（sd 缺→`sd_gen.md`；`kw_init.md` → `vibe_keyword_add_batch`）——词错用重生成修，不是放弃 |
| `n_rejected` ≥ 2 + 0 delivered + `invalid_sample` 跨主题 | 噪声制造机 | `vibe_keyword_remove` force + `vibe_opt_log`（见 Plan A）|
| `avg_score`（负）| 评分反馈聚合信号（每条你的 irrelevant −3，服务端只记录）| 越负 = 被拒越多 → 支持退役/重生成判断；**服务端不据它自动退役** |
| `query_count` < 3 | 观测不足 | 先别判（防单次误杀）|
| `created_at` 近期 | NEW30 组（判据②输入）| 近 30 天新词的命中率 → 继续扩或停 |
| `collecting_ok=false` | 后端今天采集不足 | alert——采集恢复前扩词无用 |
| `pipeline_recent`（连续多轮 matched=0）| 词在语料里现在捞不到 | 词耗尽 → probe/换词/重生成；**与语料停区分**：若 `corpus_today` 暴跌（对比 ~90k/日基准）→ 语料没在长——等待/alert，不是词的问题 |
| `arctic.limited` | 物理限流 | 暂停供给动作到解除（非冷却）|

#### 2b. `gap_reason=word_face` —— 自己修，并且**证明**修好了（闭环配方, 2026-09-22）

`word_face` 的含义: 有库存、有额度、轮次也在跑 —— 但**领回来的几乎全判无关**。这是词/面问题,
不是供给问题也不是节奏问题; 而且**由你（宿主 agent）来修** —— 服务端从不改你的词表或清单。

实测例子 (2026-09-22 sub 362): 领 8 → 判 8 → **relevant 0** → 交付率停在 `1/98 = 1%`;
`config_missing=false`、库存 97、无 429、额度没动。没有任何东西"坏了" —— 只是这些词不是这个
产品的买家语言。

**四步全做完，不要在第二步就收工:**

1. **看词级证据，不看总数。** `vibe_keywords(sub, all=true)` → 每个词的 `hit_count` /
   `n_pooled` / `n_delivered` / `n_rejected` / `avg_score` / `invalid_sample`
   (最后一个是真实的被拒帖 —— 读它, 它告诉你这个词**实际**捞到什么)。
   `n_rejected ≥ 2 且 n_delivered = 0` 的词 = 噪声发生器。
2. **动词表**: 噪声词 `vibe_keyword_remove`; 然后**按 `sd.demand_side` + `demand_pain` 重新生成
   词面** —— `kw_init.md`(从 sd 推) 或 `kw_mine.md`(扫一个高精度人群 sub 的语料、提它自己的说法)
   → `vibe_keyword_add_batch`。若某个 sub 只贡献拒绝, **面也要动**:
   `vibe_sub_list_update(mode=add|remove)` —— 同一个词能在一个 sub 95%、在另一个 sub 0%
   (先看 `stats.pairs`, 用 `vibe_pair_exclude` 而不是把一个在别处有效的词整个删掉)。
3. **再跑一轮, 用同一把尺子重测**: `score_batch.py --sub <sid> --limit <档位上限>` →
   读回每个词的 `relevant/judged`。**成功判据**: 新词的
   `n_delivered / (n_delivered + n_rejected)` 在**≥5 条已判**下 **≥ 20%**
   (低于这个数, 那就是换了个拼写的同一堆噪声), 且该订阅交付率不再往 0 走。
4. **把"改了什么、为什么"写下来** —— `vibe_opt_log` 或你自己的笔记: 退役了哪些词、加了哪些、
   前后测到的比率。下一个 agent(或下周的你自己)必须能区分"这修好了"和"这只是又跑了一遍"。

⚠️ **绝不因为一批全无关就断言"这个市场没需求"** —— 这正是本配方要防的实测失效模式
(面可以修; 而用"从来没匹配到买家"的词去检验市场, 什么都证明不了)。

#### 2c. 花额度之前先**免费看标题**，并且记住这是 AND 语义（2026-09-22）

由**客户侧 agent** 自己修 `word_face` 订阅时发现（362: 交付率 1.9% → 5.5%，新词
`facebook marketplace` 3/10 = 30%）。两条值得照抄的习惯：

- **领取前先免费看库存。** `vibe_export_leads`（库存标题/正文）与
  `vibe_pool_purge(out_of_scope=true, dry_run=true)` 能在**不领取**的前提下看清池子里到底是什么；
  **领取才计费**。用它先判"这个词该退役 / 这批库存该清"，**别让一条垃圾花掉额度**。
  实测的坑：执行器的 `--dry-run` 也不免费（老版本甚至照样领取）；
  真正免费的是 `vibe_leads(peek=true)`、`vibe_export_leads`、`vibe_pool_purge(dry_run=true)`。
- **这套匹配是 AND（所有词都出现才命中）—— 泛词就是毒药。** 362 实测：`free stuff` /
  `free items` / `buy nothing` / `moving boxes` / `needing furniture` / `nextdoor` /
  `freecycle` 全部把池子灌成噪声 —— 每一条都是**读了标题**才证伪并退役的。
  词里必须带**领域名词**（`free furniture`、`curb alert`、`facebook marketplace`），
  不能只有意图。
- **弱词是 (词 × sub) 的问题，不是词的问题**：`free furniture` 全局 7%，在城市 sub 有用、
  在 `minimalism`/`Mommit`/`ZeroWaste` 全是拒绝 —— 该用 `vibe_pair_exclude` 排格子，
  不是 `vibe_keyword_remove` 删词。

#### 3. Plan —— 一个动作，目标驱动

**A. 先闭环你自己的评分反馈**（评分反馈是最强信号）。
若你上一轮评分给某词产出 `irrelevant` 且该词 **0 delivered**
（n_rejected ≥ 2 且 `invalid_sample` 显示它拉的是跨主题垃圾）→ 该词是
噪声制造机 → **立即退役**：

```
vibe_keyword_remove(subscription_id, kw, force=true)   # auto 词 —— 你的决定，没有服务端批可等
vibe_opt_log(subscription_id, outcome="auto_retire", reason="0 relevant, N irrelevant")
```

`n_rejected` 是跨评分者累计——分不清是谁的拒绝时，让 `invalid_sample` 仲裁：明显
跨主题垃圾 = 噪声制造机可退役；本领域内合理却被拒 = 更像误判——恢复它
（`vibe_recover_lead`），不要凭它退役这个词。

**B. 然后读 NEW30 边际产出信号**（扩词还有没有用）：近 ~30 天新增词（`created_at` 新）：
- 大多**有命中**（hit>0）且交付仍缺 → 继续扩（只用 probe 验证过的词）
- 大多**零命中** → 现词面够不到需求 → 别直接停：probe 替代表达；若退役后词面
  耗尽，**先从 sd 重生成**（见 C），再谈市场结论

**C. 全 irrelevant ≠ 市场到头 —— 重生成词面。** 若你退役了一批噪声词（0 relevant）
且交付仍缺 → 是词错了，不是需求没了。从供需画像重生成：sd 缺失 → `sd_gen.md` →
`vibe_sd_update`；再 `kw_init.md`（或带现词行用 `kw_opt.md`）→ 新词面 →
`vibe_keyword_add_batch`。**只有重生成的词面也失败**（新词又 0 命中或全 irrelevant）
才转向语料探索或报告。

决策表（目标驱动，v2.2 sub 锚点 —— 2026-09-09）：

| 观察到 | 动作 |
|---|---|
| 目标达成 / 超额 | `wait`（快环消化）|
| 目标未达成、stock(new+sent)>0 | 评池（`score_batch.py`）——结果喂下轮本表 |
| **sub 清单空** | 定搜索面：`vibe_sub_catalog`（A：真实交付过的 sub——库内已有货立即可搜；B/C：垂直/名录候选——可能需取货）→ `vibe_sub_list_update(subs, mode="replace")` → 服务器自动批量取货 needs_pull sub |
| **清单 sub 全静默**（`pipeline_recent` 多轮 matched=0 且语料在长）| 扩清单——需求住在你没列的 sub 里：`vibe_sub_catalog(query=<产品/领域词>)` → 加候选（B/C 可能需一次性取货，~分钟/sub）|
| 词: 0 delivered + ≥2 rejected，`invalid_sample` 跨主题 | `vibe_keyword_remove` force + `vibe_opt_log` |
| 退役后词面清空、目标仍缺 | **重生成**：sd_gen（sd 缺）→ kw_init/kw_opt → `vibe_keyword_add_batch` |
| 新词多轮 hit=0、清单健康 | 该表达在你清单 sub 语料里不存在 → **扩/换搜索面**：`vibe_sub_search` / `vibe_sub_catalog` 找候选 sub → `vibe_sub_list_update` 加入（服务端排队取货）→ 下一轮从 `vibe_keywords` 命中统计判断表达好坏。**已无 agent 侧 probe**（`vibe_search_probe` 2026-09-11 下线：语料只经 sub 清单进来）|
| NEW30 有命中、目标仍缺 | 扩: `vibe_keyword_add_batch` |
| NEW30 扫净、collecting_ok | 语料边界窄 → 扩你的 sub 清单（阶段 B）；期间记录尝试 |
| `collecting_ok=false` | alert（采集停 —— 扩词无用）|
| `arctic.limited` | 暂停供给动作 —— 物理等待，非冷却 |
| **`stats.pairs` 某格低产**（判过 ≥5 且交付率 <20%） | **先看 `hint` 再动手**: `配对问题`（词与 sub 各自在别处都不错）→ `vibe_pair_exclude` 声明排除该格; `词面问题` → 改词（`vibe_keyword_remove`）或换**更窄的词形**（`closed testing` → `closed testing testers`）; `sub 问题` → 考虑移 sub（`vibe_sub_list_update mode=remove`）。**别只看那个低数字就删 sub** —— 实测因此差点删掉 4 个**人群没问题**的 sub。 **⑦ 只在划算时才声明**: 必须 ① `hint=配对问题`（`词面问题`→改词; `sub 问题`→排除格治不了, 那要移 sub）② 该格 `unclaimed>0`（已捞干的格声明排除**零收益**）③ 若 `sub_rate_other_kw` 只有 0.2–0.3 且**各词都低** = 整个 sub 均匀低产而非某格塌陷 → 排除格治不了, 按「delivered>0 不自退」留着或考虑移 sub |

**穷尽（唯一合法停止）** —— 交付仍缺 且 你已依序尝试并逐步验证：评分 → retire 噪声 →
扩/刷新 sub 清单（catalog A/B/C）→ 从 sd 重生成词面 → probe → 报告。然后诚实报告试过
什么、为什么上限真实（市场表达 / 语料边界），并记录。**不许静默停**：每轮以
"继续朝目标"或"穷尽 + 证据"收尾。

#### 4. Act

执行**一个**动作。加/停词**本身会自动留痕**（`kw_change_log`，按词记谁/何时/哪个词/做了什么，
你只需要传 `note` 写理由）；再调 `vibe_opt_log(...)` 记录这一次的**决策叙事**（健康页可审计）。
写下 **expect**：
动作若有效，下一轮应看到什么（如"重生成的词一轮内命中" / "退役词停止入池垃圾" /
"delivered 增 N"）？

#### 5. Verify（下一轮）

用新一轮 perceive 对照 expect，然后**回到目标检查**：
- expect 达成 → 继续同方向（同类型动作）
- expect 失败 → **切换策略**：评分 → retire → 重生成 → probe → 语料 —— 不重复失败动作
- 交付仍缺且方向未尽 → 下一轮继续；只有"穷尽"（上文）才允许 `report_exhausted`

**纪律**（无时间冷却 / 每日次数 —— v2 §5.3）：
- 每轮一个方向性动作（收敛纪律，非节流）
- verify 门控而非时钟门控：act → 看结果 → 决定下一步
- **扩面而不是探面**：语料只经 sub 清单进来 —— `vibe_sub_search` / `vibe_sub_catalog` 挑 sub，
  `vibe_sub_list_update` 加入（服务端排队取货），下一轮从 `vibe_keywords` 命中统计与
  `pipeline_recent` 读结果。原 `vibe_search_probe`（agent 触发的同步拉取）已于 2026-09-11 下线，
  所以 "0 命中" 只能读作*在你清单 sub 之内*；要验证别处就把那个 sub 加进清单，等一轮管线。
- 唯一硬等待是 ArcticShift 物理限流，经 `vibe_supply_status` 感知

#### 6. 审计日志（每轮）

每轮完整记录以便回放与迭代 prompt —— ts / sid / round_no / 目标检查结果 / world
（工具原始返回，不裁剪）/ 实际发出的 prompt / llm_raw / plan / action / result /
verify / cost。存在你自己的存储（可导出 JSON）。没有它就无法回答"agent 为什么这么判"、
无法迭代循环——日志是核心基建，不是事后补丁。

## 评分回传格式（用户 agent 调用规范）

```
vibe_leads(subscription_id=12, limit=10)          # peek=true 只读预览（免费, 不领取）
    → data.posts: [{"id": 1, "title": "...", "url": "...", "score": 系统参考分, ...}, ...]
      data.pending: [ …已领取未判定（含 id 与正文）… ]   # 历史键 data.leads 不存在, 别读它
      progress: {stage, stage_done, round{claimed_now,scored_now,delivered_now},
                 todo{to_score,claimable_now,limits{…}}, next{do,why,args}}
    （limit 传超过档位上限时按上限返回: free 20 / Starter 30 / Pro 50）

vibe_submit_score(scores=[
    {"id": 1, "verdict": "relevant",   "score": 90, "reason": "直接求方案"},
    {"id": 2, "verdict": "irrelevant", "score": 10, "reason": "与产品无关"},
    ...
])
    → {"ok": true, "passed": 1, "rejected": 1, "quota_used": 1, "quota_limit": 3000}   # 评分免费 — 这两个字段是额度回显, 不是扣费
      # batch: {"submitted": 2, "max_batch": 100, "calls": 1, "bucket": "pipeline", "bucket_tokens": 1}
      # items: [{"id": 1, "verdict": "relevant", "delivered_id": 3488}]  ← 判 relevant 才有 delivered_id
      # progress: {stage:"intake", round:{scored_now:2, delivered_now:1},
      #            todo:{to_score:16, claimable_now:34}, next:{do:"vibe_submit_score"|"vibe_leads"|…}}
      # unmarked_delivered: 15   ← 已发出未标结果的条数 (>0 → vibe_mark_leads)
      # 整批塞进这一次调用（最多 100 条）：N 条判定 = 1 次调用 = 1 个 pipeline token
      # 单条失败进 errors（带 index/id/code/err），不影响其余条目落库
```

规则：
- **首领即计费**：`vibe_leads` 返回 `billing` 块；同一条目由**先领的一端**计费，另一端领回免费；在月额度内为 $0，超出部分从**结算币种对应的钱包**扣 —— 美元钱包 `$5/千条`（Starter）/ `$3.50/千条`（Pro），或人民币钱包 `¥25/千条` / `¥18/千条`。两个钱包分开充值（Creem 充美元、微信充人民币 ¥1=¥1），用户可用 `vibe_set_currency` 切换。**告诉用户一次领取花多少是你的职责**。
- **评分免费**：`vibe_submit_score` 无论如何判定都不产生费用；`relevant` 进交付列表（`vibe_delivered` 可查）。
- **不相关也请回传**（`irrelevant`）：这是状态层学习你评价标准的方式——每次 `irrelevant`
  会降权产生该候选的词（服务端纯 SQL 状态迁移，不做 LLM）。**你的评分质量驱动词表质量**：
  认真评、读完整正文、按真实买家画像判断。敷衍或批量乱评会被一致性护栏识别并降权你的反馈影响。
- **每条候选每轮领取评一次；判 `irrelevant` 的进回收池**（`vibe_rejected` 可查）——若事后
  （如点开原文后）觉得判错了，用 `vibe_recover_lead` 恢复再评。判 `relevant` 即最终（领取时已计费）
- **领了就要全评**：你领取的候选进入 `pending`（**你自己**未评分的累积到 50 条时暂停领取）。`locked` 响应带
  `pending` 列表是**正常流程不是报错**——把每个 pending 候选评完（relevant 或 irrelevant）
  即解锁下一批。绝不丢下已领取的候选不评。
- **Web 端是同一契约上的对等方，不是另一套世界**：用户可以在 https://vibedollar.net/app.html
  手动领取与判定 —— 同一套工具、一条候选一个判定。人工判定回传的分值是
  `relevant=60` / `irrelevant=1`，所以你能把"人判的"和"你判的"区分开。**冲突时以人为准**（2026-09-11）：
  网页端提交带 `override=true`，会**改判**你已给出的 `delivered`/`rejected`。反过来，若某条已被那一端判过，
  你不带 `override` 的提交会被拒收（`该候选已评分处理过 (不可重复评分)`）——
  **跳过该条、继续提交其余条目，不要重试、也不要当失败处理**。同理 `尚未领取` 表示这条还没被领取（先领再评）。
- **共享池、分开的闸门**（2026-09-11）：用户在网页端领了但没判的条目**你随时可以领走**——后续 `vibe_leads`
  会把它交给你（**免费**：首领已由先领的一端计费），且这些条目**永不过期**，不会烂在用户手里。
  只有**你自己**领的条目会过期：`已过期` = 你领取后 7 天未判，费用已产生、线索永不重发 —— 所以"领了不评"
  比"不领"更糟。
- **只领你能处理的量**：**花钱的是领取，不是评分** —— 领了不评的线索同样占用额度。
- **正文随领取返回**（服务端 2026-09-11 起）：候选正文不再预先落库，而是在你领取时从语料池
  附着一次（`sent` 时返回、`delivered` 后永久保留）。极少数候选的原始帖子/评论已过语料保留期
  → 服务端**不交付**它们（该候选直接从池中删掉、不计费），响应里的 `skipped_no_body` 就是这批条数：
  **不用重试、也不是错误**，直接按实际返回的 `posts` 处理即可。
- **保存返回的每个字段**：每个候选完整记录（id/title/url/subreddit/score，含正文）都要持久化。
  `id` 之后 `vibe_get_delivered` 要用；不要只留标题。
- 候选的 `score` 是系统参考分（仅供你参考，以你的判断为准）

## 待处理候选（`locked` 是正常流程）

每个候选的评分问题永远是：**这篇帖子的作者是不是所订阅产品的潜在客户？** 按主题
（是否落在产品解决的问题域）与信号强度判断。是 → `relevant`；否 → `irrelevant`
（irrelevant 也在教系统、且不花钱）。

注意职责分离：**花钱的是领取，评分免费**。只领你真能处理的量 —— 领了不评的线索同样占用额度。

另外，pending 清单是**共享的**：Web 端（`app.html` → **待评分**）展示用户自己未判的条目；
用户领了没判的条目会在你下次 `vibe_leads` 时**免费**回到你手里（且不占你的 50 条闸门）。
谁先判谁生效，而人工判定可以推翻你的判定（`override`）。

**完整主流程（订阅 → 领取 → 判定 → 触达 → 标记 → 复盘, 含每步"回执字段 → 下一步"）
见前文「## 主流程（一条管线）」** —— 照 `progress.next.do` 走即可。三条最容易踩的:

1. `vibe_subscribe(product)` 描述必须完整（名称 + 定位 + 目标用户 + 网站, 40+ 字）;
2. `vibe_leads` 的返回**整条存下来**（含 `billing` 与 `progress`），别只留标题;
3. pending 要**一次批量**回传（≤100 条 = 1 个 pipeline token），判完 `relevant` 立刻按
   `progress.next`（或 `outreach_next_step.delivered_ids`）去写草稿。

## 本地脚本工具（批量执行器 —— 机械动作用脚本，决策归你）

**宿主 agent 是决策引擎**（何时做/做什么/为什么）。下面的脚本是**纯执行器**：各自高效
完成一个机械批量动作（逐条并行判真）——比现场写循环快得多。宿主决定何时调用、传什么参；
脚本返回结构化 JSON 供下一步决策。脚本**不自带调度、不自循环**。

**首次使用**：先跑一次 `--dry-run` 验证 key 与连通性（只领取、不判真、不交还），确认无误再花 LLM 调用。

### `scripts/score_batch.py` —— 评单个订阅的一批（领取→判真→交还）

| 参数 | 含义 |
|-------|------|
| `--sub` | 目标订阅 id（**必填** —— 单订阅单批）|
| `--limit` | 领取上限（默认 10）|
| `--judge` | 你的判真模板路径（默认 `scripts/judge_prompt.md`）|
| `--parallel` | 并行判真路数（默认 8 —— 效率核心）|
| `--threshold` | score ≥ 门槛 → `relevant`（默认 60）|
| `--out` | 证据输出目录（可选；relevant 行存 csv/jsonl）|
| `--dry-run` | 只领取，不判真不交还 |

```bash
export VIBEDOLLAR_API_KEY=...        # 你的 vibedollar key
export LLM_API_KEY=...               # **你自己的** LLM key（脚本可选: 不用脚本也行 —— 用你自己的模型判真后 vibe_submit_score 回传）
export LLM_BASE_URL=https://api.deepseek.com/v1
export LLM_MODEL=deepseek-chat
python3 scripts/score_batch.py --sub 12 --limit 20 --parallel 8 [--out ./evidence]
```

返回 JSON：`{sub_id, claimed, judged, relevant, submitted, failed, pending[]}` ——
读它再决定下一步（评别的订阅 / 扩词 / 等待）。

- **判真标准是你的**：编辑 `scripts/judge_prompt.md`（纯文本模板）定义"什么样的帖子算好客户"；
  `--threshold` 设 relevant 门槛
- **费用**：线索在**领取时**计 vibedollar 额度（月额度内 $0，超出从钱包扣 $5/$3.5 每千条）；评分不产生 vibedollar 费用；判真的 LLM 调用费走**你自己的 key**
- **失败安全**：某条判真失败不丢——留 pending 下轮重试；`vibe_leads` 返回 `locked`+pending 列表
  直到评完为止，把领的全评了（relevant 或 irrelevant）就解锁下一批

### `score_batch.py --engine jev` —— 用 Jev/TypeSafe 当判定引擎（可选）

默认引擎是自己带的 chat 模型（`--engine llm`）。另有 **`--engine jev`**：调 TypeSafe 的 System One。
**⚠️ 问句是「每个订阅自己写」的**：`--engine jev` 读 `data/jev_<sid>.json`（与 `data/sd_<sid>.md` 同族），
缺文件会**直接报错并指向 `scripts/jev_gen.md`** —— 刻意不内建默认问句：问句是**你的需求画像的函数**，
套用别的订阅的问句（例如「买家是不是在求获客」）对卖美甲机/剃须刀/SaaS 监控的产品就是错的。
引擎只提供**通用结构**：多条 need 问句取 OR（保召回）+ 可选闸门对 `gate_yes ∧ ¬gate_no`（治漏掉的那一类），
升级带 = 任一判定用信号落在 `[0.3,0.7]`，契约 `relevant ⟺ score>=60`。**怎么写出并验证你自己的问句看 `scripts/jev_gen.md`**。
调 TypeSafe 的 System One
决策模型，**一次调用并行问两个问题**（`is_buyer` 产品相对 + `acquisition_ask` 通用获客求助），再按
**OR 级联**出 verdict。按**定稿口径**实测（2026-09-21 用独立盲判重做基准, 旧标签与词面提示都已剥离）：
**高置信带 0.921 一致 / 精确 84% / 召回 100%**（n=38/50），全体 0.780；**真实线索轮次**（n=31）
高置信带 **0.952 / 精确 100% / 召回 90%** —— 3 条漏判全是「里程碑 / 庆祝帖」, 落在口径边缘带。
关键不是这几个数, 而是**分歧落在哪**: 73%–80% 的分歧正好落在**你自己的判者也不确定**的那条带里。
所以把 Jev 当**带路由的预筛**用, 而不是当裁决 —— 高置信带自动过, 其余升级给 `judge_prompt` 自己判。
（此处原先写着「FN=0 / 一条不漏」—— 那只在**旧口径**的 gold set 上成立, 真实线索上**不成立**。）

```bash
export TYPESAFE_API_KEY=...            # 你自己的 key（服务端不碰这个 key）
python3 score_batch.py --sub 355 --limit 20 --engine jev \
    --record-answers run1.json         # 顺手把两问答案落盘
python3 score_batch.py --sub 355 --engine jev --replay-answers run1.json   # 离线复跑（零 API）
```

- **`confidence`**：按最强证据离 0.5 边界的距离折算到 [0,1]，回传给 `vibe_submit_score`。
  服务端**只存不用**（不改 verdict/score、不参与计费）。
- **`escalate_ids`**：**落在不确定带 `max(p1,p2) ∈ [0.3,0.7]`** 的条目 —— 建议你用 `judge_prompt` 复核一遍；
  （2026-09-21 判据调整：原来是"两个问句答案不一致"，实测 1145 条带独立盲判基准的真实线索 ——
  **分歧判据升级 25% 但自动带错 10.1% 的条目；概率带判据升级 26% 而自动带错只有 5.1%**。
  同样的升级率，错误翻倍。分歧仍单独报为 `disagree`，是个有用的信号，但不再是升级判据。）
  服务端不会替你改。这是 skill 的 `confidence-routing` 用法。
- `reason` 是**机器记录**（形如 `[jev] is_buyer=0.90 acquisition_ask=0.10 → relevant`），
  **不是解释** —— Jev 不生成文本；语义理由由你（agent）在升级带里补。
- key 与成本都在**消费方**（BYOK）；这属于「模型层分工原则」第 3 条。
### `scripts/mcp.py` —— 共享 MCP 客户端（库，非 CLI）

供其他本地脚本 import：`from mcp import MCPClient`。不由你直接调用。

> **为什么用脚本而不是你自己写循环**：批量动作是机械的（领 N 条 → 逐条用你的 LLM 判 →
> 交还）。脚本把逐条判真并行化并返回干净 JSON —— 你仍是决策者，脚本替你干重复体力活，
> 比你每次现场手写循环快得多。

## 判真与调优 prompt 资产（无占位符替换 —— sd 是运行时数据文档）

评分判真与词表调优的 LLM 模板在 `scripts/*.md`。它们是 **prompt 资产**：加载对应文件，
用自己的 LLM key 按其 `sys` 内容 + 你**从订阅实际数据组装的 user 消息**调用 ——
**模板不含 `{占位符}`、也没有替换机制**（那是前端 JS 拼字符串的做法；作为 agent，
你读数据、原生组装 user 消息即可）。

**供需分析是运行时数据文档** —— 不是模板变量。存在 `data/sd_<sid>.md`
（git-ignored，每宿主本地一份），后续判分 / kw_init / kw_opt 都读这一个文件注入：

```
# 首次 / 重建后 —— 生成 sd:
scripts/sd_gen.md        → LLM（产品文案）→ 四段
python3 scripts/sd_doc.py write --sub <sid> --json '{...}'   → data/sd_<sid>.md
vibe_sd_update(subscription_id, supply_side=..., demand_side=..., ...)  # 后端副本

# 之后任何步骤 —— 读 + 注入（agent 原生读文件，无 replace）:
python3 scripts/sd_doc.py show --sub <sid> --values   → 只出四字段值（剥离自描述头 —
   可直接放进 LLM user 消息，防记号泄漏）
   （或 vibe_list_subs → sd_json —— 同数据，后端权威）
```

| 资产 | 何时加载 | 产出 → 持久化 |
|---|---|---|
| `scripts/sd_doc.py` | fetch/show/write sd 文档（`data/sd_<sid>.md`）—— 纯机械文件操作 | 是否生成/更新由你决定 |
| `scripts/sd_gen.md` | 订阅无 sd（缺 supply_side/demand_side/demand_pain）—— 首次建立或重建后 | 供需四段 → sd_doc.py write + `vibe_sd_update` |
| `scripts/kw_init.md` | 词表为空（初始建立）—— 需先有 sd 文档 | 初始词表 → `vibe_keyword_add_batch`（source=auto）；去重对全状态 |
| `scripts/kw_mine.md` | 已锁定**高精度人群 sub**（其人群 = 本订阅 demand_side），想要"他们真正会打的字" | 用 `vibe_sub_corpus` **逐贴全量扫**该 sub 语料（标题优先；实测 `r/alphaandbetausers` 3417 帖 = 7 次调用 / 13 秒），你的 LLM 按脚本里的 `sys` 提词 → 去重 → `vibe_keyword_add_batch(source=auto)` + `vibe_opt_log`。**服务端零语义**：只翻页，不筛选/不排序/不抽词 |
| `scripts/kw_opt.md` | 决策循环判"扩词" / 一轮退役后 —— 需有 sd 文档 + 现词（active+monitor 行）| `{add, weak}` → add 走 `vibe_keyword_add_batch`（去重对全状态 —— 勿复活 removed 死词）; weak 按决策表守卫 |
| `scripts/judge_prompt.md` | `score_batch.py` 默认判真模板（profile 可编辑、契约固定）| 逐条 verdict → `vibe_submit_score` |
| `scripts/eng_sys_core.md` | **只读**评分核心（计费契约）。原样引用，禁止编辑 | judge 对齐参考 |

**顺序重要**：先 sd 后词。`sd_gen.md` 产出需求侧画像（买家语言）——`kw_init`/`kw_opt`
从它推导词、评分把它注入为 `[SUPPLY/DEMAND]`；sd 为空 = 判真与扩词只靠产品文案，
这正是泛词与 0 命中清扫的起点。

## 订阅模式（持续监控，不用反复调用）

```
vibe_subscribe(product="team wiki tool for small teams")   # 创建订阅（只需产品描述）
    → {"ok": true, "subscription_id": 12, "message": "订阅创建成功, 后台正在跟踪..."}
    ↓ 系统持续跟踪，线索积累（无需你操作）
vibe_list_subs()                                          # 查看订阅状态 + 待领取数
    → {"ok": true, "data": {"subscriptions": [{"id": 12, "product": "...", "new_leads": 7}]}}
    ↓
vibe_leads(subscription_id=12, limit=10)                  # 领取候选（按领取计费，秒回）
    → {"ok": true, "data": {"posts": [{"id": 1, "title": "...", "url": "...", "subreddit": "...", "score": 90}], "count": 7},
       "billing": {"claimed_batch": 7, "free_items": 7, "billable_items": 0, "currency": "usd", "charge": 0.0, "charge_usd": 0.0,
                   "claimed_this_month": 1207, "claimed_quota": 5000, "over_price_per_1k": 5.0,
                   "daily_used": 87, "daily_cap": 1000, "wallet": 0.0, "wallet": 0.0, "wallet_usd": 0.0}}
    ↓ 你的 agent 评分后回传（评分免费）
vibe_submit_score(scores=[{"id": 1, "verdict": "relevant", "score": 90, "reason": "..."}])
    → {"ok": true, "passed": 1, "quota_used": 1, ...}
```

**适用场景**：
- 产品定位已确定，希望**持续获取**新出现的潜在客户，而不是想起来才查一次
- 词表不用手工维护——订阅产品描述即可；当 `vibe_sub_health.assessment.status=shortfall`（搜索面填不满额度）时，由**你的 agent** 读健康工具扩 sub 清单 / 扩停词（见"Agent 决策循环"）
- **线索在首次领取时计费（两端任一端先领即算），评分免费**；订阅本身不额外收费
- **先处理再取下一批**：已领取的候选需全部评分（相关/不相关都算）后，才能领取下一批；未处理完时再次领取会返回**待处理候选列表（含 id）**——直接用这些 id 评分即可解锁下一批（id 丢了也能找回，不会锁死订阅）。长期未评分的候选（7 天）会自动过期释放。

**取消订阅**用 `vibe_unsubscribe`（已积累线索保留）。

## 数据分析用法（下游 —— 需要时再读）

交付线索、候选与词表同时也是**客户访谈**、**前 100 位客户触达**、**SEO/GEO 内容**的原料 ——
完整玩法在 `references/use-cases.zh-CN.md`（英文 `references/use-cases.md`）。
当用户问"线索怎么变成对话/客户/内容"时再读。

## Agent 使用提示

- **丢了 API key？** 引导找回：`vibe_recover_key(email)` → `vibe_recover_verify(email, code)`
  （或引导打开 https://vibedollar.net/account.html → "Lost your API key? Recover it"），无需重新注册。
- **盯住 `claim_quota` 块**：`vibe_balance()` 返回 `claim_quota {month_used, month_limit, currency, over_price_per_1k, daily_used, daily_cap, wallet, wallet_usd}`，以及 `wallets{usd,cny}` 与 `settlement_currency` —— 主动告诉用户当前状态（额度用了多少、每日上限、超量从哪个钱包扣），别等他自己发现被扣费；若他充的是另一个币种，引导他用 `vibe_set_currency`。
- **注册与支付流程**：见 `references/billing.zh-CN.md`（agent 完成全流程；用户的唯一动作是提供邮箱/验证码、扫码或点链接）。
- **典型工作流**：`vibe_subscribe`（订阅产品，后台持续抓取）→ `vibe_leads` 领候选（此时计费）→ 你的 agent 用自己的 LLM 评分（免费）→ `vibe_submit_score` 回传 → 相关线索进交付列表（验证需求 + 找到第一批客户）。

## 定价 / 支付 / 接入（参考文档）

定价档位、钱包充值、Agent 支付开通全流程、MCP 客户端连接配置都在 `references/` —— 按需读取：

- **定价与支付**：用户问价格 / 升级 / 充值 / 支付后确认开通时，读 `references/billing.zh-CN.md`。日常快速查配额：调 `vibe_balance()` —— 响应带 `claim_quota`（本月已领/额度、每日上限、超出单价、钱包余额）。
- **MCP 接入配置**：首次连接或换客户端时，读 `references/mcp-config.md`（端点 URL + `Authorization: Bearer <key>` header 配置）。
