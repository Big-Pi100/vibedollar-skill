---
name: vibedollar
description: "vibedollar 帮助独立开发者找到第一批客户。基于你的产品描述，持续抓取 Reddit 上正在抱怨或求方案的潜在客户线索（帖子与评论），支持订阅持续监控。你的 agent 用自己的 LLM 判断相关性，评分通过才计费（按效果付费）。远程托管免部署。付费解锁：Starter 39/mo 或 Pro 79/mo；也可自由充值钱包额度。"
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
| 持续获客 | `vibe_subscribe` → 系统持续跟踪，候选自动积累，`vibe_leads` 领候选 → 评分通过进交付 |
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
4. **查余额/配额**: `vibe_balance()`（key 自动从请求头读取，返回 tier + 各工具配额余量）
5. **也支持网页自助注册**：打开 `https://vibedollar.net/account.html` 可完成注册/验证/支付全流程（用户可直接在网页操作，无需配置 MCP）

## 可用工具

| 工具 | 参数 | 说明 | 成本 | 鉴权 |
|------|------|------|------|------|
| `vibe_register` | `email` | 注册第 1 步: 发送 6 位邮箱验证码 | 免费 | 无需 |
| `vibe_verify` | `email, code` | 注册第 2 步: 验证码验证, 返回 api_key（同时邮件发送） | 免费 | 无需 |
| `vibe_balance` | `（无）` | 查余额/tier/配额余量（key 走 Header） | 免费 | Header |
| `vibe_subscribe` | `product`, `enable_competitor_kw`(可选), `track_type`(可选) | **订阅持续监控**：输入产品描述，系统持续抓取匹配入池（词表由你的 agent 按决策循环扩/停——见"Agent 决策循环"）。**产品描述必须完整（40+ 字）**：名称 + 一句定位 + 目标用户 + 网站 URL。过短描述会生成泛词与低相关候选，会被拒绝。`enable_competitor_kw`（默认开）：设 `false` 只收直接需求线索，排除竞品对比帖。`track_type`（内部用：outreach/seo/hot_content） | 免费（候选免费） | Header |
| `vibe_leads` | `subscription_id, limit` | **领取候选线索**（免费）：返回候选（含系统参考分），供你评分。评分通过才计费。**单次上限：free 20 / Starter 30 / Pro 50 条**（实际返回 = min(limit, 档位上限)）。响应含 `posts`（新候选）、`pending`（已领未评分，含 `id`）与 `source_status: locked`（先评完 pending 才解锁下一批）。见下方"待处理候选" | **免费** | Header |
| `vibe_submit_score` | `scores` | **评分回传**：对候选评分，`relevant` 才计入交付（扣 1 配额/条），`irrelevant` 回灌优化 | 通过才扣档位额度 | Header |
| `vibe_score_discuss` | `limit, respond_id, response` | **评分分歧对齐（可选）**：查看你与系统参考评分不一致的候选，可说明你的理由——我们据此校准标准，推送更贴合你的判断 | 免费 | Header |
| `vibe_set_notify` | `enabled` | 邮件提醒开关：候选积压时是否发邮件通知你（默认开启，可关闭）| 免费 | Header |
| `vibe_list_subs` | `（无）` | 查看我的订阅列表及候选线索积累状态 | 免费 | Header |
| `vibe_unsubscribe` | `subscription_id` | 取消订阅（已积累的线索保留） | 免费 | Header |
| `vibe_cancel_plan`（指引） | — | **付费档位（Starter/Pro）通过支付平台取消**（Creem 客户门户 / 微信支付管理），不走本 API。取消后档位保留到当期结束再降级 free；已交付线索保留。产品订阅用 `vibe_unsubscribe` 取消 | 免费 | Header |
| `vibe_mark_leads` | `lead_ids, outcome` | 标记线索结果（valid 有效 / invalid 无效 / contacted 已触达）——帮你跟踪线索跟进质量 | 免费 | Header |
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
| `vibe_keyword_add` | `subscription_id, kw, kw_type`(tail/entity/competitor/comment), `source`(manual 默认 / auto) | **加词扩召回**。`source=manual`（默认）= 你的词、受保护不会被自动停；`source=auto` = 编排器加的词（未来弱了可被停）。同词覆盖 auto 词 = 你接管（变 manual）| 免费 | Header |
| `vibe_keyword_add_batch` | `subscription_id, keywords`(list of `{kw, kw_type}`), `source`(默认 auto) | **一次调用加 N 词**（逐条语义同 `vibe_keyword_add`）——初始词/扩词列表请用批量而非循环，留在账号限流窗内（free 5 / starter 10 / pro 20 每 60s）。单词失败不影响整批；返回 `{added, total, results}` | 免费 | Header |
| `vibe_keyword_remove` | `subscription_id, kw, force`(默认 false) | **停用词**（→ removed 不再匹配）。默认只停 manual 词；`force=true` 仅供编排器停 auto 弱词——手动勿用 | 免费 | Header |
| `vibe_sd_update` | `subscription_id, supply_side, demand_side, core_friction, demand_pain` | **设供需判定口径**（四段，服务端持久化）——这是评分引擎的官方判定上下文，每次评分注入为 [SUPPLY/DEMAND]。空字段保留旧值；你编辑后后端永不覆盖 | 免费 | Header |
| `vibe_sub_health` | `subscription_id` | **交付健康（零 LLM）**：配额 / 承诺日线（2×配额÷30）/ 今日入池 / 候选存量(new+sent) / 缺口 / 采集是否足量 / 上次优化。据此决定是否扩词 | 免费 | Header |
| `vibe_opt_log` | `subscription_id, outcome, reason, n_new_kw, n_replaced` | **记录一次扩词/优化事件**（写入优化历史，健康页可见）——扩/停后调用，闭环可审计 | 免费 | Header |
| `vibe_rejected` | `subscription_id, limit` | **回收历史**：引擎判不相关的候选（含理由分），跨会话持久 | 免费 | Header |
| `vibe_export_leads` | `subscription_id`, `status`(delivered/rejected/new), `limit`, `offset`, `include_body` | **导出客户数据（2026-09-08，零 LLM）**：已交付客户 / 回收 / 候选，每条带 kw + kw_type + 最近评分 score/reason（你的评分反馈）+ outcome/marked_at 跟进状态 + 可选正文。权威存储在 PG（delivered_log/lead_pool/scoring_feedback）——本工具经 MCP 暴露给你，不用碰数据库。用于触达名单、产出分析、下游（访谈/SEO）素材 | 免费 | Header |
| `vibe_recover_lead` | `lead_id` | **恢复误判线索**：从回收池回到待评分队列，可重新评分（通过不重复计费）| 免费 | Header |
| `vibe_subs` | `subscription_id` | **来源 sub 命中统计**（各 sub 入池/状态分布）——哪些 subreddit 真在贡献。注意与 `vibe_list_subs`（你的订阅列表）区分 | 免费 | Header |
| `vibe_supply_status` | `subscription_id` | **语料供给状态快照（零 LLM，2026-09-07）**：拉取池规模 / 储备分层 / **近 7 天 post_store 入帖趋势**（语料是否还在增长）/ 名录新鲜度（总量 + 最后更新）/ ArcticShift 限流态（共享熔断，跨进程）。用于区分：*词面耗尽*（应扩词）vs *语料边界窄*（应扩 sub）vs *名录旧*（catalog 需月度刷新）vs *采集停* vs *限流中*（2026-09-09：词搜腿字段已移除——词全语料匹配看下方 `pipeline_recent`，池外定向探测用 `vibe_search_probe`） | 免费 | Header |
| `vibe_search_probe` | `subscription_id`, `query`, `subreddits`, `limit`(≤5) | **池外定向搜索探测（ArcticShift，2026-09-07）**：扩词前先在目标 sub 内搜这个词——即时验证"这个词在那边到底能不能搜出帖子"（防盲扩）。命中的帖幂等入库共享语料；**不入你的 lead_pool**（匹配仍由词驱动）。与 `sub_pull`（只覆盖池内 sub）互补 | 免费 | Header |

