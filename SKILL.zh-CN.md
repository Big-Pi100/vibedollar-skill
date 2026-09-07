---
name: vibedollar
description: "vibedollar 帮助独立开发者找到第一批客户。基于你的产品描述，持续抓取 Reddit 上正在抱怨或求方案的潜在客户线索（帖子与评论），支持订阅持续监控。你的 agent 用自己的 LLM 判断相关性，评分通过才计费（按效果付费）。远程托管免部署。付费解锁：Starter 39/mo 或 Pro 79/mo；也可自由充值钱包额度。"
---

# vibedollar — 帮你找到正在等你的客户

vibedollar 监控 Reddit，找出那些正在主动寻找用户所建产品的帖子和评论，作为评分后的**潜在客户线索**。分工：vibedollar 运行数据服务（Reddit 采集、候选匹配入池、状态层——词表 / 供需判定口径 / 回收 / 健康）；**宿主 agent 决定什么算好客户**——用自带 LLM key 评分候选，并驱动调优（见下文**交付健康管理**与**供给侧决策**）。

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
| `vibe_subscribe` | `product`, `enable_competitor_kw`(可选), `track_type`(可选) | **订阅持续监控**：输入产品描述，系统持续抓取匹配入池（词表由你的 agent 按健康缺口扩/停——见"交付健康管理"）。**产品描述必须完整（40+ 字）**：名称 + 一句定位 + 目标用户 + 网站 URL。过短描述会生成泛词与低相关候选，会被拒绝。`enable_competitor_kw`（默认开）：设 `false` 只收直接需求线索，排除竞品对比帖。`track_type`（内部用：outreach/seo/hot_content） | 免费（候选免费） | Header |
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
| `vibe_recover_lead` | `lead_id` | **恢复误判线索**：从回收池回到待评分队列，可重新评分（通过不重复计费）| 免费 | Header |
| `vibe_subs` | `subscription_id` | **来源 sub 命中统计**（各 sub 入池/状态分布）——哪些 subreddit 真在贡献。注意与 `vibe_list_subs`（你的订阅列表）区分 | 免费 | Header |
| `vibe_supply_status` | `subscription_id` | **语料供给状态快照（零 LLM，2026-09-07）**：拉取池规模 / 储备分层 / 词搜最近运行 / **近 7 天 post_store 入帖趋势**（语料是否还在增长）/ 名录新鲜度（总量 + 最后更新）/ ArcticShift 限流态（共享熔断，跨进程）。用于区分：*词面耗尽*（应扩词）vs *语料边界窄*（应扩 sub）vs *名录旧*（catalog 需月度刷新）vs *采集停* vs *限流中* | 免费 | Header |
| `vibe_search_probe` | `subscription_id`, `query`, `subreddits`, `limit`(≤5) | **池外定向搜索探测（ArcticShift，2026-09-07）**：扩词前先在目标 sub 内搜这个词——即时验证"这个词在那边到底能不能搜出帖子"（防盲扩）。命中的帖幂等入库共享语料；**不入你的 lead_pool**（匹配仍由词驱动）。与 `sub_pull`（只覆盖池内 sub）互补 | 免费 | Header |

> 费用说明：上面 12 个是读写状态操作——候选仍免费，仍只在 `vibe_submit_score` 判 `relevant` 时按效果计费（若未来有任一收费，最终计费口径会单独确认）。

### Agent 决策循环（每订阅、每轮）

vibedollar 是数据/状态层；**你（宿主 agent）是调优者**。服务端自动调优刻意做得很薄：
F3 零命中退役在每轮 pipeline 后跑、F2 深负退役每天一次、服务端扩词已停
（"P3 disabled — consumer-driven"）。所以让订阅保持健康的循环是**你的**。
每个订阅一轮一个动作地跑：

```
perceive → plan → act → verify  （verify 门控下一轮 — 无时钟冷却）
```

#### 1. Perceive（读工具，零 LLM）

```
vibe_sub_health(sid)     → stock / gap / collecting_ok / last_opt
vibe_supply_status(sid)  → 语料入库趋势 / 名录新鲜度 / arctic.limited
vibe_keywords(sid, all)  → 每词: status/source/query/hit/pooled/avg_score/
                           n_delivered/n_rejected/invalid_sample/created_at
vibe_subs(sid)           → 哪些 subreddit 真在贡献候选
```