> 费用说明：上面 13 个是读写状态操作——候选仍免费，仍只在 `vibe_submit_score` 判 `relevant` 时按效果计费（若未来有任一收费，最终计费口径会单独确认）。

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

交付目标 = 本月 delivered 累计 vs 承诺量（见 `vibe_sub_health`：quota 与月度累计
delivered）。每轮先问：

- **目标达成 / 超额** → `wait`（快环消化即可，无供给动作）
- **目标未达成** → 任务**没完成**。从下方决策表选下一个动作，执行、verify、
  **回到目标检查**。只有把每个可用方向都试过且验证无改善后，才允许停
  （report exhausted）。**评分完静默收尾 = 禁止**——"评了 15 条全 irrelevant"
  是换方向的信号，不是任务完成。

#### 1. Perceive（读工具，零 LLM）

```
vibe_sub_health(sid)     → quota / delivered_month / delivered_total / stock / gap / collecting_ok / last_opt
vibe_supply_status(sid)  → 语料入库趋势 / 名录新鲜度 / arctic.limited
vibe_keywords(sid, all)  → 每词: status/source/query/hit/pooled/avg_score/
                           n_delivered/n_rejected/invalid_sample/created_at
vibe_subs(sid)           → 哪些 subreddit 真在贡献候选
```

#### 2. 健康数据语义（每个数字代表什么 → 你该决定什么）

服务端只**报告**这些数据；**行动的是你**（v2.1 —— 服务端零决策）：

| 数据 | 含义 | 你的决定 |
|---|---|---|
| `delivered_month` vs quota | 本月交付进度 vs 目标 | **目标检查**：达成 → wait；未达成 → act（驱动一切）|
| `hit_count` = 0 | 该短语**还没命中** —— **首轮 0 命中非结论**（2026-09-08 Snag 实证：declutter home q1=0 → q2 命中；语料增量入库，词可能等帖子出现才命中）| 别凭单轮 0 命中退役：观察到 qc≥3；语料在长仍多轮 0 → probe 目标 sub / 换词 / 退役（持续 0 命中 + 语料新鲜 = 表达确实不存在）|
| `hit_count` > 0 但你的评分全 `irrelevant` | 表达存在但**匹配的是噪声**——是词错了，不是需求到头了 | 退役该词，然后**从 sd 重生成词面**（sd 缺→`sd_gen.md`；`kw_init.md` → `vibe_keyword_add_batch`）——词错用重生成修，不是放弃 |
| `n_rejected` ≥ 2 + 0 delivered + `invalid_sample` 跨主题 | 噪声制造机 | `vibe_keyword_remove` force + `vibe_opt_log`（见 Plan A）|
| `avg_score`（负）| 评分反馈聚合信号（每条你的 irrelevant −3，服务端只记录）| 越负 = 被拒越多 → 支持退役/重生成判断；**服务端不据它自动退役** |
| `query_count` < 3 | 观测不足 | 先别判（防单次误杀）|
| `created_at` 近期 | NEW30 组（判据②输入）| 近 30 天新词的命中率 → 继续扩或停 |
| `collecting_ok=false` | 后端今天采集不足 | alert——采集恢复前扩词无用 |
| `pipeline_recent`（连续多轮 matched=0）| 词在语料里现在捞不到 | 词耗尽 → probe/换词/重生成；**与语料停区分**：若 `corpus_today` 暴跌（对比 ~90k/日基准）→ 语料没在长——等待/alert，不是词的问题 |
| `arctic.limited` | 物理限流 | 暂停供给动作到解除（非冷却）|

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

决策表（目标驱动）：

| 观察到 | 动作 |
|---|---|
| 目标达成 / 超额 | `wait`（快环消化）|
| 目标未达成、stock(new+sent)>0 | 评池（`score_batch.py`）——结果喂下轮本表 |
| 词: 0 delivered + ≥2 rejected，`invalid_sample` 跨主题 | `vibe_keyword_remove` force + `vibe_opt_log` |
| 退役后词面清空、目标仍缺 | **重生成**：sd_gen（sd 缺）→ kw_init/kw_opt → `vibe_keyword_add_batch` |
| 新词池级 sweep hit=0 | 查 `pipeline_recent`（词搜覆盖**全语料**）——池搜多轮都 0 才 probe 指定 sub / 换词 / 扩 sub；**probe 在几个选定 sub 得 0 ≠ 短语不存在**（Snag："free furniture" 在 5 个 lifestyle sub probe 0，但全池词搜 hit 21 含 r/vancouver）——probe 验目标 sub，词搜才是全语料信号 |
| NEW30 有命中、目标仍缺 | 扩: `vibe_keyword_add_batch`（probe 验证过的词）|
| NEW30 扫净、collecting_ok | 语料边界窄 → expand_sub/widen_pool（阶段 B）；之前 probe + 记录 |
| `collecting_ok=false` | alert（采集停 —— 扩词无用）|
| `arctic.limited` | 暂停供给动作 —— 物理等待，非冷却 |