#### 2. Plan —— 先闭环你自己的评分反馈，再按边际产出判断

**A. 评分反馈是最强信号 —— 当轮行动，别等服务端的每日批。**
若你上一轮评分给某词产出 `irrelevant` 且该词 **0 delivered**
（n_rejected ≥ 2 来自你的评分，`invalid_sample` 显示它拉进的是什么垃圾）→ 该词是
噪声制造机 → **立即退役**：

```
vibe_keyword_remove(subscription_id, kw, force=true)   # auto 词, 编排器动作
vibe_opt_log(subscription_id, outcome="auto_retire", reason="0 relevant, N irrelevant")
```

服务端也会惩罚它（consume_feedback 每条 irrelevant −3 → F2 到 avg ≤ −6 退役），
但那在**每日批**上——你当轮就看到了噪声，就当轮退役它。

**B. 然后读 NEW30 边际产出信号**（判断"扩词还有没有用"）：
近 ~30 天新增的词（`created_at` 新）里：
- 大多**有命中**（hit>0）且存量低 → 继续扩（只用 probe 验证过的词）
- 大多**零命中**（被 F3 自动退役）→ 词面已扫净 → 停扩词——当前语料里可发现的需求
  接近天花板，转语料探索或如实报告，而不是继续盲目加词

**C. 语料 / 采集状态**（判据③）：
- `collecting_ok=false` → alert：采集停了，扩词无用
- 名录 `last_updated_at` 很旧 → alert 月度刷新（后端职责）
- 入库健康但词面扫净 → 语料边界窄 → 深挖已入池 sub / 扩新 sub 是阶段 B 工具；
  工具存在前：probe 有潜力的词 + 记录需求，不要发明扩法

决策表：

| 观察到 | 动作 |
|---|---|
| 词: 0 delivered + ≥2 条你的 irrelevant | `vibe_keyword_remove` force + `vibe_opt_log`（立即）|
| NEW30 词有命中、存量低 | 扩: `vibe_keyword_add_batch`（只用 probe 验证过的词）|
| NEW30 扫净（被 F3 退）、collecting_ok | 停扩 → 语料探索（阶段 B）/ 如实报告 |
| `collecting_ok=false` | alert（后端采集停 —— 扩词无用）|
| `arctic.limited` | 暂停供给动作 —— 物理等待，非冷却 |
| 全健康 + 存量 > 0 | wait —— 让快环（评分）消化 |

#### 3. Act

执行**一个**动作。加/停词后调 `vibe_opt_log(...)` 记录，健康页可审计。写下
**expect**：动作若有效，下一轮应该看到什么（如"新词在一轮 pipeline 内命中" /
"退役词停止入池垃圾"）？

#### 4. Verify（下一轮）

用新一轮 perceive 对照 expect：新词命中了吗？退役词停止拉垃圾了吗？下轮评分产出
改善了吗？
- expect 达成 → 继续同方向
- expect 失败 → **切换策略**（扩词 → probe 别的词 → 语料 → 如实报告），
  不要重复同一个失败动作

**纪律**（无时间冷却 / 每日次数 —— v2 §5.3）：
- 每轮一个动作（收敛纪律，非节流）
- verify 门控而非时钟门控：act → 看结果 → 决定下一步
- **扩词前先 probe**：`vibe_search_probe(query, [subs])` 秒级告诉你这词在那边有没有
  帖子——绝不盲扩然后等 30min pipeline 统计
- 唯一硬等待是 ArcticShift 物理限流，经 `vibe_supply_status` 透明感知

#### 5. 审计日志（每轮）

每轮完整记录以便回放与迭代 prompt —— ts / sid / round_no / world（工具原始返回，
不裁剪）/ 实际发出的 prompt / llm_raw / plan / action / result / verify / cost。
存在你自己的存储（可导出 JSON）。没有它就无法回答"agent 为什么这么判"、无法迭代
循环——日志是核心基建，不是事后补丁。

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
- 词表不用手工维护——订阅产品描述即可；当交付落后于承诺线时，由**你的 agent** 读健康工具扩/停词（见"交付健康管理"）
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