**穷尽（唯一合法停止）** —— 交付仍缺 且 你已依序尝试并逐步验证：评分 → retire 噪声 →
从 sd 重生成词面 → probe → expand_sub/widen_pool（工具可用处）。然后诚实报告试过
什么、为什么上限真实（市场表达 / 语料边界），并记录。**不许静默停**：每轮以
"继续朝目标"或"穷尽 + 证据"收尾。

#### 4. Act

执行**一个**动作。加/停词后调 `vibe_opt_log(...)`（健康页可审计）。写下 **expect**：
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
- **扩词前先 probe**：`vibe_search_probe(query, [subs])` 秒级验证这词在**选定的 sub** 有没有帖——
  绝不盲扩后等 pipeline 统计。但 **probe 0 是 sub 级结论**：证明不了全语料（那是池级词搜的
  事）；probe 用于在候选表达间选型或查特定 niche sub，"0 命中退役"以 `pipeline_recent`/
  hit_count（全语料）为准。
- 唯一硬等待是 ArcticShift 物理限流，经 `vibe_supply_status` 感知

#### 6. 审计日志（每轮）

每轮完整记录以便回放与迭代 prompt —— ts / sid / round_no / 目标检查结果 / world
（工具原始返回，不裁剪）/ 实际发出的 prompt / llm_raw / plan / action / result /
verify / cost。存在你自己的存储（可导出 JSON）。没有它就无法回答"agent 为什么这么判"、
无法迭代循环——日志是核心基建，不是事后补丁。

## 评分回传格式（用户 agent 调用规范）

```
vibe_leads(subscription_id=12, limit=10)
    → 候选列表: [{"id": 1, "title": "...", "url": "...", "score": 系统参考分, ...}, ...]
    （limit 传超过档位上限时按上限返回: free 20 / Starter 30 / Pro 50）

vibe_submit_score(scores=[
    {"id": 1, "verdict": "relevant",   "score": 90, "reason": "直接求方案"},
    {"id": 2, "verdict": "irrelevant", "score": 10, "reason": "与产品无关"},
    ...
])
    → {"ok": true, "passed": 1, "rejected": 1, "quota_used": 1, "quota_limit": 3000}
```

规则：
- **候选免费**：`vibe_leads` 不扣任何配额
- **通过才计费**：`verdict="relevant"` 的候选扣 1 配额/条，计入交付列表（`vibe_delivered` 可查）
- **不相关也请回传**（`irrelevant`）：这是状态层学习你评价标准的方式——每次 `irrelevant`
  会降权产生该候选的词（服务端纯 SQL 状态迁移，不做 LLM）。**你的评分质量驱动词表质量**：
  认真评、读完整正文、按真实买家画像判断。敷衍或批量乱评会被一致性护栏识别并降权你的反馈影响。
- **每条候选每轮领取评一次；判 `irrelevant` 的进回收池**（`vibe_rejected` 可查）——若事后
  （如点开原文后）觉得判错了，用 `vibe_recover_lead` 恢复再评。判 `relevant` 即最终（已计费）
- **领了就要全评**：领取一批后候选进入 `pending`，订阅暂停直到评完。`locked` 响应带
  `pending` 列表是**正常流程不是报错**——把每个 pending 候选评完（relevant 或 irrelevant）
  即解锁下一批。绝不丢下已领取的候选不评。
- **保存返回的每个字段**：每个候选完整记录（id/title/url/subreddit/score，含正文）都要持久化。
  `id` 之后 `vibe_get_delivered` 要用；不要只留标题。
- 候选的 `score` 是系统参考分（仅供你参考，以你的判断为准）

## 待处理候选（`locked` 是正常流程）

每个候选的评分问题永远是：**这篇帖子的作者是不是所订阅产品的潜在客户？** 按主题
（是否落在产品解决的问题域）与信号强度判断。是 → `relevant`；否 → `irrelevant`
（irrelevant 也在教系统、且不花钱）。

标准循环：
1. `vibe_subscribe(product)` 用**完整描述**（名称 + 定位 + 目标用户 + 网站，40+ 字）→ 拿
   `subscription_id`。过短描述（只有产品名）会被拒——只会生成泛词与低相关候选。
2. `vibe_leads(subscription_id, limit)` → 保存每个候选的**完整返回记录**，别丢字段。
3. 把**所有** pending 候选用 `vibe_submit_score` 评完（`relevant` 或 `irrelevant`），
   解锁下一批。
4. 评 `relevant` 的线索，用 `vibe_get_delivered(lead_id)` 取完整正文做触达。

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
export LLM_API_KEY=...               # 你的 LLM key
export LLM_BASE_URL=https://api.deepseek.com/v1
export LLM_MODEL=deepseek-chat
python3 scripts/score_batch.py --sub 12 --limit 20 --parallel 8 [--out ./evidence]
```

返回 JSON：`{sub_id, claimed, judged, relevant, submitted, failed, pending[]}` ——
读它再决定下一步（评别的订阅 / 扩词 / 等待）。

- **判真标准是你的**：编辑 `scripts/judge_prompt.md`（纯文本模板）定义"什么样的帖子算好客户"；
  `--threshold` 设 relevant 门槛
- **费用**：候选免费；`relevant` 才计 vibedollar 配额（按效果付费）；判真的 LLM 调用费走**你自己的 key**
- **失败安全**：某条判真失败不丢——留 pending 下轮重试；`vibe_leads` 返回 `locked`+pending 列表
  直到评完为止，把领的全评了（relevant 或 irrelevant）就解锁下一批

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
vibe_leads(subscription_id=12, limit=10)                  # 领取候选线索（免费，秒回）
    → {"ok": true, "data": {"posts": [{"id": 1, "title": "...", "url": "...", "subreddit": "...", "score": 90}], "count": 7}}
    ↓ 你的 agent 评分后回传
vibe_submit_score(scores=[{"id": 1, "verdict": "relevant", "score": 90, "reason": "..."}])
    → {"ok": true, "passed": 1, "quota_used": 1, ...}
```

**适用场景**：
- 产品定位已确定，希望**持续获取**新出现的潜在客户，而不是想起来才查一次
- 词表不用手工维护——订阅产品描述即可；当交付落后于承诺线时，由**你的 agent** 读健康工具扩/停词（见"Agent 决策循环"）
- **评分通过才消耗配额**（按效果付费），订阅本身不额外收费
- **先处理再取下一批**：已领取的候选需全部评分（相关/不相关都算）后，才能领取下一批；未处理完时再次领取会返回**待处理候选列表（含 id）**——直接用这些 id 评分即可解锁下一批（id 丢了也能找回，不会锁死订阅）。长期未评分的候选（7 天）会自动过期释放。

**取消订阅**用 `vibe_unsubscribe`（已积累线索保留）。

## 数据分析用法（下游 —— 需要时再读）

交付线索、候选与词表同时也是**客户访谈**、**前 100 位客户触达**、**SEO/GEO 内容**的原料 ——
完整玩法在 `references/use-cases.zh-CN.md`（英文 `references/use-cases.md`）。
当用户问"线索怎么变成对话/客户/内容"时再读。

## Agent 使用提示

- **丢了 API key？** 引导找回：`vibe_recover_key(email)` → `vibe_recover_verify(email, code)`
  （或引导打开 https://vibedollar.net/account.html → "Lost your API key? Recover it"），无需重新注册。
- **看 `quota` 块做自我管理**：每次调用响应带 `quota: {scope, used, limit}` —— 用尽前主动提示用户升级（Starter/Pro）。
- **注册与支付流程**：见 `references/billing.zh-CN.md`（agent 完成全流程；用户的唯一动作是提供邮箱/验证码、扫码或点链接）。
- **典型工作流**：`vibe_subscribe`（订阅产品，后台持续抓取）→ `vibe_leads` 领候选 → 你的 agent 用自己的 LLM 评分 → `vibe_submit_score` 回传 → 通过的进交付列表（验证需求 + 找到第一批客户）。

## 定价 / 支付 / 接入（参考文档）

定价档位、钱包充值、Agent 支付开通全流程、MCP 客户端连接配置都在 `references/` —— 按需读取：

- **定价与支付**：用户问价格 / 升级 / 充值 / 支付后确认开通时，读 `references/billing.zh-CN.md`。日常快速查配额：调 `vibe_balance()` —— 响应带 `quota: {scope, used, limit}`。
- **MCP 接入配置**：首次连接或换客户端时，读 `references/mcp-config.md`（端点 URL + `Authorization: Bearer <key>` header 配置）。
